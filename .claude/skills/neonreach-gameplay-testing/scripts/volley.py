#!/usr/bin/env python3
"""
Plan a multi-ring volley in ONE freeze.

While Time.timeScale == 0 a released ball keeps its armed velocity but does not
move, and BallLauncher immediately clears _activeBall - so a single hand can arm
any number of balls back to back. Unfreeze once and they all fly together.

This planner also interleaves the two hands. The four steps of a throw are
order-dependent, but the SAME step on opposite hands is independent, so the
left- and right-hand calls can be issued in one batched tool block:

    block A:  R.pose(grab_i)      L.pose(grab_j)
    block B:  R.trigger=1         L.trigger=1
    block C:  R.pose(release_i)   L.pose(release_j)
    block D:  R.trigger=0         L.trigger=0

That halves the number of agent turns, which is the dominant cost (10-15 s per
turn versus ~0.7 s for a second call inside the same turn).

Usage:
  python3 volley.py --z 6.0 --xs -2 -1 0 1 2 --ys 1.3 2.1
  python3 volley.py --targets "0.0,1.5,5.0" "1.0,1.8,6.0"
"""

import argparse
import sys

from aim_solver import solve

MIN_SEPARATION = 0.80   # 2 * hole radius + margin, so a ball cannot claim
                        # a neighbour's ring and confuse attribution

# Balls armed during one freeze all sit at their release points until unfreeze.
# A ball is 0.04 m across, and two throws by the same hand differ only by their
# launch height - which can be millimetres apart. Overlapping rigidbodies get
# blown apart by Unity's depenetration impulse the instant physics resumes,
# wrecking both trajectories. Measured: an unstaggered 10-ball volley scored
# 5/10 while the same throws fired individually scored 10/10.
# Staggering the release DEPTH per throw keeps every ball clear.
RELEASE_STAGGER = 0.10  # metres of extra stand-off per successive throw, per hand
BALL_DIAMETER = 0.04


def check_separation(targets):
    bad = []
    for i in range(len(targets)):
        for j in range(i + 1, len(targets)):
            a, b = targets[i], targets[j]
            if abs(a[2] - b[2]) > 1.0:
                continue          # different depth planes, no ambiguity
            lateral = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
            if lateral < MIN_SEPARATION:
                bad.append((i, j, lateral))
    return bad


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--z", type=float, default=6.0)
    ap.add_argument("--xs", nargs="*", type=float, default=[-2, -1, 0, 1, 2])
    ap.add_argument("--ys", nargs="*", type=float, default=[1.3, 2.1])
    # One semicolon-separated string, not nargs="*": a bare "-2.0,1.3,6.0"
    # looks like an option to argparse and blows up.
    ap.add_argument("--targets", default=None,
                    help='explicit targets as "x,y,z;x,y,z;...", overrides the grid')
    args = ap.parse_args()

    if args.targets:
        targets = [tuple(float(c) for c in t.split(","))
                   for t in args.targets.split(";") if t.strip()]
    else:
        targets = [(x, y, args.z) for y in args.ys for x in args.xs]

    bad = check_separation(targets)
    if bad:
        for i, j, s in bad:
            print(f"WARNING targets {i} and {j} are {s:.2f} m apart "
                  f"(< {MIN_SEPARATION} m) - a hit may be misattributed",
                  file=sys.stderr)

    # Alternate hands so both are busy in every block, and push each successive
    # throw by the same hand further forward so the parked balls never overlap.
    plan = []
    per_hand = {"right": 0, "left": 0}
    for idx, t in enumerate(targets):
        hand = "right" if idx % 2 == 0 else "left"
        n = per_hand[hand]
        per_hand[hand] += 1
        rz = -0.41 - n * RELEASE_STAGGER
        try:
            plan.append((idx, t, hand, solve(t, hand=hand, release_z_oxr=rz)))
        except ValueError as e:
            print(f"target {idx} {t}: UNREACHABLE - {e}", file=sys.stderr)
            plan.append((idx, t, hand, None))

    gaps = {}
    for idx, t, hand, r in plan:
        if r:
            gaps.setdefault(hand, []).append(r["release_oxr"])
    for hand, pts in gaps.items():
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                sep = sum((pts[i][k] - pts[j][k]) ** 2 for k in range(3)) ** 0.5
                if sep < BALL_DIAMETER * 1.5:
                    print(f"WARNING {hand} throws {i} and {j} park balls {sep:.3f} m "
                          f"apart - they will collide on unfreeze", file=sys.stderr)

    def fmt(v):
        return "[" + ", ".join(f"{c:.4f}" for c in v) + "]"

    print(f"{len(targets)} targets, one freeze\n")
    print(f"{'#':<3}{'hand':<7}{'target':<26}{'launch_y':<10}{'flight':<9}grab_oxr / release_oxr")
    for idx, t, hand, r in plan:
        if r is None:
            print(f"{idx:<3}{hand:<7}{str(t):<26}UNREACHABLE")
            continue
        print(f"{idx:<3}{hand:<7}{str(t):<26}{r['launch_y']:<10.4f}"
              f"{r['flight_time']:<9.4f}{fmt(r['grab_oxr'])}  {fmt(r['release_oxr'])}")

    pairs = [plan[i:i + 2] for i in range(0, len(plan), 2)]
    print(f"\nBlock plan: 1 freeze + {len(pairs)} pairs x 4 blocks + 1 unfreeze "
          f"= {len(pairs) * 4 + 2} turns")
    print(f"  (naive per-ring loop would be ~{len(targets) * 8} turns)")
    for pi, pair in enumerate(pairs):
        ids = " + ".join(f"#{i}({h})" for i, _, h, r in pair if r)
        print(f"  pair {pi}: {ids}")


if __name__ == "__main__":
    main()
