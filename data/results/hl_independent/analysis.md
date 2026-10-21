# 獨立懸吊等效：單輪彈簧、阻尼與 ARB

## 分析目的

將前後軸解耦 Heave／Roll 設定等效成每輪一支彈簧與阻尼器，並計算維持目標 roll 剛度所需的 ARB。先保持該軸純 heave 輪端剛度，再處理 roll 的額外需求；independent 運動比與解耦 heave／roll 運動比分別設定。

$$
K_{wheel,ind}=K_{wheel,heave}/2,\qquad K_{spring,ind}=\frac{K_{wheel,ind}}{MR_{ind}^2}
$$

$$
K_{roll,base}=\frac{K_{wheel,ind}t^2}{2},\qquad K_{ARB}=K_{roll,suspension}-K_{roll,base}
$$

$$
c_{shaft,ind}=\frac{c_{heave,axle}}{2MR_{ind}^2}
$$

## 結果與適用範圍

independent_equivalent.csv 列出前後輪輪端剛度、彈簧剛度 N/m 與 N/mm、基礎 roll 剛度、所需 ARB Nm/rad，以及單輪低／高速平均阻尼 N s/m。下一節將平均係數進一步拆為壓縮／回彈四種斜率。

若所需 ARB 為負，表示基礎單輪彈簧已比目標 roll 剛度更硬，必須重新選擇彈簧或運動比，不能把負值直接當一般 ARB。此等效保持純 heave 與準靜態 roll 的剛度條件，不表示所有動態模態與解耦架構完全一致。
