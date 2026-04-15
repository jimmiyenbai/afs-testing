"""
AFS Controller
================================
Phiên bản gọn cho demo mô phỏng.

Pipeline:
  Yaw:  steering → LPF → bicycle model → preview → rate limiter → clamp
  Pitch: height sensors → Δh → atan2 → bù 100% → rate limiter → clamp

Input:  speed_kmh, steering_wheel_deg, front_height_mm, rear_height_mm, dt
Output: yaw_angle_deg, pitch_angle_deg

Quy ước dấu:
  steering_wheel_deg : (+) phải, (−) trái
  yaw_angle_deg      : (+) đèn xoay phải, (−) xoay trái
  pitch_angle_deg    : (+) đèn ngẩng lên, (−) chúc xuống

Tham khảo:
  [1] ECE R123 — giới hạn swivel ±15°, rate ≤ 18°/s
  [2] Ishiguro & Yamada, SAE 2004-01-0441 — preview time
  [3] Rajamani, Vehicle Dynamics and Control, 2012 — bicycle model
"""

import math
from dataclasses import dataclass
from typing import Tuple


# ── Cấu hình ────────────────────────────────────────────────

@dataclass
class AFSConfig:
    # Hình học xe (sedan hạng C)
    steering_ratio: float = 16.0        # tỷ số lái
    wheelbase_m: float = 2.75           # chiều dài cơ sở [m]
    sensor_base_m: float = 2.60         # khoảng cách 2 cảm biến chiều cao [m]

    # Chiều cao tham chiếu (tải trọng chuẩn)
    front_height_ref_mm: float = 350.0
    rear_height_ref_mm: float = 350.0

    # Giới hạn actuator [ECE R123]
    max_yaw_deg: float = 15.0
    min_pitch_deg: float = -3.0
    max_pitch_deg: float = 1.5
    max_yaw_rate_dps: float = 18.0      # tốc độ quay đèn tối đa
    max_pitch_rate_dps: float = 6.0

    # LPF góc lái
    steering_lpf_tau_s: float = 0.06    # τ = 60ms

    # Preview time: tₚ = a + b/V, clamp [min, max]
    preview_a_s: float = 0.09
    preview_b_s_kmh: float = 33.689
    preview_min_s: float = 0.6
    preview_max_s: float = 2.8

    def __post_init__(self):
        positive_fields = (
            "steering_ratio",
            "wheelbase_m",
            "sensor_base_m",
            "front_height_ref_mm",
            "rear_height_ref_mm",
            "max_yaw_deg",
            "max_yaw_rate_dps",
            "max_pitch_rate_dps",
            "preview_min_s",
            "preview_max_s",
        )
        nonnegative_fields = (
            "steering_lpf_tau_s",
            "preview_a_s",
            "preview_b_s_kmh",
        )

        for field_name in positive_fields:
            value = getattr(self, field_name)
            if value <= 0:
                raise ValueError(f"{field_name} must be > 0")

        for field_name in nonnegative_fields:
            value = getattr(self, field_name)
            if value < 0:
                raise ValueError(f"{field_name} must be >= 0")

        if self.min_pitch_deg > self.max_pitch_deg:
            raise ValueError("min_pitch_deg must be <= max_pitch_deg")
        if self.preview_min_s > self.preview_max_s:
            raise ValueError("preview_min_s must be <= preview_max_s")


# ── Bộ lọc bậc 1 ────────────────────────────────────────────

class LPF:
    """y[n] = α·x[n] + (1−α)·y[n−1], α = dt/(τ+dt)"""
    def __init__(self, tau_s: float):
        self.tau = tau_s
        self.y = 0.0

    def update(self, x: float, dt: float) -> float:
        if self.tau <= 0:
            self.y = x
        else:
            a = dt / (self.tau + dt)
            self.y = a * x + (1 - a) * self.y
        return self.y

    def reset(self, val: float = 0.0):
        self.y = val


# ── Hàm tiện ích ─────────────────────────────────────────────

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def rate_limit(target: float, current: float, max_rate: float, dt: float) -> float:
    mx = max_rate * dt
    d = target - current
    if d > mx: return current + mx
    if d < -mx: return current - mx
    return target


