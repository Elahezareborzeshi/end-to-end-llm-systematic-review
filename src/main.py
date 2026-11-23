import streamlit as st

import textwrap
import time
import pandas as pd
import json
import os
import sys
import traceback
import re
from pathlib import Path

# Add src, src/core, and src/utils directories to path for imports
if __name__ != '__main__' or True:  # Always add path for Streamlit
    current_dir = os.path.dirname(os.path.abspath(__file__))
    core_dir = os.path.join(current_dir, 'core')
    utils_dir = os.path.join(current_dir, 'utils')
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    if utils_dir not in sys.path:
        sys.path.insert(0, utils_dir)

from streamlit_extras.tags import tagger_component
from core.keyword_extractor import extract_keywords
from streamlit_tags import st_tags
from core.mesh_term_finder import get_mesh_terms, are_mesh_terms_relevant
from core.search_query_builder import build_search_query_for_terms
from article_downloader import download_articles_from_pubmed
from core.article_deduplicator import deduplicate_articles
from core.rag_screening import add_rag_example, rag_based_summary_screening, set_base_screening_info, rag_based_full_text_screening
from core.article_data_extractor import load_article_from_file, extract_single_article_data
from core.article_full_text_downloader import download_articles_full_text, download_single_article_full_text
from core.article_full_text_screening import download_all_full_texts, display_full_text_article_dataframe, display_current_full_text_article, display_full_text_screening_stats, handle_full_text_user_decision, generate_full_text_summary
from core.search_query_validator import validate_boolean_search_query, display_validation_results, format_search_query, get_example_queries, fix_common_query_issues

# Import query enhancer for manual query integration
try:
    from query_enhancer import load_manual_query_components, enhance_grouped_terms_with_manual, enhance_query_with_manual_terms
except ImportError:
    # Fallback if import fails
    load_manual_query_components = None
    enhance_grouped_terms_with_manual = None
    enhance_query_with_manual_terms = None

# Initialize session state variables
if 'research_question' not in st.session_state:
    st.session_state.research_question = ''
if 'final_result_instructions' not in st.session_state:
    st.session_state.final_result_instructions = ''
if 'found_keywords' not in st.session_state:
    st.session_state.found_keywords = []
if 'grouped_terms' not in st.session_state:
    st.session_state.grouped_terms = {}
if 'keywords' not in st.session_state:
    st.session_state.keywords = []
if 'main_keyword_selections' not in st.session_state:
    st.session_state.main_keyword_selections = {}
if 'mesh_terms_selection' not in st.session_state:
    st.session_state.mesh_terms_selection = {}
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'search_query' not in st.session_state:
    st.session_state.search_query = ''
if 'downloaded_articles' not in st.session_state:
    st.session_state.downloaded_articles = []
if 'removed_articles_count' not in st.session_state:
    st.session_state.removed_articles_count = -1
if 'summary_screening_current_article_index' not in st.session_state:
    st.session_state.summary_screening_current_article_index = 0
if 'summary_screening_results' not in st.session_state:
    st.session_state.summary_screening_results = {}
if 'screening_mode' not in st.session_state:
    st.session_state.screening_mode = 'manual'
if 'summary_screening_done_articles' not in st.session_state:
    st.session_state.summary_screening_done_articles = 0
if 'summary_screening_correct_predictions' not in st.session_state:
    st.session_state.summary_screening_correct_predictions = 0
if 'rag_examples' not in st.session_state:
    st.session_state.rag_examples = []
if 'data_extraction_done' not in st.session_state:
    st.session_state.data_extraction_done = False
if 'full_article_screening_results' not in st.session_state:
    st.session_state.full_article_screening_results = {}
if 'research_suggestions' not in st.session_state:
    st.session_state.research_suggestions = []
if 'extraction_suggestions' not in st.session_state:
    st.session_state.extraction_suggestions = []
if 'show_research_suggestions' not in st.session_state:
    st.session_state.show_research_suggestions = False
if 'show_extraction_suggestions' not in st.session_state:
    st.session_state.show_extraction_suggestions = False
if 'show_criteria_suggestions' not in st.session_state:
    st.session_state.show_criteria_suggestions = False
if 'suggestion_history' not in st.session_state:
    st.session_state.suggestion_history = []
if 'current_suggestion_index' not in st.session_state:
    st.session_state.current_suggestion_index = 0
if 'user_feedback' not in st.session_state:
    st.session_state.user_feedback = []
if 'generating_suggestion' not in st.session_state:
    st.session_state.generating_suggestion = False
if 'inclusion_criteria' not in st.session_state:
    st.session_state.inclusion_criteria = ''
if 'exclusion_criteria' not in st.session_state:
    st.session_state.exclusion_criteria = ''
    # Add these new session state variables after your existing ones
if 'full_text_screening_current_article_index' not in st.session_state:
    st.session_state.full_text_screening_current_article_index = 0
if 'full_text_screening_results' not in st.session_state:
    st.session_state.full_text_screening_results = {}
if 'full_text_screening_done_articles' not in st.session_state:
    st.session_state.full_text_screening_done_articles = 0
if 'full_text_screening_correct_predictions' not in st.session_state:
    st.session_state.full_text_screening_correct_predictions = 0
if 'full_texts_downloaded' not in st.session_state:
    st.session_state.full_texts_downloaded = False
if 'search_query_validation_result' not in st.session_state:
    st.session_state.search_query_validation_result = None
if 'show_query_examples' not in st.session_state:
    st.session_state.show_query_examples = False
    
def safe_function_call(func, func_name):
    """Safely call a function with error handling"""
    try:
        func()
    except Exception as e:
        st.error(f"Error in {func_name}: {str(e)}")
        st.session_state.processing = False
        
