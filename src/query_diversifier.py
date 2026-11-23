"""
Query diversification utilities for generating multiple query variations
"""
from typing import List, Dict, Set
import random


def generate_diverse_queries(base_concepts: Dict[str, List[str]], 
                             num_variations: int = 5,
                             query_structures: List[str] = None) -> List[Dict[str, str]]:
    """
    Generate diverse search queries with different strategies
    
    Args:
        base_concepts: Dictionary mapping concept names to lists of terms
        num_variations: Number of query variations to generate
        query_structures: List of structure types to use
    
    Returns:
        List of dictionaries with 'name' and 'query' keys
    """
    if query_structures is None:
        query_structures = [
            "concept_blocks",      # (A OR B) AND (C OR D)
            "mesh_focused",        # Heavy use of MeSH terms
            "keyword_focused",     # More Title/Abstract terms
            "recall_oriented",     # Broader terms, more synonyms
            "precision_oriented"   # More specific terms
        ]
    
    diverse_queries = []
    
    for i in range(min(num_variations, len(query_structures))):
        structure = query_structures[i]
        query_name = f"query_{structure}_{i+1}"
        
        # Generate query based on structure
        if structure == "concept_blocks":
            query = _generate_concept_blocks_query(base_concepts, sampling_rate=0.8)
        elif structure == "mesh_focused":
            query = _generate_mesh_focused_query(base_concepts, sampling_rate=0.9)
        elif structure == "keyword_focused":
            query = _generate_keyword_focused_query(base_concepts, sampling_rate=0.7)
        elif structure == "recall_oriented":
            query = _generate_recall_oriented_query(base_concepts, sampling_rate=1.0)
        elif structure == "precision_oriented":
            query = _generate_precision_oriented_query(base_concepts, sampling_rate=0.6)
        else:
            query = _generate_concept_blocks_query(base_concepts)
        
        # Add standard filters
        query = _add_standard_filters(query)
        
        diverse_queries.append({
            "name": query_name,
            "query": query,
            "structure": structure
        })
    
    return diverse_queries


def _generate_concept_blocks_query(concepts: Dict[str, List[str]], sampling_rate: float = 0.8) -> str:
    """Generate query using concept blocks: (A OR B) AND (C OR D)"""
    concept_groups = []
    
    for concept_name, terms in concepts.items():
        if not terms:
            continue
        
        # Sample terms based on sampling rate
        num_terms = max(1, int(len(terms) * sampling_rate))
        sampled_terms = random.sample(terms, min(num_terms, len(terms)))
        
        if sampled_terms:
            # Group terms with OR
            term_group = " OR ".join(sampled_terms)
            concept_groups.append(f"({term_group})")
    
    # Combine with AND
    query = " AND ".join(concept_groups)
    return query


def _generate_mesh_focused_query(concepts: Dict[str, List[str]], sampling_rate: float = 0.9) -> str:
    """Generate query with heavy emphasis on MeSH terms"""
    concept_groups = []
    
    for concept_name, terms in concepts.items():
        if not terms:
            continue
        
        # Filter for MeSH terms
        mesh_terms = [t for t in terms if '[MeSH Terms]' in t]
        other_terms = [t for t in terms if '[MeSH Terms]' not in t]
        
        # Use more MeSH terms, fewer other terms
        num_mesh = max(1, int(len(mesh_terms) * sampling_rate))
        num_other = max(0, int(len(other_terms) * sampling_rate * 0.5))
        
        sampled_mesh = random.sample(mesh_terms, min(num_mesh, len(mesh_terms))) if mesh_terms else []
        sampled_other = random.sample(other_terms, min(num_other, len(other_terms))) if other_terms else []
        
        all_terms = sampled_mesh + sampled_other
        if all_terms:
            term_group = " OR ".join(all_terms)
            concept_groups.append(f"({term_group})")
    
    query = " AND ".join(concept_groups)
    return query


