%% Extreme_cornering_speed.m
% 彎道極端速度計算
clc; clear; close all;
addpath('data');
load_data('data.csv')

R_list = [6.17,3.26,14.88,9.07,11.97,7.65];
v_ext = R_list;
for i = 1:length(R_list)
    r = R_list(i);
    v = (mu_y*g*r)^0.5;
    fprintf("半徑:%.2f m >> 極限速度:%.2f km/hr(%.2f m/s)\n\n",r,v*3.6,v)
    v_ext(i) = v;
end

% 顯示矩陣

fprintf("R_list = [")
fprintf("%g,",R_list)
fprintf("]\nv_ext = [")
fprintf("%g,",v_ext)
fprintf("]\n")


% === 分數占分 ===
% R1(6.17): 99.47 
% R2(3.26): 95.79 
% R3(14.88): 33.16 
% R4(9.07): 18.42 
% R5(11.97): 18.42 
% Skidpad(7.65): 75.00 
