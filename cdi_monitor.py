#!/usr/bin/env python3
"""
Continuously reads and displays CDI data with decoding
Shows RPM, Battery Voltage, and Ignition Timing
"""

import serial
import time
import struct
from datetime import datetime
import sys
import argparse

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
  init_bytes = [0x01, 0xAB, 0xAC, 0xA1]
  
  for round in [1, 2]:
    print(f" Sending init #{round}...", end="")
    for byte in init_bytes:
      port.write(bytes([byte]))
    
    # Wait for response
    time.sleep(0.1)
    
    # Check if CDI responded
    if port.in_waiting > 0:
      response = port.read(port.in_waiting)
      print(f" Got response: {len(response)} bytes")
    else:
      print(" No response")
  
  return port

def decode_cdi_packet(data):
  """
  Decode CDI packet to get RPM, Battery, and Timing
  This is a simplified decoder for beginners
  """
  # Check if packet is valid (starts with 0x03, ends with 0xA9)
  if len(data) != 22 or data[0] != 0x03 or data[21] != 0xA9:
    return None
  
  # Extract RPM (bytes 1-2, big-endian format)
  # Big-endian means most significant byte first
  rpm = (data[1] << 8) | data[2]  # Combine two bytes into one number
  
  # Extract Battery Voltage (byte 7)
  # Stored as decivolts (e.g., 115 = 11.5V)
  battery_decivolts = data[7]
  battery_voltage = battery_decivolts / 10.0
  
  # Extract Status Mode (byte 8)
  # This tells us how to interpret the timing
  status = data[8]
  
  # Extract Timing (byte 9)
  # The scaling depends on the status mode
  timing_byte = data[9]

  return {
    'rpm': rpm,
    'battery': battery_voltage,
    'timing byte': timing_byte,
    'status_byte': status
  }

def main(port_name='COM5'):
  """Main program
  
  Args:
    port_name: Serial port name to connect to
  """
  print("="*70)
  print("CDI Monitor with Decoding - Simple Version")
  print("="*70)
  print("\nThis program reads data from your CDI and shows:")
  print("  • Engine RPM")
  print("  • Battery Voltage")
  print("  • Ignition Timing")
  print("\nPress Ctrl+C to stop\n")
  
  try:
    # Connect to CDI
    port = connect_to_cdi(port_name)
    print("\n✓ Connected! Starting monitor...\n")
    
    # Print header for the data
    print("Time     | RPM  | Battery | Timing byte | status byte ")
    print("-" * 70)
    
    # Main loop - keep reading data
    while True:
      # Send request for data
      request = [0x01, 0xAB, 0xAC, 0xA1]
      for byte in request:
        port.write(bytes([byte]))
      
      # Wait a bit
      time.sleep(0.1)
      
      # Read response if available
      if port.in_waiting >= 22: # CDI sends 22-byte packets
        data = port.read(22)
        
        # Decode the packet
        decoded = decode_cdi_packet(data)
        pretty_print(decoded)
      
      # Wait before next request
      time.sleep(0.9) # Total 1 second between requests
      
  except KeyboardInterrupt:
    print("\n\nStopped by user")
    
  except Exception as e:
    print(f"\nError: {e}")
    
  finally:
    # Close the port
    if 'port' in locals():
      port.close()
      print("Port closed")

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
  
  # Print header for the test data
  print("Time     | RPM  | Battery | Timing byte | status byte ")
  print("-" * 70)
  
  for a in test_data:
    decoded = decode_cdi_packet(bytes.fromhex(a))
    pretty_print(decoded)

def pretty_print(data):
  """
  Pretty print CDI data in a formatted table row
  
  Args:
    data: Dictionary with keys 'rpm', 'battery', 'timing byte', 'status_byte'
          or None if packet was invalid
  """
  if data is None:
    # Invalid packet - print error row
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{timestamp} | {'---':^4} | {'---':^7} | {'---':^11} | {'---':^11}")
    return
  
  # Get current time
  timestamp = datetime.now().strftime("%H:%M:%S")
  
  # Format each field with proper width and alignment
  rpm_str = f"{data['rpm']:4d}"  # 4 digits, right aligned
  battery_str = f"{data['battery']:5.1f}V"  # 5 chars total with 1 decimal
  timing_str = f"0x{data['timing byte']:02X} ({data['timing byte']:3d})"  # Hex and decimal
  status_str = f"0x{data['status_byte']:02X} ({data['status_byte']:3d})"  # Hex and decimal
  
  # Print the formatted row
  print(f"{timestamp} | {rpm_str} | {battery_str:^7} | {timing_str:^11} | {status_str:^11}")

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