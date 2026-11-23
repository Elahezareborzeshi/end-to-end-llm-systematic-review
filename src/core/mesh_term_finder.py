import requests
import time
import xml.etree.ElementTree as ET
from config import config

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import CharacterTextSplitter

import re

def get_mesh_terms(keyword):
    """Get MeSH terms for a given keyword by first fetching the IDs and then fetching the details"""

    print(f"🔍 Getting mesh terms for '{keyword}'")

    ids = get_mesh_term_ids(keyword)

    if len(ids) == 0:
        print(f"No IDs found for '{keyword}'")
        return []

    print(f"🧩 IDs: {ids}")

    details = get_mesh_term_details(ids)
    print(f"🧩 Total details fetch: {len(details)}")

    all_terms = []
    seen_terms = set()  # Track exact duplicates
    
    for id, detail in details.items():
        main_term = extract_main_term(detail)
        main_term = re.sub(r'\[.*?\]', '', main_term)
        print(f"ID: {id}, Main Term: {main_term}")
        
        main_term_with_suffix = f"{main_term}[MeSH Terms]"
        if main_term_with_suffix not in seen_terms:
            all_terms.append(main_term_with_suffix)
            seen_terms.add(main_term_with_suffix)
            print(f"✅ Added main term: {main_term_with_suffix}")
        else:
            print(f"❌ Skipped duplicate main term: {main_term_with_suffix}")
        
        entry_terms = extract_entry_terms(detail)
        for term in entry_terms:
            print(f"ID: {id}, Entry Term: {term}")
            entry_term_with_suffix = f"{term}[Title/Abstract]"
            if entry_term_with_suffix not in seen_terms:
                all_terms.append(entry_term_with_suffix)
                seen_terms.add(entry_term_with_suffix)
                print(f"✅ Added entry term: {entry_term_with_suffix}")
            else:
                print(f"❌ Skipped duplicate entry term: {entry_term_with_suffix}")
        
        indexing_terms = extract_previous_indexing_terms(detail)
        for term in indexing_terms:
            print(f"ID: {id}, Indexing Term: {term}")
            indexing_term_with_suffix = f"{term}[Title/Abstract]"
            if indexing_term_with_suffix not in seen_terms:
                all_terms.append(indexing_term_with_suffix)
                seen_terms.add(indexing_term_with_suffix)
                print(f"✅ Added indexing term: {indexing_term_with_suffix}")
            else:
                print(f"❌ Skipped duplicate indexing term: {indexing_term_with_suffix}")
    
    print(f"🔍 Final terms count: {len(all_terms)}")
    return all_terms

def extract_main_term(detail):
    # Get the main term from first line, remove '1:' prefix if exists
    main_term = detail.strip().split('\n')[0].replace('1:', '').strip()
    return main_term
    

def get_mesh_term_ids(term, attempt=0):
    """ Search MeSH for a term and return MeSH IDs for each term """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        'db': 'mesh',
        'term': f"\"{term}\"[MeSH Terms]", # OR {term}[Text Word]
        'retmode': 'xml',
        'retmax': '10',
        'sort': 'relevance',
        'api_key': config.PUBMED_API_KEY
    }

    try:
        response = requests.get(base_url, params=params)
        root = ET.fromstring(response.content)
        ids = [id_elem.text for id_elem in root.findall('.//IdList/Id')]
        return ids
    except Exception as e:
        if attempt < 10:
            return get_mesh_term_ids(term, attempt + 1)
        else:
            return []

def get_mesh_term_details(mesh_ids, attempt=0):
    """ Fetch details of multiple MeSH terms using their IDs """
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    details_per_id = {}
    try:
        for mesh_id in mesh_ids:
            params = {
                'db': 'mesh',
                'id': mesh_id,
                'api_key': config.PUBMED_API_KEY
            }
            response = requests.get(fetch_url, params=params)
            
            if response.text.find('Error') > -1 or response.text.find('error') > -1:
                raise Exception(f"Error fetching details for {mesh_id}: {response.text}")
            
            details_per_id[mesh_id] = response.text
        return details_per_id
    except Exception as e:
        print(f"Error fetching details for {mesh_ids}: {e}")
        if attempt < 10:
            return get_mesh_term_details(mesh_ids, attempt + 1)
        else:
            return {}

