#!/usr/bin/env python
"""
Continuously reads and displays CDI data with decoding
Shows RPM, CDI Voltage, and Ignition Timing
"""

import serial
from time import sleep
import struct
from datetime import datetime
import sys
import argparse

# message that we have to send every time to receive a response from a CDI
MESSAGE_TO_CDI = [0x01, 0xAB, 0xAC, 0xA1]

def connect_to_cdi(port_name='COM5'):
  """Connect to the CDI module
  
  Args:
    port_name: Serial port name (e.g., 'COM5' on Windows, '/dev/ttyUSB0' on Linux)
  """
  print(f"Connecting to CDI on {port_name}...")
  
  # Open the serial port
  port = serial.Serial(
    port=port_name,
    baudrate=19200, # CDI uses 19200 baud
    timeout=1.0
  )
  
  # IMPORTANT: Set DTR and RTS high (required for CDI)
  port.dtr = True
  port.rts = True
  
  print("Port opened, sending initialization...")
  
  # Send initialization sequence twice (CDI requires this)
  for round in [1, 2]:
    print(f" Sending init #{round}...", end="")
    for byte in MESSAGE_TO_CDI:
      port.write(bytes([byte]))
    
    # Wait for response
    sleep(0.1)
    
    # Check if CDI responded
    if port.in_waiting > 0:
      response = port.read(port.in_waiting)
      print(f" Got response: {len(response)} bytes")
    else:
      print(" No response")
  
  return port

def decode_cdi_packet(data):
  """
  Decode CDI packet to get RPM, CDI voltage, and Timing
  This is a simplified decoder for beginners
  """
  # Check if packet is valid (starts with 0x03, ends with 0xA9)
  if len(data) != 22 or data[0] != 0x03 or data[21] != 0xA9:
    return None
  
  # Extract RPM (bytes 1-2, big-endian format)
  # Big-endian means most significant byte first
  rpm = (data[1] << 8) | data[2]  # Combine two bytes into one number
  
  # Extract CDI Voltage (byte 7)
  # Stored as decivolts (e.g., 115 = 11.5V)
  cdi_voltage_decivolts = data[7]
  cdi_voltage = cdi_voltage_decivolts / 10.0
  
  
  timing_angle = data[13] / 2

  return {
    'rpm': rpm,
    'cdi_voltage': cdi_voltage,
    'timing byte': timing_angle
  }

def connect_and_read_data(port_name):

  try:
    # Connect to CDI
    port = connect_to_cdi(port_name)
    print("\n✓ Connected! Starting monitor...\n")
    
    pretty_header()
    
    while True:
      for byte in MESSAGE_TO_CDI:
        port.write(bytes([byte]))
      
      # Wait a bit
      sleep(0.1)
      
      # Read response if available
      if port.in_waiting >= 22: # CDI sends 22-byte packets
        data = port.read(22)
        
        pretty_print(data)
        
      
      # Wait before next request
      sleep(0.1)
      
  except KeyboardInterrupt:
    print("\n\nStopped by user")
    return 1

  except serial.SerialException as e:
    print(f"\nConnection lost, retrying. Error message:\n{e}")
    sleep(1)

  except Exception as e:
    print(f"\nError: {e}")
    sleep(1)
    
  finally:
    # Close the port
    if 'port' in locals():
      port.close()
      print("Port closed")


###
#
# MAIN
#
###

def main(port_name='COM5'):
  """Main program
  
  Args:
    port_name: Serial port name to connect to
  """
  print("="*70)
  print("CDI Monitor with Decoding")
  print("="*70)
  print("\nThis program reads data from your CDI and shows:")
  print("  • Engine RPM")
  print("  • CDI Voltage")
  print("  • Ignition Timing")
  print("\nPress Ctrl+C to stop\n")
  
  while True:
    try:
      # In case user stops the program in the read loop of a connect_and_read_data function - let's just break the loop here as well and finish operation.
      if (connect_and_read_data(port_name)):
        break
    except serial.SerialException as e:
      print(f"\nConnection lost, retrying (main loop). Error message:\n{e}")
      sleep(1)
    # This exception happens when tuner usb cable isn't connected and user cancels the program.
    except KeyboardInterrupt:
      print("\n\nStopped by user (main loop)")
      break


###
#
# Testing
#
###

def test():
  """
  Test how results are being displayed
  """

  test_data = [
    "030000000000007210040008000a020103020201a6a9",
    "030300000000007210040008000a020103020201a9a9",
    "030300000000007210040008000a020103020201a9a9",
    "030d40000000007f0660000800220201030202016aa9",
    "03078000000000780cff0009001102010403020134a9",
    "0303c000000000740da50008000a02010302020109a9",
    "0302c000000000730d9c0008000a020103020201fea9"
  ]
  
  pretty_header()
  
  for a in test_data:
    # decoded = decode_cdi_packet()
    # pretty_print(decoded)

    pretty_print(bytes.fromhex(a))


###
#
# Print functions
#
###

def format_hex(data, highlight=None):
  """Format bytes as hex with optional highlighted indices (shown in red).
  
  Args:
    data: bytes object
    highlight: set of byte indices to highlight in red (e.g., {8, 9})
  """
  parts = []
  for i, b in enumerate(data):
    hex_str = f'{b:02x}'
    if highlight and i in highlight:
      hex_str = f'\033[91m{hex_str}\033[0m'  # red text
    parts.append(hex_str)
  return ' '.join(parts)


def pretty_header():
    # Print header for the data
    print("Time     | RPM  | CDI volt | Timing | Raw message")
    print("-" * 70)


def pretty_print(bytes):
  """
  Pretty print CDI message in a formatted table row
  
  Args:
    bytes: Raw bytes - a message received from a CDI. It will be decoded to a dictionary with keys 'rpm', 'cdi_voltage', 'timing byte', 'status_byte' or None if packet was invalid
  """
  decoded_message = decode_cdi_packet(bytes)
  if decoded_message is None:
    # Invalid packet - print error row
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{timestamp} | {'---':^4} | {'---':^8} | {'---':^6} | {'---':^11}")
    return
  
  # Get current time
  timestamp = datetime.now().strftime("%H:%M:%S")
  
  # Format each field with proper width and alignment
  rpm_str = f"{decoded_message['rpm']:4d}"  # 4 digits, right aligned
  cdi_voltage_str = f"{decoded_message['cdi_voltage']:5.1f}V"  # 5 chars total with 1 decimal
  timing_angle = f"{decoded_message['timing byte']:2.1f}" # Timing in degrees
  
  # Print the formatted row with bytes 8 and 9 highlighted in red
  print(f"{timestamp} | {rpm_str} | {cdi_voltage_str:^8} | {timing_angle:^6} | {format_hex(bytes, highlight={8, 9})}")


###
#
# start sequence
#
###

if __name__ == "__main__":
  # Set up command-line argument parser
  parser = argparse.ArgumentParser(
    description='CDI Monitor - Read and display CDI data in real-time',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog='''
Examples:
  python cdi_monitor_simple.py COM5          # Windows
  python cdi_monitor_simple.py /dev/ttyUSB0  # Linux
  python cdi_monitor_simple.py test          # Run test mode
    '''
  )
  
  parser.add_argument(
    'port',
    nargs='?',  # Makes it optional
    default='COM5',
    help='Serial port name (default: COM5)'
  )
  
  # Parse arguments
  args = parser.parse_args()
  
  # Check if running in test mode
  if args.port == 'test':
    test()
  else:
    main(args.port)
