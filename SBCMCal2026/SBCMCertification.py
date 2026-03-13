import pyvisa as visa
from pylogix import PLC
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from time import sleep
import numpy as np
import os
from math import isnan
from random import randint

chain = input("Enter the SBCM Chain (A or B):")
if(chain!="A" and chain!="B"):
    print("Bad Input... Exiting.")
    exit()

resp = input("From the Characteristic Curve Enter the Slope for Channel "+chain+": ")
try:
    mcc = float(resp)
except:
    print("Bad Slope Input... Exiting.")
    mcc = 20.272
#    exit()

resp = input("From the Characteristic Curve Enter the Intercept for Channel "+chain+": ")
try:
    bcc = float(resp)
except:
    print("Bad Intercept Input... Exiting.")
    bcc = 25.813
#    exit()
    
resp = input("From the Beam Scan Enter the Slope for Channel "+chain+": ")
try:
    mbs = float(resp)
except:
    print("Bad Slope Input... Exiting.")
    mbs = 0.0516
#    exit()

resp = input("From the Characteristic Curve Enter the Intercept for Channel "+chain+": ")
try:
    bbs = float(resp)
except:
    print("Bad Intercept Input... Exiting.")
    bbs = 0.39
#    exit()
       
year = input("\nEnter Year : ")
if(int(year)<2024 or int(year)>2064):
    print("Bad Year Input... Exiting.")
    exit()

rm = visa.ResourceManager()
dev = 'TCPIP0::10.0.128.183::5025::SOCKET'
source = rm.open_resource(dev)
print('\nRF Source TCPIP Open Successful!')
source.read_termination = '\n'
source.write_termination = '\n'
response = source.query('*IDN?')
print(response[35:42])
serial_number = int(response[35:41])
if(serial_number != 102463):
    print('R&S SMB100B Source NOT FOUND...exiting!')
    exit()
else:
    print('R&S SMB100B Source FOUND.')
    
source.write("FREQ 499.68e6")
source.write("POW 0.000V")
source.write("OUTP ON")

SBCM_PLC = PLC()
if(chain=='A'):
    SBCM_PLC.IPAddress = '10.0.128.84'
else:
    SBCM_PLC.IPAddress = '10.0.128.85'
sleep(1)
Ereply = SBCM_PLC.Read("WDT_Status")
if Ereply.Status == 'Success':
    print('SBCM PLC Found!')
else:
    print('SBCM PLC ERROR! Quiting...')
    exit()
reply = SBCM_PLC.Read("WDT_Status")
if reply.Status == 'Success':
    oldwdt = reply.Value
else:
    print("SBCM PLC WDT Error")
    exit()
reply = SBCM_PLC.Read("COMP_Status")
if reply.Status == 'Success':
    oldcomp = reply.Value
else:
    print("SBCM PLC COMP Error")
    exit()
reply = SBCM_PLC.Read("RELAY_Status")
if reply.Status == 'Success':
    oldrelay = reply.Value
else:
    print("SBCM PLC RELAY Error")
    exit()
    
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
good = dict(boxstyle='round', facecolor='palegreen', alpha=0.5)
bad = dict(boxstyle='round', facecolor='lightcoral', alpha=0.5)

fa, ax = plt.subplots(1,1,figsize=(10,8))
ax2 = ax.twinx()

VRF=[]
IBC=[]
FILT=[]
WDT=[]
COM=[]
REL=[]
TEST = [0,0,0,0,0,0]

t=0
Vrf = 0
Icalc = 0
save = 0
direction = 1

while True:
    if(Icalc>550): direction=-1
    if(Icalc<20.0 and direction==1):
        Vrf = Vrf + 0.0002
    elif(Icalc<70.0 and direction==1):
        Vrf = Vrf + 0.0005
    elif(Icalc<550.0 and direction==1):
        Vrf = Vrf + 0.004
    elif(Icalc>70.0 and direction==-1):
        Vrf = Vrf - 0.004
    elif(Icalc>20.0 and direction==-1):
        Vrf = Vrf - 0.0005
    elif(Icalc>1.0 and direction==-1):
        Vrf = Vrf - 0.0002
    else:
        save = 1
    cmd = "POW "+str(Vrf)+"V"
    source.write(cmd)
    sleep(1)
    VRF.append(1000*Vrf)
    Icalc = mcc*mbs*1000*Vrf + mbs*bcc + bbs
    print(round(Icalc,2),round(Vrf,5),direction)
    IBC.append(Icalc)

    reply = SBCM_PLC.Read("Rect_Filter")
    if reply.Status == 'Success':
        filt = reply.Value
        FILT.append(filt)
    else:
        print("SBCM PLC FILTER Error")
    reply = SBCM_PLC.Read("WDT_Status")
    if reply.Status == 'Success':
        wdt = reply.Value
        WDT.append(wdt)
    else:
        print("SBCM PLC WDT Error")
    reply = SBCM_PLC.Read("COMP_Status")
    if reply.Status == 'Success':
        comp = reply.Value
        COM.append(2*comp)
    else:
        print("SBCM PLC COMP Error")
    reply = SBCM_PLC.Read("RELAY_Status")
    if reply.Status == 'Success':
        relay = reply.Value
        REL.append(3*relay)
    else:
        print("SBCM PLC RELAY Error")

