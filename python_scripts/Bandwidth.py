import pyvisa as visa
import numpy as np
from struct import unpack
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox
from time import sleep
import time
import epics
from matplotlib.widgets import Button
import os
import csv
from datetime import datetime

def list_available_resources():
    """List all available VISA resources on the system."""
    rm = visa.ResourceManager()
    resources = rm.list_resources()
    print("Available VISA resources:")
    for res in resources:
        print(f"  - {res}")
    return resources

def connect_to_resource(rm, resource_addr, max_retries=3, description="Device"):
    """Connect to a VISA resource with exponential backoff retry logic.
    
    Args:
        rm: VISA ResourceManager
        resource_addr: VISA resource address string
        max_retries: Maximum number of connection attempts
        description: Device name for logging
    
    Returns:
        instrument object if successful, None if all retries fail
    """
    for attempt in range(max_retries):
        try:
            print(f"\n[{description}] Attempt {attempt + 1}/{max_retries} to connect...")
            instr = rm.open_resource(resource_addr, open_timeout=5000)
            instr.timeout = 10000
            instr.write_termination = '\n'
            instr.read_termination = '\n'
            sleep(0.5)  # Let instrument settle after connection
            
            idn = instr.query("*IDN?")
            print(f"[{description}] Connected successfully! IDN: {idn.strip()}")
            instr.clear()
            return instr
        
        except Exception as e:
            print(f"[{description}] Connection failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # exponential backoff: 1s, 2s, 4s
                print(f"[{description}] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"[{description}] All {max_retries} attempts failed.")
                return None

def initialize_pulse_generator(pulseGen):
    # initialize the pulse generator
    sleep(0.3)  # LET THE INSTRUMENT SETTLE
    pulseGen.write("OUTPUT1 OFF")
    pulseGen.write("SOURCE:AM1:STATE 0")
    pulseGen.write("SOURCE:LFOutput1:STATE 0")

    pulseGen.write("UNIT:POW DBM")
    pulseGen.write("SOURCE:POW:LEVEL:IMM:AMPL 0")  # 0 dBm
    pulseGen.write("SOURCE:FREQUENCY:CW 499680000")  # 499.68 MHz
    pulseGen.write("SOURCE:FREQUENCY:MODE CW")
    pulseGen.write("SOURCE:FREQUENCY:OFFSET 0")
    pulseGen.write("SOURCE:LFOutput1:SHAPE SINE")
    pulseGen.write("SOURCE:LFOutput1:FREQUENCY 1")  # 1 Hz
    pulseGen.write("SOURCE:LFOutput1:VOLTAGE 2")  # 2 V amplitude
    # pulseGen.write("SOURCE:LFOutput1:STATE 1")

    pulseGen.write("SOURCE:AM1:SOURCE LF1")
    pulseGen.write("SOURCE:AM1:DEPTH 50")
    pulseGen.write("SOURCE:AM1:STATE 1")
    pulseGen.write("OUTPUT1 ON")
    
    print("Pulse Generator configured and started.")

def initialize_oscilloscope(scope):
    sleep(0.3)

    scope.write("ACQUIRE:STATE RUN")
    scope.write("ACQUIRE:MODE SAMPLE")

    scope.write("DATA:SOURCE CH1")

    scope.write("CH1:SCALE 1")
    scope.write("CH1:POSITION -5")

    scope.write("HORIZONTAL:SCALE 200e-3")

    scope.write("MEASUREMENT:DELETEALL")

    scope.write("MEASUREMENT:MEAS1:TYPE PK2PK")
    scope.write("MEASUREMENT:MEAS1:SOURCE CH1")
    scope.write("MEASUREMENT:MEAS1:STATE ON")

    sleep(1)  # let measurements settle


def save_data_and_plot(frequencies, pk2pk_values, chain,year):
    """Save measurement data to CSV and create a plot with logarithmic frequency axis."""

    # Convert to NumPy arrays for math
    frequencies = np.array(frequencies, dtype=float)
    pk2pk_values = np.array(pk2pk_values, dtype=float)

    # Safety check
    if pk2pk_values[0] == 0:
        raise ValueError("First pk2pk value is zero — cannot normalize")

   # Save data to TXT (tab-delimited)
    txt_filename = f"SBCM-{chain}_{year}_BWScan.txt"
    with open(txt_filename, 'w') as txtfile:
        for freq, pk2pk in zip(frequencies, pk2pk_values):
            txtfile.write(f"{freq},{pk2pk:.6f}\n")

    print(f"[SAVE] Data saved to {txt_filename}")

    # Normalize to first point and convert to dB
    normalized_db = 20 * np.log10(pk2pk_values / pk2pk_values[0])

    # Create and save plot
    plt.figure(figsize=(10, 6))
    plt.plot(frequencies, normalized_db, 'b-o', linewidth=2, markersize=6)
    plt.xlabel("Frequency (Hz)", fontsize=12)
    plt.ylabel("Amplitude (dB)", fontsize=12)
    plt.title(f"SBCM-{chain} Bandwidth Measurement - AM Modulation",
              fontsize=14, fontweight='bold')
    plt.grid(True, which='both', alpha=0.3)
    plt.tight_layout()

    plot_filename = f"SBCM-{chain}_Bandwidth_Plot.png"
    plt.savefig(plot_filename, dpi=150)
    plt.show(block=True)
    print(f"[SAVE] Plot saved to {plot_filename}")

    plt.close()





def main(): 
    print("\n=== Bandwidth Measurement System ===")
    print("Discovering available VISA resources...\n")
    
    rm = visa.ResourceManager()
    list_available_resources()
    
    # Connect to oscilloscope with retry logic
    scope = connect_to_resource(
        rm,
        "TCPIP0::10.0.128.110::inst0::INSTR",
        max_retries=3,
        description="Oscilloscope (TEKMS064B)"
    )

    # Connect to pulse generator with retry logic
    pulseGen = connect_to_resource(
        rm,
        "TCPIP0::10.0.128.183::inst0::INSTR",
        max_retries=3,
        description="Pulse Generator (SMB100B)"
    )
    
    # Verify both connections succeeded
    if pulseGen is None:
        print("\n[ERROR] Failed to connect to Pulse Generator. Exiting.")
        rm.close()
        return
    
    if scope is None:
        print("\n[ERROR] Failed to connect to Oscilloscope. Exiting.")
        pulseGen.close()
        rm.close()
        return
    
    print("\n[SUCCESS] Both instruments connected. Initializing...\n")
    initialize_pulse_generator(pulseGen)
    initialize_oscilloscope(scope)

    chain = input("Enter SBCM Chain (A/B): ").strip().upper()

    year = input("\n\nEnter the Year:")
    if(int(year)<2024 or int(year)>2064):
        print("Bad Input... Exiting.")
        exit()

    freq = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25
            ,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,
            60,70,80,90,100,110,120,130,140,150,160,170,180,190,200,210,220,230,240,250,
            260,270,280,290,300]
    
    # Data collection lists
    frequencies = []
    pk2pk_values = []
    
    print("\n[MEASUREMENT] Starting frequency sweep...\n")
    for fhz in freq:
        try:
            pulseGen.write(f"SOURCE:LFOutput1:FREQUENCY {fhz}")
            pulseGen.query("*OPC?")
            sleep(5)

            scope.query("*OPC?")
            val = float(scope.query("MEASUREMENT:MEAS1:VALUE?"))

            print(f"Pk2Pk @ {fhz} Hz: {val:.3f} V")
            
            frequencies.append(fhz)
            pk2pk_values.append(val)

        except (visa.VisaIOError, AttributeError, ValueError) as e:
            print(f"Failed at frequency {fhz} Hz: {e}")
            break
    
    # Save data and plot
    if frequencies and pk2pk_values:
        print(f"\n[DATA] Collected {len(frequencies)} measurements")
        save_data_and_plot(frequencies, pk2pk_values,chain,year)
    else:
        print("\n[WARNING] No data collected.")
    
    # Cleanup
    print("\nClosing instrument connections...")
    try:
        pulseGen.close()
    except:
        pass
    try:
        scope.close()
    except:
        pass
    rm.close()
    print("Done.")


if __name__ == "__main__":
    main()