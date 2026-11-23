import json
import os
import time
import streamlit as st
import pandas as pd
from langchain_openai import ChatOpenAI
from article_data_extractor import load_article_from_file
from article_full_text_downloader import download_single_article_full_text
from rag_screening import rag_based_full_text_screening, add_rag_example

# def filter_articles_based_on_full_text(directory_path, inclusion_criteria, exclusion_criteria=None):
#     llm = ChatOpenAI(temperature=0.02, model_name="gpt-4o")

#     for filename in os.listdir(directory_path):
#         if filename.endswith('_source.json'):
#             file_path = os.path.join(directory_path, filename)
#             base_filename = file_path.split("_source")[0]
#             full_text_path = os.path.join(directory_path, f"{base_filename}_full.txt")
            
#             if not os.path.exists(full_text_path):
#                 print(f"Full text not found for {filename}. Skipping...")
#                 continue

#             with open(file_path, 'r') as json_file, open(full_text_path, 'r') as full_text_file:
#                 try:
#                     data = json.load(json_file)
#                     article_title = data['MedlineCitation']['Article']['ArticleTitle']
#                     full_text = full_text_file.read()

#                     prompt = f"""
#                     Given the following article title and full text, determine if it meets the inclusion criteria and does not meet the exclusion criteria (if provided).

#                     Title: ###
#                     {article_title}
#                     ###

#                     Full Text: ###
#                     {full_text}
#                     ###

#                     INCLUSION CRITERIA: ###
#                     {inclusion_criteria}
#                     ###

#                     {"EXCLUSION CRITERIA: ###" if exclusion_criteria else ""}
#                     {exclusion_criteria if exclusion_criteria else ""}
#                     {"###" if exclusion_criteria else ""}

#                     Please respond with 'INCLUDE' or 'EXCLUDE' followed by a colon and a brief explanation of why the article was included or excluded. For example:
#                     "INCLUDE: This article meets all inclusion criteria and does not violate any exclusion criteria. It specifically addresses..."
#                     or
#                     "EXCLUDE: While the article discusses hypertension, it does not focus on risk factors as required by the inclusion criteria. Instead, it primarily covers..."

#                     Ensure your response starts with either 'INCLUDE:' or 'EXCLUDE:' followed by the explanation.
#                     """

#                     print(f" - 🔍 Screening full text: {article_title}")
#                     response = llm.invoke(prompt)
#                     time.sleep(10)
#                     print(f" - 💬 Response: {response.content}")
                    
#                     decision, reason = response.content.split(':', 1)
#                     reason = reason.strip()
                    
#                     reason_file_path = os.path.join(directory_path, f"{os.path.splitext(filename)[0]}_reason.txt")
#                     with open(reason_file_path, 'w') as reason_file:
#                         reason_file.write(f"{decision}: {reason}")
                    
#                     if decision.strip().upper() == 'INCLUDE':
#                         print(f" - ✅ Included: {filename}")
#                     else:
#                         print(f" - ❌ Excluded: {filename}")
#                         os.remove(file_path)
#                         os.remove(full_text_path)

#                 except json.JSONDecodeError:
#                     print(f"Error: Unable to parse JSON in {file_path}")
#                 except KeyError as e:
#                     print(f"Error: Missing key {e} in {file_path}")
#                 except Exception as e:
#                     print(f"Unexpected error processing {filename}: {str(e)}")

#     print("Full text screening completed.")
def download_all_full_texts():
    """Download full texts for all included articles from title/abstract screening"""
    try:
        st.subheader("📄 Downloading Full Texts...")
        
        # Get all included articles from the summary screening
        included_articles = [
            article for article, result in st.session_state.summary_screening_results.items()
            if result['decision'] == 'INCLUDE'
        ]
        
        total_articles = len(included_articles)
        st.write(f"📊 **Found {total_articles} articles that passed title/abstract screening**")
        
        if total_articles == 0:
            st.warning("No articles passed title/abstract screening. Cannot download full texts.")
            return
        
        downloaded_articles = 0
        failed_downloads = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for article_index in included_articles:
            try:
                article_path = st.session_state.downloaded_articles[article_index]
                article_info = load_article_from_file(article_path)
                status_text.text(f"Downloading full text {downloaded_articles + 1}/{total_articles}: {article_info['Title'][:50]}...")
                
                # Download full text
                download_single_article_full_text(article_path)
                
                downloaded_articles += 1
                st.write(f"✅ Downloaded: {article_info['Title'][:80]}...")
                
            except Exception as e:
                failed_downloads.append(f"Article {article_index}: {str(e)}")
                st.error(f"❌ Failed to download: {article_info.get('Title', 'Unknown title')[:50]}... Error: {str(e)}")
            
            progress_bar.progress(downloaded_articles / total_articles)
        
        # Summary
        status_text.text("✅ Full text download process completed!")
        st.success(f"Successfully downloaded {downloaded_articles} out of {total_articles} full texts")
        
        if failed_downloads:
            st.warning(f"Failed to download {len(failed_downloads)} articles:")
            for failure in failed_downloads:
                st.text(f"  • {failure}")
        
        st.session_state.full_texts_downloaded = True
        time.sleep(2)  # Show completion message
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error in download_all_full_texts: {str(e)}")
        import traceback
        st.text(traceback.format_exc())

