import json
import re  
import os
from dotenv import load_dotenv

# Load environment variables from .envdist file (one level up from src folder)
load_dotenv('../.env')

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import CharacterTextSplitter
from article_data_extractor import load_article_from_file
# Initialize OpenAI API (make sure to set your API key in the environment variables)
llm = ChatOpenAI(temperature=0.02, model_name="gpt-4o")
# llm = ChatOpenAI(temperature=0.02, model_name="gpt-3.5-turbo")
embeddings = OpenAIEmbeddings()

# Initialize an empty vector store
vector_store = FAISS.from_texts([""], embeddings)

# Initialize conversation memory
memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)

# Initialize conversation chain
conversation_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vector_store.as_retriever(),
    memory=memory
)

is_base_screening_info_set = False

global_research_question = ""

def set_base_screening_info(research_question):
    """
    Set the base screening information for the RAG system.
    
    :param research_question: String, the research question
    :param inclusion_criteria: String, the inclusion criteria
    :param exclusion_criteria: String, the exclusion criteria
    """

    global is_base_screening_info_set
    if is_base_screening_info_set:
        return
    is_base_screening_info_set = True

    print(f"Setting base screening info: {research_question}")

    # Create a text representation of the base screening information
    base_screening_info = f"""
    RESEARCH QUESTION: {research_question}
    """
    
    # # Add the base screening information to the vector store
    global vector_store
    vector_store.add_texts([base_screening_info])

    global global_research_question
    global_research_question = research_question
    
    print("Base screening information set successfully.")

def add_rag_example(article_path, decision, reason):
    """
    Add a new example to the RAG system.
    
    :param article: Dictionary containing article information
    :param decision: String, either 'include' or 'exclude'
    :param reason: String, the reason for the decision
    """
    article = load_article_from_file(article_path)
    # Create a text representation of the article
    article_text = f"""
    Title: {article['Title']}
    Abstract: {article['Abstract']}
    Publication Date: {article['Publication Date']}
    Decision: {decision.upper()}
    Reason: {reason}
    """
    # TODO add reasoning of the decision from user input
    
    # Add the example to the vector store
    global vector_store
    vector_store.add_texts([article_text])

    write_vector_store_to_file()
    
    print(f"Added new example to RAG system: {article['Title']} - Decision: {decision}")

def write_vector_store_to_file():
    global vector_store
    # Retrieve all documents from the vector store
    all_docs = vector_store.similarity_search("", k=vector_store.index.ntotal)
    
    # Write all documents to a file
    with open("data/vector_store.txt", "w", encoding="utf-8") as f:
        for doc in all_docs:
            f.write(f"Document: {doc.page_content}\n\n")
    
    print("Vector store contents written to data/vector_store.txt")

