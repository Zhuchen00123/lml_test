"""Build Android boot image from kernel + ramdisk."""
import struct, os, hashlib

def round_up(n, page):
    return (n + page - 1) // page * page

def make_bootimg(kernel_path, ramdisk_path, output_path, cmdline='', page_size=4096):
    kernel_size = os.path.getsize(kernel_path)
    ramdisk_size = os.path.getsize(ramdisk_path)

    # Android boot image v0 header is 1648 bytes but padded to page
    header_size = page_size

    # Compute offsets (page aligned)
    kernel_offset = header_size
    ramdisk_offset = round_up(kernel_offset + kernel_size, page_size)

    total_size = round_up(ramdisk_offset + ramdisk_size, page_size)

    with open(kernel_path, 'rb') as f:
        kernel_data = f.read()
    with open(ramdisk_path, 'rb') as f:
        ramdisk_data = f.read()

    # Build header
    header = bytearray(header_size)
    struct.pack_into('<8s', header, 0, b'ANDROID!')
    struct.pack_into('<I', header, 8, kernel_size)
    struct.pack_into('<I', header, 12, 0)  # kernel_addr (not used by fastboot)
    struct.pack_into('<I', header, 16, ramdisk_size)
    struct.pack_into('<I', header, 20, 0)  # ramdisk_addr
    struct.pack_into('<I', header, 24, 0)  # second_size
    struct.pack_into('<I', header, 28, 0)  # second_addr
    struct.pack_into('<I', header, 32, 0)  # tags_addr
    struct.pack_into('<I', header, 36, page_size)
    struct.pack_into('<I', header, 40, 0)  # header_version
    # cmdline at offset 64, 512 bytes
    cmd_bytes = cmdline.encode('ascii') + b'\0' * (512 - len(cmdline.encode('ascii')))
    header[64:64+512] = cmd_bytes[:512]

    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(kernel_data)
        # pad kernel to page boundary
        padding = ramdisk_offset - header_size - kernel_size
        if padding > 0:
            f.write(b'\0' * padding)
        f.write(ramdisk_data)
        # pad to total page boundary
        remaining = total_size - f.tell()
        if remaining > 0:
            f.write(b'\0' * remaining)

    total = os.path.getsize(output_path)
    print(f'Boot image created: {output_path}')
    print(f'  Kernel: {kernel_size} bytes, Ramdisk: {ramdisk_size} bytes')
    print(f'  Total: {total} bytes ({total / 1024 / 1024:.1f} MB)')
    print(f'  Cmdline: {cmdline}')

if __name__ == '__main__':
    base = r'F:\opencodeprojects\k30pro\temp_boot_unpack'
    make_bootimg(
        kernel_path=os.path.join(base, 'kernel.gz'),
        ramdisk_path=os.path.join(base, 'ramdisk_mod.cpio.gz'),
        output_path=os.path.join(base, 'boot-charisk-debian.img'),
        cmdline='loglevel=2 panic=30 root=UUID=d7e36bed-3d3f-451b-8d0c-197a356a5ac0 systemd.gpt_auto=0',
    )
