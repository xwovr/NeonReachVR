#!/usr/bin/env python3
"""
Autonomous NeonReach player: observe -> decide -> throw, in a real-time loop.

Runs as a plain process outside the agent, so the loop ticks in milliseconds
instead of agent turns. It plays the way a person does: watch the rings come in,
predict where each is heading, throw with whichever hand is free, dodge
obstacles, and never wait to see whether the last throw landed.

  agent turn          ~10-15 s   -> cannot react to a 2.3 s ring at all
  operator stdio call   1-3 ms
  unity bridge call     ~10 ms   -> a full throw costs ~50 ms of wall clock

The agent freezes the game, launches this script, and the script unpauses
itself; on game over it re-pauses so the agent can inspect the aftermath.

Usage:
  python3 play.py --max-seconds 180
  python3 play.py --max-seconds 60 --dry-run
"""

import argparse
import atexit
import math
import os
import re
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor

PID_FILE = "/tmp/neonreach_play.pid"

# Toggled by SIGUSR1 so a running session can be frozen for inspection without
# killing it:   kill -USR1 $(cat /tmp/neonreach_play.pid)
_pause_requested = False


def _toggle_pause(_sig, _frm):
    global _pause_requested
    _pause_requested = not _pause_requested

from aim_solver import (solve_angled, RELEASE_Y, RELEASE_Z, RELEASE_SIDE,
                        Y_OFFSET, Z_OFFSET)
from mcp_client import OperatorClient, BridgeClient, McpError

# All three ring prefabs instantiate under their own names. Watching only
# "Ring(Clone)" makes the bot blind to every gold (weaving) and purple
# (rotating) ring - they simply sail past untouched.
RING_PATHS = {
    "plain": "Ring(Clone)",
    "gold": "WeavingRing(Clone)",
    "purple": "RotatingRing(Clone)",
}
OBSTACLE_PATH = "Obstacle(Clone)"

TRACK_MATCH_RADIUS = 1.5
MIN_ENGAGE_Z, MAX_ENGAGE_Z = 2.0, 10.0

# PlayerBody half-extent 0.25 + obstacle half-extent 0.5 => contact within 0.75 m.
DODGE_CLEARANCE = 0.90
DODGE_LOOKAHEAD_Z = 7.0
HEAD_Y = 1.70
HEAD_X_LIMIT = 1.9

# Resolved at startup - Unity instance IDs are reassigned on every Play Mode
# session, so a hardcoded value silently breaks miss tracking and game-over
# detection (every read errors, the run idles straight past a real death).
GAME_MANAGER_ID = None


def resolve_game_manager_id(bridge):
    """Look up the GameManager's live instance ID for this Play Mode session."""
    r = str(bridge.scene("SearchGameObjects", searchPattern="GameManager",
                         exactMatch=True))
    m = re.search(r"ID:\s*(\d+)", r)
    if not m:
        raise RuntimeError(f"GameManager not found - is Play Mode running? {r}")
    return m.group(1)


class Ring:
    """Second-order motion estimate.

    Gold rings weave on a sine (A=0.9 m, f=0.25 Hz). Extrapolating that with
    velocity alone leaves ~0.5*A*w^2*dt^2 ~ 0.28 m of error over a 0.5 s
    horizon - most of the 0.35 m hole. Carrying acceleration cuts the residual
    to ~0.6*dt^3 ~ 0.07 m, which comfortably fits.
    """
    __slots__ = ("key", "kind", "pos", "vel", "acc", "last_seen", "engaged_until")

    def __init__(self, key, kind, pos, t):
        self.key, self.kind = key, kind
        self.pos = pos
        self.vel = (0.0, 0.0, 0.0)
        self.acc = (0.0, 0.0, 0.0)
        self.last_seen = t
        self.engaged_until = 0.0

    def update(self, pos, t):
        dt = t - self.last_seen
        if dt > 1e-3:
            new_vel = tuple((pos[i] - self.pos[i]) / dt for i in range(3))
            raw_acc = tuple((new_vel[i] - self.vel[i]) / dt for i in range(3))
            # Finite differences on a ~30 Hz signal are noisy; smooth hard.
            self.acc = tuple(0.7 * self.acc[i] + 0.3 * raw_acc[i] for i in range(3))
            self.vel = new_vel
        self.pos, self.last_seen = pos, t

    def predict(self, dt):
        return tuple(self.pos[i] + self.vel[i] * dt + 0.5 * self.acc[i] * dt * dt
                     for i in range(3))


