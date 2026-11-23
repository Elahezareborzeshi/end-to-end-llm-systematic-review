import json
import os
import shutil

def deduplicate_articles(directory_path):
    articles = {}
    duplicates = []
    file_paths = []

    deleted_dir = os.path.join(directory_path, 'deleted_articles')
    os.makedirs(deleted_dir, exist_ok=True)

    # Get all .json files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith('_source.json'):
            file_paths.append(os.path.join(directory_path, filename))

    for file_path in file_paths:
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
                article_ids = set(id.lower() for id in data.get('PubmedData', {}).get('ArticleIdList', []))
                
                if article_ids:
                    is_duplicate = False
                    for existing_path, existing_ids in articles.items():
                        if article_ids & existing_ids:  # Check for any intersection
                            duplicates.append((existing_path, file_path))
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        articles[file_path] = article_ids
                else:
                    print(f"Warning: No ArticleIdList found in {file_path}")
            except json.JSONDecodeError:
                print(f"Error: Unable to parse JSON in {file_path}")

    print(f"🔍 Found {len(duplicates)} duplicates.")

    # Print and delete duplicates
    for original, duplicate in duplicates:
        print(f"Duplicate found: {duplicate} (original: {original})")
        try:
            destination = os.path.join(deleted_dir, os.path.basename(duplicate))
            shutil.move(duplicate, destination)
            print(f"Moved to: {destination}")
        except OSError as e:
            print(f"Error deleting {duplicate}: {e}")

    return len(duplicates)

