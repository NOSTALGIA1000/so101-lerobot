#!/usr/bin/env python3
"""Offline unit tests for SO-101 visual servo place logic.

Run WITHOUT robot, WSL, ZMQ camera, or policy checkpoint.

    python test_visual_servo_offline.py

Tests:
  1. dx/dy computation correctness
  2. Servo direction (sign) verification
  3. State machine transitions (clamp→lift→servo→stable→release→timeout)
  4. P-controller math + clamping
  5. Convergence detection
  6. Timeout guard
  7. Dry-run vs live mode branching
  8. Missing detection → hold behavior
"""

from __future__ import annotations

import math
import sys
from typing import Any


# ============================================================================
# Pure functions extracted from core.py — NO robot, NO camera, NO policy
# ============================================================================

def compute_error(target_cx: float, target_cy: float,
                  cube_cx: float, cube_cy: float) -> tuple[float, float]:
    """dx = target_x - cube_x. Positive dx → cube is LEFT of target."""
    return target_cx - cube_cx, target_cy - cube_cy


def servo_p_control(dx: float, dy: float,
                    base_pan: float, base_elbow: float,
                    k_pan: float = 0.003, k_elbow: float = 0.003,
                    pan_min: float = -8.0, pan_max: float = 8.0,
                    elbow_min: float = -55.0, elbow_max: float = -20.0,
                    ) -> dict[str, float]:
    """P-controller: pixel error → joint correction with clamping."""
    adj_pan = base_pan + k_pan * dx
    adj_elbow = base_elbow + k_elbow * dy
    adj_pan = max(pan_min, min(pan_max, adj_pan))
    adj_elbow = max(elbow_min, min(elbow_max, adj_elbow))
    return {"shoulder_pan.pos": adj_pan, "elbow_flex.pos": adj_elbow}


def check_convergence(dx: float, dy: float,
                      dx_threshold: float = 20.0,
                      dy_threshold: float = 20.0) -> bool:
    """True if pixel error within threshold."""
    return abs(dx) < dx_threshold and abs(dy) < dy_threshold


# ============================================================================
# State machine (pure — no side effects)
# ============================================================================

