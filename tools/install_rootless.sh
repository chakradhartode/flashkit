#!/data/data/com.termux/files/usr/bin/bash
# Install the community termux-adb/termux-fastboot binaries for OTG USB access without root.
# The upstream repository's helper uses wget; use curl here to avoid wget/linker issues.
set -euo pipefail
say(){ printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die(){ printf '\033[1;31m!! %s\033[0m\n' "$*" >&2; exit 1; }
case "${PREFIX:-}" in *com.termux*) ;; *) die "Run this script inside the Termux app." ;; esac

say "Checking Termux:API command package"
pkg update -y
pkg install -y curl gnupg termux-api

REPO_DIR="$PREFIX/etc/apt/sources.list.d"
KEY_DIR="$PREFIX/etc/apt/keyrings"
mkdir -p "$REPO_DIR" "$KEY_DIR"
KEY_RAW="$KEY_DIR/nohajc.download"
KEY_TMP="$KEY_DIR/nohajc.gpg.tmp"
curl -fL --retry 3 --connect-timeout 15 https://nohajc.github.io/nohajc.gpg -o "$KEY_RAW" \
  || die "Could not download the rootless USB repository signing key. Check internet and retry."
[ -s "$KEY_RAW" ] || die "The repository signing key download was empty."
# APT expects a binary OpenPGP keyring with a .gpg suffix. Convert ASCII-armored input safely.
if head -c 32 "$KEY_RAW" | grep -q 'BEGIN PGP PUBLIC KEY BLOCK'; then
  gpg --batch --yes --dearmor --output "$KEY_TMP" "$KEY_RAW" \
    || die "The downloaded repository key could not be decoded."
else
  cp "$KEY_RAW" "$KEY_TMP"
fi
rm -f "$KEY_RAW"
gpg --batch --show-keys "$KEY_TMP" >/dev/null 2>&1 \
  || die "The downloaded repository key is not a valid OpenPGP key file."
mv "$KEY_TMP" "$KEY_DIR/nohajc.gpg"
printf '%s\n' "deb [signed-by=$KEY_DIR/nohajc.gpg] https://nohajc.github.io termux extras" > "$REPO_DIR/termux-adb.list"

say "Refreshing package indexes and installing rootless adb/fastboot"
apt update
pkg install -y termux-adb

command -v termux-adb >/dev/null 2>&1 || die "termux-adb package installed but command is missing."
command -v termux-fastboot >/dev/null 2>&1 || die "termux-fastboot command is missing; check the repository package list."
command -v termux-usb >/dev/null 2>&1 || die "termux-usb is missing. Reinstall termux-api and the matching Termux:API Android app."

say "Rootless USB backend is ready"
printf '  termux-adb: %s\n' "$(command -v termux-adb)"
printf '  termux-fastboot: %s\n' "$(command -v termux-fastboot)"
printf '\nConnect the target and approve Android USB permission prompts when they appear.\n'
