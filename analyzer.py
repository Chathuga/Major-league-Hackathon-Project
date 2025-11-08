import os
import google.generativeai as genai
import json
from cache_manager import load_file_map, save_file_map, save_key_reduce
from dotenv import load_dotenv
from PIL import Image
import fitz  # PyMuPDF
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

# Get secret API KEY
load_dotenv()
API_KEY = os.environ.get('APIKEY')
if not API_KEY:
    raise ValueError(".env file not found, please create one.")

# Configure Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')


# Calls Gemini to categorize content based Strictly on the allowed_keys fed in config
def analyze_file_with_gemini(file_path, content, allowed_keys):

    # Determine file type
    file_ext = os.path.splitext(file_path)[1].lower()

    # Image files - use vision API
    if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        try:
            # Open image using Pillow to validate and potentially convert
            img = Image.open(io.BytesIO(content))

            prompt = f"""
            You are a rigid file classifier. Analyze this image and match it to THESE allowed keys strictly: {json.dumps(allowed_keys)}.
            Rules:
            1. Output ONLY a JSON list of strings, e.g., ["pets", "dog"].
            2. If no keys match, output [].
            3. Look for: objects, animals, text, diagrams, charts, documents, receipts, etc.
            """

            # Send image directly to Gemini vision
            response = model.generate_content([prompt, img])
            cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned_text)

        except Exception as e:
            print(f"Image processing error on {file_path}: {e}")
            return []

    # PDF files - extract text
    elif file_ext == '.pdf':
        try:
            pdf_document = fitz.open(stream=content, filetype="pdf")

            # Convert PDF pages to images
            pdf_images = []
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                # Render page to image at 2x resolution for better quality
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                # Convert to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                pdf_images.append(img)

            pdf_document.close()

            prompt = f"""
            You are a rigid file classifier. Analyze this PDF document (converted to images) and match it to THESE allowed keys strictly: {json.dumps(allowed_keys)}.
            Rules:
            1. Output ONLY a JSON list of strings, e.g., ["finance", "work-project"].
            2. If no keys match, output [].
            3. Analyze all pages - look for: text, images, diagrams, charts, tables, receipts, forms, etc.
            4. Consider both visual elements and text content.
            """

            # Send all page images to Gemini vision API
            content_parts = [prompt] + pdf_images
            response = model.generate_content(content_parts)
            cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned_text)

        except Exception as e:
            print(f"PDF processing error on {file_path}: {e}")
            return []

    # Text files - decode and send as text
    else:
        try:
            text_content = content.decode('utf-8', errors='ignore')

            prompt = f"""
            You are a rigid file classifier. match the following text to THESE allowed keys strictly: {json.dumps(allowed_keys)}.
            Rules:
            1. Output ONLY a JSON list of strings, e.g., ["finance", "work-project"].
            2. If no keys match, output [].

            Text content (truncated):
            {text_content[:4000]}
            """

            response = model.generate_content(prompt)
            cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned_text)

        except Exception as e:
            print(f"Text processing error on {file_path}: {e}")
            return []



def process_single_file(file_path, file, mtime, allowed_keys):
    """Helper function to process a single file (runs in thread)"""
    with open(file_path, 'rb') as f:
        content = f.read()

    keys = analyze_file_with_gemini(file_path, content, allowed_keys)
    keys.sort()
    return keys


def run_analysis_pipeline(target_folder, allowed_keys, progress_data=None, max_workers=3):
    """
    Phase 1: The 'MAP' Phase (Scanning & tagging individual files)
    """
    file_map = load_file_map()
    files_to_process = []

    # First, collect all files that need processing
    for root, _, files in os.walk(target_folder):
        for file in files:
            file_path = os.path.abspath(os.path.join(root, file))
            mtime = os.path.getmtime(file_path)

            # Check Cache: File must exist in map AND have same modification time
            cached_data = file_map.get(file_path)
            if cached_data and cached_data.get('mtime') == mtime:
                continue  # Skip if unchanged

            files_to_process.append((file_path, file, mtime))

    # Update total count in progress tracker
    if progress_data is not None:
        progress_data["total"] = len(files_to_process)
        progress_data["completed"] = 0

    # Process files in parallel using ThreadPoolExecutor
    files_processed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {}

        for file_path, file, mtime in files_to_process:
            future = executor.submit(process_single_file, file_path, file, mtime, allowed_keys)
            future_to_file[future] = (file_path, file, mtime)

        for future in as_completed(future_to_file):
            file_path, file, mtime = future_to_file[future]
            try:
                keys = future.result()

                # Update the 'MAP' cache
                file_map[file_path] = {
                    "keys": keys,
                    "mtime": mtime,
                    "filename": file  # Store simple name for easier UI rendering later
                }
                files_processed += 1

                # Update progress tracker
                if progress_data is not None:
                    progress_data["completed"] = files_processed

                print(f"Analyzed: {file} -> {keys}")

            except Exception as e:
                print(f"Failed to process {file_path}: {e}")

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