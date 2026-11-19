import numpy as np #匯入數學
from physics import number_relation as nr
g = 9.8#重力加速度數值
#=====================================================(運動)
def length_lrth (l,r,th):#(長度,半徑,角度)
    ans = nr.multiplication(l,r,th)
    return(ans)

def length_Sat (S,a,t):#(長度,加速度,時間)
    ans = nr.twe_times_integral(S,a,t)
    return(ans)

def high_ht(h,t):#(高度,時間)
    ans = nr.twe_times_integral(h,9.8,t)
    return(ans)

def theta_thAt (th,A,t):#(角度,角加速度,時間)
    ans = nr.twe_times_integral(th,A,t)
    return(ans)

def sumlength_lxyz (l,x,y,z):#(長度,x值,y值,z值)
    ans = nr.sum_of_squares(l,x,y,z)
    return(ans)    

def velocity_StV (S,t,V):#(距離,時間,速度)
    ans = nr.multiplication(S,t,V)
    return(ans)

def velocity_Vwr (V,w,r):#(速度,角速度,半徑)
    ans = nr.multiplication(V,w,r)
    return(ans)

def sumvelocity_Vxyz (V,x,y,z):#(速度,x值,y值,z值)
    ans = nr.sum_of_squares(V,x,y,z)
    return(ans)

def Angularvelocity_wt (w,t):#(角速度,週期)
    ans = nr.multiplication(2*np.pi,w,t)
    return(ans)

def acceleration_Vta (V,t,a):#(速度,時間,加速度)
    ans = nr.multiplication(V,t,a)
    return(ans)

def acceleration_aAr (a,A,r):#(加速度,角加速度,半徑)
    ans = nr.multiplication(a,A,r)
    return(ans)

def centripetalacceleration_acDw (ac,D,w):#(加速度,圓周運動直徑,角速度)
    ans = nr.twe_times_integral(ac,D,w)
    return(ans)

def sumacceleration_axyz(a,x,y,z):#(加速度,x值,y值,z值)
    ans = nr.sum_of_squares(a,x,y,z)
    return(ans)
#=====================================================(力)
def force_FMa (F,M,a):#(力,質量,加速度)
    ans = nr.multiplication(F,M,a)
    return(ans)

def sumforce_Fxyz (F,x,y,z):#(力,x值,y值,z值)
    ans = nr.sum_of_squares(F,x,y,z)
    return(ans)

def torque_TFr (T,F,r):#(力矩,力,半徑)
    ans = nr.multiplication(T,F,r)
    return(ans)

def torque_TIA (T,I,A):#(力矩,轉動慣量,角加速度)
    ans = nr.multiplication(T,I,A)
    return(ans)

def momentum_PMV (P,M,V):#(動量,質量,速度)
    ans = nr.multiplication(P,M,V)
    return(ans)

def Angularmomentum_LIw (L,I,w):#(角動量,轉動慣量,角速度)
    ans = nr.multiplication(L,I,w)
    return(ans)
#=====================================================(能量)
def work_WFx (W,F,x):#(功,力,位移)
    ans = nr.multiplication(W,F,x)
    return(ans)

def energy_EhMg (E,h,Mg):#(能量,高度,重量!牛頓N)
    ans = nr.multiplication(E,h,Mg)
    return(ans)

def energy_EMV (E,M,V):#(能量,質量,速度)
    ans = nr.multiplication(E,M,V)
    return(ans)

def energy_Ekx (E,k,x):#(能量,彈性系數,位移)
    ans = nr.twe_times_integral(E,k,x)
    return(ans)

def power_PFV (P,F,V):#(功率,力,速度)
    ans = nr.multiplication(P,F,V)
    return(ans)

def power_PTw (P,T,w):#(功率,力矩,角速度)
    ans = nr.multiplication(P,T,w)
    return(ans)

def power_EPt (E,P,t):#(能量,功率,時間)
    ans = nr.multiplication(E,P,t)
    return(ans)
#=====================================================(材料)
def deformation_Fkx (F,k,x):#(力,彈性系數,變形量)
    ans = nr.multiplication(F,k,x)
    return(ans)

def avgstress_FPA (F,P,A):#(力,壓力,面積)
    ans = nr.multiplication(F,P,A)
    return(ans)
    
def avgshear_FVA (F,V,A):#(力,剪力,面積)
    ans = nr.multiplication(F,V,A)
    return(ans)
#=====================================================(其他)
def friction_fuN (f,u,N):#(摩擦力,摩擦系數,正向力)
    ans = nr.multiplication(f,u,N)
    return(ans)

def density_MVD (M,D,V):#(質量,密度,體積)
    ans = nr.multiplication(M,D,V)
    return(ans)