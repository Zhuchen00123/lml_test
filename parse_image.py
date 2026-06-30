import struct

with open('/tmp/kernel.raw', 'rb') as f:
    data = f.read()

print(f'Image size: {len(data)} bytes ({len(data)/1024/1024:.1f} MB)')

# ARM64 Image header parsing
# Bytes 0-3: code0 (branch instruction)
# Bytes 4-7: code1
# Bytes 8-15: text_offset (LE QWORD)
# Bytes 16-23: image_size (LE QWORD) 
# Bytes 24-31: flags
# Bytes 32-39: reserved2
# Bytes 40-47: reserved3
# Bytes 48-55: reserved4
# Bytes 56-63: magic (0x644d5241 = 'ARM\x64')

magic = data[56:60].decode('ascii', errors='replace')
print(f'Image magic: {magic}')

if magic == 'ARM\x64' or magic == 'ARMd':
    image_size = struct.unpack('<Q', data[16:24])[0]
    flags = struct.unpack('<Q', data[24:32])[0]
    print(f'Image size from header: {image_size} ({image_size/1024/1024:.1f} MB)')
    print(f'Flags: 0x{flags:016X}')
    
    # Check if DTB is appended after image_size
    if image_size < len(data):
        extra = data[image_size:]
        print(f'Extra data after Image ({len(extra)} bytes)')
        
        # Look for DTB magic
        dtb_magic = b'\xd0\x0d\xfe\xed'
        pos = extra.find(dtb_magic)
        if pos >= 0:
            dtb_size = struct.unpack('>I', extra[pos+4:pos+8])[0]
            print(f'Appended DTB at Image+{pos} ({hex(image_size+pos)}), size={dtb_size}')
            
            # Save it
            dtb = extra[pos:pos+dtb_size]
            with open('/tmp/lmi_full.dtb', 'wb') as f:
                f.write(dtb)
            print(f'Saved to /tmp/lmi_full.dtb')
        else:
            print('No appended DTB found')
            # Check if there are strings indicating DTB data
            for off in range(0, min(len(extra), 4096), 4):
                if extra[off:off+4] == dtb_magic:
                    print(f'DTB found at extra offset {off}')
            # Last 100 bytes
            print(f'Last 100 bytes: {extra[-100:].hex()}')
    else:
        print('No extra data after Image')
else:
    print('Not an ARM64 Image')
