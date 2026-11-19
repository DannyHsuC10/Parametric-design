from physics import Mechanics as me
from physics import number_relation as nr
import numpy as np

def moment_balance(Fi,li,lf):#力矩平衡(力i,長i,長f)
    T = me.torque_TFr(None,Fi,li)
    Ff = me.torque_TFr(T,None,lf)
    return(Ff)#回傳力

def RPM_w (rpm,w):#單位換算W to RPM
    if rpm == None:
        rpm = w*60/(2*np.pi)
        return(rpm)
    if w == None:
        w = rpm*(2*np.pi)/60
        return(w)
    
def Maximum_shear_square (V,A):#矩形面最大剪應力(力,面積)
    Fm = 3*V/(2*A)
    return(Fm)

def  Maximum_shear_circle (V,A):#圓形面最大剪應力(力,面積)
    Fm = 4*V/(3*A)
    return(Fm)

def Maximum_press (M,Y,I):#最大壓應力(力,最大距離,截面二次矩)
    Fm = M*Y/I
    return(Fm)