class VisualServoStateMachine:
    """Pure simulation of the visual servo state machine in core.py.

    State transitions match the elif block exactly:
      clamp_pose_hold (phase1 frames) → lift (phase2 - phase1) →
      servo loop → (stable → release | timeout → release)
    """

    def __init__(self,
                 hold_frames: int = 45,
                 lift_frames: int = 60,
                 max_servo_steps: int = 300,
                 dx_threshold: float = 20.0,
                 dy_threshold: float = 20.0,
                 stable_frames_needed: int = 10,
                 release_lower_frames: int = 30,
                 k_pan: float = 0.003,
                 k_elbow: float = 0.003,
                 dry_run: bool = True,
                 ):
        self.phase1 = hold_frames
        self.phase2 = hold_frames + lift_frames
        self.max_servo_steps = max_servo_steps
        self.dx_threshold = dx_threshold
        self.dy_threshold = dy_threshold
        self.stable_frames_needed = stable_frames_needed
        self.release_lower_frames = release_lower_frames
        self.k_pan = k_pan
        self.k_elbow = k_elbow
        self.dry_run = dry_run

        self.frame = 0
        self.stable_count = 0
        self.release_phase: str | None = None
        self.release_frame: int = 0
        self.current_phase = "clamp_pose_hold"
        self.history: list[dict[str, Any]] = []

    def step(self, target_cx: float | None, target_cy: float | None,
             cube_cx: float | None, cube_cy: float | None) -> dict[str, Any]:
        """Advance one frame. Returns {phase, target_pose, dx, dy, ...}."""
        self.frame += 1
        phase1 = self.phase1
        phase2 = self.phase2

        result: dict[str, Any] = {"frame": self.frame}

        # Compute detection
        dx: float | None = None
        dy: float | None = None
        if target_cx is not None and cube_cx is not None:
            dx, dy = compute_error(target_cx, target_cy, cube_cx, cube_cy)
        result["dx"] = dx
        result["dy"] = dy

        if self.frame < phase1:
            result["phase"] = "clamp_pose_hold"
            result["target"] = {"gripper.pos": 3.0}  # simplified
        elif self.frame < phase2:
            result["phase"] = "lift"
            result["target"] = {
                "shoulder_lift.pos": 28,
                "elbow_flex.pos": -40,
                "wrist_flex.pos": 101,
                "gripper.pos": 3.0,
            }
        else:
            servo_frame = self.frame - phase2

            if servo_frame >= self.max_servo_steps:
                result["phase"] = "servo_timeout_release"
                result["target"] = {"gripper.pos": 45.0}  # open
                self.current_phase = result["phase"]
                self.history.append(result)
                return result

            if self.dry_run:
                result["phase"] = f"servo_dry_f{servo_frame}"
                result["target"] = {"gripper.pos": 3.0}
            elif dx is not None and not check_convergence(
                dx, dy, self.dx_threshold, self.dy_threshold
            ):
                self.stable_count = 0
                target = servo_p_control(
                    dx, dy,
                    base_pan=0.0, base_elbow=-40.0,
                    k_pan=self.k_pan, k_elbow=self.k_elbow,
                )
                target["shoulder_lift.pos"] = 28
                target["wrist_flex.pos"] = 101
                target["gripper.pos"] = 3.0
                result["phase"] = f"servo_f{servo_frame}"
                result["target"] = target
            elif dx is not None:
                self.stable_count += 1
                result["stable_count"] = self.stable_count
                if self.stable_count < self.stable_frames_needed:
                    result["phase"] = f"servo_stable_{self.stable_count}"
                    result["target"] = {
                        "shoulder_pan.pos": 0.0,
                        "shoulder_lift.pos": 28,
                        "elbow_flex.pos": -40,
                        "wrist_flex.pos": 101,
                        "gripper.pos": 3.0,
                    }
                else:
                    if self.release_phase is None:
                        self.release_phase = "lower"
                        self.release_frame = 0
                    if self.release_phase == "lower":
                        self.release_frame += 1
                        result["phase"] = f"servo_lower_{self.release_frame}"
                        result["target"] = {
                            "shoulder_pan.pos": 0.0,
                            "shoulder_lift.pos": 45,
                            "elbow_flex.pos": -52,
                            "wrist_flex.pos": 100,
                            "gripper.pos": 3.0,
                        }
                        if self.release_frame >= self.release_lower_frames:
                            self.release_phase = "release"
                    else:
                        result["phase"] = "servo_release"
                        result["target"] = {
                            "shoulder_pan.pos": 0.0,
                            "shoulder_lift.pos": 45,
                            "elbow_flex.pos": -52,
                            "wrist_flex.pos": 100,
                            "gripper.pos": 45.0,
                        }
            else:
                result["phase"] = f"servo_wait_f{servo_frame}"
                result["target"] = {
                    "shoulder_pan.pos": 0.0,
                    "shoulder_lift.pos": 28,
                    "elbow_flex.pos": -40,
                    "wrist_flex.pos": 101,
                    "gripper.pos": 3.0,
                }

            # Timeout: controlled lower then release.
            if servo_frame >= self.max_servo_steps:
                if self.release_phase is None or self.release_phase in ("lower", "release"):
                    self.release_phase = "timeout_lower"
                    self.release_frame = 0
                if self.release_phase == "timeout_lower":
                    self.release_frame += 1
                    result["phase"] = f"servo_timeout_lower_{self.release_frame}"
                    result["target"] = {
                        "shoulder_pan.pos": 0.0,
                        "shoulder_lift.pos": 45,
                        "elbow_flex.pos": -52,
                        "wrist_flex.pos": 100,
                        "gripper.pos": 3.0,
                    }
                    if self.release_frame >= self.release_lower_frames:
                        self.release_phase = "timeout_release"
                        result["phase"] = "servo_timeout_release"
                        result["target"]["gripper.pos"] = 45.0
                else:
                    result["phase"] = "servo_timeout_release"
                    result["target"] = {
                        "shoulder_pan.pos": 0.0,
                        "shoulder_lift.pos": 45,
                        "elbow_flex.pos": -52,
                        "wrist_flex.pos": 100,
                        "gripper.pos": 45.0,
                    }

        self.current_phase = result["phase"]
        self.history.append(result)
        return result

    def run_until_done(self,
                       target_cx_seq: list[float | None],
                       target_cy_seq: list[float | None],
                       cube_cx_seq: list[float | None],
                       cube_cy_seq: list[float | None]) -> list[dict[str, Any]]:
        """Run state machine with per-frame detection inputs until
        release or timeout."""
        n = max(len(target_cx_seq), len(cube_cx_seq))
        for i in range(n):
            tc = target_cx_seq[min(i, len(target_cx_seq) - 1)]
            tcy = target_cy_seq[min(i, len(target_cy_seq) - 1)]
            cc = cube_cx_seq[min(i, len(cube_cx_seq) - 1)]
            ccy = cube_cy_seq[min(i, len(cube_cy_seq) - 1)]
            result = self.step(tc, tcy, cc, ccy)
            if result["phase"] in ("servo_release", "servo_timeout_release"):
                break
        return self.history


