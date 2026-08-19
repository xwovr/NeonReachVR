#!/usr/bin/env python3
"""
Ballistic aim solver for NeonReach VR slingshot testing.

Emits the pair of OpenXR grip poses (grab origin + release point) that make a
max-charge throw land on a target, for either hand, against either a static
target or a ring in motion (linear, weaving, and/or rotating).

STRATEGY: flat pull + raised launch height.
The controller is always pulled HORIZONTALLY (grab and release share the same
Y), and the launch is raised by the ballistic drop instead of angling the shot
upward. Both axes were verified to track exactly in the running game; angled
pulls under-deliver their vertical component and miss beyond ~5 m. See
SKILL.md "Verified vs. not verified".

Model (measured against the running game):
  * BallLauncher aim  = normalize(grabOrigin - releasePos)   [slingshot: pull back]
  * charge            = min(|grab - release|, 0.35)
  * launch speed      = charge * _launchMultiplier (80 in the scene) -> 28 m/s max
  * ball spawns at the release position, gravity -9.81, zero linear damping

Ring motion (RingBehavior.Update), all in Unity world space:
  * z(t) = z0 - MoveSpeed * t                       (always)
  * x(t) = _startX + sin(2*pi*f*(_elapsedTime+t))*A (only when IsWeaving)
  * y     constant
  * yaw(t) = yaw0 + RotationSpeed * t               (only when IsRotating)

Coordinate mapping, verified for BOTH hands (OVRCameraRig at origin,
tracking origin FloorLevel):
  unity  = ( oxr.x,  oxr.y + 0.0775, -oxr.z + 0.04 )
  oxr    = ( unity.x, unity.y - 0.0775, 0.04 - unity.z )

Usage:
  # static target
  python3 aim_solver.py 0.8 1.95 6.5 --hand right

  # moving ring: pass its state sampled while the game is frozen
  python3 aim_solver.py --intercept --ring-pos 0.6 1.6 9.0 --move-speed 2.5 --hand left
  python3 aim_solver.py --intercept --ring-pos 0.6 1.6 9.0 --move-speed 2.5 \
      --weaving --start-x 0.6 --elapsed 1292.08 --amplitude 0.9 --frequency 0.25
"""

import argparse
import math

G = 9.81
MAX_PULL = 0.35
# OpenXR local_floor -> Unity world offset, measured by setting a controller
# pose and reading back OVRCameraRig/TrackingSpace/{Left,Right}HandAnchor.
# Verified identical for both hands - there is no mirroring.
Y_OFFSET = 0.0775
Z_OFFSET = 0.04
# Hold this orientation for every pose. The grip->OVR-anchor offset above is
# only constant while the orientation is fixed.
GRIP_ORIENTATION = [0.5, 0.0, 0.0, 0.866]

# Release at unity z = 0.45, i.e. ~0.45 m in front of the head, so the
# controller and the charging ball stay inside the ~90 deg FOV for the whole
# throw. At the old value (unity z = 0.14) the controller sat level with the
# face and left frame, making screenshots useless for verification.
DEFAULT_RELEASE_Z_OXR = -0.41          # -> unity z = 0.45
DEFAULT_RELEASE_X_OXR = {"right": 0.20, "left": -0.20}

HOLE_RADIUS = 0.35
BOX_HALF_DEPTH = 0.40                  # ScoreZone BoxCollider is 0.7 x 0.7 x 0.8

MIN_LAUNCH_Y, MAX_LAUNCH_Y = 0.60, 2.40

# PlayerBody is a NON-trigger 0.5^3 BoxCollider that follows centreEyeAnchor.
# A ball released inside it is deflected by the player's own hitbox, which
# silently corrupts both speed and direction. Keep the release point clear.
PLAYER_BOX_HALF = 0.25
BALL_RADIUS = 0.02
DEFAULT_HEAD = (0.0, 1.7475, 0.0)


def assert_clear_of_player(release_unity, head):
    """Raise if the ball would spawn inside PlayerBody's collider."""
    m = PLAYER_BOX_HALF + BALL_RADIUS
    inside = all(abs(release_unity[i] - head[i]) < m for i in range(3))
    if inside:
        raise ValueError(
            f"release point {tuple(round(c, 3) for c in release_unity)} is inside "
            f"PlayerBody's {2*PLAYER_BOX_HALF}m hitbox at {head} - the ball will be "
            f"deflected on launch. Move the release forward (raise --release-z-oxr "
            f"magnitude) so it clears the player."
        )


def oxr_to_unity(p):
    return (p[0], p[1] + Y_OFFSET, -p[2] + Z_OFFSET)


def unity_to_oxr(p):
    return (p[0], p[1] - Y_OFFSET, Z_OFFSET - p[2])


def ring_at(t, ring):
    """Ring centre and yaw at t seconds after the unfreeze moment."""
    z = ring["pos"][2] - ring["move_speed"] * t
    if ring["weaving"]:
        phase = 2.0 * math.pi * ring["frequency"] * (ring["elapsed"] + t)
        x = ring["start_x"] + math.sin(phase) * ring["amplitude"]
    else:
        x = ring["pos"][0]
    yaw = ring["yaw"] + ring["rotation_speed"] * t if ring["rotating"] else ring["yaw"]
    return (x, ring["pos"][1], z), yaw


