"""
EndNote Validation Module

Provides robust article matching between manual EndNote reviews and LLM-based reviews
using PMID, DOI, and fuzzy title matching with fallback strategies.
"""

import json
import os
from typing import Dict, List, Tuple, Optional, Any
import re

# Try to import fuzzywuzzy, make it optional
try:
    from fuzzywuzzy import fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    print("⚠️ Warning: fuzzywuzzy not available. Title matching will use simple string comparison.")


class EndNoteValidator:
    """Validates article matching between EndNote and LLM-based screening"""
    
    def __init__(self, llm_articles_dir: str):
        """
        Initialize validator with directory containing LLM articles
        
        Args:
            llm_articles_dir: Path to directory containing LLM article JSON files
        """
        self.llm_articles_dir = llm_articles_dir
        self.llm_articles = self._load_llm_articles()
        self.validation_log = []
        
    def _load_llm_articles(self) -> List[Dict[str, Any]]:
        """Load all LLM articles from directory"""
        articles = []
        
        if not os.path.exists(self.llm_articles_dir):
            print(f"⚠️ Warning: Directory {self.llm_articles_dir} does not exist")
            return articles
        
        for filename in os.listdir(self.llm_articles_dir):
            if filename.endswith('_source.json'):
                file_path = os.path.join(self.llm_articles_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        article = self._parse_llm_article(data, file_path)
                        if article:
                            articles.append(article)
                except Exception as e:
                    print(f"❌ Error loading {file_path}: {e}")
        
        print(f"📚 Loaded {len(articles)} LLM articles")
        return articles
    
    def _parse_llm_article(self, data: Dict, file_path: str) -> Optional[Dict]:
        """Parse article data from LLM JSON file"""
        try:
            medline_citation = data.get('MedlineCitation', {})
            article_info = medline_citation.get('Article', {})
            
            # Extract identifiers
            pmid = str(medline_citation.get('PMID', {}).get('#text', '')) if isinstance(medline_citation.get('PMID'), dict) else str(medline_citation.get('PMID', ''))
            
            # Extract DOI from ELocationID
            doi = self._extract_doi_from_article(article_info)
            
            # Extract title
            title = article_info.get('ArticleTitle', '')
            
            # Extract authors
            authors = self._extract_authors(article_info.get('AuthorList', []))
            
            # Extract year
            year = article_info.get('Journal', {}).get('JournalIssue', {}).get('PubDate', {}).get('Year', '')
            
            return {
                'pmid': pmid.lower().strip() if pmid else None,
                'doi': doi.lower().strip() if doi else None,
                'title': title.strip() if title else '',
                'authors': authors,
                'year': year,
                'file_path': file_path,
                'data': data  # Store full data for later use
            }
        except Exception as e:
            print(f"❌ Error parsing article {file_path}: {e}")
            return None
    
    def _extract_doi_from_article(self, article_info: Dict) -> Optional[str]:
        """Extract DOI from article ELocationID"""
        try:
            e_location_ids = article_info.get('ELocationID', [])
            if isinstance(e_location_ids, list):
                for e_id in e_location_ids:
                    if isinstance(e_id, dict) and e_id.get('EIdType') == 'doi':
                        return e_id.get('#text', '')
            elif isinstance(e_location_ids, dict):
                if e_location_ids.get('EIdType') == 'doi':
                    return e_location_ids.get('#text', '')
        except:
            pass
        return None
    
    def _extract_authors(self, author_list: List[Dict]) -> str:
        """Extract author string from author list"""
        try:
            authors = []
            for author in author_list:
                if isinstance(author, dict):
                    last_name = author.get('LastName', '')
                    first_name = author.get('ForeName', '')
                    if last_name:
                        authors.append(f"{first_name} {last_name}".strip())
            return ', '.join(authors)
        except:
            return ''
    
    def match_article(self, endnote_article: Dict) -> Tuple[Optional[Dict], str]:
        """
        Match an EndNote article with LLM articles using fallback strategy
        
        Fallback order:
        1. PMID matching
        2. DOI matching
        3. Fuzzy title matching (with threshold)
        
        Returns:
            Tuple of (matched_article, match_method)
        """
        # Try PMID matching first
        if endnote_article.get('pmid'):
            pmid = endnote_article['pmid'].lower().strip()
            matched = self._match_by_pmid(pmid)
            if matched:
                return matched, 'pmid'
        
        # Try DOI matching
        if endnote_article.get('doi'):
            doi = endnote_article['doi'].lower().strip()
            matched = self._match_by_doi(doi)
            if matched:
                return matched, 'doi'
        
        # Try fuzzy title matching
        if endnote_article.get('title'):
            title = endnote_article['title'].strip()
            matched = self._match_by_title(title)
            if matched:
                return matched, 'title'
        
        return None, 'no_match'
    
    def _match_by_pmid(self, pmid: str) -> Optional[Dict]:
        """Match article by PMID"""
        for article in self.llm_articles:
            if article.get('pmid') == pmid:
                return article
        return None
    
    def _match_by_doi(self, doi: str) -> Optional[Dict]:
        """Match article by DOI"""
        # Normalize DOI
        doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '').strip()
        
        for article in self.llm_articles:
            if article.get('doi'):
                article_doi = article['doi'].replace('https://doi.org/', '').replace('http://dx.doi.org/', '').strip()
                if article_doi == doi:
                    return article
        return None
    
    def _match_by_title(self, title: str, threshold: int = 85) -> Optional[Dict]:
        """Match article by fuzzy title matching"""
        best_match = None
        best_score = 0
        
        for article in self.llm_articles:
            if article.get('title'):
                if FUZZYWUZZY_AVAILABLE:
                    score = fuzz.ratio(title, article['title'])
                else:
                    # Fallback to simple string comparison
                    title_lower = title.lower().strip()
                    article_title_lower = article['title'].lower().strip()
                    if title_lower == article_title_lower:
                        score = 100
                    elif title_lower in article_title_lower or article_title_lower in title_lower:
                        score = 80  # Partial match
                    else:
                        score = 0
                
                if score > best_score:
                    best_score = score
                    best_match = article
        
        if best_score >= threshold:
            return best_match
        
        return None
    
    def validate_with_endnote(self, endnote_articles: List[Dict]) -> Dict[str, Any]:
        """
        Validate LLM articles against EndNote articles
        
        Args:
            endnote_articles: List of EndNote articles from parser
            
        Returns:
            Dictionary containing validation results and metrics
        """
        matched_articles = []
        unmatched_manual = []
        unmatched_llm = []
        
        pmid_matches = 0
        doi_matches = 0
        title_matches = 0
        no_matches = 0
        
        # Match each EndNote article with LLM articles
        for endnote_article in endnote_articles:
            matched, method = self.match_article(endnote_article)
            
            if matched:
                matched_articles.append({
                    'endnote': endnote_article,
                    'llm': matched,
                    'match_method': method
                })
                
                if method == 'pmid':
                    pmid_matches += 1
                elif method == 'doi':
                    doi_matches += 1
                elif method == 'title':
                    title_matches += 1
            else:
                unmatched_manual.append(endnote_article)
                no_matches += 1
        
        # Find LLM articles that weren't matched
        matched_llm_articles = {a['llm']['file_path'] for a in matched_articles}
        for llm_article in self.llm_articles:
            if llm_article['file_path'] not in matched_llm_articles:
                unmatched_llm.append(llm_article)
        
        # Calculate match rates
        total_endnote = len(endnote_articles)
        total_llm = len(self.llm_articles)
        total_matched = len(matched_articles)
        
        match_rate = (total_matched / total_endnote * 100) if total_endnote > 0 else 0
        pmid_rate = (pmid_matches / total_matched * 100) if total_matched > 0 else 0
        doi_rate = (doi_matches / total_matched * 100) if total_matched > 0 else 0
        title_rate = (title_matches / total_matched * 100) if total_matched > 0 else 0
        
        results = {
            'matched_count': total_matched,
            'unmatched_manual_count': len(unmatched_manual),
            'unmatched_llm_count': len(unmatched_llm),
            'total_endnote': total_endnote,
            'total_llm': total_llm,
            'match_rate': match_rate,
            'pmid_matches': pmid_matches,
            'doi_matches': doi_matches,
            'title_matches': title_matches,
            'no_matches': no_matches,
            'match_rates': {
                'pmid_rate': pmid_rate,
                'doi_rate': doi_rate,
                'title_rate': title_rate
            },
            'matched_articles': matched_articles,
            'unmatched_manual': unmatched_manual,
            'unmatched_llm': unmatched_llm
        }
        
        # Log validation
        self.validation_log.append({
            'type': 'full_validation',
            'results': results
        })
        
        print(f"✅ Validation complete: {total_matched}/{total_endnote} matched ({match_rate:.1f}%)")
        print(f"   PMID: {pmid_matches}, DOI: {doi_matches}, Title: {title_matches}")
        
        return results
    
    def get_screening_comparison(self, endnote_screening: Dict, llm_screening: Dict) -> Dict[str, Any]:
        """
        Compare screening decisions between EndNote and LLM
        
        Args:
            endnote_screening: Dict mapping article identifiers to screening decisions
            llm_screening: Dict mapping article indices/paths to screening decisions
            
        Returns:
            Dictionary with confusion matrix metrics
        """
        # Match articles and get screening decisions
        tp = 0  # True Positive: Both include
        tn = 0  # True Negative: Both exclude
        fp = 0  # False Positive: LLM includes, EndNote excludes
        fn = 0  # False Negative: LLM excludes, EndNote includes
        
        matched_decisions = []
        
        for identifier, endnote_decision in endnote_screening.items():
            # Find corresponding LLM article
            matched_article, _ = self._find_matching_llm_article(identifier, endnote_screening)
            
            if matched_article and matched_article['file_path'] in llm_screening:
                llm_decision = llm_screening[matched_article['file_path']]
                
                # Normalize decisions
                endnote_inc = endnote_decision.upper() in ['INCLUDE', 'YES', 'INCLUDED']
                llm_inc = llm_decision.upper() in ['INCLUDE', 'YES', 'INCLUDED']
                
                if endnote_inc and llm_inc:
                    tp += 1
                elif not endnote_inc and not llm_inc:
                    tn += 1
                elif llm_inc and not endnote_inc:
                    fp += 1
                elif endnote_inc and not llm_inc:
                    fn += 1
                
                matched_decisions.append({
                    'identifier': identifier,
                    'endnote_decision': endnote_decision,
                    'llm_decision': llm_decision,
                    'agreement': endnote_inc == llm_inc
                })
        
        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        
        return {
            'tp': tp,
            'tn': tn,
            'fp': fp,
            'fn': fn,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'accuracy': accuracy,
            'matched_decisions': matched_decisions
        }
    
    def _find_matching_llm_article(self, identifier: str, endnote_articles: Dict) -> Optional[Dict]:
        """Helper to find matching LLM article by identifier"""
        # This would need to be implemented based on how identifiers are structured
        # For now, return None as placeholder
        return None
    
    def save_validation_log(self, output_path: str):
        """Save validation log to JSON file"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_log, f, indent=2, default=str)
        
        print(f"💾 Validation log saved to {output_path}")

