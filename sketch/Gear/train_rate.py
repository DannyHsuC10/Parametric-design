import tkinter as tk
from PIL import Image, ImageTk
from physics import mechanical_solution as ms
from gear import gear_train as gt
from physics import Mechanics as me
#========================================================(頁面設定)
root = tk.Tk()
root.title('輪系值計算')
root.geometry('1100x600')
#root.configure(background='white') 
img = Image.open('car.png')
tk_img = ImageTk.PhotoImage(img)
canvas = tk.Canvas(root, width=1200, height=600)
canvas.create_image(0, 0, anchor='nw', image=tk_img)   # 在 Canvas 中放入圖片
canvas.place(x=0,y=0)
g = 9.8#重力加速度

def show_data():#
    
    m = float(M_entry.get())#質量Kg
    l = float(l_entry.get())#軸距m
    hcog = float(H_entry.get())#重心高度m
    a = float(a_entry.get())#車輛加速度m/s^2
    R = float(D_entry.get())/2#車輪半徑長度(理論上不能用free long0.259)
    Tmotor = float(T_entry.get())#馬達扭矩N*m
    v = float(V_entry.get())*1000/60/60#車速Km/hr
    
    Fcogl = me.force_FMa(None,m,a)#加速力
    print('加速力:',Fcogl)

    Fdm = ms.moment_balance(Fcogl,hcog,l)#重心轉移量
    print('重心轉移量:',Fdm)

    Ffv = (m*g/2)-Fdm#前輪正向力
    Frv = (m*g/2)+Fdm#後輪正向力
    print('前輪正向力:',Ffv,'後輪正向力',Frv)

    u = a/g #f = umg, F = ma(摩擦力)

    Ffl = me.friction_fuN(None,u,Ffv)#前輪摩擦力
    Frl = me.friction_fuN(None,u,Frv)#後輪摩擦力
    print('前輪摩擦力:',Ffl,'後輪摩擦力:',Frl)

    Mfa = me.torque_TFr(None,Ffl,R)#前軸扭矩
    Mra = me.torque_TFr(None,Frl,R)#後軸扭矩
    print('前軸扭矩:',Mfa,'後軸扭矩:',Mra)

    Mfw = Mfa/2#前輪扭矩
    Mrw = Mra/2#後輪扭矩
    print('前輪扭矩:',Mfw,'後輪扭矩:',Mrw)

    Rwf = gt.simple_gear_ratio(Tmotor,Mfw)#前輪速比
    Rwr = gt.simple_gear_ratio(Tmotor,Mrw)#後輪速比
    print('前輪速比:',Rwf,'後輪速比:',Rwr)

    wwmax = me.velocity_Vwr(v,None,R)#輪角速度
    print('車速:',v)
    print('輪角速度:',wwmax)

    rpm = ms.RPM_w(None,wwmax)#車輪RPM
    print('車輪RPM:',rpm)

    Rn = gt.train_value(14000,rpm)#轉速減速比
    print('轉速減速比:',Rn)

#===========================================================(輸入格)
a_entry = tk.Entry(root)# 建立輸入框車輛加速度
a_entry.place(x=200,y=140)

V_entry = tk.Entry(root)# 建立輸入框車輛極速
V_entry.place(x=200,y=215)

D_entry = tk.Entry(root)# 建立輸入框車輪直徑
D_entry.place(x=50,y=530)

T_entry = tk.Entry(root)# 建立輸入框車輛馬達扭矩
T_entry.place(x=420,y=290)

H_entry = tk.Entry(root)# 建立輸入框車輛馬達扭矩
H_entry.place(x=600,y=350)

M_entry = tk.Entry(root)# 建立輸入框車輛馬達扭矩
M_entry.place(x=750,y=325)

l_entry = tk.Entry(root)# 建立輸入框車輛馬達扭矩
l_entry.place(x=555,y=560)

data_button = tk.Button(root, text="由輸入參數產生數據", command = show_data)#按鈕
data_button.place(x=550,y=50)
#=========================================================(顯示格)
label_y = 10
label_X = 10
gap = 20

a_label = tk.Label(root, text ='加速力:' )
a_label.place(x=label_X,y=label_y)
label_y = label_y+gap

Fcom_label = tk.Label(root, text ='重心轉移力:' )
Fcom_label.place(x=label_X,y=label_y)
label_y = label_y+gap

N_label = tk.Label(root, text ='正向力:' )
N_label.place(x=label_X,y=label_y)
label_y = label_y+gap

f_label = tk.Label(root, text ='摩擦力:' )
f_label.place(x=label_X,y=label_y)
label_y = label_y+gap

Ta_label = tk.Label(root, text ='輪軸扭矩:' )
Ta_label.place(x=label_X,y=label_y)
label_y = label_y+gap

#新的一排
label_X = 300
label_y = 10

Tw_label = tk.Label(root, text ='車輪扭矩:' )
Tw_label.place(x=label_X,y=label_y)
label_y = label_y+gap

V_label = tk.Label(root, text ='車輛極速:' )
V_label.place(x=label_X,y=label_y)
label_y = label_y+gap

w_label = tk.Label(root, text ='車輪角速度:' )
w_label.place(x=label_X,y=label_y)
label_y = label_y+gap

rpm_label = tk.Label(root, text ='車輪RPM:' )
rpm_label.place(x=label_X,y=label_y)
label_y = label_y+gap

e_label = tk.Label(root, text ='輪系值:' )
e_label.place(x=label_X,y=label_y)
label_y = label_y+gap


root.mainloop()