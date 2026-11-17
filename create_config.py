#!/usr/bin/env python3
"""Use the COMPLETE official buildbot seed to preserve kernel Kconfig/ABI.

The previous attempt copied only six seed options and switched to a one-device
choice. The resulting kernel hash did not match the official package feed.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    sys.exit('Usage: create_config.py OFFICIAL_CONFIG.BUILDINFO OUTPUT.CONFIG')
source = Path(sys.argv[1]).read_text(encoding='utf-8')
required = [
    'CONFIG_TARGET_ramips=y',
    'CONFIG_TARGET_ramips_mt7621=y',
    'CONFIG_TARGET_MULTI_PROFILE=y',
    'CONFIG_TARGET_ALL_PROFILES=y',
    'CONFIG_ALL_KMODS=y',
    'CONFIG_ALL_NONSHARED=y',
    'CONFIG_BUILDBOT=y',
    'CONFIG_TARGET_PER_DEVICE_ROOTFS=y',
    'CONFIG_COLLECT_KERNEL_DEBUG=y',
    'CONFIG_KERNEL_BUILD_USER="builder"',
    'CONFIG_KERNEL_BUILD_DOMAIN="buildhost"',
    '# CONFIG_KERNEL_KALLSYMS is not set',
]
for symbol in required:
    if symbol not in source.splitlines():
        sys.exit(f'Official seed unexpectedly lacks {symbol!r}')

# Package-style multi-profile symbol: NEVER select
# CONFIG_TARGET_ramips_mt7621_DEVICE_cudy_wr1300e-v2=y!
profile = 'CONFIG_TARGET_DEVICE_ramips_mt7621_DEVICE_cudy_wr1300e-v2=y'
packages = 'CONFIG_TARGET_DEVICE_PACKAGES_ramips_mt7621_DEVICE_cudy_wr1300e-v2=""'
if profile in source:
    sys.exit('Custom target already exists in the official seed; review upstream support')
result = source.rstrip('\n') + '\n' + profile + '\n' + packages + '\n'
Path(sys.argv[2]).write_text(result, encoding='utf-8')
print(f'Preserved ALL {len(source.splitlines())} official seed lines; appended one WR1300E v2 profile')
