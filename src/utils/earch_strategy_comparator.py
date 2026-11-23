"""
Search strategy comparison engine for generating reports.
Compares LLM-generated strategies with manual gold standard.
"""

import json
import re
from typing import Dict, List, Tuple
from manual_search_strategy import get_manual_strategy

class SearchStrategyComparator:
    def __init__(self):
        self.manual_strategy = get_manual_strategy()
    
    def compare_keywords(self, llm_keywords: List[str]) -> Dict:
        """Compare LLM-extracted keywords with manual keywords"""
        
        # Normalize keywords
        manual_keywords = [k.lower().strip() for k in self.manual_strategy["manual_keywords"]]
        llm_keywords_norm = [k.lower().strip() for k in llm_keywords]
        
        # Calculate metrics
        true_positives = len(set(llm_keywords_norm) & set(manual_keywords))
        false_positives = len(set(llm_keywords_norm) - set(manual_keywords))
        false_negatives = len(set(manual_keywords) - set(llm_keywords_norm))
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "matched_keywords": list(set(llm_keywords_norm) & set(manual_keywords)),
            "missed_keywords": list(set(manual_keywords) - set(llm_keywords_norm)),
            "extra_keywords": list(set(llm_keywords_norm) - set(manual_keywords))
        }
    
    def compare_concept_coverage(self, grouped_terms: Dict) -> Dict:
        """Compare concept coverage between manual and LLM strategies"""
        
        manual_concepts = self.manual_strategy["concept_groups"]
        llm_concepts = self._extract_llm_concepts(grouped_terms)
        
        concept_comparison = {}
        for concept_name, manual_terms in manual_concepts.items():
            llm_terms = llm_concepts.get(concept_name, [])
            
            # Calculate coverage for this concept
            manual_terms_norm = [t.lower().strip() for t in manual_terms]
            llm_terms_norm = [t.lower().strip() for t in llm_terms]
            
            coverage = len(set(llm_terms_norm) & set(manual_terms_norm)) / len(manual_terms_norm) if manual_terms_norm else 0
            
            concept_comparison[concept_name] = {
                "manual_terms": manual_terms,
                "llm_terms": llm_terms,
                "coverage": coverage,
                "matched_terms": list(set(llm_terms_norm) & set(manual_terms_norm)),
                "missed_terms": list(set(manual_terms_norm) - set(llm_terms_norm)),
                "extra_terms": list(set(llm_terms_norm) - set(manual_terms_norm))
            }
        
        return concept_comparison
    
    def compare_boolean_queries(self, llm_query: str) -> Dict:
        """Compare Boolean query structure and complexity"""
        
        manual_query = self.manual_strategy["manual_boolean_query"]
        
        # Analyze query structure
        manual_analysis = self._analyze_query_structure(manual_query)
        llm_analysis = self._analyze_query_structure(llm_query)
        
        return {
            "manual_query": manual_query,
            "llm_query": llm_query,
            "manual_analysis": manual_analysis,
            "llm_analysis": llm_analysis,
            "structure_similarity": self._calculate_structure_similarity(manual_analysis, llm_analysis)
        }
    
    def _extract_llm_concepts(self, grouped_terms: Dict) -> Dict:
        """Extract concepts from LLM grouped terms"""
        
        concepts = {
            "hypertension_concepts": [],
            "metabolomics_concepts": [],
            "antihypertensive_drugs": [],
            "treatment_response": []
        }
        
        for keyword, mesh_terms in grouped_terms.items():
            keyword_lower = keyword.lower()
            
            # Categorize keywords
            if any(term in keyword_lower for term in ["hypertension", "blood pressure", "htn"]):
                concepts["hypertension_concepts"].append(keyword)
            elif any(term in keyword_lower for term in ["metabolomics", "metabolome", "metabolites", "pharmacometabolomics"]):
                concepts["metabolomics_concepts"].append(keyword)
            elif any(term in keyword_lower for term in ["antihypertensive", "diuretics", "beta-blockers", "ace inhibitors", "arbs"]):
                concepts["antihypertensive_drugs"].append(keyword)
            elif any(term in keyword_lower for term in ["treatment response", "drug response", "therapeutic response"]):
                concepts["treatment_response"].append(keyword)
        
        return concepts
    
    def _analyze_query_structure(self, query: str) -> Dict:
        """Analyze Boolean query structure"""
        
        # Count operators
        and_count = len(re.findall(r'\bAND\b', query, re.IGNORECASE))
        or_count = len(re.findall(r'\bOR\b', query, re.IGNORECASE))
        not_count = len(re.findall(r'\bNOT\b', query, re.IGNORECASE))
        
        # Count parentheses
        paren_count = query.count('(')
        
        # Count field tags
        field_tags = len(re.findall(r'\[([^\]]+)\]', query))
        
        # Count quoted terms
        quoted_terms = len(re.findall(r'"([^"]+)"', query))
        
        return {
            "and_operators": and_count,
            "or_operators": or_count,
            "not_operators": not_count,
            "parentheses": paren_count,
            "field_tags": field_tags,
            "quoted_terms": quoted_terms,
            "total_length": len(query)
        }
    
    def _calculate_structure_similarity(self, manual_analysis: Dict, llm_analysis: Dict) -> float:
        """Calculate similarity between query structures"""
        
        # Simple similarity based on operator ratios
        manual_total_ops = manual_analysis["and_operators"] + manual_analysis["or_operators"]
        llm_total_ops = llm_analysis["and_operators"] + llm_analysis["or_operators"]
        
        if manual_total_ops == 0 and llm_total_ops == 0:
            return 1.0
        
        if manual_total_ops == 0 or llm_total_ops == 0:
            return 0.0
        
        # Calculate operator ratio similarity
        manual_and_ratio = manual_analysis["and_operators"] / manual_total_ops
        llm_and_ratio = llm_analysis["and_operators"] / llm_total_ops
        
        ratio_similarity = 1 - abs(manual_and_ratio - llm_and_ratio)
        
        return ratio_similarity
    
    def generate_comprehensive_report(self, llm_keywords: List[str], grouped_terms: Dict, llm_query: str) -> Dict:
        """Generate comprehensive comparison report"""
        
        keyword_comparison = self.compare_keywords(llm_keywords)
        concept_comparison = self.compare_concept_coverage(grouped_terms)
        query_comparison = self.compare_boolean_queries(llm_query)
        
        # Calculate overall performance score
        overall_score = (
            keyword_comparison["f1_score"] * 0.4 +
            sum(concept_comparison[c]["coverage"] for c in concept_comparison) / len(concept_comparison) * 0.4 +
            query_comparison["structure_similarity"] * 0.2
        )
        
        return {
            "overall_performance": {
                "score": overall_score,
                "grade": self._get_performance_grade(overall_score)
            },
            "keyword_comparison": keyword_comparison,
            "concept_comparison": concept_comparison,
            "query_comparison": query_comparison,
            "recommendations": self._generate_recommendations(keyword_comparison, concept_comparison, query_comparison)
        }
    
    def _get_performance_grade(self, score: float) -> str:
        """Convert score to grade"""
        if score >= 0.9:
            return "A+"
        elif score >= 0.8:
            return "A"
        elif score >= 0.7:
            return "B+"
        elif score >= 0.6:
            return "B"
        elif score >= 0.5:
            return "C"
        else:
            return "D"
    
    def _generate_recommendations(self, keyword_comp: Dict, concept_comp: Dict, query_comp: Dict) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if keyword_comp["recall"] < 0.5:
            recommendations.append("Improve keyword extraction to capture more manual keywords")
        
        if keyword_comp["precision"] < 0.5:
            recommendations.append("Reduce false positive keywords by improving keyword filtering")
        
        low_coverage_concepts = [c for c, data in concept_comp.items() if data["coverage"] < 0.5]
        if low_coverage_concepts:
            recommendations.append(f"Improve coverage for concepts: {', '.join(low_coverage_concepts)}")
        
        if query_comp["structure_similarity"] < 0.7:
            recommendations.append("Improve Boolean query structure to better match manual strategy")
        
        return recommendations
    def train_llm_with_manual_examples(manual_strategy, endnote_results):
    """Use manual strategy and EndNote results as training examples for the LLM"""
    # 1. Extract successful patterns from manual query
    manual_query = manual_strategy["manual_boolean_query"]
    concept_groups = manual_strategy["concept_groups"]
    
    # 2. Create training examples with variations
    training_examples = []
    
    # Example 1: Original manual query
    training_examples.append({
        "query": manual_query,
        "performance": "high recall and precision",
        "retrieved_count": len(endnote_results)
    })
    
    # Example 2-N: Variations with different structures but same concepts
    for i in range(3):  # Generate 3 variations
        variation = create_query_variation(concept_groups, i)
        training_examples.append({
            "query": variation,
            "performance": "good alternative structure",
            "intent": f"emphasize {'recall' if i % 2 == 0 else 'precision'}"
        })
    
    return training_examples