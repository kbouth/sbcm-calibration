from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from time import sleep
import numpy as np
from random import randint

props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
good = dict(boxstyle='round', facecolor='palegreen', alpha=0.5)
bad = dict(boxstyle='round', facecolor='lightcoral', alpha=0.5)

xmax=0
xmin=0
oldxmin=0
oldxmax=0

fig, ax = plt.subplots(2,1,figsize=(10,10))

axclear = plt.axes([0.1, 0.9, 0.07, 0.05])
axpause = plt.axes([0.2, 0.9, 0.07, 0.05])

clear=0
bclear = Button(axclear, 'Clear', color='lightgray', hovercolor='skyblue')
def _clear(event):
    global clear
    clear = 1
bclear.on_clicked(_clear)

pause=0
bpause = Button(axpause, 'Pause', color='lightgray', hovercolor='skyblue')
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

TM=[]
IBM=[]
VFA=[]
VFB=[]
t=0
while True:
    if(clear==0):
        if(pause==0):
            Ibeam = 300-5*t+randint(0,50)/10.0
            if(Ibeam>2):
                IBM.append(Ibeam)
                VFA.append(6300-106*t+randint(0,200)/10.0)
                VFB.append(6000-100*t+randint(0,200)/10.0)
                TM.append(3*t/11)
                t=t+1
        ax[0].clear()
        rect_selector = RectangleSelector(ax[0], onselect_function, drawtype='box', button=[1], interactive=True)
        ax[0].plot(VFA,IBM,'-o',color='blue')
        ax[0].grid(True)
        ax[0].set_xlabel("Chain-A Filter Output (mV)")
        ax[0].set_ylabel("EPS PLC DCCT Current (mA)",color='blue')
        ax[0].set_title("SBCM-A Beam Curve")
        ax[0].tick_params(axis='y', labelcolor='blue')
        if(xmax>xmin):
            ylim = ax[0].get_ylim()
            ax[0].bar((xmin+(xmax-xmin)/2),(ylim[1]-ylim[0]),width=(xmax-xmin),alpha=0.5,color='lightblue')
        if(xmax>xmin):
            VFAroi=[]
            IBMroi=[]
            for i in range(0,len(VFA)):
                if(VFA[i]>=xmin and VFA[i]<=xmax):
                    VFAroi.append(VFA[i])
                    IBMroi.append(IBM[i])
            ax[1].clear()
            ax[1].plot(VFAroi,IBMroi,'-o')
            ax[1].grid(True)
            ax[1].set_xlabel("ROI: Chain-A Filter Output (mV)")
            ax[1].set_ylabel("ROI: EPS PLC DCCT Current (mA)",color='blue')
            ax[1].tick_params(axis='y', labelcolor='blue')
            if(len(VFAroi)>2):
                m,b = np.polyfit(VFAroi,IBMroi,1)
                print(m,b)
                correlation_matrix = np.corrcoef(VFAroi,IBMroi)
                p = correlation_matrix[0, 1]
                ax[1].text(0.1, 0.93, "Slope:"+str(round(m,5))+"mA/mVfa",transform=ax[1].transAxes, fontsize=12,verticalalignment='top', bbox=props)
                ax[1].text(0.1, 0.84, "Intercept:"+str(round(b,4))+"mA",transform=ax[1].transAxes, fontsize=12,verticalalignment='top', bbox=props)
                ax[1].text(0.1, 0.75, "Correlation:"+str(round(p,4)),transform=ax[1].transAxes, fontsize=12,verticalalignment='top', bbox=props)
                if(p>0.98):
                    ax[1].text(0.1, 0.66, "Correlation>0.98?: PASS",transform=ax[1].transAxes, fontsize=12,verticalalignment='top', bbox=good)
                else:
                    ax[1].text(0.1, 0.66, "Correlation>0.98?: FAIL",transform=ax[1].transAxes, fontsize=12,verticalalignment='top', bbox=bad)
        plt.pause(0.1)
    else:
        X=[]
        Y=[]
        t=0
        xmin=0
        xmax=0
        clear=0
      
    sleep(0.33)
    
    # Display graph
plt.show()
