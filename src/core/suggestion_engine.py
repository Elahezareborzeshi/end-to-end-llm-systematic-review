import openai
from openai import OpenAI
import re
import os
import json
import uuid
import time
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Enhanced templates with more variety
RESEARCH_QUESTION_TEMPLATES_ENHANCED = [
    "Conduct a systematic review to identify metabolites and biochemical pathways associated with blood pressure response to antihypertensive drugs using pharmacometabolomics approaches. Specifically, identify key biomarkers predictive of treatment response across different drug classes (diuretics, beta-blockers, ACE inhibitors/ARBs), characterize the underlying metabolic pathways, and assess the potential for personalized antihypertensive therapy.",
    "What metabolites and metabolic pathways are associated with [antihypertensive drug class] response in patients with [condition], and how can these biomarkers be used to predict treatment efficacy?",
    "Conduct a systematic review of pharmacometabolomics studies examining the association between baseline metabolite profiles and [treatment] response in [population].",
    "What are the key metabolomic biomarkers that predict [antihypertensive drug] efficacy and safety outcomes in patients with [blood pressure condition]?",
    "What are the metabolic pathways associated with [antihypertensive drug] response in patients with [blood pressure condition], and how can these pathways be used to predict treatment efficacy?",
    "Conduct a systematic review of pharmacometabolomics studies examining the association between baseline metabolite profiles and [treatment] response in [population].",
    "What are the key metabolomic biomarkers that predict [antihypertensive drug] efficacy and safety outcomes in patients with [blood pressure condition]?",
    "What are the metabolic pathways associated with [antihypertensive drug] response in patients with [blood pressure condition], and how can these pathways be used to predict treatment efficacy?",
    "Conduct a systematic review of pharmacometabolomics studies examining the association between baseline metabolite profiles and [treatment] response in [population].",
    "What are the key metabolomic biomarkers that predict [antihypertensive drug] efficacy and safety outcomes in patients with [blood pressure condition]?"
    
]

DATA_EXTRACTION_TEMPLATES_ENHANCED = [
    """- "First Author"
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
    """,
    
    """- "First Author"
- "Publication Date"
- "Study Design"
- "Sample Size"
- "Population Characteristics (age, gender, ethnicity)"
- "Intervention/Exposure Details"
- "Control/Comparison Group"
- "Primary Outcome"
- "Secondary Outcomes"
- "Effect Size (OR/RR/HR/MD)"
- "95% Confidence Interval"
- "P-Value"
- "Follow-up Duration"
- "Loss to Follow-up Rate"
- "Risk of Bias Assessment\"""",
    
    """- "Study ID"
- "Publication Year"
- "Country/Region"
- "Study Type"
- "Participants (n)"
- "Inclusion Criteria"
- "Exclusion Criteria"
- "Age Range/Mean Age"
- "Gender Distribution (%)"
- "Intervention Description"
- "Dosage/Frequency"
- "Duration of Treatment"
- "Primary Endpoint"
- "Statistical Analysis Method"
- "Main Results"
- "Adverse Events"
- "Study Limitations\"""",
    
    """- "Author and Year"
- "Journal and Impact Factor"
- "Study Design"
- "Setting (hospital/community/clinic)"
- "Population Studied"
- "Sample Size Calculation"
- "Randomization Method"
- "Blinding"
- "Intervention Details"
- "Control Group Details"
- "Outcome Measures"
- "Statistical Tests Used"
- "Effect Estimates"
- "Confidence Intervals"
- "Subgroup Analyses"
- "Quality Assessment Score\"""",
    
    """- "Citation Information"
- "Study Objectives"
- "Study Design and Setting"
- "Participants Demographics"
- "Sample Size and Power"
- "Exposure/Intervention Definition"
- "Outcome Definition and Measurement"
- "Confounding Variables Considered"
- "Statistical Methods"
- "Main Findings"
- "Effect Measures with Precision"
- "Dose-Response Analysis"
- "Sensitivity Analysis Results"
- "Funding Source"
- "Conflicts of Interest\""""
]