def display_full_text_article_dataframe():
    """Display dataframe for full text screening with current article highlighted"""
    # Get all included articles from summary screening
    included_articles = [
        article for article, result in st.session_state.summary_screening_results.items()
        if result['decision'] == 'INCLUDE'
    ]
    
    articles_data = []
    for article_index in included_articles:
        article_path = st.session_state.downloaded_articles[article_index]
        article_info = load_article_from_file(article_path)
        article_info['Original_Index'] = article_index  # Keep track of original index
        articles_data.append(article_info)
    
    if not articles_data:
        st.write("No articles passed title/abstract screening.")
        return
        
    df = pd.DataFrame(articles_data)
    df['Screened'] = df['Original_Index'].map(lambda i: '✅' if i in st.session_state.full_text_screening_results else '⏳')
    df['Decision'] = df['Original_Index'].map(lambda i: st.session_state.full_text_screening_results.get(i, {}).get('decision', ''))
    df['Automated'] = df['Original_Index'].map(lambda i: st.session_state.full_text_screening_results.get(i, {}).get('automated_flag', ''))
    
    # Keep Original_Index for highlighting, but move it to the end so it's not prominently displayed
    display_columns = ['Screened', 'Decision', 'Automated', 'Title', 'Abstract', 'Authors', 'Publication Date', 'Journal', 'E-Location']
    available_columns = [col for col in display_columns if col in df.columns]
    df_display = df[available_columns + ['Original_Index']]
    
    # Simplified: just show the dataframe without complex highlighting for now
    # The highlighting was causing the KeyError
    try:
        # Display without Original_Index column
        df_for_display = df_display[available_columns]
        st.dataframe(df_for_display)
        
        # Show current article info separately
        current_original_index = get_current_full_text_article_index()
        if current_original_index is not None:
            st.info(f"📍 Currently screening article with index: {current_original_index}")
            
    except Exception as e:
        st.error(f"Error displaying dataframe: {e}")
        # Ultimate fallback: show basic dataframe
        st.write("**Articles for full text screening:**")
        for i, article_data in enumerate(articles_data):
            status = '✅' if article_data['Original_Index'] in st.session_state.full_text_screening_results else '⏳'
            st.write(f"{status} {article_data.get('Title', 'No title')[:80]}...")

def get_current_full_text_article_index():
    """Get the original index of the current full text article being screened"""
    included_articles = [
        article for article, result in st.session_state.summary_screening_results.items()
        if result['decision'] == 'INCLUDE'
    ]
    
    if st.session_state.full_text_screening_current_article_index < len(included_articles):
        return included_articles[st.session_state.full_text_screening_current_article_index]
    return None

def display_current_full_text_article():
    """Display current article for full text screening with summary"""
    included_articles = [
        article for article, result in st.session_state.summary_screening_results.items()
        if result['decision'] == 'INCLUDE'
    ]
    
    if st.session_state.full_text_screening_current_article_index < len(included_articles):
        article_index = included_articles[st.session_state.full_text_screening_current_article_index]
        article_path = st.session_state.downloaded_articles[article_index]
        
        article = load_article_from_file(article_path)
        
        # Show full text summary based on data extraction instructions
        full_text_summary = generate_full_text_summary(article_path)
        if full_text_summary:
            with st.expander("📋 Full Text Summary (Based on Data Extraction Features)", expanded=True):
                st.write(full_text_summary)
        
        # Add manual full text exploration section
        with st.expander("🔍 Manual Full Text Exploration", expanded=False):
            display_manual_full_text_exploration(article_path)
        
        # Get model decision
        decision, reason = rag_based_full_text_screening(article_path)
        st.write(f"**Model Decision:** {decision}")
        
        # Add a text area for the reason, pre-filled with the model's reason
        reason = st.text_area("Reason for inclusion/exclusion:", value=reason, key="full_text_reason_text_area")
        
        # Store the model's decision temporarily
        st.session_state.full_text_screening_results[article_index] = {
            'decision': decision,
            'reason': reason,
            'automated_flag': st.session_state.screening_mode == 'auto'
        }

