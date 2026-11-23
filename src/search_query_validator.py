import re
import streamlit as st
from typing import Dict, List, Tuple, Optional

def validate_boolean_search_query(query: str) -> Dict[str, any]:
    """
    Validate a Boolean search query for PubMed with comprehensive checks.
    
    Args:
        query (str): The search query to validate
        
    Returns:
        Dict with validation results including:
        - is_valid (bool): Overall validity
        - errors (List[str]): List of errors found
        - warnings (List[str]): List of warnings
        - suggestions (List[str]): List of improvement suggestions
        - formatted_query (str): Cleaned/formatted version of the query
    """
    
    result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'suggestions': [],
        'formatted_query': query.strip()
    }
    
    if not query or not query.strip():
        result['is_valid'] = False
        result['errors'].append("Query cannot be empty")
        return result
    
    # Clean and normalize the query
    cleaned_query = _clean_query(query)
    result['formatted_query'] = cleaned_query
    
    # Run all validation checks
    _check_parentheses_balance(cleaned_query, result)
    _check_boolean_operators(cleaned_query, result)
    _check_field_tags(cleaned_query, result)
    _check_quotes_balance(cleaned_query, result)
    _check_query_structure(cleaned_query, result)
    _check_pubmed_syntax(cleaned_query, result)
    _provide_optimization_suggestions(cleaned_query, result)
    
    return result

def _clean_query(query: str) -> str:
    """Clean and normalize the query string"""
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', query.strip())
    
    # Normalize boolean operators to uppercase
    cleaned = re.sub(r'\band\b', 'AND', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bor\b', 'OR', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bnot\b', 'NOT', cleaned, flags=re.IGNORECASE)
    
    return cleaned

def _check_parentheses_balance(query: str, result: Dict) -> None:
    """Check if parentheses are properly balanced"""
    stack = []
    for i, char in enumerate(query):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if not stack:
                result['is_valid'] = False
                result['errors'].append(f"Unmatched closing parenthesis at position {i}")
            else:
                stack.pop()
    
    if stack:
        result['is_valid'] = False
        result['errors'].append(f"Unmatched opening parenthesis at position(s): {', '.join(map(str, stack))}")

def _check_quotes_balance(query: str, result: Dict) -> None:
    """Check if quotes are properly balanced"""
    quote_count = query.count('"')
    if quote_count % 2 != 0:
        result['is_valid'] = False
        result['errors'].append("Unmatched quotes - quotes must be balanced")

def _check_boolean_operators(query: str, result: Dict) -> None:
    """Check for proper Boolean operator usage"""
    
    # Check for consecutive operators
    consecutive_ops = re.findall(r'\b(AND|OR|NOT)\s+(AND|OR|NOT)\b', query)
    if consecutive_ops:
        result['warnings'].append(f"Consecutive Boolean operators found: {', '.join([f'{op[0]} {op[1]}' for op in consecutive_ops])}")
    
    # Check for operators at start/end
    if re.match(r'^\s*(AND|OR|NOT)\b', query):
        result['warnings'].append("Query starts with a Boolean operator")
    
    if re.search(r'\b(AND|OR|NOT)\s*$', query):
        result['warnings'].append("Query ends with a Boolean operator")
    
    # Check for missing operators between terms
    # Look for patterns like: "term1" "term2" or term1 term2 without operators
    missing_ops = re.findall(r'"\s*[^"]*\s*"\s+"\s*[^"]*\s*"', query)
    if missing_ops:
        result['warnings'].append("Possible missing Boolean operators between quoted terms")

def _check_field_tags(query: str, result: Dict) -> None:
    """Check for proper PubMed field tag usage"""
    
    # Common PubMed field tags and filters
    valid_fields = [
        'Title', 'Abstract', 'Author', 'Journal', 'MeSH Terms', 'Publication Date',
        'Title/Abstract', 'All Fields', 'Text Word', 'Keyword', 'Affiliation',
        'Grant Number', 'Language', 'Publication Type', 'Substance Name',
        'dp', 'edat', 'crdt',  # Date fields
        'Filter', 'sb'  # Filter tags (valid in PubMed)
    ]
    
    # Also accept common variations
    field_aliases = {
        'Mesh': 'MeSH Terms',
        'mesh': 'MeSH Terms',
        'MeSH': 'MeSH Terms'
    }
    
    # Find field tags in the query
    field_pattern = r'\[([^\]]+)\]'
    found_fields = re.findall(field_pattern, query)
    
    for field in found_fields:
        # Check if it's an alias
        if field in field_aliases:
            result['suggestions'].append(f"Consider using [{field_aliases[field]}] instead of [{field}]")
        elif field not in valid_fields:
            # Check if it's a filter (like clinicaltrial[Filter])
            if field.lower() == 'filter' or 'filter' in field.lower():
                # Filters are valid in PubMed, just note it
                pass
            else:
                result['warnings'].append(f"Unknown field tag: [{field}]. Common tags: {', '.join(valid_fields[:5])}...")

