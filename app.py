from flask import Flask, render_template, jsonify
import json
from cache_manager import init_cache, load_file_map, load_key_reduce, clear_all_caches, check_for_cache, CONFIG_FILE_PATH
from analyzer import analysis, reduce

#Start flask app
app = Flask(__name__)

#Initialize caches
init_cache()

#If cache already exists then
if check_for_cache() == True:
    clear_all_caches()

#Load the main dashboard
@app.route('/')
def index():
    return render_template('index.html')

#start process
@app.route('/run')
def run_process():

    with open(CONFIG_FILE_PATH, 'r') as f:
        CONFIG = json.load(f)

    #reset cached files
    clear_all_caches()


    #Run Gemini Analysis and Map
    count = analysis(CONFIG['target_folder'], CONFIG['allowed_keys'])

    #Run Reduce (Grouping)
    reduce()

    return jsonify({"status": "complete", "newly_analyzed": count})


#For display on the website UI
@app.route('/data')
def get_ui_data():

    key_reduce = load_key_reduce()  # The grouped data
    file_map = load_file_map()      # The detailed data for each file

    #Final structure:
    ui_data = {}

    #Sort keys alphabetically for display
    sorted_genre_keys = sorted(key_reduce.keys())

    #Iterate through the list of keys
    for genre_key in sorted_genre_keys:
        #gets the list of file paths for the current key
        file_list_paths = key_reduce[genre_key]
        #creates an empty list of keys for storing the path
        ui_data[genre_key] = []

        #Iterates through all the files within the key list
        for file_path in file_list_paths:

            # Lookup details from the file map
            details = file_map.get(file_path)

            #inserts the file and its list to be shown on screen
            if details:
                ui_data[genre_key].append({
                    "name": details['filename'],
                    "all_keys": details['keys'] 
                })

    return jsonify(ui_data)



if __name__ == '__main__':
    app.run(debug=True)