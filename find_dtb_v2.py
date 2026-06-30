import struct

data = open('/tmp/kernel.raw', 'rb').read()
target = 20819152
magic = b'\xd0\x0d\xfe\xed'

# The string 'qcom,pm8998-pon' is in the DTB strings block
# The strings block is the last part of the DTB (after structure block)
# The DTB header is at the beginning with magic, total size, etc.

# Let's find the FDT structure markers near the target
# FDT_BEGIN_NODE = 0x00000001, FDT_END_NODE = 0x00000002, 
# FDT_PROP = 0x00000003, FDT_END = 0x00000009

# The string block offset is at bytes 12-15 of the DTB header
# So if we can find the DTB header, we can calculate where the string should be

# Let's search for DTB magic in the entire kernel.raw, looking for 
# DTBs that have reasonable size and overlap with our target

print(f'Searching for all DTBs in kernel.raw...')
dtbs = []
for off in range(0, len(data) - 8, 4):
    if data[off:off+4] == magic:
        if off + 40 <= len(data):  # Minimum DTB header size
            total_size = struct.unpack('>I', data[off+4:off+8])[0]
            off_dt_struct = struct.unpack('>I', data[off+8:off+12])[0]
            off_dt_strings = struct.unpack('>I', data[off+12:off+16])[0]
            version = struct.unpack('>I', data[off+28:off+32])[0]
            
            if 100 < total_size < 1000000 and off + total_size <= len(data):
                # Check if target is within this DTB's strings block
                strings_start = off + off_dt_strings
                if strings_start <= target < off + total_size:
                    dtbs.append((off, total_size, off_dt_strings, off_dt_struct))
                    print(f'  DTB at {off} (0x{off:X}): size={total_size}, strings@{off_dt_strings}, struct@{off_dt_struct}')

print(f'\nFound {len(dtbs)} DTBs containing the target string')

for off, size, str_off, struct_off in dtbs:
    print(f'\nDTB at offset {off}, size={size}:')
    print(f'  Structure block offset: {off + struct_off}')
    print(f'  Strings block offset: {off + str_off}')
    # Extract and save
    dtb = data[off:off+size]
    outpath = f'/tmp/lmi_full_{off:X}.dtb'
    with open(outpath, 'wb') as f:
        f.write(dtb)
    print(f'  Saved to {outpath}')
    
    # Show header
    print(f'  Header: {dtb[:40].hex()}')
