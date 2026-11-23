"""
Enhanced quantitative comparison methods for systematic review validation
"""
from typing import Dict, List, Set, Any, Tuple
import json
import os


def calculate_overlap_metrics(manual_articles: List[Dict], llm_articles: List[Dict], 
                              date_range: Tuple[int, int] = None) -> Dict[str, Any]:
    """
    Calculate comprehensive overlap metrics between manual and LLM results
    
    Args:
        manual_articles: List of manual review articles (from EndNote)
        llm_articles: List of LLM-downloaded articles
        date_range: Optional tuple (start_year, end_year) to filter articles
    
    Returns:
        Dictionary with comprehensive metrics including Jaccard similarity
    """
    # Extract identifiers with date filtering
    manual_ids = set()
    manual_included_ids = set()
    
    for article in manual_articles:
        # Filter by date if specified
        if date_range:
            pub_date = article.get('publication_date', '').strip()
            year = _extract_year(pub_date)
            if year and not (date_range[0] <= year <= date_range[1]):
                continue
        
        pmid = article.get('pmid', '').strip().lower()
        if pmid:
            manual_ids.add(pmid)
            # Check if included
            decision = (article.get('title_abstract_decision') or 
                       article.get('manual_screening_decision') or '').upper()
            if decision in ['INCLUDE', 'INCLUDED', 'YES'] or not decision:
                manual_included_ids.add(pmid)
    
    llm_ids = set()
    for article in llm_articles:
        # Filter by date if specified
        if date_range and isinstance(article, dict):
            pub_year = _extract_pub_year_from_llm(article)
            if pub_year and not (date_range[0] <= pub_year <= date_range[1]):
                continue
        
        pmid = _extract_pmid_from_llm(article)
        if pmid:
            llm_ids.add(pmid.lower().strip())
    
    # Calculate standard metrics
    true_positives = len(manual_ids & llm_ids)
    false_positives = len(llm_ids - manual_ids)
    false_negatives = len(manual_ids - llm_ids)
    
    precision = true_positives / len(llm_ids) if llm_ids else 0
    recall = true_positives / len(manual_ids) if manual_ids else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0
    
    # Additional metrics
    union = manual_ids | llm_ids
    jaccard = len(manual_ids & llm_ids) / len(union) if union else 0
    
    # Included articles metrics
    included_tp = len(manual_included_ids & llm_ids)
    included_precision = included_tp / len(llm_ids) if llm_ids else 0
    included_recall = included_tp / len(manual_included_ids) if manual_included_ids else 0
    included_f1 = 2 * included_precision * included_recall / (included_precision + included_recall) if (included_precision + included_recall) > 0 else 0
    
    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "jaccard": jaccard,
        "overlap_count": true_positives,
        "manual_only_count": false_negatives,
        "llm_only_count": false_positives,
        "manual_total": len(manual_ids),
        "llm_total": len(llm_ids),
        # Included articles specific metrics
        "included_precision": included_precision,
        "included_recall": included_recall,
        "included_f1_score": included_f1,
        "included_overlap_count": included_tp,
        "manual_included_total": len(manual_included_ids),
        "date_range": date_range
    }


def _extract_year(pub_date: str) -> int:
    """Extract year from publication date string"""
    if not pub_date:
        return None
    try:
        # Try direct integer conversion
        year = int(pub_date)
        return year
    except:
        # Try extracting year from date strings
        import re
        year_match = re.search(r'(\d{4})', pub_date)
        if year_match:
            try:
                return int(year_match.group(1))
            except:
                pass
    return None


def _extract_pmid_from_llm(article: Any) -> str:
    """Extract PMID from LLM article (can be dict or file path)"""
    if isinstance(article, str):
        # It's a file path, load it
        try:
            with open(article, 'r', encoding='utf-8') as f:
                data = json.load(f)
                medline = data.get('MedlineCitation', {})
                pmid_obj = medline.get('PMID')
                if isinstance(pmid_obj, dict):
                    return str(pmid_obj.get('#text', ''))
                else:
                    return str(pmid_obj) if pmid_obj else ''
        except:
            return ''
    elif isinstance(article, dict):
        # Direct dict
        if 'pmid' in article:
            return str(article['pmid'])
        medline = article.get('MedlineCitation', {})
        if medline:
            pmid_obj = medline.get('PMID')
            if isinstance(pmid_obj, dict):
                return str(pmid_obj.get('#text', ''))
            else:
                return str(pmid_obj) if pmid_obj else ''
    return ''


