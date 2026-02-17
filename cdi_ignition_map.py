#!/usr/bin/env python3
"""
CDI Ignition Map Read/Write Tool
Based on reverse engineering of the tuner program's serial communication
"""

import serial
import time
import struct
import sys

class CDIIgnitionMap:
    def __init__(self, port='COM4', baudrate=19200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        
    def connect(self):
        """Connect to the CDI"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"Connected to {self.port} at {self.baudrate} baud")
            time.sleep(0.1)  # Allow connection to stabilize
            return True
        except serial.SerialException as e:
            print(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the CDI"""
        if self.ser:
            self.ser.close()
            print("Disconnected")
    
    def write_ignition_map(self, map_data):
        """
        Write ignition map to CDI
        
        Based on the sniffed communication, the protocol appears to be:
        1. Send command 0x0D
        2. Send the ignition map data as 16-bit little-endian values
        
        The map_data should be the ignition advance values from the .cfg file
        """
        if not self.ser:
            print("Not connected")
            return False
        
        try:
            # Send the write command
            print("\nSending write ignition map command: 0x0D")
            self.ser.write(bytes([0x0D]))
            
            # Convert the map data to bytes (16-bit little-endian)
            data_bytes = bytearray()
            
            # The sniffed data shows specific values being sent
            # Let's send the second row starting from index 5 (matching the sniff)
            test_values = [
                4730, 6375, 7573, 8914, 10268, 11336, 11926, 12891,
                13975, 15070, 16000, 0, 0, 0, 0, 0
            ]
            
            print("\nSending ignition map data:")
            for i, value in enumerate(test_values):
                # Convert to 16-bit little-endian
                bytes_val = struct.pack('<H', value)
                data_bytes.extend(bytes_val)
                
                # Send each byte individually (as seen in the sniff)
                for b in bytes_val:
                    self.ser.write(bytes([b]))
                    time.sleep(0.001)  # Small delay between bytes
                
                if i < 8:
                    print(f"  Value {i}: {value:5d} = 0x{value:04X} -> {bytes_val[0]:02X} {bytes_val[1]:02X}")
            
            print(f"\nSent {len(data_bytes)} bytes total")
            
            # Wait for any response
            time.sleep(0.1)
            response = self.ser.read(100)
            if response:
                print(f"Response: {' '.join(f'{b:02X}' for b in response)}")
            else:
                print("No response received (this may be normal)")
            
            return True
            
        except Exception as e:
            print(f"Error writing ignition map: {e}")
            return False
    
    def parse_cfg_file(self, filename):
        """Parse ignition map from .cfg file"""
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            # Parse the data - it appears to be in a specific format
            # with multiple rows of values
            all_values = []
            for line in lines:
                line = line.strip()
                if line:
                    values = [int(x) for x in line.split('\t')]
                    all_values.extend(values)
            
            return all_values
            
        except Exception as e:
            print(f"Error parsing cfg file: {e}")
            return None
    
    def test_protocol(self):
        """Test the exact protocol sequence from the sniff"""
        if not self.ser:
            print("Not connected")
            return False
        
        print("\nTesting exact protocol sequence...")
        
        # Send command 0x0D
        print("Sending: 0x0D")
        self.ser.write(bytes([0x0D]))
        time.sleep(0.01)
        
        # Send the exact sequence from the sniff
        sequence = [
            0x7a, 0x12,  # 4730
            0xe7, 0x18,  # 6375
            0x95, 0x1d,  # 7573
            0xd2, 0x22,  # 8914
            0x1c, 0x28,  # 10268
            0x48, 0x2c,  # 11336
            0x96, 0x2e,  # 11926
            0x5b, 0x32,  # 12891
            0x97, 0x36,  # 13975
            0xde, 0x3a,  # 15070
            0x80, 0x3e,  # 16000
            0x58, 0x02,  # 600
            0x77, 0x02,  # 631
            0x3e, 0x04,  # 1086
            0x19, 0x07,  # 1817
            0x98, 0x09   # 2456
        ]
        
        print(f"Sending {len(sequence)} bytes:")
        for i in range(0, len(sequence), 2):
            val = sequence[i] | (sequence[i+1] << 8)
            print(f"  Bytes {sequence[i]:02X} {sequence[i+1]:02X} = {val:5d}")
            self.ser.write(bytes([sequence[i]]))
            time.sleep(0.001)
            self.ser.write(bytes([sequence[i+1]]))
            time.sleep(0.001)
        
        # Check for response
        time.sleep(0.1)
        response = self.ser.read(100)
        if response:
            print(f"\nResponse received ({len(response)} bytes):")
            print(f"  Hex: {' '.join(f'{b:02X}' for b in response)}")
        else:
            print("\nNo response (this may be normal for write operations)")
        
        return True

def main():
    # Create CDI interface
    cdi = CDIIgnitionMap()
    
    # Connect to CDI
    if not cdi.connect():
        return 1
    
    try:
        # Test the exact protocol
        cdi.test_protocol()
        
        print("\n" + "="*60)
        print("Test complete!")
        print("="*60)
        
    finally:
        cdi.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())