# ── Controller ───────────────────────────────────────────────

@dataclass
class AFSOutput:
    yaw_angle_deg: float
    pitch_angle_deg: float
    # Debug — biến cốt lõi
    front_wheel_deg: float
    curvature_1pm: float
    preview_time_s: float
    preview_distance_m: float
    yaw_target_deg: float
    pitch_body_deg: float
    dh_front_mm: float
    dh_rear_mm: float
    pitch_target_deg: float


class AFSController:
    """
    AFS baseline controller.

    Sử dụng:
        afs = AFSController()
        out = afs.update(speed_kmh=40, steering_wheel_deg=120,
                         front_height_mm=350, rear_height_mm=360, dt=0.02)
        print(out.yaw_angle_deg, out.pitch_angle_deg)
    """

    def __init__(self, cfg: AFSConfig = None):
        self.cfg = cfg or AFSConfig()
        self._steer_lpf = LPF(self.cfg.steering_lpf_tau_s)
        self._yaw_cmd = 0.0
        self._pitch_cmd = 0.0

    def reset(self):
        self._steer_lpf.reset()
        self._yaw_cmd = 0.0
        self._pitch_cmd = 0.0

    def evaluate_static(
        self,
        speed_kmh: float,
        steering_wheel_deg: float,
        front_height_mm: float,
        rear_height_mm: float,
        dt: float = 0.02,
        settle_time_s: float = 1.0,
    ) -> AFSOutput:
        """
        Reset state and run enough update steps for a one-shot/static evaluation.

        This keeps dashboard requests and CLI demo cases on the same code path.
        """
        if dt <= 0:
            raise ValueError("dt must be > 0")
        if settle_time_s < 0:
            raise ValueError("settle_time_s must be >= 0")

        self.reset()
        steps = max(1, math.ceil(settle_time_s / dt))
        out = None

        for _ in range(steps):
            out = self.update(
                speed_kmh=speed_kmh,
                steering_wheel_deg=steering_wheel_deg,
                front_height_mm=front_height_mm,
                rear_height_mm=rear_height_mm,
                dt=dt,
            )

        return out

    def update(
        self,
        speed_kmh: float,
        steering_wheel_deg: float,
        front_height_mm: float,
        rear_height_mm: float,
        dt: float = 0.02,
    ) -> AFSOutput:

        c = self.cfg
        v_mps = max(speed_kmh, 0.0) / 3.6

        # ═══ NHÁNH YAW ═══

        # 1) Lọc góc lái
        steer_f = self._steer_lpf.update(steering_wheel_deg, dt)

        # 2) Góc bánh trước (bicycle model)
        front_wheel_deg = steer_f / c.steering_ratio
        front_wheel_rad = math.radians(front_wheel_deg)

        # 3) Curvature
        if abs(front_wheel_rad) < 1e-6:
            kappa = 0.0
        else:
            kappa = math.tan(front_wheel_rad) / c.wheelbase_m

        # 4) Preview time
        v_safe = max(speed_kmh, 1.0)
        tp_raw = c.preview_a_s + c.preview_b_s_kmh / v_safe
        tp = clamp(tp_raw, c.preview_min_s, c.preview_max_s)

        # 5) Preview yaw
        preview_dist = v_mps * tp
        yaw_target = math.degrees(math.atan(preview_dist * kappa))
        yaw_target = clamp(yaw_target, -c.max_yaw_deg, c.max_yaw_deg)

        # 6) Rate limiter + clamp
        self._yaw_cmd = rate_limit(yaw_target, self._yaw_cmd, c.max_yaw_rate_dps, dt)
        self._yaw_cmd = clamp(self._yaw_cmd, -c.max_yaw_deg, c.max_yaw_deg)

        # ═══ NHÁNH PITCH ═══

        # 1) Chênh lệch chiều cao so với tham chiếu
        dh_f = front_height_mm - c.front_height_ref_mm
        dh_r = rear_height_mm - c.rear_height_ref_mm

        # 2) Pitch thân xe
        delta_h_m = (dh_r - dh_f) / 1000.0
        pitch_body = math.degrees(math.atan2(delta_h_m, c.sensor_base_m))

        # 3) Bù 100%: xe ngẩng → đèn chúc
        pitch_target = -pitch_body
        pitch_target = clamp(pitch_target, c.min_pitch_deg, c.max_pitch_deg)

        # 4) Rate limiter + clamp
        self._pitch_cmd = rate_limit(pitch_target, self._pitch_cmd, c.max_pitch_rate_dps, dt)
        self._pitch_cmd = clamp(self._pitch_cmd, c.min_pitch_deg, c.max_pitch_deg)

        return AFSOutput(
            yaw_angle_deg=round(self._yaw_cmd, 3),
            pitch_angle_deg=round(self._pitch_cmd, 3),
            front_wheel_deg=round(front_wheel_deg, 3),
            curvature_1pm=round(kappa, 6),
            preview_time_s=round(tp, 3),
            preview_distance_m=round(preview_dist, 2),
            yaw_target_deg=round(yaw_target, 3),
            pitch_body_deg=round(pitch_body, 4),
            dh_front_mm=round(dh_f, 2),
            dh_rear_mm=round(dh_r, 2),
            pitch_target_deg=round(pitch_target, 4),
        )