class AdaptiveSuggestionEngine:
    def __init__(self):
        self.feedback_file = "data/user_feedback.jsonl"
        self.suggestion_cache = {}
        
    def load_feedback_history(self):
        """Load user feedback history for learning"""
        feedback_data = []
        try:
            if os.path.exists(self.feedback_file):
                with open(self.feedback_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            feedback_data.append(json.loads(line))
        except Exception as e:
            print(f"Error loading feedback history: {e}")
        
        return feedback_data
    
    def analyze_feedback_patterns(self, suggestion_type, feedback_history):
        """Analyze feedback patterns to improve suggestions"""
        if not feedback_history:
            return {}
        
        # Filter feedback for this suggestion type
        relevant_feedback = [f for f in feedback_history if f.get('suggestion_type') == suggestion_type]
        
        if not relevant_feedback:
            return {}
        
        patterns = {
            'preferred_styles': defaultdict(int),
            'avoided_patterns': defaultdict(int),
            'successful_keywords': defaultdict(int),
            'context_preferences': defaultdict(int)
        }
        
        for feedback in relevant_feedback:
            action = feedback.get('action', '')
            suggestion_text = feedback.get('suggestion_text', '')
            
            if action in ['used', 'added']:
                # Analyze successful suggestions
                # Extract key phrases and patterns
                keywords = self.extract_key_patterns(suggestion_text)
                for keyword in keywords:
                    patterns['successful_keywords'][keyword] += 1
                
                # Analyze structure preferences
                if suggestion_text.startswith('Conduct a systematic review'):
                    patterns['preferred_styles']['systematic_review_format'] += 1
                elif '?' in suggestion_text:
                    patterns['preferred_styles']['question_format'] += 1
                
            elif action == 'skipped':
                # Analyze avoided patterns
                keywords = self.extract_key_patterns(suggestion_text)
                for keyword in keywords:
                    patterns['avoided_patterns'][keyword] += 1
        
        return patterns
    
    def extract_key_patterns(self, text):
        """Extract key patterns from text for learning"""
        # Extract meaningful phrases and keywords
        patterns = []
        
        # Medical/research terms
        medical_terms = re.findall(r'\b(?:systematic review|meta-analysis|cohort|randomized|intervention|outcome|association|prevalence|incidence|risk factors|effectiveness|diagnostic accuracy|metabolomics|pharmacometabolomics|biomarkers|metabolites|metabolic pathways|antihypertensive|blood pressure response|drug response|personalized medicine|LC-MS|GC-MS|metabolic profiling|treatment response|baseline metabolites)\b', text.lower())
        patterns.extend(medical_terms)
        
        # Structure patterns
        if 'What is' in text:
            patterns.append('what_is_structure')
        if 'How do' in text:
            patterns.append('how_do_structure')
        if 'Conduct a' in text:
            patterns.append('conduct_structure')
        
        # Length patterns
        if len(text.split()) < 20:
            patterns.append('short_format')
        elif len(text.split()) > 40:
            patterns.append('long_format')
        else:
            patterns.append('medium_format')
        
        return patterns
    
    def generate_adaptive_prompt(self, suggestion_type, current_text, context, patterns):
        """Generate an adaptive prompt based on learned patterns"""
        
        # Handle new suggestion types
        if suggestion_type == 'inclusion_criteria':
            return self.get_inclusion_criteria_prompt(current_text, context, patterns)
        elif suggestion_type == 'exclusion_criteria':
            return self.get_exclusion_criteria_prompt(current_text, context, patterns)
        elif suggestion_type in ['research_question_autocomplete', 'inclusion_criteria_autocomplete', 'exclusion_criteria_autocomplete', 'data_extraction_autocomplete']:
            return self.get_autocomplete_prompt(suggestion_type, current_text, context)
        
        # Original types
        base_prompts = {
            'research_question': self.get_research_question_prompt(current_text, patterns),
            'data_extraction': self.get_data_extraction_prompt(current_text, context, patterns)
        }
        
        return base_prompts.get(suggestion_type, "Generate a helpful suggestion.")
    
    def get_research_question_prompt(self, current_text, patterns):
        """Generate adaptive research question prompt"""
        prompt = f"Based on this partial research question: \"{current_text}\"\n\n"
        
        # Incorporate learned preferences
        if patterns.get('successful_keywords'):
            top_keywords = sorted(patterns['successful_keywords'].items(), key=lambda x: x[1], reverse=True)[:3]
            prompt += f"The user has previously found suggestions with these elements helpful: {', '.join([k for k, v in top_keywords])}\n"
        
        if patterns.get('preferred_styles'):
            top_styles = sorted(patterns['preferred_styles'].items(), key=lambda x: x[1], reverse=True)[:2]
            prompt += f"The user prefers suggestions in this style: {', '.join([k.replace('_', ' ') for k, v in top_styles])}\n"
        
        if patterns.get('avoided_patterns'):
            avoided = list(patterns['avoided_patterns'].keys())[:3]
            prompt += f"Avoid these patterns that the user typically skips: {', '.join(avoided)}\n"
        
        prompt += """
Generate 1 well-structured, complete research question that builds on what the user has written.
Focus on systematic review and meta-analysis questions.
Make it specific, clear, and follow PICO format when possible (Population, Intervention, Comparison, Outcome).
Include specific details about methodology and analysis approach.

IMPORTANT: Return ONLY the research question text.
Do NOT include any introductory phrases like "Here's a suggestion" or "Certainly".
Return only the research question, without numbering or bullets.
        """
        
        return prompt
        
    def get_data_extraction_prompt(self, current_text, research_question, patterns):
        """Generate adaptive data extraction prompt"""
        prompt = f"Research Question: \"{research_question}\"\n"
        prompt += f"Current extraction instructions: \"{current_text}\"\n\n"
        
        # Incorporate learned preferences
        if patterns.get('successful_keywords'):
            top_keywords = sorted(patterns['successful_keywords'].items(), key=lambda x: x[1], reverse=True)[:3]
            prompt += f"The user has found these elements helpful in previous suggestions: {', '.join([k for k, v in top_keywords])}\n"
        
        prompt += """
Based on this research question, generate 1 comprehensive data extraction instruction list.
The list should specify exactly what data fields to extract from research papers.

Focus on fields that are relevant to this specific research question.
Include standard fields like author, year, study design, sample size, etc.
Add specific fields relevant to the research topic and methodology.

IMPORTANT: Return ONLY the bullet-pointed list starting with the first field. 
Do NOT include any introductory text, explanations, or conversational phrases.
Format as a bullet-pointed list with field names in quotes.
Include 12-16 relevant fields for comprehensive data extraction.

Start directly with: - "First Author"
        """
        
        return prompt
    
    def get_inclusion_criteria_prompt(self, current_text, context, patterns):
        """Generate inclusion criteria prompt based on research question"""
        
        # Extract research question from context
        research_question = ""
        if "Research Question:" in context:
            research_question = context.split("Research Question:")[1].split("\n")[0].strip()
        
        prompt = f"""
Research Question: "{research_question}"
Current inclusion criteria: "{current_text}"

Generate specific inclusion criteria for this systematic review that directly relate to the research question.
Make the criteria precise, measurable, and relevant to the study design and population mentioned in the research question.

Focus on:
- Adults (≥18 years of age)
- Studies assessing metabolomics-based biomarkers of blood pressure response to antihypertensive medications
- Human subjects with hypertension or elevated blood pressure
- Studies using validated metabolomics platforms (LC-MS, GC-MS, NMR)
- Clear association reported between metabolites and BP outcomes  
- Specific metabolite identification provided
- Published in peer-reviewed journals (English language)
- Published in peer-reviewed journals (English language)
- Randomized controlled trials, cohort studies, or case-control studies
- Studies reporting quantitative data on primary outcomes
- Published from 2013 to present
- Population characteristics that match the research question
- Study designs appropriate for the research question
- Specific conditions, interventions, or exposures mentioned
- Time periods and publication criteria

Return ONLY a bullet-pointed list starting with "Inclusion Criteria:"
Include 5-8 specific, actionable criteria.
Do NOT include any introductory text or explanations.
"""
        
        return prompt
    
    def get_exclusion_criteria_prompt(self, current_text, context, patterns):
        """Generate exclusion criteria prompt based on research question"""
        
        # Extract research question from context
        research_question = ""
        if "Research Question:" in context:
            research_question = context.split("Research Question:")[1].split("\n")[0].strip()
        
        prompt = f"""
Research Question: "{research_question}"
Current exclusion criteria: "{current_text}"

Generate specific exclusion criteria for this systematic review that complement the research question.
Make the criteria clear about what should be excluded to maintain study quality and relevance.

Focus on:
- Animal or in vitro studies
- Studies without clear metabolite-BP response associations
- Case reports or studies with <10 participants
- Studies lacking specific metabolite identification
- Conference abstracts without adequate quality annotation
- Non-English publications
- Studies focused solely on metabolomics without treatment response data
- Study types that wouldn't answer the research question
- Populations that don't match the target group
- Publications that lack sufficient quality or data
- Conflicting study designs or methodologies

Return ONLY a bullet-pointed list starting with "Exclusion Criteria:"
Include 5-8 specific, actionable criteria.
Do NOT include any introductory text or explanations.
"""
        
        return prompt
    
    def get_autocomplete_prompt(self, suggestion_type, current_text, context):
        """Generate auto-complete style suggestions (shorter, completion-focused)"""
        
        base_type = suggestion_type.replace('_autocomplete', '')
        
        prompt = f"""
Current text: "{current_text}"
Context: "{context}"

Complete this {base_type.replace('_', ' ')} with a short, natural continuation (10-30 words).
Focus on completing the current thought or adding the next logical element.

Return ONLY the completion text, no explanations or formatting.
Make it feel like natural text completion, not a full suggestion.
"""
        
        return prompt
    
# Global instance
adaptive_engine = AdaptiveSuggestionEngine()

def generate_adaptive_suggestion(suggestion_type, current_text, context="", feedback_history=None):
    """Generate a single adaptive suggestion based on user feedback history"""
    
    # Load full feedback history if not provided
    if feedback_history is None:
        feedback_history = adaptive_engine.load_feedback_history()
    
    # Analyze patterns from feedback
    patterns = adaptive_engine.analyze_feedback_patterns(suggestion_type, feedback_history)
    
    # Generate suggestion based on patterns
    if len(current_text.strip()) < 10 and not patterns and not suggestion_type.endswith('_autocomplete'):
        # Return template for new users (except for autocomplete)
        return get_template_suggestion(suggestion_type)
    
    # Generate AI-powered adaptive suggestion
    try:
        prompt = adaptive_engine.generate_adaptive_prompt(suggestion_type, current_text, context, patterns)
        
        # Adjust max_tokens based on suggestion type
        max_tokens = 400
        if suggestion_type.endswith('_autocomplete'):
            max_tokens = 50  # Shorter for autocomplete
        elif suggestion_type in ['inclusion_criteria', 'exclusion_criteria']:
            max_tokens = 300
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7 if not suggestion_type.endswith('_autocomplete') else 0.5
        )
        
        suggestion_text = response.choices[0].message.content.strip()
        
        # Clean AI responses
        suggestion_text = clean_ai_response(suggestion_text)
        
        return {
            'id': str(uuid.uuid4()),
            'text': suggestion_text,
            'type': 'adaptive_ai',
            'context': context,
            'patterns_used': patterns,
            'timestamp': time.time()
        }
        
    except Exception as e:
        print(f"Error generating adaptive suggestion: {e}")
        # Fallback to template
        return get_template_suggestion(suggestion_type)

