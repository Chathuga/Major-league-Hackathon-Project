import os
import google.generativeai as genai
import json
from cache_manager import load_file_map, save_file_map, save_key_reduce

# Configure Gemini
genai.configure(api_key="AIzaSyALzWY1ZFcEK2mAcLJ07fOCalnFfCLjkC0") 
model = genai.GenerativeModel('gemini-2.0-flash')

def analyze_file_with_gemini(file_path, content, allowed_keys):
    """Calls Gemini to categorize content based STRICTLY on allowed_keys."""
    prompt = f"""
    You are a rigid file classifier. match the following text to THESE allowed keys strictly: {json.dumps(allowed_keys)}.
    Rules:
    1. Output ONLY a JSON list of strings, e.g., ["finance", "work-project"].
    2. If no keys match, output [].
    
    Text content (truncated):
    {content[:4000]}
    """
    try:
        # Simple call for testing. In production, add retries/backoff.
        response = model.generate_content(prompt)
        cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Gemini Error on {file_path}: {e}")
        return []

def run_analysis_pipeline(target_folder, allowed_keys):
    """
    Phase 1: The 'MAP' Phase (Scanning & tagging individual files)
    """
    file_map = load_file_map()
    files_processed = 0

    for root, _, files in os.walk(target_folder):
        for file in files:
            file_path = os.path.abspath(os.path.join(root, file))
            mtime = os.path.getmtime(file_path)

            # Check Cache: File must exist in map AND have same modification time
            cached_data = file_map.get(file_path)
            if cached_data and cached_data.get('mtime') == mtime:
                continue # Skip if unchanged

            # It's new or changed, analyze it
            try:
                # (Simple text extraction for this test example)
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                
                keys = analyze_file_with_gemini(file_path, content, allowed_keys)
                # Sort keys immediately for consistency
                keys.sort()

                # Update the 'MAP' cache
                file_map[file_path] = {
                    "keys": keys,
                    "mtime": mtime,
                    "filename": file # Store simple name for easier UI rendering later
                }
                files_processed += 1
                print(f"Analyzed: {file} -> {keys}")

            except Exception as e:
                print(f"Failed to read {file_path}: {e}")

    # Save the updated MAP (file-to-key.json)
    save_file_map(file_map)
    return files_processed





def run_reduce_pipeline():
    """
    Phase 2: The 'REDUCE' Phase (Grouping by key)
    Transforms file-to-key.json INTO key-to-file.json
    """
    file_map = load_file_map()
    key_reduce = {}

    for file_path, data in file_map.items():
        current_keys = data['keys']
        
        # For every key this file has, add the file path to that key's list
        for key in current_keys:
            if key not in key_reduce:
                key_reduce[key] = []
            key_reduce[key].append(file_path)

    # Save the REDUCED data (key-to-file.json)
    save_key_reduce(key_reduce)
    print("Reduce phase complete.")