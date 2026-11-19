%% Linear Bicycle Model - Dynamic Response
clc; clear; close all;

function dx = bicycle_ode(t, x, delta_fun, vx, m, Iz, lf, lr, Cf, Cr)

    vy = x(1);
    r  = x(2);

    delta = delta_fun(t);

    % =========================
    % Slip angles
    % =========================
    alpha_f = delta - (vy + lf*r)/vx;
    alpha_r = - (vy - lr*r)/vx;

    % =========================
    % Tire forces
    % =========================
    Fy_f = Cf * alpha_f;
    Fy_r = Cr * alpha_r;

    % =========================
    % Dynamics
    % =========================
    vy_dot = (Fy_f + Fy_r)/m - vx*r;
    r_dot  = (lf*Fy_f - lr*Fy_r)/Iz;

    dx = [vy_dot; r_dot];
end

%% =========================
% 車輛參數
% =========================
m   = 309.5;     % kg
Iz  = 120;       % yaw inertia (估)
lf  = 0.775;     
lr  = 0.775;
L   = lf + lr;

Cf  = 8000;      % N/rad
Cr  = 8000;

vx  = 10;        % m/s (固定速度)

%% =========================
% 模擬設定
% =========================
tspan = [0 5];

% step steering input (rad)
delta = @(t) (t > 0.5) * deg2rad(5);

%% =========================
% 初始條件
% =========================
x0 = [0; 0];   % [vy, r]

%% =========================
% ODE 求解
% =========================
[t, x] = ode45(@(t,x) bicycle_ode(t, x, delta, vx, m, Iz, lf, lr, Cf, Cr), tspan, x0);

vy = x(:,1);
r  = x(:,2);

%% =========================
% 計算滑移角
% =========================
alpha_f = zeros(size(t));
alpha_r = zeros(size(t));

for i = 1:length(t)
    d = delta(t(i));
    alpha_f(i) = d - (vy(i) + lf*r(i)) / vx;
    alpha_r(i) = - (vy(i) - lr*r(i)) / vx;
end

%% =========================
% 畫圖
% =========================
figure;
subplot(3,1,1)
plot(t, rad2deg(r), 'LineWidth',2)
ylabel('Yaw Rate (deg/s)')
grid on

subplot(3,1,2)
plot(t, vy, 'LineWidth',2)
ylabel('v_y (m/s)')
grid on

subplot(3,1,3)
plot(t, rad2deg(alpha_f), t, rad2deg(alpha_r), 'LineWidth',2)
ylabel('Slip Angle (deg)')
legend('\alpha_f','\alpha_r')
xlabel('Time (s)')
grid on

sgtitle('Linear Bicycle Model Response')