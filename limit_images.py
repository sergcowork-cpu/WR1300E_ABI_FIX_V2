#!/usr/bin/env python3
"""Filter built images to WR1300E v2 WITHOUT altering kernel Kconfig selection.

Keep all official buildbot DEVICE symbols and all kmod selections in .config.
Only alter include/image.mk's image-level DEVICE_CHECK_PROFILE predicate.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    sys.exit('Usage: limit_images.py /path/to/openwrt/include/image.mk')
p = Path(sys.argv[1])
s = p.read_text()
original = 'DEVICE_CHECK_PROFILE = $(CONFIG_TARGET_$(if $(CONFIG_TARGET_MULTI_PROFILE),DEVICE_)$(call target_conf,$(BOARD)_$(SUBTARGET))_$(1))'
restricted = ('DEVICE_CHECK_PROFILE = $(if $(filter $(1),DEVICE_cudy_wr1300e-v2 cudy_wr1300e-v2),'
              '$(CONFIG_TARGET_$(if $(CONFIG_TARGET_MULTI_PROFILE),DEVICE_)'
              '$(call target_conf,$(BOARD)_$(SUBTARGET))_$(1)))')
if s.count(original) != 1:
    sys.exit('Image-filter insertion point missing or changed; refusing to patch OpenWrt')
p.write_text(s.replace(original, restricted, 1))
print('Restricted IMAGE TARGETS to cudy_wr1300e-v2; complete Kconfig remains unchanged')
