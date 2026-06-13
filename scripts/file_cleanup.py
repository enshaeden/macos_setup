#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
import shutil
import argparse
import yaml
import logging
import re
from datetime import datetime
from pathlib import Path

# Setup logging
LOG_DIR = Path.home() / "Library/Logs/mac-setup"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "file_cleanup.log"),
        logging.StreamHandler()
    ]
)

def get_unique_path(path: Path) -> Path:
    """Returns a unique path by appending a suffix if the file already exists."""
    if not path.exists():
        return path
    
    counter = 1
    while True:
        new_path = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not new_path.exists():
            return new_path
        counter += 1

def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        logging.warning(f"Config not found at {config_path}, using defaults.")
        return {}
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def file_cleanup(folder_path: Path, config: dict, dry_run: bool = False):
    """Organizes files in the given folder based on rules in config.yaml."""
    if not folder_path.is_dir():
        logging.info(f"Skipping: {folder_path} (not a directory)")
        return

    logging.info(f"Processing: {folder_path}")
    
    routing = config.get("cleanup", {}).get("routing", {})
    ss_config = config.get("cleanup", {}).get("screenshots", {})
    
    files = [f for f in folder_path.iterdir() if f.is_file()]
    
    for file_path in files:
        try:
            # 1. Handle Screenshots
            if ss_config.get("enabled") and file_path.name.startswith("Screenshot"):
                dest_dir = Path(ss_config.get("dest")).expanduser()
                move_file(file_path, dest_dir, dry_run)
                continue

            # 2. Handle Routing by extension or regex
            moved = False
            for rule_name, rule in routing.items():
                # Check extensions
                if file_path.suffix.lower() in rule.get("extensions", []):
                    dest_dir = folder_path / rule.get("dest")
                    move_file(file_path, dest_dir, dry_run)
                    moved = True
                    break
                
                # Check regex
                pattern = rule.get("pattern")
                if pattern and re.search(pattern, file_path.name):
                    dest_dir = folder_path / rule.get("dest")
                    move_file(file_path, dest_dir, dry_run)
                    moved = True
                    break
            
            if moved:
                continue

            # 3. Default date-based organization
            stats = file_path.stat()
            creation_time = getattr(stats, "st_birthtime", stats.st_mtime)
            dt = datetime.fromtimestamp(creation_time)
            
            dest_dir = folder_path / dt.strftime("%Y") / dt.strftime("%m")
            move_file(file_path, dest_dir, dry_run)
                
        except Exception as e:
            logging.error(f"Error processing {file_path.name}: {e}")

def move_file(file_path: Path, dest_dir: Path, dry_run: bool):
    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
    
    dest_path = dest_dir / file_path.name
    unique_dest = get_unique_path(dest_path)
    
    if dry_run:
        logging.info(f"[DRY RUN] {file_path.name} -> {unique_dest}")
    else:
        logging.info(f"Moving: {file_path.name} -> {unique_dest}")
        shutil.move(str(file_path), str(unique_dest))

def main():
    parser = argparse.ArgumentParser(description="Organize files based on config.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done.")
    args = parser.parse_args()

    config = load_config()
    
    home = Path.home()
    folders = [Path(f).expanduser() for f in config.get("cleanup", {}).get("folders", [])]
    if not folders:
        folders = [home / "Desktop", home / "Downloads"]

    for folder in folders:
        file_cleanup(folder, config, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