def _generate_keyword_focused_query(concepts: Dict[str, List[str]], sampling_rate: float = 0.7) -> str:
    """Generate query with emphasis on Title/Abstract keywords"""
    concept_groups = []
    
    for concept_name, terms in concepts.items():
        if not terms:
            continue
        
        # Filter for Title/Abstract terms
        title_abstract_terms = [t for t in terms if '[Title/Abstract]' in t or '[' not in t]
        mesh_terms = [t for t in terms if '[MeSH Terms]' in t]
        
        # Use more Title/Abstract terms
        num_title = max(1, int(len(title_abstract_terms) * sampling_rate))
        num_mesh = max(0, int(len(mesh_terms) * sampling_rate * 0.5))
        
        sampled_title = random.sample(title_abstract_terms, min(num_title, len(title_abstract_terms))) if title_abstract_terms else []
        sampled_mesh = random.sample(mesh_terms, min(num_mesh, len(mesh_terms))) if mesh_terms else []
        
        all_terms = sampled_title + sampled_mesh
        if all_terms:
            term_group = " OR ".join(all_terms)
            concept_groups.append(f"({term_group})")
    
    query = " AND ".join(concept_groups)
    return query


def _generate_recall_oriented_query(concepts: Dict[str, List[str]], sampling_rate: float = 1.0) -> str:
    """Generate query optimized for recall (broader, more inclusive)"""
    concept_groups = []
    
    for concept_name, terms in concepts.items():
        if not terms:
            continue
        
        # Use all or most terms for maximum recall
        num_terms = max(1, int(len(terms) * sampling_rate))
        sampled_terms = random.sample(terms, min(num_terms, len(terms)))
        
        if sampled_terms:
            term_group = " OR ".join(sampled_terms)
            concept_groups.append(f"({term_group})")
    
    query = " AND ".join(concept_groups)
    return query


def _generate_precision_oriented_query(concepts: Dict[str, List[str]], sampling_rate: float = 0.6) -> str:
    """Generate query optimized for precision (more specific)"""
    concept_groups = []
    
    for concept_name, terms in concepts.items():
        if not terms:
            continue
        
        # Prefer MeSH terms and specific terms
        mesh_terms = [t for t in terms if '[MeSH Terms]' in t]
        specific_terms = [t for t in terms if t not in mesh_terms and len(t.split()) <= 3]
        
        # Use fewer, more specific terms
        num_terms = max(1, int(len(mesh_terms + specific_terms) * sampling_rate))
        all_specific = mesh_terms + specific_terms
        sampled_terms = random.sample(all_specific, min(num_terms, len(all_specific))) if all_specific else []
        
        if sampled_terms:
            term_group = " OR ".join(sampled_terms)
            concept_groups.append(f"({term_group})")
    
    query = " AND ".join(concept_groups)
    return query


def _add_standard_filters(query: str) -> str:
    """Add standard PubMed filters to query"""
    filters = ' AND humans[Mesh] AND english[Language] AND (clinicaltrial[Filter] OR observationalstudy[Filter] OR randomizedcontrolledtrial[Filter]) AND (2013:2024[Publication Date])'
    return f"{query} {filters}"


def expand_concepts_with_synonyms(concepts: Dict[str, List[str]], 
                                  synonym_dict: Dict[str, List[str]] = None) -> Dict[str, List[str]]:
    """
    Expand concepts with synonyms
    
    Args:
        concepts: Dictionary mapping concept names to lists of terms
        synonym_dict: Optional dictionary mapping terms to their synonyms
    
    Returns:
        Expanded concepts dictionary
    """
    expanded = {}
    
    for concept_name, terms in concepts.items():
        expanded_terms = list(terms)  # Start with original terms
        
        # Add synonyms if available
        if synonym_dict:
            for term in terms:
                # Remove field tags for lookup
                base_term = term.split('[')[0].strip().lower()
                if base_term in synonym_dict:
                    synonyms = synonym_dict[base_term]
                    # Add synonyms with same field tag
                    field_tag = term.split('[')[1] if '[' in term else ''
                    for synonym in synonyms:
                        if field_tag:
                            expanded_terms.append(f"{synonym}[{field_tag}")
                        else:
                            expanded_terms.append(synonym)
        
        expanded[concept_name] = list(set(expanded_terms))  # Remove duplicates
    
    return expanded

