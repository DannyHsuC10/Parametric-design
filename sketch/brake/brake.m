classdef brake < matlab.apps.AppBase

    % Properties that correspond to app components
    properties (Access = public)
        UIFigure     matlab.ui.Figure
        DropDown_rb  matlab.ui.control.DropDown
        Label_2      matlab.ui.control.Label
        DropDown_fb  matlab.ui.control.DropDown
        Label        matlab.ui.control.Label
        reset_D_pr   matlab.ui.control.Button
        reset_D_pf   matlab.ui.control.Button
        reset_D_pm   matlab.ui.control.Button
        Edit__D_pr   matlab.ui.control.NumericEditField
        tLabel_10    matlab.ui.control.Label
        Edit__D_pf   matlab.ui.control.NumericEditField
        tLabel_9     matlab.ui.control.Label
        Edit__D_pm   matlab.ui.control.NumericEditField
        tLabel_8     matlab.ui.control.Label
        reset_mu_d   matlab.ui.control.Button
        tLabel_7     matlab.ui.control.Label
        Edit__mu_d   matlab.ui.control.NumericEditField
        reset_dd     matlab.ui.control.Button
        reset_D_do   matlab.ui.control.Button
        reset_r_w    matlab.ui.control.Button
        reset_l      matlab.ui.control.Button
        reset_hcog   matlab.ui.control.Button
        reset_m      matlab.ui.control.Button
        reset_ag     matlab.ui.control.Button
        Edit__dd     matlab.ui.control.NumericEditField
        tLabel_6     matlab.ui.control.Label
        Edit__D_do   matlab.ui.control.NumericEditField
        tLabel_5     matlab.ui.control.Label
        Edit__r_w    matlab.ui.control.NumericEditField
        tLabel_4     matlab.ui.control.Label
        Edit_l       matlab.ui.control.NumericEditField
        tLabel_3     matlab.ui.control.Label
        Edit_hcog    matlab.ui.control.NumericEditField
        tLabel_2     matlab.ui.control.Label
        reset        matlab.ui.control.Button
        Edit_m       matlab.ui.control.NumericEditField
        tLabel       matlab.ui.control.Label
        solve        matlab.ui.control.Button
        NLabel       matlab.ui.control.Label
        Edit_ag      matlab.ui.control.NumericEditField
        xLabel       matlab.ui.control.Label
        UIAxes_tt    matlab.ui.control.UIAxes
        UIAxes_at    matlab.ui.control.UIAxes
    end

    
    properties (Access = private)

    end

    properties (Access = public)
        g          double = 9.81
        pi         double = 3.14
        ag          double
        ag_reset    double = 1.5 % 預設加速度值為 1.5個g
        m          double
        m_reset    double = 300.0 % 預設質量
        mu         double
        w          double
        a          double
        Fb         double
        hcog       double
        hcog_reset double = 0.28 % 預設重心高度
        l          double
        l_reset    double = 1.55 % 預設軸距
        Fdm        double
        N_f        double
        N_r        double
        T_fw       double
        T_rw       double
        r_w        double
        r_w_reset  double = 0.259 % 預設輪胎直徑
        D_do       double
        D_do_reset double = 0.24 % 預設碟盤外徑
        dd         double
        dd_reset   double = 0.02 % 預設來令片距離外徑距離
        r_d        double
        P_f        double
        P_r        double
        mu_d       double
        mu_d_reset double = 0.55 % 預設煞車來令片摩擦係數
        Rb_f        double
        Rb_r        double
        D_pf       double
        D_pf_reset double = 30 % 預設前煞活塞直徑
        D_pr       double
        D_pr_reset double = 34 % 預設後煞活塞直徑
        D_pm       double
        D_pm_reset double = 14 % 預設總泵活塞直徑
        A_m        double
        A_r        double
        A_f        double
        pp_f       double
        pp_r       double
        Ra_f       double
        Ra_r       double
        Fmp     double


    end
    
    methods (Access = public)
        function a = vehicle_acceleration(app,ag)%計算車輛加速度
            a = ag*app.g;
        end

        function mu = wheel_friction_coefficient(~,w,a,m)%計算車輪摩擦係數
            mu = (m*a)/(w);
        end

        function w = vehicle_weight(app,m)%計算車重
            w = m*app.g;
        end

        function F = force(~,m,a)%計算加速力
            F = m*a;
        end

        function Fdm = center_transfer(~,F,hcog,l)%計算重心轉移量
            Fdm = F*hcog./l;
        end

        function N = normal_force(~,w,F)%計算前or後正向力
            N = w/2+F;
        end

        function T_w = wheel_torque(~,N,mu,r)%計算輪煞車扭矩
            T_w = N*mu*r/2;
        end

        function r_d = disc_radius(~,D_do,dd)%計算碟盤有效半徑
            r_d = D_do/2-dd;
        end

        function P = caliper_pressure(~,T,r,mu)%計算碟盤有效半徑
            F = T./r;
            P = F./mu;
        end

        function R = braking_ratio(~,P_1,P_2)%計算煞車比
            R = P_1./(P_1+P_2);
        end
        
        function A = piston_area(app,D,pp)%計算活塞面積
            R = D/2;
            A = app.pi*R*R*pp;
        end

        function R = ratio(~,n1,n2)%油路放大比
            R = n1*2/n2;
        end
        
    end
    

    % Callbacks that handle component events
    methods (Access = private)

        % Value changed function: Edit_ag
        function Edit_agValueChanged(app, event)
            app.ag = app.Edit_ag.Value;%設定加速度 單位:g
        end

        % Value changed function: Edit_m
        function Edit_mValueChanged(app, event)
            app.m = app.Edit_m.Value;%設定質量
        end

        % Value changed function: Edit_hcog
        function Edit_hcogValueChanged(app, event)
            app.hcog = app.Edit_hcog.Value;%設定重心高度
        end

        % Value changed function: Edit_l
        function Edit_lValueChanged(app, event)
            app.l = app.Edit_l.Value;%設定軸距
        end

        % Value changed function: Edit__r_w
        function Edit__r_wValueChanged(app, event)
            app.r_w = app.Edit__r_w.Value;%設定輪胎半徑
        end

        % Value changed function: Edit__dd
        function Edit__ddValueChanged(app, event)
            app.dd = app.Edit__dd.Value;%設定來令片距離外徑距離
        end

        % Value changed function: Edit__D_do
        function Edit__D_doValueChanged(app, event)
            app.D_do = app.Edit__D_do.Value;%碟盤外徑
        end

        % Value changed function: Edit__mu_d
        function Edit__mu_dValueChanged(app, event)
            app.mu_d = app.Edit__mu_d.Value;
        end

        % Value changed function: Edit__D_pm
        function Edit__D_pmValueChanged(app, event)
            app.D_pm = app.Edit__D_pm.Value; 
        end

        % Value changed function: Edit__D_pf
        function Edit__D_pfValueChanged(app, event)
            app.D_pf = app.Edit__D_pf.Value; 
        end

        % Value changed function: Edit__D_pr
        function Edit__D_prValueChanged(app, event)
            app.D_pr = app.Edit__D_pr.Value;
        end

        % Button pushed function: solve
        function solvePushed(app, event)

            initial_ag = 0;      % 加速度的起始值
            final_ag = app.ag;   % 加速度的最終值（app.ag）
            Each_step = 0.1;     % 每次間隔
                    
            ag_data = [];
            T_fw_data = [];
            T_rw_data = [];

            % 開始迴圈計算
            for ag = initial_ag:Each_step:final_ag
                app.a = round(app.vehicle_acceleration(ag),3);
                app.w = round(app.vehicle_weight(app.m),3);
                app.mu = round(app.wheel_friction_coefficient(app.w,app.a,app.m),3);
                app.Fb = round(app.force(app.m,app.a),3);
                app.Fdm = round(app.center_transfer(app.Fb,app.hcog,app.l),3);
                app.N_f = round(app.normal_force(app.w,app.Fdm),3);
                app.N_r = round(app.normal_force(app.w,-app.Fdm),3);
                app.T_fw = round(app.wheel_torque(app.N_f,app.mu,app.r_w),3);
                app.T_rw = round(app.wheel_torque(app.N_r,app.mu,app.r_w),3);
                app.r_d = round(app.disc_radius(app.D_do,app.dd),3);
                app.P_f = round(app.caliper_pressure(app.T_fw,app.r_d,app.mu_d),3);
                app.P_r = round(app.caliper_pressure(app.T_rw,app.r_d,app.mu_d),3);
                app.Rb_f = round(app.braking_ratio(app.P_f,app.P_r),3);
                app.Rb_r = round(app.braking_ratio(app.P_r,app.P_f),3);
                app.A_m = round(app.piston_area(app.D_pm,1),3);
                app.A_f = round(app.piston_area(app.D_pf,app.pp_f),3);
                app.A_r = round(app.piston_area(app.D_pr,app.pp_r),3);
                app.Ra_f = round(app.ratio(app.A_f,app.A_m),3);
                app.Ra_r = round(app.ratio(app.A_r,app.A_m),3);
                app.Fmp = round(app.P_f*2/app.Ra_f+app.P_r*2/app.Ra_r,3);
    
                app.NLabel.Text = sprintf(['車輛加速度: ', num2str(app.a), '\n', ...
                                          '車重 (單位:N): ', num2str(app.w), '\n', ...
                                          '車輪摩擦係數: ', num2str(app.mu), '\n', ...
                                          '煞車加速力: ',num2str(app.Fb), '\n',...
                                          '重心轉移力: ',num2str(app.Fdm), '\n',...
                                          '前正向力: ',num2str(app.N_f),'       後正向力: ',num2str(app.N_r), '\n',...
                                          '前輪煞車扭矩: ',num2str(app.T_fw),'       後輪煞車扭矩: ',num2str(app.T_rw), '\n',...
                                          '前卡鉗壓力: ',num2str(app.P_f),'       後卡鉗壓力: ',num2str(app.P_r), '\n',...
                                          '前煞車比: ',num2str(app.Rb_f),'       後煞車比: ',num2str(app.Rb_r), '\n',...
                                          '總泵總面積: ',num2str(app.A_m),'       前卡鉗活塞總面積: ',num2str(app.A_f),'       後卡鉗活塞總面積: ',num2str(app.A_r), '\n',...
                                          '前油路放大比: ',num2str(app.Ra_f),'       後油路放大比: ',num2str(app.Ra_r), '\n',...
                                          '壓總泵力: ', num2str(app.Fmp), '\n', ...
                                          ]);
            
            ag_data = [ag_data, app.a];
            T_fw_data = [T_fw_data, app.T_fw];
            T_rw_data = [T_rw_data, app.T_rw];   

