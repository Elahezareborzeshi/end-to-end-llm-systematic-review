import os
import json
import requests
from PyPDF2 import PdfReader
import io
from metapub import FindIt

def download_articles_full_text(directory_path):
    for filename in os.listdir(directory_path):
        if filename.endswith('_source.json'):
            download_single_article_full_text(directory_path, filename)

def download_single_article_full_text(file_path):
    parts = os.path.splitext(file_path)
    base_filename = parts[0].split("_source")[0]
    directory_path = os.path.dirname(file_path)
    
    with open(file_path, 'r') as file:
        try:
            print(f"Downloading full text for {file_path}")
            data = json.load(file)
            pmid = data['MedlineCitation']['PMID']
            print(f" -> Found PMID: {pmid}")
            
            if pmid:
                src = FindIt(pmid)
                print(f" -> Title from PMA: {src.pma.title}")
                print(f" -> URL from PMA: {src.url}")

                # URL, if available, will be fulltext PDF
                if src.url:
                    print(f" -> Downloading full text for {src.url}")
                    response = requests.get(src.url, allow_redirects=True)
                    
                    if response.status_code == 200:
                        pdf_content = io.BytesIO(response.content)
                        try:
                            pdf_reader = PdfReader(pdf_content)
                            text_content = ""
                            for page in pdf_reader.pages:
                                text_content += page.extract_text()
                            
                            output_file = os.path.join(directory_path, f"{base_filename}_full.txt")
                            with open(output_file, 'w', encoding='utf-8') as out_file:
                                text_content = text_content.split("REFERENCES")[0]
                                out_file.write(text_content)
                            print(f"Successfully downloaded and extracted text for {base_filename}")
                            return text_content
                        except Exception as e:
                            failure_reason = f"Failed to extract text from PDF: {str(e)}"
                            create_failure_file(directory_path, base_filename, failure_reason)
                    else:
                        failure_reason = f"Failed to download PDF from {src.url} \n Status code: {response.status_code} \n Response body: {response.text}"
                        create_failure_file(directory_path, base_filename, failure_reason)
                else:
                    print(" -> Reason from PMA:")
                    # if no URL, reason is one of "PAYWALL", "TXERROR", or "NOFORMAT"
                    print(src.reason)
                    create_failure_file(directory_path, base_filename, f"Cannot download full text for PMID: {pmid} -> {src.reason}")
            else:
                failure_reason = "No PMC ID found for this article"
                print(f" -> No PMC ID found for {base_filename}")
                create_failure_file(directory_path, base_filename, failure_reason)
        except json.JSONDecodeError:
            failure_reason = "Unable to parse JSON file"
            create_failure_file(directory_path, base_filename, failure_reason)
        except Exception as e:
            failure_reason = f"Unexpected error: {str(e)}"
            create_failure_file(directory_path, base_filename, failure_reason)

def create_failure_file(directory_path, filename, reason):
    failure_file = os.path.join(directory_path, f"{os.path.splitext(filename)[0]}_failure.txt")
    with open(failure_file, 'w', encoding='utf-8') as f:
        f.write(reason)
    print(f"Created failure file for {filename}: {reason}")

# Example usage:
# download_articles_full_text('./data/downloaded_articles')