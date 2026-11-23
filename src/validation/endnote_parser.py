import xml.etree.ElementTree as ET
import json
import pandas as pd
from typing import List, Dict, Any
import re
import os

class EndNoteParser:
    def __init__(self, endnote_file_path: str):
        self.endnote_file_path = endnote_file_path
        self.all_articles = []
        self.pubmed_articles = []
    
    def parse_endnote_file(self) -> Dict[str, List[Dict[str, Any]]]:
        """Parse EndNote XML file and extract article data, separating PubMed articles for comparison"""
        try:
            tree = ET.parse(self.endnote_file_path)
            root = tree.getroot()
            
            all_articles = []
            pubmed_articles = []
            
            for record in root.findall('.//record'):
                article = self._extract_article_data(record)
                if article:
                    all_articles.append(article)
                    
                    # Check if this is a PubMed article for comparison
                    if self._is_pubmed_article(article):
                        pubmed_articles.append(article)
            
            self.all_articles = all_articles
            self.pubmed_articles = pubmed_articles
            
            print(f"📚 Parsed {len(all_articles)} total articles from EndNote file")
            print(f"🔬 Found {len(pubmed_articles)} PubMed articles for comparison")
            
            return {
                "all_articles": all_articles,
                "pubmed_articles": pubmed_articles
            }
            
        except Exception as e:
            print(f"❌ Error parsing EndNote file: {e}")
            return {"all_articles": [], "pubmed_articles": []}
    
    def _is_pubmed_article(self, article: Dict[str, Any]) -> bool:
        """Determine if an article is from PubMed based on various indicators"""
        
        # Check for PubMed-specific identifiers
        if article.get('pmid'):
            return True
        
        # Check database field if available
        database = article.get('database', '').lower()
        if 'pubmed' in database or 'medline' in database:
            return True
        
        # Check URL field for PubMed links
        url = article.get('url', '').lower()
        if 'pubmed' in url or 'ncbi.nlm.nih.gov' in url:
            return True
        
        # Check electronic resource number for PubMed format
        electronic_num = article.get('electronic_resource_num', '')
        if electronic_num and ('pmid' in electronic_num.lower() or 'pubmed' in electronic_num.lower()):
            return True
        
        # Check if it has MeSH terms (common in PubMed)
        if article.get('mesh_terms') and len(article['mesh_terms']) > 0:
            return True
        
        # Check journal field for medical journals (common in PubMed)
        journal = article.get('journal', '').lower()
        medical_journal_indicators = [
            'journal of', 'american journal', 'european journal', 'british journal',
            'new england journal', 'lancet', 'nature', 'science', 'plos',
            'bmj', 'jama', 'annals', 'archives'
        ]
        
        if any(indicator in journal for indicator in medical_journal_indicators):
            return True
        
        return False
    
    def _extract_article_data(self, record) -> Dict[str, Any]:
        """Extract article data from a single EndNote record"""
        article = {}
        
        # Extract basic information
        article['title'] = self._get_field_value(record, 'titles/title')
        article['authors'] = self._get_field_value(record, 'contributors/authors/author')
        article['journal'] = self._get_field_value(record, 'periodical/full-title')
        article['publication_date'] = self._get_field_value(record, 'dates/year')
        article['abstract'] = self._get_field_value(record, 'abstract')
        article['doi'] = self._get_field_value(record, 'electronic-resource-num')
        article['pmid'] = self._get_field_value(record, 'accession-num')
        article['url'] = self._get_field_value(record, 'urls/url')
        article['database'] = self._get_field_value(record, 'database')
        article['electronic_resource_num'] = self._get_field_value(record, 'electronic-resource-num')
        
        # Extract keywords and MeSH terms
        article['keywords'] = self._get_keywords(record)
        article['mesh_terms'] = self._get_mesh_terms(record)
        
        # Extract screening decisions (if available in custom fields)
        article['manual_screening_decision'] = self._get_field_value(record, 'custom1')
        article['manual_screening_reason'] = self._get_field_value(record, 'custom2')
        
        # Extract additional screening info from custom fields (commonly used)
        # custom1: Title/Abstract Screening Decision (INCLUDE/EXCLUDE)
        # custom2: Title/Abstract Screening Reason
        # custom3: Full-Text Screening Decision
        # custom4: Full-Text Screening Reason
        article['title_abstract_decision'] = self._get_field_value(record, 'custom1')
        article['title_abstract_reason'] = self._get_field_value(record, 'custom2')
        article['full_text_decision'] = self._get_field_value(record, 'custom3')
        article['full_text_reason'] = self._get_field_value(record, 'custom4')
        
        # Extract data extraction fields if available
        article['data_extraction_fields'] = self._get_data_extraction_fields(record)
        
        return article
    
    def _get_field_value(self, record, xpath: str) -> str:
        """Get field value using XPath"""
        element = record.find(xpath)
        return element.text.strip() if element is not None and element.text else ""
    
    def _get_keywords(self, record) -> List[str]:
        """Extract keywords from EndNote record"""
        keywords = []
        for keyword in record.findall('.//keyword'):
            if keyword.text:
                keywords.append(keyword.text.strip())
        return keywords
    
    def _get_mesh_terms(self, record) -> List[str]:
        """Extract MeSH terms from EndNote record"""
        mesh_terms = []
        for mesh in record.findall('.//mesh-heading'):
            if mesh.text:
                mesh_terms.append(mesh.text.strip())
        return mesh_terms
    
    def _get_data_extraction_fields(self, record) -> Dict[str, Any]:
        """Extract data extraction fields from EndNote custom fields"""
        extraction_fields = {}
        
        # Extract from custom5 onwards (user-defined data extraction fields)
        # This is a flexible extraction that reads any additional custom fields
        for i in range(5, 10):  # Typically use custom5-custom9 for data extraction
            custom_field = self._get_field_value(record, f'custom{i}')
            if custom_field:
                extraction_fields[f'custom{i}'] = custom_field
        
        return extraction_fields
    
    def save_to_json(self, output_path: str, articles_type: str = "all"):
        """Save parsed articles to JSON file silently"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if articles_type == "pubmed":
            articles_to_save = self.pubmed_articles
        else:
            articles_to_save = self.all_articles
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(articles_to_save, f, indent=2, ensure_ascii=False)
        
        print(f"💾 {articles_type.title()} articles saved to {output_path}")
    
    def get_pubmed_count(self) -> int:
        """Get count of PubMed articles"""
        return len(self.pubmed_articles)
    
    def get_total_count(self) -> int:
        """Get count of all articles"""
        return len(self.all_articles)