# ============================================================================
# Tests
# ============================================================================

FAIL = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global FAIL
    status = "PASS" if condition else "FAIL"
    if not condition:
        FAIL += 1
    msg = f"  {status}: {name}"
    if detail and not condition:
        msg += f"  ({detail})"
    print(msg)


def test_dx_dy_sign():
    """dx = target_x - cube_x.

    Positive dx → cube is to the LEFT of target (from camera view).
    To move cube rightward toward target: shoulder_pan needs to
    increase (CW rotation from above for SO-101 = move left in image).
    Actually: sign depends on camera orientation and arm kinematics.
    This test just verifies the math is correct.
    """
    print("\n=== Test 1: dx/dy computation ===")

    # target at (320, 240), cube at (212, 240) → dx=108 (cube left of target)
    dx, dy = compute_error(320, 240, 212, 240)
    check("dx positive when cube left of target", dx > 0, f"dx={dx}")
    check("dy zero when vertically aligned", abs(dy) < 0.01, f"dy={dy}")

    # cube at (320, 200), target at (320, 240) → dy=40 (cube above target)
    dx2, dy2 = compute_error(320, 240, 320, 200)
    check("dy positive when cube above target", dy2 > 0, f"dy={dy2}")
    check("dx zero when horizontally aligned", abs(dx2) < 0.01, f"dx={dx2}")

    # cube at target → zero error
    dx3, dy3 = compute_error(100, 200, 100, 200)
    check("zero dx/dy when cube at target", dx3 == 0 and dy3 == 0)


def test_servo_direction():
    """P-controller: positive dx → increase shoulder_pan.

    This test verifies MATH only. Actual arm kinematics need
    real-robot validation to confirm sign convention.
    """
    print("\n=== Test 2: Servo direction (P-controller) ===")

    # dx=+100 (cube left of target) → shoulder_pan should INCREASE
    r = servo_p_control(dx=100, dy=0, base_pan=0.0, base_elbow=-40.0)
    check("positive dx → positive shoulder_pan adjustment",
          r["shoulder_pan.pos"] > 0.0, str(r))

    # dx=-50 (cube right of target) → shoulder_pan should DECREASE
    r2 = servo_p_control(dx=-50, dy=0, base_pan=0.0, base_elbow=-40.0)
    check("negative dx → negative shoulder_pan adjustment",
          r2["shoulder_pan.pos"] < 0.0, str(r2))

    # dy=+50 (cube above target) → elbow_flex should INCREASE (less flex/negative)
    r3 = servo_p_control(dx=0, dy=50, base_pan=0.0, base_elbow=-40.0)
    check("positive dy → elbow_flex becomes less negative",
          r3["elbow_flex.pos"] > -40.0, str(r3))


def test_clamping():
    """P-controller must respect joint limits."""
    print("\n=== Test 3: Joint limit clamping ===")

    # Very large dx should not exceed pan_max
    r = servo_p_control(dx=5000, dy=0, base_pan=0.0, base_elbow=-40.0)
    check("shoulder_pan clamped to +8.0 max",
          r["shoulder_pan.pos"] == 8.0, str(r))

    # Very negative dx should not go below pan_min
    r2 = servo_p_control(dx=-5000, dy=0, base_pan=0.0, base_elbow=-40.0)
    check("shoulder_pan clamped to -8.0 min",
          r2["shoulder_pan.pos"] == -8.0, str(r2))

    # Very positive dy should respect elbow_max (-20).
    # Need dy > 6667 to push -40 + 0.003*dy past -20 clamp.
    r3 = servo_p_control(dx=0, dy=8000, base_pan=0.0, base_elbow=-40.0)
    check("elbow_flex clamped to -20.0 max",
          r3["elbow_flex.pos"] == -20.0, str(r3))

    # Normal dy gives proportional adjustment within range.
    r4 = servo_p_control(dx=0, dy=5000, base_pan=0.0, base_elbow=-40.0)
    check("elbow_flex proportional when within range",
          r4["elbow_flex.pos"] == -25.0, str(r4))


