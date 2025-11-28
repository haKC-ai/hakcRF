# Portapack H4M+ Comprehensive Updater

Zero-touch firmware and content manager for your Portapack Mayhem device.

## Features

- **Latest Mayhem firmware** - Auto-fetches from GitHub releases
- **World map data** - Full GPS/map support (or skip with `--no-world-map`)
- **Frequency databases** - Generic + country-specific files from the community
- **Theme resources** - Complete pp_res folder
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

### Install Everything (Default)
```bash
python3 hakcRF.py
```
Downloads and installs:
- Latest Mayhem firmware with world map (~570MB)
- All theme resources
- Frequency databases for all countries
- ADSB/AIS/HackRF data

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

### Themes Only
```bash
python3 hakcRF.py --themes-only
```
Only refresh the pp_res themes folder (uses smaller download).

### Create Backup First
```bash
python3 hakcRF.py --backup
```
Backs up your captures, recordings, screenshots, and freqman files to Desktop before updating.

### Check for Updates
```bash
python3 hakcRF.py --check
```
Shows latest available version vs. your last installed version.

### Verbose Mode
```bash
python3 hakcRF.py -v
```
Enable detailed logging output.

## What Gets Installed

| Folder | Contents |
|--------|----------|
| `firmware/` | Mayhem firmware binaries |
| `pp_res/` | Themes, fonts, UI resources |
| `ADSB/` | Aircraft database |
| `AIS/` | Maritime vessel database |
| `hackrf/` | HackRF firmware |
| `FREQMAN/` | Frequency manager presets |
| `APPS/` | External applications |

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
