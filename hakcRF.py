#!/usr/bin/env python3
"""
Portapack H4M+ Comprehensive Firmware & Content Manager
========================================================
Zero-touch updater that installs firmware, themes, frequency databases,
and all available content for your Portapack device.

Features:
- Latest Mayhem firmware installation (with world map)
- Frequency database sync (generic + country-specific)
- Clean install with user data preservation
- Progress indicators and comprehensive logging
- Disk space verification
- Backup capability
"""

import requests
import os
import zipfile
import shutil
import sys
import logging
import argparse
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
MAYHEM_RELEASES_API = "https://api.github.com/repos/portapack-mayhem/mayhem-firmware/releases/latest"
FREQMAN_API = "https://api.github.com/repos/portapack-mayhem/mayhem-freqman-files/contents"
FREQMAN_RAW_BASE = "https://raw.githubusercontent.com/portapack-mayhem/mayhem-freqman-files/main"

SD_CARD_NAME = "PORTAPACK"
MOUNT_POINT = f"/Volumes/{SD_CARD_NAME}"
LOG_FILE = Path(__file__).parent / "portapack_updater.log"
STATE_FILE = Path(__file__).parent / ".updater_state.json"

# System folders to wipe during clean install (preserves user data)
SYSTEM_FOLDERS = ["pp_res", "firmware", "ADSB", "AIS", "hackrf", "APPS"]

# User folders to NEVER delete
USER_FOLDERS = ["CAPTURES", "RECORDINGS", "SCREENSHOTS", "LOGS", "DEBUG", "FREQMAN"]

# Minimum required space in MB
MIN_SPACE_MB = 700

# Country codes for frequency files
FREQ_COUNTRIES = [
    "Australia", "Belgium", "France", "India", "Norway",
    "Poland", "Romanian", "Slovakia", "Sweden", "USA", "WorldWide"
]

# ---------------------------------------------------------
# LOGGING SETUP
# ---------------------------------------------------------
def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

# ---------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------
class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    """Display the application banner"""
    banner = f"""{Colors.CYAN}
╔═══════════════════════════════════════════════════════════════╗
║  {Colors.BOLD}PORTAPACK MAYHEM - COMPREHENSIVE UPDATER{Colors.RESET}{Colors.CYAN}                    ║
║  Firmware • Themes • Frequencies • Everything                 ║
╚═══════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
    print(banner)

def print_status(msg: str, status: str = "info"):
    """Print colored status messages"""
    icons = {
        "info": f"{Colors.BLUE}[*]{Colors.RESET}",
        "success": f"{Colors.GREEN}[+]{Colors.RESET}",
        "warning": f"{Colors.YELLOW}[!]{Colors.RESET}",
        "error": f"{Colors.RED}[✗]{Colors.RESET}",
        "progress": f"{Colors.MAGENTA}[→]{Colors.RESET}"
    }
    print(f"{icons.get(status, icons['info'])} {msg}")

def get_disk_space(path: str) -> int:
    """Return available disk space in MB"""
    stat = os.statvfs(path)
    return (stat.f_bavail * stat.f_frsize) // (1024 * 1024)

def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def load_state() -> Dict[str, Any]:
    """Load persistent state from disk"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {}

def save_state(state: Dict[str, Any]):
    """Save persistent state to disk"""
    STATE_FILE.write_text(json.dumps(state, indent=2))

# ---------------------------------------------------------
# SD CARD OPERATIONS
# ---------------------------------------------------------
def find_sd_card() -> bool:
    """Detect if the SD card volume is mounted"""
    if os.path.exists(MOUNT_POINT) and os.path.isdir(MOUNT_POINT):
        logging.info(f"SD Card detected at: {MOUNT_POINT}")
        return True
    return False

def verify_disk_space() -> bool:
    """Ensure SD card has enough space"""
    available = get_disk_space(MOUNT_POINT)
    if available < MIN_SPACE_MB:
        print_status(f"Insufficient space: {available}MB available, {MIN_SPACE_MB}MB required", "error")
        return False
    print_status(f"Disk space OK: {available}MB available", "success")
    return True

def clean_system_folders():
    """Remove old system files while preserving user data"""
    print_status(f"Cleaning system folders on {SD_CARD_NAME}...", "progress")
    cleaned = 0
    for folder in SYSTEM_FOLDERS:
        target_path = os.path.join(MOUNT_POINT, folder)
        if os.path.exists(target_path):
            try:
                logging.info(f"Removing: {target_path}")
                shutil.rmtree(target_path)
                cleaned += 1
            except OSError as e:
                logging.error(f"Failed to clean {target_path}: {e}")
    print_status(f"Cleaned {cleaned} system folders", "success")

