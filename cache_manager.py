import json
import os
from pathlib import Path

CACHE_DIR = Path("./cache")
INPUT_DIR = Path("./input")
FILE_TO_KEY_PATH = CACHE_DIR / "file-to-key.json"
KEY_TO_FILE_PATH = CACHE_DIR / "key-to-file.json"
CONFIG_FILE_PATH = Path("./config.json")
DEFAULT_CONFIG = {
    "target_folder": "./input",
    "allowed_keys": ["example"]
}

# makes sure all the paths and cache files are set up and ready for use
def init_cache():
    if not CACHE_DIR.exists():
        os.makedirs(CACHE_DIR)
    if not INPUT_DIR.exists():
        os.makedirs(INPUT_DIR)
    if not FILE_TO_KEY_PATH.exists():
        write_json(FILE_TO_KEY_PATH, {})
    if not KEY_TO_FILE_PATH.exists():
        write_json(KEY_TO_FILE_PATH, {})
    if not CONFIG_FILE_PATH.exists():
        write_json(CONFIG_FILE_PATH, DEFAULT_CONFIG)

#checks cache before clearing
def check_for_cache():
    if not CACHE_DIR.exists():
        return False
    if not INPUT_DIR.exists():
        return False
    if not FILE_TO_KEY_PATH.exists():
        return False
    if not KEY_TO_FILE_PATH.exists():
        return False
    if not CONFIG_FILE_PATH.exists():
        return False
    return True


#For reading the json files
def read_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

#For storing/writing into the json files
def write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


#Overwrites both cache files with empty JSON objects.
def clear_all_caches():
    print("Clearing all caches...")
    write_json(FILE_TO_KEY_PATH, {})
    write_json(KEY_TO_FILE_PATH, {})


# --- Helper wrappers for specific files ---
def load_file_map(): 
    return read_json(FILE_TO_KEY_PATH)

def save_file_map(data): 
    write_json(FILE_TO_KEY_PATH, data)

def load_key_reduce(): 
    return read_json(KEY_TO_FILE_PATH)

def save_key_reduce(data): 
    write_json(KEY_TO_FILE_PATH, data)