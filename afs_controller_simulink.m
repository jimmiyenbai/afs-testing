function [yaw_angle_deg, pitch_angle_deg, front_wheel_deg, curvature_1pm, ...
          preview_time_s, preview_distance_m, yaw_target_deg, pitch_body_deg] = ...
          afs_controller_simulink(speed_kmh, steering_wheel_deg, front_height_mm, rear_height_mm, dt, reset)
%#codegen
%AFS_CONTROLLER_SIMULINK Bản Simulink-ready của bộ điều khiển AFS baseline.
%
% Dùng được theo 2 cách:
% 1) Gọi trực tiếp trong MATLAB:
%    [yaw, pitch, fw, kappa, tp, sp, yaw_t, pitch_b] = ...
%       afs_controller_simulink(30, 90, 350, 350, 0.02, false);
%
% 2) Dùng trong MATLAB Function block của Simulink:
%    - Tạo 6 input:
%         speed_kmh, steering_wheel_deg, front_height_mm, rear_height_mm, dt, reset
%    - Tạo 8 output:
%         yaw_angle_deg, pitch_angle_deg, front_wheel_deg, curvature_1pm,
%         preview_time_s, preview_distance_m, yaw_target_deg, pitch_body_deg
%    - Trong block, gọi đúng hàm này.
%
% Input:
%   speed_kmh           : tốc độ xe [km/h]
%   steering_wheel_deg  : góc vô lăng [deg]
%   front_height_mm     : chiều cao trước [mm]
%   rear_height_mm      : chiều cao sau [mm]
%   dt                  : bước thời gian [s]
%   reset               : true để reset trạng thái bộ điều khiển
%
% Output:
%   yaw_angle_deg       : góc quay trái/phải của đèn [deg]
%   pitch_angle_deg     : góc lên/xuống của đèn [deg]
%   front_wheel_deg     : góc bánh trước tương đương [deg]
%   curvature_1pm       : độ cong quỹ đạo [1/m]
%   preview_time_s      : thời gian preview [s]
%   preview_distance_m  : khoảng preview [m]
%   yaw_target_deg      : góc yaw mục tiêu trước rate limit [deg]
%   pitch_body_deg      : góc pitch thân xe [deg]
%
% Thuật toán:
%   Yaw   : steering -> LPF -> bicycle model -> preview -> rate limit -> clamp
%   Pitch : height sensors -> delta_h -> atan2 -> compensate 100%% -> rate limit -> clamp
%

    % ===== Persistent states =====
    persistent steer_lpf_y yaw_cmd pitch_cmd is_initialized

    if isempty(is_initialized)
        steer_lpf_y = 0.0;
        yaw_cmd = 0.0;
        pitch_cmd = 0.0;
        is_initialized = true;
    end

    if reset
        steer_lpf_y = 0.0;
        yaw_cmd = 0.0;
        pitch_cmd = 0.0;
    end

    % ===== Bảo vệ input cơ bản =====
    if dt <= 0.0
        dt = 0.02;
    end

    % ===== Config cố định (có thể sửa sau thành parameter) =====
    steering_ratio = 16.0;
    wheelbase_m = 2.75;
    sensor_base_m = 2.60;

    front_height_ref_mm = 350.0;
    rear_height_ref_mm  = 350.0;

    max_yaw_deg = 15.0;
    min_pitch_deg = -3.0;
    max_pitch_deg = 1.5;
    max_yaw_rate_dps = 18.0;
    max_pitch_rate_dps = 6.0;

    steering_lpf_tau_s = 0.06;

    preview_a_s = 0.09;
    preview_b_s_kmh = 33.689;
    preview_min_s = 0.6;
    preview_max_s = 2.8;

    % ==========================================================
    % 1) NHÁNH YAW
    % ==========================================================
    v_mps = max(speed_kmh, 0.0) / 3.6;

    % LPF bậc 1 cho góc lái
    if steering_lpf_tau_s <= 0.0
        steer_f = steering_wheel_deg;
    else
        alpha = dt / (steering_lpf_tau_s + dt);
        steer_f = alpha * steering_wheel_deg + (1.0 - alpha) * steer_lpf_y;
    end
    steer_lpf_y = steer_f;

    % Góc bánh trước tương đương
    front_wheel_deg = steer_f / steering_ratio;
    front_wheel_rad = deg2rad(front_wheel_deg);

    % Curvature theo kinematic bicycle model
    if abs(front_wheel_rad) < 1.0e-6
        curvature_1pm = 0.0;
    else
        curvature_1pm = tan(front_wheel_rad) / wheelbase_m;
    end

    % Preview time: tp = a + b / V, sau đó clamp
    v_safe = max(speed_kmh, 1.0);
    preview_time_s = preview_a_s + preview_b_s_kmh / v_safe;
    preview_time_s = clamp_scalar(preview_time_s, preview_min_s, preview_max_s);

    % Preview distance
    preview_distance_m = v_mps * preview_time_s;

    % Yaw target
    yaw_target_deg = rad2deg(atan(preview_distance_m * curvature_1pm));
    yaw_target_deg = clamp_scalar(yaw_target_deg, -max_yaw_deg, max_yaw_deg);

    % Rate limit yaw
    yaw_cmd = rate_limit_scalar(yaw_target_deg, yaw_cmd, max_yaw_rate_dps, dt);
    yaw_cmd = clamp_scalar(yaw_cmd, -max_yaw_deg, max_yaw_deg);
    yaw_angle_deg = yaw_cmd;

    % ==========================================================
    % 2) NHÁNH PITCH
    % ==========================================================
    dh_f = front_height_mm - front_height_ref_mm;
    dh_r = rear_height_mm - rear_height_ref_mm;

    delta_h_m = (dh_r - dh_f) / 1000.0;
    pitch_body_deg = rad2deg(atan2(delta_h_m, sensor_base_m));

    % Bù 100%%
    pitch_target_deg = -pitch_body_deg;
    pitch_target_deg = clamp_scalar(pitch_target_deg, min_pitch_deg, max_pitch_deg);

    % Rate limit pitch
    pitch_cmd = rate_limit_scalar(pitch_target_deg, pitch_cmd, max_pitch_rate_dps, dt);
    pitch_cmd = clamp_scalar(pitch_cmd, min_pitch_deg, max_pitch_deg);
    pitch_angle_deg = pitch_cmd;
end

% ===== Helper: clamp =====
function y = clamp_scalar(x, lo, hi)
    y = min(max(x, lo), hi);
end

% ===== Helper: rate limiter =====
function y = rate_limit_scalar(target, current, max_rate, dt)
    max_delta = max_rate * dt;
    delta = target - current;

    if delta > max_delta
        y = current + max_delta;
    elseif delta < -max_delta
        y = current - max_delta;
    else
        y = target;
    end
end
