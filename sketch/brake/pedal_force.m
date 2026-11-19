clc; clear; close all;
%% g
g = 9.80665;

%% 車輛參數
cgh = 0.279389;
w_r_f = 0.49298;
w_r_r = 0.50702;
veh_w = 284.50;
veh_m = veh_w * g;
wheelbase = 1.55;
veh_m_f = veh_m * w_r_f;
veh_m_r = veh_m * w_r_r;

%% 零件參數
t_r = 0.25908;
caliper_r = 34 / 2;
caliper_a = (caliper_r^2) * pi;
caliper_num = 2;
mc_r = 14 / 2;
mc_a = (mc_r^2) * pi;
disc_r = 0.085;
lini_mu = 0.55;
dr_f = 500;

%% 建立存放結果的 table 變數
result = [];

for acc_g = 1:0.1:2
    mu = acc_g;

    %% 重量轉移
    d_m = veh_m * acc_g * cgh / wheelbase;
    veh_load_f = veh_m_f + d_m;
    veh_load_r = veh_m_r - d_m;

    %% 輪上扭矩
    wheel_t_f = veh_load_f * mu * t_r / 2;
    wheel_t_r = veh_load_r * mu * t_r / 2;

    %% 碟盤切向力
    disc_f_f = wheel_t_f / disc_r;
    disc_f_r = wheel_t_r / disc_r;

    %% 卡鉗正向力
    caliper_f_f = disc_f_f / lini_mu/2;
    caliper_f_r = disc_f_r / lini_mu/2;
    %% 卡鉗壓力
    caliper_p_f = caliper_f_f / caliper_a;
    caliper_p_r = caliper_f_r / caliper_a;

    %% 總泵正向力
    mc_f_f = caliper_p_f * mc_a;
    mc_f_r = caliper_p_r * mc_a;

    %% pedal ratio
    pr = (mc_f_f + mc_f_r) / dr_f;

    %% 前後扭矩分配
    bt_f = wheel_t_f / (wheel_t_f + wheel_t_r);
    bt_r = wheel_t_r / (wheel_t_f + wheel_t_r);

    %% 前後系統壓力比例
    sp_f = caliper_p_f / (caliper_p_f + caliper_p_r);
    sp_r = caliper_p_r / (caliper_p_f + caliper_p_r);

    %% balance bar
    bb_f = mc_f_f / (mc_f_f + mc_f_r);
    bb_r = mc_f_r / (mc_f_f + mc_f_r);

    %% 將結果存入陣列
    result = [result;
        acc_g, dr_f, pr, ...
        wheel_t_f, wheel_t_r, ...
        caliper_p_f, caliper_p_r, ...
        bt_f * 100, bt_r * 100, ...
        sp_f * 100, sp_r * 100, ...
        bb_f * 100, bb_r * 100];
end

%% 建立 table 並命名欄位
result_table = array2table(result, ...
    'VariableNames', {'acc_g', 'driver_input', 'pedal_ratio', ...
    'wheel_torque_front', 'wheel_torque_rear', ...
    'pressure_front', 'pressure_rear', ...
    'torque_distribution_f', 'torque_distribution_r', ...
    'system_pressure_ratio_f', 'system_pressure_ratio_r', ...
    'balance_bar_f', 'balance_bar_r'});

%% 顯示結果
disp(result_table);