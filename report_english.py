"""English text for the shared sizing report, keyed by its Traditional Chinese source."""

from project import TENDER_PITCH_HINT, TENDER_PITCH_HINT_EN


ENGLISH = {
    TENDER_PITCH_HINT: TENDER_PITCH_HINT_EN,
    "整車總質量": "Total vehicle mass",
    "前軸靜態重量分配": "Front static weight distribution",
    "Skidpad 所需下壓力": "Required skidpad downforce",
    "Roll gradient（含輪胎）": "Roll gradient with tires",
    "無可用解": "No available solution",
    "—（無可用解）": "— (No available solution)",
    "是": "Yes",
    "否": "No",
    "車輛初步設計估算報告": "Vehicle Initial Sizing Report",
    "產生時間：{stamp}（Asia/Taipei）。本報告由 Vehicle Initial Sizing Lab 依本次求解結果產生。":
        "Generated at {stamp} (Asia/Taipei) by Vehicle Initial Sizing Lab from the current run.",
    "在左側調整車重、幾何或其他參數後按「求解」，即可更新本次參數、數值代入與結果。"
    "公式內角度使用 rad，度數另行換算；計算保留原始精度，報告數字顯示最多 12 位有效數字。":
        "Edit the vehicle mass, geometry, or other parameters on the left and select Solve to update the inputs, "
        "substitutions, and results. The formulas use radians and show degree conversions separately. "
        "Calculations use full precision. The report displays up to 12 significant digits.",
    "計算流程": "Calculation workflow",
    "當次參數與重量分配": "Current inputs and weight distribution",
    "CG 檢查": "CG geometry check",
    "Skidpad 下壓力與空力係數": "Skidpad downforce and aerodynamic coefficients",
    "角度／行程剛性取較高值": "Select the higher stiffness from angle and travel limits",
    "輪胎柔度與自然頻率": "Tire compliance and natural frequencies",
    "使用 Tender？": "Use a tender spring?",
    "Heave 反算與 Tender 可行性": "Calculate target heave stiffness and check tender feasibility",
    "直接使用原 Heave 主簧剛性": "Use the main heave spring rate",
    "前後剛性基準 → 煞車與加速 Anti；前後 RC": "Axle stiffness, braking and acceleration anti geometry, and roll centers",
    "FVSA、輪胎 Roll、半徑求轉角與 Caster": "FVSA, tire roll, steering angle, and caster",
    "空力載重與四輪受力；Tender 啟用時另算串聯壓縮": "Aerodynamic loading, wheel forces, and series spring compression if enabled",
    "齒比、煞車與機械利益": "Gear ratios, braking, and mechanical advantage",
    "前後阻尼、四組 Ks→Kw→Kr": "Axle damping and four Ks → Kw → Kr cases",
    "Roll／Pitch gradient": "Roll and pitch gradients",
    "本次結果與 LaTeX 數值代入": "Results and formula substitutions",
    "預覽或儲存 Markdown 報告": "View or save the Markdown report",
    "更新方式": "Updating the report",
    "在 Vehicle Initial Sizing Lab 調整左側參數並按「求解」。完整結果可匯出為 CSV 或 Excel。Excel 另附欄位說明與單位。":
        "Edit the parameters on the left and select Solve. Export the complete results as CSV or Excel. "
        "The Excel export includes a description and units for each field.",
    "0. 本次輸入、質量與幾何": "0. Current inputs, mass, and geometry",
    "kg（全車簧上）": "kg (total sprung mass)",
    "kg（單輪簧下）": "kg (unsprung mass per wheel)",
    "deg（由半徑導出）": "deg (derived from the radius)",
    "無因次": "Dimensionless",
    "N/m（單輪）": "N/m (per wheel)",
    "是否使用 Tender 彈簧": "Whether the tender spring is enabled",
    "N/m（本次採用的 Heave 剛性）": "N/m (active heave stiffness)",
    "g（沿用 ax）": "g (uses ax)",
    "N/m（由共用剛性比計算的前軸車體等效剛性）": "N/m (equivalent front chassis stiffness from the shared ratio)",
    "N/m（由共用剛性比計算的後軸車體等效剛性）": "N/m (equivalent rear chassis stiffness from the shared ratio)",
    "參數": "Parameter",
    "本次值": "Current value",
    "單位／定義": "Unit or definition",
    "比例／無因次": "Ratio or dimensionless",
    "1. CG：重心高度與傾斜幾何檢查": "1. CG height and tilt geometry checks",
    "{angle}° 判定：**{status}**。": "{angle}° check: **{status}**.",
    "臨界（無高度餘裕）": "At the limit (no height margin)",
    "通過幾何檢查": "Passes the geometry check",
    "超過幾何上限": "Exceeds the geometric limit",
    "這是左右對稱、無懸吊變形的幾何檢查。":
        "The geometry check assumes left-right symmetry and a rigid suspension.",
    "2. Skidpad：目標圈速與所需下壓力": "2. Skidpad target lap time and required downforce",
    "2.4 空力有效面積與目標係數": "2.4 Effective aerodynamic area and target coefficients",
    "係數以下壓力為正；C 採指定公式，Cl 對照原 Aero_Cl_Cd 定義。完整需求不乘下壓力施加比例。":
        "Downforce is positive. C uses the specified equation and Cl follows the original Aero_Cl_Cd definition. "
        "The full requirement is calculated before applying the downforce fraction.",
    "3. 指定 Pitch／Roll 角度所需剛性": "3. Stiffness required for the target pitch and roll angles",
    "此處 K 是原角度分析的等效需求剛性；與單支彈簧簧率不同。":
        "K is the equivalent stiffness required by the angle analysis. An individual spring rate is calculated separately.",
    "4. Compressed travel：行程限制": "4. Compression travel limit",
    "5. Frequency vs stiffness：較高需求剛性": "5. Natural frequency at the governing stiffness",
    "6. Tire stiffness：輪胎柔度與彈簧簧率": "6. Tire compliance and spring rates",
    "計入輪胎柔度後的 Pitch 簧率是前後 Heave 主簧的簧率，也是第 9 節反算 Tender 的主簧基準。":
        "The pitch spring rate corrected for tire compliance is the main heave spring rate at both axles. Section 9 uses it to size the tender spring.",
    "{mode}：使用兩條輪胎的等效剛性": "{mode}: Equivalent stiffness of two tires",
    "一般 Ks 沿用原模型：20,000～80,000 N/m 之間 2,000 個等距候選，選 ride rate 誤差最小者。":
        "The model tests 2,000 evenly spaced Ks values from 20,000 to 80,000 N/m and selects the one with the smallest ride-rate error.",
    "7. Frequency vs mass：簧上與簧下頻率": "7. Sprung and unsprung natural frequencies",
    "8. 固定 Roll，反算 Heave": "8. Calculate target heave stiffness with fixed roll stiffness",
    "使用指定的 Tender 目標簧上自然頻率，固定 Roll 剛性反算 Heave 串聯剛性。":
        "Use the specified tender target sprung natural frequency and hold roll stiffness fixed to calculate the required heave series rate.",
    "**Tender 已關閉（use_tender = False）。** 跳過 Heave 反算與 Tender 可行性計算，直接使用原 Heave 主簧剛性。":
        "**The tender spring is disabled (use_tender = False).** The calculation uses the original main heave spring rate.",
    "以新 Heave 和固定 Roll 代回第 7 節的同一公式，回算頻率如下。":
        "The frequencies below use the Section 7 equations with the revised heave rate and fixed roll rate.",
    "調整後簧上頻率 Hz": "Adjusted sprung frequency (Hz)",
    "調整後簧下頻率 Hz": "Adjusted unsprung frequency (Hz)",
    "**無可行正 Heave 解：**{reason}": "**No feasible positive heave stiffness.** {reason}",
    "目標頻率所需的 ride rate 不小於輪胎剛性 Kt，無有限正剛性解。":
        "The target ride rate is at least as high as the tire stiffness Kt, so no finite positive spring rate can achieve it.",
    "目標頻率過低；固定目前 Roll 剛性時，沒有正的 heave 剛性可達成。":
        "With the current roll stiffness held fixed, the target frequency is too low for any positive heave stiffness.",
    "9. 主 Heave 與 Tender 串聯": "9. Main heave and tender springs in series",
    "Tender 已關閉，略過串聯彈簧設計；Heave 與 Heave & Roll 組合均直接使用原主簧剛性。":
        "The tender spring is disabled. Both the heave case and the combined heave and roll case use the main spring rate.",
    "**Tender 無可行解。** 前序 Heave 目標不可行，或目標未低於主簧剛性。依賴 Tender 的數值不填入 0。":
        "**No feasible tender spring solution.** The heave target is infeasible or is at least as high as the main spring rate. "
        "Tender-dependent results are unavailable.",
    "串聯剛性僅適用於 Tender 未併圈階段。": "The series spring rate applies before the tender spring reaches coil bind.",
    "9.3 前 Anti-dive 與 9.4 加速／煞車 Anti 設定": "9.3 Front anti-dive and 9.4 acceleration and braking anti settings",
    "Roll Center、前 Anti 與後 Anti 共用車體／懸吊剛性比 c。"
    "Anti 使用各軸純 Heave 主簧換算軸端垂向剛性 Kz，再乘以 c 得到車體等效剛性 Kc，兩者單位均為 N/m。":
        "Roll center and both anti settings share the chassis-to-suspension stiffness ratio c. "
        "For anti, the main heave spring gives each axle's vertical suspension stiffness Kz. "
        "Multiplying Kz by c gives the equivalent chassis stiffness Kc. Both stiffnesses are in N/m.",
    "純 Heave": "Main heave spring only",
    "前軸剛性基準（前 Anti-dive）": "Front axle stiffness basis for anti-dive",
    "後軸剛性基準（後 Anti-squat 來源）": "Rear axle stiffness basis for anti-squat",
    "前 Anti-dive、後 Anti-squat 與前後 Anti-lift": "Front anti-dive, rear anti-squat, and front and rear anti-lift",
    "設定項目": "Setting",
    "比例": "Ratio",
    "百分比": "Percent",
    "來源": "Basis",
    "前 Anti-dive": "Front anti-dive",
    "前軸剛性基準": "Front axle stiffness basis",
    "後 Anti-lift": "Rear anti-lift",
    "等於前 Anti-dive": "Equal to front anti-dive",
    "後 Anti-squat": "Rear anti-squat",
    "後軸剛性基準 × a_acc / ax": "Rear axle stiffness basis × a_acc / ax",
    "前 Anti-lift": "Front anti-lift",
    "等於後 Anti-squat": "Equal to rear anti-squat",
    "前 Anti": "Front anti setting",
    "取前 Anti-dive 與前 Anti-lift 的較大值": "Greater of front anti-dive and front anti-lift",
    "後 Anti": "Rear anti setting",
    "取後 Anti-squat 與後 Anti-lift 的較大值": "Greater of rear anti-squat and rear anti-lift",
    "Anti 使用純 Heave 主簧。後 Anti-squat 由後軸剛性基準乘以 a_acc／ax 得出。"
    "程式參數 a_acc 對應加速目標，與 ax 均以 g 輸入。此為兩路剛性類比及指定比例設定；幾何硬點與實際煞車力路徑不在此求解。":
        "The anti settings use the main heave spring. Rear anti-squat is the rear stiffness basis multiplied by a_acc / ax. "
        "Both inputs are expressed in g, with a_acc representing the acceleration target. "
        "The model approximates two stiffness paths. Suspension hardpoints and actual brake-force paths are outside this calculation.",
    "加速工況將前 Anti-lift 設為後 Anti-squat。以 Dynamics 的全車力公式套用相同係數時，"
    "前後驅動力各占 50% 會得到相同大小的前後 Anti 力矩貢獻。":
        "Under acceleration, front anti-lift equals rear anti-squat. Using the same coefficients in the Dynamics vehicle "
        "force equations, a 50:50 drive-force split gives equal front and rear anti moment magnitudes.",
    "10. 前 Roll Center 與 11. 後 Roll Center": "10. Front roll center and 11. rear roll center",
    "11.1 FVSA 與 Camber gain": "11.1 Front-view swing arm and camber gain",
    "保留指定的公尺數值公式。tan 的引數使用公尺數值約定，不能將 d 改成毫米後直接代入；"
    "deg/mm 是單位比例換算，最大 Camber 變化採指定的線性外推。":
        "Use the numeric value of d in meters in the tangent function. Convert the result separately to deg/mm. "
        "The maximum camber change uses the specified linear extrapolation.",
    "前軸": "Front axle",
    "後軸": "Rear axle",
    "11.2 純 ay 的輪胎壓縮與額外 Roll": "11.2 Tire compression and additional roll under lateral acceleration",
    "這是各軸獨立的兩輪模型，無 ax、無空力；各軸承載質量依前後重量比例分配。":
        "Each axle is modeled independently as two wheels with zero longitudinal acceleration and downforce. "
        "Axle masses follow the front and rear weight distribution.",
    "**接地有效。**": "**Both tires remain in contact.**",
    "**接地失效：存在負輪載。** 上述負壓縮及 Roll 為線性外推參考；有效接地 Roll 為 None，不代表輪胎可承受拉力。":
        "**The contact assumption fails because a wheel load is negative.** Negative compression and roll are linear "
        "extrapolations for reference only. The roll value for valid contact is unavailable because a tire cannot carry tension.",
    "靜態單輪壓縮 m": "Static compression per wheel (m)",
    "ay 引起左側增量 m": "Left compression change due to ay (m)",
    "ay 引起右側增量 m": "Right compression change due to ay (m)",
    "接地界限 g": "Contact limit (g)",
    "離地臨界": "At the lift threshold",
    "11.3 最小半徑轉角、方向查核與 Caster": "11.3 Minimum-radius steering angle, sign check, and caster",
    "單軌等效前輪角取已確認的正方向。方向查核以固定 Caster 比較正、負轉向角。整式的座標負號固定為 −1。":
        "The bicycle-model equivalent front steering angle uses the established positive direction. "
        "The sign check compares positive and negative steering angles at fixed caster. The coordinate sign factor is −1.",
    "方向驗證 Caster deg": "Caster for sign check (deg)",
    "轉向角 deg": "Steering angle (deg)",
    "原式 Camber 變化 deg": "Raw camber change (deg)",
    "**Caster 算式有實數解，接地模型失效。** 本節 Camber 與 Caster 僅為線性外推參考。":
        "**The caster equation has a real solution, but the contact model fails.** The camber and caster values in this section "
        "are linear extrapolations for reference.",
    "**Caster 狀態：{status}。** {reason}": "**Caster status: {status}.** {reason}",
    "delta = 0 且原 Camber 已為 0，無法決定唯一 Caster。":
        "Steering angle and initial camber are both zero, so the model cannot determine a unique caster angle.",
    "delta = 0，轉向不會產生 Camber 變化。": "At zero steering angle, steering produces no camber change.",
    "固定轉向角下所需 sin(caster) 超出 [-1, 1]，無實數解。":
        "At the fixed steering angle, the required sin(caster) lies outside [-1, 1]. No real solution exists.",
    "12. 下壓力造成的 Tender 壓縮": "12. Tender spring compression under downforce",
    "Tender 已關閉，略過 Tender 串聯壓縮計算。": "The tender spring is disabled, so the series compression calculation is skipped.",
    "**無可行 Tender，串聯壓縮不計算。**": "**Series compression is unavailable without a feasible tender spring.**",
    "前後各一組相同彈簧，Heave 等於同一總壓縮量；零點為原平衡位置，只算空力增量。"
    "沿用 Tender 設計，此下壓力為併圈切換點，不把它當成任意工況下都已併圈。":
        "The front and rear each use an identical spring assembly, so the heave displacement equals the total compression "
        "of one assembly. Displacement is measured from the original equilibrium and includes only the aerodynamic increment. "
        "This downforce is the design transition point for tender coil bind.",
    "13. 空力及 ax／ay 下的四輪受力": "13. Four-wheel loads and forces under downforce, ax, and ay",
    "**接地失效，以下三向需求力為參考。** 原始負輪載保留；截零後的總正向力與原始垂向力平衡不同。":
        "**The contact assumption fails, so the three-axis force demands below are for reference.** "
        "The original negative wheel loads are shown. Clipping them to zero changes the sum of vertical forces.",
    "輪位": "Wheel",
    "原始 Fz N": "Raw Fz (N)",
    "分配後 Fx N": "Allocated Fx (N)",
    "分配後 Fy N": "Allocated Fy (N)",
    "截零 Fz N": "Clipped Fz (N)",
    "合力 N": "Resultant force (N)",
    "載重占比": "Load share",
    "最大參考合力輪位：**{wheel}**。": "Wheel with the largest reference resultant force: **{wheel}**.",
    "最大合力輪位：**{wheel}**。": "Wheel with the largest resultant force: **{wheel}**.",
    "14. 無空力加速與極速齒比": "14. Acceleration and top-speed gear ratios without downforce",
    "工況為 ax = a_acc、ay = 0、下壓力 = 0；前後軸按輪載分配需求力，每軸兩輪、每輪一顆馬達。":
        "The case uses ax = a_acc, ay = 0, and zero downforce. The required force is distributed by axle load, "
        "with two wheels per axle and one motor per wheel.",
    "15. 無空力煞車力、前後比與回歸": "15. Brake forces, front-rear split, and fit without downforce",
    "z 取輸入的縱向加速度 ax 作為煞車減速度（g）。煞車時車身縱向加速度為 −z。"
    "指定需求與輪胎摩擦可達性分開列出。":
        "The longitudinal acceleration input ax supplies the braking deceleration z in g. "
        "Vehicle acceleration during braking is −z. "
        "The requested deceleration and the tire friction limit are shown separately.",
    "指定工況": "Requested case",
    "可達設計上限": "Feasible design case",
    "指定減速度可達：**{result}**。": "Requested deceleration is feasible: **{result}**.",
    "十點通過原點的最小平方擬合": "Ten-point least-squares fit through the origin",
    "減速度 g": "Deceleration (g)",
    "前煞車力 N": "Front brake force (N)",
    "後煞車力 N": "Rear brake force (N)",
    "前比": "Front share",
    "後比": "Rear share",
    "16. 煞車機構整體等效機械利益": "16. Overall equivalent brake mechanical advantage",
    "此倍率是腳力至四輪接地總煞車力的整體等效值；硬體槓桿、液壓與制動半徑仍需另行分配。":
        "This ratio relates pedal force to the total braking force at the four tire contact patches. "
        "The pedal lever, hydraulics, and effective braking radius must be sized separately.",
    "17. Roll、Heave + Tender 與純 Heave 的前後臨界阻尼": "17. Front and rear critical damping for roll, heave with tender, and main heave",
    "17. Roll 與純 Heave 的前後臨界阻尼": "17. Front and rear critical damping for roll and main heave",
    "每軸各一支 Roll 和 Heave 阻尼器；彈簧與阻尼器共用 MR。此節採固定輪端的單自由度參考。":
        "Each axle has one roll damper and one heave damper. The springs and dampers use the same motion ratio. "
        "This section uses a single-degree-of-freedom reference with fixed wheel ends.",
    "Ixx 為手動指定的簧上 CG 慣量；修改車體質量分布時需同步更新此輸入，質量改動不會自動推估新的慣量。":
        "Ixx is the supplied sprung-mass inertia about the CG. Update this input when the mass distribution changes. "
        "Changing the mass alone does not recalculate inertia.",
    "Tender 無可行解，此組阻尼不計算。": "Damping for this case is unavailable without a feasible tender spring.",
    "Dynamics 匯出剛性、阻尼與車架傳力": "Dynamics export stiffness, damping, and chassis load transfer",
    "heave_f_k 與 heave_r_k 儲存實體 Heave 主簧簧率，SuspensionDynamicsLab 直接使用這兩個剛性值。Heave 阻尼換算至雙輪位移總和座標後匯出。"
    "Roll 使用阻尼器端係數，四輪使用相同的胎剛性與單輪簧下質量。":
        "heave_f_k and heave_r_k store the physical main heave spring rates, which SuspensionDynamicsLab uses directly. Exported heave damping uses the sum of the two wheel displacements as its coordinate. "
        "Roll uses the damper-side coefficient. All four wheels use the same tire stiffness and per-wheel unsprung mass.",
    "車架傳力採選定的線性 Roll 剛性（N/m）。": "The chassis load-transfer model uses the selected linear roll stiffness (N/m).",
    "18. 四種指定 Ks：前後 Ks → Kw → Kr、自然頻率、臨界阻尼與目標阻尼":
        "18. Four Ks cases: Axle spring, wheel, and ride rates, natural frequencies, and damping",
    "Kht 為 Heave 與 Tender 的串聯值。": "Kht is the combined rate of the heave and tender springs in series.",
    "Tender 已關閉，Kh 直接使用原 Heave 主簧剛性；Heave & Roll 採 (Kh + Kroll)/2。":
        "The tender spring is disabled. Kh is the original main heave spring rate. The combined heave and roll case uses (Kh + Kroll)/2.",
    "本節依指定除以 2，各 Ks 作單輪線性等效比較；第 7 節原 Frequency vs mass 的除以 4 模式仍另行保留。":
        "This section divides by two for a linear per-wheel comparison of each Ks. The frequency calculation in Section 7 uses its own factor of four.",
    "{axle}：{case}": "{axle}: {case}",
    "Tender 無可行解，這個 Ks 案例不計算。": "This Ks case is unavailable without a feasible tender spring.",
    "軸別": "Axle",
    "案例": "Case",
    "Kr 臨界阻尼 N·s/m": "Kr critical damping (N·s/m)",
    "Kr 目標阻尼 N·s/m": "Kr target damping (N·s/m)",
    "fKs = fKw 是座標一致性的結果。Kr 的臨界與目標阻尼為 ride 等效單自由度參考，不直接代表實體阻尼器係數；"
    "Kroll 案例也不是以轉動慣量求得的整車 Roll 模態頻率。":
        "fKs equals fKw because both use consistent coordinates. Kr critical and target damping are equivalent "
        "single-degree-of-freedom ride references. Physical damper coefficients require a separate conversion. "
        "The Kroll case uses per-wheel motion. The full-vehicle roll mode would use rotational inertia.",
    "19. Roll 與 Pitch gradient": "19. Roll and pitch gradients",
    "以整車慣性力及各固定切線剛性階段求準靜態小角度斜率，單位 deg/g；空力不增加慣性質量。":
        "The quasi-static small-angle gradients use vehicle inertial forces and the tangent stiffness in each stage. "
        "The unit is deg/g. Downforce changes loading while inertial mass stays constant.",
    "跨越 Tender 併圈點時改用相應階段，空力影響載重及所處階段。":
        "Use the corresponding stiffness stage when the tender spring reaches coil bind. Downforce affects loading and can change the active stage.",
    "Tender 已關閉，Pitch gradient 直接使用原 Heave 主簧剛性。":
        "The tender spring is disabled, so the pitch gradient uses the original main heave spring rate.",
    "僅懸吊": "Suspension only",
    "含輪胎柔度": "Including tire compliance",
    "前後 Anti 修正僅用於純 Heave 主簧的煞車工況，使用設定後的前 Anti-dive 與後 Anti-lift；後 Anti-lift 等於前 Anti-dive。":
        "Apply the front and rear anti corrections to the main-heave braking case using the configured front anti-dive "
        "and rear anti-lift. Rear anti-lift equals front anti-dive.",
    "Pitch：{mode}": "Pitch: {mode}",
    "Tender 無可行解，此階段不計算。": "This stage is unavailable without a feasible tender spring.",
    "純 Heave 主簧工況的前 Anti-dive 與後 Anti-lift 各自減少該軸的懸吊變形，再相加為整車 Pitch；"
    "輪胎變形保留完整負載轉移的部分。Pitch 每軸一組彈簧，與第 18 節單輪等效案例的座標及彈簧數量不同。":
        "In the main-heave case, front anti-dive and rear anti-lift reduce suspension deflection at their respective axles. "
        "The two contributions add to vehicle pitch. Tire deflection still reflects the full load transfer. "
        "The pitch model uses one spring assembly per axle and different coordinates from the per-wheel cases in Section 18.",
}