class Tracker:
    def __init__(self):
        self.rings = []
        self._next_key = 0
        self.lost = {"plain": 0, "gold": 0, "purple": 0}

    def observe(self, by_kind, t):
        seen = []
        for kind, positions in by_kind.items():
            for p in positions:
                seen.append((kind, p))
        unmatched = list(self.rings)
        for kind, p in seen:
            best, best_d = None, TRACK_MATCH_RADIUS
            for r in unmatched:
                if r.kind != kind:
                    continue
                d = math.dist(p, r.pos)
                if d < best_d:
                    best, best_d = r, d
            if best is not None:
                best.update(p, t)
                unmatched.remove(best)
            else:
                self._next_key += 1
                self.rings.append(Ring(self._next_key, kind, p, t))
        gone = [r for r in unmatched if t - r.last_seen > 0.25]
        for r in gone:
            self.lost[r.kind] += 1
            self.rings.remove(r)
        return len(gone)


class Hand:
    """Paces one throw across real Unity frames.

    The four steps must straddle frame boundaries: if press and release land in
    the same Update the launcher never sees a rising edge and the throw is
    silently lost.
    """
    FRAME = 0.020
    PULL_TIME = 0.15
    COOLDOWN = 0.08

    def __init__(self, name, op):
        self.name, self.op = name, op
        self.state, self.t_next = "idle", 0.0
        self.plan = None
        self.throws = 0
        self.by_kind = {"plain": 0, "gold": 0, "purple": 0}

    def busy(self, now):
        return self.state != "idle" or now < self.t_next

    def begin(self, plan, kind, now):
        self.plan = plan
        self.op.call("openxr_set_controller_pose", hand=self.name, pose_type="grip",
                     base_space="local_floor", position=list(plan["grab_oxr"]),
                     orientation=[0.5, 0, 0, 0.866],
                     reason="autonomous player: grab origin")
        self.by_kind[kind] += 1
        self.state, self.t_next = "press", now + self.FRAME

    def step(self, now):
        if now < self.t_next or self.state == "idle":
            return
        if self.state == "press":
            self.op.call("openxr_set_controller_input", hand=self.name,
                         component="Trigger", value=1, auto_release=False,
                         reason="autonomous player: grab")
            self.state, self.t_next = "pull", now + self.FRAME
        elif self.state == "pull":
            self.op.call("openxr_set_controller_pose", hand=self.name,
                         pose_type="grip", base_space="local_floor",
                         position=list(self.plan["release_oxr"]),
                         orientation=[0.5, 0, 0, 0.866],
                         duration_seconds=self.PULL_TIME,
                         reason="autonomous player: draw")
            self.state, self.t_next = "release", now + self.PULL_TIME + self.FRAME
        elif self.state == "release":
            self.op.call("openxr_set_controller_input", hand=self.name,
                         component="Trigger", value=0, auto_release=False,
                         reason="autonomous player: loose")
            self.throws += 1
            self.state, self.t_next = "idle", now + self.COOLDOWN

    @property
    def throw_latency(self):
        return 3 * self.FRAME + self.PULL_TIME


def rest_pose_oxr(hand, head_x):
    """Neutral stance: hands at chest height, 0.45 m forward, in frame.

    This is the same point a throw releases from, so the hands look settled
    rather than parked mid-draw.
    """
    side = RELEASE_SIDE if hand == "right" else -RELEASE_SIDE
    return [head_x + side, RELEASE_Y - Y_OFFSET, Z_OFFSET - RELEASE_Z]


def reset_stance(op, head_x=0.0):
    """Put head and both hands back to a known neutral pose.

    Needed at BOTH ends of a run. A previous session leaves the head wherever
    its last dodge put it and a controller wherever its last grab origin was -
    and if the process died mid-throw, the trigger is still held. Starting a
    fresh game from that state throws from the wrong place with the wrong hand
    offset; observed carry-over was head x=-0.9 with a hand stuck out at a
    grab origin.
    """
    op.call("openxr_set_head_pose", base_space="local_floor",
            position=[head_x, HEAD_Y, 0.0],
            reason="reset stance: recentre head")
    for hand in ("right", "left"):
        op.call("openxr_set_controller_input", hand=hand, component="Trigger",
                value=0, auto_release=False,
                reason="reset stance: make sure no ball is held")
        op.call("openxr_set_controller_pose", hand=hand, pose_type="grip",
                base_space="local_floor", position=rest_pose_oxr(hand, head_x),
                orientation=[0.5, 0, 0, 0.866],
                reason="reset stance: neutral hand position")


