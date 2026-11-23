"""
Quality Scoring Module

Implements PRISMA checklist-based quality assessment for systematic reviews.
Evaluates data extraction completeness and quality.
"""

import re
from typing import Dict, List, Any, Tuple
import json


class PRISMAQualityScorer:
    """
    PRISMA-based quality scorer for systematic review articles
    """
    
    # PRISMA 2020 Checklist Items
    PRISMA_CRITERIA = {
        'title': {
            'items': [
                'title_mentions_review',
                'title_mentions_systematic'
            ],
            'weight': 0.05
        },
        'abstract': {
            'items': [
                'abstract_structured',
                'abstract_mentions_objectives',
                'abstract_mentions_methods',
                'abstract_mentions_results',
                'abstract_mentions_conclusions',
                'abstract_protocol_registration'
            ],
            'weight': 0.10
        },
        'introduction': {
            'items': [
                'rationale_provided',
                'objectives_specified'
            ],
            'weight': 0.10
        },
        'methods': {
            'items': [
                'eligibility_criteria',
                'information_sources',
                'search_strategy',
                'search_date_range',
                'study_selection_process',
                'data_collection_process',
                'data_items_listed',
                'study_risk_of_bias_assessment',
                'effect_measures_specified',
                'analysis_methods_specified'
            ],
            'weight': 0.35
        },
        'results': {
            'items': [
                'study_selection_diagram',
                'study_characteristics_table',
                'risk_of_bias_results',
                'results_presented',
                'certainty_of_evidence_assessed'
            ],
            'weight': 0.20
        },
        'discussion': {
            'items': [
                'summary_provided',
                'limitations_discussed',
                'interpretation_provided',
                'funder_information'
            ],
            'weight': 0.15
        },
        'other': {
            'items': [
                'declaration_of_interest',
                'registration_available',
                'data_availability_statement'
            ],
            'weight': 0.05
        }
    }
    
    def __init__(self):
        """Initialize PRISMA quality scorer"""
        self.criteria = self.PRISMA_CRITERIA
    
    def assess_article_quality(self, extracted_data: Dict[str, Any], 
                              full_text: str = "") -> Dict[str, Any]:
        """
        Assess article quality using PRISMA checklist
        
        Args:
            extracted_data: Dictionary of extracted data fields
            full_text: Full text of the article (optional)
            
        Returns:
            Dictionary with quality scores and assessments
        """
        scores = {}
        
        # Assess each PRISMA section
        for section, criteria in self.criteria.items():
            section_score = self._assess_section(section, criteria, extracted_data, full_text)
            scores[section] = {
                'score': section_score,
                'total_items': len(criteria['items']),
                'weight': criteria['weight']
            }
        
        # Calculate overall weighted score
        overall_score = sum(
            scores[section]['score'] * scores[section]['weight']
            for section in scores
        )
        
        # Additional quality metrics
        completeness = self._assess_completeness(extracted_data)
        accuracy = self._assess_accuracy(extracted_data)
        
        return {
            'overall_score': overall_score * 100,  # Scale to 0-100
            'section_scores': scores,
            'completeness_score': completeness,
            'accuracy_score': accuracy,
            'quality_grade': self._get_quality_grade(overall_score * 100)
        }
    
    def _assess_section(self, section: str, criteria: Dict, 
                       extracted_data: Dict, full_text: str) -> float:
        """Assess a specific PRISMA section"""
        items_found = 0
        
        for item in criteria['items']:
            if self._check_prisma_item(item, extracted_data, full_text):
                items_found += 1
        
        return items_found / len(criteria['items']) if criteria['items'] else 0
    
    def _check_prisma_item(self, item: str, extracted_data: Dict, 
                          full_text: str) -> bool:
        """Check if a specific PRISMA item is present"""
        
        # Check in extracted data first
        if item in extracted_data:
            value = extracted_data[item]
            if value and value != 'N/A' and value != '':
                return True
        
        # Check in full text if available
        if full_text:
            search_patterns = {
                'title_mentions_review': r'\breview\b',
                'title_mentions_systematic': r'\bsystematic\b',
                'rationale_provided': r'(rationale|background|context)',
                'objectives_specified': r'objective[s]?|aim[s]?|goal[s]?',
                'eligibility_criteria': r'inclusion|exclusion.*criteri[ao]',
                'information_sources': r'database[s]?|search.*database',
                'search_strategy': r'search.*strategy',
                'study_selection_process': r'study.*selection',
                'data_collection_process': r'data.*collect',
                'study_risk_of_bias_assessment': r'risk.*bias|quality.*assess',
                'results_presented': r'result[s]?',
                'limitations_discussed': r'limitation[s]?',
                'declaration_of_interest': r'conflict[s]?.*interest|declaration.*interest',
                'protocol_registration': r'protocol|registered',
                'data_availability_statement': r'data.*available'
            }
            
            if item in search_patterns:
                pattern = search_patterns[item]
                if re.search(pattern, full_text, re.IGNORECASE):
                    return True
        
        return False
    
    def _assess_completeness(self, extracted_data: Dict) -> float:
        """Assess completeness of extracted data fields"""
        required_fields = [
            'title', 'authors', 'publication_date', 'journal',
            'abstract', 'methods', 'results', 'conclusions'
        ]
        
        if not required_fields:
            return 0.0
        
        fields_present = sum(
            1 for field in required_fields
            if field in extracted_data and extracted_data[field] and extracted_data[field] not in ['N/A', '']
        )
        
        return fields_present / len(required_fields)
    
    def _assess_accuracy(self, extracted_data: Dict) -> float:
        """Assess accuracy of extracted data (placeholder)"""
        # This would require comparison with manual extraction
        # For now, return a default score based on data quality checks
        
        accuracy_indicators = [
            'numerical_consistency',  # Are numbers consistent?
            'date_format_correct',    # Are dates in correct format?
            'author_format_consistent'  # Are authors properly formatted?
        ]
        
        # Simple heuristic: check if key fields exist and are not empty
        key_fields = ['title', 'authors', 'publication_date', 'journal']
        accurate_fields = sum(
            1 for field in key_fields
            if field in extracted_data and extracted_data[field] not in ['N/A', '', None]
        )
        
        return accurate_fields / len(key_fields) if key_fields else 0.5
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C'
        else:
            return 'D'
    
    def compare_extractions(self, manual_extraction: Dict, 
                           llm_extraction: Dict) -> Dict[str, Any]:
        """
        Compare manual and LLM extractions
        
        Args:
            manual_extraction: Manually extracted data
            llm_extraction: LLM-extracted data
            
        Returns:
            Comparison metrics and results
        """
        all_fields = set(list(manual_extraction.keys()) + list(llm_extraction.keys()))
        
        comparison = {
            'agreement_rate': 0.0,
            'field_agreement': {},
            'manual_only': [],
            'llm_only': [],
            'disagreements': []
        }
        
        agreements = 0
        total_compared = 0
        
        for field in all_fields:
            manual_value = manual_extraction.get(field, '')
            llm_value = llm_extraction.get(field, '')
            
            # Skip empty fields
            if not manual_value and not llm_value:
                continue
            
            total_compared += 1
            
            # Check agreement (using simple string comparison)
            manual_norm = str(manual_value).lower().strip()
            llm_norm = str(llm_value).lower().strip()
            
            is_agreement = manual_norm == llm_norm
            comparison['field_agreement'][field] = is_agreement
            
            if is_agreement:
                agreements += 1
            else:
                comparison['disagreements'].append({
                    'field': field,
                    'manual': manual_value,
                    'llm': llm_value
                })
        
        comparison['agreement_rate'] = agreements / total_compared if total_compared > 0 else 0
        comparison['manual_only'] = [f for f in manual_extraction.keys() if f not in llm_extraction]
        comparison['llm_only'] = [f for f in llm_extraction.keys() if f not in manual_extraction]
        
        return comparison