# Start Plotting...
    ax.clear()
    ax2.clear()
    ax.plot(IBC,'-o',color='blue')
    ax.grid(True)
    ax.set_xlabel("Time (Seconds)")
    ax.set_ylabel("Calculated Beam Current (mA)",color='blue')
    ax.set_title("SBCM-"+chain+" "+" Certification Test")
    ax.tick_params(axis='y', labelcolor='blue')
    line = "Icalc: "+str(round(Icalc,2))+" mA\nVfilt: "+str(int(filt))+" mV\nVrf  : "+str(round(1000*Vrf,1))+" mV"
    ax.text(0.02, 1.10,line,transform=ax2.transAxes,fontsize=12,fontname='Courier New',weight='bold',verticalalignment='top', bbox=props)
    ax2.plot(WDT,'-o',color='red')
    ax2.plot(COM,'-o',color='green')
    ax2.plot(REL,'-o',color='black')
    ax2.set_ylabel("SBCM-"+chain+" Status Bits",color='black')
    ax2.set_yticks([0,1,2,3,4,5])
    ax2.set_yticklabels(['OFF','WDT','COM','REL','',''])
    if(oldwdt!=wdt):
        if(wdt==1):
            TEST[0] = 1
            IwdtOn = Icalc
            VwdtOn = filt 
        else:
            TEST[3] = 1
            IwdtOff = Icalc
            VwdtOff = filt 
        oldwdt = wdt            
    if(oldcomp!=comp):
        if(comp==1):
            TEST[1] = 1
            IcompOn = Icalc
            VcompOn = filt
        else:
            TEST[4] = 1
            IcompOff = Icalc
            VcompOff = filt
        oldcomp = comp
    if(oldrelay!=relay):
        if(relay==1):
            TEST[2] = 1
            IrelayOn = Icalc
            VrelayOn = filt 
        else:
            TEST[5] = 1
            IrelayOff = Icalc
            VrelayOff = filt
        oldrelay = relay
    if(TEST[0]==1):
        line = "WDT ON: Beam="+str(round(IwdtOn,2))+"mA  SBCM="+str(round(VwdtOn,0))+"mV"
        ax2.text(0.02, 0.96,line,transform=ax2.transAxes,fontsize=10,verticalalignment='top', bbox=props)
    if(TEST[1]==1):
        line = "COMP ON: Beam="+str(round(IcompOn,2))+"mA  SBCM="+str(round(VcompOn,0))+"mV"
        ax2.text(0.02, 0.89,line,transform=ax2.transAxes,fontsize=10,verticalalignment='top', bbox=props)
    if(TEST[2]==1):
        line = "RELAY ON: Beam="+str(round(IrelayOn,2))+"mA  SBCM="+str(round(VrelayOn,0))+"mV"
        ax2.text(0.02, 0.82,line,transform=ax2.transAxes,fontsize=10,verticalalignment='top', bbox=props)
    if(TEST[3]==1):
        line = "WDT OFF: Beam="+str(round(IwdtOff,2))+"mA  SBCM="+str(round(VwdtOff,0))+"mV"
        ax2.text(0.56, 0.96,line,transform=ax2.transAxes,fontsize=10,verticalalignment='top', bbox=props)
    if(TEST[4]==1):
        line = "COMP OFF: Beam="+str(round(IcompOff,2))+"mA  SBCM="+str(round(VcompOff,0))+"mV"
        ax2.text(0.56, 0.89,line,transform=ax2.transAxes,fontsize=10,verticalalignment='top', bbox=props)
    if(TEST[5]==1):
        line = "RELAY OFF: Beam="+str(round(IrelayOff,2))+"mA  SBCM="+str(round(VrelayOff,0))+"mV"
        ax2.text(0.56, 0.82,line,transform=ax2.transAxes,fontsize=10,verticalalignment='top', bbox=props) 
        
    plt.pause(0.1)
    
    if(save==1):
        fname = "SBCM_Chain_"+chain+"_Certification_"+year
        fa.savefig(fname+".png")
        fdat = open(fname+'.txt',"w")
        for i in range(0,len(IBC)):
            dat = str(round(IBC[i],3))+','+str(round(FILT[i],3))+','+str(round(VRF[i],5))+','
            dat = dat+str(WDT[i])+','+str(COM[i])+','+str(REL[i])+'\n'
            fdat.write(dat)
        fdat.close()
        plt.show(block=True)
        exit()