def choose_dodge(head_x, obstacles):
    """Nearest safe lateral slot, or None if already clear."""
    near = [o for o in obstacles if 0.0 < o[2] < DODGE_LOOKAHEAD_Z]
    if not any(abs(o[0] - head_x) < DODGE_CLEARANCE for o in near):
        return None
    for cand in sorted([-1.8, -1.2, -0.9, 0.0, 0.9, 1.2, 1.8],
                       key=lambda x: abs(x - head_x)):
        if abs(cand) > HEAD_X_LIMIT:
            continue
        if all(abs(o[0] - cand) >= DODGE_CLEARANCE for o in near):
            return cand
    return None


class ParallelObserver:
    """Query the three ring prefabs concurrently.

    unity_get_world_pose round-trips into Unity at ~16 ms a call, and the
    operator speaks over a single stdio pipe, so three sequential queries pin
    the loop near 10 Hz. One proxy connection per prefab, fanned out across a
    thread pool, overlaps the waits and pulls the tick cost back down to about
    one call.
    """

    def __init__(self, paths):
        self.paths = paths
        self.clients = {k: OperatorClient() for k in paths}
        self.pool = ThreadPoolExecutor(max_workers=len(paths))

    def _one(self, kind):
        return kind, parse_positions(self.clients[kind].call(
            "unity_get_world_pose", path=self.paths[kind],
            reason="autonomous player: observe rings"))

    def observe(self):
        return dict(self.pool.map(self._one, list(self.paths)))

    def close(self):
        self.pool.shutdown(wait=False)
        for c in self.clients.values():
            c.close()


