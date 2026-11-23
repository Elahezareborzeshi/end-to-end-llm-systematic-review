"""
Query Enhancement Module
Enhances LLM-generated queries using manual review query knowledge
"""

import re
from typing import Dict, List, Set, Tuple
from manual_search_strategy import get_manual_strategy

# Try to import docx reader (optional dependency)
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


def read_manual_query(docx_path: str) -> str:
    """Read manual search query from docx file (optional, falls back to manual_search_strategy.py)"""
    if not DOCX_AVAILABLE or not docx_path:
        return ""
    
    try:
        doc = Document(docx_path)
        # Extract text from all paragraphs
        text_parts = [para.text for para in doc.paragraphs]
        
        # Also try to extract from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text_parts.append(cell.text)
        
        full_text = "\n".join(text_parts)
        
        # Clean up empty lines
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        full_text = '\n'.join(lines)
        
        if not full_text or len(full_text) < 10:
            return ""
        
        # Try to find the query (look for common patterns)
        query_patterns = [
            r'\([^)]+\)\s+AND\s+\([^)]+\)',  # (A) AND (B)
            r'\[MeSH Terms?\]',  # Contains MeSH Terms
            r'\[Title/Abstract\]',  # Contains Title/Abstract
        ]
        
        for pattern in query_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                # Find the section containing the query
                lines = full_text.split('\n')
                for i, line in enumerate(lines):
                    if re.search(pattern, line, re.IGNORECASE):
                        # Get surrounding context
                        start = max(0, i - 5)
                        end = min(len(lines), i + 20)
                        query_section = '\n'.join(lines[start:end])
                        return query_section
        
        return full_text
    except Exception:
        return ""


def extract_query_components(query: str) -> Dict[str, List[str]]:
    """Extract components from a query"""
    components = {
        'mesh_terms': [],
        'title_abstract_terms': [],
        'filters': [],
        'date_range': None
    }
    
    if not query:
        return components
    
    # Extract MeSH Terms
    mesh_pattern = r'"([^"]+)"\[MeSH Terms\]'
    components['mesh_terms'] = re.findall(mesh_pattern, query)
    
    # Extract Title/Abstract terms
    title_pattern = r'"([^"]+)"\[Title/Abstract\]'
    components['title_abstract_terms'] = re.findall(title_pattern, query)
    
    # Extract filters
    filter_pattern = r'(\w+\[(?:Mesh|Language|Filter)\])'
    components['filters'] = re.findall(filter_pattern, query)
    
    # Extract date range
    date_pattern = r'(\d{4}):(\d{4})\[pdat\]|(\d{4}):(\d{4})\[Publication Date\]'
    date_match = re.search(date_pattern, query)
    if date_match:
        components['date_range'] = (date_match.group(1) or date_match.group(3), 
                                    date_match.group(2) or date_match.group(4))
    
    return components

def load_manual_query_components(manual_query_path: str = None) -> Dict:
    """Load and extract components from manual query"""
    manual_strategy = get_manual_strategy()
    
    # Try to get query from docx file if path provided
    manual_query = ""
    if manual_query_path:
        manual_query = read_manual_query(manual_query_path)
    
    # Fallback to manual_search_strategy.py
    if not manual_query or len(manual_query) < 100:
        manual_query = manual_strategy.get("manual_boolean_query", "")
    
    if not manual_query:
        return {}
    
    # Extract components
    components = extract_query_components(manual_query)
    
    return {
        'query': manual_query,
        'mesh_terms': set(term.lower() for term in components.get('mesh_terms', [])),
        'title_abstract_terms': set(term.lower() for term in components.get('title_abstract_terms', [])),
        'keywords': manual_strategy.get("manual_keywords", []),
        'concept_groups': manual_strategy.get("concept_groups", {}),
        'manual_mesh_list': manual_strategy.get("manual_mesh_terms", [])
    }

def extract_mesh_terms_from_query(query: str) -> Set[str]:
    """Extract all MeSH terms from a query string"""
    mesh_pattern = r'"([^"]+)"\[MeSH Terms\]'
    mesh_terms = re.findall(mesh_pattern, query)
    return set(term.lower() for term in mesh_terms)

