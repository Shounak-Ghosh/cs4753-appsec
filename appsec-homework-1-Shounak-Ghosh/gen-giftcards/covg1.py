import struct
import sys

data = b"A" * 32  # Merchant ID
data += b"B" * 32  # Customer ID
data += struct.pack("<I", 1)  # One record

# Record type: Animated Message
data += struct.pack("<I", 8 + 32 + 256)  # Record size
data += struct.pack("<I", 3)  # Record type
data += b"X" * 31 + b'\x00'  # 32-byte message

#Should be harmless: (0+0 = 0), but increases coverage
data += b'\x06\x01\x02'  # add regs[1] to regs[2] and store in regs[1] (0+0 = 0)
data += b'\x08' * (256 - 3)  # Fill remaining space with NOP-like instructions

# Write the file
f = open(sys.argv[1], 'wb')
datalen = len(data) + 4  # Plus 4 bytes for the length itself
f.write(struct.pack("<I", datalen))
f.write(data)
f.close()

