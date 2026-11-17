#!/usr/bin/env python3
"""Basic size and header tests; NOT a physical hardware certification."""
from pathlib import Path
import binascii
import hashlib
import struct
import sys

if len(sys.argv) != 2:
    sys.exit('Usage: verify_image.py IMAGE')
p = Path(sys.argv[1])
data = p.read_bytes()
if 'cudy_wr1300e-v2' not in p.name or 'sysupgrade' not in p.name:
    sys.exit('Wrong filename / target')
if not 0x400000 < len(data) <= 0xF80000:
    sys.exit(f'Wrong image size: {len(data)} bytes')
if data[:4] != bytes.fromhex('27051956'):
    sys.exit('Missing uImage U-Boot header (expected by this target)')
magic, hcrc, timestamp, size, load, entry, dcrc = struct.unpack_from('>7I', data)
h = bytearray(data[:64]); h[4:8] = b'\x00' * 4
if binascii.crc32(h) & 0xffffffff != hcrc:
    sys.exit('uImage header CRC invalid')
if size > len(data) - 64 or binascii.crc32(data[64:64+size]) & 0xffffffff != dcrc:
    sys.exit('uImage kernel CRC invalid')
print('Image size, name, U-Boot header and CRC: PASS')
print('SHA-256:', hashlib.sha256(data).hexdigest())
print('WARNING: This check does not establish safe flashing or device compatibility')