def find_missing_terms(llm_components: Dict, manual_components: Dict) -> Dict[str, List[str]]:
    """Find terms in manual query that are missing from LLM query"""
    missing = {
        'mesh_terms': [],
        'title_abstract_terms': [],
        'keywords': []
    }
    
    # Find missing MeSH terms
    llm_mesh = llm_components.get('mesh_terms', set())
    manual_mesh = manual_components.get('mesh_terms', set())
    missing_mesh = manual_mesh - llm_mesh
    
    # Convert back to original case (approximate)
    for term in missing_mesh:
        # Try to find original case from manual query
        manual_query = manual_components.get('query', '')
        mesh_pattern = rf'"{re.escape(term)}"\[MeSH Terms\]'
        match = re.search(mesh_pattern, manual_query, re.IGNORECASE)
        if match:
            # Extract the quoted term
            quoted_match = re.search(r'"([^"]+)"', match.group(0))
            if quoted_match:
                missing['mesh_terms'].append(quoted_match.group(1))
    
    # Find missing Title/Abstract terms (top 10 most important)
    llm_title_abstract = llm_components.get('title_abstract_terms', set())
    manual_title_abstract = manual_components.get('title_abstract_terms', set())
    missing_title_abstract = manual_title_abstract - llm_title_abstract
    
    # Filter out common words and keep important terms
    common_words = {'the', 'and', 'or', 'not', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    important_missing = [term for term in missing_title_abstract 
                       if len(term) >= 4 and term not in common_words][:10]
    
    for term in important_missing:
        # Try to find original case
        manual_query = manual_components.get('query', '')
        title_pattern = rf'"{re.escape(term)}"\[Title/Abstract\]'
        match = re.search(title_pattern, manual_query, re.IGNORECASE)
        if match:
            quoted_match = re.search(r'"([^"]+)"', match.group(0))
            if quoted_match:
                missing['title_abstract_terms'].append(quoted_match.group(1))
    
    # Find missing keywords
    manual_keywords = set(k.lower() for k in manual_components.get('keywords', []))
    llm_keywords = llm_components.get('keywords', set())
    missing_keywords = manual_keywords - llm_keywords
    missing['keywords'] = [k for k in manual_components.get('keywords', []) 
                          if k.lower() in missing_keywords]
    
    return missing

def enhance_grouped_terms_with_manual(grouped_terms: Dict, manual_components: Dict) -> Dict:
    """Enhance LLM grouped_terms with missing terms from manual query"""
    enhanced = grouped_terms.copy()
    
    # Get missing terms
    llm_mesh = set()
    llm_keywords = set(k.lower() for k in grouped_terms.keys())
    
    for keyword, terms in grouped_terms.items():
        for term in terms:
            if '[MeSH Terms]' in term:
                mesh_term = term.replace('[MeSH Terms]', '').replace('[Title/Abstract]', '').strip()
                llm_mesh.add(mesh_term.lower())
    
    llm_components = {
        'mesh_terms': llm_mesh,
        'keywords': llm_keywords
    }
    
    missing = find_missing_terms(llm_components, manual_components)
    
    # Add missing keywords to grouped_terms
    for keyword in missing['keywords']:
        if keyword.lower() not in llm_keywords:
            enhanced[keyword] = []
            # Find related MeSH terms from manual
            keyword_lower = keyword.lower()
            for mesh_term in missing['mesh_terms']:
                if keyword_lower in mesh_term.lower() or mesh_term.lower() in keyword_lower:
                    enhanced[keyword].append(f"{mesh_term}[MeSH Terms]")
    
    # Add missing MeSH terms to existing keywords
    manual_concept_groups = manual_components.get('concept_groups', {})
    
    for concept_name, concept_keywords in manual_concept_groups.items():
        for manual_keyword in concept_keywords:
            manual_keyword_lower = manual_keyword.lower()
            # Try to find matching LLM keyword
            matched = False
            for llm_keyword in enhanced.keys():
                if manual_keyword_lower in llm_keyword.lower() or llm_keyword.lower() in manual_keyword_lower:
                    # Add missing MeSH terms to this keyword
                    for mesh_term in missing['mesh_terms']:
                        mesh_term_lower = mesh_term.lower()
                        # Check if mesh term is relevant to this concept
                        if any(kw in mesh_term_lower for kw in [manual_keyword_lower, concept_name.lower()]):
                            mesh_entry = f"{mesh_term}[MeSH Terms]"
                            if mesh_entry not in enhanced[llm_keyword]:
                                enhanced[llm_keyword].append(mesh_entry)
                    matched = True
                    break
            
            # If no match found, add as new keyword
            if not matched and manual_keyword_lower not in llm_keywords:
                enhanced[manual_keyword] = []
                # Add related MeSH terms
                for mesh_term in missing['mesh_terms']:
                    if manual_keyword_lower in mesh_term.lower():
                        enhanced[manual_keyword].append(f"{mesh_term}[MeSH Terms]")
    
    return enhanced

def enhance_query_with_manual_terms(llm_query: str, manual_components: Dict) -> str:
    """Enhance LLM query by adding missing important terms from manual query"""
    
    # Extract components from both queries
    llm_components = extract_query_components(llm_query)
    missing = find_missing_terms(llm_components, manual_components)
    
    # Add critical missing MeSH terms
    critical_mesh_terms = [
        "Vasodilator Agents",
        "Calcium Channel Blockers", 
        "Angiotensin Receptor Antagonists"
    ]
    
    enhanced_query = llm_query
    
    # Find antihypertensive section and add missing terms
    for mesh_term in critical_mesh_terms:
        if mesh_term.lower() not in llm_components['mesh_terms']:
            # Try to add to antihypertensive section
            pattern = r'("Antihypertensive Agents"\[MeSH Terms\])'
            if re.search(pattern, enhanced_query):
                replacement = f'\\1 OR "{mesh_term}"[MeSH Terms]'
                enhanced_query = re.sub(pattern, replacement, enhanced_query, count=1)
    
    return enhanced_query

