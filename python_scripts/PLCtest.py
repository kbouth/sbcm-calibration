from pylogix import PLC

# Create PLC objects for SBCM chain A and B and DCCT EPS chassis
SBCM_A_PLC = PLC()
SBCM_B_PLC = PLC()
EPS_PLC = PLC()

# Set the IP address of each PLC
SBCM_A_PLC.IPAddress = '10.0.128.84'
SBCM_B_PLC.IPAddress = '10.0.128.85'
EPS_PLC.IPAddress = '10.0.128.49'

try:
    # Read a tag from the PLC
    tag_name = 'WDT_Status'  # Replace with the name of the tag you want to read
    Areply = SBCM_A_PLC.Read(tag_name)
    Breply = SBCM_B_PLC.Read(tag_name)
    Ereply = EPS_PLC.Read("EPS_I")
    # Check if the reads were successful
    if Areply.Status == 'Success':
        print(f'Tag: {tag_name}, Value: {Areply.Value}')
    else:
        print(f'Failed to read tag: {tag_name}, Status: {Areply.Status}')
    if Breply.Status == 'Success':
        print(f'Tag: {tag_name}, Value: {Breply.Value}')
    else:
        print(f'Failed to read tag: {tag_name}, Status: {Breply.Status}')
    if Ereply.Status == 'Success':
        print(Ereply.Value)
    else:
        print(f'Failed to read tag. Status: {Breply.Status}')
except Exception as e:
    print(f'An error occurred: {e}')
finally:
    # Close the connection to the PLC
    SBCM_A_PLC.Close()
    SBCM_B_PLC.Close()
    EPS_PLC.Close()
