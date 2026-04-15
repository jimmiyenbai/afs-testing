# AFS Controller

## 1. Mục đích

Bộ code này mô phỏng thuật toán điều khiển cơ bản cho **hệ thống đèn pha thích nghi AFS (Adaptive Front-lighting System)**.

Mục tiêu:

- Demo mô phỏng trực quan qua dashboard web
- Sinh dữ liệu cho bài toán machine learning
- Kiểm tra nhanh ảnh hưởng của tốc độ, góc lái, tải trọng lên góc đèn

**Câu hỏi mà controller trả lời:**

> Với tốc độ xe, góc vô lăng, chiều cao trước/sau — đèn nên xoay trái/phải bao nhiêu độ và ngẩng/chúc bao nhiêu độ

---

## 2. Quy ước dấu

| Biến | Dương (+) | Âm (−) | Đơn vị |
|------|-----------|--------|--------|
| `steering_wheel_deg` | Quay phải (CW nhìn từ trên) | Quay trái (CCW) | deg |
| `yaw_angle_deg` | Đèn xoay phải → chiếu vào cua phải | Đèn xoay trái | deg |
| `pitch_angle_deg` | Đèn ngẩng lên | Đèn chúc xuống | deg |
| `front/rear_height_mm` | Gầm xe cao (xe nhấc lên) | — (không âm) | mm |

---

## 3. Cấu trúc thư mục

```
AFS_Project/
├── afs.py
├── app.py
├── afs_controller_simulink.m
├── afs.slx
├── README.md
└── requirements.txt
```


---

## 4. Sơ đồ khối

### 4.1. Nhánh ngang — Yaw

```
steering_wheel_deg
       │
  [LPF τ=60ms]
       │
  δ_f = δ_sw / i_s          (i_s = 16)
       │
  κ = tan(δ_f) / L          (L = 2.75 m)
       │
  tₚ = clamp(0.09 + 33.689/V, 0.6, 2.8)
       │
  θ = atan(v · tₚ · κ)
       │
  [Rate limiter ≤ 18°/s]
       │
  [Clamp ±15°]
       │
  yaw_angle_deg → OUTPUT
```

### 4.2. Nhánh dọc — Pitch

```
front_height_mm ──┐
                   ├─→ Δh = (h_r − h_f) − (h_r_ref − h_f_ref)
rear_height_mm  ──┘
                         │
               pitch_body = atan2(Δh/1000, L_sensor)
                         │
               pitch_đèn = −pitch_body    (bù 100%)
                         │
               [Rate limiter ≤ 6°/s]
                         │
               [Clamp −3° … +1.5°]
                         │
               pitch_angle_deg → OUTPUT
```

---

## 5. Chi tiết thuật toán

### 5.1. Nhánh ngang (Yaw)

**Bước 1 — Lọc góc vô lăng.**
Bộ lọc thông thấp bậc 1 dùng hằng số thời gian τ = 60 ms. Tần số cắt f_c = 1/(2πτ) không đổi khi sample rate thay đổi.

**Bước 2 — Góc bánh trước.**
δ_f = δ_sw / i_s, trong đó i_s = 16 là tỷ số lái.

**Bước 3 — Curvature từ bicycle model.**
κ = tan(δ_f) / L, với L = 2.75 m là chiều dài cơ sở.

**Bước 4 — Preview time.**
tₚ = 0.09 + 33.689/V [s], clamp vào [0.6, 2.8]. Công thức từ Ishiguro & Yamada (SAE 2004-01-0441).

**Bước 5 — Góc xoay đèn.**
θ_yaw = atan(v · tₚ · κ), clamp vào ±15°.

**Bước 6 — Rate limiter.**
Giới hạn tốc độ quay đèn ≤ 18°/s (tham khảo ECE R123).

### 5.2. Nhánh dọc (Pitch)

**Bước 1 — Chênh lệch chiều cao.**
Δh_front = h_f − h_f_ref, Δh_rear = h_r − h_r_ref.

