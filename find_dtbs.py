import struct

data = open('/tmp/kernel.raw', 'rb').read()
magic = b'\xd0\x0d\xfe\xed'

positions = []
start = 0
while True:
    idx = data.find(magic, start)
    if idx == -1:
        break
    size = struct.unpack('>I', data[idx+4:idx+8])[0]
    positions.append((idx, size))
    start = idx + 1

print(f'Found {len(positions)} DTB(s) in kernel.raw')
for i, p in enumerate(positions[:20]):
    off, sz = p
    label = '(small/overlay)' if sz < 500 else ''
    print(f'  #{i}: offset={off} (0x{off:X}) size={sz} {label}')

# Save the largest DTB
if positions:
    largest = max(positions, key=lambda x: x[1])
    off, sz = largest
    print(f'\nLargest DTB: offset={off} size={sz}')
    dtb = data[off:off+sz]
    open('/tmp/lmi_largest.dtb', 'wb').write(dtb)
    print('Saved to /tmp/lmi_largest.dtb')
