#!/usr/bin/env python3
"""Compare enabled Linux Kconfig options with the earlier V2 attempt.

This report is diagnostic; the official kernel configuration is NOT publicly
reconstructible from config.buildinfo alone. This tool never claims a match.
"""
from pathlib import Path
import hashlib
import json
import re
import sys

if len(sys.argv) != 4:
    sys.exit('Usage: compare_kconfig.py V2_CONFIG CURRENT_CONFIG REPORT_JSON')
old_path, new_path, out_path = map(Path, sys.argv[1:])
rx = re.compile(r'^(CONFIG_[A-Za-z0-9_]+)=([ym])$')
def read(path):
    lines = path.read_text(encoding='utf-8').splitlines()
    return {m.group(1): m.group(2) for line in lines if (m := rx.fullmatch(line))}
def sig(symbols):
    return hashlib.md5(('\n'.join(sorted(f'{k}={v}' for k,v in symbols.items()))+'\n').encode()).hexdigest()
old = read(old_path)
new = read(new_path)
changed = [dict(symbol=k, previous=old.get(k,'n'), current=new.get(k,'n'))
           for k in sorted(set(old)|set(new)) if old.get(k) != new.get(k)]
report = {
    'note': 'Differences vs V2 only; not a diff against the official Linux Kconfig',
    'v2_kconfig_hash': sig(old),
    'current_kconfig_hash': sig(new),
    'v2_enabled_options': len(old),
    'current_enabled_options': len(new),
    'changed_options_count': len(changed),
    'changed_options': changed,
}
out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('V2 Kconfig hash:', report['v2_kconfig_hash'])
print('Current Kconfig hash:', report['current_kconfig_hash'])
print('Enabled CONFIG_*=y/m changes vs V2:',len(changed))
print('Diagnostic report saved to',out_path)
if report['v2_kconfig_hash'] != 'c479569322c3e45f042ca22dd188c1ac':
    sys.exit('Reference V2 kernel config does not match archived V2 hash')
