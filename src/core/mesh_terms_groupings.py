import time

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import CharacterTextSplitter

def group_mesh_terms_by_keyword(mesh_terms):
    """Group MeSH terms based on relevancy using Langchain RAG."""
    # Prepare the data for RAG
    text_data = "\n".join(mesh_terms)
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_text(text_data)

    # Create embeddings and vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts, embedding=embeddings)

    # Create conversation chain
    llm = ChatOpenAI(temperature=0.02, model_name="gpt-4o")
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )

    # Query the RAG system
    query = f"""
    Given the following MeSH scientific medical and medicine related terms, group them together based on synonyms and related keywords and semantic meaning:
    {' @ '.join(mesh_terms)}

    Please follow these instructions:
    1. Create groups of related terms based on synonyms and meanings, and even semantically similar words in context of medical science.
    2. Assign a relevant keyword or short phrase to each group.
    3. Present the results in the following format:
       Keyword1: term1 @ term2 @ term3
       Keyword2: term4 @ term5 @ term6
       ...
    4. Ensure that each term appears in only one group.
    5. All input terms will be separated by '@' character.
    """

    result = conversation_chain.invoke({"question": query})
    time.sleep(10)
    
    # Process the result
    grouped_terms = {}
    for line in result['answer'].split('\n'):
        if ':' in line:
            keyword, terms = line.split(':', 1)
            keyword = keyword.strip()
            terms = [term.strip() for term in terms.split('@')]
            grouped_terms[keyword] = terms

    return grouped_terms
