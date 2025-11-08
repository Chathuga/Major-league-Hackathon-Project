import json
import os
from pathlib import Path

CACHE_DIR = Path("./cache")
INPUT_DIR = Path("./input")
FILE_TO_KEY_PATH = CACHE_DIR / "file-to-key.json"
KEY_TO_FILE_PATH = CACHE_DIR / "key-to-file.json"
CONFIG = Path("./")

def init_cache():
    """Ensures cache directory and files exist."""
    if not CACHE_DIR.exists():
        os.makedirs(CACHE_DIR)
    if not INPUT_DIR.exists():
        os.makedirs(INPUT_DIR)
    if not FILE_TO_KEY_PATH.exists():
        write_json(FILE_TO_KEY_PATH, {})
    if not KEY_TO_FILE_PATH.exists():
        write_json(KEY_TO_FILE_PATH, {})
    if not CONFIG.exists():
        write_json(CONFIG, {
            "target_folder": "./input",
            "allowed_keys": []
            })


def read_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def clear_all_caches():
    #Overwrites both cache files with empty JSON objects.
    print("Clearing all caches...")
    write_json(FILE_TO_KEY_PATH, {})
    write_json(KEY_TO_FILE_PATH, {})


# --- Helper wrappers for specific files ---
def load_file_map(): return read_json(FILE_TO_KEY_PATH)
def save_file_map(data): write_json(FILE_TO_KEY_PATH, data)
def load_key_reduce(): return read_json(KEY_TO_FILE_PATH)
def save_key_reduce(data): write_json(KEY_TO_FILE_PATH, data)