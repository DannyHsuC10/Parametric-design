"""Export the full sizing snapshot as a filterable Excel worksheet."""

from io import BytesIO
import math
import re
from xml.etree.ElementTree import Element, SubElement, tostring
from zipfile import ZIP_DEFLATED, ZipFile

from project import FIELDS
from vehicle_initial_sizing_report import iter_result_rows


GROUP_LABELS = {
    "parameters": "本次參數與衍生值",
    "cg": "重心高度幾何檢查",
    "skidpad": "Skidpad 與下壓力",
    "aero": "空力係數",
    "angle_stiffness": "目標角度所需剛性",
    "compressed_travel": "行程限制所需剛性",
    "selected_stiffness": "採用剛性與頻率",
    "tire": "輪胎柔度與彈簧簧率",
    "frequency_mass": "質量與自然頻率",
    "heave": "Heave 頻率反算",
    "tender": "主簧與 Tender 串聯",
    "anti": "懸吊 Anti 比例",
    "front_rc": "前軸 Roll Center",
    "rear_rc_height_m": "後軸 Roll Center",
    "fvsa": "FVSA 與外傾角增益",
    "lateral_tire_roll": "輪胎變形與側傾",
    "caster": "Caster 反算",
    "steering_checks": "轉向外傾方向檢查",
    "compression": "下壓力與 Tender 壓縮",
    "wheel_loads": "四輪垂直輪載",
    "tire_forces": "四輪三向需求力",
    "gear": "加速與極速齒比",
    "brake": "煞車力與前後分配",
    "brake_mechanical_advantage": "煞車機構機械利益",
    "damping": "臨界阻尼",
    "rate_cases": "Ks、Kw、Kr 與頻率",
    "gradients": "側傾與俯仰梯度",
}

CONTEXT_LABELS = {
    "front": "前軸", "rear": "後軸",
    "FL": "左前輪", "FR": "右前輪", "RL": "左後輪", "RR": "右後輪",
    "pitch": "俯仰", "roll": "側傾",
    "pure_heave": "純 Heave 主簧", "heave_only": "純 Heave 主簧",
    "heave_with_tender": "本次採用的 Heave 設定",
    "combined_average": "Heave 與 Roll 簧率平均",
    "requested_point": "設定減速度工況", "limit_point": "物理極限工況",
    "wheel_loads_N": "原始垂直輪載", "wheel_forces": "",
}

UNIT_SUFFIXES = (
    ("Nms_per_rad", "N·m·s/rad"), ("Nm_per_rad", "N·m/rad"),
    ("Ns_per_m", "N·s/m"), ("N_per_m", "N/m"),
    ("kg_per_m3", "kg/m³"), ("kg_m2", "kg·m²"),
    ("m_per_s2", "m/s²"), ("m_per_s", "m/s"), ("kmh", "km/h"),
    ("deg_per_mm", "°/mm"), ("deg_per_m", "°/m"),
    ("rad_per_m", "rad/m"), ("deg_per_g", "°/g"),
    ("percent", "%"), ("deg", "°"), ("rad", "rad"), ("Hz", "Hz"),
    ("Nm", "N·m"), ("N", "N"), ("kg", "kg"),
    ("mm", "mm"), ("m", "m"), ("rpm", "rpm"), ("s", "s"), ("g", "g"),
)

FIELD_UNITS = {
    "g": "m/s²", "L": "m", "t": "m", "Ks": "N/m", "F_ref": "N", "v_ref": "m/s",
    "FL": "N", "FR": "N", "RL": "N", "RR": "N",
}

