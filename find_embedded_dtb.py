import struct

data = open('/tmp/kernel.raw', 'rb').read()
target = 20819152  # offset of 'qcom,pm8998-pon' string
magic = b'\xd0\x0d\xfe\xed'

# Search backwards from target for DTB magic
found = False
for off in range(target, max(0, target - 1000000), -4):
    if off + 8 > len(data):
        continue
    if data[off:off+4] == magic:
        d0 = off
        d1 = d0 + 4
        size = struct.unpack('>I', data[d0+4:d0+8])[0]
        
        # Sanity check: DTB should be at least 100 bytes and contain the target string
        if 100 < size < 1000000 and d0 + size <= len(data):
            if d0 <= target < d0 + size:
                print(f'DTB found at offset {d0} (0x{d0:X})')
                print(f'DTB size: {size} bytes ({size/1024:.1f} KB)')
                print(f'DTB end: {d0 + size} (0x{d0+size:X})')
                print(f'Target string at {target} is inside this DTB: YES')
                
                dtb = data[d0:d0+size]
                with open('/tmp/lmi_embedded.dtb', 'wb') as f:
                    f.write(dtb)
                print(f'Saved {size} bytes to /tmp/lmi_embedded.dtb')
                found = True
                break

if not found:
    print(f'No DTB found containing offset {target}')
    # Try searching forward too
    for off in range(max(0, target - 500000), min(len(data), target + 10000), 4):
        if off + 8 > len(data):
            continue
        if data[off:off+4] == magic:
            size = struct.unpack('>I', data[off+4:off+8])[0]
            if 100 < size < 1000000:
                print(f'Nearby DTB at {off}, size={size}, ends at {off+size}')
