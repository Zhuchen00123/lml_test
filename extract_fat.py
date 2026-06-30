import struct
import os

src = '/mnt/c/Users/15185/Desktop/mi12/images/NON-HLOS.bin'
outdir = '/tmp/nonhlos_extracted'

with open(src, 'rb') as f:
    data = f.read()

# Pad to 469MB as per AGENTS.md
required_size = 469 * 1024 * 1024
if len(data) < required_size:
    data = data + b'\x00' * (required_size - len(data))
    print(f'Padded to {len(data)} bytes ({len(data)/1024/1024:.1f} MB)')
else:
    print(f'Size: {len(data)} bytes ({len(data)/1024/1024:.1f} MB)')

# Parse FAT16 BPB
header = data[:512]
bytes_per_sector = struct.unpack('<H', header[11:13])[0]
sectors_per_cluster = header[13]
reserved_sectors = struct.unpack('<H', header[14:16])[0]
num_fats = header[16]
root_entries = struct.unpack('<H', header[17:19])[0]
total_sectors_16 = struct.unpack('<H', header[19:21])[0]
sectors_per_fat = struct.unpack('<H', header[22:24])[0]

print(f'FAT16: {bytes_per_sector}B/sector, {sectors_per_cluster} sec/cluster, {root_entries} root entries')

root_start = (reserved_sectors + num_fats * sectors_per_fat) * bytes_per_sector
data_start = root_start + root_entries * 32
cluster_size = sectors_per_cluster * bytes_per_sector

os.makedirs(outdir, exist_ok=True)

# Read root directory entries
offset = root_start
entries_found = 0
while offset < data_start:
    entry = data[offset:offset+32]
    if entry[0] == 0:
        break
    if entry[0] == 0xe5:  # deleted
        offset += 32
        continue
    
    name = entry[0:8].decode('ascii', errors='replace').strip()
    ext = entry[8:11].decode('ascii', errors='replace').strip()
    attr = entry[11]
    first_cluster = struct.unpack('<H', entry[26:28])[0]
    file_size = struct.unpack('<I', entry[28:32])[0]
    
    if attr & 0x08:  # Volume label
        offset += 32
        continue
    
    fullname = f'{name}.{ext}' if ext else name
    
    if attr & 0x10:  # Directory
        if name not in ('.', '..'):
            print(f'[DIR]  {fullname} (cluster {first_cluster})')
            entries_found += 1
            
            # Read subdirectory
            subdir_start = data_start + (first_cluster - 2) * cluster_size
            sub_offset = subdir_start
            while sub_offset < subdir_start + cluster_size * 4:
                sub_entry = data[sub_offset:sub_offset+32]
                if sub_entry[0] == 0:
                    break
                if sub_entry[0] == 0xe5:
                    sub_offset += 32
                    continue
                sub_name = sub_entry[0:8].decode('ascii', errors='replace').strip()
                sub_ext = sub_entry[8:11].decode('ascii', errors='replace').strip()
                sub_attr = sub_entry[11]
                sub_cluster = struct.unpack('<H', sub_entry[26:28])[0]
                sub_size = struct.unpack('<I', sub_entry[28:32])[0]
                sub_full = f'{sub_name}.{sub_ext}' if sub_ext else sub_name
                if not (sub_attr & 0x08):
                    print(f'  [FILE] {sub_full} ({sub_size} bytes, cluster {sub_cluster})')
                sub_offset += 32
    else:
        print(f'[FILE] {fullname} ({file_size} bytes, cluster {first_cluster})')
        entries_found += 1
        
        # For QCA6390 BT firmware, extract the file
        if 'btfw' in fullname.lower() or 'hpnv' in fullname.lower() or 'htbt' in fullname.lower() or fullname.lower().endswith('.tlv'):
            file_data = bytearray()
            cluster = first_cluster
            while cluster < 0xFFF8 and len(file_data) < file_size:
                sect_start = data_start + (cluster - 2) * cluster_size
                file_data.extend(data[sect_start:sect_start + cluster_size])
                # FAT16 cluster chain - simplified, just read sequentially
                cluster += 1
                if len(file_data) >= file_size:
                    break
            file_data = bytes(file_data[:file_size])
            outpath = os.path.join(outdir, fullname.replace(' ', '_'))
            with open(outpath, 'wb') as o:
                o.write(file_data)
            print(f'  -> Extracted to {outpath} ({len(file_data)} bytes)')
    
    offset += 32
    if entries_found > 200:
        break

print(f'\nDone. Listed {entries_found} entries in root dir.')