def display_manual_full_text_exploration(article_path):
    """Display manual full text exploration tools"""
    try:
        # Check if full text file exists
        parts = os.path.splitext(article_path)
        base_filename = parts[0].split("_source")[0]
        directory_path = os.path.dirname(article_path)
        full_text_path = os.path.join(directory_path, f"{os.path.basename(base_filename)}_full.txt")
        
        if not os.path.exists(full_text_path):
            st.error("❌ Full text not available for manual exploration")
            return
        
        # Load full text
        with open(full_text_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
        
        if not full_text.strip():
            st.error("❌ Full text file is empty")
            return
        
        # Search functionality
        st.subheader("🔍 Search in Full Text")
        search_term = st.text_input("Enter search term:", key="full_text_search_term")
        
        if search_term:
            # Case-insensitive search
            search_results = []
            lines = full_text.split('\n')
            for i, line in enumerate(lines):
                if search_term.lower() in line.lower():
                    # Get context (previous and next lines)
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    context = '\n'.join(lines[start:end])
                    search_results.append({
                        'line_number': i + 1,
                        'context': context,
                        'highlighted_line': line
                    })
            
            if search_results:
                st.write(f"Found {len(search_results)} occurrences:")
                
                # Use columns and containers instead of expanders
                for i, result in enumerate(search_results):
                    with st.container():
                        st.markdown(f"**Line {result['line_number']}:** {result['highlighted_line'][:100]}...")
                        
                        # Use a checkbox to toggle context display
                        show_context = st.checkbox(f"Show context for line {result['line_number']}", key=f"show_context_{i}")
                        
                        if show_context:
                            # Highlight the search term in the context
                            highlighted_context = result['context'].replace(
                                search_term, 
                                f"**{search_term}**"
                            )
                            st.text_area(
                                f"Context around line {result['line_number']}:",
                                value=highlighted_context,
                                height=150,
                                key=f"context_{i}"
                            )
                        st.markdown("---")
            else:
                st.write("No occurrences found.")
        
        # Section navigation
        st.subheader("📖 Navigate by Sections")
        
        # Common section headers to look for
        section_headers = [
            'Abstract', 'Introduction', 'Methods', 'Methodology', 'Results', 
            'Discussion', 'Conclusion', 'References', 'Background', 'Objective',
            'Study Design', 'Participants', 'Data Analysis', 'Findings'
        ]
        
        found_sections = []
        lines = full_text.split('\n')
        for i, line in enumerate(lines):
            line_clean = line.strip()
            for header in section_headers:
                if header.lower() in line_clean.lower() and len(line_clean) < 100:
                    found_sections.append({
                        'header': header,
                        'line_number': i + 1,
                        'content': line_clean
                    })
                    break
        
        if found_sections:
            st.write("**Available sections:**")
            for section in found_sections:
                if st.button(f" {section['header']} (Line {section['line_number']})", key=f"section_{section['line_number']}"):
                    # Show section content
                    start_line = section['line_number'] - 1
                    end_line = min(len(lines), start_line + 50)  # Show next 50 lines
                    section_content = '\n'.join(lines[start_line:end_line])
                    
                    st.text_area(
                        f"Content starting from {section['header']}:",
                        value=section_content,
                        height=300,
                        key=f"section_content_{section['line_number']}"
                    )
        else:
            st.write("No standard sections found. You can search for specific terms above.")
        
        # Download full text functionality
        st.subheader("📄 Download Full Text")
        
        # Get article title for filename
        article = load_article_from_file(article_path)
        article_title = article.get('Title', 'Unknown Title')
        
        # Clean title for filename (remove special characters)
        import re
        clean_title = re.sub(r'[^\w\s-]', '', article_title).strip()
        clean_title = re.sub(r'[-\s]+', '_', clean_title)
        filename = f"{clean_title[:50]}_full_text.pdf"
        
        # Convert text to PDF
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            import io
            
            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Create custom style for the content
            content_style = ParagraphStyle(
                'CustomContent',
                parent=styles['Normal'],
                fontSize=10,
                leading=12,
                leftIndent=0,
                rightIndent=0,
                spaceAfter=6
            )
            
            # Build PDF content
            story = []
            
            # Add title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=14,
                leading=16,
                spaceAfter=12
            )
            story.append(Paragraph(article_title, title_style))
            story.append(Spacer(1, 12))
            
            # Add full text content
            # Split text into paragraphs and add to PDF
            paragraphs = full_text.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    # Clean up the paragraph text
                    para_clean = para.strip().replace('\n', ' ')
                    story.append(Paragraph(para_clean, content_style))
                    story.append(Spacer(1, 6))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            pdf_data = buffer.getvalue()
            buffer.close()
            
            # Create download button
            st.download_button(
                label="📄 Download Full Text Article (PDF)",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                help="Download the complete full text of this article as a PDF for offline reading"
            )
            
        except ImportError:
            st.error("❌ PDF generation requires 'reportlab' package. Please install it with: pip install reportlab")
            # Fallback to text download
            st.download_button(
                label="📄 Download Full Text Article (TXT)",
                data=full_text,
                file_name=filename.replace('.pdf', '.txt'),
                mime="text/plain",
                help="Download the complete full text of this article as a text file"
            )
        except Exception as e:
            st.error(f"❌ Error generating PDF: {str(e)}")
            # Fallback to text download
            st.download_button(
                label="📄 Download Full Text Article (TXT)",
                data=full_text,
                file_name=filename.replace('.pdf', '.txt'),
                mime="text/plain",
                help="Download the complete full text of this article as a text file"
            )
        
        # Show file info
        st.info(f"📊 **File size:** {len(full_text):,} characters ({len(full_text.split())} words)")
        
    except Exception as e:
        st.error(f"❌ Error in manual exploration: {str(e)}")

