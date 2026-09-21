---
name: neonreach-gameplay-testing
description: Drives and verifies NeonReach VR's core slingshot/ring gameplay at runtime via Meta XR Operator plus the Meta Unity MCP bridge - Play Mode bring-up, a deterministic harness, calibrated left/right throws, freeze-lead-throw interception, and an autonomous real-time player script that plays whole games (plain, weaving and rotating rings, obstacle dodging) to game over with pause-for-inspection.
allowed-tools:
  - Bash(python3 *)
tags:
  - agentic-xr
  - openxr
  - unity
  - vr
  - testing
  - neonreach
---

# NeonReach VR — Gameplay Testing

Test the ring-shooter loop (`PinchBallLauncher` → ball → `RingScoreZone` →
`GameManager`) against the running game. Builds on **hz-meta-xr-operator** and
**hz-meta-xr-operator-unity-test-mechanics**; this skill adds the project
numbers, the pose sequences, and the interception technique — all measured
against the live build.

## The mechanic under test

Rings spawn at Unity `z = +12` across 7 spawn points and travel `-Z` at
1.5→5.5 m/s. The player holds the index trigger to grab a ball, pulls the
controller **backward**, and releases — a slingshot, so **aim = `grabOrigin −
releasePos`**. Charge is the pull distance clamped to 0.35 m; launch speed is
`charge × _launchMultiplier`, and the scene sets the multiplier to **80**, so
max muzzle speed is **28 m/s**. `RingScoreZone` catches colliders tagged `Ball`
in a 0.7×0.7×0.8 trigger box, then requires the ball centre within **0.35 m** of
the ring's local XY origin. The ring has no solid collider — a ball that misses
the hole passes straight through the rim.

## ⚠️ Never release inside the player hitbox

`PlayerBody` is a **non-trigger 0.5³ BoxCollider glued to `centerEyeAnchor`**.
A ball released inside it is physically deflected by the player's own body, which
corrupts launch speed *and* direction with no error and no log line. This
produced hours of phantom "vertical aim is broken" and "charge is only 94%"
results before it was found.

Keep the release point at least ~0.3 m in front of the head. The solver enforces
this (`assert_clear_of_player`) and the default release sits at Unity `z = 0.45`,
which also keeps the controller inside the ~90° FOV so screenshots are useful.

This is plausibly a **real game bug**, not just a harness artifact: a player who
pulls a ball right up to their face and releases will have the throw deflected by
their own hitbox. Worth raising separately.

## Bring-up

1. **Activate the simulator.** It ships inside `com.meta.xr.sdk.core` (v205) and
   is NOT active by default.
   - macOS: check `XR_SELECTED_RUNTIME_JSON` via `IReflectionService`; empty →
     `UIVerificationTools.ExecuteMenuItem("Meta/Meta XR Simulator/Activate")`.
     Requires `/Applications/MetaXRSimulator.app` (Apple Silicon only).
     Do **not** call the `Status` menu item — it opens a blocking modal dialog.
   - Windows: `HKLM:\SOFTWARE\Khronos\OpenXR\1\ActiveRuntime` must point at the
     simulator JSON (`C:\Program Files\MetaXRSimulator\v207.0\meta_openxr_simulator.json`).
     `activate_simulator.ps1` in the simulator install dir sets it (self-elevates).
2. **Load the operator API layer (Windows only).** The layer is not registered by
   default: set `XR_API_LAYER_PATH` to the
   `meta-xr-operator-standalone-public/windows` folder and
   `XR_ENABLE_API_LAYERS=XR_APILAYER_METAX_operator` **in the Unity process**
   (`unity command eval` + `System.Environment.SetEnvironmentVariable`), then
   restart Play Mode so `xrCreateInstance` picks it up. Without this every
   `openxr_*` call fails with `Server unavailable` at the MCP transport layer.
3. **Enter Play Mode.** macOS/MCP: `Edit/Play` is not a resolvable menu path —
   use `IReflectionService` → `UnityEditor.EditorApplication.EnterPlaymode`.
   Windows/Unity CLI: `unity command editor_play`. Then wait ~10 s.
