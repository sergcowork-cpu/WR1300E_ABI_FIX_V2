#!/usr/bin/env python3
"""Fail closed unless this image can use official OpenWrt 25.12.6 kmods."""
import json
from pathlib import Path
import sys

OFFICIAL_KERNEL = '6.12.112'
OFFICIAL_VERMAGIC = 'aa81475ddbdbcc69877f69037ae40cd8'
OFFICIAL_KERNEL_RELEASE = '1'
if len(sys.argv) != 3:
    sys.exit('Usage: check_abi.py BUILT_PROFILES.JSON OUTPUT.JSON')
profiles = json.loads(Path(sys.argv[1]).read_text())
kernel = profiles.get('linux_kernel') or {}
profile = profiles.get('profiles', {}).get('cudy_wr1300e-v2')
result = {
    'target': profiles.get('target'),
    'version_number': profiles.get('version_number'),
    'arch_packages': profiles.get('arch_packages'),
    'device_present': profile is not None,
    'built_kernel': kernel,
    'official_version': OFFICIAL_KERNEL,
    'official_release': OFFICIAL_KERNEL_RELEASE,
    'official_vermagic': OFFICIAL_VERMAGIC,
    'official_kmod_feed': f'https://downloads.openwrt.org/releases/25.12.6/targets/ramips/mt7621/kmods/{OFFICIAL_KERNEL}-{OFFICIAL_KERNEL_RELEASE}-{OFFICIAL_VERMAGIC}/packages.adb'
}
result['matches_official_abi'] = all([
    profiles.get('target') == 'ramips/mt7621',
    profiles.get('version_number') == '25.12.6',
    profiles.get('arch_packages') == 'mipsel_24kc',
    profile is not None,
    kernel.get('version') == OFFICIAL_KERNEL,
    str(kernel.get('release')) == OFFICIAL_KERNEL_RELEASE,
    kernel.get('vermagic') == OFFICIAL_VERMAGIC,
])
Path(sys.argv[2]).write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
print(json.dumps(result, indent=2))
if not result['matches_official_abi']:
    sys.exit('ERROR: firmware ABI does NOT match official repository: do NOT flash for official kmod support')
print('PASS: official kernel ABI matches; official kmod repository is compatible at the package metadata level')
