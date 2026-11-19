%% 定義變數
clc; clear; close all;
l = 220;%踏板長度
theta = 11.794;%前傾斜角度
theta_Mc = -9.938;%Master cylinder
PedalPushTheta=3.387*pi/180;%踏板旋轉角
PR = 2.48;%初始Pedal ratio

l_sensor = 152.088;
GasPadelAxis=[0;0;1];                                               %踏板旋轉軸點
SensorAxis=[100;22;1];                                              %Master cylinder 旋轉軸點
brakePadelForcePoint = [l*sind(-theta); l*cosd(-theta); 1];           %腳踩在踏板上的點
GasPadelSensorPoint = [l_sensor*sind(theta_Mc); l_sensor*cosd(theta_Mc); 1];  %Master cylinder接在踏板上的點
MCLengthchange=[0,0,0];         %用來記錄等一下循環內需要的值，要初始化
%% 計算機構變化
ind=1;  %計數器
for i=0:0.01:1 %用比例下去算目前轉了幾%，極限就是PedalPushTheta=11.89*pi/180
    
    %目前轉了幾度
    PedalPushThetaNow=PedalPushTheta*i;

    % 創建旋轉矩陣(踩踏板時踏板轉動的角度)
    brakePadelLocalation = [cos(PedalPushThetaNow) sin(PedalPushThetaNow) 0;
                         -sin(PedalPushThetaNow) cos(PedalPushThetaNow) 0;
                          0 0 1]; 

    %用旋轉矩陣去算出brakePadelForcePoint旋轉時會跑去哪
    brakePadelForcePointNow = brakePadelLocalation * brakePadelForcePoint;
    
    %用旋轉矩陣去算出brakePadelSensorPoint旋轉時會跑去哪
    brakePadelSensorPointNow = brakePadelLocalation * GasPadelSensorPoint;

    %求當下sensor的長度
    Sensorlength = sqrt((SensorAxis(1) - brakePadelSensorPointNow(1))^2 + (SensorAxis(2) - brakePadelSensorPointNow(2))^2);

    MCLengthchange(ind,1)=PedalPushThetaNow*180/pi;         %紀錄轉角
    MCLengthchange(ind,2)=Sensorlength;                     %紀錄Master cylinder長
    MCLengthchange(ind,3)=brakePadelForcePointNow(1);         %紀錄施力點x軸的移動量

    brakePadelSensorPoint_x(ind,1)=brakePadelSensorPointNow(1);     %紀錄施力點x軸的移動量
    brakePadelSensorPoint_y(ind,1)=brakePadelSensorPointNow(2);     %紀錄施力點y軸的移動量

    brakePadelForcePoint_x(ind,1)=brakePadelForcePointNow(1);       %紀錄腳踩在踏板上的點x值
    brakePadelForcePoint_y(ind,1)=brakePadelForcePointNow(2);       %紀錄腳踩在踏板上的點y值
    ind=ind+1;  %更新計數器
end

%% 計算在不同轉角下Master cylinder的變化
caulMCLengthchange=[MCLengthchange(1,2);MCLengthchange(:,2)];   %開頭重複一次因應下面的for循環
for i=1:length(caulMCLengthchange)-1
    a=caulMCLengthchange(i)-caulMCLengthchange(i+1);
    deltaMCLengthchange(i,:)=a;     %這個就是不同轉角下Master cylinder壓縮的變化量
end
deltasensorLengt=MCLengthchange(1,2)-MCLengthchange(end,2);

%% 畫圖
figure
plot(brakePadelSensorPoint_x,brakePadelSensorPoint_y)
hold on
plot(brakePadelForcePoint_x,brakePadelForcePoint_y)

plot([brakePadelSensorPoint_x(1);SensorAxis(1)],[brakePadelSensorPoint_y(1);SensorAxis(2)])
plot([brakePadelSensorPoint_x(end);SensorAxis(1)],[brakePadelSensorPoint_y(end);SensorAxis(2)])

plot([brakePadelForcePoint_x(1);GasPadelAxis(1)],[brakePadelForcePoint_y(1);GasPadelAxis(2)])
plot([brakePadelForcePoint_x(end);GasPadelAxis(1)],[brakePadelForcePoint_y(end);GasPadelAxis(2)])

title('機構移動簡圖')
legend('Master cylinder於踏板固定點移動軌跡','踏板施力點移動軌跡','Master cylinder初始位置','Master cylinder最終位置','踏板初始位置','踏板最終位置',Location='northeast')
axis equal
grid on


figure
%轉角對上長度變化
plot(MCLengthchange(:,1),MCLengthchange(:,2))
title('踏板轉角與Master cylinder長度變化關係')
xlabel('踏板轉角 deg')
ylabel('sensor長度 mm')

figure
%施力點x軸位移對上長度變化
plot(MCLengthchange(:,3)-MCLengthchange(1,3),MCLengthchange(:,2))
title('施力點x軸位移與Master cylinder長度變化關係')
xlabel('施力點x軸位移 mm')
ylabel('sensor長度 mm')

figure
%轉角對上sensor長度變化量
plot(MCLengthchange(:,1),deltaMCLengthchange(:,1))
title('踏板轉角與Master cylinder長度變化量關係關係')
xlabel('踏板轉角 deg')
ylabel('sensor長度變化量 mm')

figure
%施力點x軸位移對上sensor長度變化量
plot(MCLengthchange(:,3)-MCLengthchange(1,3),deltaMCLengthchange(:,1))
title('施力點x軸位移與Master cylinder長度變化量關係')
xlabel('施力點x軸位移 mm')
ylabel('sensor長度變化量 mm')