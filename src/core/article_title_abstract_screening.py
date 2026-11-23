import json
import os
import time
from langchain_openai import ChatOpenAI

def filter_articles_based_on_title_and_abstract(directory_path, inclusion_criteria, exclusion_criteria=None):
    filtered_articles = []
    llm = ChatOpenAI(temperature=0.02, model_name="gpt-4o")

    for filename in os.listdir(directory_path):
        if filename.endswith('_source.json'):
            file_path = os.path.join(directory_path, filename)
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                    article_title = data['MedlineCitation']['Article']['ArticleTitle']
                    abstract_texts = data['MedlineCitation']['Article']['Abstract']['AbstractText']

                    prompt = f"""
                    Given the following article title and abstract, determine if it meets the inclusion criteria and does not meet the exclusion criteria (if provided).

                    Title: ###
                    {article_title}
                    ###

                    Abstract: ###
                    {abstract_texts}
                    ###

                    INCLUSION CRITERIA: ###
                    {inclusion_criteria}
                    ###

                    {"EXCLUSION CRITERIA: ###" if exclusion_criteria else ""}
                    {exclusion_criteria if exclusion_criteria else ""}
                    {"###" if exclusion_criteria else ""}

                    Please respond with only 'INCLUDE' if the article meets the inclusion criteria and does not meet any exclusion criteria, or 'EXCLUDE' if it does not meet the inclusion criteria or meets any exclusion criteria.
                    Explain the reason for your decision after the 'INCLUDE' or 'EXCLUDE' keyword.
                    """

                    print(f" - 🔍 Screening: {article_title}")
                    print(prompt)
                    response = llm.invoke(prompt)
                    time.sleep(10)
                    print(f" - 💬 Response: {response.content}")
                    
                    if response.content.strip().upper().find('INCLUDE') != -1:
                        print(f" - ✅ Included: {filename}")
                        filtered_articles.append(file_path)
                    else:
                        print(f" - ❌ Excluded: {filename}")
                        os.remove(file_path)

                except json.JSONDecodeError:
                    print(f"Error: Unable to parse JSON in {file_path}")
                except KeyError as e:
                    print(f"Error: Missing key {e} in {file_path}")

    return filtered_articles
