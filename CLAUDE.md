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

## Reading ignition map

There are 16 points we can use for ignition. First is at 1000 RPMs and last is at 16000. All other are flexible.

Ignition map is being received in number of 64 bytes chunks that we have to read and put together. First 4 bytes is a header and last 2 bytes are a message end. We end up with 58 bytes of usable data. First 32 bytes are RPM values and next 32 bytes are ignition angle degreees. A single information takes 2 bytes and it is in Little Endian. However, since first message holds only 58 bytes of information we end up with 32 bytes of RPM data and only 26 bytes of timing angle information. We have to read the missing 6 bytes from a next message. That's why we have to read 2 messages to get a full picture.
