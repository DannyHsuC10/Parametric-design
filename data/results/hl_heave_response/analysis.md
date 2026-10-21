# Heave：Step response 與頻率響應

## 分析目的與模型

依 「Ride rate 與 Heave 自然頻率」的前後軸設定，各建立簧上位移與簧下位移兩自由度狀態空間模型。輸入是路面位移 r，輸出是簧上位移。每軸分別以低速與高速區域的平均阻尼係數進行線性化，並比較 20 mm 路面階躍與頻率響應。

$$
m_s\ddot{z}_s=-K_w(z_s-z_u)-c(\dot{z}_s-\dot{z}_u)
$$

$$
m_u\ddot{z}_u=K_w(z_s-z_u)+c(\dot{z}_s-\dot{z}_u)-2K_t(z_u-r)
$$

ms、mu 皆為軸上的質量。採 3 秒、1200 點的 step 視窗，頻率範圍為 0.1 至約 200 Hz。頻率響應直接求解狀態空間矩陣，輸出 magnitude ratio、dB 與相位。

## 結果與判讀

圖表選單可切換前後軸，每張圖包含低／高速的 step、幅值與相位。heave_step_metrics.csv 的位移 final 及 peak_abs 為 mm，包含峰值時間、超越量及 2% 收斂時間；若視窗結束仍未收斂則 settling 欄留空。

完整時序及頻率資料各存為 CSV。高／低速指阻尼器軸速度區域，這裡的兩條線使用固定線性係數；跨越 knee 的非線性切換在 「非線性 ODE、姿態與輪胎 Fz」 ODE 執行。前後軸線性響應沒有 pitch 耦合。
