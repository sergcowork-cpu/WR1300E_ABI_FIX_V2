#!/usr/bin/env python3
"""Add a Cudy WR1300E v2 device profile to the pinned OpenWrt release."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    sys.exit('Usage: apply_wr1300e.py PATH_TO_OPENWRT_SOURCE')
root = Path(sys.argv[1]).resolve()
kit = Path(__file__).resolve().parent
mk = root / 'target/linux/ramips/image/mt7621.mk'
network = root / 'target/linux/ramips/mt7621/base-files/etc/board.d/02_network'
common = root / 'target/linux/ramips/dts/mt7621_cudy_wr1300-v2v3.dtsi'
dst = root / 'target/linux/ramips/dts/mt7621_cudy_wr1300e-v2.dts'
src = kit / 'device/mt7621_cudy_wr1300e-v2.dts'
for f in [mk, network, common, src]:
    if not f.is_file():
        sys.exit(f'Missing required file: {f}')
common_text = common.read_text()
for anchor in ('partition@50000', 'reg = <0x50000 0xf80000>', 'eeprom_factory_8000', '&switch0'):
    if anchor not in common_text:
        sys.exit(f'Unexpected upstream DTSI, missing: {anchor}')
if dst.exists() and dst.read_bytes() != src.read_bytes():
    sys.exit('Refusing to overwrite a different upstream device tree')
makefile = mk.read_text()
nettext = network.read_text()
if 'TARGET_DEVICES += cudy_wr1300e-v2' not in makefile and makefile.count('define Device/cudy_wr1300-v2\n') != 1:
    sys.exit('Device insertion point missing in mt7621.mk')
if 'cudy,wr1300e-v2|\\' not in nettext and nettext.count('glinet,gl-mt1300|\\') != 1:
    sys.exit('Network insertion point missing in 02_network')
block = '''define Device/cudy_wr1300e-v2
  $(Device/dsa-migration)
  IMAGE_SIZE := 15872k
  DEVICE_VENDOR := Cudy
  DEVICE_MODEL := WR1300E
  DEVICE_VARIANT := v2
  DEVICE_PACKAGES := kmod-mt7603 kmod-mt7615e kmod-mt7663-firmware-ap \\
    -uboot-envtools
  SUPPORTED_DEVICES += cudy,wr1300e R60
endef
TARGET_DEVICES += cudy_wr1300e-v2
'''
if 'TARGET_DEVICES += cudy_wr1300e-v2' not in makefile:
    makefile = makefile.replace('define Device/cudy_wr1300-v2\n', block + '\ndefine Device/cudy_wr1300-v2\n', 1)
    mk.write_text(makefile)
if 'cudy,wr1300e-v2|\\' not in nettext:
    nettext = nettext.replace('glinet,gl-mt1300|\\', 'cudy,wr1300e-v2|\\\n\tglinet,gl-mt1300|\\', 1)
    network.write_text(nettext)
dst.write_bytes(src.read_bytes())
print('WR1300E v2 device profile applied; hardware validation NOT performed')
