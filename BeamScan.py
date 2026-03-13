import pyvisa as visa
from pylogix import PLC
from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from time import sleep
import numpy as np
import os
from random import randint

pattern = input("Enter Fill Pattern [90,20] : ")
if(int(pattern)!=90 and int(pattern)!=20):
    print("Bad Pattern Input... Exiting.")
    exit()
    
year = input("\nEnter Year : ")
if(int(year)<2024 or int(year)>2064):
    print("Bad Year Input... Exiting.")
    exit()
    
rm = visa.ResourceManager()

#Chain A Keithley 2100 DMM Module:
done=0
while(done==0):
    DMMsn = input('\nEnter Chain-A Keithley 2100 DMM serial number (Default=8020356, "H" for help, "Q" to quit):')
    if(DMMsn=="H"):
        print('Serial Number is at the rear of the module on a small white label')
    elif(DMMsn=="Q"):
        print('Quiting...')
        exit()
    elif(DMMsn.isdigit() or DMMsn==""):
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
    else:
        print("Bad input for Keithley 2100 DMM.  Quiting...")
        exit()
        
#Chain B Keithley 2100 DMM Module:
done=0
print("\n\n")
while(done==0):
    DMMsn = input('Enter Chain-B Keithley 2100 DMM serial number (Default=8020357, "H" for help, "Q" to quit):')
    if(DMMsn=="H"):
        print('Serial Number is at the rear of the module on a small white label')
    elif(DMMsn=="Q"):
        print('Quiting...')
        exit()
    elif(DMMsn.isdigit() or DMMsn==""):
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
    else:
        print("Bad input for Keithley 2100 DMM.  Quiting...")
        exit()
        
print("\n\n")  
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
    
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
good = dict(boxstyle='round', facecolor='palegreen', alpha=0.5)
bad = dict(boxstyle='round', facecolor='lightcoral', alpha=0.5)

xmax=0
xmin=0
oldxmin=0
oldxmax=0

fa, ax = plt.subplots(2,1,figsize=(8,10))
axclear = plt.axes([0.1, 0.92, 0.07, 0.03])
axpause = plt.axes([0.19, 0.92, 0.07, 0.03])
axsave = plt.axes([0.28, 0.92, 0.07, 0.03])

fb, bx = plt.subplots(2,1,figsize=(8,10))

clear=0
bclear = Button(axclear, 'Clear', color='lightgray', hovercolor='skyblue')
def _clear(event):
    global clear
    clear = 1
bclear.on_clicked(_clear)

save=0
bsave = Button(axsave, 'Save', color='lightgray', hovercolor='skyblue')
def _save(event):
    global save
    save = 1
bsave.on_clicked(_save)

pause=0
bpause = Button(axpause, 'Pause', color='lightgray', hovercolor='lightgray')
def _pause(event):
    global pause
    if pause==1: 
        pause=0
        bpause.color='lightgray'
        bpause.hovercolor='lightgray'
    else:
        pause=1
        bpause.color='gold'
        bpause.hovercolor='gold'
bpause.on_clicked(_pause)

def onselect_function(eclick, erelease):
    global xmin
    global xmax
    # Obtain (xmin, xmax, ymin, ymax) values
    extent = rect_selector.extents
    xmin=round(extent[0],2)
    xmax=round(extent[1],2)

IBM=[]
VFA=[]
VFB=[]
t=0
    
