import pyvisa as visa
import numpy as np
from struct import unpack
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox
from time import sleep
import epics
from matplotlib.widgets import Button
import os

props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
good = dict(boxstyle='round', facecolor='palegreen', alpha=0.5)
bad = dict(boxstyle='round', facecolor='lightcoral', alpha=0.5)

rm = visa.ResourceManager()

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
    

for j in range(0,1000):
    Vrf = 0.08 - j*0.0005
    cmd = "POW "+str(Vrf)+"V"
    source.write(cmd)
    sleep(1)
