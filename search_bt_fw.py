"""Search for QCA6390 Bluetooth firmware in NON-HLOS.bin"""
import struct

src = '/mnt/c/Users/15185/Desktop/mi12/images/NON-HLOS.bin'
data = open(src, 'rb').read()

# Pad to 469MB as per AGENTS.md
req = 469 * 1024 * 1024
if len(data) < req:
    data = data + b'\x00' * (req - len(data))

# Search for QCA6390 BT firmware signatures
# hpnv21 / hpnv20 / htbtfw / bt_nv patterns
patterns = [
    b'htbtfw', b'hpnv', b'htnv', b'bt_nv', b'btfw',
    b'qca6390', b'QCA6390', b'rampatch', b'nvm',
]

for pat in patterns:
    results = []
    offset = 0
    while True:
        pos = data.find(pat, offset)
        if pos == -1:
            break
        # Get surrounding context
        start = max(0, pos - 20)
        end = min(len(data), pos + len(pat) + 60)
        ctx = data[start:end]
        results.append((pos, ctx))
        offset = pos + 1
    
    if results:
        print(f'\n=== "{pat.decode()}" found at {len(results)} location(s) ===')
        for pos, ctx in results[:5]:
            # Show printable context
            printable = ''.join(chr(b) if 32 <= b < 127 else '.' for b in ctx)
            print(f'  offset {pos}: {printable[:80]}')