def rag_based_summary_screening(article_path, attempt=0):
    """
    Perform screening using RAG.
    
    :param article_path: String, path to the article file
    :return: Tuple of (decision, reason)
    """
    article = load_article_from_file(article_path)

    # if abstract is an array, join it into a single string
    if isinstance(article['Abstract'], list):
        abstract_text = "\n".join(article['Abstract'])
    else:
        abstract_text = article['Abstract']

    # Create a text representation of the article to be screened
    article_text = f"""
    <TITLE> 
    {article['Title']}
    </TITLE>
    
    <ABSTRACT> 
    {abstract_text}
    </ABSTRACT>

    <PUBLICATION_DATE> 
    {article['Publication Date']}
    </PUBLICATION_DATE>
    """

    global global_research_question

    # Prepare the query
    query = f"""
CRITICAL: You MUST respond with ONLY a JSON object. Do not include any other text.

Task: Decide whether to INCLUDE or EXCLUDE this article for a systematic review.

Research Question: {global_research_question}

Article:
{article_text}

Requirements:
- Base decision on title and abstract relevance to the research question
- Consider previous screening decisions if available

RESPOND WITH ONLY THIS JSON FORMAT (no other text):
{{
    "decision": "INCLUDE",
    "reason": "Brief explanation"
}}

OR

{{
    "decision": "EXCLUDE", 
    "reason": "Brief explanation"
}}

JSON Response:
"""

    print(f"QUERY: {query}")
    
    # Use the conversation chain to get a response
    result = conversation_chain.invoke({"question": query})
    
    # Parse the JSON result with improved error handling
    try:
        answer = result['answer'].strip()
        print("=" * 50)
        print("🔍 FULL DEBUG INFO:")
        print(f"RAW RESPONSE LENGTH: {len(answer)}")
        print(f"RAW RESPONSE TYPE: {type(answer)}")
        print("RAW RESPONSE CONTENT:")
        print(repr(answer))  # This shows hidden characters
        print("RAW RESPONSE DISPLAY:")
        print(answer)
        print("=" * 50)
        
        # Multiple strategies to extract JSON
        json_content = None
        
        # Strategy 1: Look for ```json blocks
        json_start = answer.find('```json')
        if json_start != -1:
            json_end = answer.find('```', json_start + 7)
            if json_end != -1:
                json_content = answer[json_start + 7:json_end].strip()
        
        # Strategy 2: Look for any {...} block
        if not json_content:
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', answer, re.DOTALL)
            if json_match:
                json_content = json_match.group(0)
        
        # Strategy 3: If it looks like JSON already, use as is
        if not json_content and (answer.startswith('{') and answer.endswith('}')):
            json_content = answer
        
        # Strategy 4: Extract from plain text
        if not json_content:
            decision_match = re.search(r'(?:decision|Decision|DECISION)["\s]*:["\s]*(INCLUDE|EXCLUDE)', answer, re.IGNORECASE)
            reason_match = re.search(r'(?:reason|Reason|REASON)["\s]*:["\s]*([^"]+)', answer, re.IGNORECASE)
            
            if decision_match:
                decision = decision_match.group(1).upper()
                reason = reason_match.group(1).strip() if reason_match else "No specific reason provided"
                print(f"EXTRACTED - Decision: {decision}, Reason: {reason}")
                return decision, reason
        
        # Try to parse the JSON
        if json_content:
            print(f"TRYING TO PARSE: {json_content}")
            response = json.loads(json_content)
            
            # Extract decision with fallbacks
            decision = None
            for key in ['decision', 'Decision', 'DECISION']:
                if key in response and response[key]:
                    decision = str(response[key]).upper()
                    break
            
            # Extract reason with fallbacks
            reason = None
            for key in ['reason', 'Reason', 'REASON']:
                if key in response and response[key]:
                    reason = str(response[key]).strip()
                    break
            
            if not decision or decision not in ['INCLUDE', 'EXCLUDE']:
                raise Exception(f"Invalid decision: {decision}")
            
            if not reason:
                reason = "No specific reason provided"
            
            print(f"PARSED - Decision: {decision}, Reason: {reason}")
            return decision, reason
        
        # If all parsing failed
        raise Exception("Could not extract JSON or decision from response")
        
    except Exception as e:
        print(f"Parsing error: {e}")
        if attempt < 5:
            print(f"Retrying... attempt {attempt + 1}")
            return rag_based_summary_screening(article_path, attempt + 1)
        else:
            print(f"All parsing attempts failed after {attempt + 1} tries")
            decision = "MANUAL"
            reason = f"Failed to parse LLM response after {attempt + 1} attempts. Please review manually."
            return decision, reason

