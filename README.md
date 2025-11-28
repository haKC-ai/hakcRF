# Portapack H4M+ Comprehensive Updater

Zero-touch firmware and content manager for your Portapack Mayhem device.

## Features

- **Latest Mayhem firmware** - Auto-fetches stable or nightly builds from GitHub
- **Nightly builds** - Get bleeding-edge features with `--nightly`
- **World map data** - Full GPS/map support (or skip with `--no-world-map`)
- **Frequency databases** - Generic + country-specific files from the community
- **Sample files & presets** - LED samples, OOK files, remotes, etc.
- **ADSB/AIS databases** - Aviation and maritime tracking data
- **User data preservation** - Never touches your captures, recordings, or custom files
- **Backup support** - Optional backup before updates
- **Update checking** - Check for new versions without installing

## Quick Start

```bash
# One-time setup
chmod +x installer.sh
./installer.sh

# Activate environment
source portapack_updater_env/bin/activate

# Install EVERYTHING (firmware + themes + frequencies + maps)
python3 hakcRF.py
```

## Usage

### Install Everything (Stable)
```bash
python3 hakcRF.py
```
Downloads and installs:
- Latest stable Mayhem firmware with world map (~570MB)
- All SD card resources (samples, presets, databases)
- Frequency databases for all countries

### Install Nightly Build
```bash
python3 hakcRF.py --nightly
```
Installs the latest nightly build with bleeding-edge features and bug fixes.

### Smaller Install (No World Map)
```bash
python3 hakcRF.py --no-world-map
```
Downloads the lighter firmware package (~210MB) without world map data.

### Firmware Only
```bash
python3 hakcRF.py --firmware-only
```
Just update the firmware, skip frequency files.

### Frequencies Only
```bash
python3 hakcRF.py --freq-only
```
Only download/update frequency database files.

### Specific Countries
```bash
python3 hakcRF.py --freq-only --countries USA Australia France
```
Available countries: Australia, Belgium, France, India, Norway, Poland, Romanian, Slovakia, Sweden, USA, WorldWide

### Create Backup First
```bash
python3 hakcRF.py --backup
```
Backs up your captures, recordings, screenshots, and freqman files to Desktop before updating.

### Check for Updates
```bash
python3 hakcRF.py --check
```
Shows latest stable and nightly versions vs. your last installed version.

```bash
python3 hakcRF.py --check --nightly
```
Check specifically for nightly updates.

### Verbose Mode
```bash
python3 hakcRF.py -v
```
Enable detailed logging output.

## What Gets Installed

| Folder | Contents |
|--------|----------|
| `FIRMWARE/` | Mayhem firmware binaries (.bin, .ppfw.tar) |
| `ADSB/` | Aircraft database |
| `AIS/` | Maritime vessel database |
| `APPS/` | External applications |
| `FREQMAN/` | Frequency manager presets |
| `GPS/` | GPS data files |
| `OSM/` | OpenStreetMap data (world map) |
| `SAMPLES/` | LED, RF sample files |
| `REMOTES/` | IR/RF remote codes |
| `SPLASH/` | Boot splash screens |
| `MACADDRESS/` | MAC address lookup database |
| ...and more | BLETX, SSTV, SUBGHZ, WAV, etc. |

## What's Preserved

Your personal data is **never deleted**:
- `CAPTURES/` - Signal captures
- `RECORDINGS/` - Audio recordings
- `SCREENSHOTS/` - Device screenshots
- `LOGS/` - Debug logs
- `FREQMAN/` - Custom frequency files (merged, not replaced)

## Requirements

- macOS (uses `/Volumes/PORTAPACK` mount point)
- Python 3.9+
- SD card named "PORTAPACK"
- ~700MB free space on SD card

## Logs

All operations are logged to `portapack_updater.log` for troubleshooting.

## Links

- [Mayhem Firmware](https://github.com/portapack-mayhem/mayhem-firmware)
- [Frequency Files](https://github.com/portapack-mayhem/mayhem-freqman-files)
- [Mayhem Wiki](https://github.com/portapack-mayhem/mayhem-firmware/wiki)
