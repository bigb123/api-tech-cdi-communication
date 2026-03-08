#!/usr/bin/env python
"""
CDI Ignition Map Read Tool
Reads ignition map from API Tech CDI via serial communication.

Protocol (from COM port sniffing):
1. Send ignition map request: 01 06 00 00 ... checksum B8 (64 bytes)
2. Send HANDSHAKE_MESSAGE
2. CDI responds with: 02 07 00 XX ... checksum B9 (64 bytes per page)
3. Host acknowledges each page with: 01 07 00 XX ... checksum B8
"""

import serial
from time import sleep, time
import sys

# HANDSHAKE_MESSAGE is sent after read message
HANDSHAKE_MESSAGE = bytes([0x01, 0xAB, 0xAC, 0xA1])

READ_TIMING_MAP_MESSAGE = [0x01, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07, 0xb8]


def send_message(port, message):
  for byte in message:
    port.write(bytes([byte]))
  
def read_message(port):
  if port.in_waiting > 0:
    return port.read(port.in_waiting)
  return None

def parse_ignition_map(data):
  """Parse the 64-byte response and extract RPM and timing values"""
  if len(data) < 64:
    return None, None
  
  # Skip header bytes (0-3), data starts at byte 4
  # First 16 values (32 bytes) = RPM, next 13 values = timing
  rpm_values = []
  timing_values = []
  
  # Extract 16-bit little-endian values
  for i in range(4, 36, 2):  # bytes 4-35: RPM values
    val = data[i] | (data[i + 1] << 8)
    rpm_values.append(val)
  
  for i in range(36, 62, 2):  # bytes 36-61: timing values
    val = data[i] | (data[i + 1] << 8)
    timing_values.append(val)
  
  return rpm_values, timing_values

def print_ignition_map(rpm_values, timing_values):
  """Print the ignition map as a simple table"""
  print("\n  RPM    | Timing")
  print("---------+--------")
  for i in range(min(len(rpm_values), len(timing_values))):
    if rpm_values[i] > 0 or timing_values[i] > 0:
      print(f" {rpm_values[i]:>6}  | {timing_values[i]:>6}")
  print()

def main():
  if len(sys.argv) < 2:
    print("Usage: python cdi_ignition_map.py <COM_PORT>")
    print("Example: python cdi_ignition_map.py COM4")
    return 1
  
  port_name = sys.argv[1]
  
  port = serial.Serial(
    port=port_name,
    baudrate=19200,
    timeout=1.0
  )

  port.dtr = True
  port.rts = True

  print(f"Reading ignition map from {port_name}...")
  
  data = None
  while data is None:
    send_message(port, READ_TIMING_MAP_MESSAGE)
    sleep(0.1)
    send_message(port, HANDSHAKE_MESSAGE)
    sleep(0.1)
    data = read_message(port)
  
  port.close()
  
  rpm_values, timing_values = parse_ignition_map(data)
  
  if rpm_values and timing_values:
    print_ignition_map(rpm_values, timing_values)
  else:
    print("Failed to parse ignition map data")
    print(f"Raw data: {data.hex()}")
    return 1
  
  return 0


if __name__ == "__main__":
  sys.exit(main())
