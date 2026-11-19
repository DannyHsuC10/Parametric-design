import numpy as np
import Load_solving as fwl

g = 9.81

FWL_data = fwl.CalculationInput(# 定義物件
    m=309.5,
    h=0.284,
    L=1.55,
    d=1.25,
    ax=0.3 * g,
    ay=1.5 * g,
    CG_x=(0.48, 0.52),# front, rear
    CG_y=(0.5, 0.5),# left, right
    K=np.diag([30000, 30000, 25000, 25000])# k_fl, k_fr, k_rl, k_rr
)

load = fwl.Model(FWL_data)
print(load.solve_cg())
print(load.solve_lsm())
print(load.solve_lagrange())