def parse_positions(resp):
    if not isinstance(resp, dict):
        return []
    out = []
    for m in resp.get("matches", []):
        if not m.get("active", True):
            continue
        p = m["position"]
        out.append((p["x"], p["y"], p["z"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-seconds", type=float, default=240.0)
    ap.add_argument("--tick", type=float, default=0.02)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-dodge", action="store_true")
    ap.add_argument("--keep-running", action="store_true",
                    help="do not re-pause the game when the run ends")
    ap.add_argument("--pause-on-miss", action="store_true",
                    help="freeze the moment a ring gets past, for inspection")
    ap.add_argument("--pause-at", type=float, default=None,
                    help="freeze this many seconds in, for inspection")
    ap.add_argument("--play-seconds", type=float, default=None,
                    help="throw for this long, then go idle and let rings "
                         "through - exercises the drain-to-game-over path "
                         "immediately after a known-good active phase")
    args = ap.parse_args()

    signal.signal(signal.SIGUSR1, _toggle_pause)
    with open(PID_FILE, "w") as fh:
        fh.write(str(os.getpid()))
    print(f"pid {os.getpid()} -> {PID_FILE}   "
          f"(kill -USR1 to pause/resume for inspection)")

    op = OperatorClient()
    bridge = BridgeClient()
    observer = ParallelObserver(RING_PATHS)
    tracker = Tracker()
    hands = [Hand("right", op), Hand("left", op)]

    global GAME_MANAGER_ID
    GAME_MANAGER_ID = resolve_game_manager_id(bridge)
    print(f"GameManager instance id {GAME_MANAGER_ID}")

    def field(name):
        r = bridge.scene("GetComponentValue", instanceId=GAME_MANAGER_ID,
                         componentName="GameManager", memberName=name)
        v = str(r).split("=")[-1].split("(")[0].strip()
        if "DATA:" not in str(r):
            raise RuntimeError(f"GameManager.{name} read failed: {r}")
        return v

    # Clear any stance left behind by a previous session BEFORE unpausing, so
    # the first frame of the new game already has hands and head where they
    # belong. Done while the game is still frozen.
    reset_stance(op, 0.0)
    print("stance reset (head centred, hands at rest, triggers released)")

    # Restore the stance however we exit, including a kill mid-draw - otherwise
    # the next run inherits a held trigger and an outstretched arm.
    def _cleanup():
        try:
            reset_stance(op, 0.0)
        except Exception:
            pass
    atexit.register(_cleanup)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))

    # The agent freezes before launching us so it has time to start the script;
    # we take over and unpause.
    bridge.set_time_scale(1.0)
    print("unpaused, playing")

    t0 = time.time()
    ticks = observe_ms = disappeared = unreachable = dodges = 0
    stalls, worst_stall = 0, 0.0
    head_x, next_poll, prev_missed, poll_fails = 0.0, 0.0, 0, 0
    next_obstacle_poll, obstacles = 0.0, []
    events, reason = [], "time limit"

    paused = pause_at_fired = went_idle = False
    idle_at_missed, idle_started = None, None
    while time.time() - t0 < args.max_seconds:
        loop_start = now = time.time()

        # One-shot: without the latch this re-fires every tick and instantly
        # undoes any SIGUSR1 resume.
        if args.pause_at is not None and not pause_at_fired and now - t0 >= args.pause_at:
            pause_at_fired = True
            globals()["_pause_requested"] = True

        # Hold the world still, but keep the loop alive so it can be resumed.
        if _pause_requested != paused:
            paused = _pause_requested
            bridge.set_time_scale(0.0 if paused else 1.0)
            state = "PAUSED for inspection" if paused else "resumed"
            events.append((round(now - t0, 1), state))
            print(f"[{now - t0:6.1f}s] {state}", flush=True)
        if paused:
            time.sleep(0.1)
            continue

        # Each unity_get_world_pose costs ~16 ms (it round-trips into Unity), so
        # the call count per tick sets the loop rate. Rings need all three
        # prefab names every tick for clean velocity estimates; obstacles are
        # slow and rare, so sampling them at 4 Hz keeps the loop ~3x faster.
        a = time.time()
        try:
            by_kind = observer.observe()
            if now >= next_obstacle_poll:
                next_obstacle_poll = now + 0.25
                obstacles = parse_positions(
                    op.call("unity_get_world_pose", path=OBSTACLE_PATH,
                            reason="autonomous player: watch obstacles"))
        except McpError:
            reason = "operator disconnected"
            break
        dt_obs = (time.time() - a) * 1000
        observe_ms += dt_obs
        ticks += 1
        # A blocked operator link (reconnects respawn a proxy, which costs
        # seconds) stalls the loop while the game keeps running unattended -
        # health drains and the run is silently invalidated. Make it visible.
        if dt_obs > 500:
            stalls += 1
            worst_stall = max(worst_stall, dt_obs)
            events.append((round(now - t0, 1), f"STALL {dt_obs/1000:.1f}s observing"))

        disappeared += tracker.observe(by_kind, now)

        for hand in hands:
            hand.step(now)

        # Active phase gate: after --play-seconds the bot deliberately goes
        # idle - no throwing, no dodging - so health drains to a game over.
        active = args.play_seconds is None or (now - t0) < args.play_seconds
        if not active and not went_idle:
            went_idle = True
            idle_at_missed = prev_missed
            idle_started = now
            events.append((round(now - t0, 1),
                           f"IDLE - stopped throwing at {prev_missed} missed"))
            print(f"[{now - t0:6.1f}s] going idle after "
                  f"{sum(h.throws for h in hands)} throws", flush=True)

        # Dodging moves the controllers with the head, so only between throws.
        # The release pose is body-relative, so the hands follow the new stance.
        if active and obstacles and not args.dry_run and not args.no_dodge \
                and all(not h.busy(now) for h in hands):
            target_x = choose_dodge(head_x, obstacles)
            if target_x is not None and abs(target_x - head_x) > 0.05:
                op.call("openxr_set_head_pose", base_space="local_floor",
                        position=[target_x, HEAD_Y, 0.0], duration_seconds=0.15,
                        reason="autonomous player: dodge obstacle")
                head_x = target_x
                dodges += 1
                time.sleep(0.16)
                continue

        order = hands if ticks % 2 == 0 else list(reversed(hands))
        head = (head_x, HEAD_Y, 0.0)
        for hand in (order if active else []):
            if hand.busy(now):
                continue
            lead = hand.throw_latency
            best = best_plan = best_kind = None
            for r in tracker.rings:
                if now < r.engaged_until:
                    continue
                horizon, plan = lead + 0.25, None
                try:
                    for _ in range(6):          # converge lead + flight together
                        p = r.predict(horizon)
                        if not (MIN_ENGAGE_Z < p[2] < MAX_ENGAGE_Z):
                            raise ValueError("outside engagement window")
                        plan = solve_angled(p, hand=hand.name, head=head)
                        horizon = lead + plan["flight_time"]
                except ValueError:
                    unreachable += 1
                    continue
                pz = r.predict(horizon)[2]
                if best is None or pz < best[0]:
                    best, best_plan, best_kind = (pz, r), plan, r.kind
            if best is not None and not args.dry_run:
                best[1].engaged_until = now + 0.8
                hand.begin(best_plan, best_kind, now)

        if now >= next_poll:
            next_poll = now + 0.4
            try:
                m = int(field("MissedRings"))
                over = field("IsGameOver").lower() == "true"
                poll_fails = 0
            except (ValueError, RuntimeError) as exc:
                # A blind poll means misses and game over go unseen and the run
                # idles past a real death, so tolerate a blip and then bail.
                m, over = prev_missed, False
                poll_fails += 1
                if poll_fails >= 5:
                    raise RuntimeError(
                        f"GameManager unreadable {poll_fails} polls running - "
                        f"aborting rather than reporting a blind run: {exc}")
            if m != prev_missed:
                events.append((round(now - t0, 1), f"missed {prev_missed} -> {m}"))
                prev_missed = m
                if args.pause_on_miss:
                    globals()["_pause_requested"] = True
            if over:
                # The final miss can land between the MissedRings read and this
                # one, so re-read or the summary reports 9/10 on a game over.
                try:
                    prev_missed = int(field("MissedRings"))
                except (ValueError, RuntimeError):
                    pass
                events.append((round(now - t0, 1), "GAME OVER"))
                reason = "game over"
                break

        time.sleep(max(0.0, args.tick - (time.time() - loop_start)))

    elapsed = time.time() - t0
    if not args.keep_running:
        bridge.set_time_scale(0.0)
        print("re-paused for inspection")

    thrown = sum(h.throws for h in hands)
    print(f"\nstopped        {reason} after {elapsed:.1f}s "
          f"({ticks} ticks, {ticks/max(elapsed,1e-9):.1f} Hz)")
    print(f"observe        {observe_ms/max(ticks,1):.2f} ms per tick "
          f"(3 rings in parallel + obstacles at 4 Hz)")
    print(f"throws         {thrown}  right {hands[0].throws} / left {hands[1].throws}")
    for kind in ("plain", "gold", "purple"):
        aimed = sum(h.by_kind[kind] for h in hands)
        print(f"  {kind:<7} aimed {aimed:<4} vanished {tracker.lost[kind]}")
    reconnects = op.reconnects + sum(c.reconnects for c in observer.clients.values())
    print(f"dodges         {dodges}  (final head x {head_x:+.2f})")
    if reconnects:
        print(f"reconnects     {reconnects} operator link(s) respawned mid-run")
    if stalls:
        print(f"stalls         {stalls} tick(s) over 0.5s, worst "
              f"{worst_stall/1000:.1f}s - RESULTS SUSPECT, the game ran "
              f"unattended during these")
    print(f"rings vanished {disappeared}")
    print(f"MissedRings    {prev_missed} / 10")
    if went_idle:
        drained = prev_missed - idle_at_missed
        span = elapsed - (idle_started - t0)
        print(f"phases         active {args.play_seconds:.0f}s -> "
              f"{idle_at_missed} missed | idle {span:.1f}s -> +{drained} missed"
              + (f" ({span/drained:.1f}s per miss)" if drained else ""))
    if disappeared:
        hits = disappeared - prev_missed
        print(f"inferred hits  {hits}/{disappeared} ({100.0*hits/max(disappeared,1):.0f}%)")
    if unreachable:
        print(f"unreachable    {unreachable} evaluations rejected")
    if events:
        print("\ntimeline (s):")
        for t, what in events:
            print(f"  {t:7.1f}  {what}")

    observer.close()
    op.close()


if __name__ == "__main__":
    main()
