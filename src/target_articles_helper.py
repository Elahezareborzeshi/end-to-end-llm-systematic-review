"""
Target Articles Helper Module

References the 5 key articles for data extraction validation.
These articles should be prioritized during validation.
"""

import json
import os
from typing import List, Dict, Any

# Target articles for data extraction (from user specification)
TARGET_ARTICLES_PMIDS = [
    "34952949",  # Huang
    "26783503",  # Rotroff
    "29288159",  # Shahin
    "28217401",  # Weng
    "31583478"   # Sonn
]

TARGET_ARTICLES_DETAILED = {
    "34952949": {
        "first_author": "Huang",
        "pmid": "34952949",
        "doi": "10.1038/s41440-021-00825-9",
        "priority": "high"
    },
    "26783503": {
        "first_author": "Rotroff",
        "pmid": "26783503",
        "pmcid": "PMC4716583",
        "doi": "10.1002/psp4.12017",
        "priority": "high"
    },
    "29288159": {
        "first_author": "Shahin",
        "pmid": "29288159",
        "pmcid": "PMC5778957",
        "doi": "10.1161/JAHA.117.006656",
        "priority": "high"
    },
    "28217401": {
        "first_author": "Weng",
        "pmid": "28217401",
        "pmcid": "PMC5313050",
        "doi": "10.1007/s11306-016-1098-2",
        "priority": "high"
    },
    "31583478": {
        "first_author": "Sonn",
        "pmid": "31583478",
        "pmcid": "PMC6815665",
        "doi": "10.1007/s11306-019-1601-7",
        "priority": "high"
    }
}


def get_target_pmids() -> List[str]:
    """Get list of target PMIDs"""
    return TARGET_ARTICLES_PMIDS


def is_target_article(pmid: str) -> bool:
    """Check if a PMID is in the target articles list"""
    return pmid in TARGET_ARTICLES_PMIDS


def get_target_article_info(pmid: str) -> Dict[str, Any]:
    """Get detailed info for a target article"""
    return TARGET_ARTICLES_DETAILED.get(pmid, {})


def load_target_articles_from_json(json_path: str = "data/target_articles_pmids.json") -> List[Dict]:
    """Load target articles from JSON file"""
    try:
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('target_articles_for_data_extraction', [])
        else:
            # Return as list of dicts from TARGET_ARTICLES_DETAILED
            return list(TARGET_ARTICLES_DETAILED.values())
    except Exception as e:
        print(f"Warning: Could not load target articles from {json_path}: {e}")
        return list(TARGET_ARTICLES_DETAILED.values())


def filter_articles_by_target_pmids(articles: List[Dict]) -> List[Dict]:
    """Filter articles to only include target articles"""
    target_pmids = get_target_pmids()
    filtered = []
    
    for article in articles:
        pmid = str(article.get('pmid', '')).lower().strip()
        if pmid in target_pmids:
            filtered.append(article)
    
    return filtered


def get_target_articles_for_validation(llm_articles_dir: str) -> List[Dict]:
    """
    Get target articles from LLM articles directory
    
    Args:
        llm_articles_dir: Directory containing LLM article files
        
    Returns:
        List of target article dictionaries
    """
    import json
    
    target_articles = []
    target_pmids = get_target_pmids()
    
    for filename in os.listdir(llm_articles_dir):
        if filename.endswith('_source.json'):
            file_path = os.path.join(llm_articles_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    medline_citation = data.get('MedlineCitation', {})
                    
                    # Extract PMID
                    pmid = str(medline_citation.get('PMID', {}).get('#text', '')) if isinstance(medline_citation.get('PMID'), dict) else str(medline_citation.get('PMID', ''))
                    pmid = pmid.lower().strip()
                    
                    if pmid in target_pmids:
                        target_articles.append({
                            'pmid': pmid,
                            'file_path': file_path,
                            'data': data
                        })
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    print(f"✅ Found {len(target_articles)}/{len(target_pmids)} target articles")
    return target_articles



