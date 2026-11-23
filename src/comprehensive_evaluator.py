import json
import pandas as pd
from typing import Dict, List, Tuple, Any
import os
from search_strategy_comparator import SearchStrategyComparator
from endnote_parser import EndNoteParser

class ComprehensiveEvaluator:
    def __init__(self, manual_endnote_file: str = None):
        self.manual_endnote_file = manual_endnote_file
        self.all_manual_data = None  # All articles for training
        self.pubmed_manual_data = None  # Only PubMed articles for comparison
        self.comparator = SearchStrategyComparator()
        
    def load_manual_data(self):
        """Load manual review data from EndNote file, separating all articles from PubMed-only articles"""
        if not self.manual_endnote_file or not os.path.exists(self.manual_endnote_file):
            print("⚠️ No EndNote file provided or file not found")
            return
        
        parser = EndNoteParser(self.manual_endnote_file)
        parsed_data = parser.parse_endnote_file()
        
        self.all_manual_data = parsed_data["all_articles"]
        self.pubmed_manual_data = parsed_data["pubmed_articles"]
        
        # Save parsed data for future use
        parser.save_to_json("data/all_manual_articles.json", "all")
        parser.save_to_json("data/pubmed_manual_articles.json", "pubmed")
        
        print(f"📚 Loaded {len(self.all_manual_data)} total articles for training")
        print(f"🔬 Loaded {len(self.pubmed_manual_data)} PubMed articles for retrieval comparison")
    
    def evaluate_keywords(self, llm_keywords: List[str]) -> Dict[str, float]:
        """Evaluate keyword extraction performance using ALL manual articles for training"""
        manual_keywords = self.comparator.manual_strategy["manual_keywords"]
        
        # Normalize keywords
        manual_norm = [k.lower().strip() for k in manual_keywords]
        llm_norm = [k.lower().strip() for k in llm_keywords]
        
        # Calculate metrics
        true_positives = len(set(llm_norm) & set(manual_norm))
        false_positives = len(set(llm_norm) - set(manual_norm))
        false_negatives = len(set(manual_norm) - set(llm_norm))
        
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
            "training_articles_count": len(self.all_manual_data) if self.all_manual_data else 0
        }
    
    def evaluate_mesh_terms(self, llm_grouped_terms: Dict) -> Dict[str, float]:
        """Evaluate MeSH term extraction performance using ALL manual articles for training"""
        manual_mesh = self.comparator.manual_strategy["manual_mesh_terms"]
        
        # Extract LLM MeSH terms
        llm_mesh_terms = []
        for keyword, terms in llm_grouped_terms.items():
            for term in terms:
                if '[MeSH Terms]' in term:
                    llm_mesh_terms.append(term)
        
        # Normalize terms
        manual_norm = [t.lower().strip() for t in manual_mesh]
        llm_norm = [t.lower().strip() for t in llm_mesh_terms]
        
        # Calculate metrics
        true_positives = len(set(llm_norm) & set(manual_norm))
        false_positives = len(set(llm_norm) - set(manual_norm))
        false_negatives = len(set(manual_norm) - set(llm_norm))
        
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
            "training_articles_count": len(self.all_manual_data) if self.all_manual_data else 0
        }
    
    def evaluate_search_query(self, llm_query: str) -> Dict[str, float]:
        """Evaluate search query structure and effectiveness using ALL manual articles for training"""
        manual_query = self.comparator.manual_strategy["manual_boolean_query"]
        
        # Analyze query structure
        manual_analysis = self.comparator._analyze_query_structure(manual_query)
        llm_analysis = self.comparator._analyze_query_structure(llm_query)
        
        # Calculate structural similarity
        structure_similarity = self.comparator._calculate_structure_similarity(manual_analysis, llm_analysis)
        
        # Calculate concept coverage
        manual_concepts = self.comparator.manual_strategy["concept_groups"]
        llm_concepts = self.comparator._extract_llm_concepts({})
        
        concept_coverage = 0
        for concept_name, manual_terms in manual_concepts.items():
            llm_terms = llm_concepts.get(concept_name, [])
            manual_norm = [t.lower().strip() for t in manual_terms]
            llm_norm = [t.lower().strip() for t in llm_terms]
            
            if manual_norm:
                coverage = len(set(llm_norm) & set(manual_norm)) / len(manual_norm)
                concept_coverage += coverage
        
        concept_coverage = concept_coverage / len(manual_concepts)
        
        # Overall query effectiveness score
        query_score = (structure_similarity * 0.6 + concept_coverage * 0.4)
        
        return {
            "structure_similarity": structure_similarity,
            "concept_coverage": concept_coverage,
            "query_effectiveness": query_score,
            "f1_score": query_score,
            "training_articles_count": len(self.all_manual_data) if self.all_manual_data else 0
        }
    
    def evaluate_article_retrieval(self, llm_articles: List[str]) -> Dict[str, float]:
        """Evaluate article retrieval performance using ONLY PubMed articles for comparison"""
        if not self.pubmed_manual_data:
            return {"error": "PubMed manual data not loaded", "f1_score": 0.0}
        
        # Extract PubMed article identifiers for comparison
        pubmed_identifiers = []
        for article in self.pubmed_manual_data:
            if article.get('pmid'):
                pubmed_identifiers.append(article['pmid'].lower())
            elif article.get('doi'):
                pubmed_identifiers.append(article['doi'].lower())
            elif article.get('title'):
                pubmed_identifiers.append(article['title'].lower())
        
        # Extract LLM article identifiers
        llm_identifiers = []
        for article_path in llm_articles:
            try:
                with open(article_path, 'r') as f:
                    article_data = json.load(f)
                    if 'pmid' in article_data:
                        llm_identifiers.append(article_data['pmid'].lower())
                    elif 'doi' in article_data:
                        llm_identifiers.append(article_data['doi'].lower())
                    elif 'title' in article_data:
                        llm_identifiers.append(article_data['title'].lower())
            except:
                continue
        
        # Calculate retrieval metrics
        true_positives = len(set(llm_identifiers) & set(pubmed_identifiers))
        false_positives = len(set(llm_identifiers) - set(pubmed_identifiers))
        false_negatives = len(set(pubmed_identifiers) - set(llm_identifiers))
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        # Calculate Jaccard similarity
        union = set(llm_identifiers) | set(pubmed_identifiers)
        jaccard = len(set(llm_identifiers) & set(pubmed_identifiers)) / len(union) if union else 0
        
        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "jaccard": jaccard,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "pubmed_articles_count": len(pubmed_identifiers),
            "llm_articles_count": len(llm_identifiers),
            "comparison_note": "Compared against PubMed articles only (n=1507)"
        }
    
    def evaluate_screening(self, llm_screening_results: Dict) -> Dict[str, float]:
        """Evaluate screening performance using ONLY PubMed articles for comparison"""
        if not self.pubmed_manual_data:
            return {"error": "PubMed manual data not loaded", "f1_score": 0.0}
        
        # Extract PubMed screening decisions
        pubmed_decisions = {}
        for i, article in enumerate(self.pubmed_manual_data):
            if article.get('manual_screening_decision'):
                decision = article['manual_screening_decision'].upper()
                pubmed_decisions[i] = decision
        
        # Extract LLM screening decisions
        llm_decisions = {}
        for article_idx, result in llm_screening_results.items():
            llm_decisions[int(article_idx)] = result['decision']
        
        # Calculate screening agreement
        common_articles = set(pubmed_decisions.keys()) & set(llm_decisions.keys())
        
        if not common_articles:
            return {"error": "No common articles for screening comparison", "f1_score": 0.0}
        
        correct_decisions = 0
        total_decisions = len(common_articles)
        
        for article_idx in common_articles:
            if pubmed_decisions[article_idx] == llm_decisions[article_idx]:
                correct_decisions += 1
        
        accuracy = correct_decisions / total_decisions if total_decisions > 0 else 0
        
        # Calculate precision, recall, F1 for INCLUDE decisions
        pubmed_includes = [idx for idx, decision in pubmed_decisions.items() if decision == 'INCLUDE']
        llm_includes = [idx for idx, decision in llm_decisions.items() if decision == 'INCLUDE']
        
        true_positives = len(set(pubmed_includes) & set(llm_includes))
        false_positives = len(set(llm_includes) - set(pubmed_includes))
        false_negatives = len(set(pubmed_includes) - set(llm_includes))
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "correct_decisions": correct_decisions,
            "total_decisions": total_decisions,
            "pubmed_includes": len(pubmed_includes),
            "llm_includes": len(llm_includes),
            "comparison_note": "Compared against PubMed articles only (n=1507)"
        }
    
    def evaluate_data_extraction(self, llm_extracted_data: List[Dict]) -> Dict[str, float]:
        """Evaluate data extraction performance using ALL manual articles for training"""
        # Placeholder for data extraction evaluation
        return {
            "extraction_completeness": 0.0,
            "field_accuracy": 0.0,
            "f1_score": 0.0,
            "training_articles_count": len(self.all_manual_data) if self.all_manual_data else 0
        }
    
    def generate_comprehensive_report(self, 
                                    llm_keywords: List[str],
                                    llm_grouped_terms: Dict,
                                    llm_query: str,
                                    llm_articles: List[str],
                                    llm_screening_results: Dict,
                                    llm_extracted_data: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive evaluation report silently"""
        
        if not self.all_manual_data or not self.pubmed_manual_data:
            self.load_manual_data()
        
        # Evaluate each step
        keyword_eval = self.evaluate_keywords(llm_keywords)
        mesh_eval = self.evaluate_mesh_terms(llm_grouped_terms)
        query_eval = self.evaluate_search_query(llm_query)
        retrieval_eval = self.evaluate_article_retrieval(llm_articles)
        screening_eval = self.evaluate_screening(llm_screening_results)
        extraction_eval = self.evaluate_data_extraction(llm_extracted_data)
        
        # Calculate overall performance
        step_scores = [
            keyword_eval.get('f1_score', 0),
            mesh_eval.get('f1_score', 0),
            query_eval.get('f1_score', 0),
            retrieval_eval.get('f1_score', 0),
            screening_eval.get('f1_score', 0),
            extraction_eval.get('f1_score', 0)
        ]
        
        overall_score = sum(step_scores) / len(step_scores)
        
        report = {
            "overall_performance": {
                "score": overall_score,
                "grade": self._get_performance_grade(overall_score)
            },
            "step_evaluations": {
                "keywords": keyword_eval,
                "mesh_terms": mesh_eval,
                "search_query": query_eval,
                "article_retrieval": retrieval_eval,
                "screening": screening_eval,
                "data_extraction": extraction_eval
            },
            "summary": {
                "total_steps": 6,
                "completed_steps": len([s for s in step_scores if s > 0]),
                "average_f1": overall_score,
                "best_performing_step": self._get_best_step(step_scores),
                "worst_performing_step": self._get_worst_step(step_scores),
                "training_articles_count": len(self.all_manual_data) if self.all_manual_data else 0,
                "pubmed_comparison_count": len(self.pubmed_manual_data) if self.pubmed_manual_data else 0
            }
        }
        
        # Save report silently
        self._save_comprehensive_report(report)
        
        return report
    
    def _save_comprehensive_report(self, report: Dict):
        """Save comprehensive report to files silently"""
        try:
            from datetime import datetime
            
            # Save JSON report (always overwrite with latest)
            json_path = "data/comprehensive_evaluation_report.json"
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            
            # Add generation timestamp to report
            if 'generation_timestamp' not in report:
                report['generation_timestamp'] = datetime.now().isoformat()
            
            with open(json_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
            
            # Generate and save markdown report (always overwrite with latest)
            markdown_content = self._generate_markdown_report(report)
            md_path = "data/comprehensive_evaluation_report.md"
            
            with open(md_path, "w") as f:
                f.write(markdown_content)
            
            print(f"📊 Comprehensive evaluation reports saved:")
            print(f"   - JSON: {json_path}")
            print(f"   - Markdown: {md_path}")
            print(f"📈 Overall Performance: {report['overall_performance']['score']:.2f} ({report['overall_performance']['grade']})")
            print(f"📚 Training articles: {report['summary']['training_articles_count']}")
            print(f"🔬 PubMed comparison articles: {report['summary']['pubmed_comparison_count']}")
            
        except Exception as e:
            print(f"❌ Error saving comprehensive report: {e}")
    
    def _generate_markdown_report(self, evaluation_data: Dict) -> str:
        """Generate markdown report from evaluation data"""
        
        report = f"""# Comprehensive LLM vs Manual Systematic Review Evaluation

## Overall Performance
- **Overall Score**: {evaluation_data['overall_performance']['score']:.2f}
- **Grade**: {evaluation_data['overall_performance']['grade']}
- **Completed Steps**: {evaluation_data['summary']['completed_steps']}/{evaluation_data['summary']['total_steps']}

## Training and Comparison Data
- **Training Articles**: {evaluation_data['summary']['training_articles_count']} (All databases)
- **Retrieval Comparison**: {evaluation_data['summary']['pubmed_comparison_count']} (PubMed only)

## Step-by-Step Evaluation

### 1. Keyword Extraction
- **F1 Score**: {evaluation_data['step_evaluations']['keywords']['f1_score']:.2f}
- **Precision**: {evaluation_data['step_evaluations']['keywords']['precision']:.2f}
- **Recall**: {evaluation_data['step_evaluations']['keywords']['recall']:.2f}
- **Training Articles**: {evaluation_data['step_evaluations']['keywords'].get('training_articles_count', 'N/A')}

### 2. MeSH Terms Extraction
- **F1 Score**: {evaluation_data['step_evaluations']['mesh_terms']['f1_score']:.2f}
- **Precision**: {evaluation_data['step_evaluations']['mesh_terms']['precision']:.2f}
- **Recall**: {evaluation_data['step_evaluations']['mesh_terms']['recall']:.2f}
- **Training Articles**: {evaluation_data['step_evaluations']['mesh_terms'].get('training_articles_count', 'N/A')}

### 3. Search Query Generation
- **Query Effectiveness**: {evaluation_data['step_evaluations']['search_query']['query_effectiveness']:.2f}
- **Structure Similarity**: {evaluation_data['step_evaluations']['search_query']['structure_similarity']:.2f}
- **Concept Coverage**: {evaluation_data['step_evaluations']['search_query']['concept_coverage']:.2f}
- **Training Articles**: {evaluation_data['step_evaluations']['search_query'].get('training_articles_count', 'N/A')}

### 4. Article Retrieval
- **F1 Score**: {evaluation_data['step_evaluations']['article_retrieval']['f1_score']:.2f}
- **Precision**: {evaluation_data['step_evaluations']['article_retrieval']['precision']:.2f}
- **Recall**: {evaluation_data['step_evaluations']['article_retrieval']['recall']:.2f}
- **PubMed Articles**: {evaluation_data['step_evaluations']['article_retrieval'].get('pubmed_articles_count', 'N/A')}
- **LLM Articles**: {evaluation_data['step_evaluations']['article_retrieval'].get('llm_articles_count', 'N/A')}
- **Note**: {evaluation_data['step_evaluations']['article_retrieval'].get('comparison_note', '')}

### 5. Article Screening
- **F1 Score**: {evaluation_data['step_evaluations']['screening']['f1_score']:.2f}
- **Accuracy**: {evaluation_data['step_evaluations']['screening'].get('accuracy', 0):.2f}
- **Precision**: {evaluation_data['step_evaluations']['screening']['precision']:.2f}
- **Recall**: {evaluation_data['step_evaluations']['screening']['recall']:.2f}
- **PubMed Includes**: {evaluation_data['step_evaluations']['screening'].get('pubmed_includes', 'N/A')}
- **LLM Includes**: {evaluation_data['step_evaluations']['screening'].get('llm_includes', 'N/A')}
- **Note**: {evaluation_data['step_evaluations']['screening'].get('comparison_note', '')}

### 6. Data Extraction
- **F1 Score**: {evaluation_data['step_evaluations']['data_extraction']['f1_score']:.2f}
- **Extraction Completeness**: {evaluation_data['step_evaluations']['data_extraction']['extraction_completeness']:.2f}
- **Field Accuracy**: {evaluation_data['step_evaluations']['data_extraction']['field_accuracy']:.2f}
- **Training Articles**: {evaluation_data['step_evaluations']['data_extraction'].get('training_articles_count', 'N/A')}

## Summary
- **Best Performing Step**: {evaluation_data['summary']['best_performing_step']}
- **Worst Performing Step**: {evaluation_data['summary']['worst_performing_step']}
- **Average F1 Score**: {evaluation_data['summary']['average_f1']:.2f}

## Methodology Notes
- **Training**: Uses all articles from EndNote library for model training and keyword/MeSH term evaluation
- **Retrieval Comparison**: Uses only PubMed articles (n=1507) for fair comparison with LLM PubMed search results
- **Screening Comparison**: Uses only PubMed articles for screening decision comparison

## Recommendations
Based on the evaluation results, focus improvement efforts on the {evaluation_data['summary']['worst_performing_step']} step to enhance overall framework performance.
"""
        
        return report
    
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
    
    def _get_best_step(self, scores: List[float]) -> str:
        """Get the best performing step"""
        steps = ["keywords", "mesh_terms", "search_query", "article_retrieval", "screening", "data_extraction"]
        max_idx = scores.index(max(scores))
        return steps[max_idx]
    
    def _get_worst_step(self, scores: List[float]) -> str:
        """Get the worst performing step"""
        steps = ["keywords", "mesh_terms", "search_query", "article_retrieval", "screening", "data_extraction"]
        min_idx = scores.index(min(scores))
        return steps[min_idx]