# Keys omit the unit suffix. Nested paths supply the axle, wheel or calculation case.
FIELD_LABELS = {
    "g": "重力加速度",
    "L": "前後軸距，為重心至前軸及後軸距離的總和",
    "t": "前後輪距的平均值",
    "wf": "前軸靜態重量占比",
    "wr": "後軸靜態重量占比",
    "steering_angle": "達到指定最小轉彎半徑的轉向角",
    "active_heave_spring": "本次計算採用的 Heave 彈簧剛性",
    "cg_min_track": "前後輪距中較小的值",
    "cg_height_limit_45": "45° 傾斜幾何檢查的重心高度上限",
    "cg_height_margin_45": "45° 重心高度上限扣除實際高度的餘裕",
    "cg_safe_45": "是否通過 45° 傾斜幾何檢查",
    "cg_status_45": "45° 傾斜幾何檢查的判定文字",
    "cg_height_limit_60": "60° 傾斜幾何檢查的重心高度上限",
    "cg_height_margin_60": "60° 重心高度上限扣除實際高度的餘裕",
    "cg_safe_60": "是否通過 60° 傾斜幾何檢查",
    "cg_status_60": "60° 傾斜幾何檢查的判定文字",
    "cg_geometric_safe": "是否同時通過 45° 和 60° 幾何檢查",
    "F_ref": "依摩擦需求反算的原始下壓力，保留負值",
    "v_ref": "目標圈時對應的參考車速",
    "skidpad_target_lap_time": "Skidpad 目標單圈時間",
    "skidpad_target_downforce": "目標圈時所需下壓力",
    "skidpad_target_required_mu": "含安全係數的目標等效橫向摩擦需求",
    "skidpad_total_mass": "Skidpad 計算採用的整車質量",
    "skidpad_diameter": "Skidpad 計算圓的直徑",
    "skidpad_safety_factor": "目標橫向摩擦需求的安全係數",
    "skidpad_target_speed": "目標圈時對應的車速",
    "skidpad_target_lateral_acceleration": "目標車速與圓半徑對應的側向加速度",
    "skidpad_required_aero_downforce": "將負需求截為零後，整車實際需要的空力下壓力",
    "target_coefficient_C": "採 F = CρAv² 定義的目標下壓力係數",
    "standard_downforce_coefficient_Cl": "採 F = ½ClρAv² 定義的下壓力係數",
    "stiffness": "此工況所需或採用的等效線性剛性",
    "displacement": "目標角度換算的單側位移",
    "angle": "達到指定壓縮行程時對應的車體角度",
    "frequency": "由採用剛性與簧上質量估算的自然頻率",
    "Ks": "以目標乘坐剛性反算的等效彈簧簧率",
    "Ks_pitch": "俯仰工況反算的彈簧簧率",
    "Ks_roll": "側傾工況反算的彈簧簧率",
    "target_ride_rate": "計入輪胎柔度後的目標乘坐剛性",
    "actual_ride_rate": "由實際彈簧、運動比和輪胎串聯得到的乘坐剛性",
    "m_total_vehicle": "整車總質量，包含簧上質量和四輪簧下質量",
    "quarter_sprung_mass": "全車簧上質量的四分之一",
    "unsprung_mass_ratio_target": "單輪簧下質量占該輪簧上與簧下質量合計的百分比",
    "equivalent_spring_stiffness": "頻率估算採用的等效彈簧簧率",
    "wheel_rate": "彈簧簧率經運動比換算至輪端的剛性 Kw",
    "ride_rate": "輪端剛性與輪胎垂向剛性串聯後的乘坐剛性 Kr",
    "frequency_sprung_target": "目前乘坐剛性對應的簧上自然頻率",
    "frequency_unsprung_target": "目前輪端及輪胎剛性對應的簧下自然頻率",
    "target_natural_frequency": "反算 Heave 剛性時採用的目標簧上頻率",
    "current_sprung_frequency": "調整 Heave 前的簧上自然頻率",
    "current_unsprung_frequency": "調整 Heave 前的簧下自然頻率",
    "can_reach_target": "固定 Roll 剛性時能否達到目標簧上頻率",
    "Ks_required_target_frequency": "達到目標簧上頻率所需的等效彈簧簧率",
    "Ks_scale_target_frequency": "目標等效彈簧簧率相對原值的比例",
    "heave_stiffness_reduction": "Heave 彈簧剛性需減少的量",
    "adjusted_sprung_frequency": "調整 Heave 後的簧上自然頻率",
    "adjusted_unsprung_frequency": "調整 Heave 後的簧下自然頻率",
    "K_heave_main": "主 Heave 彈簧的剛性",
    "K_tender_required": "達到目標串聯剛性所需的 Tender 簧率",
    "tender_to_heave_stiffness_ratio": "Tender 簧率除以主 Heave 簧率",
    "K_series_target": "主簧與 Tender 串聯的目標等效剛性",
    "K_heave_with_tender": "主 Heave 彈簧與 Tender 串聯後的剛性",
    "suspension_stiffness": "對應車軸的懸吊等效線性剛性",
    "chassis_stiffness": "對應車軸的車體垂向等效剛性",
    "chassis_to_suspension_stiffness_ratio": "車體等效剛性與懸吊剛性的比值",
    "anti_ratio": "由懸吊與車體剛性求得的 Anti 比例",
    "anti": "Anti 設定以百分比表示的數值",
    "suspension_fraction": "由懸吊彈性路徑承受的載重轉移占比",
    "equivalent_stiffness": "Anti 最佳設定對應的等效剛性",
    "normalized_min_stiffness": "最小等效剛性除以基準懸吊剛性",
    "acceleration_ratio": "加速與煞車工況的加速度量級比值",
    "front_anti_dive": "前軸煞車 Anti-dive 設定",
    "rear_anti_lift": "後軸煞車 Anti-lift 設定",
    "rear_anti_squat": "後軸加速 Anti-squat 設定",
    "front_anti_lift": "前軸加速 Anti-lift 設定",
    "front_anti": "前軸最終採用的 Anti 設定",
    "rear_anti": "後軸最終採用的 Anti 設定",
    "rc_normalized_optimal_ratio": "最佳前軸 Roll Center 高度與重心高度的比值",
    "rc_normalized_min_stiffness": "前軸 Roll Center 最佳點的正規化等效剛性",
    "rc_suspension_fraction": "前軸側向載重轉移中由懸吊彈性路徑承受的占比",
    "rc_normalized_optimal_height": "解析求得的最佳前軸 Roll Center 高度",
    "rear_rc_height": "由前 Roll Center 與前後軸配置估算的後 Roll Center 高度",
    "max_roll_angle": "可用懸吊行程對應的最大側傾角",
    "fvsa_length": "前視虛擬擺臂長度",
    "camber_change": "每單位垂向行程造成的外傾角變化",
    "camber_gain": "每單位垂向行程的外傾角增益",
    "max_camber_change": "最大側傾工況對應的外傾角變化",
    "axle_mass": "分配至此軸的整車質量",
    "lateral_force": "作用在此軸的側向慣性力",
    "roll_moment": "側向力作用於重心高度所產生的側傾力矩",
    "axle_weight": "此軸的靜態重量",
    "left_normal_load": "左輪原始垂直輪載",
    "right_normal_load": "右輪原始垂直輪載",
    "normal_load_difference": "左右輪垂直輪載的有號差值",
    "lateral_load_transfer": "此軸由一側轉移至另一側的輪載",
    "static_compression": "無側向載重轉移時的單輪靜態壓縮量",
    "left_linear_compression": "線性模型估算的左輪總壓縮量",
    "right_linear_compression": "線性模型估算的右輪總壓縮量",
    "left_compression_change": "側向加速度造成的左輪壓縮增量",
    "right_compression_change": "側向加速度造成的右輪壓縮增量",
    "deformation_difference": "左右輪胎線性壓縮量的有號差值",
    "linear_tire_roll_angle": "由左右輪線性變形差換算的參考側傾角",
    "tire_roll_angle": "接地條件有效時的輪胎額外側傾角",
    "contact_valid": "原始輪載是否符合接地假設",
    "at_lift_boundary": "是否達到單側輪胎離地的臨界點",
    "ay_contact_limit": "模型可維持雙輪接地的側向加速度界限",
    "base_camber": "加上轉向外傾變化之前的外傾角",
    "kpi": "主銷內傾角",
    "kpi_camber_change": "主銷內傾造成的轉向外傾角變化",
    "required_caster_sine": "抵消外傾角所需的 Caster 正弦值",
    "solution_status": "Caster 反算結果的狀態代碼",
    "has_real_solution": "指定條件是否存在實數 Caster 解",
    "caster": "轉向工況採用或反算的主銷後傾角",
    "raw_steering_camber_change": "原始轉向模型的外傾角變化",
    "camber_direction_factor": "把原始外傾角換成報告方向慣例的符號因子",
    "caster_camber_change": "Caster 分量造成的外傾角變化",
    "steering_camber_change": "轉向造成的總外傾角變化",
    "final_camber": "基礎外傾加上轉向變化後的外傾角",
    "reason": "Caster 求解狀態的文字原因",
    "raw_camber_change": "方向查核用的原式轉向外傾角變化",
    "tender_bind_vehicle_downforce": "Tender 設計切換工況施加於整車的下壓力",
    "tender_bind_force": "下壓力分配後單組串聯彈簧承受的力",
    "main_spring_compression": "此工況的單組主簧壓縮增量",
    "tender_bind_spring_stroke": "此工況的單組 Tender 壓縮增量",
    "tender_bind_total_stroke": "單組主簧與 Tender 壓縮增量之和",
    "front_compression": "前懸吊相對原平衡位置的壓縮增量",
    "rear_compression": "後懸吊相對原平衡位置的壓縮增量",
    "heave": "車身垂向壓縮量",
    "total_mass": "此工況採用的整車總質量",
    "total_normal_load": "四輪原始垂直輪載之和",
    "front_axle_load": "前軸垂直輪載總和",
    "rear_axle_load": "後軸垂直輪載總和",
    "longitudinal_transfer": "由縱向加速度造成的前後軸載重轉移",
    "front_roll_fraction": "分配到前軸的側傾載重轉移比例",
    "front_lateral_transfer": "前軸左右輪之間的側向載重轉移",
    "rear_lateral_transfer": "後軸左右輪之間的側向載重轉移",
    "raw_Fz": "原始垂直輪載，保留負輪載",
    "Fx": "依有效垂直輪載占比分配到單輪的縱向需求力",
    "Fy": "依有效垂直輪載占比分配到單輪的側向需求力",
    "Fz": "將負值截為零後，用於分配需求力的垂直輪載",
    "force_magnitude": "單輪縱向、側向與垂直三向力的合力大小",
    "load_fraction": "此輪占四輪非負垂直輪載總和的比例",
    "total_Fx": "整車縱向需求力",
    "total_Fy": "整車側向需求力",
    "clipped_total_Fz": "四輪輪載截零後的總和",
    "reference_only": "有原始負輪載時，需求力分配結果僅供參考",
    "most_loaded_wheel": "三向合力最大的輪位代碼",
    "gear_rate_acceleration": "反算加速齒比的目標縱向加速度",
    "gear_rate_target_speed": "反算極速齒比的目標車速",
    "front_axle_Fx": "加速工況分配至前軸的縱向力",
    "rear_axle_Fx": "加速工況分配至後軸的縱向力",
    "maximum_wheel_Fx": "加速工況下需求縱向力最大的單輪力",
    "wheel_torque_required": "達到目標加速度的單輪扭矩需求",
    "target_wheel": "目標極速對應的輪胎轉速",
    "gear_ratio_accel": "依扭矩需求反算的加速齒比",
    "gear_ratio_top_speed": "依馬達最高轉速與目標極速反算的齒比",
    "gear_ratio_avg": "加速齒比與極速齒比的平均值",
    "deceleration": "此煞車工況的減速度",
    "front_brake_force": "前軸理想煞車力",
    "rear_brake_force": "後軸理想煞車力",
    "front_ratio": "此工況前軸煞車力占總煞車力的比例",
    "rear_ratio": "此工況後軸煞車力占總煞車力的比例",
    "required_tire_mu": "此工況達到減速度目標所需的輪胎摩擦係數",
    "rear_lift_limit": "後軸輪載降為零的減速度極限",
    "physical_deceleration_limit": "同時考量摩擦與後軸離地的減速度極限",
    "target_achievable": "目標減速度是否在物理可行範圍內",
    "brake_design_deceleration": "實際用於設計點計算的減速度",
    "brake_ideal_front_ratio": "由前後煞車力擬合得到的理想前軸分配比例",
    "brake_ideal_rear_ratio": "由前後煞車力擬合得到的理想後軸分配比例",
    "brake_ideal_fit_rear_over_front": "回歸直線的後煞車力除以前煞車力",
    "brake_total_required_force": "前後軸需求煞車力之和",
    "brake_driver_force": "駕駛施加的煞車踏力",
    "brake_mechanical_advantage": "總需求煞車力除以駕駛踏力",
    "roll_total_stiffness": "前後軸合計的側傾角剛性",
    "roll_total_critical_damping": "以車身側傾座標表示的總臨界阻尼",
    "spring_stiffness": "彈簧座標的簧率",
    "angular_stiffness": "換算到車身角度座標的剛性",
    "stiffness_fraction": "此軸剛性占前後軸合計剛性的比例",
    "angular_damping": "此軸換算到車身角度座標的阻尼",
    "damper_critical_damping": "換算到避震器行程座標的臨界阻尼",
    "sprung_mass": "此軸分配的簧上質量",
    "body_stiffness": "換算到車身垂向位移座標的剛性",
    "body_critical_damping": "車身垂向位移座標的臨界阻尼",
    "spring_rate": "此工況的彈簧簧率 Ks",
    "sprung_mass_per_wheel": "此軸分配至單輪的簧上質量",
    "spring_coordinate_mass": "依運動比換算至彈簧位移座標的等效質量",
    "frequency_Ks": "以彈簧座標 Ks 計算的自然頻率",
    "frequency_Kw": "以輪端剛性 Kw 計算的簧上自然頻率",
    "frequency_Kr": "以含輪胎柔度的乘坐剛性 Kr 計算的簧上自然頻率",
    "critical_damping_Ks": "以彈簧座標 Ks 計算的臨界阻尼",
    "critical_damping_Kw": "以輪端剛性 Kw 計算的臨界阻尼",
    "critical_damping_Kr": "以含輪胎柔度的乘坐剛性 Kr 計算的臨界阻尼",
    "roll_axis_height_at_cg": "側傾軸在重心縱向位置的高度",
    "roll_moment_arm": "重心到側傾軸的垂直力臂",
    "roll_suspension_stiffness": "只計懸吊的側傾角剛性",
    "roll_ride_stiffness": "計入輪胎柔度後的側傾角剛性",
    "roll_gradient_suspension": "只計懸吊時，每 1 g 側向加速度的側傾角",
    "roll_gradient_with_tires": "含輪胎柔度時，每 1 g 側向加速度的側傾角",
    "pitch_suspension_stiffness": "只計懸吊的俯仰角剛性",
    "pitch_tire_stiffness": "由輪胎垂向柔度換算的俯仰角剛性",
    "gradient_suspension": "只計懸吊時，每 1 g 縱向減速度的俯仰角",
    "gradient_with_tires": "含輪胎柔度時，每 1 g 縱向減速度的俯仰角",
    "front_suspension_gradient": "前軸懸吊對總俯仰梯度的貢獻",
    "rear_suspension_gradient": "後軸懸吊對總俯仰梯度的貢獻",
    "gradient_with_tires_and_anti": "計入輪胎柔度及前後 Anti 後的俯仰梯度",
}


