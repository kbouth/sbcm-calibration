import pyvisa as visa
import numpy as np
from struct import unpack
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox
from time import sleep
import epics
from matplotlib.widgets import Button
import os
from pylogix import PLC
from matplotlib.widgets import RectangleSelector

rm = visa.ResourceManager()

#Chain A Keithley 2100 DMM Module:
done=0
while(done==0):
    DMMsn = input('Enter serial number of the Keithley 2100 DMM for Chain A (Default=8020356, "H" for help, "Q" to quit):')
    if(DMMsn=="H"):
        print('Serial Number is at the rear of the module on a small white label')
    elif(DMMsn=="Q"):
        print('Quiting...')
        exit()
    else:
        if(DMMsn==""):
            DMMsn=8020356 #the default serial number
        dev='USB0::0x05E6::0x2100::'+str(DMMsn)+'::INSTR' 
        print(dev)
        dmmA = rm.open_resource(dev)
        print('\nDMM-A USB Open Successful!')
        response = dmmA.query('*IDN?')
        model1_number = int(response[32:36])
        if(model1_number != 2100):
            print('Keithley 2100 DMM NOT FOUND...exiting!')
            done = 0
        else:
            print('Chain A Keithley 2100 DMM FOUND.')
            dmmA.write(':SENS:FUNC "VOLT:DC"')
            done = 1
            
#Chain B Keithley 2100 DMM Module:
done=0
print("\n\n\n")
while(done==0):
    DMMsn = input('Enter serial number of the Keithley 2100 DMM for Chain B (Default=8020357, "H" for help, "Q" to quit):')
    if(DMMsn=="H"):
        print('Serial Number is at the rear of the module on a small white label')
    elif(DMMsn=="Q"):
        print('Quiting...')
        exit()
    else:
        if(DMMsn==""):
            DMMsn=8020357 #the default serial number
        dev='USB0::0x05E6::0x2100::'+str(DMMsn)+'::INSTR' 
        print(dev)
        dmmB = rm.open_resource(dev)
        print('\nDMM-A USB Open Successful!')
        response = dmmB.query('*IDN?')
        model1_number = int(response[32:36])
        if(model1_number != 2100):
            print('Keithley 2100 DMM NOT FOUND...exiting!')
            done = 0
        else:
            print('Chain A Keithley 2100 DMM FOUND.')
            dmmB.write(':SENS:FUNC "VOLT:DC"')
            done = 1

props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
good = dict(boxstyle='round', facecolor='palegreen', alpha=0.5)
bad = dict(boxstyle='round', facecolor='lightcoral', alpha=0.5)

#DCCT EPS CompactLogix L32E PLC in Cell 3:
EPS_PLC = PLC()
# Set the IP address of DCCT EPS PLC
EPS_PLC.IPAddress = '10.0.128.49'
sleep(1)
Ereply = EPS_PLC.Read("EPS_I")
if Ereply.Status == 'Success':
    print('EPS PLC Found!')
else:
    print('EPS PLC ERROR! Quiting...')
    exit()

xmin1=0
xmax1=1
def rbbox1(eclick, erelease):
    global xmin1
    global xmax1  
    xmin1 = int(min(eclick.xdata,erelease.xdata))
    xmax1 = int(max(eclick.xdata,erelease.xdata))
    
year = input("\n\nEnter the Year:")
if(int(year)<2024 or int(year)>2064):
    print("Bad Input... Exiting.")
    exit()
    
fbeam = "SBCM_"+year+"_BeamCurve.txt"

if(os.path.exists(fbeam)):
    resp = input("File "+fbeam+" exists.  Overwrite? (Y or N):")
    if(resp!="Y"):
        exit()
        
fb = open(fbeam,"w")

plt.ion()
f,ax = plt.subplots(2,1,figsize=(8,10))
ax02 = ax[0].twinx()

#rs0 = RectangleSelector(ax[0],rbbox1,drawtype='box', useblit=False, button=[1], 
#    minspanx=5, minspany=5, spancoords='pixels',interactive=True)

rs0 = RectangleSelector(ax[0],rbbox1, button=[1]) 

N = 0
VBM=[]
VRA=[]
VRB=[]
TM=[]

while(True):
    Va = 1000.0*float(dmmA.query("MEAS:VOLT:DC?"))
    Vb = 1000.0*float(dmmB.query("MEAS:VOLT:DC?"))
    Ereply = EPS_PLC.Read("EPS_I")
    if(Ereply.Status!='Success'):
        print('EPS DCCT Transfer ERROR! Quitting...')
        exit()
    Vbeam = Ereply.Value
    data = str(round(Va,2))+','+str(round(Vb,2))+','+str(round(Vbeam,2))+'\n'
    print(data)
    print(xmin1,xmax1)
    fb.write(data)
    VBM.append(Vbeam)
    VRA.append(Va)
    TM.append(N)
    N=N+1
    
    ax[0].clear()
    ax02.clear()
    ax[0].plot(TM,VBM,'-o',color='blue')
    ax[0].grid(True)
    ax[0].set_xlabel("Time (Secs)")
    ax[0].set_ylabel("EPS PLC DCCT Current (mA)",color='blue')
    ax[0].set_title("SBCM-A Beam Curve")
    ax[0].tick_params(axis='y', labelcolor='blue')
    ax02.plot(TM,VRA,'-o',color='red')
    ax02.set_ylabel("SBCM-A Rectifier (mV)",color='red')
    ax02.tick_params(axis='y', labelcolor='red')
    
    ax[1].clear()
    ax[1].plot(VRA,VBM,'-o')
    ax[1].grid(True)
    ax[1].set_xlabel("SBCM-A Rectifier Output (mV)")
    ax[1].set_ylabel("EPS PLC DCCT Current (mA)")
    ax[1].set_title("SBCM-A Beam Curve")
    
    plt.pause(0.01)

    sleep(1)