4. **Confirm attach.** `openxr_get_session_info` should report
   `XR_SESSION_STATE_FOCUSED`. Before that, every `openxr_*` call fails with
   `Server unavailable` at the MCP transport layer.
5. **Check the profile.** `openxr_get_active_interaction_profile` must return a
   touch controller (`/interaction_profiles/meta/touch_controller_plus`).
   `PinchBallLauncher` early-outs on `OVRInput.IsControllerConnected`, so with
   no profile bound nothing happens and every test silently "fails".

## Coordinates

Tracking origin is **FloorLevel** → always pass `base_space: "local_floor"`.
With `OVRCameraRig` at the origin the mapping is a fixed offset, **verified
identical for both hands — there is no mirroring**:

```
unity = ( oxr.x,  oxr.y + 0.0775, -oxr.z + 0.04 )
oxr   = ( unity.x, unity.y - 0.0775, 0.04 - unity.z )
```

Only constant while controller **orientation is fixed** — keep every pose at
`[0.5, 0, 0, 0.866]`. Re-derive by setting one pose and reading back
`OVRCameraRig/TrackingSpace/{Left,Right}HandAnchor` if the rig moves (the player
can walk with the arrow keys).

## Deterministic harness

The spawner is randomised and difficulty ramps with a timer. All of this is Play
Mode state, discarded on exit — no cleanup needed.

| Step | Call |
|---|---|
| Lock health | `SetComponentValue GameManager._maxMissedRings = 100000` |
| Stop obstacles | `SetGameObjectActive ObstacleSpawner false` |
| Freeze future rings | `RingSpawner._baseSpeed = 0`, `_maxSpeed = 0` |
| Only plain rings | `RingSpawner._rotatingRingChance = 0`, `_waveSize = 9999` |
| Emit frozen targets | `InvokeComponentMethod GameManager.Restart` (public; fires `OnGameRestart` → restarts `SpawnLoop`) |
| Stop emitting | `SetGameObjectActive RingSpawner false` |
| Recycle a spent ring | `SetGameObjectActive <ringId> true` — deactivated rings are reusable |

**Two modes, pick deliberately.**

- *Whole-game testing* (default for `play.py`): leave `_maxMissedRings` at **10**,
  obstacles on, `_rotatingRingChance` 0.2, `_waveSize` 6. The run ends in a real
  game over, which is the point — it exercises health, the game-over path and
  the auto-restart.
- *Isolated mechanic assertions*: lock health with
  `_maxMissedRings = 100000` first, or the run reaches game over in ~30 s and
  restarts the scene mid-test. Remember to restore it to 10 afterwards.

`GetComponentValue`/`SetComponentValue` reach **private fields** (`_elapsedTime`,
`_startX`, `_maxMissedRings`), which is what makes weave phase controllable. They
do **not** reach private *methods* — route restarts through public
`GameManager.Restart()`.

Other gotchas:
- Disabling the spawner GameObject kills its coroutine permanently (`Start()`
  only runs once, so re-enabling does not resume it).
- **`GameManager.Restart()` destroys every previously spawned ring** —
  `HandleGameRestart` iterates `_activeRings` and `Destroy`s them, including ones
  you deactivated for later reuse. Recycling and re-spawning are mutually
  exclusive: pick one. To stock up, Restart *once* and let the spawner run
  (~2.5 s per ring at `_gameTimer = 0`).
- More rings spawn in the gap between your search and disabling the spawner.
- Live scene values differ from code defaults (`_launchMultiplier` 80 not 20,
  `_waveSize` 6 not 18).

**Batch independent calls.** Calls in one tool block run ~0.7 s apart versus
10–15 s across turns. Ten `SetComponentValue` placements or ten
`SetGameObjectActive` calls go in a single turn. Only genuinely ordered steps
(the four throw steps) need separate turns — and the same step on opposite hands
is independent, so left and right can share a block.

## The throw

Compute poses with `scripts/aim_solver.py`, then issue exactly four calls.
Never use `auto_release` — the press must span several frames so
`OnPinchStart` can latch `_pinchOrigin`.

```
1. openxr_set_controller_pose  hand=<h> pose_type=grip base_space=local_floor
                               position=<grab_oxr> orientation=[0.5,0,0,0.866]
2. openxr_set_controller_input hand=<h> component=Trigger value=1 auto_release=false
3. openxr_set_controller_pose  ... position=<release_oxr> duration_seconds=0.5
4. openxr_set_controller_input hand=<h> component=Trigger value=0 auto_release=false
```

