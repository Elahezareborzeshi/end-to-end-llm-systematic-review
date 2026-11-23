def evaluate_keywords_and_generate_report(llm_keywords, save_path="evaluation_report.md"):
    """
    Evaluates LLM-extracted keywords against manual review keywords
    and generates a comprehensive report
    """
    try:
        try:
            from .search_strategy_comparator import SearchStrategyComparator
        except ImportError:
            from search_strategy_comparator import SearchStrategyComparator
        
        comparator = SearchStrategyComparator()
        
        # Get comparison data
        keyword_comparison = comparator.compare_keywords(llm_keywords)
        
        # Generate markdown report
        report_content = f"""
# LLM-Augmented vs. Manual Systematic Review Comparison

## Keyword Extraction Performance

| Metric | Value |
| ------ | ----- |
| Precision | {keyword_comparison['precision']:.2f} |
| Recall | {keyword_comparison['recall']:.2f} |
| F1 Score | {keyword_comparison['f1_score']:.2f} |

## Keyword Analysis

### Correctly Identified Keywords ({len(keyword_comparison['matched_keywords'])})
{chr(10).join(f"- {kw}" for kw in keyword_comparison['matched_keywords'])}

### Missed Keywords ({len(keyword_comparison['missed_keywords'])})
{chr(10).join(f"- {kw}" for kw in keyword_comparison['missed_keywords'])}

### Extra Keywords ({len(keyword_comparison['extra_keywords'])})
{chr(10).join(f"- {kw}" for kw in keyword_comparison['extra_keywords'])}

## Qualitative Assessment

The LLM-augmented approach showed {keyword_comparison['precision']:.2f} precision and {keyword_comparison['recall']:.2f} recall compared to manual review.
This suggests the LLM-based approach {'performed well' if keyword_comparison['f1_score'] > 0.7 else 'needs improvement'} in capturing medical terminology.

## Recommendations

- **Precision**: {'Good' if keyword_comparison['precision'] > 0.7 else 'Needs improvement'} - {'Low false positive rate' if keyword_comparison['precision'] > 0.7 else 'Too many irrelevant keywords'}
- **Recall**: {'Good' if keyword_comparison['recall'] > 0.7 else 'Needs improvement'} - {'Captured most relevant terms' if keyword_comparison['recall'] > 0.7 else 'Missed important keywords'}
- **Overall**: {'Framework is effective' if keyword_comparison['f1_score'] > 0.7 else 'Framework needs refinement'}
"""
        
        # Save report
        with open(save_path, "w") as f:
            f.write(report_content)
        
        print(f"📊 Evaluation report saved to {save_path}")
        
    except Exception as e:
        print(f"Error generating evaluation report: {e}")