def _check_query_structure(query: str, result: Dict) -> None:
    """Check overall query structure"""
    
    # Check for empty parentheses
    if re.search(r'\(\s*\)', query):
        result['errors'].append("Empty parentheses found")
        result['is_valid'] = False
    
    # Check for doubled field tags (common generation error)
    doubled_tags = re.findall(r'\[([^\]]+)\]\s*\)\s*\[([^\]]+)\]', query)
    if doubled_tags:
        result['errors'].append(f"Doubled field tags found: {doubled_tags}. This usually indicates a query generation error.")
        result['is_valid'] = False
    
    # Check for very long query (PubMed has limits)
    if len(query) > 4000:
        result['warnings'].append("Query is very long (>4000 characters). PubMed may have limits.")
    
    # Check for excessive nesting
    max_nesting = 0
    current_nesting = 0
    for char in query:
        if char == '(':
            current_nesting += 1
            max_nesting = max(max_nesting, current_nesting)
        elif char == ')':
            current_nesting -= 1
    
    if max_nesting > 10:
        result['warnings'].append(f"Very deep nesting ({max_nesting} levels). Consider simplifying.")

def _check_pubmed_syntax(query: str, result: Dict) -> None:
    """Check for PubMed-specific syntax issues"""
    
    # Check for wildcard usage
    if '*' in query and not re.search(r'\w\*', query):
        result['warnings'].append("Wildcard (*) should be preceded by at least one character")
    
    # Check for phrase searching
    phrases = re.findall(r'"([^"]+)"', query)
    for phrase in phrases:
        if len(phrase.split()) > 10:
            result['warnings'].append(f"Very long phrase: '{phrase[:50]}...' Consider breaking into shorter phrases")

def _provide_optimization_suggestions(query: str, result: Dict) -> None:
    """Provide suggestions for query optimization"""
    
    # Suggest MeSH terms usage
    if '[MeSH Terms]' not in query and '[Title/Abstract]' in query:
        result['suggestions'].append("Consider adding MeSH terms for more comprehensive searching")
    
    # Suggest field-specific searching
    if '[' not in query:
        result['suggestions'].append("Consider using field tags like [Title/Abstract] or [MeSH Terms] for more precise searching")
    
    # Check for common terms that might be too broad
    broad_terms = ['health', 'disease', 'treatment', 'patient', 'study', 'research']
    query_lower = query.lower()
    found_broad = [term for term in broad_terms if term in query_lower]
    if found_broad:
        result['suggestions'].append(f"Consider being more specific with broad terms: {', '.join(found_broad)}")

def format_search_query(query: str) -> str:
    """Format a search query for better readability"""
    
    # Add line breaks for better readability
    formatted = query
    
    # Add newlines before major AND operations (but not within parentheses)
    paren_level = 0
    result_chars = []
    i = 0
    
    while i < len(formatted):
        char = formatted[i]
        
        if char == '(':
            paren_level += 1
        elif char == ')':
            paren_level -= 1
        elif paren_level == 0 and formatted[i:i+4] == ' AND':
            result_chars.append('\nAND')
            i += 3  # Skip the 'AND' part as we already added it
        else:
            result_chars.append(char)
        
        i += 1
    
    return ''.join(result_chars)

def display_validation_results(validation_result: Dict) -> None:
    """Display validation results in Streamlit UI"""
    
    if validation_result['is_valid']:
        st.success("✅ Search query is valid!")
    else:
        st.error("❌ Search query has errors that need to be fixed")
    
    # Display errors
    if validation_result['errors']:
        st.subheader("🚨 Errors")
        for error in validation_result['errors']:
            st.error(f"• {error}")
    
    # Display warnings
    if validation_result['warnings']:
        st.subheader("⚠️ Warnings")
        for warning in validation_result['warnings']:
            st.warning(f"• {warning}")
    
    # Display suggestions
    if validation_result['suggestions']:
        st.subheader("💡 Suggestions")
        for suggestion in validation_result['suggestions']:
            st.info(f"• {suggestion}")
    
    # Show formatted query if different
    if validation_result['formatted_query'].strip() != validation_result.get('original_query', '').strip():
        st.subheader("🔧 Formatted Query")
        st.code(validation_result['formatted_query'], language="text")

