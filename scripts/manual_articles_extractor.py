import os
import json
from pathlib import Path

from PyPDF2 import PdfReader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.text_splitter import CharacterTextSplitter


def read_pdf_text(pdf_path: Path) -> str:
    """Extract raw text from a PDF file."""
    reader = PdfReader(str(pdf_path))
    chunks = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text:
            chunks.append(text)
    return "\n\n".join(chunks).strip()


def build_qa_chain(text: str) -> RetrievalQA:
    """Build a RetrievalQA chain over the given text."""
    embeddings = OpenAIEmbeddings()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_text(text)
    vectorstore = FAISS.from_texts(texts, embedding=embeddings)

    llm = ChatOpenAI(temperature=0.02, model_name="gpt-4o")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
    )
    return qa_chain


def extract_from_pdf(
    pdf_path: Path,
    output_dir: Path,
    research_question: str,
    selection_criteria: str,
    final_result_instructions: str,
) -> None:
    """Run LLM-based extraction for a single manual-review PDF."""
    print(f"\n📄 Processing PDF: {pdf_path}")

    if not pdf_path.exists():
        print(f"❌ File not found: {pdf_path}")
        return

    text = read_pdf_text(pdf_path)
    if not text:
        print(f"❌ No text could be extracted from: {pdf_path}")
        return

    qa_chain = build_qa_chain(text)

    # 1) Human-readable summary
    summarization_prompt = f"""
You are assisting a systematic review.

Research question:
{research_question}

Selection criteria (inclusion / exclusion):
{selection_criteria}

Based on the full text of the article, summarize it in a human-readable way. Follow these instructions:
- What are the main findings relevant to the research question? Provide a list of key findings.
- What are the key results? Include numerical values where available.
- What is the method and study design? Include the type of study (e.g., RCT, cohort, case-control) and any key methodological details.
- What are the inclusion and exclusion criteria? If applicable.
- What is the intervention or exposure? If applicable.
- What are the patient/population characteristics? Include sample size, age range, and any other relevant demographic information.
- What are the main conclusions of the study? Provide a concise list.
- What recommendations follow from the findings? If applicable.
- What are the main limitations of the study?
- What are the exposures of interest and outcomes? List them separately.
"""
    summarization = qa_chain.run(summarization_prompt)

    # 2) Structured extraction for your evaluation table
    final_result_prompt = f"""
You are extracting data for a systematic review.

Research question:
{research_question}

Selection criteria (inclusion / exclusion):
{selection_criteria}

Based on the full text of the article, extract the most important information for each of these fields:
{final_result_instructions}

Follow these instructions:
- Provide the results in a JSON object.
- Use each field description (e.g. "First Author", "Publication Date") as a JSON key.
- Focus on raw data and short, clear phrases, not long explanations.
- If multiple values exist for a field, you may repeat other fields as needed to keep rows consistent.
- If a field cannot be determined, set its value to null or an empty string.

Return ONLY valid JSON, with no surrounding markdown.
"""
    final_results_raw = qa_chain.run(final_result_prompt)

    # Try to parse JSON; if it fails, wrap as a string
    try:
        # Strip any accidental code fences
        cleaned = final_results_raw.replace("```json", "").replace("```", "").strip()
        final_results = json.loads(cleaned)
    except Exception:
        final_results = {"raw_response": final_results_raw}

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / (pdf_path.stem + "_extracted.json")

    payload = {
        "source_pdf": str(pdf_path),
        "summarization": summarization,
        "final_results": final_results,
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"✅ Extraction saved to: {out_path}")


def main():
    # --- CONFIGURE THESE FOR YOUR EVALUATION ---
    research_question = """
Identify metabolome and metabolomic profiles, as well as biochemical pathways, associated with hypertension response to different classes of antihypertensive drugs using pharmacometabolomics approaches.
Specifically, identify key metabolic biomarkers and signatures predictive of treatment response across diuretics, beta-blockers, ACE inhibitors, ARBs, vasodilators, and calcium channel blockers, and assess the potential for metabolome-informed, personalized antihypertensive therapy.
""".strip()

    selection_criteria = """
Inclusion:
- Human studies assessing metabolomics-based biomarkers of blood pressure response to antihypertensive medications
- Clear association between metabolites and BP changes reported
- Specific metabolite identification
- Validated metabolomics platforms (e.g. GC-TOF/MS, LC-MS, NMR, UHPLC-MS)
- Peer-reviewed, English-language publications from 2013 onwards

Exclusion:
- Animal or in vitro studies
- Studies without clear metabolite–BP association
- Case reports, conference abstracts without full text, or insufficient data for extraction
""".strip()

    final_result_instructions = """
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
""".strip()

    # Place full-text PDFs under data/manual_pdfs/ (or set MANUAL_PDF_DIR).
    # Do not hard-code personal absolute paths in this repository.
    pdf_dir = Path(os.getenv("MANUAL_PDF_DIR", "data/manual_pdfs"))
    pdf_names = [
        "Rotroff-2015.pdf",
        "shahin2017.pdf",
        "Weng-2016.pdf",
        "Sonn.pdf",
        "Haung-2022.pdf",
    ]
    pdf_paths = [pdf_dir / name for name in pdf_names]

    output_dir = Path("data/manual_evaluation_extraction")

    for pdf in pdf_paths:
        if not pdf.exists():
            print(f"⚠️  Skipping missing PDF: {pdf}")
            continue
        extract_from_pdf(
            pdf_path=pdf,
            output_dir=output_dir,
            research_question=research_question,
            selection_criteria=selection_criteria,
            final_result_instructions=final_result_instructions,
        )


if __name__ == "__main__":
    main()