Both hands work identically; `--hand left|right` picks a sensible release X
(`±0.20`). `PinchBallLauncher_Left`/`_Right` are independent instances, so both
hands can hold and throw simultaneously.

**Always pull horizontally.** The solver keeps grab and release at the same
height and pays for the ballistic drop by raising the launch. Angled pulls are
*not* broken (a deliberate 30° pull measured exactly `(0, 14.00, 24.25)` against
a predicted `(0, 14.0, 24.25)`), but flat pulls keep the launch clear of the
player hitbox and need no elevation solve.

Mid-throw introspection: after step 2 the ball spawns exactly at `_pinchOrigin`;
during step 3 `OnPinchHold` parks it on the controller. So
`SearchGameObjects("PinchBall")` + `Transform.position` reveals both endpoints of
the pull before you commit to the release.

## Scripted play — the fast path, use this by default

**Both MCP servers are directly callable from a plain Python process**, which
removes agent turn latency entirely:

| Path | Round trip |
|---|---|
| agent turn | 10–15 s |
| unity bridge, HTTP POST to `127.0.0.1:48736/mcpbridge/` + Bearer token (macOS) | ~11 ms |
| unity pipeline, HTTP POST to the pipeline server + descriptor token (Windows, no MCP) | ~30 ms |
| operator, stdio to `meta-xr-operator-mcp-proxy` | 1–3 ms |
| `unity_get_world_pose` (operator → Unity → back) | ~16 ms |

`scripts/mcp_client.py` wraps both. `scripts/play.py` is an autonomous player —
observe → decide → throw at **~19 Hz**, dodging obstacles, playing a real game
to game over.

### Pause protocol

**Freeze the game BEFORE launching, always.** Startup spawns four operator
proxies and takes **~7–12 s** before the first tick. Launch against a running
game and it plays itself unattended for that whole window — one run opened with
`missed 0 -> 2` at t=0 and the result was junk. Correct order:

```
# agent: set_timeScale(0)  ->  GameManager.Restart()  ->  then launch
python play.py --max-seconds 240                 # stops at game over, re-pauses
python play.py --max-seconds 240 --play-seconds 60  # play 60 s, then go idle
python play.py --max-seconds 60 --dry-run        # observe and decide only
python play.py --pause-at 30                     # freeze 30 s in
python play.py --pause-on-miss                   # freeze the instant one gets past
python play.py --keep-running                    # leave running at exit
kill -USR1 $(cat /tmp/neonreach_play.pid)        # toggle pause/resume (POSIX)
New-Item $env:TEMP/neonreach_play.pause          # freeze (Windows; delete to resume)
```

The ~7–12 s startup also offsets the script's clock from wall time; correlate
using its own timeline, not your shell sleeps.

### Stance must be reset at both ends

The script resets head and both hands to a neutral stance (hands at chest
height, ±0.20 m either side of the head, 0.45 m forward) while the game is still
frozen at startup, and again via `atexit` plus SIGTERM/SIGINT handlers on exit.

Without this a new game inherits whatever the last session left behind. Observed
carry-over: **head stuck at x = −0.9** from an un-undone dodge, and the left
controller frozen out at a *grab origin* with its trigger still held, because
the previous process was killed mid-draw. Every throw of the next run then
starts from the wrong place.

### Phase testing

`--play-seconds N` throws for N seconds then deliberately goes idle — no
throwing, no dodging — so health drains to a real game over straight after a
known-good active phase. It isolates the scoring/health path from aiming
quality, and gives a clean drain rate to compare against.

### Watch for stalls

A blocked operator link (a reconnect respawns a proxy, costing seconds) freezes
the loop *while the game keeps running*, silently invalidating a run — one such
stall let health fall 3 → 10 unattended and reported it as an "idle phase".
Any tick over 0.5 s is now counted and flagged `RESULTS SUSPECT` in the summary.
Treat any run with stalls as void.

### Design points that matter

