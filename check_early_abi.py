#!/usr/bin/env python3
"""Validate the built .vermagic before expensive image/package steps.

The official kmod dependency requires both a matching kernel version and hash.
The exact version is also checked by check_abi.py after image compilation.
"""
import json
from pathlib import Path
import sys

OFFICIAL = 'aa81475ddbdbcc69877f69037ae40cd8'
if len(sys.argv) != 3:
    sys.exit('Usage: check_early_abi.py LINUX_DIR/.vermagic OUTPUT.JSON')
actual = Path(sys.argv[1]).read_text().strip()
result = {'official_vermagic': OFFICIAL, 'built_vermagic': actual,
          'matches_official_abi_hash': actual == OFFICIAL}
Path(sys.argv[2]).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
if actual != OFFICIAL:
    sys.exit('ERROR: kernel ABI hash mismatch. Build stopped before packaging firmware.')