**Bước 2 — Pitch thân xe.**
pitch_body = atan2((Δh_rear − Δh_front)/1000, L_sensor), với L_sensor = 2.60 m.

**Bước 3 — Pitch đèn.**
pitch_đèn = −pitch_body (bù 100%). Dấu âm: xe ngẩng đầu → đèn phải chúc xuống.

**Bước 4 — Rate limiter.**
Giới hạn tốc độ ≤ 6°/s, biên độ −3° đến +1.5° (ECE R48).

---

## 6. Cấu trúc output

```python
@dataclass
class AFSOutput:
    yaw_angle_deg: float       # Góc xoay đèn [deg]
    pitch_angle_deg: float     # Góc ngẩng/chúc đèn [deg]
    front_wheel_deg: float     # Góc bánh trước [deg]
    curvature_1pm: float       # Curvature [1/m]
    preview_time_s: float      # Thời gian nhìn trước [s]
    preview_distance_m: float  # Khoảng cách nhìn trước [m]
    yaw_target_deg: float      # Yaw trước rate limiter [deg]
    pitch_body_deg: float      # Pitch thân xe [deg]
    dh_front_mm: float         # Δh trước so với ref [mm]
    dh_rear_mm: float          # Δh sau so với ref [mm]
    pitch_target_deg: float    # Pitch trước rate limiter [deg]
```

---

## 7. Dashboard

Dashboard web hiển thị realtime:

- **Preset buttons** — 8 tình huống lái xe, bấm là slider nhảy đúng giá trị
- **Input sliders** — tốc độ, vô lăng, chiều cao trước/sau
- **Nhìn trên (Yaw)** — chùm sáng hình quạt xoay theo góc đèn, hiển thị góc
- **Nhìn ngang (Pitch)** — xe nghiêng theo tải trọng, chùm sáng bù ngược
- **Debug Yaw** — curvature, preview time, bán kính cua, tốc độ
- **Debug Pitch** — Δh trước/sau, pitch thân xe, pitch target, pitch output

---


## 8. Tham số cấu hình

| Tham số | Giá trị | Đơn vị | Nguồn |
|---------|---------|--------|-------|
| Tỷ số lái (i_s) | 16.0 | — | Mitschke & Wallentowitz 2014 |
| Chiều dài cơ sở (L) | 2.75 | m | Sedan hạng C |
| Khoảng cách cảm biến | 2.60 | m | — |
| Chiều cao ref trước | 350 | mm | Tải trọng chuẩn |
| Chiều cao ref sau | 350 | mm | Tải trọng chuẩn |
| Giới hạn yaw | ±15 | deg | ECE R123 |
| Giới hạn pitch | −3 … +1.5 | deg | ECE R48 |
| Rate limit yaw | 18 | deg/s | ECE R123 |
| Rate limit pitch | 6 | deg/s | ECE R48 |
| LPF τ góc lái | 60 | ms | — |
| Preview a | 0.09 | s | Ishiguro 2004 |
| Preview b | 33.689 | s·km/h | Ishiguro 2004 |
| Preview min | 0.6 | s | — |
| Preview max | 2.8 | s | — |

---


## 9. Tài liệu tham khảo

| # | Nguồn | Nội dung |
|---|-------|----------|
| [1] | ECE R123 — Adaptive Front-lighting Systems | Giới hạn swivel, tốc độ quay |
| [2] | ECE R48 — Installation of lighting devices | Auto-leveling cho đèn projector |
| [3] | Ishiguro K., Yamada K. — SAE 2004-01-0441 | Preview time: tₚ = a + b/V |
| [4] | Rajamani R. — Vehicle Dynamics and Control, 2012 | Bicycle model (chương 2–3) |
| [5] | Gao Z., Li Y. — Math. Probl. Eng. 2014 | AFS dựa trên hành vi nhìn trước |
| [6] | De Santos-Berbel C., Castro M. — Math. Comput. Simul. 2020 | Hàm xoay đèn tối ưu |
