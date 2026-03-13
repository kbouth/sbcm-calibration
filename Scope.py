import pyvisa as visa
import numpy as np
from struct import unpack
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox
from time import sleep
import epics
from matplotlib.widgets import Button

props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

rm = visa.ResourceManager()
dev = 'TCPIP0::10.0.128.66::4000::SOCKET'
scope = rm.open_resource(dev)
print('\nScope TCPIP Open Successful!')
scope.read_termination = '\n'
scope.write_termination = '\n'
response = scope.query('*IDN?')
print(response[18:24])
serial_number = int(response[18:24])
if(serial_number != 27138):
    print('Tektronix MSO64B Scope NOT FOUND...exiting!')
    exit()
else:
    print('Tektronix MSO64B Scope FOUND.')
    
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
   
dev='USB0::0x05E6::0x2100::1182957::INSTR'   
dmm1 = rm.open_resource(dev)
print('\nDMM1 USB Open Successful!')
#dmm1.read_termination = '\n'
#dmm1.write_termination = '\n'
response = dmm1.query('*IDN?')
model1_number = int(response[32:36])
if(model1_number != 2100):
    print('Keithley 2100 DMM NOT FOUND...exiting!')
    exit()
else:
    print('Keithley 2100 DMM FOUND.')
    dmm1.write(':SENS:FUNC "VOLT:DC"')

#Set up the scope:
#scope.write('ACQ:MODE HIRES')
#scope.write('HOR:RECO 1000')
scope.write('TRIGGER:A:MODE NORM')
scope.write('TRIGGER:A:TYPE EDGE')
scope.write('TRIGGER:A:EDGE:SOURCE CH1')
scope.write('TRIGGER:A:EDGE:SLOPE FALL')
scope.write('TRIGGER:A:EDGE:COUPLING DC')
scope.write('HORIZONTAL:MODE MANUAL')
scope.write('HORIZONTAL:MODE:SAMPLERATE 6.25E8')
scope.write('HORIZONTAL:SCALE 2e-5')
scope.write('HORIZONTAL:POS 20')
scope.write('*WAI')
scope.write('CH1:SCALE 0.1')
scope.write('CH1:POS 3.0')

Qtest = []
Itest = []

plt.ion()
fq,axq = plt.subplots(2,1,figsize=(7,7.5))

while(True):
    scope.write('ACQUIRE:STOPAFTER SEQUENCE')
    scope.write('ACQUIRE:STATE 1')
    scope.write('*WAI')

    good=0
    while(good==0):
        
        try:
            scope.write('DATA:SOU CH1')
            scope.write('DATA:START 0')
            scope.write('DATA:STOP 50000')
            scope.write('DATA:WIDTH 2')
            scope.write('DATA:ENC RPB')
            scope.write('WFMOUTPRE:BYT_NR 2')
            ymult1 = float(scope.query('WFMPRE:YMULT?'))
            yzero1 = float(scope.query('WFMPRE:YZERO?'))
            yoff1 = float(scope.query('WFMPRE:YOFF?'))
            xincr1 = float(scope.query('WFMPRE:XINCR?'))
            scope.write('CURVE?')
            data1 = scope.read_bytes(50000)
            print(ymult1,yzero1,yoff1,xincr1)    
            good = 1
        except:
            good = 0
        
    headerlen = 2 + int(data1[1])
    header = data1[:headerlen]
    ADC_wave1 = data1[headerlen:-1]
    if(len(ADC_wave1)%2==1):
        ADC_wave1 = ADC_wave1[0:len(ADC_wave1)-1]
    CH1 = []
    Tq = []
    for i in range(0,len(ADC_wave1),2):
        CH1.append(256*ADC_wave1[i]+ADC_wave1[i+1])
        Tq.append(100000.0*i*xincr1)
    CH1offset = -32767+(65536)*(yzero1)
    print(CH1offset)
    CH1 = np.add(CH1,CH1offset)
    Vq = np.multiply(CH1,1.0)  #ymult1)

    axq[0].clear()
    axq[0].plot(Tq,Vq)
    axq[0].grid(color='lightgray',linestyle='-',linewidth=1)
    axq[0].set_xlabel("Time (nSec)")
    axq[0].set_ylabel("Voltage") 

    plt.pause(0.1)

    voltage = dmm1.query(':READ?')
    print(f"Measured Voltage: {voltage} V")