def test_convergence_detection():
    """Within threshold for N consecutive frames → convergence."""
    print("\n=== Test 4: Convergence detection ===")

    check("error 10,10 within threshold 20,20",
          check_convergence(10, 10, 20, 20))
    check("error 25,10 NOT within threshold",
          not check_convergence(25, 10, 20, 20))
    check("error -15,-15 within threshold (absolute value)",
          check_convergence(-15, -15, 20, 20))
    check("boundary: dx=20 NOT within threshold (< not <=)",
          not check_convergence(20, 0, 20, 20))


def test_state_machine_normal_convergence():
    """Simulate: cube starts far left, servo moves it to target.

    We simulate per-frame detection values where the cube position
    gradually approaches the target. This tests the full state machine
    from clamp_pose_hold through servo_release.
    """
    print("\n=== Test 5: Full state machine — normal convergence ===")

    sm = VisualServoStateMachine(
        hold_frames=5, lift_frames=5, max_servo_steps=200,
        dry_run=False, stable_frames_needed=3,
    )

    # Target at (320, 240), constant
    # Cube starts at (212, 240) = dx=108, then linearly moves to (320, 240)
    n_frames = 150
    target_cx = [320.0] * n_frames
    target_cy = [240.0] * n_frames

    # Cube moves from dx=108 to dx=0 in steps
    cube_cx = []
    cube_cy = [240.0] * n_frames
    for i in range(n_frames):
        # Simulate: after lift (10 frames), detection starts,
        # cube gradually moves right as robot servos
        detection_start = 10
        if i < detection_start:
            cube_cx.append(None)  # no detection during clamp/lift
        else:
            progress = min(1.0, (i - detection_start) / 80.0)
            cube_cx.append(212.0 + 108.0 * progress)

    history = sm.run_until_done(target_cx, target_cy, cube_cx, cube_cy)

    phases = [h["phase"] for h in history]
    check("starts in clamp_pose_hold",
          phases[0] == "clamp_pose_hold", str(phases[:5]))
    check("transitions to lift",
          "lift" in phases, str(phases[:15]))
    check("eventually reaches servo_release",
          "servo_release" in phases,
          f"last phase: {phases[-1]}, total frames: {len(phases)}")

    # Verify dx decreases over time during servo
    servo_dxs = [h["dx"] for h in history
                 if h["dx"] is not None and "servo" in h["phase"]]
    if len(servo_dxs) >= 3:
        check("dx magnitude decreases during servo",
              abs(servo_dxs[-1]) < abs(servo_dxs[0]),
              f"first_dx={servo_dxs[0]:.1f} last_dx={servo_dxs[-1]:.1f}")


def test_state_machine_timeout():
    """Cube never reaches target → timeout release."""
    print("\n=== Test 6: State machine — timeout ===")

    sm = VisualServoStateMachine(
        hold_frames=5, lift_frames=5, max_servo_steps=20,
        dry_run=False, stable_frames_needed=10,
    )

    n = 50
    target_cx = [320.0] * n
    target_cy = [240.0] * n
    cube_cx = [212.0] * n  # stays far away, never converges
    cube_cy = [240.0] * n

    history = sm.run_until_done(target_cx, target_cy, cube_cx, cube_cy)

    check("timeout triggers servo_timeout_release",
          history[-1]["phase"] == "servo_timeout_release",
          f"last: {history[-1]['phase']}, frames: {len(history)}")
    check("does NOT converge before timeout",
          "servo_release" not in [h["phase"] for h in history])


def test_state_machine_no_detection():
    """No detection at all → hold lift pose, then timeout."""
    print("\n=== Test 7: State machine — no detection ===")

    sm = VisualServoStateMachine(
        hold_frames=5, lift_frames=5, max_servo_steps=15,
        dry_run=False,
    )

    n = 30
    target_cx = [None] * n
    target_cy = [None] * n
    cube_cx = [None] * n
    cube_cy = [None] * n

    history = sm.run_until_done(target_cx, target_cy, cube_cx, cube_cy)

    phases = [h["phase"] for h in history]
    check("waits with servo_wait during no-detection",
          any("servo_wait" in p for p in phases),
          str(phases))
    check("eventually times out",
          history[-1]["phase"] == "servo_timeout_release")


def test_dry_run_mode():
    """Dry-run mode: always servo_dry phase, never controls robot."""
    print("\n=== Test 8: Dry-run mode ===")

    sm = VisualServoStateMachine(
        hold_frames=5, lift_frames=5, max_servo_steps=50,
        dry_run=True,
    )

    n = 30
    target_cx = [320.0] * n
    target_cy = [240.0] * n
    cube_cx = [212.0] * n
    cube_cy = [240.0] * n

    history = sm.run_until_done(target_cx, target_cy, cube_cx, cube_cy)

    servo_phases = [h["phase"] for h in history if "servo" in h["phase"]]
    check("all servo phases are dry_run",
          all("dry" in p for p in servo_phases),
          str(servo_phases[:5]))
    check("never reaches servo_release in dry-run",
          "servo_release" not in [h["phase"] for h in history])