def extract_entry_terms(text):
    # Find the Entry Terms section
    entry_terms_match = re.search(r'Entry Terms:(.*?)(?:\n\n|\Z)', text, re.DOTALL)
    
    if not entry_terms_match:
        return []  # Return an empty list if Entry Terms section is not found
    
    entry_terms_text = entry_terms_match.group(1).strip()
    
    # Split the entry terms and remove empty lines
    entry_terms = [term.strip() for term in entry_terms_text.split('\n') if term.strip()]
    
    return entry_terms

def extract_previous_indexing_terms(text):
    # Find the Previous Indexing section
    previous_indexing_match = re.search(r'Previous Indexing:(.*?)(?:\n\n|\Z)', text, re.DOTALL)
    
    if not previous_indexing_match:
        return []  # Return an empty list if Previous Indexing section is not found
    
    previous_indexing_text = previous_indexing_match.group(1).strip()
    
    # Split the terms and remove empty lines
    terms = [term.strip().split(' (')[0] for term in previous_indexing_text.split('\n') if term.strip()]
    
    return terms

def extract_mesh_categories(text):
    # Find the All MeSH Categories section
    mesh_categories_match = re.search(r'All MeSH Categories(.*?)(?:\Z)', text, re.DOTALL)
    
    if not mesh_categories_match:
        return []  # Return an empty list if All MeSH Categories section is not found
    
    mesh_categories_text = mesh_categories_match.group(1).strip()
    
    # Split the categories and remove empty lines
    categories = [line.strip() for line in mesh_categories_text.split('\n') if line.strip()]
    
    # Extract the bottom-most 3 levels
    if len(categories) >= 3:
        return categories[-3:]
    else:
        return categories  # Return all if there are fewer than 3 levels

def filter_mesh_terms_with_rag(grouped_terms, research_question):
    """Filter MeSH terms based on relevance to the research question using Langchain RAG."""

    all_terms_combined = ""
    for keyword, terms in grouped_terms.items():
        all_terms_combined += keyword + "\n" + "\n".join(terms) + "\n"
    
    # Prepare the data for RAG
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splitted_texts = text_splitter.split_text(all_terms_combined)

    # Create embeddings and vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(splitted_texts, embedding=embeddings)

    # Create conversation chain
    llm = ChatOpenAI(temperature=0.05, model_name="gpt-4o")
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )

    # Query the RAG system
    query = f"""
    Given the research question list all relevant MeSH terms?

    #### START OF RESEARCH QUESTION
    {research_question}
    #### END OF RESEARCH QUESTION

    - List the relevant scientific terms used for medical research.
    - Remove exact duplicates.
    - Only list the terms without any description or explanation, just the terms.
    - Keep suffixes like [MeSH Terms], [Title/Abstract] etc. without removing them.
    - List the terms separated by newline.
    """
    
    print(query)
    result = conversation_chain.invoke({"question": query})
    print("🔍 Filtering result:")
    print(result['answer'])
    time.sleep(10)
    filtered_terms = result['answer'].split('\n')

    # Clean up the filtered terms
    filtered_terms = [term.strip() for term in filtered_terms if term.strip()]

    return filtered_terms

def are_mesh_terms_relevant(grouped_terms, research_question):
    """Determine if the group of MeSH terms is relevant to the research question using Langchain RAG."""

    # Combine all terms into a single string
    all_terms_combined = ""
    for keyword, terms in grouped_terms.items():
        all_terms_combined += keyword + "\n" + "\n".join(terms) + "\n"
    
    # Prepare the data for RAG
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splitted_texts = text_splitter.split_text(all_terms_combined)

    # Create embeddings and vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(splitted_texts, embedding=embeddings)

    # Create conversation chain
    llm = ChatOpenAI(temperature=0.05, model_name="gpt-4")
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )

    # Query the RAG system
    query = f"""
    Given the following research question and group of MeSH terms, determine if the group is relevant to the research question.

    #### START OF RESEARCH QUESTION
    {research_question}
    #### END OF RESEARCH QUESTION

    #### START OF MESH TERMS
    {all_terms_combined}
    #### END OF MESH TERMS

    Please respond with 'RELEVANT' or 'IRRELEVANT' only.
    """
        
    print(query)
    result = conversation_chain.invoke({"question": query})
    print("🔍 Relevance result:")
    print(result['answer'])
    time.sleep(10)
    relevance = result['answer'].strip().upper()

    return relevance.find('IRRELEVANT') == -1

def print_mesh_terms(keyword, mesh_terms):
    """Print MeSH terms for a keyword."""
    print(f"MeSH terms for '{keyword}':")
    for term in mesh_terms:
        print(f"- {term}")
    print()