def main():
    # CSS styling for better button appearance + SMALLER BOXES ONLY
    st.markdown("""
    <style>
    /* Force all button content to stay on one line */
    .stButton > button {
        white-space: nowrap !important;
        min-width: 150px !important;
        height: auto !important;
        padding: 0.25rem 0.75rem !important;
    }
    
    .stButton > button p {
        white-space: nowrap !important;
        margin: 0 !important;
        line-height: 1.2 !important;
    }
    
    .stButton > button div {
        white-space: nowrap !important;
        display: inline !important;
    }
    
    /* Target the specific button content more aggressively */
    .stButton > button > div {
        white-space: nowrap !important;
    }
    
    .stButton > button > div > div {
        white-space: nowrap !important;
    }
    
    .stButton > button * {
        white-space: nowrap !important;
        word-break: keep-all !important;
    }
    
    /* Alternative approach - if the above doesn't work */
    [data-testid="stButton"] button {
        white-space: nowrap !important;
        min-width: 150px !important;
    }
    
    [data-testid="stButton"] button * {
        white-space: nowrap !important;
    }
    
    /* Column spacing */
    .row-widget.stColumns > div {
        padding-right: 0.5rem;
    }
    
    /* ONLY ADD: Tab suggestion styling */
    .tab-suggestion {
        background: #f0f9ff;
        border: 1px solid #0ea5e9;
        border-radius: 4px;
        padding: 4px 8px;
        margin: 2px 0;
        font-size: 0.85rem;
        color: #0369a1;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Default values
    default_research_question = textwrap.dedent(
        """Identify metabolome and metabolomic profiles, as well as biochemical pathways, associated with hypertension response to different classes of antihypertensive drugs using pharmacometabolomics approaches. Specifically, identify key metabolic biomarkers and signatures predictive of treatment response across diuretics, Adrenergic beta-Antagonists, ACE inhibitors, angiotensin receptor blockers (ARBs), vasodilator agents, and calcium channel blockers. Characterize the underlying metabolomic alterations and biochemical pathways to elucidate mechanisms of drug efficacy and variability, and assess the potential for metabolome-informed, personalized antihypertensive therapy."""
    )
    
    default_final_result_instructions = textwrap.dedent("""
        - "First Author"
        - "Publication Date"
        - "Study Design"
        - "Sample Size"
        - "Patient Type/Inclusion Criteria"
        - "Antihypertensive Drug Class (e.g., diuretics, beta-blockers, ACE inhibitors/ARBs)"
        - "Metabolomics Measurement Method (e.g., LC-MS/MS, NMR, GC-MS)"
        - "Targeted or Untargeted Metabolomics"
        - "Identified Metabolites (name, concentration, and unit)"
        - "BP Assessment Method (e.g., systolic/diastolic blood pressure, mean arterial pressure)"
        - "Association with BP Response (positive or negative)"
        - "Statistical Significance (p-value)"
        - "Biochemical Pathway (e.g., pathway name, pathway description)"
        - "Quality Assessment Score"
    """)
    
    st.title('LLM Systematic Review Assistant')
    
    # Disable widgets when processing
    disabled = st.session_state.processing
    
    # 1) Research Question Section - ADD TAB SUGGESTION
    research_question = create_enhanced_research_section_with_tab(
        label="🧠 1) Research Question",
        value=st.session_state.research_question or default_research_question,
        height=200,
        disabled=disabled,
        default_research_question=default_research_question
    )
    
    # Update session state
    set_base_screening_info(research_question)
    st.session_state.research_question = research_question
    
    # Selection Criteria Section (Expandable) - ADD TAB SUGGESTIONS + SMALLER BOXES
    with st.expander("🎯 Selection Criteria", expanded=False):
        # Add default criteria if not set
        if 'inclusion_criteria' not in st.session_state or st.session_state.inclusion_criteria == '':
            st.session_state.inclusion_criteria = textwrap.dedent("""
                - Studies assessing metabolomics-based biomarkers of BP response to antihypertensive medications
                - Human subjects diagnosed with hypertension
                - Clear association between metabolites and BP changes reported
                - Specific metabolite identification provided
                - Studies using validated metabolomics platforms (GC-TOF/MS, LC-MS, UHPLC-MS, etc.)
                - Published in peer-reviewed journals (English language)
                - Published from January 2013 onwards
            """).strip()

        if 'exclusion_criteria' not in st.session_state or st.session_state.exclusion_criteria == '':
            st.session_state.exclusion_criteria = textwrap.dedent("""
                - Animal studies or in vitro studies
                - Studies without clear metabolite-BP association
                - Lack of specific metabolite identification
                - Inadequate quality annotation
                - Severe or secondary hypertension focus only
                - Conference abstracts without full text
                - Case reports or studies with insufficient data
            """).strip()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📥 Inclusion Criteria**")
            current_inclusion = st.text_area(
                "",
                value=st.session_state.get('inclusion_criteria', ''),
                height=100,  # SMALLER HEIGHT
                disabled=disabled,
                key="inclusion_criteria_input",
                placeholder="Adults ≥18 years, confirmed diagnosis..."
            )
            
            # ADD: Tab suggestion for inclusion criteria
            show_tab_suggestion("inclusion_criteria", current_inclusion, research_question)
            
            # KEEP: Original auto-suggestion interface
            updated_inclusion = create_continuous_suggestion_interface_no_expander(
                "inclusion_criteria", 
                current_inclusion, 
                context=research_question
            )
            
            if updated_inclusion != current_inclusion:
                st.session_state.inclusion_criteria = updated_inclusion
            else:
                st.session_state.inclusion_criteria = current_inclusion
        
        with col2:
            st.markdown("**📤 Exclusion Criteria**")
            current_exclusion = st.text_area(
                "",
                value=st.session_state.get('exclusion_criteria', ''),
                height=100,  # SMALLER HEIGHT
                disabled=disabled,
                key="exclusion_criteria_input",
                placeholder="Pediatric populations, animal studies..."
            )
            
            # ADD: Tab suggestion for exclusion criteria
            show_tab_suggestion("exclusion_criteria", current_exclusion, research_question)
            
            # KEEP: Original auto-suggestion interface
            updated_exclusion = create_continuous_suggestion_interface_no_expander(
                "exclusion_criteria", 
                current_exclusion, 
                context=research_question
            )
            
            if updated_exclusion != current_exclusion:
                st.session_state.exclusion_criteria = updated_exclusion
            else:
                st.session_state.exclusion_criteria = current_exclusion
    
    st.markdown("---")
    
    # Data Extraction Instructions Section - ADD TAB SUGGESTION + SMALLER BOX
    result_instructions = create_enhanced_extraction_section_with_tab(
        label="📋 Data Extraction Instructions",
        value=st.session_state.final_result_instructions or default_final_result_instructions,
        height=180,  # SMALLER HEIGHT
        disabled=disabled,
        research_question=research_question,
        default_instructions=default_final_result_instructions
    )
    
    # Update session state
    st.session_state.final_result_instructions = result_instructions
    
    # Extract keywords button
    st.button("🔍 Extract keywords...", on_click=run_extract_keywords, disabled=disabled)
    
    # Show spinner if processing
    if st.session_state.processing:
        with st.spinner('Processing...'):
            pass
    
    # Display results if available
    if st.session_state.found_keywords:
        st.subheader("🕵🏻‍♀️ 2) Main keywords")
        keywords = st_tags(
            label=' ',
            text='These are the keywords extracted from your research question (update as you please):',
            value=st.session_state.found_keywords,
            suggestions=st.session_state.found_keywords,
            maxtags=100,
            key='main_keywords'
        )
        deduplicated_keywords = []
        for keyword in keywords:
            if keyword not in deduplicated_keywords:
                deduplicated_keywords.append(keyword)
        st.session_state.keywords = deduplicated_keywords
        st.button("🔍 Find MeSH terms...", on_click=run_find_mesh_terms, disabled=disabled)
    
    if st.session_state.grouped_terms:
        render_mesh_terms(st.session_state.grouped_terms)
        st.button("🧳 Generate search strategy...", on_click=run_generate_search_strategy, disabled=disabled)
    
    if st.session_state.search_query:
        st.subheader("🔍 4) Search Query")
        
        # Query input and tools
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Use a unique key and ensure value updates correctly
            search_query_text = st.text_area(
                "",
                value=st.session_state.search_query,
                height=200,
                disabled=st.session_state.processing,
                help="Edit your Boolean search query using AND, OR, NOT operators",
                key="search_query_textarea"
            )
        
        with col2:
            st.markdown("**Query Tools**")
            
            # Validate button
            if st.button("🔍 Validate", use_container_width=True, help="Check query for errors"):
                st.session_state.search_query_validation_result = validate_boolean_search_query(search_query_text)
            
            # Simplify button - NEW!
            if st.button("✨ Simplify", use_container_width=True, help="Make query simpler"):
                st.session_state.search_query = simplify_search_query(search_query_text)
                st.session_state.search_query_validation_result = validate_boolean_search_query(st.session_state.search_query)
                st.rerun()
            
            # Format button
            if st.button("🔧 Format", use_container_width=True, help="Format for readability"):
                st.session_state.search_query = format_search_query(search_query_text)
                st.rerun()
            
            # Auto-fix button - FIXED!
            if st.button("🩹 Auto-Fix", use_container_width=True, help="Fix common issues"):
                # Fix the query
                fixed_query = fix_common_query_issues(search_query_text)
                st.session_state.search_query = fixed_query
                # Re-validate after fixing
                st.session_state.search_query_validation_result = validate_boolean_search_query(fixed_query)
                st.rerun()
        
        # Update session state with manual edits immediately
        if search_query_text != st.session_state.search_query:
            st.session_state.search_query = search_query_text
        
        # Display validation results if available
        if st.session_state.search_query_validation_result:
            with st.expander("🎯 Query Validation Results", expanded=True):
                display_validation_results(st.session_state.search_query_validation_result)
        
        # Show examples if requested
        # if st.session_state.show_query_examples:
        #     with st.expander("📚 Example Boolean Queries", expanded=True):
        #         examples = get_example_queries()
        #         for example in examples:
        #             st.markdown(f"**{example['name']}**")
        #             st.markdown(f"*{example['description']}*")
        #             st.code(example['query'], language="text")
        #             if st.button(f"Use this example", key=f"use_example_{example['name']}", use_container_width=True):
        #                 st.session_state.search_query = example['query']
        #                 st.session_state.show_query_examples = False
        #                 st.rerun()
        #             st.markdown("---")
        
        # Download button - disabled if query has validation errors
        validation_ok = (st.session_state.search_query_validation_result is None or 
                        st.session_state.search_query_validation_result.get('is_valid', True))
        
        download_disabled = disabled or not validation_ok
        
        if not validation_ok:
            st.warning("⚠️ Please fix query validation errors before downloading articles")
        
        # IMPORTANT: Pass the current search_query_text to the download function
        # This ensures the latest textarea content is used
        st.button("🏃🏻‍♀️‍➡️ Download articles...", 
                 on_click=lambda: run_download_articles_with_query(search_query_text), 
                 disabled=download_disabled,
                 help="Downloads articles from PubMed using your search query" if validation_ok else "Fix validation errors first")
    
    if st.session_state.downloaded_articles:
        st.subheader("📚 5) Downloaded articles")
        
        articles_data = []
        failed_articles = []
        for article_path in st.session_state.downloaded_articles:
            article_info = load_article_from_file(article_path)
            if article_info is None:
                st.error(f"Failed to load article from {article_path}")
            else:
                articles_data.append(article_info)
        
        df = pd.DataFrame(articles_data)
        
        # Fix PyArrow conversion error by ensuring consistent data types
        if not df.empty:
            if 'Abstract' in df.columns:
                df['Abstract'] = df['Abstract'].astype(str)
                df['Abstract'] = df['Abstract'].fillna('No abstract available')
            
            # Clean other columns that might cause similar issues
            for col in ['Title', 'Authors', 'Journal', 'Publication Date', 'E-Location']:
                if col in df.columns:
                    df[col] = df[col].astype(str).fillna('N/A')
        
        st.dataframe(df)
        st.button("🪄 De-duplicate articles...", on_click=run_de_duplicate_articles, disabled=disabled)
    
    if st.session_state.removed_articles_count > -1:
        st.subheader("🧹 De-duplicated articles")
        st.write(f"Removed {st.session_state.removed_articles_count} articles")
    
    if st.session_state.removed_articles_count > -1:
        st.subheader("🗂️ 6) Article Title/Abstract Screening")
        
        # Display dataframe with highlight
        display_article_dataframe()
        
        # Article info display
        col1, col2 = st.columns([2, 1])
        with col1:
            display_current_article()
        with col2:
            display_screening_stats()
        
        if st.session_state.screening_mode == 'manual':
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                st.button("⬅️ Exclude", on_click=handle_user_decision, args=("EXCLUDE",), key="exclude_btn")
            with col2:
                st.button("Include ➡️", on_click=handle_user_decision, args=("INCLUDE",), key="include_btn")
            with col3:
                st.button("🦄 Enable auto-screening", on_click=toggle_auto_screening, key="auto_screen_btn")
        else:
            st.button("🦄 Turn off auto-screening", on_click=toggle_auto_screening, key="auto_screen_btn")
            
            # Check if there are more articles to screen
            if st.session_state.summary_screening_current_article_index < len(st.session_state.downloaded_articles):
                # Automatically call rag_based_summary_screening for the current article after a few seconds
                summary_auto_screening_placeholder = st.empty()
                with summary_auto_screening_placeholder.container():
                    st.write("Auto-screening in progress...")
                    time.sleep(3)  # Wait for 3 seconds
                    decision, reason = rag_based_summary_screening(st.session_state.downloaded_articles[st.session_state.summary_screening_current_article_index])
                    st.session_state.summary_screening_results[st.session_state.summary_screening_current_article_index] = {
                        'decision': decision,
                        'reason': reason,
                        'automated_flag': True
                    }
                    st.write(f"Auto-screening complete. Decision: {decision}")
                    st.write(f"Reason: {reason}")
                    time.sleep(2)  # Display result for 2 seconds
                summary_auto_screening_placeholder.empty()
                
                # Move to the next article
                st.session_state.summary_screening_current_article_index += 1
                st.session_state.summary_screening_done_articles += 1
                if decision == st.session_state.summary_screening_results.get(st.session_state.summary_screening_current_article_index - 1, {}).get('decision'):
                    st.session_state.summary_screening_correct_predictions += 1
                
                # Rerun the app to update the display
                st.rerun()
            else:
                st.write("✅ All articles have been screened!")   
    # Check if title/abstract screening is complete
    if len(st.session_state.downloaded_articles) > 0 and st.session_state.summary_screening_current_article_index >= len(st.session_state.downloaded_articles):
        
        # Debug info (can be removed in production)
        st.write(f"✅ **Status:** Title/abstract screening complete! {len(st.session_state.downloaded_articles)} articles processed.")
        st.write(f"📁 **Full texts downloaded:** {'Yes' if st.session_state.full_texts_downloaded else 'No'}")
        
        # Step 7: Download Full Texts
        if not st.session_state.full_texts_downloaded:
            st.subheader("📥 7) Download Full Texts")
            
            # Get count of included articles
            included_count = sum(1 for result in st.session_state.summary_screening_results.values() if result['decision'] == 'INCLUDE')
            st.write(f"Articles to download full texts: {included_count}")
            
            if included_count > 0:
                st.button("📄 Download all full texts...", on_click=download_all_full_texts, disabled=disabled)
                # Debug button for testing
                if st.button("🔧 Debug: Skip to Full Text Screening", help="For testing - skip full text download"):
                    st.session_state.full_texts_downloaded = True
                    st.rerun()
            else:
                st.warning("No articles passed title/abstract screening.")
        
        # Step 8: Full Text Screening (Interactive) - Only show if full texts are downloaded
        if st.session_state.full_texts_downloaded:
            # Define included_articles
            included_articles = [
                article for article, result in st.session_state.summary_screening_results.items()
                if result['decision'] == 'INCLUDE'
            ]
            
            st.subheader("📜 8) Full Text Screening")
            # st.write(f"📊 **Screening Progress:** {len(included_articles)} articles included from title/abstract screening")
            # st.write(f"🎯 **Current article:** {st.session_state.full_text_screening_current_article_index + 1} of {len(included_articles)}")

            if st.session_state.full_text_screening_current_article_index < len(included_articles):
                st.write(f"🎯 **Current article:** {st.session_state.full_text_screening_current_article_index + 1} of {len(included_articles)}")
            else:
                st.write(f"🎯 **All articles screened:** {len(included_articles)} of {len(included_articles)}")
            # Display dataframe with highlight
            display_full_text_article_dataframe()
            
            # Check if there are more articles to screen
            if st.session_state.full_text_screening_current_article_index < len(included_articles):
                # Article info display
                col1, col2 = st.columns([2, 1])
                with col1:
                    display_current_full_text_article()
                with col2:
                    display_full_text_screening_stats()
                
                if st.session_state.screening_mode == 'manual':
                    # Action buttons (same style as title/abstract screening)
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        st.button("⬅️ Exclude", on_click=handle_full_text_user_decision, args=("EXCLUDE",), key="full_text_exclude_btn")
                    with col2:
                        st.button("Include ➡️", on_click=handle_full_text_user_decision, args=("INCLUDE",), key="full_text_include_btn")
                    with col3:
                        st.button("🦄 Enable auto-screening", on_click=toggle_auto_screening, key="full_text_auto_screen_btn")
                else:
                    st.button("🦄 Turn off auto-screening", on_click=toggle_auto_screening, key="full_text_auto_screen_off_btn")
                    
                    # Auto-screening logic (similar to title/abstract)
                    full_text_auto_screening_placeholder = st.empty()
                    with full_text_auto_screening_placeholder.container():
                        st.write("Auto-screening in progress...")
                        time.sleep(3)  # Wait for 3 seconds
                        
                        # Get current article
                        current_article_index = included_articles[st.session_state.full_text_screening_current_article_index]
                        article_path = st.session_state.downloaded_articles[current_article_index]
                        
                        decision, reason = rag_based_full_text_screening(article_path)
                        st.session_state.full_text_screening_results[current_article_index] = {
                            'decision': decision,
                            'reason': reason,
                            'automated_flag': True
                        }
                        st.write(f"Auto-screening complete. Decision: {decision}")
                        st.write(f"Reason: {reason}")
                        time.sleep(2)  # Display result for 2 seconds
                    full_text_auto_screening_placeholder.empty()
                    
                    # Move to the next article
                    st.session_state.full_text_screening_current_article_index += 1
                    st.session_state.full_text_screening_done_articles += 1
                    if decision == st.session_state.full_text_screening_results.get(current_article_index, {}).get('decision'):
                        st.session_state.full_text_screening_correct_predictions += 1
                    
                    # Rerun the app to update the display
                    st.rerun()
            else:
                st.write("✅ All full text articles have been screened!")
                
    #             # Copy results to full_article_screening_results for compatibility with data extraction
    #             if st.session_state.full_text_screening_results:
    #                 st.session_state.full_article_screening_results = st.session_state.full_text_screening_results.copy()
    
    # # Step 9: Show Full Text Screening Results
    # elif st.session_state.full_text_screening_results:
    #     st.subheader("📊 8) Full Text Screening Results")
        
    #     included_count = sum(1 for result in st.session_state.full_text_screening_results.values() if result['decision'] == 'INCLUDE')
    #     excluded_count = sum(1 for result in st.session_state.full_text_screening_results.values() if result['decision'] == 'EXCLUDE')
        
    #     st.write(f"**Full text articles included:** {included_count}")
    #     st.write(f"**Full text articles excluded:** {excluded_count}")
        
    #     # Show breakdown
    #     with st.expander("📋 View Full Text Screening Details", expanded=False):
    #         for article_index, result in st.session_state.full_text_screening_results.items():
    #             article_path = st.session_state.downloaded_articles[article_index]
    #             article = load_article_from_file(article_path)
                
    #             col1, col2 = st.columns([3, 1])
    #             with col1:
    #                 st.write(f"**{article['Title'][:80]}...**")
    #                 st.write(f"*Reason: {result['reason']}*")
    #             with col2:
    #                 status = "✅ INCLUDE" if result['decision'] == 'INCLUDE' else "❌ EXCLUDE"
    #                 st.write(status)
    #                 if result.get('automated_flag'):
    #                     st.write("🤖 Auto")
    #                 else:
    #                     st.write("👤 Manual")
    #             st.markdown("---")
        
    #     # Copy results to full_article_screening_results for compatibility with data extraction
    #     if st.session_state.full_text_screening_results:
    #         st.session_state.full_article_screening_results = st.session_state.full_text_screening_results.copy()
        
    #     # Proceed to data extraction
    #     if not st.session_state.data_extraction_done:
    #         st.button("🔍 Proceed to Data Extraction...", on_click=lambda: perform_article_data_extraction(), disabled=disabled)

    # if st.session_state.data_extraction_done:
    #     # After data extraction is complete, process and display final results
    #     final_results_df = process_final_results("./data/downloaded_articles")
    #     if final_results_df is not None:
    #         display_final_results(final_results_df)
    #     else:
    #         st.warning("No final results found to display.")
        # Check if full text screening is complete and proceed to data extraction
    if (len(st.session_state.downloaded_articles) > 0 and 
        st.session_state.full_texts_downloaded and
        st.session_state.full_text_screening_current_article_index >= len(included_articles)):
        
        # Step 9: Show Full Text Screening Results
        st.subheader("📊 9) Full Text Screening Results")
        
        included_count = sum(1 for result in st.session_state.full_text_screening_results.values() if result['decision'] == 'INCLUDE')
        excluded_count = sum(1 for result in st.session_state.full_text_screening_results.values() if result['decision'] == 'EXCLUDE')
        
        st.write(f"**Full text articles included:** {included_count}")
        st.write(f"**Full text articles excluded:** {excluded_count}")
        
        # Show breakdown
        with st.expander("📋 View Full Text Screening Details", expanded=False):
            for article_index, result in st.session_state.full_text_screening_results.items():
                article_path = st.session_state.downloaded_articles[article_index]
                article = load_article_from_file(article_path)
                
                if article is None:
                    st.error(f"❌ Error loading article from {article_path}")
                    continue
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{article['Title'][:80]}...**")
                    st.write(f"*Reason: {result['reason']}*")
                with col2:
                    status = "✅ INCLUDE" if result['decision'] == 'INCLUDE' else "❌ EXCLUDE"
                    st.write(status)
                    if result.get('automated_flag'):
                        st.write("🤖 Auto")
                    else:
                        st.write("👤 Manual")
                st.markdown("---")
        
        # Copy results to full_article_screening_results for compatibility with data extraction
        st.session_state.full_article_screening_results = st.session_state.full_text_screening_results.copy()
        
        # Step 10: Data Extraction
        if not st.session_state.data_extraction_done and included_count > 0:
            st.subheader("🔬 10) Data Extraction")
            st.write(f"Ready to extract data from {included_count} articles that passed full text screening.")
            
            if st.button("📊 Start Data Extraction...", disabled=disabled):
                perform_article_data_extraction()
        
        # Show final results if data extraction is complete
        if st.session_state.data_extraction_done:
            final_results_df = process_final_results("./data/downloaded_articles")
            if final_results_df is not None:
                display_final_results(final_results_df)
            else:
                st.warning("No final results found to display.")
    # if len(st.session_state.downloaded_articles) > 0 and st.session_state.summary_screening_current_article_index >= len(st.session_state.downloaded_articles):
    #     if not st.session_state.full_article_screening_results:
    #         perform_full_article_screening()
    #     else:
    #         st.subheader("📄 7) Full Article Screening Results")
    #         st.write("Full article screening has been completed.")
    #         included_count = sum(1 for result in st.session_state.full_article_screening_results.values() if result['decision'] == 'INCLUDE')
    #         excluded_count = sum(1 for result in st.session_state.full_article_screening_results.values() if result['decision'] == 'EXCLUDE')
    #         st.write(f"Articles included: {included_count}")
    #         st.write(f"Articles excluded: {excluded_count}")
    
    # if st.session_state.full_article_screening_results:
    #     perform_article_data_extraction()
    # Replace the section after title/abstract screening with this:

# NEW: Tab suggestion function (like ChatGPT auto-complete)
def show_tab_suggestion(suggestion_type, current_text, context=""):
    """Show tab suggestion like ChatGPT when user is typing"""
    
    # Only show if user has typed something substantial
    if len(current_text.strip()) > 20:
        tab_key = f"{suggestion_type}_tab_suggestion"
        last_text_key = f"{suggestion_type}_last_text"
        
        # Generate suggestion if text changed
        if st.session_state.get(last_text_key, "") != current_text:
            st.session_state[last_text_key] = current_text
            
            # Generate auto-complete suggestion
            try:
                from suggestion_engine import generate_adaptive_suggestion
                
                suggestion = generate_adaptive_suggestion(
                    suggestion_type=f"{suggestion_type}_autocomplete",
                    current_text=current_text,
                    context=context,
                    feedback_history=[]
                )
                
                if suggestion and 'text' in suggestion:
                    # Take first 50 characters for tab completion
                    completion = suggestion['text'][:50] + "..." if len(suggestion['text']) > 50 else suggestion['text']
                    st.session_state[tab_key] = completion
                else:
                    st.session_state[tab_key] = ""
                    
            except Exception as e:
                st.session_state[tab_key] = ""
        # Show tab suggestion if available
        if st.session_state.get(tab_key, ""):
            pass  # Disabled - don't show the blue box
        # st.markdown(f'<div class="tab-suggestion">💡 Press Tab to complete: {st.session_state[tab_key]}</div>', unsafe_allow_html=True)
# MODIFIED: Research section with tab suggestion
def create_enhanced_research_section_with_tab(label, value, height, disabled, default_research_question):
    """Research question section with tab suggestions"""
    
    initialize_suggestion_states()
    
    st.markdown(f"### {label}")
    
    # Main text area
    current_text = st.text_area(
        "",
        value=value,
        height=height,
        disabled=disabled,
        key="research_textarea_enhanced_v2"
    )
    
    # ADD: Tab suggestion
    show_tab_suggestion("research_question", current_text, "")
    
    # KEEP: Original suggestion interface
    updated_text = create_continuous_suggestion_interface(
        "research_question", 
        current_text, 
        context=""
    )
    
    if updated_text != current_text:
        return updated_text
    
    return current_text

# MODIFIED: Extraction section with tab suggestion
def create_enhanced_extraction_section_with_tab(label, value, height, disabled, research_question, default_instructions):
    """Data extraction section with tab suggestions"""
    
    initialize_suggestion_states()
    
    st.markdown(f"### {label}")
    
    # Main text area
    current_text = st.text_area(
        "",
        value=value,
        height=height,
        disabled=disabled,
        key="extraction_textarea_enhanced_v2"
    )
    
    # ADD: Tab suggestion
    show_tab_suggestion("data_extraction", current_text, research_question)
    
    # KEEP: Original suggestion interface
    updated_text = create_continuous_suggestion_interface(
        "data_extraction", 
        current_text, 
        context=research_question
    )
    
    if updated_text != current_text:
        return updated_text
    
    return current_text

# ALL OTHER FUNCTIONS REMAIN EXACTLY THE SAME - COPY FROM YOUR ORIGINAL FILE
def render_mesh_terms(grouped_terms):
    st.subheader("🧩 3) MeSH Terms")
    
    # Create headers for the table
    header_cols = st.columns([1, 3])
    header_cols[0].markdown("**Keyword**")
    header_cols[1].markdown("**MeSH Terms**")
    
    # Iterate over the grouped terms to build the table
    for keyword, mesh_terms in grouped_terms.items():
        # Create columns for the keyword and mesh terms
        row_cols = st.columns([1, 3])  # Adjust column widths as needed
        
        # Display keyword checkbox in the first column
        with row_cols[0]:
            keyword_selected = st.checkbox(
                label=f"🦚 **{keyword}**",
                value=st.session_state.main_keyword_selections.get(keyword, True),
                key=f"keyword_{keyword}"
            )
            st.session_state.main_keyword_selections[keyword] = keyword_selected
        
        # Disable mesh terms checkboxes if keyword is not selected
        terms_disabled = not keyword_selected
        
        # Display mesh terms with checkboxes in the second column
        with row_cols[1]:
            # Arrange mesh terms in multiple columns within the second column
            sub_cols = st.columns(2)  # Number of sub-columns
            
            # Split mesh terms for sub-columns
            terms_chunks = [mesh_terms[i::2] for i in range(2)]
            
            for idx, terms in enumerate(terms_chunks):
                with sub_cols[idx]:
                    for term in terms:
                        term_key = f"term_{keyword}_{term}"
                        if keyword not in st.session_state.mesh_terms_selection:
                            st.session_state.mesh_terms_selection[keyword] = {}
                        term_selected = st.checkbox(
                            term,
                            value=st.session_state.mesh_terms_selection[keyword].get(term, True),
                            key=term_key,
                            disabled=terms_disabled
                        )
                        st.session_state.mesh_terms_selection[keyword][term] = term_selected
        
        st.markdown("""<hr style="margin-top: 0px; margin-bottom: 0px;">""", unsafe_allow_html=True)

def run_extract_keywords():
    # Set processing state to True
    st.session_state.processing = True
    
    # Retrieve the research question from session state
    research_question = st.session_state.research_question
    
    # Perform the processing
    with st.spinner('Processing...'):
        # Simulate a long-running task
        st.session_state.found_keywords = extract_keywords(research_question)
    
    # Set processing state to False
    st.session_state.processing = False

def run_find_mesh_terms():
    # Set processing state to True
    st.session_state.processing = True
    
    # Retrieve the keywords from session state
    keywords = st.session_state.keywords.copy()
    
    # Initialize progress elements
    progress_text = st.empty()
    progress_bar = st.progress(0)
    total_keywords = len(keywords)
    completed_keywords = 0
    
    # Lists to keep track
    remaining_keywords = keywords.copy()
    finished_keywords = []
    
    # Placeholders for displaying lists
    remaining_keywords_placeholder = st.empty()
    finished_keywords_placeholder = st.empty()
    
    # Perform the processing
    grouped_terms = {}
    for keyword in keywords:
        # Update progress text
        progress_text.text(f"Processing keyword: '{keyword}' ({completed_keywords}/{total_keywords})")
        
        # Update lists
        remaining_keywords_placeholder.text(f"**Remaining keywords:** {', '.join(remaining_keywords)}")
        finished_keywords_placeholder.text(f"**Finished keywords:** {', '.join(finished_keywords)}")
        
        # Process keyword
        mesh_terms = get_mesh_terms(keyword)
        
        # Store results
        if len(mesh_terms) == 0:
            st.warning(f"No mesh terms found for '{keyword}'")
        else:
            grouped_terms[keyword] = mesh_terms
        
        this_group_only = {keyword: mesh_terms}
        is_relevant = are_mesh_terms_relevant(this_group_only, st.session_state.research_question)
        st.session_state.main_keyword_selections[keyword] = is_relevant
        
        # Update progress
        completed_keywords += 1
        progress_bar.progress(completed_keywords / total_keywords)
        
        # Update lists
        remaining_keywords.remove(keyword)
        finished_keywords.append(keyword)
        
        # Sleep to allow UI to update
        time.sleep(0.1)
    
    # After processing
    progress_text.text("Processing complete.")
    remaining_keywords_placeholder.text("**Remaining keywords:** None")
    finished_keywords_placeholder.text(f"**Finished keywords:** {', '.join(finished_keywords)}")
    st.session_state.grouped_terms = grouped_terms
    st.session_state.processing = False

def run_generate_search_strategy():
    """Generate search query with proper concept grouping, enhanced with manual query"""
    st.session_state.processing = True
    
    grouped_terms = st.session_state.grouped_terms
    
    # Optional: enhance generation with a local manual query file (set MANUAL_QUERY_PATH in .env)
    from config import config as app_config
    manual_query_path = app_config.MANUAL_QUERY_PATH or os.getenv('MANUAL_QUERY_PATH', '')
    manual_components = None
    
    if load_manual_query_components and manual_query_path:
        try:
            manual_components = load_manual_query_components(manual_query_path)
            if manual_components:
                print("🔧 Enhancing query with manual review knowledge...")
                grouped_terms = enhance_grouped_terms_with_manual(grouped_terms, manual_components)
                print(f"   ✅ Enhanced with {len(manual_components.get('mesh_terms', set()))} manual MeSH terms")
        except Exception as e:
            print(f"   ⚠️  Could not load manual query: {e}")
            manual_components = None
    elif not manual_query_path:
        print("ℹ️  MANUAL_QUERY_PATH not set; generating search strategy without manual query enhancement.")
    
    # Group keywords by semantic concepts
    concept_groups = group_keywords_by_concepts(grouped_terms)
    
    term_groups = []
    
    for concept_name, concept_terms in concept_groups.items():
        if not concept_terms:  # Skip empty concepts
            continue
            
        group_terms = []
        
        # Simplified: Use wildcards and prioritize MeSH terms to reduce query length
        for term in concept_terms:
            # Add Title/Abstract search with wildcard if term is long enough
            if len(term) >= 4:
                # Use wildcard for variations (e.g., hypertens*)
                base_term = term.lower().rstrip('s')  # Remove plural
                if len(base_term) >= 4:
                    group_terms.append(f'"{base_term}*"[Title/Abstract]')
                else:
                    group_terms.append(f'"{term}"[Title/Abstract]')
            else:
                group_terms.append(f'"{term}"[Title/Abstract]')
            
            # Add MeSH Terms (limit to top 5 to include more manual terms)
            mesh_terms = find_all_mesh_terms_for_keyword(term, grouped_terms)
            for mesh_term in mesh_terms[:5]:  # Increased from 3 to 5 to include more manual terms
                clean_mesh_term = mesh_term.replace('[Title/Abstract]', '').replace('[MeSH Terms]', '').strip()
                if clean_mesh_term and f'"{clean_mesh_term}"[MeSH Terms]' not in group_terms:
                    group_terms.append(f'"{clean_mesh_term}"[MeSH Terms]')
        
        if group_terms:
            # All terms within a concept are connected with OR
            term_groups.append(f"({' OR '.join(group_terms)})")
    
    # All concept groups are connected with AND
    search_query = " AND ".join(term_groups)
    
    # Add comprehensive PubMed filters aligned with manual query
    # Using PubMed's filter format that matches manual query structure
    # First add MeSH Terms filters, then Filter tags
    filters = ' AND "humans"[MeSH Terms] AND "english"[Language] AND ((y_10[Filter]) AND (humans[Filter]) AND (english[Filter]) AND (alladult[Filter]))'
    search_query = search_query + filters
    
    # NEW: Further enhance with critical manual terms
    if manual_components and enhance_query_with_manual_terms:
        try:
            search_query = enhance_query_with_manual_terms(search_query, manual_components)
            print("   ✅ Added critical missing MeSH terms from manual query")
        except Exception as e:
            print(f"   ⚠️  Could not enhance query with manual terms: {e}")
    
    # Clean up any double ANDs
    search_query = re.sub(r'\s+AND\s+AND\s+', ' AND ', search_query)
    
    print(f"🔍 Query Length: {len(search_query)} characters")
    print(f"🔍 Search Query:\n{search_query}\n")
    
    st.session_state.processing = False
    st.session_state.search_query = search_query
    
    # Validate immediately
    st.session_state.search_query_validation_result = validate_boolean_search_query(search_query)
    
    # Generate comparison report (backend only)
    generate_comparison_report()

def group_keywords_by_concepts(grouped_terms):
    """Group keywords by semantic concepts based on manual strategy"""
    try:
        from .manual_search_strategy import MANUAL_SEARCH_STRATEGY
    except ImportError:
        from manual_search_strategy import MANUAL_SEARCH_STRATEGY
    
    concept_groups = {
        "hypertension_concepts": [],
        "metabolomics_concepts": [],
        "antihypertensive_drugs": [],
        "treatment_response": [],
        "other_concepts": []  # Catch-all for unmatched keywords
    }
    
    # Map keywords to concepts
    for keyword, mesh_terms in grouped_terms.items():
        keyword_lower = keyword.lower()
        matched = False
        
        # Categorize keywords
        if any(term in keyword_lower for term in ["hypertension", "blood pressure", "htn"]):
            concept_groups["hypertension_concepts"].append(keyword)
            matched = True
        elif any(term in keyword_lower for term in ["metabolomics", "metabolome", "metabolites", "pharmacometabolomics"]):
            concept_groups["metabolomics_concepts"].append(keyword)
            matched = True
        elif any(term in keyword_lower for term in ["antihypertensive", "diuretics", "beta-blockers", "beta blockers", "ace inhibitors", "arbs", "angiotensin receptor blockers", "vasodilator", "vasodilators", "calcium channel blockers", "ccb"]):
            concept_groups["antihypertensive_drugs"].append(keyword)
            matched = True
        elif any(term in keyword_lower for term in ["treatment response", "drug response", "therapeutic response"]):
            concept_groups["treatment_response"].append(keyword)
            matched = True
        
        # FIX: Add unmatched keywords to other_concepts so they're not lost
        if not matched:
            concept_groups["other_concepts"].append(keyword)
    
    return concept_groups

def find_all_mesh_terms_for_keyword(keyword, grouped_terms):
    """Find ALL MeSH terms for a keyword (clean, no tags)"""
    mesh_terms = []
    if keyword in grouped_terms:
        for term in grouped_terms[keyword]:
            # Clean term - remove any existing tags
            clean_term = term.replace('[Title/Abstract]', '').replace('[MeSH Terms]', '').strip()
            if clean_term and clean_term not in mesh_terms:
                mesh_terms.append(clean_term)
    return mesh_terms

def generate_comparison_report():
    """Generate comparison report for evaluation (backend only)"""
    try:
        try:
            from .search_strategy_comparator import SearchStrategyComparator
        except ImportError:
            from search_strategy_comparator import SearchStrategyComparator
        
        comparator = SearchStrategyComparator()
        
        # Get LLM data
        llm_keywords = st.session_state.found_keywords
        grouped_terms = st.session_state.grouped_terms
        llm_query = st.session_state.search_query
        
        # Generate comprehensive report
        report = comparator.generate_comprehensive_report(llm_keywords, grouped_terms, llm_query)
        
        # Save report to file
        import json
        import os
        
        report_path = "data/comparison_report.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Comparison report saved to {report_path}")
        print(f"📈 Overall Performance: {report['overall_performance']['score']:.2f} ({report['overall_performance']['grade']})")
        
        # ALSO generate comprehensive evaluation silently
        comprehensive_report = generate_comprehensive_evaluation()
        if comprehensive_report:
            print("📊 Comprehensive evaluation completed silently")
        
    except Exception as e:
        print(f"Error generating comparison report: {e}")

def generate_comprehensive_evaluation():
    """Generate comprehensive evaluation report silently in background"""
    try:
        try:
            from .comprehensive_evaluator import ComprehensiveEvaluator
        except ImportError:
            from comprehensive_evaluator import ComprehensiveEvaluator
        
        # Optional EndNote library path for validation (set ENDNOTE_FILE_PATH in .env)
        from config import config as app_config
        endnote_file_path = app_config.ENDNOTE_FILE_PATH or os.getenv('ENDNOTE_FILE_PATH', '')
        
        if not endnote_file_path or not os.path.exists(endnote_file_path):
            print("⚠️ ENDNOTE_FILE_PATH not set or file not found; skipping comprehensive evaluation.")
            return None
        
        evaluator = ComprehensiveEvaluator(endnote_file_path)
        
        # FIX: Load manual data if not already loaded
        if not evaluator.all_manual_data or not evaluator.pubmed_manual_data:
            evaluator.load_manual_data()
        
        # Get LLM data from session state
        llm_keywords = st.session_state.found_keywords
        llm_grouped_terms = st.session_state.grouped_terms
        llm_query = st.session_state.search_query
        llm_articles = st.session_state.downloaded_articles
        llm_screening_results = st.session_state.summary_screening_results
        llm_extracted_data = []  # You'll implement this later
        
        # FIX: Add timestamp to force regeneration
        import time
        timestamp = time.time()
        
        # Generate comprehensive report silently
        report = evaluator.generate_comprehensive_report(
            llm_keywords, llm_grouped_terms, llm_query, 
            llm_articles, llm_screening_results, llm_extracted_data
        )
        
        # FIX: Update report with timestamp
        if report:
            report['generation_timestamp'] = timestamp
            report['query_used'] = llm_query[:200] if llm_query else ''  # Store query snippet for verification
        
        return report
        
    except Exception as e:
        print(f"❌ Error generating comprehensive evaluation: {e}")
        import traceback
        traceback.print_exc()  # FIX: Show full error
        return None

def run_download_articles_with_query(query_text=None):
    """
    Download articles using either provided query text or session state query
    
    Args:
        query_text: Query text to use (if None, uses session state)
    """
    # Set processing state to True
    st.session_state.processing = True
    
    try:
        # Use provided query text or fall back to session state
        if query_text is not None:
            search_query = query_text
            # Update session state with the new query
            st.session_state.search_query = query_text
        else:
            # Retrieve the search query from session state
            search_query = st.session_state.search_query
        
        # Ensure search_query is not None or empty
        if not search_query or search_query.strip() == '':
            st.error("❌ Search query is empty. Please generate a search strategy first.")
            st.session_state.processing = False
            return
        
        # FIX: Check if query has changed (for debugging)
        query_hash = hash(search_query)
        if hasattr(st.session_state, 'last_query_hash'):
            if st.session_state.last_query_hash == query_hash:
                st.info("ℹ️ Using same query as before - results may be similar")
            else:
                st.info("🔄 Query has changed - fetching new results")
        st.session_state.last_query_hash = query_hash
        
        # Final validation before download
        validation_result = validate_boolean_search_query(search_query)
        if not validation_result['is_valid']:
            st.error("Cannot download articles: Search query has validation errors")
            st.session_state.processing = False
            return
        
        all_articles = []
        # FIX: Remove hardcoded date parameters - let the query handle it
        # The query already has date filters, so don't add them again
        all_articles.extend(download_articles_from_pubmed(search_query, max_articles=None))
        
        st.session_state.downloaded_articles = all_articles
        
        # FIX: Clear old screening results when new articles are downloaded
        st.session_state.summary_screening_results = {}
        st.session_state.summary_screening_current_article_index = 0
        
    except Exception as e:
        st.error(f"Error downloading articles: {str(e)}")
        st.error("Please check your search query and internet connection.")
        # Print full traceback for debugging
        import traceback
        st.text(traceback.format_exc())
    finally:
        st.session_state.processing = False

def run_download_articles():
    """Download articles using search query from session state (for backward compatibility)"""
    run_download_articles_with_query(None)

def run_de_duplicate_articles():
    # Set processing state to True
    st.session_state.processing = True
    try:
        articles_dir = Path("./data/downloaded_articles")
        removed_articles_count = deduplicate_articles(str(articles_dir))
        print(f"🧹 Removed {removed_articles_count} articles")

        # Refresh session state with the updated file list to avoid missing-file errors
        updated_files = sorted(str(path) for path in articles_dir.glob("*_source.json"))
        st.session_state.downloaded_articles = updated_files

        # Clear any cached screening outputs to keep indexes consistent
        st.session_state.summary_screening_results = {}
        st.session_state.summary_screening_current_article_index = 0

        st.session_state.removed_articles_count = removed_articles_count
    finally:
        st.session_state.processing = False

def display_article_dataframe():
    articles_data = []
    for article_path in st.session_state.downloaded_articles:
        article_info = load_article_from_file(article_path)
        if article_info is not None:  # Filter out None values
            articles_data.append(article_info)
    df = pd.DataFrame(articles_data)
    df['Screened'] = df.index.map(lambda i: '✅' if i in st.session_state.summary_screening_results else '⏳')
    df['Decision'] = df.index.map(lambda i: st.session_state.summary_screening_results.get(i, {}).get('decision', ''))
    df['Automated'] = df.index.map(lambda i: st.session_state.summary_screening_results.get(i, {}).get('automated_flag', ''))
    
    df = df[['Screened', 'Decision', 'Automated', 'Title', 'Abstract', 'Authors', 'Publication Date', 'Journal', 'E-Location']]
    
    # Fix PyArrow conversion error by ensuring consistent data types
    if not df.empty:
        # Clean all columns that might cause PyArrow conversion issues
        for col in df.columns:
            if col in ['Title', 'Abstract', 'Authors', 'Journal', 'Publication Date', 'E-Location', 'Screened', 'Decision', 'Automated']:
                df[col] = df[col].astype(str).fillna('N/A')
    
    # Highlight current article
    def highlight_current(row):
        if row.name == st.session_state.summary_screening_current_article_index:
            return ['background-color: yellow'] * len(row)
        return [''] * len(row)
    
    st.dataframe(df.style.apply(highlight_current, axis=1))

def display_current_article():
    if st.session_state.summary_screening_current_article_index < len(st.session_state.downloaded_articles):
        article_path = st.session_state.downloaded_articles[st.session_state.summary_screening_current_article_index]
        print(f"🤓 Article: {article_path}")
        with open(article_path, 'r') as file:
            article = load_article_from_file(article_path)
            if article is None:
                st.error(f"❌ Error loading article from {article_path}")
                return
            
            st.write(f"**Title:** {article['Title']}")
            st.write(f"**Authors:** {article['Authors']}")
            st.write(f"**Abstract:** {article['Abstract']}")
            st.write(f"**Publication Date:** {article['Publication Date']}")
            st.write(f"**Journal:** {article['Journal']}")
        
            decision, reason = rag_based_summary_screening(article_path)
            st.write(f"**Model Decision:** {decision}")
            
            # Add a text area for the reason, pre-filled with the model's reason
            reason = st.text_area("Reason for inclusion/exclusion:", value=reason, key="reason_text_area")
            
            st.session_state.summary_screening_results[st.session_state.summary_screening_current_article_index] = {
                'decision': decision,
                'reason': reason,
                'automated_flag': st.session_state.screening_mode == 'auto'
            }

def display_screening_stats():
    total_screened = st.session_state.summary_screening_done_articles
    accuracy = (st.session_state.summary_screening_correct_predictions / total_screened * 100) if total_screened > 0 else 0
    st.write(f"**Total Screened:** {total_screened}")
    st.write(f"**Correct Predictions:** {st.session_state.summary_screening_correct_predictions}")
    st.write(f"**Accuracy:** {accuracy:.2f}%")

def handle_user_decision(decision):
    current_index = st.session_state.summary_screening_current_article_index
    current_screening_result = st.session_state.summary_screening_results.get(current_index, {})
    
    # Get the reason from the text area
    reason = st.session_state.get('full_text_reason_text_area', '')
    
    user_screening_result = {
        'decision': decision,
        'reason': reason,
        'automated_flag': False
    }
    st.session_state.summary_screening_done_articles += 1
    if current_screening_result.get('decision', '') == decision:
        st.session_state.summary_screening_correct_predictions += 1
    st.session_state.summary_screening_results[current_index] = user_screening_result
    
    add_rag_example(st.session_state.downloaded_articles[current_index], decision, reason)
    
    st.session_state.summary_screening_current_article_index += 1

def toggle_auto_screening():
    st.session_state.screening_mode = 'auto' if st.session_state.screening_mode == 'manual' else 'manual'

def remove_excluded_article(index):
    file_path = f"./data/downloaded_articles/article_{index+1}_source.json"
    if os.path.exists(file_path):
        os.remove(file_path)

def perform_article_data_extraction():
    st.subheader("🤷🏻‍♀️ Data Extraction in Progress...")
    
    # Get all included articles from the FULL TEXT screening (not summary screening)
    included_articles = [
        article for article, result in st.session_state.full_text_screening_results.items()
        if result['decision'] == 'INCLUDE'
    ]
    
    # CLEANUP: Remove old extraction files before starting new extraction
    cleanup_old_extraction_files()
    
    total_articles = len(included_articles)
    extracted_articles = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for article_index in included_articles:
        article_path = st.session_state.downloaded_articles[article_index]
        
        status_text.text(f"Extracting data from article {extracted_articles + 1}/{total_articles}")
        extract_single_article_data(article_path, st.session_state.final_result_instructions)
        
        extracted_articles += 1
        progress_bar.progress(extracted_articles / total_articles)
    
    st.session_state.data_extraction_done = True
    status_text.text("✅ Data extraction completed.")

def cleanup_old_extraction_files():
    """Remove old extraction files to ensure clean extraction results"""
    try:
        directory_path = "./data/downloaded_articles"
        if os.path.exists(directory_path):
            for filename in os.listdir(directory_path):
                if filename.endswith('_extracted.json'):
                    file_path = os.path.join(directory_path, filename)
                    os.remove(file_path)
                    print(f"Removed old extraction file: {filename}")
    except Exception as e:
        print(f"Error cleaning up old extraction files: {e}")

def process_final_results(directory_path):
    """
    Process extracted JSON files to create a DataFrame of final results
    and save it to CSV.
    
    Args:
        directory_path (str): Path to directory containing extracted JSON files
        
    Returns:
        pd.DataFrame: DataFrame containing the processed results
    """
    # Get only articles that passed FULL TEXT screening
    included_articles = [
        article for article, result in st.session_state.full_text_screening_results.items()
        if result['decision'] == 'INCLUDE'
    ]
    
    # List to store all final results
    all_results = []
    
    # Only process extraction files for included articles
    for article_index in included_articles:
        article_path = st.session_state.downloaded_articles[article_index]
        extracted_filename = article_path.replace('_source.json', '_extracted.json')
        
        if os.path.exists(extracted_filename):
            source_file_path = article_path
            
            try:
                with open(extracted_filename, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    result_entry = data.get('final_results', {})
                    
                    final_results = []
                    if isinstance(result_entry, list):
                        final_results = result_entry
                    elif isinstance(result_entry, dict):
                        final_results = [result_entry]
                    
                    with open(source_file_path, 'r', encoding='utf-8') as source_file:
                        source_data = json.load(source_file)
                        # read from MedlineCitation.Article.ELocationID
                        MedlineCitation = source_data.get('MedlineCitation', {})
                        Article = MedlineCitation.get('Article', {})
                        
                        final_elocations = []
                        ELocationID = Article.get('ELocationID', [])
                        if isinstance(ELocationID, list):
                            final_elocations = ELocationID
                        elif isinstance(ELocationID, str):
                            final_elocations = [ELocationID]
                        else:
                            final_elocations = []
                        
                        for result in final_results:
                            result['ELocations'] = ', '.join(final_elocations)
                            all_results.append(result)
            except Exception as e:
                st.error(f"Error processing file {extracted_filename}: {str(e)} stack: {traceback.format_exc()}")
    
    if not all_results:
        return None
        
    # Create DataFrame from results
    df = pd.DataFrame(all_results)
    
    # Save to CSV
    csv_path = os.path.join(directory_path, 'final_results.csv')
    df.to_csv(csv_path, index=False)
    
    return df

def display_final_results(df):
    """
    Display final results in Streamlit UI with formatting.
    
    Args:
        df (pd.DataFrame): DataFrame containing the final results
    """
    st.subheader("📊 Final Extracted Results")
    
    # Display summary statistics
    st.write(f"Total articles processed: {len(df)}")
    
    # Create an expander for the full results table
    with st.expander("View Full Results Table", expanded=True):
        # Apply styling to the dataframe
        styled_df = df.style.set_properties(**{
            'background-color': '#f0f2f6',
            'color': 'black',
            'border-color': 'white'
        })
        
        # Display the styled dataframe
        st.dataframe(styled_df, use_container_width=True)
    
    # Add download button for CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv,
        file_name="final_results.csv",
        mime="text/csv"
    )

# Enhanced suggestion system functions
def initialize_suggestion_states():
    """Initialize session state variables for the enhanced suggestion system"""
    if 'suggestion_history' not in st.session_state:
        st.session_state.suggestion_history = []
    if 'current_suggestion_index' not in st.session_state:
        st.session_state.current_suggestion_index = 0
    if 'user_feedback' not in st.session_state:
        st.session_state.user_feedback = []
    if 'generating_suggestion' not in st.session_state:
        st.session_state.generating_suggestion = False

def create_continuous_suggestion_interface(suggestion_type, current_text, context=""):
    """Create a continuous suggestion interface with Next button"""
    
    # Initialize suggestion state for this type
    suggestion_key = f"{suggestion_type}_suggestions"
    if suggestion_key not in st.session_state:
        st.session_state[suggestion_key] = []
    
    current_index_key = f"{suggestion_type}_current_index"
    if current_index_key not in st.session_state:
        st.session_state[current_index_key] = 0
    
    # Container for the suggestion
    suggestion_container = st.container()
    
    with suggestion_container:
        # Control buttons row
        col1, spacer1, col2, spacer2, col3, spacer3, col4 = st.columns([1, 0.006, 1, 0.006, 1, 0.006, 2])
        
        with col1:
            if st.button("💡 Inspire", key=f"{suggestion_type}_toggle", 
                        help="Generate AI suggestions", use_container_width=True):
                # Generate first suggestion if none exist
                if not st.session_state[suggestion_key]:
                    with st.spinner("Generating suggestion..."):
                        new_suggestion = generate_single_suggestion(suggestion_type, current_text, context)
                        if new_suggestion:
                            st.session_state[suggestion_key].append(new_suggestion)
                            st.session_state[current_index_key] = 0
        
        with col2:
            if st.button("➡️ Next", key=f"{suggestion_type}_next", 
                        disabled=not st.session_state[suggestion_key],
                        use_container_width=True):
                # Generate next suggestion
                with st.spinner("Generating next suggestion..."):
                    new_suggestion = generate_single_suggestion(suggestion_type, current_text, context)
                    if new_suggestion:
                        st.session_state[suggestion_key].append(new_suggestion)
                        st.session_state[current_index_key] = len(st.session_state[suggestion_key]) - 1
        
        with col3:
            if st.button("🗑️ Clear", key=f"{suggestion_type}_clear", 
                        disabled=not st.session_state[suggestion_key],
                        use_container_width=True):
                st.session_state[suggestion_key] = []
                st.session_state[current_index_key] = 0
        
        # Display current suggestion if available
        if st.session_state[suggestion_key]:
            current_idx = st.session_state[current_index_key]
            current_suggestion = st.session_state[suggestion_key][current_idx]
            
            st.markdown("---")
            
            # Suggestion display
            with st.container():
                st.markdown(f"**🎯 Suggestion {current_idx + 1} of {len(st.session_state[suggestion_key])}**")
                
                # Preview in expandable section
                with st.expander("👀 Preview", expanded=True):
                    st.write(current_suggestion['text'])
                
                # Action buttons with feedback tracking
                action_col1, spacer1, action_col2, spacer2, action_col3, spacer3, action_col4 = st.columns([1, 0.006, 1, 0.006, 1, 0.006, 2])
                
                with action_col1:
                    if st.button("📋 Use", key=f"{suggestion_type}_use_{current_idx}", 
                                help="Replace current text"):
                        # Track positive feedback
                        track_user_feedback(suggestion_type, current_suggestion, "used", current_text)
                        return current_suggestion['text']
                
                with action_col2:
                    if st.button("➕ Add", key=f"{suggestion_type}_add_{current_idx}", 
                                help="Add to current text"):
                        # Track positive feedback
                        track_user_feedback(suggestion_type, current_suggestion, "added", current_text)
                        return current_text + "\n\n" + current_suggestion['text']
                
                with action_col3:
                    if st.button("💨 Skip", key=f"{suggestion_type}_skip_{current_idx}", 
                                help="Not useful"):
                        # Track negative feedback
                        track_user_feedback(suggestion_type, current_suggestion, "skipped", current_text)
                        # Auto-generate next suggestion
                        with st.spinner("Getting next suggestion..."):
                            new_suggestion = generate_single_suggestion(suggestion_type, current_text, context)
                            if new_suggestion:
                                st.session_state[suggestion_key].append(new_suggestion)
                                st.session_state[current_index_key] = len(st.session_state[suggestion_key]) - 1
                                st.rerun()
                
                # Navigation if multiple suggestions exist
                if len(st.session_state[suggestion_key]) > 1:
                    st.markdown("**Navigate suggestions:**")
                    nav_cols = st.columns([1, 1, 1])
                    
                    with nav_cols[0]:
                        if st.button("⬅️", key=f"{suggestion_type}_prev", 
                                    disabled=current_idx == 0):
                            st.session_state[current_index_key] = max(0, current_idx - 1)
                            st.rerun()
                    
                    with nav_cols[1]:
                        st.write(f"Suggestion {current_idx + 1} of {len(st.session_state[suggestion_key])}")
                    
                    with nav_cols[2]:
                        if st.button("➡️", key=f"{suggestion_type}_next_nav", 
                                    disabled=current_idx == len(st.session_state[suggestion_key]) - 1):
                            st.session_state[current_index_key] = min(len(st.session_state[suggestion_key]) - 1, current_idx + 1)
                            st.rerun()
    
    return current_text

# KEEP: No nested expanders version for criteria sections
def create_continuous_suggestion_interface_no_expander(suggestion_type, current_text, context=""):
    """Create a continuous suggestion interface WITHOUT nested expanders for criteria sections"""
    
    # Initialize suggestion state for this type
    suggestion_key = f"{suggestion_type}_suggestions"
    if suggestion_key not in st.session_state:
        st.session_state[suggestion_key] = []
    
    current_index_key = f"{suggestion_type}_current_index"
    if current_index_key not in st.session_state:
        st.session_state[current_index_key] = 0
    
    # Container for the suggestion
    suggestion_container = st.container()
    
    with suggestion_container:
        # Control buttons row - smaller for criteria
        col1, spacer1, col2, spacer2, col3 = st.columns([1, 0.006, 1, 0.006, 1])
        
        with col1:
            if st.button("💡", key=f"{suggestion_type}_toggle", 
                        help="Generate AI suggestions", use_container_width=True):
                # Generate first suggestion if none exist
                if not st.session_state[suggestion_key]:
                    with st.spinner("Generating..."):
                        new_suggestion = generate_single_suggestion(suggestion_type, current_text, context)
                        if new_suggestion:
                            st.session_state[suggestion_key].append(new_suggestion)
                            st.session_state[current_index_key] = 0
        
        with col2:
            if st.button("➡️", key=f"{suggestion_type}_next", 
                        disabled=not st.session_state[suggestion_key],
                        help="Next suggestion", use_container_width=True):
                # Generate next suggestion
                with st.spinner("Next..."):
                    new_suggestion = generate_single_suggestion(suggestion_type, current_text, context)
                    if new_suggestion:
                        st.session_state[suggestion_key].append(new_suggestion)
                        st.session_state[current_index_key] = len(st.session_state[suggestion_key]) - 1
        
        with col3:
            if st.button("🗑️", key=f"{suggestion_type}_clear", 
                        disabled=not st.session_state[suggestion_key],
                        help="Clear suggestions", use_container_width=True):
                st.session_state[suggestion_key] = []
                st.session_state[current_index_key] = 0
        
        # Display current suggestion if available - NO EXPANDER!
        if st.session_state[suggestion_key]:
            current_idx = st.session_state[current_index_key]
            current_suggestion = st.session_state[suggestion_key][current_idx]
            
            # Use styled container instead of expander
            st.markdown(f"**💡 Suggestion {current_idx + 1}/{len(st.session_state[suggestion_key])}**")
            st.write(current_suggestion['text'])
            
            # Compact action buttons
            action_col1, spacer1, action_col2, spacer2, action_col3 = st.columns([1, 0.006, 1, 0.006, 1])
            
            with action_col1:
                if st.button("📋 Use", key=f"{suggestion_type}_use_{current_idx}", 
                            help="Replace current text", use_container_width=True):
                    track_user_feedback(suggestion_type, current_suggestion, "used", current_text)
                    return current_suggestion['text']
            
            with action_col2:
                if st.button("➕ Add", key=f"{suggestion_type}_add_{current_idx}", 
                            help="Add to current text", use_container_width=True):
                    track_user_feedback(suggestion_type, current_suggestion, "added", current_text)
                    return current_text + "\n\n" + current_suggestion['text']
            
            with action_col3:
                if st.button("💨 Skip", key=f"{suggestion_type}_skip_{current_idx}", 
                            help="Not useful", use_container_width=True):
                    track_user_feedback(suggestion_type, current_suggestion, "skipped", current_text)
                    # Auto-generate next suggestion
                    with st.spinner("Next..."):
                        new_suggestion = generate_single_suggestion(suggestion_type, current_text, context)
                        if new_suggestion:
                            st.session_state[suggestion_key].append(new_suggestion)
                            st.session_state[current_index_key] = len(st.session_state[suggestion_key]) - 1
                            st.rerun()
    
    return current_text

def generate_single_suggestion(suggestion_type, current_text, context=""):
    """Generate a single suggestion using the enhanced suggestion engine"""
    try:
        from suggestion_engine import generate_adaptive_suggestion
        
        # Get user feedback history for this suggestion type
        feedback_history = [f for f in st.session_state.get('user_feedback', []) 
                          if f.get('suggestion_type') == suggestion_type]
        
        suggestion = generate_adaptive_suggestion(
            suggestion_type=suggestion_type,
            current_text=current_text,
            context=context,
            feedback_history=feedback_history
        )
        
        return suggestion
        
    except Exception as e:
        st.error(f"Error generating suggestion: {e}")
        return None

def track_user_feedback(suggestion_type, suggestion, action, original_text):
    """Track user feedback for RAG-based improvement"""
    
    feedback_entry = {
        'timestamp': time.time(),
        'suggestion_type': suggestion_type,
        'suggestion_text': suggestion['text'],
        'suggestion_id': suggestion.get('id', 'unknown'),
        'action': action,  # 'used', 'added', 'skipped'
        'original_text': original_text,
        'context': suggestion.get('context', '')
    }
    
    if 'user_feedback' not in st.session_state:
        st.session_state.user_feedback = []
    
    st.session_state.user_feedback.append(feedback_entry)
    
    # Also save to a persistent store (optional)
    save_feedback_to_storage(feedback_entry)

def save_feedback_to_storage(feedback_entry):
    """Save feedback to persistent storage for long-term learning"""
    try:
        import json
        import os
        
        feedback_file = "data/user_feedback.jsonl"
        os.makedirs(os.path.dirname(feedback_file), exist_ok=True)
        
        with open(feedback_file, "a") as f:
            f.write(json.dumps(feedback_entry) + "\n")
            
    except Exception as e:
        print(f"Error saving feedback: {e}")
        
# This function is removed - replaced by interactive full text screening

# def perform_article_data_extraction():
#     st.subheader("🤷🏻‍♀️ 8) Data Extraction")
    
#     # DEBUG: Show what's in full_article_screening_results
#     st.write("**DEBUG: Full Article Screening Results:**")
#     for article_idx, result in st.session_state.full_article_screening_results.items():
#         st.write(f"Article {article_idx}: {result['decision']} - {result['reason']}")
    
#     # Get all included articles from the full text screening
#     included_articles = [
#         article for article, result in st.session_state.full_article_screening_results.items()
#         if result['decision'] == 'INCLUDE'
#     ]
    
#     st.write(f"**DEBUG: Found {len(included_articles)} articles marked as INCLUDE in full text screening**")
    
    
#     total_articles = len(included_articles)
#     extracted_articles = 0
    
#     progress_bar = st.progress(0)
#     status_text = st.empty()
    
#     for article_index in included_articles:
#         article_path = st.session_state.downloaded_articles[article_index]
        
#         status_text.text(f"Extracting data from article {extracted_articles + 1}/{total_articles}")
#         extract_single_article_data(article_path, st.session_state.final_result_instructions)
        
#         extracted_articles += 1
#         progress_bar.progress(extracted_articles / total_articles)
    
#     st.session_state.data_extraction_done = True
#     status_text.text("Data extraction completed.")
# Duplicate removed - using the original version above

def process_final_results(directory_path):
    """
    Process extracted JSON files to create a DataFrame of final results
    and save it to CSV.
    
    Args:
        directory_path (str): Path to directory containing extracted JSON files
        
    Returns:
        pd.DataFrame: DataFrame containing the processed results
    """
    # Get only articles that passed FULL TEXT screening
    included_articles = [
        article for article, result in st.session_state.full_text_screening_results.items()
        if result['decision'] == 'INCLUDE'
    ]
    
    # List to store all final results
    all_results = []
    
    # Only process extraction files for included articles
    for article_index in included_articles:
        article_path = st.session_state.downloaded_articles[article_index]
        extracted_filename = article_path.replace('_source.json', '_extracted.json')
        
        if os.path.exists(extracted_filename):
            source_file_path = article_path
            
            try:
                with open(extracted_filename, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    result_entry = data.get('final_results', {})
                    
                    final_results = []
                    if isinstance(result_entry, list):
                        final_results = result_entry
                    elif isinstance(result_entry, dict):
                        final_results = [result_entry]
                    
                    with open(source_file_path, 'r', encoding='utf-8') as source_file:
                        source_data = json.load(source_file)
                        # read from MedlineCitation.Article.ELocationID
                        MedlineCitation = source_data.get('MedlineCitation', {})
                        Article = MedlineCitation.get('Article', {})
                        
                        final_elocations = []
                        ELocationID = Article.get('ELocationID', [])
                        if isinstance(ELocationID, list):
                            final_elocations = ELocationID
                        elif isinstance(ELocationID, str):
                            final_elocations = [ELocationID]
                        else:
                            final_elocations = []
                        
                        for result in final_results:
                            result['ELocations'] = ', '.join(final_elocations)
                            all_results.append(result)
            except Exception as e:
                st.error(f"Error processing file {extracted_filename}: {str(e)} stack: {traceback.format_exc()}")
    
    if not all_results:
        return None
        
    # Create DataFrame from results
    df = pd.DataFrame(all_results)
    
    # Save to CSV
    csv_path = os.path.join(directory_path, 'final_results.csv')
    df.to_csv(csv_path, index=False)
    
    return df

def display_final_results(df):
    """
    Display final results in Streamlit UI with formatting.
    
    Args:
        df (pd.DataFrame): DataFrame containing the final results
    """
    st.subheader("📊 Final Extracted Results")
    
    # Display summary statistics
    st.write(f"Total articles processed: {len(df)}")
    
    # Create an expander for the full results table
    with st.expander("View Full Results Table", expanded=True):
        # Apply styling to the dataframe
        styled_df = df.style.set_properties(**{
            'background-color': '#f0f2f6',
            'color': 'black',
            'border-color': 'white'
        })
        
        # Display the styled dataframe
        st.dataframe(styled_df, use_container_width=True)
    
    # Add download button for CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv,
        file_name="final_results.csv",
        mime="text/csv"
    )

# These functions are now imported from article_full_text_screening.py
    included_articles = [
        article for article, result in st.session_state.summary_screening_results.items()
        if result['decision'] == 'INCLUDE'
    ]
    
    total_to_screen = len(included_articles)
    total_screened = st.session_state.full_text_screening_done_articles
    accuracy = (st.session_state.full_text_screening_correct_predictions / total_screened * 100) if total_screened > 0 else 0
    
    st.write(f"**Total to Screen:** {total_to_screen}")
    st.write(f"**Total Screened:** {total_screened}")
    st.write(f"**Correct Predictions:** {st.session_state.full_text_screening_correct_predictions}")
    st.write(f"**Accuracy:** {accuracy:.2f}%")

# This function is now imported from article_full_text_screening.py

def simplify_search_query(query: str) -> str:
    """Simplify a complex search query by reducing nesting and grouping similar terms"""
    
    # Extract PubMed filters to preserve them (updated to match new format)
    # Match: AND humans[MeSH Terms] AND english[Language] AND (2013:2024[dp])
    filter_pattern = r'(\s+AND\s+humans\[MeSH Terms\]\s+AND\s+english\[Language\].*?(\d{4}:\d{4}\[dp\]))'
    match = re.search(filter_pattern, query, re.IGNORECASE | re.DOTALL)
    
    # Also try old format for backward compatibility
    if not match:
        filter_pattern_old = r'(\s+AND\s+humans\[Mesh\]\s+AND\s+english\[Language\].*?(\d{4}:\d{4}\[pdat\]))'
        match = re.search(filter_pattern_old, query, re.IGNORECASE | re.DOTALL)
    
    # Remove filters temporarily
    query_without_filters = query
    saved_filters = ""
    
    if match:
        saved_filters = match.group(0)
        query_without_filters = query[:match.start()] + query[match.end():]
    
    # Simplify the query without filters
    simplified = query_without_filters
    
    # Remove excessive parentheses around single terms
    simplified = re.sub(r'\(([^()]+)\)(?!\s*\[)', r'\1', simplified)
    
    # Flatten nested OR groups
    # Convert ((A OR B) OR C) to (A OR B OR C)
    while True:
        before = simplified
        simplified = re.sub(r'\(\(([^()]+)\)\s+OR\s+([^()]+)\)', r'(\1 OR \2)', simplified)
        simplified = re.sub(r'\(([^()]+)\s+OR\s+\(([^()]+)\)\)', r'(\1 OR \2)', simplified)
        if before == simplified:
            break
    
    # Remove duplicate terms (same term with different field tags)
    # This is complex, so we'll just clean up whitespace for now
    
    # Clean up whitespace
    simplified = re.sub(r'\s+', ' ', simplified.strip())
    
    # Add back the filters (ensure proper format)
    if saved_filters:
        # Normalize filter format
        saved_filters = saved_filters.replace('[Mesh]', '[MeSH Terms]')
        saved_filters = saved_filters.replace('[pdat]', '[dp]')
        simplified = simplified + saved_filters
    
    return simplified

if __name__ == "__main__":
    main()