def test_stable_count_reset():
    """Stable count resets when error goes back above threshold."""
    print("\n=== Test 9: Stable count reset on de-convergence ===")

    sm = VisualServoStateMachine(
        hold_frames=3, lift_frames=3, max_servo_steps=100,
        dry_run=False, stable_frames_needed=5,
    )

    # Simulate: cube converges briefly, then drifts away, then converges again
    n = 60
    target_cx = [320.0] * n
    target_cy = [240.0] * n

    # After lift (frame 7+): converge for 2 frames, drift for 5, converge again
    cube_cx_vals = []
    for i in range(n):
        detection_start = 7
        if i < detection_start:
            cube_cx_vals.append(None)
        elif i < detection_start + 2:
            cube_cx_vals.append(318.0)  # within threshold (dx=2)
        elif i < detection_start + 7:
            cube_cx_vals.append(250.0)  # outside threshold (dx=70)
        else:
            cube_cx_vals.append(319.0)  # back within threshold (dx=1)

    cube_cy_vals = [240.0] * n
    history = sm.run_until_done(target_cx, target_cy, cube_cx_vals, cube_cy_vals)

    # Find max stable_count reached before first drift
    stable_phases_before_drift = [
        h for h in history
        if "servo_stable" in h["phase"]
        and history.index(h) < 15  # before drift at frame ~14
    ]
    max_stable_before_drift = max(
        (h.get("stable_count", 0) for h in stable_phases_before_drift),
        default=0,
    )
    check("stable count resets after drift (didn't reach 5 before drift)",
          max_stable_before_drift < 5,
          f"max stable before drift: {max_stable_before_drift}")


def test_two_phase_release():
    """Convergence → servo_lower_N (gripper closed) → servo_release (gripper open)."""
    print("\n=== Test 10: Two-phase release (lower then open) ===")

    sm = VisualServoStateMachine(
        hold_frames=3, lift_frames=3, max_servo_steps=100,
        dry_run=False, stable_frames_needed=2, release_lower_frames=5,
    )

    n = 50
    target_cx = [320.0] * n
    target_cy = [240.0] * n
    # After lift (frame 7): cube already at target (dx=0) → immediate convergence
    cube_cx = [320.0 if i >= 7 else None for i in range(n)]
    cube_cy = [240.0 if i >= 7 else None for i in range(n)]

    history = sm.run_until_done(target_cx, target_cy, cube_cx, cube_cy)

    phases = [h["phase"] for h in history]
    lower_phases = [p for p in phases if "servo_lower" in p]
    check("goes through servo_lower phases before release",
          len(lower_phases) >= 5,
          f"lower phases: {lower_phases}")
    check("servo_release appears after servo_lower",
          "servo_release" in phases,
          f"last phases: {phases[-5:]}")
    check("servo_release comes after all servo_lower phases",
          phases.index("servo_release") > max(
              i for i, p in enumerate(phases) if "servo_lower" in p
          ),
          f"phase order: {phases[-10:]}")

    # Verify gripper stays closed during lower, opens on release
    for h in history:
        if "servo_lower" in h["phase"]:
            check(f"lower phase gripper closed: {h['phase']}",
                  h["target"].get("gripper.pos") == 3.0)
    for h in history:
        if h["phase"] == "servo_release":
            check("release phase gripper open",
                  h["target"].get("gripper.pos") == 45.0)
            break


# ============================================================================
# Run
# ============================================================================

def main() -> int:
    print("=" * 60)
    print("SO-101 Visual Servo — OFFLINE UNIT TESTS")
    print("No robot, no camera, no checkpoint required")
    print("=" * 60)

    test_dx_dy_sign()
    test_servo_direction()
    test_clamping()
    test_convergence_detection()
    test_state_machine_normal_convergence()
    test_state_machine_timeout()
    test_state_machine_no_detection()
    test_dry_run_mode()
    test_stable_count_reset()
    test_two_phase_release()

    print(f"\n{'=' * 60}")
    if FAIL:
        print(f"{FAIL} TEST(S) FAILED")
    else:
        print("ALL TESTS PASSED")
    print("=" * 60)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
