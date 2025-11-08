from flask import Flask, render_template, jsonify
import json
from cache_manager import init_cache, load_file_map, load_key_reduce, clear_all_caches
from analyzer import run_analysis_pipeline, run_reduce_pipeline

app = Flask(__name__)
init_cache()

# Load config once on startup
with open('config.json', 'r') as f:
    CONFIG = json.load(f)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/run')
def run_process():
    clear_all_caches()
    # 1. Run Map (Gemini Analysis)
    count = run_analysis_pipeline(CONFIG['target_folder'], CONFIG['allowed_keys'])
    # 2. Run Reduce (Grouping)
    run_reduce_pipeline()
    return jsonify({"status": "complete", "newly_analyzed": count})


@app.route('/data')
def get_ui_data():
    """
    Constructs the exact nested data structure requested for the UI.
    It needs BOTH JSON cache files to do this efficiently.
    """
    key_reduce = load_key_reduce()  # The grouped data
    file_map = load_file_map()      # The detailed data for each file

    # Final structure: { "finance": [ {name: "doc1.txt", all_keys: [...]}, ... ] }
    ui_data = {}

    # Sort keys alphabetically for display
    sorted_genre_keys = sorted(key_reduce.keys())

    for genre_key in sorted_genre_keys:
        file_list_paths = key_reduce[genre_key]
        ui_data[genre_key] = []

        for file_path in file_list_paths:
            # Lookup details from the file map
            details = file_map.get(file_path)
            if details:
                ui_data[genre_key].append({
                    "name": details['filename'],
                    # Requested format: needs ALL keys present for this file
                    "all_keys": details['keys'] 
                })

    return jsonify(ui_data)

if __name__ == '__main__':
    app.run(debug=True)