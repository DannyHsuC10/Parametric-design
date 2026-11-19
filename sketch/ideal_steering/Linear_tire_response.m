clc; clear;

% 計算函式
%%
function [Fy_f, Fy_r] = tire_linear(alpha_f, alpha_r, Caf, Car)% 線性輪胎模型
    
    Fy_f = Caf * alpha_f;
    Fy_r = Car * alpha_r;

end

function [alpha_f, alpha_r] = slip_angle(vx, vy, omega_yaw, delta, l)% 滑移角計算
% 計算前輪和後輪的滑移角
    % 前輪
    alpha_f = delta - atan((vy + l(1)*omega_yaw) / vx);
    
    % 後輪
    alpha_r = -atan((vy + l(2)*omega_yaw) / vx);
    
    % 轉換成 degree (因為 MF API 用 deg)
    %SA_f = rad2deg(alpha_f);
    %SA_r = rad2deg(alpha_r);

end

function delta = steering_ideal(L, R)% 理想轉向角 (bicycle model)
    % L : 軸距
    % R : 轉彎半徑
    delta = atan(L / R);

end

function [delta_l, delta_r] = steering_ackermann(L, d, R)% 理想Ackermann 轉向角
    % L : 軸距
    % d : 輪距
    % R : 車輛中心轉彎半徑
    
    delta_l = atan(L / (R - d/2));
    delta_r = atan(L / (R + d/2));

end


% 參數
%%
l = [0.775, -0.775];   % [lf, -lr]
L = sum(abs(l));       % 軸距
R = 8.5;
m = 300;
vy = 0;
vx = 10;
d = 1.2;

Caf = 8000;
Car = 8000;


% 1. 理想轉向角

delta = steering_ideal(L, R);

[delta_l, delta_r] = steering_ackermann(L, d, R);

% 2. yaw rate

omega_yaw = vx / R;

vx_l = omega_yaw*(R-d/2);
vx_r = omega_yaw*(R+d/2);

% 3. 滑移角

[alpha_fl, alpha_rl] = slip_angle(vx_l, vy, omega_yaw, delta_l, l);
[alpha_fr, alpha_rr] = slip_angle(vx_r, vy, omega_yaw, delta_r, l);


% 4. 輪胎力

[Fy_fl, Fy_rl] = tire_linear(alpha_fl, alpha_rl, Caf, Car);
[Fy_fr, Fy_rr] = tire_linear(alpha_fr, alpha_rr, Caf, Car);


% 5. 驗證

Fy_total = Fy_fl + Fy_rl + Fy_fr + Fy_rr;
Fy_required = m * vx^2 / R;


% 輸出

fprintf("delta (deg) = %.2f\n", rad2deg(delta));

fprintf("Fy_total = %.2f N\n", Fy_total);
fprintf("Fy_required = %.2f N\n", Fy_required);


%% 掃描轉彎半徑並畫圖
R_range = linspace(3, 30, 100); % 半徑範圍 (m)

delta_l_list = zeros(size(R_range));
delta_r_list = zeros(size(R_range));

for i = 1:length(R_range)
    R_i = R_range(i);
    
    [delta_l, delta_r] = steering_ackermann(L, d, R_i);
    
    delta_l_list(i) = rad2deg(delta_l);
    delta_r_list(i) = rad2deg(delta_r);
end

%% 繪圖
figure;
plot(R_range, delta_l_list, 'LineWidth', 2); hold on;
plot(R_range, delta_r_list, 'LineWidth', 2);

xlabel('Turning Radius R (m)');
ylabel('Steering Angle (deg)');
title('Ackermann Steering Angle vs Turning Radius');

legend('Left Wheel', 'Right Wheel');
grid on;