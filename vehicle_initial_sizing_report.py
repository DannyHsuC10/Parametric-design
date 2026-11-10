"""Render the calculation run supplied by vehicle_initial_sizing, using only the standard library."""

import csv
from datetime import datetime, timedelta, timezone
from io import StringIO
import math
import re

from dynamics_export import damping_coefficients, frame_parameters
from report_english import ENGLISH
from vehicle_initial_sizing import calculate_roll_axle_stiffness


def build_report(snapshot, language="zh"):
    p = snapshot["parameters"]
    summary = [
        {"label": "整車總質量", "value": f"{snapshot['frequency_mass']['m_total_vehicle_kg']:.2f}", "unit": "kg"},
        {"label": "前軸靜態重量分配", "value": f"{p['wf'] * 100:.1f}", "unit": "%"},
        {"label": "Skidpad 所需下壓力", "value": f"{snapshot['skidpad']['skidpad_required_aero_downforce_N']:.1f}", "unit": "N"},
        {"label": "Roll gradient（含輪胎）",
         "value": f"{snapshot['gradients']['roll_gradient_with_tires_deg_per_g']:.3f}", "unit": "°/g"},
    ]
    if language == "en":
        for metric in summary:
            metric["label"] = ENGLISH[metric["label"]]
    return {"language": language, "markdown": render_markdown_report(snapshot, language), "summary": summary}


def _number(value, unavailable="無可用解"):
    if value is None:
        return rf"\text{{{unavailable}}}"
    if math.isinf(value):
        return r"\infty" if value > 0 else r"-\infty"
    rendered = format(value, ".12g")
    if "e" in rendered:
        mantissa, exponent = rendered.split("e")
        return mantissa + r"\times10^{" + str(int(exponent)) + "}"
    return rendered