- **Watch all three ring prefabs.** They instantiate as `Ring(Clone)`,
  **`WeavingRing(Clone)`** (gold, weaves left/right) and
  **`RotatingRing(Clone)`** (purple). Path matching is by exact name, so
  watching only `Ring(Clone)` makes the bot blind to every gold and purple ring
  — they sail past untouched. This silently capped the early runs.
- **Observe in parallel.** Three ring queries at ~16 ms each over one stdio pipe
  pinned the loop at 9.6 Hz. One proxy connection per prefab, fanned out over a
  thread pool, cut observation from 53 ms to 21 ms and doubled the loop to 19 Hz.
  Obstacles are slow and rare — poll them at 4 Hz, not every tick.
- **Track to second order.** Gold rings weave on a sine (A = 0.9 m, f = 0.25 Hz).
  Velocity-only extrapolation leaves ≈ 0.5·A·ω²·dt² ≈ **0.28 m** of error over a
  0.5 s horizon — most of the 0.35 m hole. Carrying acceleration drops the
  residual to ≈ 0.07 m. Smooth the second difference hard; it is noisy at 20 Hz.
- **Aim angled and body-relative.** `solve_angled()` keeps the hand at chest
  height (release 1.45 m, 0.45 m forward, ±0.20 m to the side of the head) and
  tilts the throw. The flat solver's raised launch demanded a hand at 2.2–2.4 m
  — out of frame, and rejected outright past 2.4 m. Angled aiming puts
  effectively the whole arena in range (v²/g ≈ 80 m) and looks like a person.
  The release tracks head X, so after a dodge the hands stay with the body
  instead of snapping to a world-fixed spot.
- **Pace each throw across Unity frames.** The four steps must straddle frame
  boundaries; if press and release land in the same `Update` the launcher never
  sees a rising edge and the throw is silently lost. `play.py` waits ≥1 frame
  (20 ms) per step and draws over 150 ms.
- **Fire and forget.** Never wait for a ring to die before the next throw. Mark
  the target engaged ~0.8 s so it isn't re-picked, then move on.
- **Alternate which hand picks first.** Fixed order lets the first hand claim
  every best target and starves the other: 48/11 became 25/26, and throughput
  rose from 59 to 70 throws.
- **Dodge only between throws.** `openxr_set_head_pose` moves the *controllers
  with the head*, so a dodge mid-throw drags the controller off the grab origin
  and corrupts the shot.
- **Auto-reconnect.** A 260 s run with four concurrent proxies lost one at 114 s
  and aborted. `OperatorClient.call` now respawns and retries once.
- No release staggering is needed in real-time play — consecutive balls leave at
  28 m/s and are metres apart by the next throw. Staggering matters only for the
  frozen volley (below).

## Windows port

The scripts are cross-platform; the differences from the original macOS setup:

- **Unity connection is the Unity Pipeline package, not MCP.**
  `PipelineClient` (`mcp_client.py`) POSTs to the editor's pipeline server
  (`127.0.0.1:7800/api/exec`) with the Bearer token from
  `Library/Pipeline/.unity-pipeline-port` — the same channel the `unity` CLI
  uses, minus its ~900 ms per-call process-spawn overhead. Measured eval: ~120 ms
  cold, ~30 ms warm. `NEONREACH_UNITY=mcp` selects the legacy Meta MCP bridge;
  `NEONREACH_PROJECT` overrides project-root discovery.
- **Operator proxy path is resolved per platform** (`%APPDATA%\metavr\tools\...\
  windows\meta-xr-operator-mcp-proxy.exe` on Windows, override with
  `NEONREACH_OPERATOR_BIN`).
- **No SIGUSR1 on Windows.** Pause/resume for inspection via the pause file
  (`%TEMP%\neonreach_play.pause`: create to freeze, delete to resume); the PID
  file also lives under the platform temp dir. SIGUSR1 still works on POSIX.
- **Close proxies explicitly.** `OperatorClient.close()` closes stdin (EOF lets
  the proxy exit cleanly), terminates, and reaps — otherwise GC-time pipe
  finalization prints `OSError: EINVAL` shutdown noise on Windows.
- **Remember the layer env (bring-up step 2).** It is set in-process and dies
  with the editor session — after any Unity restart, re-set
  `XR_API_LAYER_PATH`/`XR_ENABLE_API_LAYERS` via `unity command eval` and
  re-enter Play Mode before the operator tools work.