def _field_details(section, path, value):
    field = FIELDS.get(path) if section == "parameters" else None
    if field:
        label = field["label"]
        if field.get("hint"):
            label += f"（{field['hint']}）"
        return field["unit"] or ("無因次" if field["kind"] == "number" else ""), label

    *parents, leaf = path.split(".")
    context = []
    for part in parents:
        match = re.fullmatch(r"(samples)?\[(\d+)\]", part)
        if match:
            name = "煞車擬合取樣" if match[1] else "轉向方向檢查"
            context.append(f"{name}第 {int(match[2]) + 1} 點")
        elif label := CONTEXT_LABELS.get(part, part):
            context.append(label)

    unit = FIELD_UNITS.get(leaf, "")
    stem = leaf
    if not unit:
        for suffix, symbol in UNIT_SUFFIXES:
            if leaf.endswith("_" + suffix):
                stem, unit = leaf[:-(len(suffix) + 1)], symbol
                break
    label = FIELD_LABELS.get(stem)
    if label is None and stem.endswith("_ratio"):
        label = FIELD_LABELS.get(stem.removesuffix("_ratio"))
    if section == "wheel_loads" and leaf in ("FL", "FR", "RL", "RR"):
        label = CONTEXT_LABELS[leaf]
    if value is None and (path == section or leaf in CONTEXT_LABELS):
        label = CONTEXT_LABELS.get(leaf, GROUP_LABELS.get(section, section)) + "本次無可用結果"
    if not unit and (type(value) in (int, float) or stem.endswith(("_ratio", "_fraction"))):
        unit = "無因次"
    context.append(label or leaf)
    return unit, "／".join(context)


SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
WORKBOOK_PARTS = {
    "[Content_Types].xml": """
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>""",
    "_rels/.rels": f"""
<Relationships xmlns="{PACKAGE_REL_NS}">
  <Relationship Id="rId1" Type="{OFFICE_REL_NS}/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
    "xl/workbook.xml": f"""
<workbook xmlns="{SHEET_NS}" xmlns:r="{OFFICE_REL_NS}">
  <bookViews><workbookView/></bookViews>
  <sheets><sheet name="完整結果" sheetId="1" r:id="rId1"/></sheets>
</workbook>""",
    "xl/_rels/workbook.xml.rels": f"""
<Relationships xmlns="{PACKAGE_REL_NS}">
  <Relationship Id="rId1" Type="{OFFICE_REL_NS}/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="{OFFICE_REL_NS}/styles" Target="styles.xml"/>
</Relationships>""",
    "xl/styles.xml": f"""
<styleSheet xmlns="{SHEET_NS}">
  <fonts count="2">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font>
  </fonts>
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF203F56"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="1"><border/></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="2">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>""",
}


def _write_row(data, index, values):
    row = SubElement(data, "row", r=str(index))
    for column, value in zip("ABCDE", values):
        cell = SubElement(row, "c", r=f"{column}{index}")
        if index == 1:
            cell.set("s", "1")
        if isinstance(value, bool):
            cell.set("t", "b")
            SubElement(cell, "v").text = "1" if value else "0"
        elif isinstance(value, (int, float)) and math.isfinite(value):
            SubElement(cell, "v").text = str(value)
        else:
            if value is None or (isinstance(value, float) and math.isnan(value)):
                value = "無可用解"
            elif isinstance(value, float) and math.isinf(value):
                value = "∞" if value > 0 else "−∞"
            cell.set("t", "inlineStr")
            SubElement(SubElement(cell, "is"), "t", {"xml:space": "preserve"}).text = str(value)