def solve(target_unity, hand="right", release_x_oxr=None,
          release_z_oxr=DEFAULT_RELEASE_Z_OXR, speed_mult=80.0, ring=None,
          head=DEFAULT_HEAD):
    v = MAX_PULL * speed_mult
    rx = DEFAULT_RELEASE_X_OXR[hand] if release_x_oxr is None else release_x_oxr
    rz = -release_z_oxr + Z_OFFSET

    # Fixed-point iteration on flight time; converges in a few passes because
    # the ring's displacement is small next to the throw distance.
    aim = target_unity
    yaw = 0.0
    flight = 0.0
    for _ in range(64):
        d = math.hypot(aim[0] - rx, aim[2] - rz)
        if d < 1e-6:
            raise ValueError("target is directly above/below the release point")
        new_flight = d / v
        if ring is None:
            flight = new_flight
            break
        if abs(new_flight - flight) < 1e-7:
            break
        flight = new_flight
        aim, yaw = ring_at(flight, ring)

    d = math.hypot(aim[0] - rx, aim[2] - rz)
    drop = 0.5 * G * flight * flight
    launch_y = aim[1] + drop

    if not (MIN_LAUNCH_Y <= launch_y <= MAX_LAUNCH_Y):
        raise ValueError(
            f"required launch height {launch_y:.3f}m is outside the plausible "
            f"range [{MIN_LAUNCH_Y}, {MAX_LAUNCH_Y}] - target too far or too high")

    release_unity = (rx, launch_y, rz)
    assert_clear_of_player(release_unity, head)
    grab_unity = (rx + (aim[0] - rx) / d * MAX_PULL, launch_y,
                  rz + (aim[2] - rz) / d * MAX_PULL)

    return {
        "grab_oxr": unity_to_oxr(grab_unity), "release_oxr": unity_to_oxr(release_unity),
        "aim_point": aim, "impact_yaw": yaw, "speed": v, "horizontal_distance": d,
        "flight_time": flight, "drop": drop, "launch_y": launch_y,
        "hand": hand, "orientation": GRIP_ORIENTATION,
    }


# --- angled aiming, body-relative -------------------------------------------
# The flat solver above raises the whole launch to pay for the drop, which for a
# far/high target demands a release up at 2.2-2.4 m - an arm held absurdly high,
# often out of frame, and rejected outright past ~2.4 m. Angled aiming instead
# keeps the hand at a natural chest height and tilts the throw, which looks like
# a real player and puts effectively the whole arena in range (v^2/g ~ 80 m).
# Safe now that the PlayerBody deflection is understood: a 30 deg pull measured
# exactly (0, 14.00, 24.25) against a predicted (0, 14.0, 24.25).
RELEASE_Y = 1.45          # chest height, below the 1.70 head
RELEASE_Z = 0.45          # clear of the 0.25 m player half-box
RELEASE_SIDE = 0.20       # lateral offset from body centre, per hand


def solve_angled(target_unity, hand="right", head=(0.0, HEAD_Y_DEFAULT := 1.70, 0.0),
                 speed_mult=80.0, ring=None):
    """Aim at a target from a natural, body-relative release pose.

    The release tracks the head laterally, so after a dodge the hands stay with
    the body instead of snapping back to a world-fixed spot.
    """
    v = MAX_PULL * speed_mult
    side = RELEASE_SIDE if hand == "right" else -RELEASE_SIDE
    release = (head[0] + side, RELEASE_Y, RELEASE_Z)

    aim_pt = target_unity
    flight = 0.0
    for _ in range(64):
        dx, dy, dz = (aim_pt[i] - release[i] for i in range(3))
        d = math.hypot(dx, dz)
        if d < 1e-6:
            raise ValueError("target is directly above/below the release point")
        disc = v**4 - G * (G * d * d + 2 * dy * v * v)
        if disc < 0:
            raise ValueError(f"out of range: d={d:.2f} h={dy:+.2f}")
        theta = math.atan2(v * v - math.sqrt(disc), G * d)
        new_flight = d / (v * math.cos(theta))
        if ring is None or abs(new_flight - flight) < 1e-7:
            flight = new_flight
            break
        flight = new_flight
        aim_pt, _ = ring_at(flight, ring)

    dx, dy, dz = (aim_pt[i] - release[i] for i in range(3))
    d = math.hypot(dx, dz)
    disc = v**4 - G * (G * d * d + 2 * dy * v * v)
    if disc < 0:
        raise ValueError(f"out of range: d={d:.2f} h={dy:+.2f}")
    theta = math.atan2(v * v - math.sqrt(disc), G * d)

    aim = (dx / d * math.cos(theta), math.sin(theta), dz / d * math.cos(theta))
    grab = tuple(release[i] + aim[i] * MAX_PULL for i in range(3))

    assert_clear_of_player(release, head)
    return {
        "grab_oxr": unity_to_oxr(grab), "release_oxr": unity_to_oxr(release),
        "grab_unity": grab, "release_unity": release, "aim_point": aim_pt,
        "elevation_deg": math.degrees(theta), "speed": v,
        "flight_time": flight, "hand": hand, "orientation": GRIP_ORIENTATION,
    }