def get_template_suggestion(suggestion_type):
    """Get a template suggestion as fallback"""
    if suggestion_type == 'research_question':
        template = RESEARCH_QUESTION_TEMPLATES_ENHANCED[0]
        return {
            'id': str(uuid.uuid4()),
            'text': template,
            'type': 'template',
            'context': '',
            'timestamp': time.time()
        }
    elif suggestion_type == 'data_extraction':
        template = DATA_EXTRACTION_TEMPLATES_ENHANCED[0]
        return {
            'id': str(uuid.uuid4()),
            'text': template,
            'type': 'template',
            'context': '',
            'timestamp': time.time()
        }
    elif suggestion_type == 'inclusion_criteria':
        template = """Inclusion Criteria:
- Adults (≥18 years of age)
- Published in peer-reviewed journals (English language)
- Randomized controlled trials, cohort studies, or case-control studies
- Studies reporting quantitative data on primary outcomes
- Minimum sample size of 50 participants
- Published from 2013 to present"""
        return {
            'id': str(uuid.uuid4()),
            'text': template,
            'type': 'template',
            'context': '',
            'timestamp': time.time()
        }
    elif suggestion_type == 'exclusion_criteria':
        template = """Exclusion Criteria:
- Pediatric populations (<18 years)
- Animal studies and in vitro studies
- Case reports and case series with <10 participants
- Conference abstracts without full peer review
- Non-English publications
- Studies with insufficient data for analysis"""
        return {
            'id': str(uuid.uuid4()),
            'text': template,
            'type': 'template',
            'context': '',
            'timestamp': time.time()
        }
    
    return None

