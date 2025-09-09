import struct
import sys

# We build the content of the file in a byte string first
# This lets us calculate the length for the header at the end
data = b''
data += b"A" * 32  # Merchant ID
data += b"B" * 32  # Customer ID
data += struct.pack("<I", 1)  # One record
# Record of type animation
data += struct.pack("<I", 8 + 32 + 6)  # Record size (4 bytes)
data += struct.pack("<I", 3)  # Record type (4 bytes)
data += b"A" * 31 + b'\x00'  # Note: 32 byte message

# Program to create an infinite loop
data += b'\x00\x00\x00'  # NOP
data += b'\x09\xFD\x00'  # Jump back by -3
data += b'\x08' * (256-6)  # Fill the rest of the record with end program instructions

# Write the file
f = open(sys.argv[1], 'wb')
datalen = len(data) + 4  # Plus 4 bytes for the length itself
f.write(struct.pack("<I", datalen))
f.write(data)
f.close()
