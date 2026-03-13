import pyvisa as visa
from pylogix import PLC
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
    
direction = input("\nBeam Rising or Falling [R,F] : ")
if(direction!='R' and direction!='F'):
    print("Bad Beam Direction... Exiting.")
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

print("\n\n")  
#SBCM-A CompactLogix L32E PLC in Cell 4:
SBCMA_PLC = PLC()
# Set the IP address of SBCM-A PLC
SBCMA_PLC.IPAddress = '10.0.128.84'
sleep(1)
Ereply = SBCMA_PLC.Read("WDT_Status")
if Ereply.Status == 'Success':
    print('SBCM-A PLC Found!')
else:
    print('SBCM-A PLC ERROR! Quiting...')
    exit()
    
print("\n\n")  
#SBCM-B CompactLogix L32E PLC in Cell 4:
SBCMB_PLC = PLC()
# Set the IP address of SBCM-B PLC
SBCMB_PLC.IPAddress = '10.0.128.85'
sleep(1)
Ereply = SBCMB_PLC.Read("WDT_Status")
if Ereply.Status == 'Success':
    print('SBCM-B PLC Found!')
else:
    print('SBCM-B PLC ERROR! Quiting...')
    exit()
    
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
good = dict(boxstyle='round', facecolor='palegreen', alpha=0.5)
bad = dict(boxstyle='round', facecolor='lightcoral', alpha=0.5)

fa, ax = plt.subplots(2,1,figsize=(8,10))
ax02 = ax[0].twinx()
ax12 = ax[1].twinx()
axclear = plt.axes([0.1, 0.92, 0.07, 0.03])
axpause = plt.axes([0.19, 0.92, 0.07, 0.03])
axsave = plt.axes([0.28, 0.92, 0.07, 0.03])

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

reply = SBCMA_PLC.Read("WDT_Status")
if reply.Status == 'Success':
    oldwdtA = reply.Value
else:
    print("SBCM-A PLC WDT Error")
    exit()
reply = SBCMA_PLC.Read("COMP_Status")
if reply.Status == 'Success':
    oldcompA = reply.Value
else:
    print("SBCM-A PLC COMP Error")
    exit()
reply = SBCMA_PLC.Read("RELAY_Status")
if reply.Status == 'Success':
    oldrelayA = reply.Value
else:
    print("SBCM-A PLC RELAY Error")
    exit()

reply = SBCMB_PLC.Read("WDT_Status")
if reply.Status == 'Success':
    oldwdtB = reply.Value
else:
    print("SBCM-B PLC WDT Error")
    exit()
reply = SBCMB_PLC.Read("COMP_Status")
if reply.Status == 'Success':
    oldcompB = reply.Value
else:
    print("SBCM-B PLC COMP Error")
    exit()
reply = SBCMB_PLC.Read("RELAY_Status")
if reply.Status == 'Success':
    oldrelayB = reply.Value
else:
    print("SBCM-B PLC RELAY Error")
    exit()

IBM=[]
VFA=[]
VFB=[]
WDTA=[]
COMA=[]
RELA=[]
WDTB=[]
COMB=[]
RELB=[]
TESTB = [0,0,0,0,0,0]
TESTA = [0,0,0,0,0,0]
t=0

