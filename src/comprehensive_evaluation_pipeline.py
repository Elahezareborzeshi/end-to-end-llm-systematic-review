"""
Comprehensive evaluation pipeline for testing multiple LLM queries
"""
import json
import os
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from endnote_parser import EndNoteParser
from enhanced_metrics import calculate_overlap_metrics, calculate_detailed_matching_stats
from validation_visualizer import ValidationVisualizer
from article_downloader import download_articles_from_pubmed


class ComprehensiveEvaluationPipeline:
    """Pipeline for evaluating multiple LLM queries against manual review"""
    
    def __init__(self, manual_endnote_file: str, output_dir: str = "evaluation_results"):
        self.manual_endnote_file = manual_endnote_file
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Load manual data
        self.parser = EndNoteParser(manual_endnote_file)
        self.endnote_data = self.parser.parse_endnote_file()
        self.manual_articles = self.endnote_data.get('pubmed_articles', self.endnote_data.get('all_articles', []))
        
        self.visualizer = ValidationVisualizer(output_dir)
        
        print(f"✅ Loaded {len(self.manual_articles)} manual articles for evaluation")
    
    def evaluate_query_overlap(self, llm_query: str, query_name: str = None, 
                              max_articles: int = 100,
                              date_range: Tuple[int, int] = (2013, 2024)) -> Dict[str, Any]:
        """
        Evaluate overlap between EndNote articles and LLM query results
        
        Args:
            llm_query: The search query to test
            query_name: Name identifier for this query
            max_articles: Maximum articles to download
            date_range: Date range tuple (start_year, end_year)
        
        Returns:
            Dictionary with metrics and matched results
        """
        if query_name is None:
            query_name = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"\n{'='*80}")
        print(f"Evaluating Query: {query_name}")
        print(f"{'='*80}")
        print(f"Query: {llm_query[:200]}..." if len(llm_query) > 200 else f"Query: {llm_query}")
        print()
        
        # Step 1: Run LLM query to download articles
        print("📥 Downloading articles from PubMed...")
        try:
            llm_article_paths = download_articles_from_pubmed(
                llm_query, 
                max_articles=max_articles,
                date_start=str(date_range[0]),
                date_end=str(date_range[1])
            )
            print(f"   ✅ Downloaded {len(llm_article_paths)} articles")
        except Exception as e:
            print(f"   ❌ Error downloading articles: {e}")
            return {
                "query": llm_query,
                "query_name": query_name,
                "error": str(e),
                "metrics": None
            }
        
        # Step 2: Load downloaded articles
        print("📚 Loading downloaded articles...")
        llm_articles = []
        for path in llm_article_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    llm_articles.append(json.load(f))
            except Exception as e:
                print(f"   ⚠️  Warning: Could not load {path}: {e}")
        
        print(f"   ✅ Loaded {len(llm_articles)} articles")
        
        # Step 3: Calculate metrics
        print("📊 Calculating overlap metrics...")
        metrics = calculate_overlap_metrics(
            self.manual_articles, 
            llm_articles,
            date_range=date_range
        )
        
        # Step 4: Get detailed matching stats
        print("🔍 Analyzing matching details...")
        detailed_stats = calculate_detailed_matching_stats(
            self.manual_articles,
            llm_article_paths,
            date_range=date_range
        )
        
        # Step 5: Generate visualization
        print("🎨 Generating Venn diagram...")
        manual_pmids = set()
        for article in self.manual_articles:
            if date_range:
                pub_date = article.get('publication_date', '').strip()
                from enhanced_metrics import _extract_year
                year = _extract_year(pub_date)
                if year and not (date_range[0] <= year <= date_range[1]):
                    continue
            pmid = article.get('pmid', '').strip().lower()
            if pmid:
                manual_pmids.add(pmid)
        
        llm_pmids = set()
        for article in llm_articles:
            from enhanced_metrics import _extract_pmid_from_llm
            pmid = _extract_pmid_from_llm(article)
            if pmid:
                llm_pmids.add(pmid.lower().strip())
        
        venn_filename = f"{query_name}_overlap_venn.png"
        self.visualizer.create_venn_diagram(
            manual_pmids,
            llm_pmids,
            ('Manual EndNote', 'LLM Query'),
            f'Article Overlap: {query_name}',
            venn_filename
        )
        print(f"   ✅ Venn diagram saved: {venn_filename}")
        
        # Compile results
        results = {
            "query": llm_query,
            "query_name": query_name,
            "metrics": metrics,
            "detailed_stats": detailed_stats,
            "llm_articles_count": len(llm_articles),
            "manual_articles_count": len(self.manual_articles),
            "venn_diagram": venn_filename,
            "evaluation_timestamp": datetime.now().isoformat()
        }
        
        # Print summary
        print()
        print("📈 Results Summary:")
        print(f"   Precision: {metrics['precision']:.2%}")
        print(f"   Recall: {metrics['recall']:.2%}")
        print(f"   F1-Score: {metrics['f1_score']:.2%}")
        print(f"   Jaccard: {metrics['jaccard']:.2%}")
        print(f"   Overlap: {metrics['overlap_count']} articles")
        print(f"   Manual only: {metrics['manual_only_count']} articles")
        print(f"   LLM only: {metrics['llm_only_count']} articles")
        print()
        
        return results
    
    def run_comprehensive_evaluation(self, llm_queries: List[Dict[str, str]], 
                                    max_articles: int = 100,
                                    date_range: Tuple[int, int] = (2013, 2024)) -> Dict[str, Any]:
        """
        Run comprehensive evaluation of multiple LLM queries
        
        Args:
            llm_queries: List of dicts with 'name' and 'query' keys
            max_articles: Maximum articles per query
            date_range: Date range tuple
        
        Returns:
            Dictionary with results for all queries and best performing query
        """
        print(f"\n{'='*80}")
        print("COMPREHENSIVE QUERY EVALUATION")
        print(f"{'='*80}")
        print(f"Evaluating {len(llm_queries)} queries...")
        print()
        
        all_results = {}
        
        # Evaluate each query
        for i, query_info in enumerate(llm_queries):
            query_name = query_info.get('name', f"query_{i+1}")
            query = query_info.get('query', '')
            
            if not query:
                print(f"⚠️  Skipping {query_name}: No query provided")
                continue
            
            results = self.evaluate_query_overlap(
                query,
                query_name=query_name,
                max_articles=max_articles,
                date_range=date_range
            )
            
            all_results[query_name] = results
        
        # Find best performing query
        best_query = None
        best_f1 = -1
        
        for query_name, results in all_results.items():
            if results.get('metrics') and results['metrics'].get('f1_score', -1) > best_f1:
                best_f1 = results['metrics']['f1_score']
                best_query = query_name
        
        # Generate comparison visualization
        print("\n📊 Generating performance comparison...")
        self._create_performance_comparison(all_results)
        
        # Save comprehensive results
        output_file = os.path.join(self.output_dir, "comprehensive_evaluation_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "evaluation_timestamp": datetime.now().isoformat(),
                "date_range": date_range,
                "queries_evaluated": len(all_results),
                "results": all_results,
                "best_query": best_query,
                "best_f1_score": best_f1
            }, f, indent=2, default=str)
        
        print(f"✅ Comprehensive results saved to: {output_file}")
        
        return {
            "all_results": all_results,
            "best_query": best_query,
            "best_f1_score": best_f1,
            "output_file": output_file
        }
    
    def _create_performance_comparison(self, all_results: Dict[str, Dict]):
        """Create visualization comparing performance of all queries"""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
            
            query_names = []
            f1_scores = []
            precision_scores = []
            recall_scores = []
            jaccard_scores = []
            
            for query_name, results in all_results.items():
                if results.get('metrics'):
                    metrics = results['metrics']
                    query_names.append(query_name)
                    f1_scores.append(metrics.get('f1_score', 0))
                    precision_scores.append(metrics.get('precision', 0))
                    recall_scores.append(metrics.get('recall', 0))
                    jaccard_scores.append(metrics.get('jaccard', 0))
            
            if not query_names:
                print("   ⚠️  No valid results to compare")
                return
            
            # Create comparison chart
            fig, ax = plt.subplots(figsize=(12, 6))
            x = np.arange(len(query_names))
            width = 0.2
            
            ax.bar(x - 1.5*width, f1_scores, width, label='F1-Score', alpha=0.8)
            ax.bar(x - 0.5*width, precision_scores, width, label='Precision', alpha=0.8)
            ax.bar(x + 0.5*width, recall_scores, width, label='Recall', alpha=0.8)
            ax.bar(x + 1.5*width, jaccard_scores, width, label='Jaccard', alpha=0.8)
            
            ax.set_xlabel('Query')
            ax.set_ylabel('Score')
            ax.set_title('Performance Comparison of LLM Queries')
            ax.set_xticks(x)
            ax.set_xticklabels(query_names, rotation=45, ha='right')
            ax.legend()
            ax.set_ylim([0, 1])
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            comparison_file = os.path.join(self.output_dir, "query_comparison.png")
            plt.savefig(comparison_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"   ✅ Performance comparison saved: query_comparison.png")
        except Exception as e:
            print(f"   ⚠️  Could not create performance comparison: {e}")