def _extract_pub_year_from_llm(article: Any) -> int:
    """Extract publication year from LLM article"""
    if isinstance(article, str):
        try:
            with open(article, 'r', encoding='utf-8') as f:
                data = json.load(f)
                article_info = data.get('MedlineCitation', {}).get('Article', {})
                journal_issue = article_info.get('Journal', {}).get('JournalIssue', {})
                pub_date = journal_issue.get('PubDate', {})
                if isinstance(pub_date, dict):
                    pub_year = pub_date.get('Year')
                    if pub_year:
                        try:
                            return int(pub_year)
                        except:
                            pass
        except:
            pass
    elif isinstance(article, dict):
        article_info = article.get('MedlineCitation', {}).get('Article', {})
        journal_issue = article_info.get('Journal', {}).get('JournalIssue', {})
        pub_date = journal_issue.get('PubDate', {})
        if isinstance(pub_date, dict):
            pub_year = pub_date.get('Year')
            if pub_year:
                try:
                    return int(pub_year)
                except:
                    pass
    return None


def calculate_detailed_matching_stats(manual_articles: List[Dict], 
                                       llm_article_paths: List[str],
                                       date_range: Tuple[int, int] = None) -> Dict[str, Any]:
    """
    Calculate detailed matching statistics with multiple matching strategies
    
    Returns:
        Dictionary with matching statistics by method (PMID, DOI, Title)
    """
    from endnote_parser import EndNoteParser
    
    # Build manual identifier maps
    manual_pmid_map = {}
    manual_doi_map = {}
    manual_title_map = {}
    
    for article in manual_articles:
        if date_range:
            pub_date = article.get('publication_date', '').strip()
            year = _extract_year(pub_date)
            if year and not (date_range[0] <= year <= date_range[1]):
                continue
        
        pmid = article.get('pmid', '').strip().lower()
        doi = article.get('doi', '').strip().lower()
        title = article.get('title', '').strip().lower()
        
        if pmid:
            manual_pmid_map[pmid] = article
        if doi:
            doi_clean = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '').replace('doi:', '').strip()
            manual_doi_map[doi_clean] = article
        if title:
            manual_title_map[title] = article
    
    # Match LLM articles
    match_stats = {
        'pmid_matches': 0,
        'doi_matches': 0,
        'title_matches': 0,
        'unmatched': 0,
        'date_filtered': 0
    }
    
    matched_articles = []
    
    for article_path in llm_article_paths:
        try:
            with open(article_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                medline_citation = data.get('MedlineCitation', {})
                article_info = medline_citation.get('Article', {})
                
                # Extract publication year
                pub_year = _extract_pub_year_from_llm(data)
                if date_range and pub_year and not (date_range[0] <= pub_year <= date_range[1]):
                    match_stats['date_filtered'] += 1
                    continue
                
                # Extract identifiers
                pmid_obj = medline_citation.get('PMID')
                if isinstance(pmid_obj, dict):
                    pmid = str(pmid_obj.get('#text', '')).strip().lower()
                else:
                    pmid = str(pmid_obj).strip().lower() if pmid_obj else ''
                
                doi = ''
                e_location_ids = article_info.get('ELocationID', [])
                if isinstance(e_location_ids, list):
                    for e_id in e_location_ids:
                        if isinstance(e_id, dict) and e_id.get('EIdType') == 'doi':
                            doi = e_id.get('#text', '').strip().lower()
                
                title = ''
                title_elem = article_info.get('ArticleTitle', '')
                if isinstance(title_elem, str):
                    title = title_elem.strip().lower()
                
                # Try matching
                matched = None
                match_method = None
                
                if pmid and pmid in manual_pmid_map:
                    matched = manual_pmid_map[pmid]
                    match_method = 'pmid'
                    match_stats['pmid_matches'] += 1
                elif doi:
                    doi_clean = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '').replace('doi:', '').strip()
                    if doi_clean in manual_doi_map:
                        matched = manual_doi_map[doi_clean]
                        match_method = 'doi'
                        match_stats['doi_matches'] += 1
                elif title and title in manual_title_map:
                    matched = manual_title_map[title]
                    match_method = 'title'
                    match_stats['title_matches'] += 1
                else:
                    match_stats['unmatched'] += 1
                
                if matched:
                    matched_articles.append({
                        'llm_article': data,
                        'manual_article': matched,
                        'match_method': match_method
                    })
        except Exception as e:
            match_stats['unmatched'] += 1
    
    return {
        'match_stats': match_stats,
        'matched_articles': matched_articles,
        'total_matched': len(matched_articles)
    }

