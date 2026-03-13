import pyvisa as visa
import numpy as np
from struct import unpack
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox
from time import sleep
import epics
from matplotlib.widgets import Button
import os

chain = input("Enter the SBCM Chain (A or B):")
if(chain!="A" and chain!="B"):
    print("Bad Input... Exiting.")
    exit()

rm = visa.ResourceManager()

if(chain=='A'):
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
            dmm = rm.open_resource(dev)
            print('\nDMM-A USB Open Successful!')
            response = dmm.query('*IDN?')
            model1_number = int(response[32:36])
            if(model1_number != 2100):
                print('Keithley 2100 DMM NOT FOUND...exiting!')
                done = 0
            else:
                print('Chain A Keithley 2100 DMM FOUND.')
                dmm.write(':SENS:FUNC "VOLT:DC"')
                done = 1

if(chain=='B'):            
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
            dmm = rm.open_resource(dev)
            print('\nDMM-A USB Open Successful!')
            response = dmm.query('*IDN?')
            model1_number = int(response[32:36])
            if(model1_number != 2100):
                print('Keithley 2100 DMM NOT FOUND...exiting!')
                done = 0
            else:
                print('Chain A Keithley 2100 DMM FOUND.')
                dmm.write(':SENS:FUNC "VOLT:DC"')
                done = 1

props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
good = dict(boxstyle='round', facecolor='palegreen', alpha=0.5)
bad = dict(boxstyle='round', facecolor='lightcoral', alpha=0.5)

dev = 'TCPIP0::10.0.128.188::5025::SOCKET'
source = rm.open_resource(dev)
print('\nRF Source TCPIP Open Successful!')
source.read_termination = '\n'
source.write_termination = '\n'
response = source.query('*IDN?')
print(response[35:42])
serial_number = int(response[35:41])
if(serial_number != 102801):
    print('R&S SMB100B Source NOT FOUND...exiting!')
    exit()
else:
    print('R&S SMB100B Source FOUND.')

source.write("FREQ 499.68e6")
source.write("POW 0.005V")
source.write("OUTP ON")

year = input("\n\nEnter the Year:")
if(int(year)<2024 or int(year)>2064):
    print("Bad Input... Exiting.")
    exit()

fmeas = "SBCM-"+chain+"_"+year+"_CharCurve.txt"
fraw = "SBCM-"+chain+"_"+year+"_CharCurve.raw"

if(os.path.exists(fmeas)):
    resp = input("File "+fmeas+" exists.  Overwrite? (Y or N):")
    if(resp!="Y"):
        exit()
        
fm = open(fmeas,"w")
fr = open(fraw,"w")

plt.ion()
f,ax = plt.subplots(2,1,figsize=(8,10))

Vsource = []
VdmmAvg = []
VdmmStd = []
for j in range(0,111):
    Vrf = round((j+1)/200.0,3)
    Vsource.append(1000*Vrf)
    cmd = "POW "+str(Vrf)+"V"
    source.write(cmd)
    sleep(3)
    Vdmm=[]
    for i in range(0,16):
        Vmeas = 1000.0*float(dmm.query("MEAS:VOLT:DC?"))
        Vdmm.append(Vmeas)
        print(i,Vrf)
        fr.write(str(i)+","+str(Vrf)+","+str(Vmeas)+"\n")
        sleep(0.4)
    Vavg = np.round(np.mean(Vdmm),3)
    Vstd = np.round(np.std(Vdmm),4)    
    print(Vrf,Vavg,Vstd)
    fm.write(str(Vrf)+","+str(Vavg)+","+str(Vstd)+"\n")
    VdmmAvg.append(Vavg)
    VdmmStd.append(Vstd)
    ax[0].clear()
    ax[0].plot(Vsource,VdmmAvg,'-o')
    ax[0].grid(True)
    ax[0].set_xlabel("RF Level @ 499.68MHz (mV)")
    ax[0].set_ylabel("Rectifier Filter Output (mV)")
    ax[0].set_title("SBCM Chain "+chain+" Characteristic Curve")
    
    ax[1].clear()
    ax[1].plot(Vsource,VdmmStd,'-o')
    ax[1].grid(True)
    ax[1].set_xlabel("RF Level @ 499.68MHz (mV)")
    ax[1].set_ylabel("Filter Output StDev (mV)") 
    plt.pause(0.1)
    
VdmmAvg = VdmmAvg[0:100]
Vsource = Vsource[0:100]

m,b = np.polyfit(Vsource,VdmmAvg,1)
correlation_matrix = np.corrcoef(Vsource,VdmmAvg)
p = correlation_matrix[0, 1]

ax[0].text(0.1, 0.93, "Slope:"+str(round(m,3))+"mV/mV",transform=ax[0].transAxes, fontsize=12,verticalalignment='top', bbox=props)
ax[0].text(0.1, 0.84, "Intercept:"+str(round(b,3))+"mV",transform=ax[0].transAxes, fontsize=12,verticalalignment='top', bbox=props)
ax[0].text(0.1, 0.75, "Correlation:"+str(round(p,4)),transform=ax[0].transAxes, fontsize=12,verticalalignment='top', bbox=props)
if(p>0.98):
    ax[0].text(0.1, 0.66, "Correlation>0.98?: PASS",transform=ax[0].transAxes, fontsize=12,verticalalignment='top', bbox=good)
else:
    ax[0].text(0.1, 0.66, "Correlation>0.98?: FAIL",transform=ax[0].transAxes, fontsize=12,verticalalignment='top', bbox=bad)

plt.savefig("SBCM-"+chain+"_"+year+"_CharCurve.png")
plt.show(block=True)