def get_research_question_suggestions(current_text="", max_suggestions=1):
    """Legacy function - now redirects to adaptive suggestion"""
    suggestion = generate_adaptive_suggestion('research_question', current_text)
    return [suggestion] if suggestion else []

def get_data_extraction_suggestions(current_text="", research_question="", max_suggestions=1):
    """Legacy function - now redirects to adaptive suggestion"""
    suggestion = generate_adaptive_suggestion('data_extraction', current_text, research_question)
    return [suggestion] if suggestion else []

def get_suggestion_analytics():
    """Get analytics about suggestion usage for debugging"""
    feedback_history = adaptive_engine.load_feedback_history()
    
    analytics = {
        'total_feedback_entries': len(feedback_history),
        'suggestion_types': defaultdict(int),
        'action_types': defaultdict(int),
        'recent_activity': []
    }
    
    for feedback in feedback_history:
        analytics['suggestion_types'][feedback.get('suggestion_type', 'unknown')] += 1
        analytics['action_types'][feedback.get('action', 'unknown')] += 1
    
    # Get recent activity (last 10 entries)
    analytics['recent_activity'] = feedback_history[-10:] if len(feedback_history) > 10 else feedback_history
    
    return analytics

# Enhanced inclusion/exclusion suggestions with more variety
INCLUSION_EXCLUSION_TEMPLATES_ENHANCED = [
    {
        "type": "inclusion",
        "text": """Inclusion Criteria:
- Adults (≥18 years of age)
- Diagnosed with [specific condition]
- Published in peer-reviewed journals
- English language publications
- [Study design: randomized controlled trials, cohort studies, case-control studies]
- Minimum follow-up period of [time period]
- Studies reporting [specific outcome measures]
- Published between [start year] and [end year]"""
    },
    {
        "type": "exclusion", 
        "text": """Exclusion Criteria:
- Pediatric populations (<18 years)
- Animal studies and in vitro studies
- Case reports and case series (n<10)
- Conference abstracts without full-text availability
- Non-English publications
- Studies with insufficient data for analysis
- Duplicate publications or overlapping populations
- Studies with high risk of bias (score <X on quality assessment)"""
    },
    {
        "type": "combined",
        "text": """Inclusion Criteria:
- Adults (≥18 years) with confirmed diagnosis of [condition]
- Studies investigating [specific intervention/exposure]
- Randomized controlled trials, cohort studies, or case-control studies
- Minimum sample size of [number] participants
- English language publications in peer-reviewed journals
- Studies reporting quantitative data on [primary outcome]
- Published from [start year] to present

Exclusion Criteria:
- Pediatric studies (participants <18 years)
- Animal studies, in vitro studies, and cell culture studies
- Case reports, case series, editorials, and reviews
- Conference abstracts without full peer review
- Studies with unclear methodology or inadequate reporting
- Duplicate publications or overlapping study populations
- Studies not reporting sufficient data for meta-analysis"""
    }
]