Full-game run on Windows (shipping settings, health 10), ending in a genuine
game over — matches the macOS results:

| Run | Loop | Observe | Throws | Hits | Survived | First miss |
|---|---|---|---|---|---|---|
| Windows, pipeline Unity link | 15.2 Hz | 35 ms | 226 | 92 % | 121.8 s | 48 s |

## Moving targets: freeze → lead → throw → unfreeze

Agent turn latency (**10–15 s**, measured from Unity log timestamps) dwarfs a
ring's lifetime (**2.3 s** at ramped speed, 8.3 s at base). Real-time reaction is
therefore impossible in the naive loop — a single tool call outlasts a fast ring.

`Time.timeScale = 0` makes the whole throw **atomic in game time**:

1. `IReflectionService` → `UnityEngine.Time.set_timeScale(0)`
2. Sample the ring: `Transform.position`, `RingBehavior.MoveSpeed`, and for
   weaving rings `_startX`, `_elapsedTime`, `LateralAmplitude`, `LateralFrequency`
3. `aim_solver.py --intercept --ring-pos X Y Z --move-speed S [--weaving ...]`
4. Issue the four throw calls (all still work — `Update` runs at `timeScale 0`,
   so press/hold/release latch normally; `FixedUpdate` is suspended so the armed
   velocity doesn't move the ball yet)
5. `set_timeScale(1)` — ball and ring start moving in the same frame, so the
   intercept carries **zero latency error** however long step 3 took

The solver fixed-point-iterates flight time against the ring's motion model:

```
z(t) = z0 - MoveSpeed*t
x(t) = _startX + sin(2*pi*f*(_elapsedTime + t))*A     (IsWeaving)
yaw(t) = yaw0 + RotationSpeed*t                        (IsRotating)
```

Because `_elapsedTime` and `_startX` are settable, weave phase is fully
controllable — set `_elapsedTime = 0` for the **worst case**, where lateral speed
peaks at `A·2πf` = 1.41 m/s and the ring drifts ~0.38 m during a 0.28 s flight.
That exceeds the 0.35 m hole radius, so a led shot and an unled shot give
opposite results — use it as the discriminating test.

Verify hits on moving rings with **`MissedRings`**, not just object existence: a
moving ring disappears either way, but only a miss increments the counter.

## Rotating rings — hit test is suspect (predicted, NOT yet verified)

`IsInsideHole` projects into the ScoreZone's **local** XY plane, but
`OnTriggerEnter` fires at the box boundary where local z ≈ ±0.40. For a ring
yawed off face-on, that depth leaks into local x as `0.40·sin(yaw_off)` — at 30°
that is 0.20 m of the 0.35 m radius, at 60° it is the entire radius. Predictions:
dead-centre shots get rejected at moderate yaw, and an edge-on ring may register
hits from balls that visually pass beside it.

The solver prints the yaw at impact and flags the leak. **This is derived from
reading the code, not measured.** To test: hold a fixed yaw with
`IsRotating = false` + `Transform.eulerAngles = "(0, 180+θ, 0)"` and fire
dead-centre shots at θ = 0, 20, 40, 60.

## Assertions

- **Hit** — `InspectGameObject(ringId)` returns "not found" *and*
  `GameManager.MissedRings` is unchanged.
- **Miss** — ring still inspects clean (static), or `MissedRings` incremented
  (moving).
- Health bar: `HealthBarFill` `anchorMax.x` (1.0 full → 0.0 dead).
- `openxr_capture_composited_image` for corroboration.

**Measuring launch velocity: only do it frozen.** Reading
`Rigidbody.linearVelocity` over MCP always lands hundreds of ms after launch, so
gravity has already contaminated `vy`; slowing `timeScale` does not help (it
scales flight too, and an upward shot bounces off the ceiling collider at
y = 3.5). At `timeScale = 0` the read is exact — that is how the model was
confirmed to be dead-on: predicted `(1.375, 0, 27.966)`, measured
`(1.38, 0.00, 27.97)`, magnitude 28.004 m/s = exactly max charge.

Expected console noise — not gameplay failures:
- Two Interaction SDK assertions at startup (`TurningSetting` /
  `MovementAimingSetting`), left over from the hand-tracking removal.
- `Quaternion To Matrix conversion failed ... l=0.999956` every frame, from the
  simulator's slightly non-unit head quaternion. Tens of thousands of entries —
  `ClearDiagnosticData` before a run and filter this string.
- `Coroutine couldn't be started because ... 'ObstacleSpawner' is inactive!` —
  self-inflicted by `GameManager.Restart()` with obstacles disabled. Harmless.

## Verified

Measured against the live build, 2026-08-17:

| Case | Result |
|---|---|
| Static hit, 4 m and 6.5 m, on- and off-axis | pass |
| Hole discrimination: radial 0.300 m vs 0.424 m, same throw | destroyed / survived |
| Left-hand throw, same calibration | pass |
| Intercept, ring closing at 2.5 m/s | pass |
| Intercept, weaving ring at peak lateral speed | pass |
| Launch vector vs. model (frozen read) | exact, 28.004 m/s |
| 10-ring volley, one freeze, unstaggered releases | **5/10** — balls collided |
| Same 5 survivors, staggered releases | 5/5 |
| Full game, shipping settings, real 10-life health | played to game over |
| Auto-restart after game over | recovers, no Play Mode restart needed |
| Pause / resume via `--pause-at`, `--pause-on-miss`, SIGUSR1 | drives `timeScale` exactly |

Full-game runs at shipping settings (health 10, obstacles on, difficulty ramping
1.5 → 5.5 m/s), each ending in a genuine game over:

| Run | Loop | Observe | Throws | Hits | Survived | First miss |
|---|---|---|---|---|---|---|
| all three ring types, sequential observe | 8.2 Hz | 63 ms | 183 | 91 % | 81.7 s | 23 s |
| + obstacles polled at 4 Hz | 9.6 Hz | 54 ms | 195 | 93 % | 85.9 s | 28 s |
| + parallel observe + auto-reconnect | **19.0 Hz** | 21 ms | 238 | 92 % | **121.9 s** | **64 s** |

Loop rate is the dominant lever: doubling it pushed survival 49 % longer and the
first miss from 23 s out to 64 s. Misses cluster hard in the last ~20 s, when the
spawn interval reaches 0.6 s and ring speed 5.5 m/s.

Phase test — 60 s active, then deliberately idle (`--play-seconds 60`), launched
from a properly paused game at **23.0 Hz**:

| Phase | Duration | Throws | Misses |
|---|---|---|---|
| active | 60 s | 80 | **0 / 10** |
| idle | 12.9 s | 0 | **+10 → game over** |

A perfect minute, then full health gone in under 13 s at ~1.4 s per miss. The
gap between those two numbers is the cleanest single measure of whether the
player loop is actually working.

Ball placement is accurate to better than ±0.05 m. The 0.300 / 0.424 pair is the
strongest evidence: identical throws bracketing the 0.35 m radius, both inside the
0.7×0.7 box, proving `IsInsideHole` genuinely rejects the box corners.

**Resolved — the freeze is no longer needed.** It was only ever compensating for
agent turn latency. A standalone script talking to the MCP servers directly runs
the whole loop at 30–42 Hz and plays in real time at 88 % accuracy. Keep the
freeze for two narrower jobs: exact launch-velocity measurement, and
single-shot geometry assertions where you want zero timing variance.

**Ball stacking — the volley trap.** Arming several balls during one freeze
parks them all at their release points. Two throws by the same hand differ only
by launch height, sometimes by ~5 mm, and a ball is 40 mm across; on unfreeze
Unity's depenetration impulse blows the overlapping balls apart and wrecks their
trajectories. An unstaggered 10-ball volley scored 5/10 where individual throws
scored 10/10; staggering the release depth by 0.10 m per successive throw
restored 5/5. `volley.py` staggers automatically and warns if any two parked
balls are closer than 1.5 ball diameters.

**Still open:** the rotating-ring hit-test leak above, and whether
`openxr_set_controller_input(auto_release=true, hold_duration=H)` accepts
multi-second values — no longer needed for scheduling, but it would let a throw
be armed and fired without holding the loop.
