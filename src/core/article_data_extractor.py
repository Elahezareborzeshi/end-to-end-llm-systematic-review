import os
import json
import time
import traceback
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.text_splitter import CharacterTextSplitter

def load_article_from_file(file_path):
    """
    Loads an article from a JSON file and returns a structured object.

    Args:
    file_path (str): Path to the JSON file containing the article data.

    Returns:
    dict: A dictionary containing structured information about the article.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            article_info = data['MedlineCitation']['Article']

            # Try to load full text if available
            full_text = ""
            full_text_path = file_path.replace('_source.json', '_full.txt')
            try:
                with open(full_text_path, 'r', encoding='utf-8') as full_text_file:
                    full_text = full_text_file.read()
            except Exception as e:
                pass  # Full text not available, which is fine
            
            # Handle cases where Abstract might be missing or in different formats
            abstract = ""
            if 'Abstract' in article_info:
                if isinstance(article_info['Abstract'], dict):
                    abstract = article_info['Abstract'].get('AbstractText', '')
                elif isinstance(article_info['Abstract'], str):
                    abstract = article_info['Abstract']
                elif isinstance(article_info['Abstract'], list):
                    # Sometimes abstracts are lists of structured parts
                    abstract = ' '.join([str(part) for part in article_info['Abstract']])
            
            # Handle ELocationID which might be missing or in different formats
            e_location = 'N/A'
            if 'ELocationID' in article_info:
                if isinstance(article_info['ELocationID'], list) and len(article_info['ELocationID']) > 0:
                    e_location = article_info['ELocationID'][0]
                elif isinstance(article_info['ELocationID'], str):
                    e_location = article_info['ELocationID']
            
            return {
                "Title": article_info.get('ArticleTitle', 'N/A'),
                "E-Location": e_location,
                "PMID": data['MedlineCitation'].get('PMID', 'N/A'),
                "Authors": ', '.join([f"{author.get('LastName', '')} {author.get('ForeName', '')}".strip() 
                                      for author in article_info.get('AuthorList', [])]) if 'AuthorList' in article_info else 'N/A',
                "Publication Date": article_info.get('Journal', {}).get('JournalIssue', {}).get('PubDate', {}).get('Year', 'N/A'),
                "Journal": article_info.get('Journal', {}).get('Title', 'N/A'),
                "Abstract": abstract,
                "Full Text": full_text
            }
    except Exception as e:
        print(f"Error loading article from {file_path}: {str(e)}")
        print(f"Stack trace: {traceback.format_exc()}")
        return None
    
def extract_article_data(directory_path, final_result_instructions):
    for filename in os.listdir(directory_path):
        if filename.endswith('_full.txt'):
            extract_single_article_data(filename, directory_path, final_result_instructions)

    print("Article data extraction completed.")

def extract_single_article_data(source_path, final_result_instructions):
    """
    Extract data from a single article, handling cases where full text might not be available.
    
    Args:
        source_path (str): Path to the source JSON file
        final_result_instructions (str): Instructions for data extraction
    """
    try:
        llm = ChatOpenAI(temperature=0.02, model_name="gpt-4o")
        embeddings = OpenAIEmbeddings()

        article_info = load_article_from_file(source_path)
        if not article_info:
            print(f"Could not load article info from {source_path}")
            return

        print(f"🐙 Analyzing article: {article_info['Title']}")

        # Check if full text is available
        full_text_path = source_path.replace('_source.json', '_full.txt')
        has_full_text = False
        analysis_text = ""
        
        try:
            with open(full_text_path, 'r', encoding='utf-8') as full_text_file:
                analysis_text = full_text_file.read()
                has_full_text = True
                content_type = "full text"
                print(f"✅ Using full text for analysis")
        except FileNotFoundError:
            # If full text is not available, use abstract as the content
            analysis_text = article_info['Abstract']
            has_full_text = False
            content_type = "abstract"
            print(f"⚠️ Full text not found, using abstract for analysis")
        except Exception as e:
            print(f"Error reading full text for {source_path}: {str(e)}")
            analysis_text = article_info['Abstract']
            has_full_text = False
            content_type = "abstract"
        
        if not analysis_text:
            print(f"❌ No content available for analysis in article {source_path}")
            return

        # Create a vector store from the text
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_text(analysis_text)
        vectorstore = FAISS.from_texts(texts, embedding=embeddings)

        # Extract information
        extracted_data = {
            "title": article_info['Title'],
            "has_full_text": has_full_text
        }

        # Create a retrieval QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever()
        )
        
        # Extract human-readable summary
        summarization_prompt = f"""
        Based on the {content_type} of the article, summarize it in a human-readable way. Follow these instructions:
        - What are the main findings relevant to the research question? Provide a list of key findings.
        - What are the key results? Include numerical values where available.
        - What is the method and study design? Include the type of study (e.g., RCT, cohort, case-control) and any key methodological details.
        - What are the inclusion and exclusion criteria? If applicable.
        - What is the intervention? If applicable.
        - What are the patient/population characteristics? Include sample size, age range, and any other relevant demographic information.
        - What are the main conclusions of the study? Provide a concise list.
        - What are the recommendations based on the study findings? If applicable.
        - What are the limitations of the study? List the main limitations, if applicable.
        - What are the exposures of interest and outcomes? If applicable. List them separately.
        
        Note: {'This summary is based on the full text of the article.' if has_full_text else 'This summary is based only on the abstract as full text was not available.'}
        """
        summarization_response = qa_chain.run(summarization_prompt)
        extracted_data["summarization"] = summarization_response

        # Process final result instructions
        final_result_prompt = f"""
        Based on the {content_type} of the article, try to extract the most important and summarization of each of these fields:
        {final_result_instructions}
        
        Follow these instructions:
        - Provide the results in a structured format suitable for a table, with clear labels for each piece of information extracted.
        - Avoid explanations, and only focus on raw data and most complete but simple phrases.
        - Return results in a JSON format with each field as a key.
        - If for any of the fields there are multiple values, it is OK to repeat all the other cells.
        - Make sure all values for all fields are covered.
        
        Note: {'This extraction is based on the full text of the article.' if has_full_text else 'This extraction is based only on the abstract as full text was not available.'}
        """
        final_result_response = qa_chain.run(final_result_prompt).replace("```json", '').replace("```", '')
        extracted_data["final_results"] = json.loads(final_result_response)

        # Save extracted data
        output_path = source_path.replace('_source.json', '_extracted.json')
        with open(output_path, 'w', encoding='utf-8') as out_file:
            json.dump(extracted_data, out_file, indent=2)

        print(f"✅ Extracted data saved to {output_path}")
        if not has_full_text:
            print("⚠️ Note: Analysis was performed using only the abstract as full text was not available")

    except Exception as e:
        print(f"❌ Error processing article {source_path}: {str(e)}")
        print(f"Stack trace: {traceback.format_exc()}")