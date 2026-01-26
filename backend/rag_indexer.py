import os
import time
import glob
import concurrent.futures
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)

def create_file_search_store():
    print("Creating File Search Store...")
    file_search_store = client.file_search_stores.create(
        config={'display_name': 'Optometry Wales Docs'}
    )
    print(f"Store created: {file_search_store.name}")
    return file_search_store

def upload_single_file(file_path, store_name):
    display_name = os.path.basename(file_path)
    print(f"Starting upload: {display_name}")
    
    try:
        # Upload and import directly to the store
        operation = client.file_search_stores.upload_to_file_search_store(
            file=file_path,
            file_search_store_name=store_name,
            config={
                'display_name': display_name
            }
        )
        
        # Wait for the operation to complete (blocks only this thread)
        while not operation.done:
            time.sleep(1)
            operation = client.operations.get(operation)
        
        print(f"✅ Successfully uploaded: {display_name}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to upload {display_name}: {e}")
        return False

def upload_files(store_name, files_dir):
    print(f"Scanning for files in {files_dir}...")
    # Get all files recursively
    files_to_upload = []
    for root, dirs, files in os.walk(files_dir):
        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue
            
            # Only upload relevant documents
            ext = os.path.splitext(file)[1].lower()
            if ext not in ['.md', '.pdf', '.docx', '.txt']:
                continue
            
            if file == 'core-hours.md':
                print(f"Skipping {file} due to known issues.")
                continue

            file_path = os.path.join(root, file)
            files_to_upload.append(file_path)

    print(f"Found {len(files_to_upload)} files.")
    print("Starting parallel upload with 10 workers...")
    
    # Use ThreadPoolExecutor for parallel uploads
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        futures = [executor.submit(upload_single_file, fp, store_name) for fp in files_to_upload]
        
        # Wait for all to complete
        concurrent.futures.wait(futures)
        
    print("All uploads processed.")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files_dir = os.path.join(base_dir, 'clean_knowledge')
    
    if not os.path.exists(files_dir):
        print(f"Error: Directory not found: {files_dir}")
        return

    # Create a new store
    store = create_file_search_store()
    
    # Upload files
    upload_files(store.name, files_dir)
    
    print("\n--- Indexing Complete ---")
    print(f"Store Name (Save this for the chat script): {store.name}")
    
    # Save store name to a file for easy access by the chat script
    config_path = os.path.join(os.path.dirname(__file__), 'rag_config.txt')
    with open(config_path, 'w') as f:
        f.write(store.name)
    print(f"Store name saved to {config_path}")

if __name__ == "__main__":
    main()