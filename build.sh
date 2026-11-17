#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SRC="${OPENWRT_DIR:-$HERE/openwrt}"
VERSION=25.12.6
BASE="https://downloads.openwrt.org/releases/$VERSION/targets/ramips/mt7621"
EXPECTED_CONFIG_SHA256=a806cbb8394c4014cae202faabb9914bbc058b22b0ee1c0cc3bbbe307d2b5a5b

if [ ! -d "$SRC/.git" ]; then
    git clone --depth 1 --branch "v$VERSION" https://github.com/openwrt/openwrt.git "$SRC"
fi
if [ "$(git -C "$SRC" describe --tags --exact-match HEAD 2>/dev/null || true)" != "v$VERSION" ]; then
    echo "ERROR: wrong OpenWrt source revision, expected v$VERSION" >&2
    exit 1
fi
python3 "$HERE/apply_wr1300e.py" "$SRC"
cd "$SRC"

# Kernel .vermagic hashes the ACTUAL Linux CONFIG_*=y/m options.
# CONFIG_ALL_KMODS=y can only reproduce the official buildbot module selection
# when ALL pinned feeds are *installed*, not merely downloaded. V2 installed
# 5 packages; that omitted many optional kmod definitions and dependencies.
./scripts/feeds update -a
for d in feeds/*; do
    if [ -d "$d/.git" ]; then
        printf '%s %s\n' "${d#feeds/}" "$(git -C "$d" rev-parse HEAD)"
    fi
done > "$HERE/feeds-revisions.txt"
./scripts/feeds install -a 2>&1 | tee "$HERE/feeds-install.log"
python3 "$HERE/fix_weechat.py" "$SRC"
find package/feeds -type l | LC_ALL=C sort > "$HERE/installed-feed-package-links.txt"
printf 'Installed feed package links: '
wc -l < "$HERE/installed-feed-package-links.txt"

curl --fail --location --retry 3 --silent --show-error \
    "$BASE/config.buildinfo" -o "$HERE/official_config.buildinfo"
echo "$EXPECTED_CONFIG_SHA256  $HERE/official_config.buildinfo" | sha256sum --check --status || {
    echo 'ERROR: official config.buildinfo checksum changed; review before building' >&2
    exit 1
}
python3 "$HERE/create_config.py" "$HERE/official_config.buildinfo" .config
make defconfig 2>&1 | tee "$HERE/defconfig.log"

# Keep the FULL official buildbot recipe; keep the package-style custom device.
for entry in \
    'CONFIG_TARGET_MULTI_PROFILE=y' \
    'CONFIG_TARGET_ALL_PROFILES=y' \
    'CONFIG_TARGET_DEVICE_ramips_mt7621_DEVICE_cudy_wr1300e-v2=y' \
    'CONFIG_ALL_KMODS=y' \
    'CONFIG_ALL_NONSHARED=y' \
    'CONFIG_BUILDBOT=y' \
    'CONFIG_TARGET_PER_DEVICE_ROOTFS=y' \
    'CONFIG_COLLECT_KERNEL_DEBUG=y' \
    'CONFIG_KERNEL_BUILD_USER="builder"' \
    'CONFIG_KERNEL_BUILD_DOMAIN="buildhost"' \
    'CONFIG_PACKAGE_luci=y'; do
    if ! grep -Fqx "$entry" .config; then
        echo "ERROR: required official buildbot configuration lost: $entry" >&2
        exit 1
    fi
done
if grep -Eq '^CONFIG_TARGET_ramips_mt7621_DEVICE_cudy_wr1300e-v2=y$' .config; then
    echo 'ERROR: switched to one-device choice; this changes buildbot Kconfig' >&2
    exit 1
fi
if grep -Eq '^CONFIG_PACKAGE_(kmod-amneziawg|amneziawg-tools|pbr|luci-app-pbr|podkop|easytier)=y$' .config; then
    echo 'ERROR: unsupported VPN/PBR package selected in image' >&2
    exit 1
fi
cp .config "$HERE/effective.config"

# Build kernel first and report ABI mismatch BEFORE full image/package phase.
# Do not alter OpenWrt image makefiles until the ABI check succeeds.
# Explicitly build host tools and cross-toolchain before the kernel target.
make download -j4
make -j2 tools/install V=s
make -j2 toolchain/install V=s
make -j2 target/linux/compile V=s
mapfile -t VERMAGIC_FILES < <(find build_dir -type f -path "*/linux-6.12.112/.vermagic" -print)
# The kernel version (6.12.112) and exact location are checked below.
if [ "${#VERMAGIC_FILES[@]}" -ne 1 ]; then
    mapfile -t VERMAGIC_FILES < <(find build_dir -type f -name .vermagic -print)
fi
if [ "${#VERMAGIC_FILES[@]}" -ne 1 ]; then
    printf 'ERROR: expected one kernel .vermagic; found %s\n' "${#VERMAGIC_FILES[@]}" >&2
    printf '%s\n' "${VERMAGIC_FILES[@]}" >&2
    exit 1
fi
VERMAGIC_FILE="${VERMAGIC_FILES[0]}"
cp "$VERMAGIC_FILE" "$HERE/kernel-vermagic.txt"
if [ -f "$(dirname "$VERMAGIC_FILE")/.config.set" ]; then
    cp "$(dirname "$VERMAGIC_FILE")/.config.set" "$HERE/kernel-config.set"
    python3 "$HERE/compare_kconfig.py" \
        "$HERE/reference/v2-kernel-config.set" \
        "$HERE/kernel-config.set" \
        "$HERE/kernel-kconfig-diff-v2.json"
fi
python3 "$HERE/check_early_abi.py" "$VERMAGIC_FILE" "$HERE/early-abi-result.json"

# Restrict IMAGE OUTPUTS only after proving the official kernel ABI.
# The package selections stay untouched (ALL_KMODS / ALL_NONSHARED).
python3 "$HERE/limit_images.py" "$SRC/include/image.mk"
# Only if the kernel ABI matches, finish the image build.
make -j2 V=s
IMG_DIR="bin/targets/ramips/mt7621"
IMAGE=$(find "$IMG_DIR" -maxdepth 1 -type f -name '*cudy_wr1300e-v2*squashfs-sysupgrade.bin' -print -quit)
[ -n "$IMAGE" ] || { echo 'ERROR: sysupgrade image not created' >&2; exit 1; }
python3 "$HERE/verify_image.py" "$IMAGE"
python3 "$HERE/check_abi.py" "$IMG_DIR/profiles.json" "$HERE/abi-result.json"
sha256sum "$IMAGE" | tee "$HERE/firmware.sha256"
echo "IMAGE=$IMAGE"
echo 'DO NOT FLASH WITHOUT BACKUP AND BOARD VERIFICATION.'
