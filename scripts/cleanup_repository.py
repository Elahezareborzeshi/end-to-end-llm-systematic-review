#!/usr/bin/env python3
"""
Repository Cleanup Script
Removes unnecessary files before making the repository public.
This script is safe to run - it only removes files that are not needed for the Streamlit UI.
"""

import os
import shutil
from pathlib import Path

# Files and patterns to remove
FILES_TO_REMOVE = [
    # Analysis/utility scripts
    "analyze_missed_articles.py",
    "analyze_query_comparison.py",
    "analyze_search_queries.py",
    "check_current_capture_results.py",
    "compare_manual_vs_llm.py",
    "create_comprehensive_analysis_report.py",
    "create_enhanced_search_queries.py",
    "create_query_comparison_report.py",
    "debug_endnote.py",
    "fix_and_improve_query.py",
    "generate_comprehensive_comparison_report.py",
    "generate_publication_report.py",
    "improve_search_query.py",
    "regenerate_venn_diagram.py",
    "run_backend_full_text_screening.py",
    "run_backend_title_abstract_screening_all.py",
    "run_comprehensive_evaluation.py",
    "run_full_workflow.py",
    "run_workflow_with_existing_data.py",
    "test_imports.py",
    "verify_matching_results.py",
    "convert_markdown_to_docx.py",
    
    # Report/documentation files
    "BACKEND_FULL_TEXT_SCREENING_RESULTS_SUMMARY.md",
    "BACKEND_SCREENING_INSTRUCTIONS.md",
    "BACKEND_SCREENING_RESULTS_SUMMARY.md",
    "COMPREHENSIVE_ANALYSIS_SUMMARY.md",
    "COMPREHENSIVE_LLM_VS_MANUAL_METRICS.md",
    "CURRENT_CAPTURE_RESULTS_SUMMARY.md",
    "ENHANCED_EVALUATION_METHODS.md",
    "ENHANCED_QUERY_SUMMARY.md",
    "evaluation_report.md",
    "FINAL_VERIFICATION_REPORT.md",
    "FIXES_APPLIED.md",
    "MANUAL_QUERY_INTEGRATION_COMPLETE.md",
    "QUERY_ENHANCEMENT_IMPLEMENTATION.md",
    "SCREENING_RESULTS_COMPARISON.md",
    "SEARCH_QUERY_ENHANCEMENT_GUIDE.md",
    "SEARCH_QUERY_IMPROVEMENTS.md",
    "WORKFLOW_EXECUTION_SUMMARY.md",
]

# Directories to clean (remove contents but keep directory)
DIRECTORIES_TO_CLEAN = [
    "data/validation_plots",  # Keep directory, remove PNG files
]

# Patterns to match (for additional safety checks)
PATTERNS_TO_REMOVE = [
    "test_*.py",  # Test files in root
]

def remove_file(filepath):
    """Safely remove a file"""
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"✅ Removed: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error removing {filepath}: {e}")
            return False
    else:
        print(f"⚠️  File not found (already removed?): {filepath}")
        return False

def clean_directory(dirpath):
    """Clean a directory by removing all files but keeping the directory"""
    if os.path.exists(dirpath):
        try:
            for filename in os.listdir(dirpath):
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    print(f"✅ Removed: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error cleaning {dirpath}: {e}")
            return False
    else:
        print(f"⚠️  Directory not found: {dirpath}")
        return False

def main():
    """Main cleanup function"""
    print("="*80)
    print("REPOSITORY CLEANUP SCRIPT")
    print("="*80)
    print("\nThis script will remove unnecessary files to prepare for public release.")
    print("Files removed will NOT affect the Streamlit UI functionality.\n")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print(f"Project root: {project_root}\n")
    
    # Remove individual files
    print("="*80)
    print("REMOVING FILES")
    print("="*80)
    removed_count = 0
    for filename in FILES_TO_REMOVE:
        filepath = os.path.join(project_root, filename)
        if remove_file(filepath):
            removed_count += 1
    
    # Clean directories
    print("\n" + "="*80)
    print("CLEANING DIRECTORIES")
    print("="*80)
    for dirname in DIRECTORIES_TO_CLEAN:
        dirpath = os.path.join(project_root, dirname)
        clean_directory(dirpath)
    
    # Remove files matching patterns
    print("\n" + "="*80)
    print("REMOVING FILES MATCHING PATTERNS")
    print("="*80)
    import glob
    for pattern in PATTERNS_TO_REMOVE:
        matches = glob.glob(os.path.join(project_root, pattern))
        for match in matches:
            # Skip if it's in tests/ directory (we want to keep that structure)
            if "tests" not in match:
                if remove_file(match):
                    removed_count += 1
    
    # Summary
    print("\n" + "="*80)
    print("CLEANUP SUMMARY")
    print("="*80)
    print(f"✅ Removed {removed_count} files")
    print("\n⚠️  IMPORTANT: Review the changes before committing!")
    print("   - Check that .gitignore is properly configured")
    print("   - Verify Streamlit UI still works: streamlit run src/main.py")
    print("   - Test that all core functionality is intact")
    print("\n✅ Cleanup complete!")

if __name__ == "__main__":
    main()