def create_backup(backup_dir: Optional[str] = None) -> Optional[str]:
    """Create a backup of important files"""
    if not backup_dir:
        backup_dir = os.path.join(
            os.path.expanduser("~"),
            "Desktop",
            f"PORTAPACK_BACKUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

    print_status(f"Creating backup at: {backup_dir}", "progress")
    os.makedirs(backup_dir, exist_ok=True)

    backed_up = 0
    for folder in USER_FOLDERS:
        src = os.path.join(MOUNT_POINT, folder)
        if os.path.exists(src):
            dst = os.path.join(backup_dir, folder)
            try:
                shutil.copytree(src, dst)
                backed_up += 1
                logging.info(f"Backed up: {folder}")
            except Exception as e:
                logging.warning(f"Could not backup {folder}: {e}")

    # Backup freqman files
    freqman_src = os.path.join(MOUNT_POINT, "FREQMAN")
    if os.path.exists(freqman_src):
        shutil.copytree(freqman_src, os.path.join(backup_dir, "FREQMAN"), dirs_exist_ok=True)

    print_status(f"Backed up {backed_up} user folders", "success")
    return backup_dir

# ---------------------------------------------------------
# DOWNLOAD OPERATIONS
# ---------------------------------------------------------
def download_with_progress(url: str, dest_path: str, desc: str = "Downloading") -> bool:
    """Download file with progress bar"""
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0

            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = int(100 * downloaded / total_size)
                        bar_len = 40
                        filled = int(bar_len * downloaded / total_size)
                        bar = '█' * filled + '░' * (bar_len - filled)
                        sys.stdout.write(f"\r{Colors.CYAN}{desc}: {bar} {pct}% ({format_size(downloaded)}/{format_size(total_size)}){Colors.RESET}")
                        sys.stdout.flush()

            print()  # newline after progress bar
            return True

    except requests.RequestException as e:
        logging.error(f"Download failed: {e}")
        return False

def fetch_github_release() -> Optional[Dict[str, Any]]:
    """Fetch latest release info from GitHub"""
    try:
        response = requests.get(MAYHEM_RELEASES_API, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"GitHub API error: {e}")
        return None

# ---------------------------------------------------------
# FIRMWARE INSTALLATION
# ---------------------------------------------------------
def install_firmware(include_world_map: bool = True):
    """Download and install the latest Mayhem firmware"""
    print_status("Fetching latest Mayhem firmware release...", "progress")

    release = fetch_github_release()
    if not release:
        print_status("Failed to fetch release info from GitHub", "error")
        return False

    version = release.get('tag_name', 'Unknown')
    print_status(f"Latest version: {Colors.GREEN}{version}{Colors.RESET}", "info")

    # Find the right asset
    assets = release.get('assets', [])
    target_asset = None

    for asset in assets:
        name = asset['name']
        if "COPY_TO_SDCARD" in name:
            if include_world_map and "no-world-map" not in name:
                target_asset = asset
                break
            elif not include_world_map and "no-world-map" in name:
                target_asset = asset
                break

    if not target_asset:
        print_status("Could not find firmware asset", "error")
        return False

    # Create staging directory
    staging_dir = Path(__file__).parent / "staging_tmp"
    staging_dir.mkdir(exist_ok=True)

    zip_path = staging_dir / target_asset['name']
    download_url = target_asset['browser_download_url']

    print_status(f"Downloading: {target_asset['name']} ({format_size(target_asset['size'])})", "info")

    if not download_with_progress(download_url, str(zip_path), "Firmware"):
        return False

    logging.info(f"Download complete: {zip_path}")

    # Clean old system files
    clean_system_folders()

    # Extract to SD card
    print_status("Extracting firmware to SD card...", "progress")
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            members = z.namelist()
            total = len(members)
            for i, member in enumerate(members):
                # Security: skip suspicious paths
                if member.startswith("/") or ".." in member:
                    logging.warning(f"Skipping suspicious path: {member}")
                    continue
                z.extract(member, MOUNT_POINT)
                if (i + 1) % 50 == 0 or i == total - 1:
                    pct = int(100 * (i + 1) / total)
                    sys.stdout.write(f"\r{Colors.CYAN}Extracting: {pct}% ({i+1}/{total} files){Colors.RESET}")
                    sys.stdout.flush()
        print()
        print_status("Firmware extraction complete", "success")

    except zipfile.BadZipFile:
        print_status("Downloaded file is corrupted", "error")
        return False
    except Exception as e:
        print_status(f"Extraction failed: {e}", "error")
        return False
    finally:
        # Cleanup staging
        try:
            shutil.rmtree(staging_dir)
            logging.info("Staging directory cleaned up")
        except:
            pass

    # Update state
    state = load_state()
    state['last_firmware_version'] = version
    state['last_firmware_update'] = datetime.now().isoformat()
    save_state(state)

    return True

# ---------------------------------------------------------
# FREQUENCY DATABASE OPERATIONS
# ---------------------------------------------------------
def fetch_freqman_file_list(path: str = "") -> List[Dict[str, Any]]:
    """Fetch list of files from freqman repository"""
    url = f"{FREQMAN_API}/{path}" if path else FREQMAN_API
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch freqman list: {e}")
        return []

def download_freqman_file(path: str, dest_dir: str) -> bool:
    """Download a single freqman file"""
    url = f"{FREQMAN_RAW_BASE}/{path}"
    filename = os.path.basename(path)
    dest_path = os.path.join(dest_dir, filename)

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        logging.warning(f"Failed to download {path}: {e}")
        return False

def install_frequency_databases(countries: Optional[List[str]] = None):
    """Download and install frequency databases"""
    print_status("Installing frequency databases...", "progress")

    freqman_dir = os.path.join(MOUNT_POINT, "FREQMAN")
    os.makedirs(freqman_dir, exist_ok=True)

    installed = 0
    failed = 0

    # Install generic files
    print_status("Fetching generic frequency files...", "info")
    generic_files = fetch_freqman_file_list("generic")
    for item in generic_files:
        if item.get('type') == 'file' and item['name'].endswith(('.txt', '.TXT')):
            if download_freqman_file(f"generic/{item['name']}", freqman_dir):
                installed += 1
            else:
                failed += 1

    # Install country-specific files
    target_countries = countries if countries else FREQ_COUNTRIES

    for country in target_countries:
        print_status(f"Fetching {country} frequency files...", "info")
        country_files = fetch_freqman_file_list(f"country-specific/{country}")

        for item in country_files:
            if item.get('type') == 'file':
                if download_freqman_file(f"country-specific/{country}/{item['name']}", freqman_dir):
                    installed += 1
                else:
                    failed += 1

    print_status(f"Installed {installed} frequency files ({failed} failed)", "success" if failed == 0 else "warning")

    # Update state
    state = load_state()
    state['last_freqman_update'] = datetime.now().isoformat()
    state['freqman_countries'] = target_countries
    save_state(state)

    return installed > 0

# ---------------------------------------------------------
# COMPREHENSIVE INSTALL
# ---------------------------------------------------------
def install_everything(include_world_map: bool = True, freq_countries: Optional[List[str]] = None, backup: bool = False):
    """Perform a complete installation of all available content"""
    print_banner()
    logging.info("Starting comprehensive installation")

    # 1. Check SD card
    if not find_sd_card():
        print_status(f"SD Card '{SD_CARD_NAME}' not found at {MOUNT_POINT}", "error")
        print_status("Please insert your PORTAPACK SD card and ensure it's mounted", "warning")
        return False

    print_status(f"SD Card detected at {MOUNT_POINT}", "success")

    # 2. Verify disk space
    if not verify_disk_space():
        return False

    # 3. Optional backup
    if backup:
        create_backup()

    # 4. Install firmware (includes themes in pp_res)
    print(f"\n{Colors.BOLD}═══ FIRMWARE & THEMES ═══{Colors.RESET}")
    if not install_firmware(include_world_map):
        print_status("Firmware installation failed", "error")
        return False

    # 5. Install frequency databases
    print(f"\n{Colors.BOLD}═══ FREQUENCY DATABASES ═══{Colors.RESET}")
    install_frequency_databases(freq_countries)

    # 6. Final sync
    print(f"\n{Colors.BOLD}═══ FINALIZING ═══{Colors.RESET}")
    print_status("Syncing filesystem...", "progress")
    os.sync()

    # Summary
    print(f"""
{Colors.GREEN}{'═' * 50}
  INSTALLATION COMPLETE
{'═' * 50}{Colors.RESET}

{Colors.BOLD}What was installed:{Colors.RESET}
  ✓ Latest Mayhem firmware
  ✓ Theme resources (pp_res)
  ✓ World map data{"" if include_world_map else " (SKIPPED)"}
  ✓ ADSB & AIS databases
  ✓ Frequency manager files
  ✓ HackRF firmware

{Colors.BOLD}Next steps:{Colors.RESET}
  1. {Colors.YELLOW}Wait 30 seconds{Colors.RESET} for write buffers to flush
  2. {Colors.YELLOW}Safely eject{Colors.RESET} the SD card
  3. Insert into Portapack and power on
  4. Go to {Colors.CYAN}Options → Firmware Update{Colors.RESET} to flash new firmware

{Colors.GREEN}{'═' * 50}{Colors.RESET}
""")

    logging.info("Comprehensive installation completed successfully")
    return True

# ---------------------------------------------------------
# CLI INTERFACE
# ---------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Portapack Mayhem Comprehensive Updater",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      Install everything with defaults
  %(prog)s --no-world-map       Install without world map (smaller download)
  %(prog)s --firmware-only      Only update firmware
  %(prog)s --freq-only          Only update frequency databases
  %(prog)s --freq-only --countries USA Australia
                                Install specific country frequencies
  %(prog)s --backup             Create backup before installing
  %(prog)s --check              Check for updates without installing
        """
    )

    parser.add_argument('--no-world-map', action='store_true',
                        help="Download smaller firmware without world map")
    parser.add_argument('--firmware-only', action='store_true',
                        help="Only install firmware (skip frequencies)")
    parser.add_argument('--freq-only', action='store_true',
                        help="Only install frequency databases")
    parser.add_argument('--themes-only', action='store_true',
                        help="Only refresh pp_res themes folder")
    parser.add_argument('--countries', nargs='+',
                        choices=FREQ_COUNTRIES,
                        help="Specific countries for frequency files")
    parser.add_argument('--backup', action='store_true',
                        help="Create backup of user data before install")
    parser.add_argument('--check', action='store_true',
                        help="Check for updates without installing")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Enable verbose logging")

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Check mode - just show status
    if args.check:
        print_banner()
        release = fetch_github_release()
        if release:
            version = release.get('tag_name', 'Unknown')
            state = load_state()
            current = state.get('last_firmware_version', 'None')
            print_status(f"Latest available: {Colors.GREEN}{version}{Colors.RESET}", "info")
            print_status(f"Last installed: {Colors.YELLOW}{current}{Colors.RESET}", "info")
            if current != version:
                print_status("Update available!", "success")
            else:
                print_status("You're up to date", "success")
        return

    # Firmware only
    if args.firmware_only:
        print_banner()
        if not find_sd_card():
            print_status(f"SD Card '{SD_CARD_NAME}' not found", "error")
            sys.exit(1)
        if args.backup:
            create_backup()
        success = install_firmware(not args.no_world_map)
        sys.exit(0 if success else 1)

    # Frequencies only
    if args.freq_only:
        print_banner()
        if not find_sd_card():
            print_status(f"SD Card '{SD_CARD_NAME}' not found", "error")
            sys.exit(1)
        success = install_frequency_databases(args.countries)
        sys.exit(0 if success else 1)

    # Themes only (just pp_res from firmware)
    if args.themes_only:
        print_banner()
        if not find_sd_card():
            print_status(f"SD Card '{SD_CARD_NAME}' not found", "error")
            sys.exit(1)

        print_status("Refreshing themes (pp_res)...", "progress")

        release = fetch_github_release()
        if not release:
            print_status("Failed to fetch release", "error")
            sys.exit(1)

        # Find asset
        assets = release.get('assets', [])
        target = None
        for asset in assets:
            if "COPY_TO_SDCARD" in asset['name'] and "no-world-map" in asset['name']:
                target = asset  # Use smaller no-map version for themes
                break

        if not target:
            print_status("Could not find firmware asset", "error")
            sys.exit(1)

        print_status("Downloading and extracting themes...", "progress")
        try:
            with requests.get(target['browser_download_url'], stream=True, timeout=120) as r:
                r.raise_for_status()
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    # Only extract pp_res
                    theme_files = [f for f in z.namelist() if f.startswith("pp_res/")]

                    # Remove old themes
                    pp_res_path = os.path.join(MOUNT_POINT, "pp_res")
                    if os.path.exists(pp_res_path):
                        shutil.rmtree(pp_res_path)

                    for member in theme_files:
                        z.extract(member, MOUNT_POINT)

                    print_status(f"Extracted {len(theme_files)} theme files", "success")
        except Exception as e:
            print_status(f"Failed: {e}", "error")
            sys.exit(1)

        sys.exit(0)

    # Default: install everything
    success = install_everything(
        include_world_map=not args.no_world_map,
        freq_countries=args.countries,
        backup=args.backup
    )
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
