import struct, os, sys

path = r'F:\opencodeprojects\k30pro\boot_lmi.img'
with open(path, 'rb') as f:
    data = f.read()

page_size = struct.unpack_from('<I', data, 36)[0]
kernel_size = struct.unpack_from('<I', data, 8)[0]
ramdisk_size = struct.unpack_from('<I', data, 16)[0]
second_size = struct.unpack_from('<I', data, 24)[0]
cmdline = data[64:64+512].rstrip(b'\0').decode('ascii', errors='replace')

print(f'page_size={page_size} kernel_size={kernel_size} ramdisk_size={ramdisk_size} second_size={second_size}')
print(f'cmdline={cmdline}')

outdir = r'F:\opencodeprojects\k30pro\temp_boot_unpack'
os.makedirs(outdir, exist_ok=True)

base = page_size
kernel_data = data[base:base+kernel_size]
with open(os.path.join(outdir, 'kernel.gz'), 'wb') as f:
    f.write(kernel_data)
print(f'kernel.gz written: {len(kernel_data)} bytes')

base = (base + kernel_size + page_size - 1) // page_size * page_size
ramdisk_data = data[base:base+ramdisk_size]
with open(os.path.join(outdir, 'ramdisk.cpio.gz'), 'wb') as f:
    f.write(ramdisk_data)
print(f'ramdisk.cpio.gz written: {len(ramdisk_data)} bytes')

base = (base + ramdisk_size + page_size - 1) // page_size * page_size
if second_size > 0:
    second_data = data[base:base+second_size]
    with open(os.path.join(outdir, 'dtb'), 'wb') as f:
        f.write(second_data)
    print(f'dtb written: {len(second_data)} bytes, magic={second_data[:4].hex()}')
else:
    print('no dtb/second stage')

# Decompress kernel
import gzip
kernel_decomp = gzip.decompress(kernel_data)
with open(os.path.join(outdir, 'Image'), 'wb') as f:
    f.write(kernel_decomp)
print(f'Image (uncompressed) written: {len(kernel_decomp)} bytes')

# List ramdisk contents if possible
print('\n--- Ramdisk top-level entries ---')
import subprocess
result = subprocess.run(['wsl', 'zcat', os.path.join(outdir, 'ramdisk.cpio.gz').replace('\\', '/').replace('F:', '/mnt/f'), '|', 'cpio', '-t'], 
                       capture_output=True, text=True, shell=True)
if result.stdout:
    for line in result.stdout.strip().split('\n')[:50]:
        print(line)
else:
    print(f'wsl not available or error: {result.stderr[:200]}')
