#!/usr/bin/env python
"""
CDI Ignition Map Read Tool
Reads ignition map from API Tech CDI via serial communication.

Protocol (from COM port sniffing):
1. Send ignition map request: 01 06 00 00 ... 07 B8 (64 bytes)
3. CDI responds with page 0: 02 07 00 00 ... B9 (64 bytes)
4. Host echoes page back: 01 07 00 00 ... B8 (to request next page)
5. CDI sends page 1: 02 07 00 01 ... B9
6. ... continues for pages 0-6
"""

import serial
from time import sleep
import sys

READ_TIMING_MAP_MESSAGE = bytes([
  0x01, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07, 0xb8
])

def send_message(port, message):
  port.write(message)

def read_page(port, timeout=1.0):
  """Read a 64-byte page from CDI"""
  data = bytearray()
  start = port.timeout
  port.timeout = timeout
  
  while len(data) < 64:
    chunk = port.read(64 - len(data))
    if not chunk:
      break
    data.extend(chunk)
  
  port.timeout = start
  return bytes(data) if len(data) == 64 else None

def make_ack(page_data):
  """Create acknowledgment by changing byte 0 from 02 to 01 and adjusting checksum"""
  ack = bytearray(page_data)
  ack[0] = 0x01  # Change response marker to request marker
  ack[62] = ack[62] - 1 # subtract 1. Required for a proper message format
  ack[63] = ack[63] - 1  # End marker
  return bytes(ack)

def read_all_CDI_timing_messages(port):
  """Read ignition map bytes from CDI"""
  message_bytes = []
  
  # Send initial request
  send_message(port, READ_TIMING_MAP_MESSAGE)
  sleep(0.1)
  
  # Read pages
  for attempt in range(2):  # We only need 2 pages of data because our CDI supports just a single ignition map
    page = read_page(port, timeout=0.5)
    
    # Immediately request for next page
    ack = make_ack(page)
    send_message(port, ack)

    message_bytes += page[4:62]

  return message_bytes

def parse_ignition_map(message_bytes):
  
  rpm_values = []
  timing_values = []
  
  # for counter, data in pages.items():
    
  # first 16 bytes are RPMs
  for i in range(0, 32, 2):
    val = message_bytes[i] | (message_bytes[i + 1] << 8)
    rpm_values.append(val)
  
  # next 16 bytes are timings
  for i in range(32, 64, 2):
    val = message_bytes[i] | (message_bytes[i + 1] << 8)
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
  
  message_bytes = read_all_CDI_timing_messages(port)
  port.close()
  
  
  rpm_values, timing_values = parse_ignition_map(message_bytes)
  print("rpm_values:", rpm_values)
  print("timing_values:", timing_values)
  
  print_ignition_map(rpm_values, timing_values)
  
  return 0

if __name__ == "__main__":
  sys.exit(main())