def get_inclusion_exclusion_suggestions(current_text="", research_question="", max_suggestions=3):
    """Generate enhanced inclusion/exclusion criteria suggestions"""
    suggestions = []
    
    for i, template in enumerate(INCLUSION_EXCLUSION_TEMPLATES_ENHANCED):
        suggestions.append({
            'id': str(uuid.uuid4()),
            'text': template['text'],
            'type': 'template',
            'description': f'{template["type"].title()} criteria template (Version {i+1})',
            'timestamp': time.time()
        })
    
    return suggestions[:max_suggestions]

# Legacy functions to maintain compatibility
def extract_keywords_from_text(text):
    """Extract key medical/research terms from text for suggestion context."""
    medical_terms = re.findall(r'\b(?:hypertension|diabetes|cancer|cardiovascular|mortality|morbidity|intervention|treatment|therapy|diagnosis|prevalence|incidence|risk|factors|outcome|effect|association|correlation|meta-analysis|systematic review|randomized|cohort|case-control)\b', text.lower())
    return list(set(medical_terms))

def generate_ai_research_suggestions(current_text):
    """Generate AI-powered research question suggestions."""
    suggestion = generate_adaptive_suggestion('research_question', current_text)
    return [suggestion['text']] if suggestion else []

def generate_ai_extraction_suggestions(current_text, research_question):
    """Generate AI-powered data extraction suggestions."""
    suggestion = generate_adaptive_suggestion('data_extraction', current_text, research_question)
    return [suggestion['text']] if suggestion else []