def rag_based_full_text_screening(article_path, attempt=0):
    """
    Perform full text screening using RAG with selection criteria.
    
    :param article_path: String, path to the article file
    :return: Tuple of (decision, reason)
    """
    global global_research_question
    
    article = load_article_from_file(article_path)

    # if abstract is an array, join it into a single string
    if isinstance(article['Abstract'], list):
        abstract_text = "\n".join(article['Abstract'])
    else:
        abstract_text = article['Abstract']

    # SOLUTION: Truncate full text to prevent token limit exceeded
    full_text = article.get('Full Text', '')
    max_full_text_chars = 60000  # Reduced to be safer
    if len(full_text) > max_full_text_chars:
        full_text = full_text[:max_full_text_chars] + "\\n\\n[TEXT TRUNCATED DUE TO LENGTH]"

    # Create a text representation of the article to be screened
    article_text = f"""
    <TITLE> 
    {article['Title']}
    </TITLE>

    <ABSTRACT> 
    {abstract_text}
    </ABSTRACT>

    <FULL_ARTICLE_TEXT> 
    {full_text}
    </FULL_ARTICLE_TEXT>

    <PUBLICATION_DATE> 
    {article['Publication Date']}
    </PUBLICATION_DATE>
    """

    # Get selection criteria from session state if available
    try:
        import streamlit as st
        inclusion_criteria = st.session_state.get('inclusion_criteria', 'Not specified')
        exclusion_criteria = st.session_state.get('exclusion_criteria', 'Not specified')
        data_extraction_instructions = st.session_state.get('final_result_instructions', 'Not specified')
    except:
        inclusion_criteria = 'Not specified'
        exclusion_criteria = 'Not specified'
        data_extraction_instructions = 'Not specified'
        
    # Prepare the query with selection criteria
    query = f"""
CRITICAL: You MUST respond with ONLY a JSON object. Do not include any other text.

Task: Decide whether to INCLUDE or EXCLUDE this article for a systematic review based on comprehensive full text analysis.

RESEARCH QUESTION: {global_research_question}

INCLUSION CRITERIA: {inclusion_criteria}

EXCLUSION CRITERIA: {exclusion_criteria}

DATA EXTRACTION FEATURES: {data_extraction_instructions}

ARTICLE TO EVALUATE:
{article_text}

INSTRUCTIONS:
- Carefully evaluate the full article content against the research question
- Check if the article meets ALL inclusion criteria
- Verify the article does NOT meet any exclusion criteria  
- Assess if the article contains data relevant to the data extraction features
- Consider the methodological quality and relevance of the study
- Look for specific outcomes, populations, and interventions mentioned in the research question

RESPOND WITH ONLY THIS JSON FORMAT (no other text):
{{
    "decision": "INCLUDE",
    "reason": "Brief explanation of how this article meets inclusion criteria and relates to research question"
}}

OR

{{
    "decision": "EXCLUDE", 
    "reason": "Brief explanation of which criteria are not met or why article is not relevant"
}}

JSON Response:
"""

    print(f"QUERY: {query}")

    # Use the conversation chain to get a response
    result = conversation_chain.invoke({"question": query})

    # Parse the JSON result with improved error handling
    try:
        answer = result['answer'].strip()
        print("=" * 50)
        print("🔍 FULL TEXT SCREENING DEBUG INFO:")
        print(f"RAW RESPONSE LENGTH: {len(answer)}")
        print(f"RAW RESPONSE TYPE: {type(answer)}")
        print("RAW RESPONSE CONTENT:")
        print(repr(answer))  # This shows hidden characters
        print("RAW RESPONSE DISPLAY:")
        print(answer)
        print("=" * 50)
        
        # Multiple strategies to extract JSON
        json_content = None
        
        # Strategy 1: Look for ```json blocks
        json_start = answer.find('```json')
        if json_start != -1:
            json_end = answer.find('```', json_start + 7)
            if json_end != -1:
                json_content = answer[json_start + 7:json_end].strip()
        
        # Strategy 2: Look for any {...} block
        if not json_content:
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', answer, re.DOTALL)
            if json_match:
                json_content = json_match.group(0)
        
        # Strategy 3: If it looks like JSON already, use as is
        if not json_content and (answer.startswith('{') and answer.endswith('}')):
            json_content = answer
        
        # Strategy 4: Extract from plain text
        if not json_content:
            decision_match = re.search(r'(?:decision|Decision|DECISION)["\s]*:["\s]*(INCLUDE|EXCLUDE)', answer, re.IGNORECASE)
            reason_match = re.search(r'(?:reason|Reason|REASON)["\s]*:["\s]*([^"]+)', answer, re.IGNORECASE)
            
            if decision_match:
                decision = decision_match.group(1).upper()
                reason = reason_match.group(1).strip() if reason_match else "No specific reason provided"
                print(f"EXTRACTED - Decision: {decision}, Reason: {reason}")
                return decision, reason
        
        # Try to parse the JSON
        if json_content:
            print(f"TRYING TO PARSE: {json_content}")
            response = json.loads(json_content)
            
            # Extract decision with fallbacks
            decision = None
            for key in ['decision', 'Decision', 'DECISION']:
                if key in response and response[key]:
                    decision = str(response[key]).upper()
                    break
            
            # Extract reason with fallbacks
            reason = None
            for key in ['reason', 'Reason', 'REASON']:
                if key in response and response[key]:
                    reason = str(response[key]).strip()
                    break
            
            if not decision or decision not in ['INCLUDE', 'EXCLUDE']:
                raise Exception(f"Invalid decision: {decision}")
            
            if not reason:
                reason = "No specific reason provided"
            
            print(f"PARSED - Decision: {decision}, Reason: {reason}")
            return decision, reason
        
        # If all parsing failed
        raise Exception("Could not extract JSON or decision from response")
        
    except Exception as e:
        print(f"Parsing error: {e}")
        if attempt < 3:
            print(f"Retrying... attempt {attempt + 1}")
            return rag_based_full_text_screening(article_path, attempt + 1)
        else:
            print(f"All parsing attempts failed after {attempt + 1} tries")
            decision = "MANUAL"
            reason = f"Failed to parse LLM response after {attempt + 1} attempts. Please review manually."
            return decision, reason