def rotation_warning(yaw_deg):
    """
    RingHitZone projects the ball into the ScoreZone's LOCAL xy plane, but
    OnTriggerEnter fires at the box boundary where local z is ~+/-0.40. For a
    ring yawed away from face-on, that depth leaks into local x as
    0.40*sin(yaw), eating into the 0.35 hole radius. Rings spawn at yaw 180
    (face-on); IsRotating spins them away from it.
    """
    off = abs(((yaw_deg - 180.0) + 180.0) % 360.0 - 180.0)
    leak = BOX_HALF_DEPTH * math.sin(math.radians(off))
    return off, leak


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tx", type=float, nargs="?")
    ap.add_argument("ty", type=float, nargs="?")
    ap.add_argument("tz", type=float, nargs="?")
    ap.add_argument("--hand", choices=["left", "right"], default="right")
    ap.add_argument("--release-x-oxr", type=float, default=None)
    ap.add_argument("--release-z-oxr", type=float, default=DEFAULT_RELEASE_Z_OXR)
    ap.add_argument("--speed-mult", type=float, default=80.0,
                    help="BallLauncher._launchMultiplier (scene value: 80)")

    ap.add_argument("--intercept", action="store_true",
                    help="target is a moving ring; requires --ring-pos")
    ap.add_argument("--ring-pos", nargs=3, type=float, metavar=("X", "Y", "Z"))
    ap.add_argument("--move-speed", type=float, default=0.0)
    ap.add_argument("--weaving", action="store_true")
    ap.add_argument("--start-x", type=float, default=0.0)
    ap.add_argument("--elapsed", type=float, default=0.0)
    ap.add_argument("--amplitude", type=float, default=0.9)
    ap.add_argument("--frequency", type=float, default=0.25)
    ap.add_argument("--rotating", action="store_true")
    ap.add_argument("--yaw", type=float, default=180.0, help="current yaw in degrees")
    ap.add_argument("--rotation-speed", type=float, default=45.0)
    args = ap.parse_args()

    ring = None
    if args.intercept:
        if not args.ring_pos:
            ap.error("--intercept requires --ring-pos X Y Z")
        ring = {
            "pos": tuple(args.ring_pos), "move_speed": args.move_speed,
            "weaving": args.weaving, "start_x": args.start_x,
            "elapsed": args.elapsed, "amplitude": args.amplitude,
            "frequency": args.frequency, "rotating": args.rotating,
            "yaw": args.yaw, "rotation_speed": args.rotation_speed,
        }
        target = tuple(args.ring_pos)
    else:
        if args.tx is None or args.ty is None or args.tz is None:
            ap.error("static mode requires TX TY TZ")
        target = (args.tx, args.ty, args.tz)

    r = solve(target, args.hand, args.release_x_oxr, args.release_z_oxr,
              args.speed_mult, ring)

    def fmt(v):
        return "[" + ", ".join(f"{c:.4f}" for c in v) + "]"

    print(f"hand             {r['hand']}")
    if ring:
        print(f"ring now         {fmt(ring['pos'])}  move_speed={ring['move_speed']}"
              f"{'  weaving' if ring['weaving'] else ''}"
              f"{'  rotating' if ring['rotating'] else ''}")
        print(f"intercept at     {fmt(r['aim_point'])}   (t+{r['flight_time']:.4f}s)")
    else:
        print(f"target (unity)   {fmt(target)}")
    print(f"speed            {r['speed']:.2f} m/s over {r['horizontal_distance']:.3f} m")
    print(f"drop             {r['drop']:.4f} m  -> launch height {r['launch_y']:.4f} m")

    if ring and ring["rotating"]:
        off, leak = rotation_warning(r["impact_yaw"])
        print(f"yaw at impact    {r['impact_yaw']:.1f} deg ({off:.1f} deg off face-on)")
        print(f"  depth leak into local x: {leak:.3f} m of the {HOLE_RADIUS} m radius"
              + ("   <-- HIT TEST UNRELIABLE" if leak > 0.5 * HOLE_RADIUS else ""))

    print()
    if ring:
        print("Freeze the world first:  Time.set_timeScale(0)")
    print(f"Tool-call sequence (hand={r['hand']}, base_space=local_floor, pose_type=grip):")
    print(f"  1. set_controller_pose  position={fmt(r['grab_oxr'])} "
          f"orientation={fmt(r['orientation'])}")
    print( "  2. set_controller_input Trigger=1  auto_release=false")
    print(f"  3. set_controller_pose  position={fmt(r['release_oxr'])} "
          f"orientation={fmt(r['orientation'])} duration_seconds=0.5")
    print( "  4. set_controller_input Trigger=0  auto_release=false")
    if ring:
        print("Then unfreeze:           Time.set_timeScale(1)")


if __name__ == "__main__":
    main()