while True:
    if(clear==0):
        if(pause==0):
            Ereply = EPS_PLC.Read("EPS_I")
            if Ereply.Status == 'Success':
                Ibeam = Ereply.Value         
            else:
                print('EPS PLC ERROR!')
            Va = 1000.0*float(dmmA.query("MEAS:VOLT:DC?"))
            Vb = 1000.0*float(dmmB.query("MEAS:VOLT:DC?"))
            if(Ibeam>2):
                IBM.append(Ibeam)
                VFA.append(Va)
                VFB.append(Vb)
                t=t+1
        ax[0].clear()
        rect_selector = RectangleSelector(ax[0], onselect_function, drawtype='box', button=[1], interactive=True)
        ax[0].plot(VFA,IBM,'-o',color='blue')
        ax[0].grid(True)
        ax[0].set_xlabel("Chain-A Filter Output (mV)")
        ax[0].set_ylabel("EPS PLC DCCT Current (mA)",color='blue')
        ax[0].set_title("SBCM-A "+pattern+"% Fill Beam Scan")
        ax[0].tick_params(axis='y', labelcolor='blue')
        
        bx[0].clear()
        bx[0].plot(VFB,IBM,'-o',color='blue')
        bx[0].grid(True)
        bx[0].set_xlabel("Chain-B Filter Output (mV)")
        bx[0].set_ylabel("EPS PLC DCCT Current (mA)",color='blue')
        bx[0].set_title("SBCM-B "+pattern+"% Fill Beam Scan")
        bx[0].tick_params(axis='y', labelcolor='blue')
        if(xmax>xmin):
            ylim = ax[0].get_ylim()
            ax[0].bar((xmin+(xmax-xmin)/2),(ylim[1]-ylim[0]),width=(xmax-xmin),alpha=0.5,color='lightblue')
            bx[0].bar((xmin+(xmax-xmin)/2),(ylim[1]-ylim[0]),width=(xmax-xmin),alpha=0.5,color='lightblue')
        if(xmax>xmin):
            VFAroi=[]
            VFBroi=[]
            IBMAroi=[]
            IBMBroi=[]
            for i in range(0,len(VFA)):
                if(VFA[i]>=xmin and VFA[i]<=xmax):
                    VFAroi.append(VFA[i])
                    IBMAroi.append(IBM[i])
                if(VFB[i]>=xmin and VFB[i]<=xmax):
                    VFBroi.append(VFB[i])
                    IBMBroi.append(IBM[i])
            ax[1].clear()
            ax[1].plot(VFAroi,IBMAroi,'-o')
            ax[1].grid(True)
            ax[1].set_xlabel("ROI: Chain-A Filter Output (mV)")
            ax[1].set_ylabel("ROI: EPS PLC DCCT Current (mA)",color='blue')
            ax[1].tick_params(axis='y', labelcolor='blue')
            bx[1].clear()
            bx[1].plot(VFBroi,IBMBroi,'-o')
            bx[1].grid(True)
            bx[1].set_xlabel("ROI: Chain-B Filter Output (mV)")
            bx[1].set_ylabel("ROI: EPS PLC DCCT Current (mA)",color='blue')
            bx[1].tick_params(axis='y', labelcolor='blue')
            if(len(VFAroi)>2):
                m,b = np.polyfit(VFAroi,IBMAroi,1)
                correlation_matrix = np.corrcoef(VFAroi,IBMAroi)
                p = correlation_matrix[0, 1]
                ax[1].text(0.05, 0.93, "Slope:"+str(round(m,5))+"mA/mVfa",transform=ax[1].transAxes, fontsize=12,verticalalignment='top', bbox=props)
                ax[1].text(0.05, 0.84, "Intercept:"+str(round(b,4))+"mA",transform=ax[1].transAxes, fontsize=12,verticalalignment='top', bbox=props)
                ax[1].text(0.05, 0.75, "Correlation:"+str(round(p,4)),transform=ax[1].transAxes, fontsize=12,verticalalignment='top', bbox=props)
                if(p>0.98):
                    ax[1].text(0.05, 0.66, "Correlation>0.98?: PASS",transform=ax[1].transAxes, fontsize=12,verticalalignment='top', bbox=good)
                else:
                    ax[1].text(0.05, 0.66, "Correlation>0.98?: FAIL",transform=ax[1].transAxes, fontsize=12,verticalalignment='top', bbox=bad)
                IBMAfit=[]
                for v in VFAroi:
                    IBMAfit.append(m*v+b)
                ax[1].plot(VFAroi,IBMAfit)
                aV54ma = (54.0-b)/m
                ax[1].text(0.3, 0.08, "Vtoss = {VFA @ (IBM=54mA)} :"+str(round(aV54ma,1))+"mV",transform=ax[1].transAxes, fontsize=12,verticalalignment='top', bbox=props)
                
                m,b = np.polyfit(VFBroi,IBMBroi,1)
                correlation_matrix = np.corrcoef(VFBroi,IBMBroi)
                p = correlation_matrix[0, 1]
                bx[1].text(0.05, 0.93, "Slope:"+str(round(m,5))+"mA/mVfb",transform=bx[1].transAxes, fontsize=12,verticalalignment='top', bbox=props)
                bx[1].text(0.05, 0.84, "Intercept:"+str(round(b,4))+"mA",transform=bx[1].transAxes, fontsize=12,verticalalignment='top', bbox=props)
                bx[1].text(0.05, 0.75, "Correlation:"+str(round(p,4)),transform=bx[1].transAxes, fontsize=12,verticalalignment='top', bbox=props)
                if(p>0.98):
                    bx[1].text(0.05, 0.66, "Correlation>0.98?: PASS",transform=bx[1].transAxes, fontsize=12,verticalalignment='top', bbox=good)
                else:
                    bx[1].text(0.05, 0.66, "Correlation>0.98?: FAIL",transform=bx[1].transAxes, fontsize=12,verticalalignment='top', bbox=bad)
                IBMBfit=[]
                for v in VFBroi:
                    IBMBfit.append(m*v+b)
                bx[1].plot(VFBroi,IBMBfit)
                bV54ma = (54.0-b)/m
                bx[1].text(0.3, 0.08, "Vtoss = {VFB @ (IBM=54mA)} :"+str(round(bV54ma,1))+"mV",transform=bx[1].transAxes, fontsize=12,verticalalignment='top', bbox=props)
        plt.pause(0.1)
    else:
        VFA=[]
        VFB=[]
        IBM=[]
        t=0
        xmin=0
        xmax=0
        clear=0
    if(save==1):
        save=0
        fname = "SBCM_BeamScanFull_"+pattern+"pctFill_"+year+".txt"
        if(os.path.exists(fname)):
            resp = input("File "+fname+" exists.  Overwrite? (Y or N):")
        else:
            resp = "F"
        if(resp=="Y" or resp=="F"):
            print('Saving:   ',fname)
            fdat = open(fname,"w")
            for i in range(0,len(VFA)):
                data = str(round(VFA[i],3))+','+str(round(VFB[i],3))+','+str(round(IBM[i],3))+'\n'
                fdat.write(data)
            fdat.close()
            
        fnameA = "SBCM_BeamScanROIA_"+pattern+"pctFill_"+year+".txt"
        fnameB = "SBCM_BeamScanROIB_"+pattern+"pctFill_"+year+".txt"
        if(os.path.exists(fnameA)):
            resp = input("File "+fnameA+" exists.  Overwrite? (Y or N):")
        else:
            resp = "F"
        if(resp=="Y" or resp=="F"):
            print('Saving:   ',fnameA)
            fdat = open(fnameA,"w")
            for i in range(0,len(VFAroi)):
                data = str(round(VFAroi[i],3))+','+str(round(IBMAroi[i],3))+'\n'
                fdat.write(data)
            fdat.close() 
            
        if(os.path.exists(fnameB)):
            resp = input("File "+fnameB+" exists.  Overwrite? (Y or N):")
        else:
            resp = "F"
        if(resp=="Y" or resp=="F"):
            print('Saving:   ',fnameB)
            fdat = open(fnameB,"w")
            for i in range(0,len(VFBroi)):
                data = str(round(VFBroi[i],3))+','+str(round(IBMBroi[i],3))+'\n'
                fdat.write(data)
            fdat.close() 
            
        fa.savefig("SBCM_BeamScanA_"+pattern+"pctFill_"+year+".png")
        fb.savefig("SBCM_BeamScanB_"+pattern+"pctFill_"+year+".png")
    sleep(0.33)
    
    # Display graph
plt.show()
