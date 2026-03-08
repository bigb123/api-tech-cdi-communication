# Files formatting

Indentation: 2 spaces.

# Decoding CDI messages

CDI communicates with us over USB cable via serial protocol.

- baud rate: 19200
- DTR: high
- DTS: high
-  8 data bits
-  no parity
-  1 stop bit

We send a sequence of bytes:

```
0x01 0xAB 0xAC 0xA1
```

CDI responds with messages of 22 bytes about current status of running engine:

```
Byte 0:      0x03        - Packet header/type identifier
Bytes 1-2:   RPM         - Engine RPM (16-bit big-endian)
Bytes 3-6:   0x00        - Reserved/unused
Byte 7:      CDI voltage - CDI voltage in decivolts (11.5V = 115 = 0x73)
Byte 8:      unknown     - Decreases with RPM 
Byte 9:      unknown     - Varies significantly
Byte 10:     zero        - always zero
Byte 11:     unknown     
Byte 12:     zero
Byte 13:     Ignition    - Base ignition angle x 2
Bytes 14-19: Various     - Additional status/config data
Byte 20:     Checksum    - Packet checksum
Byte 21:     0xA9        - End marker
```

Check README.md for more details.