import struct
import sys

data = open('/tmp/kernel.raw', 'rb').read()
magic = b'\xd0\x0d\xfe\xed'
pos = data.find(magic)
if pos >= 0:
    print(f'DTB found at offset {pos} (0x{pos:X})')
    dtb_size = struct.unpack('>I', data[pos+4:pos+8])[0]
    print(f'DTB size: {dtb_size} bytes')
    dtb = data[pos:pos+dtb_size]
    open('/tmp/lmi.dtb', 'wb').write(dtb)
    print('DTB saved to /tmp/lmi.dtb')
else:
    print('DTB not found in kernel.raw')
