"""
Title/Abstract Screening Validation Module

Validates LLM-based title/abstract screening against manual EndNote reviews.
"""

import json
import os
from typing import Dict, List, Any
from endnote_validator import EndNoteValidator
from endnote_parser import EndNoteParser
from validation_visualizer import ValidationVisualizer


class TitleAbstractValidator:
    """Validates title/abstract screening results"""
    
    def __init__(self, llm_articles_dir: str, llm_screening_results: Dict):
        """
        Initialize validator
        
        Args:
            llm_articles_dir: Directory containing LLM article files
            llm_screening_results: Dictionary mapping article indices/paths to screening decisions
        """
        self.validator = EndNoteValidator(llm_articles_dir)
        self.llm_screening_results = llm_screening_results
        self.visualizer = ValidationVisualizer()
    
    def validate_with_endnote(self, endnote_file_path: str) -> Dict[str, Any]:
        """
        Validate LLM screening against EndNote manual review
        
        Args:
            endnote_file_path: Path to EndNote XML file
            
        Returns:
            Validation results dictionary
        """
        # Parse EndNote file
        parser = EndNoteParser(endnote_file_path)
        endnote_data = parser.parse_endnote_file()
        endnote_articles = endnote_data['all_articles']
        
        # Get manual screening decisions
        manual_screening = {}
        manual_included = set()
        manual_excluded = set()
        
        for article in endnote_articles:
            # Create identifier (prefer PMID, fallback to title)
            identifier = article.get('pmid') or article.get('title') or str(hash(article.get('title', '')))
            
            # Get decision (check both formats)
            decision = (article.get('title_abstract_decision') or 
                       article.get('manual_screening_decision') or '').upper()
            
            manual_screening[identifier] = decision
            if decision in ['INCLUDE', 'INCLUDED', 'YES']:
                manual_included.add(identifier)
            elif decision in ['EXCLUDE', 'EXCLUDED', 'NO']:
                manual_excluded.add(identifier)
        
        # Get LLM screening decisions
        llm_included = set()
        llm_excluded = set()
        
        for article_path, result in self.llm_screening_results.items():
            decision = result.get('decision', '').upper()
            # Create identifier from article data
            article_data = self._get_article_from_path(article_path)
            identifier = article_data.get('pmid') or article_data.get('title') if article_data else article_path
            
            if decision in ['INCLUDE', 'INCLUDED', 'YES']:
                llm_included.add(identifier)
            else:
                llm_excluded.add(identifier)
        
        # Match articles
        validation_results = self.validator.validate_with_endnote(endnote_articles)
        matched_articles = validation_results['matched_articles']
        
        # Compare screening decisions
        tp = len(manual_included & llm_included)  # Both include
        tn = len(manual_excluded & llm_excluded)    # Both exclude
        fp = len(llm_included - manual_included)   # LLM includes, manual excludes
        fn = len(manual_included - llm_included)   # Manual includes, LLM excludes
        
        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        
        results = {
            'validation_results': validation_results,
            'confusion_matrix': {
                'tp': tp,
                'tn': tn,
                'fp': fp,
                'fn': fn
            },
            'metrics': {
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'accuracy': accuracy
            },
            'manual_included': len(manual_included),
            'manual_excluded': len(manual_excluded),
            'llm_included': len(llm_included),
            'llm_excluded': len(llm_excluded),
            'manual_articles': list(manual_included | manual_excluded),
            'llm_articles': list(llm_included | llm_excluded)
        }
        
        # Create visualization
        self.visualizer.create_venn_diagram(
            manual_included | manual_excluded,
            llm_included | llm_excluded,
            ('Manual Review', 'LLM Framework'),
            'Title/Abstract Screening: Article Coverage',
            'title_abstract_coverage_venn.png'
        )
        
        self.visualizer.create_confusion_matrix(
            tp, tn, fp, fn,
            'Title/Abstract Screening Confusion Matrix',
            'title_abstract_confusion_matrix.png'
        )
        
        return results
    
    def _get_article_from_path(self, article_path: str) -> Dict[str, Any]:
        """Get article data from file path"""
        try:
            with open(article_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                medline_citation = data.get('MedlineCitation', {})
                article_info = medline_citation.get('Article', {})
                
                return {
                    'pmid': medline_citation.get('PMID', {}).get('#text', '') if isinstance(medline_citation.get('PMID'), dict) else str(medline_citation.get('PMID', '')),
                    'title': article_info.get('ArticleTitle', ''),
                    'file_path': article_path
                }
        except:
            return {'file_path': article_path}
    
    def save_results(self, results: Dict, output_path: str):
        """Save validation results to JSON"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Title/abstract validation results saved to {output_path}")