%            cla(app.UIAxes_at);
            xlim(app.UIAxes_at, [0 app.vehicle_acceleration(app.ag)]); % 設置 x 軸範圍
%            ylim(app.UIAxes_at, [0 1000]); % 設置 y 軸範圍

            plot(app.UIAxes_at, ag_data,T_fw_data, '-b', 'LineWidth', 2);
            hold(app.UIAxes_at, 'on');
            plot(app.UIAxes_at, ag_data,T_rw_data, '-r', 'LineWidth', 2);
            legend(app.UIAxes_at, {'前輪煞車扭矩', '後輪煞車扭矩'}, 'Location', 'best');

%            cla(app.UIAxes_tt);
            plot(app.UIAxes_tt, T_fw_data,T_fw_data*0.73, '-b', 'LineWidth', 2);
            hold(app.UIAxes_tt, 'on');
            plot(app.UIAxes_tt, T_fw_data,T_rw_data, '-r', 'LineWidth', 2);
            legend(app.UIAxes_tt, {'前輪煞車扭矩', '後輪煞車扭矩'}, 'Location', 'best');

%            drawnow;

                pause(1*Each_step/app.ag);
            end
            drawnow;
            disp('Finish');
        end

        % Button pushed function: reset
        function resetButtonPushed(app, event)
            app.Edit_ag.Value = app.ag_reset;
            app.ag = app.ag_reset;
            
            app.Edit_m.Value = app.m_reset;
            app.m = app.m_reset;
            
            app.Edit_hcog.Value = app.hcog_reset;
            app.hcog = app.hcog_reset;            
            
            app.Edit_l.Value = app.l_reset;
            app.l = app.l_reset;

            app.Edit__r_w.Value = app.r_w_reset;
            app.r_w = app.r_w_reset;

            app.Edit__D_do.Value = app.D_do_reset;
            app.D_do = app.D_do_reset;

            app.Edit__dd.Value = app.dd_reset;
            app.dd = app.dd_reset;

            app.Edit__mu_d.Value = app.mu_d_reset;
            app.mu_d = app.mu_d_reset;

            app.Edit__D_pm.Value = app.D_pm_reset;
            app.D_pm = app.D_pm_reset;

            app.Edit__D_pf.Value = app.D_pf_reset;
            app.D_pf = app.D_pf_reset;

            app.Edit__D_pr.Value = app.D_pr_reset;
            app.D_pr = app.D_pr_reset;

            app.DropDown_fb.Value = '對4(預設)';
            app.pp_f = 2;

            app.DropDown_rb.Value = '對2(預設)';
            app.pp_r = 1;

        end

        % Button pushed function: reset_ag
        function reset_agButtonPushed(app, event)
            app.Edit_ag.Value = app.ag_reset;
            app.ag = app.ag_reset;
        end

        % Button pushed function: reset_m
        function reset_mButtonPushed(app, event)
            app.Edit_m.Value = app.m_reset;
            app.m = app.m_reset;
        end

        % Button pushed function: reset_hcog
        function reset_hcogButtonPushed(app, event)
            app.Edit_hcog.Value = app.hcog_reset;
            app.hcog = app.hcog_reset;  
        end

        % Button pushed function: reset_l
        function reset_lButtonPushed(app, event)
            app.Edit_l.Value = app.l_reset;
            app.l = app.l_reset;
        end

        % Button pushed function: reset_r_w
        function reset_r_wButtonPushed(app, event)
            app.Edit__r_w.Value = app.r_w_reset;
            app.r_w = app.r_w_reset;
        end

        % Button pushed function: reset_D_do
        function reset_D_doButtonPushed(app, event)
            app.Edit__D_do.Value = app.D_do_reset;
            app.D_do = app.D_do_reset;
        end

        % Button pushed function: reset_dd
        function reset_ddButtonPushed(app, event)
            app.Edit__dd.Value = app.dd_reset;
            app.dd = app.dd_reset;
        end

        % Button pushed function: reset_mu_d
        function reset_mu_dButtonPushed(app, event)
            app.Edit__mu_d.Value = app.mu_d_reset;
            app.mu_d = app.mu_d_reset;
        end

        % Button pushed function: reset_D_pm
        function reset_D_pmButtonPushed(app, event)
            app.Edit__D_pm.Value = app.D_pm_reset;
            app.D_pm = app.D_pm_reset;
        end

        % Button pushed function: reset_D_pf
        function reset_D_pfButtonPushed(app, event)
            app.Edit__D_pf.Value = app.D_pf_reset;
            app.D_pf = app.D_pf_reset;
        end

        % Button pushed function: reset_D_pr
        function reset_D_prButtonPushed(app, event)
            app.Edit__D_pr.Value = app.D_pr_reset;
            app.D_pr = app.D_pr_reset;
        end

        % Value changed function: DropDown_fb
        function DropDown_fbValueChanged(app, event)
            value = app.DropDown_fb.Value; % 獲取當前選擇的值
            switch value
                case '對4(預設)'
                    app.pp_f = 2;
                case '對2'
                    app.pp_f = 1;
                case '對6'
                    app.pp_f = 3;
                otherwise
                    app.pp_r = NaN; % 或其他默認值，根據需求設置
                    disp('未匹配的選項');
            end
        end

        % Value changed function: DropDown_rb
        function DropDown_rbValueChanged(app, event)
            value = app.DropDown_rb.Value; % 獲取當前選擇的值
            switch value
                case '對2(預設)'
                    app.pp_r = 1;
                case '對4'
                    app.pp_r = 2;
                case '對6'
                    app.pp_r = 3;
                otherwise
                    app.pp_r = NaN; % 或其他默認值，根據需求設置
                    disp('未匹配的選項');
            end
        end
    end

    % Component initialization
    methods (Access = private)

        % Create UIFigure and components
        function createComponents(app)

            % Create UIFigure and hide until all components are created
            app.UIFigure = uifigure('Visible', 'off');
            app.UIFigure.Position = [100 100 1238 578];
            app.UIFigure.Name = 'MATLAB App';

            % Create UIAxes_at
            app.UIAxes_at = uiaxes(app.UIFigure);
            title(app.UIAxes_at, '加速度與扭矩關係')
            xlabel(app.UIAxes_at, '加速度')
            ylabel(app.UIAxes_at, '扭矩')
            zlabel(app.UIAxes_at, 'Z')
            app.UIAxes_at.Position = [816 311 402 239];

            % Create UIAxes_tt
            app.UIAxes_tt = uiaxes(app.UIFigure);
            title(app.UIAxes_tt, '前後煞車比')
            xlabel(app.UIAxes_tt, '前煞車')
            ylabel(app.UIAxes_tt, '後煞車')
            zlabel(app.UIAxes_tt, 'Z')
            app.UIAxes_tt.Position = [817 36 401 242];

            % Create xLabel
            app.xLabel = uilabel(app.UIFigure);
            app.xLabel.HorizontalAlignment = 'right';
            app.xLabel.Position = [10 528 131 22];
            app.xLabel.Text = '最高煞車加速度 (單位g)';

            % Create Edit_ag
            app.Edit_ag = uieditfield(app.UIFigure, 'numeric');
            app.Edit_ag.ValueChangedFcn = createCallbackFcn(app, @Edit_agValueChanged, true);
            app.Edit_ag.Position = [155 528 100 22];

            % Create NLabel
            app.NLabel = uilabel(app.UIFigure);
            app.NLabel.FontSize = 14;
            app.NLabel.Position = [27 53 559 211];
            app.NLabel.Text = {'車輛加速度: '; '車重 (單位:N): '; '車輪摩擦係數: '; '煞車加速力: '; '重心轉移力: '; '前正向力:                            後正向力:'; '前輪煞車扭矩:                        後輪煞車扭矩:'; '前卡鉗壓力:                            後卡鉗壓力: '; '前煞車比:                                 後煞車比: '; '總泵總面積:                             前卡鉗活塞總面積:                               後卡鉗活塞總面積: '; '前油路放大比:                        後油路放大比: '; '壓總泵力:'};

            % Create solve
            app.solve = uibutton(app.UIFigure, 'push');
            app.solve.ButtonPushedFcn = createCallbackFcn(app, @solvePushed, true);
            app.solve.BackgroundColor = [0.8 0.8 0.8];
            app.solve.FontSize = 24;
            app.solve.FontWeight = 'bold';
            app.solve.Position = [629 86 115 39];
            app.solve.Text = '計算';

            % Create tLabel
            app.tLabel = uilabel(app.UIFigure);
            app.tLabel.HorizontalAlignment = 'right';
            app.tLabel.Position = [12 497 50 22];
            app.tLabel.Text = '質量(kg)';

            % Create Edit_m
            app.Edit_m = uieditfield(app.UIFigure, 'numeric');
            app.Edit_m.Limits = [0 Inf];
            app.Edit_m.ValueChangedFcn = createCallbackFcn(app, @Edit_mValueChanged, true);
            app.Edit_m.Position = [154 497 100 22];

            % Create reset
            app.reset = uibutton(app.UIFigure, 'push');
            app.reset.ButtonPushedFcn = createCallbackFcn(app, @resetButtonPushed, true);
            app.reset.Position = [643 147 100 22];
            app.reset.Text = '全部預設';

            % Create tLabel_2
            app.tLabel_2 = uilabel(app.UIFigure);
            app.tLabel_2.HorizontalAlignment = 'right';
            app.tLabel_2.Position = [12 464 71 22];
            app.tLabel_2.Text = '重心高度(m)';

            % Create Edit_hcog
            app.Edit_hcog = uieditfield(app.UIFigure, 'numeric');
            app.Edit_hcog.Limits = [0 3];
            app.Edit_hcog.ValueChangedFcn = createCallbackFcn(app, @Edit_hcogValueChanged, true);
            app.Edit_hcog.Position = [154 464 101 22];

            % Create tLabel_3
            app.tLabel_3 = uilabel(app.UIFigure);
            app.tLabel_3.HorizontalAlignment = 'right';
            app.tLabel_3.Position = [12 434 47 22];
            app.tLabel_3.Text = '軸距(m)';

            % Create Edit_l
            app.Edit_l = uieditfield(app.UIFigure, 'numeric');
            app.Edit_l.Limits = [0 10];
            app.Edit_l.ValueChangedFcn = createCallbackFcn(app, @Edit_lValueChanged, true);
            app.Edit_l.Position = [154 434 101 22];

            % Create tLabel_4
            app.tLabel_4 = uilabel(app.UIFigure);
            app.tLabel_4.HorizontalAlignment = 'right';
            app.tLabel_4.Position = [12 402 71 22];
            app.tLabel_4.Text = '輪胎半徑(m)';

            % Create Edit__r_w
            app.Edit__r_w = uieditfield(app.UIFigure, 'numeric');
            app.Edit__r_w.Limits = [0 1];
            app.Edit__r_w.ValueChangedFcn = createCallbackFcn(app, @Edit__r_wValueChanged, true);
            app.Edit__r_w.Position = [154 401 101 22];

            % Create tLabel_5
            app.tLabel_5 = uilabel(app.UIFigure);
            app.tLabel_5.HorizontalAlignment = 'right';
            app.tLabel_5.Position = [427 528 71 22];
            app.tLabel_5.Text = '碟盤外徑(m)';

            % Create Edit__D_do
            app.Edit__D_do = uieditfield(app.UIFigure, 'numeric');
            app.Edit__D_do.Limits = [0 1];
            app.Edit__D_do.ValueChangedFcn = createCallbackFcn(app, @Edit__D_doValueChanged, true);
            app.Edit__D_do.Position = [571 528 102 22];

            % Create tLabel_6
            app.tLabel_6 = uilabel(app.UIFigure);
            app.tLabel_6.HorizontalAlignment = 'right';
            app.tLabel_6.Position = [427 497 119 22];
            app.tLabel_6.Text = '來令片與外徑距離(m)';

            % Create Edit__dd
            app.Edit__dd = uieditfield(app.UIFigure, 'numeric');
            app.Edit__dd.Limits = [0 0.5];
            app.Edit__dd.ValueChangedFcn = createCallbackFcn(app, @Edit__ddValueChanged, true);
            app.Edit__dd.Position = [571 497 102 22];

            % Create reset_ag
            app.reset_ag = uibutton(app.UIFigure, 'push');
            app.reset_ag.ButtonPushedFcn = createCallbackFcn(app, @reset_agButtonPushed, true);
            app.reset_ag.Position = [272 528 100 22];
            app.reset_ag.Text = '預設';

            % Create reset_m
            app.reset_m = uibutton(app.UIFigure, 'push');
            app.reset_m.ButtonPushedFcn = createCallbackFcn(app, @reset_mButtonPushed, true);
            app.reset_m.Position = [272 497 100 22];
            app.reset_m.Text = '預設';

            % Create reset_hcog
            app.reset_hcog = uibutton(app.UIFigure, 'push');
            app.reset_hcog.ButtonPushedFcn = createCallbackFcn(app, @reset_hcogButtonPushed, true);
            app.reset_hcog.Position = [272 464 100 22];
            app.reset_hcog.Text = '預設';

            % Create reset_l
            app.reset_l = uibutton(app.UIFigure, 'push');
            app.reset_l.ButtonPushedFcn = createCallbackFcn(app, @reset_lButtonPushed, true);
            app.reset_l.Position = [273 434 100 22];
            app.reset_l.Text = '預設';

            % Create reset_r_w
            app.reset_r_w = uibutton(app.UIFigure, 'push');
            app.reset_r_w.ButtonPushedFcn = createCallbackFcn(app, @reset_r_wButtonPushed, true);
            app.reset_r_w.Position = [272 401 100 22];
            app.reset_r_w.Text = '預設';

            % Create reset_D_do
            app.reset_D_do = uibutton(app.UIFigure, 'push');
            app.reset_D_do.ButtonPushedFcn = createCallbackFcn(app, @reset_D_doButtonPushed, true);
            app.reset_D_do.Position = [688 528 100 22];
            app.reset_D_do.Text = '預設';

            % Create reset_dd
            app.reset_dd = uibutton(app.UIFigure, 'push');
            app.reset_dd.ButtonPushedFcn = createCallbackFcn(app, @reset_ddButtonPushed, true);
            app.reset_dd.Position = [688 497 100 22];
            app.reset_dd.Text = '預設';

            % Create Edit__mu_d
            app.Edit__mu_d = uieditfield(app.UIFigure, 'numeric');
            app.Edit__mu_d.Limits = [0 Inf];
            app.Edit__mu_d.ValueChangedFcn = createCallbackFcn(app, @Edit__mu_dValueChanged, true);
            app.Edit__mu_d.Position = [570 468 103 22];

            % Create tLabel_7
            app.tLabel_7 = uilabel(app.UIFigure);
            app.tLabel_7.HorizontalAlignment = 'right';
            app.tLabel_7.Position = [422 468 89 22];
            app.tLabel_7.Text = '來令片摩擦係數';

            % Create reset_mu_d
            app.reset_mu_d = uibutton(app.UIFigure, 'push');
            app.reset_mu_d.ButtonPushedFcn = createCallbackFcn(app, @reset_mu_dButtonPushed, true);
            app.reset_mu_d.Position = [689 468 100 22];
            app.reset_mu_d.Text = '預設';

            % Create tLabel_8
            app.tLabel_8 = uilabel(app.UIFigure);
            app.tLabel_8.HorizontalAlignment = 'right';
            app.tLabel_8.Position = [421 434 129 22];
            app.tLabel_8.Text = '煞車總泵活塞直徑(mm)';

            % Create Edit__D_pm
            app.Edit__D_pm = uieditfield(app.UIFigure, 'numeric');
            app.Edit__D_pm.Limits = [0 1000];
            app.Edit__D_pm.ValueChangedFcn = createCallbackFcn(app, @Edit__D_pmValueChanged, true);
            app.Edit__D_pm.Position = [570 434 103 22];

            % Create tLabel_9
            app.tLabel_9 = uilabel(app.UIFigure);
            app.tLabel_9.HorizontalAlignment = 'right';
            app.tLabel_9.Position = [422 401 129 22];
            app.tLabel_9.Text = '前輪煞車活塞直徑(mm)';

            % Create Edit__D_pf
            app.Edit__D_pf = uieditfield(app.UIFigure, 'numeric');
            app.Edit__D_pf.Limits = [0 1000];
            app.Edit__D_pf.ValueChangedFcn = createCallbackFcn(app, @Edit__D_pfValueChanged, true);
            app.Edit__D_pf.Position = [571 401 103 22];

            % Create tLabel_10
            app.tLabel_10 = uilabel(app.UIFigure);
            app.tLabel_10.HorizontalAlignment = 'right';
            app.tLabel_10.Position = [422 339 129 22];
            app.tLabel_10.Text = '後輪煞車活塞直徑(mm)';

            % Create Edit__D_pr
            app.Edit__D_pr = uieditfield(app.UIFigure, 'numeric');
            app.Edit__D_pr.Limits = [0 1000];
            app.Edit__D_pr.ValueChangedFcn = createCallbackFcn(app, @Edit__D_prValueChanged, true);
            app.Edit__D_pr.Position = [570 339 103 22];

            % Create reset_D_pm
            app.reset_D_pm = uibutton(app.UIFigure, 'push');
            app.reset_D_pm.ButtonPushedFcn = createCallbackFcn(app, @reset_D_pmButtonPushed, true);
            app.reset_D_pm.Position = [688 434 100 22];
            app.reset_D_pm.Text = '預設';

            % Create reset_D_pf
            app.reset_D_pf = uibutton(app.UIFigure, 'push');
            app.reset_D_pf.ButtonPushedFcn = createCallbackFcn(app, @reset_D_pfButtonPushed, true);
            app.reset_D_pf.Position = [688 401 100 22];
            app.reset_D_pf.Text = '預設';

            % Create reset_D_pr
            app.reset_D_pr = uibutton(app.UIFigure, 'push');
            app.reset_D_pr.ButtonPushedFcn = createCallbackFcn(app, @reset_D_prButtonPushed, true);
            app.reset_D_pr.Position = [690 339 100 22];
            app.reset_D_pr.Text = '預設';

            % Create Label
            app.Label = uilabel(app.UIFigure);
            app.Label.HorizontalAlignment = 'right';
            app.Label.Position = [422 372 65 22];
            app.Label.Text = '前煞車選項';

            % Create DropDown_fb
            app.DropDown_fb = uidropdown(app.UIFigure);
            app.DropDown_fb.Items = {'未選擇', '對2', '對4(預設)', '對6'};
            app.DropDown_fb.ValueChangedFcn = createCallbackFcn(app, @DropDown_fbValueChanged, true);
            app.DropDown_fb.Position = [571 371 102 22];
            app.DropDown_fb.Value = '未選擇';

            % Create Label_2
            app.Label_2 = uilabel(app.UIFigure);
            app.Label_2.HorizontalAlignment = 'right';
            app.Label_2.Position = [422 312 65 22];
            app.Label_2.Text = '後煞車選項';

            % Create DropDown_rb
            app.DropDown_rb = uidropdown(app.UIFigure);
            app.DropDown_rb.Items = {'未選擇', '對2(預設)', '對4', '對6'};
            app.DropDown_rb.ValueChangedFcn = createCallbackFcn(app, @DropDown_rbValueChanged, true);
            app.DropDown_rb.Position = [571 312 102 22];
            app.DropDown_rb.Value = '未選擇';

            % Show the figure after all components are created
            app.UIFigure.Visible = 'on';
        end
    end

    % App creation and deletion
    methods (Access = public)

        % Construct app
        function app = brake

            % Create UIFigure and components
            createComponents(app)

            % Register the app with App Designer
            registerApp(app, app.UIFigure)

            if nargout == 0
                clear app
            end
        end

        % Code that executes before app deletion
        function delete(app)

            % Delete UIFigure when app is deleted
            delete(app.UIFigure)
        end
    end
end