def render_excel_results(snapshot):
    sheet = Element("worksheet", xmlns=SHEET_NS)
    view = SubElement(SubElement(sheet, "sheetViews"), "sheetView", workbookViewId="0")
    SubElement(view, "pane", ySplit="1", topLeftCell="A2", activePane="bottomLeft", state="frozen")
    columns = SubElement(sheet, "cols")
    for index, width in enumerate((28, 66, 18, 13, 80), start=1):
        SubElement(columns, "col", min=str(index), max=str(index), width=str(width), customWidth="1")
    data = SubElement(sheet, "sheetData")
    _write_row(data, 1, ("分類", "欄位", "數值／狀態", "單位", "說明"))
    last_row = 1
    for last_row, (section, path, value) in enumerate(iter_result_rows(snapshot), start=2):
        unit, description = _field_details(section, path, value)
        _write_row(data, last_row, (GROUP_LABELS.get(section, section), path, value, unit, description))
    SubElement(sheet, "autoFilter", ref=f"A1:E{last_row}")

    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as workbook:
        for name, contents in WORKBOOK_PARTS.items():
            workbook.writestr(name, contents.strip())
        workbook.writestr("xl/worksheets/sheet1.xml", tostring(sheet, encoding="utf-8", xml_declaration=True))
    return output.getvalue()
