import time
from langchain_openai import ChatOpenAI


def build_search_query_for_terms(mesh_terms):
    llm = ChatOpenAI(temperature=0.02, model_name="gpt-4o")

    combined_terms_text = " ".join(mesh_terms)

    instruction = f"""
    Generate an advanced search query using Boolean operators for the following request. Use the following Boolean operators:
    - AND: To include all specified terms.
    - OR: To include any of the specified terms.
    - NOT: To exclude specified terms.
    - Parentheses (): To group terms and operators together.
    
    Examples:
    1. Find articles about machine learning and artificial intelligence but exclude neural networks.
       Output: ("machine learning" AND "artificial intelligence") NOT "neural networks"
    2. Find research papers on deep learning or reinforcement learning that mention training but exclude testing.
       Output: ("deep learning" OR "reinforcement learning") AND "training" NOT "testing"
    
    ALL MESH TERMS: {combined_terms_text}
    """                    
    response = llm.invoke(instruction)
    time.sleep(10)

    search_query = response.content.strip()
    return search_query


def build_search_query(mesh_terms):
    """Build an advanced search query using boolean operators."""
    query_parts = []
    for i, term in enumerate(mesh_terms):
        if i == 0:
            query_parts.append(f'("{term}")')
        else:
            query_parts.append(f'OR ("{term}")')
    return " ".join(query_parts)

def print_search_query(query):
    """Print the generated search query."""
    print("Generated search query:")
    print(query)
    print()

def build_search_query_for_groups(grouped_terms):
    """Build a search query for each group of terms, within each group use OR and between groups use AND."""
    query_parts = []
    for group in grouped_terms:
        group_query_parts = []
        for term in group:
            group_query_parts.append(f'"{term}"')
        query_parts.append(" OR ".join(group_query_parts))
    return "(" + ") AND (".join(query_parts) + ")"
