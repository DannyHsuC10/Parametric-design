# tooth_Strength：齒根強度與模數需求

以目標齒比 $i_{avg}$、馬達扭矩 $T_m$、安全係數 $SF$、齒寬 $b$ 與材料強度 $\tau$，掃描太陽輪齒數 $Z_s$。

$$m_{req}(Z_s)=\sqrt{\frac{6T_mi_{avg}SF}{Z_s\pi b\tau}}$$

$$m_{selected}(Z_s)=\max(m_{req}(Z_s),m_{input})$$

掃描範圍為設定的最小齒數至 100 齒，轉折齒數為首次滿足下式的 $Z_s$：

$$m_{req}(Z_s)\leq m_{input}$$

若掃描內沒有交點，程式以最後一個掃描齒數作為輸出。此處公式按現行程式整理；程式直接代入 N·m 的 $T_m$、mm 的 $b$ 與 MPa 的 $\tau$，尚未加入 N·m 至 N·mm 的換算，採用強度結果前需核對單位。