# ADD these new templates for criteria suggestions
INCLUSION_CRITERIA_TEMPLATES = [
    """Inclusion Criteria:
- Studies assessing metabolomics-based biomarkers of blood pressure response to antihypertensive medications
- Human subjects with hypertension or elevated blood pressure
- Studies using validated metabolomics platforms (LC-MS, GC-MS, NMR)
- Clear association reported between metabolites and BP outcomes  
- Specific metabolite identification provided
- Published in peer-reviewed journals (English language)
- Published from 2013 onwards"""
    """Inclusion Criteria:
- Adults (≥18 years of age)
- Confirmed diagnosis of [condition] based on [diagnostic criteria]
- Published in peer-reviewed journals (English language)
- [Study designs]: randomized controlled trials, cohort studies, case-control studies
- Studies reporting quantitative data on [primary outcome]
- Minimum sample size of [number] participants
- Published from [start year] to [end year]
- Minimum follow-up period of [time period]""",
    
    """Inclusion Criteria:
- Human studies involving [target population]
- Studies investigating [intervention/exposure] vs [control/comparison]
- Full-text articles available for review
- Studies conducted in [geographic regions/healthcare settings]
- Studies using validated outcome measures
- Clear methodology and adequate statistical analysis
- Studies following relevant reporting guidelines (CONSORT/STROBE)""",
]

EXCLUSION_CRITERIA_TEMPLATES = [
"""Exclusion Criteria:
- Animal or in vitro studies
- Studies without clear metabolite-BP response associations
- Case reports or studies with <10 participants
- Studies lacking specific metabolite identification
- Conference abstracts without adequate quality annotation
- Non-English publications
- Studies focused solely on metabolomics without treatment response data"""

    """Exclusion Criteria:
- Pediatric populations (<18 years)
- Animal studies, in vitro studies, and cell culture research
- Case reports and case series with <10 participants
- Conference abstracts without full peer review
- Non-English publications
- Studies with insufficient data for analysis
- Duplicate publications or overlapping study populations
- Studies with high risk of bias (quality score <[threshold])""",
    
    """Exclusion Criteria:
- Studies without appropriate control groups
- Cross-sectional studies (unless specifically relevant)
- Studies with unclear methodology or inadequate reporting
- Review articles, editorials, and opinion pieces
- Studies with significant conflicts of interest
- Pilot studies with preliminary results only
- Studies not reporting essential outcome data""",
]

# ADD this function to handle criteria suggestions
def generate_criteria_suggestion(criteria_type, current_text, research_question):
    """Generate suggestions for inclusion/exclusion criteria"""
    try:
        if criteria_type == 'inclusion_criteria':
            templates = INCLUSION_CRITERIA_TEMPLATES
            prompt_type = "inclusion"
        else:
            templates = EXCLUSION_CRITERIA_TEMPLATES  
            prompt_type = "exclusion"
        
        # If no text, return template
        if len(current_text.strip()) < 10:
            return {
                'id': str(uuid.uuid4()),
                'text': templates[0],
                'type': 'template',
                'context': research_question,
                'timestamp': time.time()
            }
        
        # Generate AI-powered suggestion
        prompt = f"""
        Research Question: "{research_question}"
        Current {prompt_type} criteria: "{current_text}"
        
        Generate comprehensive {prompt_type} criteria for this systematic review.
        Make them specific to the research question and follow systematic review standards.
        
        Format as a bullet-pointed list starting with "{prompt_type.title()} Criteria:"
        Include 6-8 relevant criteria that are specific and actionable.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.5
        )
        
        return {
            'id': str(uuid.uuid4()),
            'text': response.choices[0].message.content.strip(),
            'type': 'adaptive_ai',
            'context': research_question,
            'timestamp': time.time()
        }
        
    except Exception as e:
        print(f"Error generating criteria suggestion: {e}")
        # Fallback to template
        return {
            'id': str(uuid.uuid4()),
            'text': templates[0],
            'type': 'template',
            'context': research_question,
            'timestamp': time.time()
        }
    
def clean_ai_response(text):
    """Remove common AI introductory phrases from responses"""
    
    # Common introductory phrases to remove
    intro_patterns = [
        r"^Certainly!?\s*",
        r"^Here's\s+a\s+comprehensive\s+.*?:\s*",
        r"^Here's\s+a\s+.*?:\s*", 
        r"^Based\s+on\s+.*?:\s*",
        r"^I'll\s+.*?:\s*",
        r"^Here\s+is\s+.*?:\s*",
        r"^.*?tailored\s+to\s+.*?:\s*",
        r"^.*?research\s+question\s+.*?:\s*"
    ]
    
    # Remove introductory patterns
    for pattern in intro_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Clean up any remaining leading/trailing whitespace
    text = text.strip()
    
    # Remove empty lines at the beginning
    lines = text.split('\n')
    while lines and not lines[0].strip():
        lines.pop(0)
    
    return '\n'.join(lines)