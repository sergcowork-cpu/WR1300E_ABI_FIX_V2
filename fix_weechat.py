#!/usr/bin/env python3
"""Repair an unrelated package Kconfig cycle in the pinned LuCI feed.

Only touches a known LuCI dependency line. No kernel Kconfig flags are modified.
"""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    sys.exit('Usage: fix_weechat.py OPENWRT_ROOT')
path = Path(sys.argv[1]) / 'package/feeds/luci/luci-app-weechat/Makefile'
if not path.exists():
    print('luci-app-weechat is not installed; no patch needed')
    sys.exit(0)
text = path.read_text(encoding='utf-8')
# The cycle is: luci-app-weechat -> weechat-full -> weechat-minimal
# -> luci-app-weechat, when a generic +weechat resolves ambiguously.
pattern = r'(?m)^(\s*LUCI_DEPENDS\s*:=.*?)(\+weechat)(?=\s|$)'
updated, count = re.subn(pattern, r'\1+weechat-full', text)
if count == 0:
    if '+weechat-full' in text:
        print('WeeChat dependency already points to weechat-full; unchanged')
    else:
        print('No matching generic WeeChat dependency found; unchanged')
    sys.exit(0)
if count != 1:
    sys.exit(f'Unexpected number of WeeChat dependency matches: {count}; refusing patch')
path.write_text(updated, encoding='utf-8')
print('Patched one WeeChat LuCI dependency to avoid recursive Kconfig dependency')