def reset_full_text_exploration():
    """Reset full text exploration state when moving to next article"""
    # No longer needed since we removed pagination
    pass

def generate_full_text_summary(article_path):
    """Generate a summary of the full text based on data extraction instructions and research criteria"""
    try:
        # Check if full text file exists
        parts = os.path.splitext(article_path)
        base_filename = parts[0].split("_source")[0]
        directory_path = os.path.dirname(article_path)
        full_text_path = os.path.join(directory_path, f"{os.path.basename(base_filename)}_full.txt")
        
        if not os.path.exists(full_text_path):
            return "❌ Full text not available for summary"
        
        # Load full text
        with open(full_text_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
        
        if not full_text.strip():
            return "❌ Full text file is empty"
        
        # Truncate if too long
        max_chars = 50000
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "\n\n[TEXT TRUNCATED FOR ANALYSIS]"
        
        # Load article info
        article = load_article_from_file(article_path)
        
        # Create summary prompt
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(temperature=0.1, model_name="gpt-4o")
        
        summary_prompt = f"""
        Based on the following research context and full article text, provide a structured summary focusing on the data extraction features and research relevance.

        RESEARCH QUESTION: {st.session_state.research_question}
        
        DATA EXTRACTION FEATURES: 
        {st.session_state.final_result_instructions}
        
        INCLUSION CRITERIA: {st.session_state.get('inclusion_criteria', 'Not specified')}
        
        EXCLUSION CRITERIA: {st.session_state.get('exclusion_criteria', 'Not specified')}

        ARTICLE TITLE: {article['Title']}
        
        FULL TEXT: {full_text}

        Please provide a structured summary covering:
        1. **Research Relevance**: How well does this article address the research question?
        2. **Study Design & Methods**: What type of study is this and what methods were used?
        3. **Key Findings**: What are the main results related to our research question?
        4. **Data Extraction Potential**: Based on the data extraction features list, what relevant data can be extracted from this article?
        5. **Inclusion/Exclusion Assessment**: How well does this article meet our selection criteria?

        Keep the summary concise but informative (max 500 words).
        """
        
        response = llm.invoke(summary_prompt)
        return response.content
        
    except Exception as e:
        return f"❌ Error generating summary: {str(e)}"

def display_full_text_screening_stats():
    """Display statistics for full text screening"""
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

def handle_full_text_user_decision(decision):
    """Handle user decision for full text screening"""
    included_articles = [
        article for article, result in st.session_state.summary_screening_results.items()
        if result['decision'] == 'INCLUDE'
    ]
    
    current_index = st.session_state.full_text_screening_current_article_index
    article_index = included_articles[current_index]
    
    current_screening_result = st.session_state.full_text_screening_results.get(article_index, {})
    
    # Get the reason from the text area
    reason = st.session_state.full_text_reason_text_area
    
    user_screening_result = {
        'decision': decision,
        'reason': reason,
        'automated_flag': False
    }
    
    st.session_state.full_text_screening_done_articles += 1
    if current_screening_result.get('decision', '') == decision:
        st.session_state.full_text_screening_correct_predictions += 1
    
    st.session_state.full_text_screening_results[article_index] = user_screening_result
    
    # Add RAG example for learning
    article_path = st.session_state.downloaded_articles[article_index]
    add_rag_example(article_path, decision, reason)
    
    # Reset full text exploration state for next article
    reset_full_text_exploration()
    
    st.session_state.full_text_screening_current_article_index += 1