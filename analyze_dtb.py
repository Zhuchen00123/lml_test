import struct

data = open('/tmp/kernel.raw', 'rb').read()
print(f'kernel.raw len: {len(data)} bytes ({len(data)/1024/1024:.1f} MB)')

# Check for DTB magic at multiple spots
magic = b'\xd0\x0d\xfe\xed'

# Find all occurrences
for off in range(0, len(data), 4):
    if data[off:off+4] == magic:
        # Read total size from header (offset 4, big-endian 32-bit)
        if off + 8 <= len(data):
            sz = struct.unpack('>I', data[off+4:off+8])[0]
            if off + sz <= len(data):
                print(f'DTB at {off} (0x{off:X}), size={sz}')
                # Check if this DTB contains expected strings
                chunk = data[off:off+min(sz, 50000)]
                if b'pm8150b' in chunk or b'pm8150' in chunk:
                    print(f'  -> Contains pm8150 reference!')
                if b'system-power-controller' in chunk:
                    print(f'  -> Already has system-power-controller')
                if b'qcom,pm8998-pon' in chunk:
                    print(f'  -> Has qcom,pm8998-pon')
                if b'lmi' in chunk:
                    print(f'  -> Contains lmi reference!')
                
                # Show some content
                strings = [s for s in chunk.split(b'\x00') if len(s) > 2][:30]
                print(f'  -> Strings: {[s.decode("ascii","replace") for s in strings[:15]]}')
                
print('\nDone.')
