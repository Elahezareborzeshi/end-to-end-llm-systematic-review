import time

from openai import OpenAI
from config import config

client = OpenAI(api_key=config.OPENAI_API_KEY)

def extract_keywords(text, max_keywords=10):
    """Extract NLP-based keywords from the given text."""
    # kw_extractor = yake.KeywordExtractor(top=max_keywords, dedupLim=0.9, n=3, lan="en", features=None)
    # nlp_keywords = kw_extractor.extract_keywords(text)

    # print("🧩 Extracted NLP-based keywords:")
    # for keyword in [kw for kw, _ in nlp_keywords]:
    #     print(f"- {keyword}")
    # print()

    temperatures = [0.01] # , 0.2, 0.5, 1.05, 1.4
    llm_keywords_sets = []
    for temp in temperatures:
        print(f" -> Extracting keywords with temperature {temp}")
        llm_keywords = extract_keywords_via_llm(text, temperature=temp)
        llm_keywords_sets.append(set(llm_keywords))

    lowercase_keywords = sorted(set(keyword.lower().strip() for keywords_set in llm_keywords_sets for keyword in keywords_set))

    synonyms_keywords = []
    # for keyword in lowercase_keywords:
    #     print(f" -> Generating synonyms for '{keyword}'")
    #     synonyms = generate_synonyms(keyword, temperature=0.01)
    #     synonyms_keywords.extend(synonyms)

    print("🧩 Extracted LLM-based keywords:")
    for keyword in lowercase_keywords:
        print(f"- {keyword.strip()}")
    print()

    print("🧩 Extracted LLM-based synonyms:")
    for keyword in synonyms_keywords:
        print(f"- {keyword.strip()}")
    print()

    all_keywords = lowercase_keywords + synonyms_keywords
    deduplicated_keywords = list(set(all_keywords))

    print("🧩 Extracted keywords:")
    for keyword in deduplicated_keywords:
        print(f"- {keyword.strip()}")
    print()

    from keyword_evaluator import evaluate_keywords_and_generate_report
    evaluate_keywords_and_generate_report(deduplicated_keywords)
    
    return deduplicated_keywords

def extract_keywords_via_llm(text, temperature):
    # Ensure your API key is configured properly in your environment or securely in your script
    # gpt_assistant_prompt = f"""As a systematic review assistant, your role is generate a semantically meaningful search 
    #                  to extract the main keywords from this text: {text} and 
    #                 return list of all relevant keywords, synonyms, and related terms that describe the main keywords. 
    #                 For example if the text is 'What are the modifiable and non-modifiable risk factors for HTNE and HTNU in adults 
    #                 with hypertension' the keywords should be [	Prevalence,Risk Factors, Hypertension ,Ethiopia,
    #                 determinants of hypertension in Ethiopia,associated factors of hypertension in Ethiopia,
    #                 risk factors of hypertension in Ethiopia,Magnitudes] """

    # semantically meaningful 

    gpt_assistant_prompt = f"""
    As a systematic scientific health academic review assistant specializing in pharmacometabolomics and precision medicine, your role is to extract search terms from a text that user provides.
    You must make sure to:
    - Include metabolomics-specific terms (metabolites, biomarkers, metabolic pathways, pharmacometabolomics)
    - Include drug response terminology (treatment response, drug efficacy, personalized medicine)
    - Extract CORE medical concepts (e.g., "blood pressure" not "blood pressure response")
    - Include metabolomics-specific terms (metabolites, biomarkers, metabolic pathways, pharmacometabolomics)
    - Include drug response terminology (treatment response, drug efficacy, personalized medicine)
    - Keep terms broad and foundational rather than overly specific
    - Prefer base concepts over compound phrases when possible
    - Suggest scientific and medical synonyms
    - Do not return any other text or explanation.
    - Suggest all known scientific and exact medical synonyms for all keywords, avoid purely dictionary synonyms.
    - Keep terms broad without being too generic
    - Suggest scientific and medical synonyms
    - Do not return any other text or explanation.
    - Suggest all known scientific and exact medical synonyms for all keywords, avoid purely dictionary synonyms.
    - Avoid explaning the result or the process, just print the keywords.
    - You must return only the list of relevant keywords separated by comma.
    - User will provide you directly with their prompt.
    - Avoid too generic and broad keywords some examples include 'epidemiology', 'rate', 'etiology', 'frequency'
    """
    # - Avoid trying to answer user's question, we need to extract keywords only for the purpose of good search coverage.
    # - Return list of all relevant keywords, synonyms, and related terms without any description separated by comma.
    # - Keep the terms broad and generic without expanding the semantics that makes the term too specific like an answer.
    #   For example do not suggest 'cardiovascular' for 'risk factor'.
    messages = [
        {"role": "assistant", "content": gpt_assistant_prompt},
        {"role": "user", "content": text}
    ]

    # semantically meaningful 
    #prompt_text = f"""As a systematic review assistant, your role is generate a semantic search to extract the main keywords from this text: {keywords_text} and return list of synonyms of the main keywords""",
    #prompt_text = f"""As a systematic review assistant, your role is to generate the semantic keywords from this text: {keywords_text} and return list the main keywords""",
    #prompt_text = f"""As a systematic review assistant, your role is to extract the main keywords from this text: {keywords_text} and return list of synonyms of the main keywords""",

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,                     # The structured text sent to the model, designed to guide the model to respond with both keywords and their synonyms.
        temperature=temperature,                        # Controls the randomness of the output. A lower temperature results in more deterministic outputs.
        max_tokens=256,                         # Maximum length of the model's response.
        frequency_penalty=0.0,                  # Reduces the model's tendency to repeat itself.
    )
    time.sleep(10)
    response_text = response.choices[0].message.content
    separated_keywords = response_text.split(",")
    return separated_keywords


def generate_synonyms(keyword, temperature):
    gpt_assistant_prompt = f"""
    As a systematic scientific health academic review assistant, your role is to help find exact medical synonyms for a given keyword.
    You must make sure to:
    - Return only the list of synonyms separated by comma.
    - Preserve established medical compound terms (e.g., "blood pressure" should stay together, not be split)
    - Return standard medical terminology as used in scientific databases
    - Include specific compound terms like "antihypertensive drugs", "blood pressure", "metabolic pathways"
    - Return only a list of relevant keywords separated by comma
    - Prioritize these key compound terms from medicine: hypertension, antihypertensive drug, blood pressure, metabolomics
    - Avoid common dictionary synonyms, and keep the synonyms related to medicine and science useful for search queries.
    - Avoid explaining the result or the process, just print the synonyms.
    - User will provide you directly with their keyword.
    - Be very selective to avoid too far off synonyms.
    """
    messages = [
        {"role": "assistant", "content": gpt_assistant_prompt},
        {"role": "user", "content": keyword}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=temperature,
        max_tokens=256,
        frequency_penalty=0.0,
    )
    response_text = response.choices[0].message.content
    return [keyword.strip() for keyword in response_text.split(",")]