# ── Demo ─────────────────────────────────────────────────────

if __name__ == "__main__":
    afs = AFSController()

    print("=" * 80)
    print("DEMO — AFS Controller")
    print("=" * 80)

    cases = [
        ("Đi thẳng 60 km/h",           60,    0,  350, 350),
        ("Nội thành, rẽ phải vừa",      40,   20,  350, 350),
        ("Nội thành, rẽ trái gắt",      40, -40,  350, 350),
        ("Cao tốc, chỉnh làn",           100,   8,  350, 350),
        ("Tải nặng phía sau",           50,   0,  345, 370),
        ("Phanh gấp (đầu xe chúi)",     50,   0,  365, 340),
        ("Đỗ xe, cua rất gấp",          3,   220,  350, 350),
    ]

    print(f"\n{'Tình huống':<30} {'v':>5} {'δ_sw':>7} {'yaw':>8} {'pitch':>8} {'tₚ':>6} {'κ':>10}")
    print("-" * 80)

    for name, v, sw, hf, hr in cases:
        out = afs.evaluate_static(v, sw, hf, hr, dt=0.02)
        print(f"{name:<30} {v:>5} {sw:>+7} {out.yaw_angle_deg:>+8.3f} "
              f"{out.pitch_angle_deg:>+8.3f} {out.preview_time_s:>6.3f} "
              f"{out.curvature_1pm:>+10.6f}")

    # Demo chuỗi thời gian: vào cua → ra cua
    print("\n" + "=" * 80)
    print("CHUỖI THỜI GIAN: vào cua → giữa cua → ra cua")
    print("=" * 80)

    afs.reset()
    dt = 0.05
    # [v, steering, h_front, h_rear]
    sequence = [
        (40,   0, 350, 350),  # đi thẳng
        (40,  30, 350, 350),  # bắt đầu vào cua
        (40,  80, 350, 350),  # vào sâu
        (35, 140, 350, 352),  # giữa cua, giảm tốc nhẹ
        (35, 160, 350, 354),  # cua gấp nhất
        (35, 160, 350, 354),  # giữ cua
        (40, 120, 350, 352),  # bắt đầu ra cua
        (45,  60, 350, 350),  # ra gần thẳng
        (50,  10, 350, 350),  # gần thẳng
        (50,   0, 350, 350),  # đi thẳng
    ]

    print(f"\n{'t':>5} {'v':>5} {'δ_sw':>7} {'yaw':>8} {'pitch':>8} {'tₚ':>6}")
    print("-" * 50)

    for i, (v, sw, hf, hr) in enumerate(sequence):
        out = afs.update(v, sw, hf, hr, dt=dt)
        print(f"{i*dt:>5.2f} {v:>5} {sw:>+7} {out.yaw_angle_deg:>+8.3f} "
              f"{out.pitch_angle_deg:>+8.3f} {out.preview_time_s:>6.3f}")
