import os

img = open(r'F:\opencodeprojects\k30pro\temp_boot_unpack\Image', 'rb').read()
pos = 0
dtb_count = 0
while True:
    p = img.find(b'\xd0\x0d\xfe\xed', pos)
    if p == -1:
        break
    dtb_count += 1
    if p + 8 <= len(img):
        total_size = int.from_bytes(img[p+4:p+8], 'big')
        end = min(p + total_size, len(img))
        # Find model string
        model = b''
        for i in range(p, end - 50):
            if img[i:i+6] == b'model\x00':
                end_str = img.find(b'\x00', i+6)
                model = img[i+6:end_str] if end_str > 0 else b''
                break
        # Find bootargs
        bootargs = b''
        for i in range(p, end - 100):
            if img[i:i+9] == b'bootargs\x00':
                end_str = img.find(b'\x00', i+9)
                bootargs = img[i+9:end_str] if end_str > 0 else b''
                break
        print(f"DTB #{dtb_count} offset={p:#x} size={total_size} model={model.decode(errors='replace')}")
        if bootargs:
            print(f"  bootargs={bootargs.decode(errors='replace')}")
    pos = p + 4

print(f"Total DTBs found: {dtb_count}")

# Also search for compatible strings
if dtb_count == 0:
    # Maybe embedded in a different way
    for pattern in [b'xiaomi', b'lmi', b'sm8250', b'qcom']:
        count = img.count(pattern)
        if count > 0:
            print(f"Found '{pattern.decode()}' {count} times in Image")