def _flatten(value, prefix=""):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _flatten(child, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(value, (tuple, list)):
        for index, child in enumerate(value):
            yield from _flatten(child, f"{prefix}[{index}]")
    else:
        yield prefix, value


def iter_result_rows(snapshot):
    for section, values in snapshot.items():
        if isinstance(values, (dict, list, tuple)):
            yield from ((section, field, value) for field, value in _flatten(values))
        else:
            yield section, section, values


def render_csv_results(snapshot):
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(("section", "field", "value"))
    writer.writerows(iter_result_rows(snapshot))
    return output.getvalue()


class MarkdownReport:
    def __init__(self, language):
        self.parts = []
        self.messages = ENGLISH if language == "en" else {}

    def translate(self, value):
        return self.messages.get(value, value)

    def text(self, value, **fields):
        value = self.translate(value)
        if fields:
            value = value.format(**fields)
        self.parts.append(value.strip() + "\n\n")

    def heading(self, value, level=2, **fields):
        value = self.translate(value)
        if fields:
            value = value.format(**fields)
        self.parts.append("#" * level + " " + value + "\n\n")

    def eq(self, formula, substitution=None, **numbers):
        # 跨行公式字串以 \quad{} 分隔，避免接合後變成 \quadc、\quadm 等無效指令。
        self.text("$$\n" + self.translate(formula) + "\n$$")
        if substitution is not None:
            unavailable = self.translate("無可用解")
            filled = re.sub(r"@([A-Za-z_][A-Za-z_0-9]*)@",
                            lambda match: _number(numbers[match.group(1)], unavailable), substitution)
            self.text("$$\n" + filled + "\n$$")

    def cell(self, value):
        if value is None:
            return self.translate("—（無可用解）")
        if isinstance(value, bool):
            return self.translate("是" if value else "否")
        if isinstance(value, (int, float)):
            if math.isinf(value):
                return "∞" if value > 0 else "−∞"
            return format(value, ".12g")
        return self.translate(str(value)).replace("|", r"\|").replace("\n", "<br>")

    def table(self, headers, rows):
        headers = [self.translate(header) for header in headers]
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
        lines.extend("| " + " | ".join(self.cell(value) for value in row) + " |" for row in rows)
        self.text("\n".join(lines))


FLOW = """```mermaid
graph TD
    A["當次參數與重量分配"] --> B["CG 檢查"]
    B --> C["Skidpad 下壓力與空力係數"]
    C --> D["角度／行程剛性取較高值"]
    D --> E["輪胎柔度與自然頻率"]
    E --> T{"使用 Tender？"}
    T -->|"是"| F["Heave 反算與 Tender 可行性"]
    T -->|"否"| HF["直接使用原 Heave 主簧剛性"]
    HF --> G
    F --> G["前後剛性基準 → 煞車與加速 Anti；前後 RC"]
    G --> H["FVSA、輪胎 Roll、半徑求轉角與 Caster"]
    H --> I["空力載重與四輪受力；Tender 啟用時另算串聯壓縮"]
    I --> J["齒比、煞車與機械利益"]
    J --> K["前後阻尼、四組 Ks→Kw→Kr"]
    K --> L["Roll／Pitch gradient"]
    L --> M["本次結果與 LaTeX 數值代入"]
    M --> N["預覽或儲存 Markdown 報告"]
```"""


def render_markdown_report(snapshot, language="zh"):
    r = MarkdownReport(language)
    stamp = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    r.heading("車輛初步設計估算報告", 1)
    r.text("產生時間：{stamp}（Asia/Taipei）。本報告由 Vehicle Initial Sizing Lab 依本次求解結果產生。", stamp=stamp)
    r.text("在左側調整車重、幾何或其他參數後按「求解」，即可更新本次參數、數值代入與結果。"
           "公式內角度使用 rad，度數另行換算；"
           "計算保留原始精度，報告數字顯示最多 12 位有效數字。")
    r.heading("計算流程")
    r.text(re.sub(r'"([^"]+)"', lambda match: '"' + r.translate(match[1]) + '"', FLOW))
    _render_basics(r, snapshot)
    _render_loads(r, snapshot)
    _render_modes(r, snapshot)
    r.heading("更新方式")
    r.text("在 Vehicle Initial Sizing Lab 調整左側參數並按「求解」。"
           "完整結果可匯出為 CSV 或 Excel。Excel 另附欄位說明與單位。")
    return "".join(r.parts)


def _render_basics(r, s):
    p = s["parameters"]
    M = s["frequency_mass"]["m_total_vehicle_kg"]
    r.heading("0. 本次輸入、質量與幾何")
    units = {
        "ms": "kg（全車簧上）", "mu": "kg（單輪簧下）", "h_cog": "m", "lf": "m", "lr": "m",
        "L": "m", "tf": "m", "tr": "m", "t": "m", "sus_travel": "m", "min_turn_radius_m": "m",
        "steering_angle_deg": "deg（由半徑導出）", "MR": "無因次", "Kt": "N/m（單輪）",
        "A_air": "m²", "air_density_kg_per_m3": "kg/m³", "g": "m/s²",
        "ax": "g", "ay": "g", "a_acc": "g", "brake_ax": "g", "target_lap_time_s": "s",
        "drive_target_speed_kmh": "km/h", "R_tire": "m", "drive_motor_torque_Nm": "N·m",
        "drive_motor_rpm": "rpm", "brake_driver_force_N": "N", "sprung_roll_inertia_kg_m2": "kg·m²",
        "target_pitch_angle_deg": "deg", "target_roll_angle_deg": "deg", "kpi_deg": "deg",
        "use_tender": "是否使用 Tender 彈簧",
        "active_heave_spring_N_per_m": "N/m（本次採用的 Heave 剛性）",
        "anti_front_chassis_stiffness_N_per_m": "N/m（前軸車體垂向等效剛性，固定估值）",
        "anti_rear_chassis_stiffness_N_per_m": "N/m（後軸車體垂向等效剛性，固定估值）",
    }
    r.table(["參數", "本次值", "單位／定義"], ((key, value, units.get(key, "比例／無因次")) for key, value in p.items()))
    r.eq(r"L=l_f+l_r", r"L=@f@+@b@=@L@\ \mathrm{m}", f=p["lf"], b=p["lr"], L=p["L"])
    r.eq(r"w_f=\frac{l_r}{L},\quad w_r=\frac{l_f}{L}",
         r"w_f=\frac{@b@}{@L@}=@wf@,\quad w_r=\frac{@f@}{@L@}=@wr@",
         b=p["lr"], L=p["L"], f=p["lf"], wf=p["wf"], wr=p["wr"])
    r.eq(r"M=M_s+4m_u", r"M=@ms@+4\cdot@mu@=@M@\ \mathrm{kg}", ms=p["ms"], mu=p["mu"], M=M)
    r.eq(r"m_{s,q}=\frac{M_s}{4}", r"m_{s,q}=\frac{@ms@}{4}=@m@\ \mathrm{kg}",
         ms=p["ms"], m=s["frequency_mass"]["quarter_sprung_mass_kg"])

    r.heading("1. CG：重心高度與傾斜幾何檢查")
    cg = s["cg"]
    r.eq(r"h_{\max}=\frac{\min(t_f,t_r)}{2S_F\tan\beta},\quad \mathrm{margin}=h_{\max}-h")
    for angle in (45, 60):
        limit, margin = cg[f"cg_height_limit_{angle}_m"], cg[f"cg_height_margin_{angle}_m"]
        r.eq(r"\beta=" + str(angle) + r"^\circ",
             r"h_{\max}=\frac{@t@}{2\cdot@sf@\cdot\tan(@a@)}=@limit@\ \mathrm{m}",
             t=cg["cg_min_track_m"], sf=p["cg_safety_factor"], a=math.radians(angle), limit=limit)
        r.eq(r"\mathrm{margin}=h_{\max}-h", r"\mathrm{margin}=@limit@-@h@=@margin@\ \mathrm{m}",
             limit=limit, h=p["h_cog"], margin=margin)
        r.text("{angle}° 判定：**{status}**。", angle=angle, status=r.translate(cg[f"cg_status_{angle}"]))
    r.text("這是左右對稱、無懸吊變形的幾何檢查。")

    q = s["skidpad"]
    v, ay = q["skidpad_target_speed_m_per_s"], q["skidpad_target_lateral_acceleration_m_per_s2"]
    D, factor = q["skidpad_diameter_m"], q["skidpad_safety_factor"]
    down = q["skidpad_required_aero_downforce_N"]
    r.heading("2. Skidpad：目標圈速與所需下壓力")
    r.eq(r"R_{\mathrm{skid}}=\frac{D}{2},\quad v=\frac{\pi D}{T}",
         r"R_{\mathrm{skid}}=\frac{@D@}{2}=@R@\ \mathrm{m},\quad v=\frac{\pi\cdot@D@}{@T@}=@v@\ \mathrm{m/s}",
         D=D, R=D / 2, T=p["target_lap_time_s"], v=v)
    r.eq(r"a_y=\frac{v^2}{R_{\mathrm{skid}}},\quad \mu_{\mathrm{req}}=\eta\frac{a_y}{g}",
         r"a_y=\frac{@v@^2}{@R@}=@a@\ \mathrm{m/s^2},\quad\mu_{\mathrm{req}}=@eta@\frac{@a@}{@g@}=@mu@",
         v=v, R=D / 2, a=ay, eta=factor, g=p["g"], mu=q["skidpad_target_required_mu"])
    r.eq(r"F_{\mathrm{raw}}=\left(\frac{\mu_{\mathrm{req}}}{\mu_y}-1\right)Mg",
         r"F_{\mathrm{raw}}=\left(\frac{@mu@}{@muy@}-1\right)\cdot@M@\cdot@g@=@F@\ \mathrm{N}",
         mu=q["skidpad_target_required_mu"], muy=p["wl_mu_y"], M=M, g=p["g"], F=q["F_ref"])
    r.eq(r"F_{\mathrm{down}}=\max(0,F_{\mathrm{raw}})",
         r"F_{\mathrm{down}}=\max(0,@raw@)=@F@\ \mathrm{N}", raw=q["F_ref"], F=down)

    r.heading("2.4 空力有效面積與目標係數")
    r.eq(r"F=C\rho Av^2,\qquad C=\frac{F}{\rho Av^2}",
         r"C=\frac{@F@}{@rho@\cdot@A@\cdot@v@^2}=@C@",
         F=down, rho=p["air_density_kg_per_m3"], A=p["A_air"], v=v, C=s["aero"]["target_coefficient_C"])
    r.eq(r"F=\frac{1}{2} Cl\rho Av^2,\qquad Cl=2C",
         r"Cl=2\cdot@C@=@Cl@", C=s["aero"]["target_coefficient_C"], Cl=s["aero"]["standard_downforce_coefficient_Cl"])
    r.text("係數以下壓力為正；C 採指定公式，Cl 對照原 Aero_Cl_Cd 定義。完整需求不乘下壓力施加比例。")

    r.heading("3. 指定 Pitch／Roll 角度所需剛性")
    r.eq(r"s=\frac{\ell}{2}\theta,\quad \mathcal{M}=M_s|a_g|gh,\quad K=\frac{\mathcal{M}}{\ell s}")
    for mode, span, accel, angle in (
        ("pitch", p["L"], abs(p["ax"]), p["target_pitch_angle_deg"]),
        ("roll", p["t"], abs(p["ay"]), p["target_roll_angle_deg"]),
    ):
        data = s["angle_stiffness"][mode]
        r.heading(mode.title(), 3)
        r.eq(r"s=\frac{\ell}{2}\theta",
             r"s=\frac{@span@}{2}\cdot@theta@=@s@\ \mathrm{m}",
             span=span, theta=math.radians(angle), s=data["displacement_m"])
        r.eq(r"K=\frac{M_s|a_g|gh}{\ell s}",
             r"K=\frac{@ms@\cdot@a@\cdot@g@\cdot@h@}{@span@\cdot@disp@}=@K@\ \mathrm{N/m}",
             ms=p["ms"], a=accel, g=p["g"], h=p["h_cog"], span=span, disp=data["displacement_m"],
             K=data["stiffness_N_per_m"])
    r.text("此處 K 是原角度分析的等效需求剛性；與單支彈簧簧率不同。")

    r.heading("4. Compressed travel：行程限制")
    for mode, span, accel in (("pitch", p["L"], abs(p["ax"])), ("roll", p["t"], abs(p["ay"]))):
        data = s["compressed_travel"][mode]
        r.heading(mode.title(), 3)
        r.eq(r"K_{\mathrm{travel}}=\frac{M_s|a_g|gh}{\ell d}",
             r"K_{\mathrm{travel}}=\frac{@ms@\cdot@a@\cdot@g@\cdot@h@}{@span@\cdot@d@}=@K@\ \mathrm{N/m}",
             ms=p["ms"], a=accel, g=p["g"], h=p["h_cog"], span=span, d=p["sus_travel"], K=data["stiffness_N_per_m"])
        r.eq(r"\theta_{\mathrm{travel}}=\arctan\left(\frac{2d}{\ell}\right)\frac{180}{\pi}",
             r"\theta_{\mathrm{travel}}=\arctan\left(\frac{2\cdot@d@}{@span@}\right)\frac{180}{\pi}=@a@^\circ",
             d=p["sus_travel"], span=span, a=data["angle_deg"])

    r.heading("5. Frequency vs stiffness：較高需求剛性")
    for mode in ("pitch", "roll"):
        data = s["selected_stiffness"][mode]
        r.heading(mode.title(), 3)
        r.eq(r"K_{\mathrm{selected}}=\max(K_{\mathrm{angle}},K_{\mathrm{travel}})",
             r"K_{\mathrm{selected}}=\max(@a@,@t@)=@K@\ \mathrm{N/m}",
             a=s["angle_stiffness"][mode]["stiffness_N_per_m"], t=s["compressed_travel"][mode]["stiffness_N_per_m"],
             K=data["stiffness_N_per_m"])
        r.eq(r"f_n=\frac{1}{2\pi}\sqrt{\frac{K_{\mathrm{selected}}}{M_s/2}}",
             r"f_n=\frac{1}{2\pi}\sqrt{\frac{@K@}{@ms@/2}}=@f@\ \mathrm{Hz}",
             K=data["stiffness_N_per_m"], ms=p["ms"], f=data["frequency_Hz"])

    r.heading("6. Tire stiffness：輪胎柔度與彈簧簧率")
    tire = s["tire"]
    r.eq(r"K_w=K_sMR^2,\qquad K_r=\frac{K_wK_t}{K_w+K_t}")
    for mode in ("pitch", "roll"):
        target = s["selected_stiffness"][mode]["stiffness_N_per_m"]
        rate = tire[f"Ks_{mode}_N_per_m"]
        r.heading("{mode}：使用兩條輪胎的等效剛性", 3, mode=mode.title())
        r.eq(r"K_{s,j}=\frac{K_j(2K_t)}{(2K_t-K_j)MR^2}",
             r"K_{s,j}=\frac{@K@\cdot(2\cdot@Kt@)}{(2\cdot@Kt@-@K@)\cdot@mr@^2}=@Ks@\ \mathrm{N/m}",
             K=target, Kt=p["Kt"], mr=p["MR"], Ks=rate)
    r.eq(r"K_{\mathrm{ride,target}}=\frac{K_p+K_{\mathrm{roll}}}{4}",
         r"K_{\mathrm{ride,target}}=\frac{@p@+@r@}{4}=@K@\ \mathrm{N/m}",
         p=s["selected_stiffness"]["pitch"]["stiffness_N_per_m"], r=s["selected_stiffness"]["roll"]["stiffness_N_per_m"],
         K=tire["target_ride_rate_N_per_m"])
    r.text("一般 Ks 沿用原模型：20,000～80,000 N/m 之間 2,000 個等距候選，選 ride rate 誤差最小者。")
    r.eq(r"K_s^*=\mathrm{argmin}_{K_s}\left|\frac{K_sMR^2K_t}{K_sMR^2+K_t}-K_{\mathrm{ride,target}}\right|",
         r"K_s^*=@Ks@\ \mathrm{N/m},\qquad K_{\mathrm{ride,actual}}=@Kr@\ \mathrm{N/m}",
         Ks=tire["Ks"], Kr=tire["actual_ride_rate_N_per_m"])

    r.heading("7. Frequency vs mass：簧上與簧下頻率")
    fm = s["frequency_mass"]
    r.eq(r"K_{s,\mathrm{eq}}=\frac{K_{s,\mathrm{roll}}+K_{s,\mathrm{pitch}}}{4}",
         r"K_{s,\mathrm{eq}}=\frac{@r@+@p@}{4}=@K@\ \mathrm{N/m}",
         r=tire["Ks_roll_N_per_m"], p=tire["Ks_pitch_N_per_m"], K=fm["equivalent_spring_stiffness_N_per_m"])
    r.eq(r"K_w=K_{s,\mathrm{eq}}MR^2,\quad K_r=\frac{K_wK_t}{K_w+K_t}",
         r"K_w=@Ks@\cdot@mr@^2=@Kw@,\quad K_r=\frac{@Kw@\cdot@Kt@}{@Kw@+@Kt@}=@Kr@\ \mathrm{N/m}",
         Ks=fm["equivalent_spring_stiffness_N_per_m"], mr=p["MR"], Kw=fm["wheel_rate_N_per_m"],
         Kt=p["Kt"], Kr=fm["ride_rate_N_per_m"])
    r.eq(r"f_s=\frac{1}{2\pi}\sqrt{\frac{K_r}{M_s/4}},\quad f_u=\frac{1}{2\pi}\sqrt{\frac{K_t+K_w}{m_u}}",
         r"f_s=\frac{1}{2\pi}\sqrt{\frac{@Kr@}{@ms@/4}}=@fs@\ \mathrm{Hz},\quad{}"
         r"f_u=\frac{1}{2\pi}\sqrt{\frac{@Kt@+@Kw@}{@mu@}}=@fu@\ \mathrm{Hz}",
         Kr=fm["ride_rate_N_per_m"], ms=p["ms"], fs=fm["frequency_sprung_target_Hz"], Kt=p["Kt"],
         Kw=fm["wheel_rate_N_per_m"], mu=p["mu"], fu=fm["frequency_unsprung_target_Hz"])
    r.eq(r"\mathrm{unsprung\ ratio}=\frac{m_u}{M_s/4+m_u}\cdot100",
         r"\mathrm{unsprung\ ratio}=\frac{@mu@}{@ms@/4+@mu@}\cdot100=@ratio@\%",
         mu=p["mu"], ms=p["ms"], ratio=fm["unsprung_mass_ratio_target_percent"])

    r.heading("8. 固定 Roll，反算 Heave")
    heave = s["heave"]
    if not p["use_tender"]:
        r.text("**Tender 已關閉（use_tender = False）。** 跳過 Heave 反算與 Tender 可行性計算，直接使用原 Heave 主簧剛性。")
        r.eq(r"K_{h,\mathrm{active}}=K_{\mathrm{main}}",
             r"K_{h,\mathrm{active}}=K_{\mathrm{main}}=@K@\ \mathrm{N/m}", K=tire["Ks_pitch_N_per_m"])
    else:
        target = heave["target_natural_frequency_Hz"]
        required_ride = (2 * math.pi * target)**2 * p["ms"] / 4
        r.eq(r"f_{\mathrm{target}}=\frac{f_{u,0}}{N}",
             r"f_{\mathrm{target}}=\frac{@fu@}{@N@}=@f@\ \mathrm{Hz}",
             fu=heave["current_unsprung_frequency_Hz"], N=p["N"], f=target)
        r.eq(r"K_{r,\mathrm{target}}=(2\pi f_{\mathrm{target}})^2\frac{M_s}{4}",
             r"K_{r,\mathrm{target}}=(2\pi\cdot@f@)^2\frac{@ms@}{4}=@Kr@\ \mathrm{N/m}",
             f=target, ms=p["ms"], Kr=required_ride)
        r.eq(r"K_{h,\mathrm{target}}=\frac{4K_{r,\mathrm{target}}K_t}{(K_t-K_{r,\mathrm{target}})MR^2}-K_{s,\mathrm{roll}}")
        if heave["can_reach_target"]:
            r.eq(r"K_{h,\mathrm{target}}",
                 r"K_{h,\mathrm{target}}=\frac{4\cdot@Kr@\cdot@Kt@}{(@Kt@-@Kr@)\cdot@mr@^2}-@roll@=@Kh@\ \mathrm{N/m}",
                 Kr=required_ride, Kt=p["Kt"], mr=p["MR"], roll=tire["Ks_roll_N_per_m"],
                 Kh=heave["Ks_required_target_frequency_N_per_m"])
            r.eq(r"\lambda_h=\frac{K_{h,\mathrm{target}}}{K_{\mathrm{main}}},\quad\Delta K_h=K_{\mathrm{main}}-K_{h,\mathrm{target}}",
                 r"\lambda_h=\frac{@new@}{@old@}=@ratio@,\quad\Delta K_h=@old@-@new@=@delta@\ \mathrm{N/m}",
                 new=heave["Ks_required_target_frequency_N_per_m"], old=tire["Ks_pitch_N_per_m"],
                 ratio=heave["Ks_scale_target_frequency"], delta=heave["heave_stiffness_reduction_N_per_m"])
            r.eq(r"\mathrm{reduction}=(1-\lambda_h)100",
                 r"\mathrm{reduction}=(1-@ratio@)\cdot100=@pct@\%", ratio=heave["Ks_scale_target_frequency"],
                 pct=heave["heave_stiffness_reduction_percent"])
            r.text("以新 Heave 和固定 Roll 代回第 7 節的同一公式，回算頻率如下。")
            r.table(["調整後簧上頻率 Hz", "調整後簧下頻率 Hz"],
                    [(heave["adjusted_sprung_frequency_Hz"], heave["adjusted_unsprung_frequency_Hz"])])
        else:
            r.text("**無可行正 Heave 解：**{reason}", reason=r.translate(heave["reason"]))

    r.heading("9. 主 Heave 與 Tender 串聯")
    tender = s["tender"]
    if p["use_tender"]:
        r.eq(r"K_{\mathrm{series}}=\frac{K_{\mathrm{main}}K_{\mathrm{tender}}}{K_{\mathrm{main}}+K_{\mathrm{tender}}},\quad{}"
             r"K_{\mathrm{tender}}=\frac{K_{\mathrm{series,target}}K_{\mathrm{main}}}{K_{\mathrm{main}}-K_{\mathrm{series,target}}}")
    if not p["use_tender"]:
        r.text("Tender 已關閉，略過串聯彈簧設計；Heave 與 Heave & Roll 組合均直接使用原主簧剛性。")
    elif tender is None:
        r.text("**Tender 無可行解。** 前序 Heave 目標不可行，或目標未低於主簧剛性。依賴 Tender 的數值不填入 0。")
    else:
        r.eq(r"K_{\mathrm{tender}}",
             r"K_{\mathrm{tender}}=\frac{@target@\cdot@main@}{@main@-@target@}=@tender@\ \mathrm{N/m}",
             target=tender["K_series_target_N_per_m"], main=tender["K_heave_main_N_per_m"],
             tender=tender["K_tender_required_N_per_m"])
        r.eq(r"\rho_t=\frac{K_{\mathrm{tender}}}{K_{\mathrm{main}}}",
             r"\rho_t=\frac{@tender@}{@main@}=@ratio@,\quad K_{\mathrm{series}}=@series@\ \mathrm{N/m}",
             tender=tender["K_tender_required_N_per_m"], main=tender["K_heave_main_N_per_m"],
             ratio=tender["tender_to_heave_stiffness_ratio"], series=tender["K_heave_with_tender_N_per_m"])
        r.text("串聯剛性僅適用於 Tender 未併圈階段。")

    r.heading("9.3 前 Anti-dive 與 9.4 加速／煞車 Anti 設定")
    r.text("前後軸分別使用軸端垂向懸吊剛性 Kz 與車體等效剛性 Kc，單位均為 N/m。"
           "Kc 為可獨立修改的固定輸入；初始值由改版前主 Heave 72829.63107381333 N/m、MR = 1 的 10 倍假設估算，非量測值。"
           "目前前後使用相同 Heave 彈簧；Roll 的 kf／kr 不套用於此處。")
    r.eq(r"K_{z,i}=K_{h,i}MR^2,\quad K_{\mathrm{eq},i}=(1-a_i)^2K_{z,i}+a_i^2K_{c,i}")
    r.eq(r"\frac{dK_{\mathrm{eq},i}}{da_i}=-2(1-a_i)K_{z,i}+2a_iK_{c,i}=0,\quad{}"
         r"a_i=\frac{K_{z,i}}{K_{z,i}+K_{c,i}},\quad \alpha_i=1-a_i")
    r.heading("純 Heave", 3)
    values = s["anti"]["heave_only"]
    spring = s["tire"]["Ks_pitch_N_per_m"]
    for axle, axle_label in (("front", "前軸剛性基準（前 Anti-dive）"),
                             ("rear", "後軸剛性基準（後 Anti-squat 來源）")):
        x = values[axle]
        r.heading(axle_label, 4)
        r.eq(r"K_{z,i}=K_{h,i}MR^2,\quad K_{c,i}=\text{固定輸入}",
             r"K_{z,i}=@spring@\cdot@mr@^2=@kz@\ \mathrm{N/m},\quad K_{c,i}=@kc@\ \mathrm{N/m}",
             spring=spring, mr=p["MR"], kz=x["suspension_stiffness_N_per_m"], kc=x["chassis_stiffness_N_per_m"])
        r.eq(r"a_i=\frac{K_{z,i}}{K_{z,i}+K_{c,i}},\quad \alpha_i=1-a_i",
             r"a_i=\frac{@kz@}{@kz@+@kc@}=@a@=@percent@\%,\quad \alpha_i=1-@a@=@alpha@",
             kz=x["suspension_stiffness_N_per_m"], kc=x["chassis_stiffness_N_per_m"],
             a=x["anti_ratio"], percent=x["anti_percent"], alpha=x["suspension_fraction"])
        r.eq(r"K_{\mathrm{eq},i,\min}=\frac{K_{z,i}K_{c,i}}{K_{z,i}+K_{c,i}}",
             r"K_{\mathrm{eq},i,\min}=\frac{@kz@\cdot@kc@}{@kz@+@kc@}=@eq@\ \mathrm{N/m}",
             kz=x["suspension_stiffness_N_per_m"], kc=x["chassis_stiffness_N_per_m"],
             eq=x["equivalent_stiffness_N_per_m"])
    r.heading("前 Anti-dive、後 Anti-squat 與前後 Anti-lift", 3)
    r.eq(r"\mathrm{AntiDive}_f=a_f",
         r"\mathrm{AntiDive}_f=@a@=@percent@\%",
         a=values["front_anti_dive_ratio"], percent=values["front_anti_dive_percent"])
    r.eq(r"\mathrm{AntiSquat}_r=a_r\frac{a_{\mathrm{acc}}}{a_x}",
         r"\mathrm{AntiSquat}_r=@raw@\frac{@acc@}{@ax@}=@ratio@=@percent@\%",
         raw=values["rear"]["anti_ratio"], acc=p["a_acc"], ax=p["ax"],
         ratio=values["rear_anti_squat_ratio"], percent=values["rear_anti_squat_percent"])
    r.eq(r"\mathrm{AntiLift}_r=\mathrm{AntiDive}_f,\quad \mathrm{AntiLift}_f=\mathrm{AntiSquat}_r",
         r"\mathrm{AntiLift}_r=@rear@=@rear_percent@\%,\quad{}"
         r"\mathrm{AntiLift}_f=@front@=@front_percent@\%",
         rear=values["rear_anti_lift_ratio"], rear_percent=values["rear_anti_lift_percent"],
         front=values["front_anti_lift_ratio"], front_percent=values["front_anti_lift_percent"])
    r.table(["設定項目", "比例", "百分比", "來源"], (
        ("前 Anti-dive", values["front_anti_dive_ratio"], values["front_anti_dive_percent"], "前軸剛性基準"),
        ("後 Anti-lift", values["rear_anti_lift_ratio"], values["rear_anti_lift_percent"], "等於前 Anti-dive"),
        ("後 Anti-squat", values["rear_anti_squat_ratio"], values["rear_anti_squat_percent"], "後軸剛性基準 × a_acc / ax"),
        ("前 Anti-lift", values["front_anti_lift_ratio"], values["front_anti_lift_percent"], "等於後 Anti-squat"),
        ("前 Anti", values["front_anti_ratio"], values["front_anti_percent"], "取前 Anti-dive 與前 Anti-lift 的較大值"),
        ("後 Anti", values["rear_anti_ratio"], values["rear_anti_percent"], "取後 Anti-squat 與後 Anti-lift 的較大值"),
    ))
    r.text("Anti 使用純 Heave 主簧。後 Anti-squat 由後軸剛性基準乘以 a_acc／ax 得出。"
           "程式參數 a_acc 對應加速目標，與 ax 均以 g 輸入。"
           "此為兩路剛性類比及指定比例設定；幾何硬點與實際煞車力路徑不在此求解。")
    r.text("加速工況將前 Anti-lift 設為後 Anti-squat。以 Dynamics 的全車力公式套用相同係數時，"
           "前後驅動力各占 50% 會得到相同大小的前後 Anti 力矩貢獻。")

    r.heading("10. 前 Roll Center 與 11. 後 Roll Center")
    rc = s["front_rc"]
    r.eq(r"r=\frac{h_{\mathrm{RC},f}}{h}=\frac{1}{1+c},\quad h_{\mathrm{RC},f}=rh",
         r"h_{\mathrm{RC},f}=\frac{@h@}{1+@c@}=@rc@\ \mathrm{m}",
         h=p["h_cog"], c=p["rc_chassis_stiffness_ratio"], rc=rc["rc_normalized_optimal_height_m"])
    r.eq(r"h_{\mathrm{RC},r}=h_{\mathrm{RC},f}\frac{w_f}{w_r}\frac{t_r}{t_f}\frac{k_f}{k_r}",
         r"h_{\mathrm{RC},r}=@front@\frac{@wf@}{@wr@}\frac{@tr@}{@tf@}\frac{@kf@}{@kr@}=@rear@\ \mathrm{m}",
         front=rc["rc_normalized_optimal_height_m"], wf=p["wf"], wr=p["wr"], tr=p["tr"], tf=p["tf"],
         kf=p["kf"], kr=p["kr"], rear=s["rear_rc_height_m"])

    r.heading("11.1 FVSA 與 Camber gain")
    r.text("保留指定的公尺數值公式。tan 的引數使用公尺數值約定，不能將 d 改成毫米後直接代入；"
           "deg/mm 是單位比例換算，最大 Camber 變化採指定的線性外推。")
    for axle, track in (("前軸", p["tf"]), ("後軸", p["tr"])):
        fv = s["fvsa"][axle]
        r.heading(axle, 3)
        r.eq(r"\theta=\arctan\left(\frac{2d}{t}\right)",
             r"\theta=\arctan\left(\frac{2\cdot@d@}{@t@}\right)=@rad@\ \mathrm{rad}=@deg@^\circ",
             d=p["sus_travel"], t=track, rad=fv["max_roll_angle_rad"], deg=fv["max_roll_angle_deg"])
        r.eq(r"L_{\mathrm{FVSA}}=\frac{1}{\tan(\theta/(2d))}",
             r"L_{\mathrm{FVSA}}=\frac{1}{\tan(@theta@/(2\cdot@d@))}=@L@\ \mathrm{m}",
             theta=fv["max_roll_angle_rad"], d=p["sus_travel"], L=fv["fvsa_length_m"])
        r.eq(r"G_\gamma=\arctan\left(\frac{1}{L_{\mathrm{FVSA}}}\right)\frac{180}{\pi}",
             r"G_\gamma=\arctan\left(\frac{1}{@L@}\right)\frac{180}{\pi}=@G@\ \mathrm{deg/m}",
             L=fv["fvsa_length_m"], G=fv["camber_gain_deg_per_m"])
        r.eq(r"\Delta\gamma_{\mathrm{FVSA}}=G_\gamma d",
             r"\Delta\gamma_{\mathrm{FVSA}}=@G@\cdot@d@=@angle@^\circ,\quad G_\gamma=@mm@\ \mathrm{deg/mm}",
             G=fv["camber_gain_deg_per_m"], d=p["sus_travel"], angle=fv["max_camber_change_deg"],
             mm=fv["camber_gain_deg_per_mm"])

    r.heading("11.2 純 ay 的輪胎壓縮與額外 Roll")
    r.text("這是各軸獨立的兩輪模型，無 ax、無空力；各軸承載質量依前後重量比例分配。")
    for axle, fraction, track in (("前軸", p["wf"], p["tf"]), ("後軸", p["wr"], p["tr"])):
        t = s["lateral_tire_roll"][axle]
        r.heading(axle, 3)
        r.eq(r"m_i=Mw_i,\quad F_{y,i}=m_i a_{y,g}g",
             r"m_i=@M@\cdot@fraction@=@m@\ \mathrm{kg},\quad F_{y,i}=@m@\cdot@ay@\cdot@g@=@F@\ \mathrm{N}",
             M=M, fraction=fraction, m=t["axle_mass_kg"], ay=p["ay"], g=p["g"], F=t["lateral_force_N"])
        r.eq(r"T_i=\frac{F_{y,i}h}{t_i},\quad N_L=\frac{m_ig}{2}-T_i,\quad N_R=\frac{m_ig}{2}+T_i",
             r"T_i=\frac{@F@\cdot@h@}{@t@}=@T@\ \mathrm{N},\quad{}"
             r"N_L=\frac{@m@\cdot@g@}{2}-@T@=@NL@,\quad N_R=\frac{@m@\cdot@g@}{2}+@T@=@NR@\ \mathrm{N}",
             F=t["lateral_force_N"], h=p["h_cog"], t=track, T=t["lateral_load_transfer_N"],
             m=t["axle_mass_kg"], g=p["g"], NL=t["left_normal_load_N"], NR=t["right_normal_load_N"])
        r.eq(r"\delta_L=\frac{N_L}{K_t},\quad\delta_R=\frac{N_R}{K_t}",
             r"\delta_L=\frac{@L@}{@Kt@}=@dl@\ \mathrm{m},\quad\delta_R=\frac{@R@}{@Kt@}=@dr@\ \mathrm{m}",
             L=t["left_normal_load_N"], R=t["right_normal_load_N"], Kt=p["Kt"],
             dl=t["left_linear_compression_m"], dr=t["right_linear_compression_m"])
        r.eq(r"\phi_{\mathrm{tire}}=\frac{\delta_R-\delta_L}{t_i}",
             r"\phi_{\mathrm{tire}}=\frac{@dr@-(@dl@)}{@t@}=@rad@\ \mathrm{rad}=@deg@^\circ",
             dr=t["right_linear_compression_m"], dl=t["left_linear_compression_m"], t=track,
             rad=t["linear_tire_roll_angle_rad"], deg=t["linear_tire_roll_angle_deg"])
        r.text("**接地有效。**" if t["contact_valid"] else
               "**接地失效：存在負輪載。** 上述負壓縮及 Roll 為線性外推參考；有效接地 Roll 為 None，不代表輪胎可承受拉力。")
        r.table(["靜態單輪壓縮 m", "ay 引起左側增量 m", "ay 引起右側增量 m", "接地界限 g", "離地臨界"],
                [(t["static_compression_m"], t["left_compression_change_m"], t["right_compression_change_m"],
                  t["ay_contact_limit_g"], t["at_lift_boundary"])])

    r.heading("11.3 最小半徑轉角、方向查核與 Caster")
    caster = s["caster"]
    delta = math.radians(p["steering_angle_deg"])
    r.eq(r"R=\frac{L}{\tan\delta},\quad \delta_{\max}=\arctan\left(\frac{L}{R_{\min}}\right)",
         r"\delta_{\max}=\arctan\left(\frac{@L@}{@R@}\right)=@rad@\ \mathrm{rad}=@deg@^\circ",
         L=p["L"], R=p["min_turn_radius_m"], rad=delta, deg=p["steering_angle_deg"])
    r.text("單軌等效前輪角取已確認的正方向。方向查核以固定 Caster 比較正、負轉向角。整式的座標負號固定為 −1。")
    r.table(["方向驗證 Caster deg", "轉向角 deg", "原式 Camber 變化 deg"],
            [(item["caster_deg"], item["steering_angle_deg"], item["raw_camber_change_deg"])
             for item in s["steering_checks"]])
    front = s["fvsa"]["前軸"]
    tilt = s["lateral_tire_roll"]["前軸"]
    r.eq(r"\gamma_b=\phi_{\mathrm{roll}}+\phi_{\mathrm{tire}}-\Delta\gamma_{\mathrm{FVSA}}",
         r"\gamma_b=@roll@+@tire@-@fvsa@=@base@^\circ",
         roll=front["max_roll_angle_deg"], tire=tilt["linear_tire_roll_angle_deg"],
         fvsa=front["max_camber_change_deg"], base=caster["base_camber_deg"])
    r.eq(r"\Delta\gamma_{\mathrm{raw}}=\delta\sin C-(1-\cos\delta)\sin K,\quad{}"
         r"\Delta\gamma_{\mathrm{applied}}=-\Delta\gamma_{\mathrm{raw}}")
    r.eq(r"\sin C=\frac{\gamma_b+(1-\cos\delta)\sin K}{\delta}")
    if caster["solution_status"] == "solved":
        r.eq(r"C=\arcsin\left(\frac{\gamma_b+(1-\cos\delta)\sin K}{\delta}\right)",
             r"C=\arcsin\left(\frac{@base@+(1-\cos(@delta@))\sin(@kpi@)}{@delta@}\right)"
             r"=@rad@\ \mathrm{rad}=@deg@^\circ",
             base=math.radians(caster["base_camber_deg"]), delta=delta, kpi=math.radians(p["kpi_deg"]),
             rad=math.radians(caster["caster_deg"]), deg=caster["caster_deg"])
        r.eq(r"\gamma_{\mathrm{final}}=\gamma_b-\Delta\gamma_{\mathrm{raw}}",
             r"\gamma_{\mathrm{final}}=@base@-(@raw@)=@final@^\circ",
             base=caster["base_camber_deg"], raw=caster["raw_steering_camber_change_deg"], final=caster["final_camber_deg"])
        if not tilt["contact_valid"]:
            r.text("**Caster 算式有實數解，接地模型失效。** 本節 Camber 與 Caster 僅為線性外推參考。")
    else:
        r.text("**Caster 狀態：{status}。** {reason}",
               status=caster["solution_status"], reason=r.translate(caster["reason"]))



def _render_loads(r, s):
    p = s["parameters"]
    M = s["frequency_mass"]["m_total_vehicle_kg"]
    r.heading("12. 下壓力造成的 Tender 壓縮")
    compression, tender = s["compression"], s["tender"]
    r.eq(r"F_{\mathrm{applied}}=F_{\mathrm{down}}\eta_F,\quad F_{\mathrm{assembly}}=\frac{F_{\mathrm{applied}}}{2}")
    if not p["use_tender"]:
        r.text("Tender 已關閉，略過 Tender 串聯壓縮計算。")
    elif compression is None:
        r.text("**無可行 Tender，串聯壓縮不計算。**")
    else:
        force = compression["tender_bind_force_N"]
        main_mm = tender["K_heave_main_N_per_m"] / 1000
        tender_mm = tender["K_tender_required_N_per_m"] / 1000
        r.eq(r"F_{\mathrm{assembly}}",
             r"F_{\mathrm{assembly}}=\frac{@F@\cdot@ratio@}{2}=@force@\ \mathrm{N}",
             F=s["skidpad"]["skidpad_required_aero_downforce_N"], ratio=p["F_ref_ratio"], force=force)
        r.eq(r"d_{\mathrm{main}}=\frac{F_{\mathrm{assembly}}}{K_{\mathrm{main}}/1000},\quad{}"
             r"d_{\mathrm{tender}}=\frac{F_{\mathrm{assembly}}}{K_{\mathrm{tender}}/1000}",
             r"d_{\mathrm{main}}=\frac{@F@}{@km@}=@dm@\ \mathrm{mm},\quad{}"
             r"d_{\mathrm{tender}}=\frac{@F@}{@kt@}=@dt@\ \mathrm{mm}",
             F=force, km=main_mm, dm=compression["main_spring_compression_mm"],
             kt=tender_mm, dt=compression["tender_bind_spring_stroke_mm"])
        r.eq(r"d_{\mathrm{total}}=d_{\mathrm{main}}+d_{\mathrm{tender}}",
             r"d_{\mathrm{total}}=@dm@+@dt@=@total@\ \mathrm{mm}",
             dm=compression["main_spring_compression_mm"], dt=compression["tender_bind_spring_stroke_mm"],
             total=compression["tender_bind_total_stroke_mm"])
        r.text("前後各一組相同彈簧，Heave 等於同一總壓縮量；零點為原平衡位置，只算空力增量。"
               "沿用 Tender 設計，此下壓力為併圈切換點，不把它當成任意工況下都已併圈。")

    r.heading("13. 空力及 ax／ay 下的四輪受力")
    w, forces = s["wheel_loads"], s["tire_forces"]
    F = s["skidpad"]["skidpad_required_aero_downforce_N"] * p["F_ref_ratio"]
    k_front = s["damping"]["roll"]["front"]["angular_stiffness_Nm_per_rad"]
    k_rear = s["damping"]["roll"]["rear"]["angular_stiffness_Nm_per_rad"]
    r.eq(r"D=F_{\mathrm{down}}\eta_F,\quad T_x=\frac{Ma_{x,g}gh}{L}",
         r"D=@F@\cdot@ratio@=@D@\ \mathrm{N},\quad T_x=\frac{@M@\cdot@ax@\cdot@g@\cdot@h@}{@L@}=@T@\ \mathrm{N}",
         F=s["skidpad"]["skidpad_required_aero_downforce_N"], ratio=p["F_ref_ratio"], D=F,
         M=M, ax=p["ax"], g=p["g"], h=p["h_cog"], L=p["L"], T=w["longitudinal_transfer_N"])
    r.eq(r"N_f=Mgw_f+D\eta_a-T_x,\quad N_r=Mgw_r+D(1-\eta_a)+T_x",
         r"N_f=@M@\cdot@g@\cdot@wf@+@D@\cdot@eta@-(@T@)=@front@\ \mathrm{N}",
         M=M, g=p["g"], wf=p["wf"], D=F, eta=p["wl_aero_front_ratio"],
         T=w["longitudinal_transfer_N"], front=w["front_axle_load_N"])
    r.eq(r"N_r=Mgw_r+D(1-\eta_a)+T_x",
         r"N_r=@M@\cdot@g@\cdot@wr@+@D@(1-@eta@)+(@T@)=@rear@\ \mathrm{N}",
         M=M, g=p["g"], wr=p["wr"], D=F, eta=p["wl_aero_front_ratio"],
         T=w["longitudinal_transfer_N"], rear=w["rear_axle_load_N"])
    r.eq(r"K_{\phi f}=K_{s,\mathrm{roll}}(MRt_f)^2,\quad{}"
         r"K_{\phi r}=K_{s,\mathrm{roll}}\frac{k_r}{k_f}(MRt_r)^2")
    r.eq(r"\beta_f=\frac{K_{\phi f}}{K_{\phi f}+K_{\phi r}}",
         r"\beta_f=\frac{@f@}{@f@+@b@}=@beta@", f=k_front, b=k_rear, beta=w["front_roll_fraction"])
    r.eq(r"T_f=\frac{\beta_f Ma_{y,g}gh}{t_f},\quad T_r=\frac{(1-\beta_f)Ma_{y,g}gh}{t_r}",
         r"T_f=\frac{@beta@\cdot@M@\cdot@ay@\cdot@g@\cdot@h@}{@tf@}=@Tf@,\quad{}"
         r"T_r=\frac{(1-@beta@)\cdot@M@\cdot@ay@\cdot@g@\cdot@h@}{@tr@}=@Tr@\ \mathrm{N}",
         beta=w["front_roll_fraction"], M=M, ay=p["ay"], g=p["g"], h=p["h_cog"],
         tf=p["tf"], tr=p["tr"], Tf=w["front_lateral_transfer_N"], Tr=w["rear_lateral_transfer_N"])
    r.eq(r"N_{FL}=\frac{N_f}{2}-T_f,\quad N_{FR}=\frac{N_f}{2}+T_f,\quad{}"
         r"N_{RL}=\frac{N_r}{2}-T_r,\quad N_{RR}=\frac{N_r}{2}+T_r")
    for wheel, axle, transfer, sign in (
        ("FL", "front_axle_load_N", "front_lateral_transfer_N", -1),
        ("FR", "front_axle_load_N", "front_lateral_transfer_N", 1),
        ("RL", "rear_axle_load_N", "rear_lateral_transfer_N", -1),
        ("RR", "rear_axle_load_N", "rear_lateral_transfer_N", 1),
    ):
        r.eq(r"N_{" + wheel + r"}",
             r"N=\frac{@axle@}{2}+(@sign@)\cdot(@T@)=@N@\ \mathrm{N}",
             axle=w[axle], sign=sign, T=w[transfer], N=w["wheel_loads_N"][wheel])
    r.eq(r"F_{x,\mathrm{total}}=Ma_{x,g}g,\quad F_{y,\mathrm{total}}=Ma_{y,g}g",
         r"F_{x,\mathrm{total}}=@M@\cdot@ax@\cdot@g@=@Fx@,\quad{}"
         r"F_{y,\mathrm{total}}=@M@\cdot@ay@\cdot@g@=@Fy@\ \mathrm{N}",
         M=M, ax=p["ax"], ay=p["ay"], g=p["g"], Fx=forces["total_Fx_N"], Fy=forces["total_Fy_N"])
    r.eq(r"N_i^+=\max(0,N_i),\quad q_i=\frac{N_i^+}{\sum_jN_j^+},\quad{}"
         r"F_{x,i}=q_iF_{x,\mathrm{total}},\quad F_{y,i}=q_iF_{y,\mathrm{total}}")
    if forces["reference_only"]:
        r.text("**接地失效，以下三向需求力為參考。** 原始負輪載保留；截零後的總正向力與原始垂向力平衡不同。")
    r.table(["輪位", "原始 Fz N", "分配後 Fx N", "分配後 Fy N", "截零 Fz N", "合力 N", "載重占比"],
            [(wheel, data["raw_Fz_N"], data["Fx_N"], data["Fy_N"], data["Fz_N"],
              data["force_magnitude_N"], data["load_fraction"]) for wheel, data in forces["wheel_forces"].items()])
    for wheel, data in forces["wheel_forces"].items():
        r.eq(r"F_{" + wheel + r"}=\sqrt{F_x^2+F_y^2+F_z^2}",
             r"F=\sqrt{(@x@)^2+(@y@)^2+(@z@)^2}=@F@\ \mathrm{N}",
             x=data["Fx_N"], y=data["Fy_N"], z=data["Fz_N"], F=data["force_magnitude_N"])
    r.text("最大參考合力輪位：**{wheel}**。" if forces["reference_only"] else "最大合力輪位：**{wheel}**。",
           wheel=forces["most_loaded_wheel"])

    r.heading("14. 無空力加速與極速齒比")
    gear = s["gear"]
    r.text("工況為 ax = a_acc、ay = 0、下壓力 = 0；前後軸按輪載分配需求力，每軸兩輪、每輪一顆馬達。")
    r.eq(r"T_x=\frac{Ma_{\mathrm{acc}}gh}{L},\quad N_f=Mgw_f-T_x,\quad N_r=Mgw_r+T_x",
         r"T_x=\frac{@M@\cdot@acc@\cdot@g@\cdot@h@}{@L@}=@T@,\quad{}"
         r"N_f=@M@\cdot@g@\cdot@wf@-@T@=@Nf@,\quad N_r=@M@\cdot@g@\cdot@wr@+@T@=@Nr@\ \mathrm{N}",
         M=M, acc=p["a_acc"], g=p["g"], h=p["h_cog"], L=p["L"], T=gear["longitudinal_transfer_N"],
         wf=p["wf"], wr=p["wr"], Nf=gear["front_axle_load_N"], Nr=gear["rear_axle_load_N"])
    r.eq(r"F_{x,f}=Ma_{\mathrm{acc}}g\frac{N_f}{Mg},\quad F_{x,r}=Ma_{\mathrm{acc}}g\frac{N_r}{Mg}",
         r"F_{x,f}=@acc@\cdot@Nf@=@Ff@,\quad F_{x,r}=@acc@\cdot@Nr@=@Fr@\ \mathrm{N}",
         acc=p["a_acc"], Nf=gear["front_axle_load_N"], Nr=gear["rear_axle_load_N"],
         Ff=gear["front_axle_Fx_N"], Fr=gear["rear_axle_Fx_N"])
    r.eq(r"T_w=\frac{\max(F_{x,f},F_{x,r})}{2}R_t,\quad i_{\mathrm{acc}}=\frac{T_w}{T_{\mathrm{motor}}}",
         r"T_w=\frac{\max(@Ff@,@Fr@)}{2}\cdot@R@=@T@\ \mathrm{Nm},\quad{}"
         r"i_{\mathrm{acc}}=\frac{@T@}{@motor@}=@i@",
         Ff=gear["front_axle_Fx_N"], Fr=gear["rear_axle_Fx_N"], R=p["R_tire"],
         T=gear["wheel_torque_required_Nm"], motor=p["drive_motor_torque_Nm"], i=gear["gear_ratio_accel"])
    r.eq(r"n_w=\frac{v_{\mathrm{km/h}}/3.6}{2\pi R_t}60,\quad i_{\mathrm{speed}}=\frac{n_{\mathrm{motor}}}{n_w}",
         r"n_w=\frac{@v@/3.6}{2\pi\cdot@R@}60=@rpm@\ \mathrm{rpm},\quad{}"
         r"i_{\mathrm{speed}}=\frac{@motor@}{@rpm@}=@i@",
         v=p["drive_target_speed_kmh"], R=p["R_tire"], rpm=gear["target_wheel_rpm"],
         motor=p["drive_motor_rpm"], i=gear["gear_ratio_top_speed"])
    r.eq(r"i_{\mathrm{avg}}=\frac{i_{\mathrm{acc}}+i_{\mathrm{speed}}}{2}",
         r"i_{\mathrm{avg}}=\frac{@a@+@b@}{2}=@i@", a=gear["gear_ratio_accel"],
         b=gear["gear_ratio_top_speed"], i=gear["gear_ratio_avg"])

    r.heading("15. 無空力煞車力、前後比與回歸")
    brake = s["brake"]
    r.text("z 是正的煞車減速度 g 倍數，車身 ax = −z。指定需求與輪胎摩擦可達性分開列出。")
    r.eq(r"T_b=\frac{Mgzh}{L},\quad N_f=Mgw_f+T_b,\quad N_r=Mgw_r-T_b,\quad B_f=zN_f,\quad B_r=zN_r")
    for label, data in (("指定工況", brake["requested_point"]), ("可達設計上限", brake["limit_point"])):
        r.heading(label, 3)
        z = data["deceleration_g"]
        r.eq(r"T_b=\frac{Mgzh}{L}",
             r"T_b=\frac{@M@\cdot@g@\cdot@z@\cdot@h@}{@L@}=@T@\ \mathrm{N}",
             M=M, g=p["g"], z=z, h=p["h_cog"], L=p["L"], T=data["longitudinal_transfer_N"])
        r.eq(r"N_f=Mgw_f+T_b,\quad N_r=Mgw_r-T_b",
             r"N_f=@M@\cdot@g@\cdot@wf@+@T@=@Nf@,\quad N_r=@M@\cdot@g@\cdot@wr@-@T@=@Nr@\ \mathrm{N}",
             M=M, g=p["g"], wf=p["wf"], wr=p["wr"], T=data["longitudinal_transfer_N"],
             Nf=data["front_axle_load_N"], Nr=data["rear_axle_load_N"])
        r.eq(r"B_f=zN_f,\quad B_r=zN_r",
             r"B_f=@z@\cdot@Nf@=@Bf@,\quad B_r=@z@\cdot@Nr@=@Br@\ \mathrm{N}",
             z=z, Nf=data["front_axle_load_N"], Nr=data["rear_axle_load_N"],
             Bf=data["front_brake_force_N"], Br=data["rear_brake_force_N"])
        r.eq(r"\beta_f=\frac{N_f}{Mg},\quad\beta_r=\frac{N_r}{Mg}",
             r"\beta_f=\frac{@Nf@}{@M@\cdot@g@}=@bf@,\quad\beta_r=\frac{@Nr@}{@M@\cdot@g@}=@br@",
             Nf=data["front_axle_load_N"], Nr=data["rear_axle_load_N"], M=M, g=p["g"],
             bf=data["front_ratio"], br=data["rear_ratio"])
    r.eq(r"z_{\mathrm{lift}}=\frac{l_f}{h},\quad z_{\mathrm{physical}}=\min(\mu_x,z_{\mathrm{lift}}),\quad{}"
         r"z_{\mathrm{design}}=\min(z_{\mathrm{requested}},z_{\mathrm{physical}})",
         r"z_{\mathrm{lift}}=@lift@,\quad z_{\mathrm{physical}}=\min(@mu@,@lift@)=@physical@,\quad{}"
         r"z_{\mathrm{design}}=\min(@req@,@physical@)=@design@",
         lift=brake["rear_lift_limit_g"], mu=p["mu_w"], physical=brake["physical_deceleration_limit_g"],
         req=p["brake_ax"], design=brake["brake_design_deceleration_g"])
    r.text("指定減速度可達：**{result}**。", result=r.cell(brake["target_achievable"]))
    r.heading("十點通過原點的最小平方擬合", 3)
    r.table(["減速度 g", "前煞車力 N", "後煞車力 N", "前比", "後比"],
            [(x["deceleration_g"], x["front_brake_force_N"], x["rear_brake_force_N"], x["front_ratio"], x["rear_ratio"])
             for x in brake["samples"]])
    numerator = sum(x["front_brake_force_N"] * x["rear_brake_force_N"] for x in brake["samples"])
    denominator = sum(x["front_brake_force_N"]**2 for x in brake["samples"])
    r.eq(r"k=\frac{\sum B_fB_r}{\sum B_f^2},\quad\beta_{f,\mathrm{fit}}=\frac{1}{1+k},\quad\beta_{r,\mathrm{fit}}=1-\beta_{f,\mathrm{fit}}",
         r"k=\frac{@num@}{@den@}=@k@,\quad\beta_{f,\mathrm{fit}}=\frac{1}{1+@k@}=@f@,\quad\beta_{r,\mathrm{fit}}=1-@f@=@b@",
         num=numerator, den=denominator, k=brake["brake_ideal_fit_rear_over_front"],
         f=brake["brake_ideal_front_ratio"], b=brake["brake_ideal_rear_ratio"])

    r.heading("16. 煞車機構整體等效機械利益")
    ma = s["brake_mechanical_advantage"]
    r.eq(r"MA=\frac{B_f+B_r}{F_{\mathrm{foot}}}",
         r"MA=\frac{@f@+@b@}{@foot@}=\frac{@total@}{@foot@}=@ma@",
         f=brake["requested_point"]["front_brake_force_N"], b=brake["requested_point"]["rear_brake_force_N"],
         foot=ma["brake_driver_force_N"], total=ma["brake_total_required_force_N"], ma=ma["brake_mechanical_advantage"])
    r.text("此倍率是腳力至四輪接地總煞車力的整體等效值；硬體槓桿、液壓與制動半徑仍需另行分配。")


def _render_modes(r, s):
    p = s["parameters"]
    d = s["damping"]
    r.heading("17. Roll、Heave + Tender 與純 Heave 的前後臨界阻尼" if p["use_tender"]
              else "17. Roll 與純 Heave 的前後臨界阻尼")
    r.text("每軸各一支 Roll 和 Heave 阻尼器；彈簧與阻尼器共用 MR。此節採固定輪端的單自由度參考。")
    r.eq(r"c_{\mathrm{crit}}=2\sqrt{km},\quad \zeta=\frac{c}{c_{\mathrm{crit}}},\quad c=\zeta c_{\mathrm{crit}}",
         r"\zeta_{\mathrm{target}}=@zeta@", zeta=p["zeta"])
    r.eq(r"K_\phi=K_{\phi f}+K_{\phi r},\quad C_{\phi,\mathrm{crit}}=2\sqrt{K_\phi I_{xx,s}}",
         r"K_\phi=@f@+@b@=@K@\ \mathrm{Nm/rad},\quad C_{\phi,\mathrm{crit}}=2\sqrt{@K@\cdot@I@}=@C@\ \mathrm{Nm\,s/rad}",
         f=d["roll"]["front"]["angular_stiffness_Nm_per_rad"], b=d["roll"]["rear"]["angular_stiffness_Nm_per_rad"],
         K=d["roll_total_stiffness_Nm_per_rad"], I=p["sprung_roll_inertia_kg_m2"],
         C=d["roll_total_critical_damping_Nms_per_rad"])
    r.text("Ixx 為手動指定的簧上 CG 慣量；修改車體質量分布時需同步更新此輸入，質量改動不會自動推估新的慣量。")
    for axle, label, track in (("front", "前軸", p["tf"]), ("rear", "後軸", p["tr"])):
        x = d["roll"][axle]
        r.heading(r.translate(label) + " Roll", 3)
        r.eq(r"K_{\phi i}=K_{s,i}(MRt_i)^2",
             r"K_{\phi i}=@Ks@(@mr@\cdot@t@)^2=@K@\ \mathrm{Nm/rad}",
             Ks=x["spring_stiffness_N_per_m"], mr=p["MR"], t=track, K=x["angular_stiffness_Nm_per_rad"])
        r.eq(r"C_{\phi i}=C_{\phi,\mathrm{crit}}\frac{K_{\phi i}}{K_\phi},\quad{}"
             r"c_{\mathrm{damper},i}=\frac{C_{\phi i}}{(MRt_i)^2}",
             r"C_{\phi i}=@C@\frac{@Ki@}{@K@}=@Ci@,\quad{}"
             r"c_{\mathrm{damper},i}=\frac{@Ci@}{(@mr@\cdot@t@)^2}=@c@\ \mathrm{N\,s/m}",
             C=d["roll_total_critical_damping_Nms_per_rad"], Ki=x["angular_stiffness_Nm_per_rad"],
             K=d["roll_total_stiffness_Nm_per_rad"], Ci=x["angular_damping_Nms_per_rad"],
             mr=p["MR"], t=track, c=x["damper_critical_damping_Ns_per_m"])
    for mode, label in (("heave_with_tender", "Heave + Tender"), ("pure_heave", "純 Heave")):
        if mode == "heave_with_tender" and not p["use_tender"]:
            continue
        r.heading(label, 3)
        if d[mode] is None:
            r.text("Tender 無可行解，此組阻尼不計算。")
            continue
        for axle, axle_label, fraction in (("front", "前軸", p["wf"]), ("rear", "後軸", p["wr"])):
            x = d[mode][axle]
            r.text(axle_label)
            r.eq(r"m_i=M_sw_i,\quad K_{z,i}=K_{s,i}MR^2",
                 r"m_i=@ms@\cdot@fraction@=@m@\ \mathrm{kg},\quad K_{z,i}=@Ks@\cdot@mr@^2=@Kz@\ \mathrm{N/m}",
                 ms=p["ms"], fraction=fraction, m=x["sprung_mass_kg"], Ks=x["spring_stiffness_N_per_m"],
                 mr=p["MR"], Kz=x["body_stiffness_N_per_m"])
            r.eq(r"c_{z,i}=2\sqrt{K_{z,i}m_i},\quad c_{d,i}=\frac{c_{z,i}}{MR^2}",
                 r"c_{z,i}=2\sqrt{@K@\cdot@m@}=@cz@,\quad c_{d,i}=\frac{@cz@}{@mr@^2}=@cd@\ \mathrm{N\,s/m}",
                 K=x["body_stiffness_N_per_m"], m=x["sprung_mass_kg"],
                 cz=x["body_critical_damping_Ns_per_m"], mr=p["MR"], cd=x["damper_critical_damping_Ns_per_m"])

    r.heading("Dynamics 匯出阻尼與車架傳力", 3)
    r.text("純 Heave 通道使用兩輪位移總和，剛性與阻尼係數各除以 4。Roll 使用阻尼器端係數，四輪使用相同的胎剛性與單輪簧下質量。")
    coefficients = damping_coefficients(s)
    for end, axle, label in (("f", "front", "前軸"), ("r", "rear", "後軸")):
        r.text(label)
        r.eq(r"c_{\mathrm{heave,JSON}}=\frac{\zeta c_{\mathrm{heave,crit}}}{4},\quad{}"
             r"c_{\mathrm{roll,JSON}}=\zeta c_{\mathrm{roll,crit}}",
             r"c_{\mathrm{heave,JSON}}=\frac{@z@\cdot @h@}{4}=@hc@\ \mathrm{N\,s/m},\quad{}"
             r"c_{\mathrm{roll,JSON}}=@z@\cdot @r@=@rc@\ \mathrm{N\,s/m}",
             z=p["zeta"], h=d["pure_heave"][axle]["damper_critical_damping_Ns_per_m"],
             r=d["roll"][axle]["damper_critical_damping_Ns_per_m"],
             hc=coefficients[f"heave_{end}_c"], rc=coefficients[f"roll_{end}_c"])
    r.eq(r"c_{\mathrm{tire}}=2\zeta\sqrt{K_t m_u}",
         r"c_{\mathrm{tire}}=2\cdot @z@\sqrt{@Kt@\cdot @mu@}=@c@\ \mathrm{N\,s/m}",
         z=p["zeta"], Kt=p["Kt"], mu=p["mu"], c=coefficients["tire_c"])
    frame = frame_parameters(s)
    r.eq(r"m_{\mathrm{frame}}=\frac{M_s}{4},\quad k_{\mathrm{frame}}=10K_{\mathrm{roll}}",
         r"m_{\mathrm{frame}}=\frac{@ms@}{4}=@m@\ \mathrm{kg},\quad{}"
         r"k_{\mathrm{frame}}=10\cdot @kr@=@k@\ \mathrm{N/m}",
         ms=p["ms"], m=frame["m_frame"], kr=s["selected_stiffness"]["roll"]["stiffness_N_per_m"],
         k=frame["k_frame"])
    r.text("車架傳力採選定的線性 Roll 剛性（N/m）。")

    r.heading("18. 四種指定 Ks：前後 Ks → Kw → Kr、自然頻率、臨界阻尼與目標阻尼")
    heave_symbol = r"K_{ht}" if p["use_tender"] else r"K_h"
    r.eq((r"K_s^{(1)}=\frac{K_{ht}+K_{\mathrm{roll}}}{2},\quad K_s^{(2)}=K_{ht},\quad{}"
          r"K_s^{(3)}=K_{\mathrm{roll}},\quad K_s^{(4)}=K_{\mathrm{heaveonly}}")
         .replace(r"K_{ht}", heave_symbol))
    r.text("Kht 為 Heave 與 Tender 的串聯值。" if p["use_tender"]
           else "Tender 已關閉，Kh 直接使用原 Heave 主簧剛性；Heave & Roll 採 (Kh + Kroll)/2。")
    r.text("本節依指定除以 2，各 Ks 作單輪線性等效比較；第 7 節原 Frequency vs mass 的除以 4 模式仍另行保留。")
    r.eq(r"m_w=\frac{M_sw_i}{2},\quad m_{s,\mathrm{coord}}=\frac{m_w}{MR^2},\quad{}"
         r"K_w=K_sMR^2,\quad K_r=\frac{K_wK_t}{K_w+K_t}")
    r.eq(r"f_{Ks}=\frac{1}{2\pi}\sqrt{\frac{K_s}{m_{s,\mathrm{coord}}}},\quad{}"
         r"f_{Kw}=\frac{1}{2\pi}\sqrt{\frac{K_w}{m_w}},\quad f_{Kr}=\frac{1}{2\pi}\sqrt{\frac{K_r}{m_w}}")
    r.eq(r"c_{Ks}=2\sqrt{K_sm_{s,\mathrm{coord}}},\quad c_{Kw}=2\sqrt{K_wm_w},\quad c_{Kr}=2\sqrt{K_rm_w}")
    zeta = p["zeta"]
    r.eq(r"c_{\mathrm{target},j}=\zeta c_j,\quad j\in\{Ks,Kw,Kr\}",
         r"\zeta=@zeta@", zeta=zeta)
    heave_label = "Kht" if p["use_tender"] else "Kheave"
    cases = (("combined_average", f"({heave_label} + Kroll)/2"), ("heave_with_tender", heave_label),
             ("roll", "Kroll"), ("heave_only", "Kheaveonly"))
    summary = []
    for axle, label, fraction in (("front", "前軸", p["wf"]), ("rear", "後軸", p["wr"])):
        for mode, case_label in cases:
            x = s["rate_cases"][axle][mode]
            r.heading("{axle}：{case}", 3, axle=r.translate(label), case=case_label)
            if x is None:
                r.text("Tender 無可行解，這個 Ks 案例不計算。")
                continue
            ks, kw, kr = x["spring_rate_N_per_m"], x["wheel_rate_N_per_m"], x["ride_rate_N_per_m"]
            if mode == "combined_average":
                ht = p["active_heave_spring_N_per_m"]
                roll = s["damping"]["roll"][axle]["spring_stiffness_N_per_m"]
                r.eq(r"K_s=\frac{K_{ht}+K_{\mathrm{roll}}}{2}".replace(r"K_{ht}", heave_symbol),
                     r"K_s=\frac{@ht@+@roll@}{2}=@Ks@\ \mathrm{N/m}", ht=ht, roll=roll, Ks=ks)
            else:
                r.eq(r"K_s", r"K_s=@Ks@\ \mathrm{N/m}", Ks=ks)
            r.eq(r"m_w=\frac{M_sw_i}{2},\quad m_{s,\mathrm{coord}}=\frac{m_w}{MR^2}",
                 r"m_w=\frac{@ms@\cdot@fraction@}{2}=@m@,\quad{}"
                 r"m_{s,\mathrm{coord}}=\frac{@m@}{@mr@^2}=@mc@\ \mathrm{kg}",
                 ms=p["ms"], fraction=fraction, m=x["sprung_mass_per_wheel_kg"],
                 mr=p["MR"], mc=x["spring_coordinate_mass_kg"])
            r.eq(r"K_w=K_sMR^2,\quad K_r=\frac{K_wK_t}{K_w+K_t}",
                 r"K_w=@Ks@\cdot@mr@^2=@Kw@,\quad K_r=\frac{@Kw@\cdot@Kt@}{@Kw@+@Kt@}=@Kr@\ \mathrm{N/m}",
                 Ks=ks, mr=p["MR"], Kw=kw, Kt=p["Kt"], Kr=kr)
            for stage, stiffness, mass in (("Ks", ks, x["spring_coordinate_mass_kg"]),
                                            ("Kw", kw, x["sprung_mass_per_wheel_kg"]),
                                            ("Kr", kr, x["sprung_mass_per_wheel_kg"])):
                critical = x[f"critical_damping_{stage}_Ns_per_m"]
                r.eq(r"f_{" + stage + r"}=\frac{1}{2\pi}\sqrt{\frac{K}{m}},\quad c_{" + stage + r"}=2\sqrt{Km}",
                     r"f=\frac{1}{2\pi}\sqrt{\frac{@K@}{@m@}}=@f@\ \mathrm{Hz},\quad{}"
                     r"c=2\sqrt{@K@\cdot@m@}=@c@\ \mathrm{N\,s/m}",
                     K=stiffness, m=mass, f=x[f"frequency_{stage}_Hz"], c=critical)
                r.eq(rf"c_{{\mathrm{{target}},{stage}}}=\zeta c_{{{stage}}}"
                     rf"={_number(zeta)}\cdot {_number(critical)}={_number(zeta * critical)}\ \mathrm{{N\,s/m}}")
            critical_kr = x["critical_damping_Kr_Ns_per_m"]
            summary.append((label, case_label, ks, kw, kr, x["frequency_Kr_Hz"], critical_kr, zeta * critical_kr))
    r.table(["軸別", "案例", "Ks N/m", "Kw N/m", "Kr N/m", "fKr Hz",
             "Kr 臨界阻尼 N·s/m", "Kr 目標阻尼 N·s/m"], summary)
    r.text("fKs = fKw 是座標一致性的結果。Kr 的臨界與目標阻尼為 ride 等效單自由度參考，"
           "不直接代表實體阻尼器係數；Kroll 案例也不是以轉動慣量求得的整車 Roll 模態頻率。")

    r.heading("19. Roll 與 Pitch gradient")
    gr = s["gradients"]
    M = s["frequency_mass"]["m_total_vehicle_kg"]
    r.text("以整車慣性力及各固定切線剛性階段求準靜態小角度斜率，單位 deg/g；空力不增加慣性質量。")
    r.text("跨越 Tender 併圈點時改用相應階段，空力影響載重及所處階段。" if p["use_tender"]
           else "Tender 已關閉，Pitch gradient 直接使用原 Heave 主簧剛性。")
    r.eq(r"h_{\mathrm{RA}}=w_fh_{\mathrm{RC},f}+w_rh_{\mathrm{RC},r},\quad h_\phi=h-h_{\mathrm{RA}}",
         r"h_{\mathrm{RA}}=@wf@\cdot@front@+@wr@\cdot@rear@=@axis@\ \mathrm{m},\quad{}"
         r"h_\phi=@h@-@axis@=@arm@\ \mathrm{m}",
         wf=p["wf"], front=s["front_rc"]["rc_normalized_optimal_height_m"], wr=p["wr"], rear=s["rear_rc_height_m"],
         axis=gr["roll_axis_height_at_cg_m"], h=p["h_cog"], arm=gr["roll_moment_arm_m"])
    r.eq(r"K_{\phi s,i}=K_{s,i}\left(\frac{MRt_i}{2}\right)^2,\quad K_{\phi t,i}=\frac{K_tt_i^2}{2},\quad{}"
         r"K_{\phi r,i}=\frac{K_{\phi s,i}K_{\phi t,i}}{K_{\phi s,i}+K_{\phi t,i}}")
    for axle, track in (("front", p["tf"]), ("rear", p["tr"])):
        spring = s["damping"]["roll"][axle]["spring_stiffness_N_per_m"]
        suspension, tire, ride = calculate_roll_axle_stiffness(spring, p["MR"], track, p["Kt"])
        r.text("前軸" if axle == "front" else "後軸")
        r.eq(r"K_{\phi s,i},\quad K_{\phi t,i},\quad K_{\phi r,i}",
             r"K_{\phi s,i}=@Ks@\left(\frac{@mr@\cdot@t@}{2}\right)^2=@s@,\quad{}"
             r"K_{\phi t,i}=\frac{@Kt@\cdot@t@^2}{2}=@tire@,\quad{}"
             r"K_{\phi r,i}=\frac{@s@\cdot@tire@}{@s@+@tire@}=@ride@\ \mathrm{Nm/rad}",
             Ks=spring, mr=p["MR"], t=track, s=suspension, Kt=p["Kt"], tire=tire, ride=ride)
    r.eq(r"G_{\mathrm{roll}}=\frac{Mgh_\phi}{K_{\phi,\mathrm{total}}}\frac{180}{\pi}")
    for label, stiffness, gradient in (
        ("僅懸吊", gr["roll_suspension_stiffness_Nm_per_rad"], gr["roll_gradient_suspension_deg_per_g"]),
        ("含輪胎柔度", gr["roll_ride_stiffness_Nm_per_rad"], gr["roll_gradient_with_tires_deg_per_g"]),
    ):
        r.text(label)
        r.eq(r"G_{\mathrm{roll}}",
             r"G_{\mathrm{roll}}=\frac{@M@\cdot@g@\cdot@h@}{@K@}\frac{180}{\pi}=@G@\ \mathrm{deg/g}",
             M=M, g=p["g"], h=gr["roll_moment_arm_m"], K=stiffness, G=gradient)
    r.eq(r"T_{1g}=\frac{Mgh}{L},\quad{}"
         r"\theta_{1g}=\frac{T_{1g}}{L}\left(\frac{1}{K_{z,f}}+\frac{1}{K_{z,r}}\right)")
    r.eq(r"K_{\theta s}=\frac{L^2}{1/K_{z,f}+1/K_{z,r}}=\frac{K_hMR^2L^2}{2},\quad K_{\theta t}=K_tL^2")
    r.eq(r"G_{\mathrm{pitch},s}=\frac{Mgh}{K_{\theta s}}\frac{180}{\pi},\quad{}"
         r"G_{\mathrm{pitch},t}=\frac{Mgh}{K_{\theta t}}\frac{180}{\pi}")
    r.eq(r"G_{\mathrm{pitch,total}}=G_{s,f}+G_{s,r}+G_{\mathrm{pitch},t},\quad{}"
         r"G_{s,i}=\frac{Mgh}{L^2K_{z,i}}\frac{180}{\pi}")
    r.text("前後 Anti 修正僅用於純 Heave 主簧的煞車工況，使用設定後的前 Anti-dive 與後 Anti-lift；"
           "後 Anti-lift 等於前 Anti-dive。")
    for mode, label in (("heave_with_tender", "Heave + Tender"), ("heave_only", "純 Heave")):
        if mode == "heave_with_tender" and not p["use_tender"]:
            continue
        x = gr["pitch"][mode]
        r.heading("Pitch：{mode}", 3, mode=r.translate(label))
        if x is None:
            r.text("Tender 無可行解，此階段不計算。")
            continue
        spring = s["tire"]["Ks_pitch_N_per_m"] if mode == "heave_only" else s["tender"]["K_heave_with_tender_N_per_m"]
        tire_gradient = x["gradient_with_tires_deg_per_g"] - x["gradient_suspension_deg_per_g"]
        r.eq(r"K_{\theta s}=\frac{K_hMR^2L^2}{2},\quad K_{\theta t}=K_tL^2",
             r"K_{\theta s}=\frac{@Kh@\cdot@mr@^2\cdot@L@^2}{2}=@Ks@,\quad{}"
             r"K_{\theta t}=@Kt@\cdot@L@^2=@Kti@\ \mathrm{Nm/rad}",
             Kh=spring, mr=p["MR"], L=p["L"], Ks=x["pitch_suspension_stiffness_Nm_per_rad"],
             Kt=p["Kt"], Kti=x["pitch_tire_stiffness_Nm_per_rad"])
        r.eq(r"G_{\mathrm{pitch},s}",
             r"G_{\mathrm{pitch},s}=\frac{@M@\cdot@g@\cdot@h@}{@K@}\frac{180}{\pi}=@G@\ \mathrm{deg/g}",
             M=M, g=p["g"], h=p["h_cog"], K=x["pitch_suspension_stiffness_Nm_per_rad"],
             G=x["gradient_suspension_deg_per_g"])
        r.eq(r"G_{\mathrm{pitch},t}",
             r"G_{\mathrm{pitch},t}=\frac{@M@\cdot@g@\cdot@h@}{@K@}\frac{180}{\pi}=@G@\ \mathrm{deg/g}",
             M=M, g=p["g"], h=p["h_cog"], K=x["pitch_tire_stiffness_Nm_per_rad"], G=tire_gradient)
        r.eq(r"G_{\mathrm{pitch,total}}=G_{\mathrm{pitch},s}+G_{\mathrm{pitch},t}",
             r"G_{\mathrm{pitch,total}}=@s@+@t@=@total@\ \mathrm{deg/g}",
             s=x["gradient_suspension_deg_per_g"], t=tire_gradient, total=x["gradient_with_tires_deg_per_g"])
        if mode == "heave_only":
            r.eq(r"G_{\mathrm{pitch,anti}}=(1-\mathrm{AntiDive}_f)G_{s,f}+(1-\mathrm{AntiLift}_r)G_{s,r}+G_{\mathrm{pitch},t}",
                 r"G_{\mathrm{pitch,anti}}=(1-@af@)\cdot@sf@+(1-@ar@)\cdot@sr@+@t@=@anti@\ \mathrm{deg/g}",
                 af=x["front_anti_dive_ratio"], ar=x["rear_anti_lift_ratio"], t=tire_gradient,
                 sf=x["front_suspension_gradient_deg_per_g"], sr=x["rear_suspension_gradient_deg_per_g"],
                 anti=x["gradient_with_tires_and_anti_deg_per_g"])
    r.text("純 Heave 主簧工況的前 Anti-dive 與後 Anti-lift 各自減少該軸的懸吊變形，再相加為整車 Pitch；輪胎變形保留完整負載轉移的部分。"
           "Pitch 每軸一組彈簧，與第 18 節單輪等效案例的座標及彈簧數量不同。")
