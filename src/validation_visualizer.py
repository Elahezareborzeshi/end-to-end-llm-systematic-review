"""
Validation Visualization Module

Creates static visualization plots for validation results:
- Venn diagrams showing overlap between manual and LLM reviews
- Bar charts for precision/recall/F1-score comparison
- Confusion matrices for screening decisions
- Quality score distributions
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
import os
from typing import Dict, List, Tuple, Any
import json

# Try to import optional dependencies
try:
    import matplotlib_venn as venn
    VENN_AVAILABLE = True
except ImportError:
    VENN_AVAILABLE = False
    print("⚠️ Warning: matplotlib_venn not available. Venn diagrams will use alternative method.")

try:
    import seaborn as sns
    sns.set_style("whitegrid")
except ImportError:
    print("⚠️ Warning: seaborn not available. Using basic matplotlib styling.")


class ValidationVisualizer:
    """Generate visualizations for validation results"""
    
    def __init__(self, output_dir: str = "data/validation_plots"):
        """
        Initialize visualizer
        
        Args:
            output_dir: Directory to save visualization files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        try:
            sns.set_style("whitegrid")
        except:
            pass  # Continue without seaborn styling
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 12
        
    def create_venn_diagram(self, set1: set, set2: set, labels: Tuple[str, str], 
                           title: str, subtitle_or_filename: str = None, recall: float = None, filename: str = None):
        """
        Create 2-set Venn diagram matching reference style
        
        Args:
            set1: First set
            set2: Second set
            labels: Tuple of labels for the sets
            title: Main plot title
            subtitle_or_filename: Subtitle with article counts OR filename (for backward compatibility)
            recall: Recall percentage for manual articles captured (optional)
            filename: Output filename (optional, if not provided, subtitle_or_filename is used as filename)
        """
        # Handle backward compatibility
        if filename is None:
            if subtitle_or_filename and subtitle_or_filename.endswith('.png'):
                filename = subtitle_or_filename
                subtitle = None
            else:
                subtitle = subtitle_or_filename
                filename = 'venn_diagram.png'
        else:
            subtitle = subtitle_or_filename
        
        # Create figure matching reference style
        fig = plt.figure(figsize=(12, 10), facecolor='white')
        ax = fig.add_axes([0.1, 0.25, 0.8, 0.60])  # [left, bottom, width, height] - more space for diagram
        
        # Color palette matching reference: light red, light teal, high contrast for overlap
        color_set1 = '#E57373'  # Light red
        color_set2 = '#4DB6AC'  # Light teal
        color_overlap = '#1565C0'  # Dark blue for high contrast overlap
        alpha_main = 0.6
        alpha_overlap = 0.9  # More opaque for better visibility
        
        # Calculate values
        only_set1 = len(set1 - set2)
        only_set2 = len(set2 - set1)
        both = len(set1 & set2)
        total = len(set1 | set2)
        
        if VENN_AVAILABLE:
            # Create equal-sized circles by using subset_areas
            # Calculate the maximum total size to make circles equal
            max_total = max(len(set1), len(set2))
            
            # Create equal-sized circles by setting subset_areas
            # Format: (only_set1, only_set2, both)
            # To make circles equal, we need: (max_total - both, max_total - both, both)
            subset_areas = (max_total - both, max_total - both, both)
            
            venn_diagram = venn.venn2(subsets=subset_areas, set_labels=labels, ax=ax,
                                     set_colors=(color_set1, color_set2), alpha=alpha_main)
            
            # Style the overlap area
            try:
                overlap_patch = venn_diagram.get_patch_by_id('11')
                if overlap_patch:
                    overlap_patch.set_color(color_overlap)
                    overlap_patch.set_alpha(alpha_overlap)
                    overlap_patch.set_edgecolor('#0D47A1')  # Dark blue edge for high contrast
                    overlap_patch.set_linewidth(2.5)
                
                # Update labels to show actual counts (not the normalized areas)
                label_10 = venn_diagram.get_label_by_id('10')
                if label_10:
                    label_10.set_text(f'{only_set1:,}')
                    label_10.set_fontsize(12)
                    label_10.set_fontweight('normal')
                
                label_01 = venn_diagram.get_label_by_id('01')
                if label_01:
                    label_01.set_text(f'{only_set2:,}')
                    label_01.set_fontsize(12)
                    label_01.set_fontweight('normal')
                
                label_11 = venn_diagram.get_label_by_id('11')
                if label_11:
                    label_11.set_text(f'{both:,}')
                    label_11.set_fontsize(13)
                    label_11.set_fontweight('bold')
                    label_11.set_color('#FFFFFF')
                
                # Style set labels
                for text in ax.texts:
                    if text.get_text() in labels:
                        text.set_fontsize(13)
                        text.set_fontweight('bold')
            except:
                pass
        else:
            ax.axis('off')
            ax.text(0.5, 0.5, 'Venn diagram requires matplotlib_venn', 
                   ha='center', va='center', transform=ax.transAxes)
        
        ax.axis('off')
        
        # Title at top with more space
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.97, color='#212121')
        
        # Subtitle above diagram with more space from title
        if subtitle:
            fig.text(0.5, 0.91, subtitle, ha='center', fontsize=11, 
                   style='italic', color='#616161')
        
        # Statistics text box below diagram
        stats_text = f"{labels[0]} only (articles unique to {labels[0]}): {only_set1:,} ({only_set1/total*100:.1f}%)\n"
        stats_text += f"{labels[1]} only (articles unique to {labels[1]}): {only_set2:,} ({only_set2/total*100:.1f}%)\n"
        stats_text += f"Overlap (articles found by both methods): {both:,} ({both/total*100:.1f}%)\n"
        stats_text += f"Total unique articles considered: {total:,}"
        
        if recall is not None:
            stats_text += f"\n\nLLM captured {recall:.1f}% of manually reviewed articles (recall)."
        
        fig.text(0.02, 0.10, stats_text, fontsize=11, 
                verticalalignment='bottom', family='sans-serif',
                bbox=dict(boxstyle='round,pad=0.8', facecolor='#FAFAFA', 
                         alpha=0.9, edgecolor='#BDBDBD', linewidth=1))
        
        plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"📊 Venn diagram saved: {filename}")
    
    def create_metrics_bar_chart(self, metrics: Dict[str, Dict[str, float]], 
                                title: str, filename: str):
        """
        Create bar chart comparing metrics (precision, recall, F1)
        
        Args:
            metrics: Dictionary mapping metric names to values
            title: Chart title
            filename: Output filename
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Prepare data
        metric_names = list(metrics.keys())
        values = [metrics[name] for name in metric_names]
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        
        bars = ax.bar(metric_names, values, color=colors[:len(metric_names)])
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        ax.set_ylim([0, 1.1])
        ax.set_ylabel('Score', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Bar chart saved: {filename}")
    
    def create_confusion_matrix(self, tp: int, tn: int, fp: int, fn: int,
                               title: str, filename: str):
        """
        Create confusion matrix heatmap
        
        Args:
            tp, tn, fp, fn: Confusion matrix values
            title: Chart title
            filename: Output filename
        """
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Create matrix
        matrix = np.array([[tp, fp], [fn, tn]])
        
        # Create heatmap
        try:
            import seaborn as sns
            sns.heatmap(matrix, annot=True, fmt='d', cmap='Blues', 
                       xticklabels=['Predicted: Include', 'Predicted: Exclude'],
                       yticklabels=['Actual: Include', 'Actual: Exclude'],
                       cbar_kws={'label': 'Count'}, ax=ax)
        except ImportError:
            # Fallback to matplotlib imshow
            im = ax.imshow(matrix, cmap='Blues', aspect='auto')
            ax.set_xticks([0, 1])
            ax.set_yticks([0, 1])
            ax.set_xticklabels(['Predicted: Include', 'Predicted: Exclude'])
            ax.set_yticklabels(['Actual: Include', 'Actual: Exclude'])
            # Add text annotations
            for i in range(2):
                for j in range(2):
                    ax.text(j, i, str(matrix[i, j]), ha='center', va='center', 
                           color='white' if matrix[i, j] > matrix.max()/2 else 'black', fontweight='bold')
            plt.colorbar(im, ax=ax, label='Count')
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Confusion matrix saved: {filename}")
    
    def create_performance_comparison(self, stage_metrics: Dict[str, Dict[str, float]],
                                     title: str, filename: str):
        """
        Create comparison chart across multiple stages
        
        Args:
            stage_metrics: Dict mapping stage names to metric dicts
            title: Chart title
            filename: Output filename
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        stages = list(stage_metrics.keys())
        
        for idx, metric in enumerate(['precision', 'recall', 'f1_score']):
            values = [stage_metrics[stage].get(metric, 0) for stage in stages]
            
            bars = axes[idx].bar(stages, values, color='#45B7D1')
            
            # Add value labels
            for bar, value in zip(bars, values):
                height = bar.get_height()
                axes[idx].text(bar.get_x() + bar.get_width()/2., height,
                              f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
            
            axes[idx].set_ylim([0, 1.1])
            axes[idx].set_ylabel('Score', fontsize=10)
            axes[idx].set_title(metric.upper().replace('_', ' '), fontsize=11, fontweight='bold')
            axes[idx].grid(axis='y', alpha=0.3)
            axes[idx].tick_params(axis='x', rotation=15)
        
        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Performance comparison saved: {filename}")
    
    def create_quality_score_distribution(self, scores: List[float], title: str, filename: str):
        """
        Create histogram of quality scores
        
        Args:
            scores: List of quality scores
            title: Chart title
            filename: Output filename
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create histogram
        ax.hist(scores, bins=20, color='#4ECDC4', edgecolor='black', alpha=0.7)
        
        # Add statistics
        mean_score = np.mean(scores)
        median_score = np.median(scores)
        
        ax.axvline(mean_score, color='red', linestyle='--', linewidth=2, 
                   label=f'Mean: {mean_score:.1f}')
        ax.axvline(median_score, color='blue', linestyle='--', linewidth=2, 
                   label=f'Median: {median_score:.1f}')
        
        ax.set_xlabel('Quality Score', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Quality score distribution saved: {filename}")
    
    def create_comprehensive_report_visuals(self, validation_results: Dict, filename: str):
        """
        Create all visualizations for comprehensive validation report
        
        Args:
            validation_results: Complete validation results dictionary
            filename: Base filename for output
        """
        # Create PDF with multiple pages
        pdf_path = os.path.join(self.output_dir, f"{filename}_plots.pdf")
        
        with PdfPages(pdf_path) as pdf:
            # Title/Abstract Venn Diagram
            if 'title_abstract' in validation_results:
                ta_data = validation_results['title_abstract']
                manual_set = set(ta_data.get('manual_articles', []))
                llm_set = set(ta_data.get('llm_articles', []))
                
                self.create_venn_diagram(
                    manual_set, llm_set,
                    ('Manual Review', 'LLM Framework'),
                    'Title/Abstract Screening: Manual vs LLM',
                    f"{filename}_title_abstract_venn.png"
                )
            
            # Full-Text Venn Diagram
            if 'full_text' in validation_results:
                ft_data = validation_results['full_text']
                manual_set = set(ft_data.get('manual_articles', []))
                llm_set = set(ft_data.get('llm_articles', []))
                
                self.create_venn_diagram(
                    manual_set, llm_set,
                    ('Manual Review', 'LLM Framework'),
                    'Full-Text Screening: Manual vs LLM',
                    f"{filename}_full_text_venn.png"
                )
            
            # Confusion Matrices
            if 'title_abstract' in validation_results:
                ta_data = validation_results['title_abstract']
                self.create_confusion_matrix(
                    ta_data.get('tp', 0),
                    ta_data.get('tn', 0),
                    ta_data.get('fp', 0),
                    ta_data.get('fn', 0),
                    'Title/Abstract Screening Confusion Matrix',
                    f"{filename}_confusion_ta.png"
                )
            
            # Metrics Comparison
            if 'stage_metrics' in validation_results:
                self.create_performance_comparison(
                    validation_results['stage_metrics'],
                    'Performance Metrics Across Stages',
                    f"{filename}_performance_comparison.png"
                )
        
        print(f"📊 Comprehensive report PDF saved: {pdf_path}")
    
    def save_validation_summary_json(self, validation_results: Dict, filename: str):
        """Save validation results as JSON"""
        output_path = os.path.join(self.output_dir, f"{filename}_summary.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2, default=str)
        
        print(f"💾 Validation summary saved: {output_path}")