while True:
    if(clear==0):
        if(pause==0):
            Va = 1000.0*float(dmmA.query("MEAS:VOLT:DC?"))
            VFA.append(Va)
            Vb = 1000.0*float(dmmB.query("MEAS:VOLT:DC?"))
            VFB.append(Vb)
            Ereply = EPS_PLC.Read("EPS_I")
            if Ereply.Status == 'Success':
                Ibeam = Ereply.Value         
            else:
                print('EPS PLC ERROR!')
            IBM.append(Ibeam)
            reply = SBCMA_PLC.Read("WDT_Status")
            if reply.Status == 'Success':
                wdtA = reply.Value
                WDTA.append(wdtA)
            else:
                print("SBCM-A PLC WDT Error")
            reply = SBCMA_PLC.Read("COMP_Status")
            if reply.Status == 'Success':
                compA = reply.Value
                COMA.append(2*compA)
            else:
                print("SBCM-A PLC COMP Error")
            reply = SBCMA_PLC.Read("RELAY_Status")
            if reply.Status == 'Success':
                relayA = reply.Value
                RELA.append(3*relayA)
            else:
                print("SBCM-A PLC RELAY Error")
                
            reply = SBCMB_PLC.Read("WDT_Status")
            if reply.Status == 'Success':
                wdtB = reply.Value
                WDTB.append(wdtB)
            else:
                print("SBCM-B PLC WDT Error")
            reply = SBCMB_PLC.Read("COMP_Status")
            if reply.Status == 'Success':
                compB = reply.Value
                COMB.append(2*compB)
            else:
                print("SBCM-B PLC COMP Error")
            reply = SBCMB_PLC.Read("RELAY_Status")
            if reply.Status == 'Success':
                relayB = reply.Value
                RELB.append(3*relayB)
            else:
                print("SBCM-B PLC RELAY Error")
                
        ax[0].clear()
        ax02.clear()
        ax[0].plot(IBM,'-o',color='blue')
        ax[0].grid(True)
        ax[0].set_xlabel("Chain-A Filter Output (mV)")
        ax[0].set_ylabel("EPS PLC DCCT Current (mA)",color='blue')
        ax[0].set_title("SBCM-A "+pattern+"% Fill Functional Test")
        ax[0].tick_params(axis='y', labelcolor='blue')
        ax02.plot(WDTA,'-o',color='red')
        ax02.plot(COMA,'-o',color='green')
        ax02.plot(RELA,'-o',color='black')
        ax02.set_ylabel("SBCM-A Status Bits",color='black')
        ax02.set_yticks([0,1,2,3,4,5])
        ax02.set_yticklabels(['OFF','WDT','COM','REL','',''])
        if(oldwdtA!=wdtA):
            if(wdtA==1):
                TESTA[0] = 1
                IwdtAon = Ibeam
                VwdtAon = Va 
            else:
                TESTA[3] = 1
                IwdtAoff = Ibeam
                VwdtAoff = Va 
            oldwdtA = wdtA            
        if(oldcompA!=compA):
            if(compA==1):
                TESTA[1] = 1
                IcompAon = Ibeam
                VcompAon = Va 
            else:
                TESTA[4] = 1
                IcompAoff = Ibeam
                VcompAoff = Va
            oldcompA = compA
        if(oldrelayA!=relayA):
            if(relayA==1):
                TESTA[2] = 1
                IrelayAon = Ibeam
                VrelayAon = Va 
            else:
                TESTA[5] = 1
                IrelayAoff = Ibeam
                VrelayAoff = Va
            oldrelayA = relayA
        if(TESTA[0]==1):
            line = "WDT ON: Beam="+str(round(IwdtAon,2))+"mA  SBCM="+str(round(VwdtAon,1))+"mV"
            ax02.text(0.05, 0.93,line,transform=ax02.transAxes,fontsize=10,verticalalignment='top', bbox=props)
        if(TESTA[1]==1):
            line = "COMP ON: Beam="+str(round(IcompAon,2))+"mA  SBCM="+str(round(VcompAon,1))+"mV"
            ax02.text(0.05, 0.84,line,transform=ax02.transAxes,fontsize=10,verticalalignment='top', bbox=props)
        if(TESTA[2]==1):
            line = "RELAY ON: Beam="+str(round(IrelayAon,2))+"mA  SBCM="+str(round(VrelayAon,1))+"mV"
            ax02.text(0.05, 0.75,line,transform=ax02.transAxes,fontsize=10,verticalalignment='top', bbox=props)
        if(TESTA[3]==1):
            line = "WDT OFF: Beam="+str(round(IwdtAoff,2))+"mA  SBCM="+str(round(VwdtAoff,1))+"mV"
            ax02.text(0.45, 0.93,line,transform=ax02.transAxes,fontsize=10,verticalalignment='top', bbox=props)
        if(TESTA[4]==1):
            line = "COMP OFF: Beam="+str(round(IcompAoff,2))+"mA  SBCM="+str(round(VcompAoff,1))+"mV"
            ax02.text(0.45, 0.85,line,transform=ax02.transAxes,fontsize=10,verticalalignment='top', bbox=props)
        if(TESTA[5]==1):
            line = "RELAY OFF: Beam="+str(round(IrelayAoff,2))+"mA  SBCM="+str(round(VrelayAoff,1))+"mV"
            ax02.text(0.45, 0.77,line,transform=ax02.transAxes,fontsize=10,verticalalignment='top', bbox=props)        
        ax[1].clear()
        ax12.clear()
        ax[1].plot(IBM,'-o',color='blue')
        ax[1].grid(True)
        ax[1].set_xlabel("Chain-B Filter Output (mV)")
        ax[1].set_ylabel("EPS PLC DCCT Current (mA)",color='blue')
        ax[1].set_title("SBCM-B "+pattern+"% Fill Functional Test")
        ax[1].tick_params(axis='y', labelcolor='blue')
        ax12.plot(WDTB,'-o',color='red')
        ax12.plot(COMB,'-o',color='green')
        ax12.plot(RELB,'-o',color='black')
        ax12.set_ylabel("SBCM-B Status Bits",color='black')
        ax12.set_yticks([0,1,2,3,4,5])
        ax12.set_yticklabels(['OFF','WDT','COM','REL','',''])
        if(oldwdtB!=wdtB):
            if(wdtB==1):
                TESTB[0] = 1
                IwdtBon = Ibeam
                VwdtBon = Vb
            else:
                TESTB[3] = 1
                IwdtBoff = Ibeam
                VwdtBoff = Vb 
            oldwdtB = wdtB            
        if(oldcompB!=compB):
            if(compB==1):
                TESTB[1] = 1
                IcompBon = Ibeam
                VcompBon = Vb 
            else:
                TESTB[4] = 1
                IcompBoff = Ibeam
                VcompBoff = Vb
            oldcompB = compB
        if(oldrelayB!=relayB):
            if(relayB==1):
                TESTB[2] = 1
                IrelayBon = Ibeam
                VrelayBon = Vb 
            else:
                TESTB[5] = 1
                IrelayBoff = Ibeam
                VrelayBoff = Vb
            oldrelayB = relayB
        if(TESTB[0]==1):
            line = "WDT ON: Beam="+str(round(IwdtBon,2))+"mA  SBCM="+str(round(VwdtBon,1))+"mV"
            ax12.text(0.05, 0.93,line,transform=ax12.transAxes,fontsize=10,verticalalignment='top', bbox=props)
        if(TESTB[1]==1):
            line = "COMP ON: Beam="+str(round(IcompBon,2))+"mA  SBCM="+str(round(VcompBon,1))+"mV"
            ax12.text(0.05, 0.84,line,transform=ax12.transAxes,fontsize=10,verticalalignment='top', bbox=props)
        if(TESTB[2]==1):
            line = "RELAY ON: Beam="+str(round(IrelayBon,2))+"mA  SBCM="+str(round(VrelayBon,1))+"mV"
            ax12.text(0.05, 0.75,line,transform=ax12.transAxes,fontsize=10,verticalalignment='top', bbox=props)
        if(TESTB[3]==1):
            line = "WDT OFF: Beam="+str(round(IwdtBoff,2))+"mA  SBCM="+str(round(VwdtBoff,1))+"mV"
            ax12.text(0.45, 0.93,line,transform=ax12.transAxes,fontsize=10,verticalalignment='top', bbox=props)
        if(TESTB[4]==1):
            line = "COMP OFF: Beam="+str(round(IcompBoff,2))+"mA  SBCM="+str(round(VcompBoff,1))+"mV"
            ax12.text(0.45, 0.85,line,transform=ax12.transAxes,fontsize=10,verticalalignment='top', bbox=props)
        if(TESTB[5]==1):
            line = "RELAY OFF: Beam="+str(round(IrelayBoff,2))+"mA  SBCM="+str(round(VrelayBoff,1))+"mV"
            ax12.text(0.45, 0.77,line,transform=ax12.transAxes,fontsize=10,verticalalignment='top', bbox=props)
        plt.pause(0.1)
    else:
        VFA=[]
        VFB=[]
        IBM=[]
        WDTA=[]
        COMA=[]
        RELA=[]
        WDTB=[]
        COMB=[]
        RELB=[]
        TESTB = [0,0,0,0,0,0]
        TESTA = [0,0,0,0,0,0]
        clear=0
    if(save==1):
        save=0
        if(direction=="R"):
            fname = "SBCM_FunctionalTestRising_"+pattern+"pctFill_"+year+".txt"
        else:
            fname = "SBCM_FunctionalTestFalling_"+pattern+"pctFill_"+year+".txt"
        if(os.path.exists(fname)):
            resp = input("File "+fname+" exists.  Overwrite? (Y or N):")
        else:
            resp = "F"
        if(resp=="Y" or resp=="F"):
            fdat = open(fname,"w")
            print("Saving: ",fname)
            for i in range(0,len(VFA)):
                dat = str(round(IBM[i],3))+','+str(round(VFA[i],3))+','+str(round(VFB[i],3))+','+str(WDTA[i])+','+str(COMA[i])+','+str(RELA[i])+','+str(WDTB[i])+','+str(COMB[i])+','+str(RELB[i])+"\n"
                fdat.write(dat)    
            fdat.close()
            fa.savefig("SBCM_FunctionalTest_"+pattern+"pctFill_"+year+".png")
    sleep(0.33)
    
    # Display graph
plt.show()
