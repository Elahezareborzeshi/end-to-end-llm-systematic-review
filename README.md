# LLM Systematic Review Framework

An end-to-end, human-in-the-loop large language model (LLM) framework for systematic reviews. The software supports research-question formulation, keyword and MeSH discovery, PubMed query construction, literature retrieval, title/abstract and full-text screening with RAG-assisted LLM decisions, structured data extraction, and evaluation against a manual reference standard.

## Citation

> **Paper citation (placeholder):** Zare Borzeshi, E., et al. (year). *Title of the paper*. PLOS ONE. DOI: `https://doi.org/10.XXXX/journal.pone.XXXXXXX`

> **Software archive (placeholder):** Zenodo DOI: `https://doi.org/10.5281/zenodo.XXXXXXX`

Please replace the placeholders above with the final PLOS ONE citation and Zenodo DOI before submission/publication.

## License

MIT License — Copyright (c) 2026 Elahe Zare Borzeshi. See [LICENSE](LICENSE).

## Requirements

- Python 3.9+ (developed/tested with Python 3.9)
- An OpenAI API key (required for LLM stages)
- Optional: NCBI/PubMed API key and contact email (recommended for higher rate limits)

## Setup

```bash
git clone https://github.com/Elahezareborzeshi/end-to-end-llm-systematic-review
cd end-to-end-llm-systematic-review

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and set OPENAI_API_KEY=YOUR_API_KEY_HERE
# Optionally set PUBMED_EMAIL and PUBMED_API_KEY
```

**Never commit your `.env` file.** It is listed in `.gitignore`.

## Run the interactive app

```bash
streamlit run src/main.py
```

## Repository structure

```
end-to-end-llm-systematic-review/
├── src/                         # Application source code
│   ├── main.py                  # Streamlit entry point
│   ├── config.py                # Loads API keys / paths from environment
│   ├── core/                    # Search, retrieval, screening, extraction
│   ├── validation/              # EndNote parsing, validators, visuals
│   └── utils/                   # Evaluation helpers and comparators
├── data/                        # Evaluation outputs used in the paper
├── scripts/                     # Offline utility scripts
├── docs/                        # Additional documentation
├── requirements.txt
├── .env.example
├── LICENSE
└── README.md
```

### Logical module groups (`src/`)

| Group | Main modules |
|---|---|
| **Search / strategy** | `core/keyword_extractor.py`, `core/mesh_term_finder.py`, `core/mesh_terms_groupings.py`, `core/search_query_builder.py`, `core/search_query_validator.py`, `core/suggestion_engine.py`, `query_enhancer.py`, `query_diversifier.py`, `manual_search_strategy.py` |
| **Retrieval** | `core/article_downloader.py`, `article_downloader.py`, `core/article_full_text_downloader.py`, `core/article_deduplicator.py` |
| **Screening** | `core/rag_screening.py`, `core/article_title_abstract_screening.py`, `core/article_full_text_screening.py`, `backend_title_abstract_screening.py` |
| **Extraction** | `core/article_data_extractor.py` |
| **Evaluation** | `comprehensive_evaluator.py`, `comprehensive_validator.py`, `comprehensive_evaluation_pipeline.py`, `enhanced_metrics.py`, `validation/*`, `utils/*` |

### Evaluation data (`data/`)

Key files underlying the reported metrics (keep these for reproducibility):

| File | Role |
|---|---|
| `backend_title_abstract_screening_all.json` | LLM title/abstract screening decisions + rationales (batch) |
| `backend_included_articles_list.json` | Title/abstract INCLUDE subset |
| `backend_screening_metrics.json` | LLM vs manual title/abstract comparison metrics |
| `backend_full_text_screening_results.json` | LLM full-text screening decisions + rationales |
| `backend_full_text_included_articles_list.json` | Full-text INCLUDE subset |
| `backend_full_text_screening_metrics.json` | LLM vs manual full-text comparison metrics |
| `comprehensive_llm_vs_manual_metrics.json` | Aggregated LLM-vs-manual metrics |
| `missed_articles_analysis.json` | Missed-article analysis |
| `comparison_report.json` / `evaluation_report.md` | Keyword / strategy comparison outputs |
| `workflow_comparison_results.json` | Workflow-level overlap summary |
| `data_extraction_shahin_29288159.json` (+ CSV) | Example structured extraction |
| `manual_evaluation_extraction/` | Offline PDF extraction outputs used in evaluation |
| `sample/` | Small sample article JSON files for smoke tests |

Large raw PubMed download caches (`data/downloaded_articles/`) are **not** required to recompute the published metric tables from the JSON/CSV files above and are excluded from version control.

## Reproducing the evaluation

The reported comparison metrics are stored as JSON and can be inspected without calling the OpenAI API:

```bash
# Title/abstract LLM vs manual
python3 -c "import json; print(json.load(open('data/backend_screening_metrics.json'))['metrics'])"

# Full-text LLM vs manual
python3 -c "import json; print(json.load(open('data/backend_full_text_screening_metrics.json'))['metrics'])"

# Aggregated metrics
python3 -c "import json; print(json.dumps(json.load(open('data/comprehensive_llm_vs_manual_metrics.json')), indent=2))"
```

To re-run interactive stages of the framework (optional; incurs API cost):

1. Configure `.env` with your own `OPENAI_API_KEY`.
2. Start the app: `streamlit run src/main.py`.
3. Follow the UI workflow (research question → keywords/MeSH → query → download → screening → extraction).
4. For offline PDF extraction of evaluation targets, place PDFs under `data/manual_pdfs/` and run `python scripts/manual_articles_extractor.py`.

**Note:** Historical batch runners used for some paper tables are not all present in this repository. Metric tables themselves are preserved under `data/`. A new LLM run will not bit-match historical outputs because model behaviour and API versions change over time.

## Security

- Supply secrets only via environment variables (see `.env.example`).
- Do not commit `.env`, API keys, or personal absolute file paths.
- Before uploading a ZIP to Zenodo, confirm `.env` and `.venv/` are excluded.

## Documentation

- [Framework instructions](docs/LLM_SYSTEMATIC_REVIEW_FRAMEWORK_INSTRUCTIONS.md)