# def fix_common_query_issues(query: str) -> str:
#     """Automatically fix common query issues"""
    
#     fixed_query = query
    
#     # Fix doubled field tags like )[Title/Abstract]
#     fixed_query = re.sub(r'\[([^\]]+)\]\s*\)\s*\[([^\]]+)\]', r'[\1])', fixed_query)
    
#     # Fix consecutive operators
#     fixed_query = re.sub(r'\b(AND|OR|NOT)\s+(AND|OR|NOT)\b', r'\2', fixed_query)
    
#     # Remove operators from start/end
#     fixed_query = re.sub(r'^\s*(AND|OR|NOT)\s+', '', fixed_query)
#     fixed_query = re.sub(r'\s+(AND|OR|NOT)\s*$', '', fixed_query)
    
#     # Clean up extra whitespace
#     fixed_query = re.sub(r'\s+', ' ', fixed_query.strip())
    
#     return fixed_query
def fix_common_query_issues(query: str) -> str:
    """Fix common query problems automatically"""
    
    fixed_query = query
    
    # Fix doubled field tags
    fixed_query = re.sub(r'\[([^\]]+)\]\s*\)\s*\[([^\]]+)\]', r'[\1])', fixed_query)
    
    # Fix consecutive operators (AND AND becomes just AND)
    fixed_query = re.sub(r'\b(AND|OR|NOT)\s+(AND|OR|NOT)\b', r'\2', fixed_query)
    
    # Remove operators from start/end
    fixed_query = re.sub(r'^\s*(AND|OR|NOT)\s+', '', fixed_query)
    fixed_query = re.sub(r'\s+(AND|OR|NOT)\s*$', '', fixed_query)
    
    # NEW: Remove duplicate language filters
    lang_count = fixed_query.lower().count('and "english"[language]')
    if lang_count > 1:
        # Remove all and add one at the end
        fixed_query = re.sub(r'AND\s+"english"\[Language\]', '', fixed_query, flags=re.IGNORECASE)
        fixed_query = fixed_query.strip() + ' AND "english"[Language]'
    
    # NEW: Remove duplicate humans filters
    human_count = fixed_query.lower().count('and "humans"[mesh terms]')
    if human_count > 1:
        # Remove all and add one at the end
        fixed_query = re.sub(r'AND\s+"humans"\[MeSH Terms\]', '', fixed_query, flags=re.IGNORECASE)
        fixed_query = fixed_query.strip() + ' AND "humans"[MeSH Terms]'
    
    # Clean up multiple ANDs
    fixed_query = re.sub(r'\s+AND\s+AND\s+', ' AND ', fixed_query)
    
    # Clean up whitespace
    fixed_query = re.sub(r'\s+', ' ', fixed_query.strip())
    
    return fixed_query

def get_example_queries() -> List[Dict[str, str]]:
    """Get example Boolean search queries for PubMed"""
    
    return [
        {
            "name": "Basic AND/OR combination",
            "query": '("hypertension"[MeSH Terms] OR "high blood pressure"[Title/Abstract]) AND ("sudden cardiac death"[MeSH Terms] OR "sudden death"[Title/Abstract])',
            "description": "Combines MeSH terms and title/abstract searching"
        },
        {
            "name": "Complex multi-concept search",
            "query": '(("diabetes mellitus"[MeSH Terms] OR "diabetes"[Title/Abstract]) AND ("cardiovascular disease"[MeSH Terms] OR "heart disease"[Title/Abstract])) NOT ("pediatric"[Title/Abstract] OR "children"[Title/Abstract])',
            "description": "Multiple concepts with exclusions"
        },
        {
            "name": "Date and study type limited",
            "query": '("systematic review"[Publication Type] OR "meta-analysis"[Publication Type]) AND "2020/01/01"[Date - Publication] : "2024/12/31"[Date - Publication]',
            "description": "Includes publication type and date limits"
        }
    ] 