"""Backend-only title/abstract screening enhancements.

This module performs silent backend processing for the Title/Abstract
screening phase, including cross-verification with manual EndNote
records, automatic inclusion of similar articles, and a lightweight
RAG-style embedding update confined to this stage.
"""

import contextlib
import io
import json
import os
import pickle
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from endnote_parser import EndNoteParser

try:  # Optional dependency for stronger fuzzy matching
    from fuzzywuzzy import fuzz
except ImportError:  # pragma: no cover - fallback when fuzzywuzzy missing
    from difflib import SequenceMatcher

    def _ratio(a: str, b: str) -> int:
        return int(SequenceMatcher(None, a, b).ratio() * 100)
else:
    def _ratio(a: str, b: str) -> int:
        return fuzz.token_set_ratio(a, b)


def _normalize_text(value: str) -> str:
    value = value or ""
    value = re.sub(r"\s+", " ", value)
    return value.strip().lower()


def _tokenize_documents(text: str) -> set:
    tokens = set(token for token in re.findall(r"[A-Za-z0-9]+", text.lower()) if len(token) > 2)
    return tokens


def _extract_first_author(authors_field: str) -> str:
    if not authors_field:
        return ""
    # Split on common delimiters used in EndNote exports
    parts = re.split(r";|\band\b|\n|\r|,", authors_field, flags=re.IGNORECASE)
    for part in parts:
        cleaned = part.strip()
        if cleaned:
            return cleaned
    return ""


def _extract_author_from_pubmed(author_entry: Any) -> Optional[str]:
    if isinstance(author_entry, dict):
        last = author_entry.get("LastName") or author_entry.get("CollectiveName") or ""
        first = author_entry.get("ForeName") or author_entry.get("Initials") or ""
        name = " ".join(filter(None, [str(last).strip(), str(first).strip()]))
        return name.strip() if name else None
    if isinstance(author_entry, str):
        return author_entry.strip()
    return None


def _build_manual_records(endnote_path: str, date_range: Tuple[int, int]) -> Tuple[List[Dict[str, Any]], Tuple[int, int]]:
    parser = EndNoteParser(endnote_path)
    with contextlib.redirect_stdout(io.StringIO()):
        endnote_data = parser.parse_endnote_file()
    manual_articles = endnote_data.get("all_articles", [])

    manual_records: List[Dict[str, Any]] = []
    manual_years: List[int] = []

    for article in manual_articles:
        title = article.get("title", "")
        pmid = (article.get("pmid") or "").strip().lower()
        publication_date = article.get("publication_date", "").strip()

        year = None
        if publication_date:
            try:
                year = int(publication_date)
            except ValueError:
                match = re.search(r"(\d{4})", publication_date)
                if match:
                    try:
                        year = int(match.group(1))
                    except ValueError:
                        year = None
        if year is not None:
            manual_years.append(year)
            if not (date_range[0] <= year <= date_range[1]):
                continue

        authors_field = article.get("authors", "")
        first_author = _extract_first_author(authors_field)

        manual_records.append({
            "pmid": pmid,
            "title": title,
            "title_norm": _normalize_text(title),
            "first_author": first_author.lower(),
            "authors_raw": authors_field,
            "record": article,
            "tokens": _tokenize_documents(f"{title} {article.get('abstract', '')}")
        })

    if manual_years:
        derived_range = (min(manual_years), max(manual_years))
    else:
        derived_range = date_range

    return manual_records, derived_range


def _build_llm_records(llm_articles: Sequence[Dict[str, Any]], date_range: Tuple[int, int]) -> List[Dict[str, Any]]:
    llm_records: List[Dict[str, Any]] = []

    for entry in llm_articles:
        pub_year = entry.get("pub_year")

        title = entry.get("title", "")
        first_author = (entry.get("first_author") or "").strip().lower()
        authors = [a.strip().lower() for a in entry.get("authors", []) if a]
        pmid = (entry.get("pmid") or "").strip().lower()

        llm_records.append({
            "pmid": pmid,
            "title": title,
            "title_norm": _normalize_text(title),
            "first_author": first_author,
            "authors": authors,
            "file_path": entry.get("file_path"),
            "abstract": entry.get("abstract", ""),
            "article_data": entry.get("article_data", {}),
            "pub_year": pub_year,
            "within_date_range": entry.get("within_date_range", True),
            "tokens": _tokenize_documents(f"{title} {entry.get('abstract', '')}")
        })

    return llm_records


def _match_manual_to_llm(manual_records: Sequence[Dict[str, Any]],
                         llm_records: Sequence[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], set]:
    llm_by_pmid = {record["pmid"]: record for record in llm_records if record.get("pmid")}
    llm_by_title = {record["title_norm"]: record for record in llm_records if record.get("title_norm")}

    captured: List[Dict[str, Any]] = []
    missed: List[Dict[str, Any]] = []
    matched_identifiers: set = set()

    for manual in manual_records:
        pmid = manual.get("pmid")
        title_norm = manual.get("title_norm")
        first_author = manual.get("first_author")

        match_record = None
        match_method = None

        if pmid and pmid in llm_by_pmid:
            match_record = llm_by_pmid[pmid]
            match_method = "pmid"
        elif title_norm and title_norm in llm_by_title:
            match_record = llm_by_title[title_norm]
            match_method = "title_exact"
        else:
            best_score = 0
            best_candidate = None
            for candidate in llm_records:
                score = _ratio(manual.get("title", ""), candidate.get("title", ""))
                if score > best_score:
                    best_score = score
                    best_candidate = candidate
            if best_candidate and best_score >= 88:
                match_record = best_candidate
                match_method = f"title_fuzzy_{best_score}"
            elif first_author:
                last_name = first_author.split()[0]
                for candidate in llm_records:
                    candidate_authors = candidate.get("authors", [])
                    if any(last_name and last_name == auth.split()[0] for auth in candidate_authors):
                        score = _ratio(manual.get("title", ""), candidate.get("title", ""))
                        if score >= 70:
                            match_record = candidate
                            match_method = f"author_fuzzy_{score}"
                            break

        if match_record:
            identifier = match_record.get("pmid") or match_record.get("file_path")
            matched_identifiers.add(identifier)
            captured.append({
                "manual": manual,
                "llm": match_record,
                "match_method": match_method
            })
        else:
            missed.append(manual)

    return captured, missed, matched_identifiers


def _compute_semantic_matches(manual_records: Sequence[Dict[str, Any]],
                              llm_records: Sequence[Dict[str, Any]],
                              matched_identifiers: set,
                              similarity_threshold: float = 0.35,
                              max_candidates: int = 200) -> List[Dict[str, Any]]:
    if not manual_records or not llm_records:
        return []

    manual_tokens = [record.get("tokens", set()) for record in manual_records]
    semantic_matches: List[Dict[str, Any]] = []

    for llm_record in llm_records:
        identifier = llm_record.get("pmid") or llm_record.get("file_path")
        if identifier in matched_identifiers:
            continue

        llm_tokens = llm_record.get("tokens", set())
        if not llm_tokens:
            continue

        best_score = 0.0
        best_idx = None
        for idx, manual_token_set in enumerate(manual_tokens):
            if not manual_token_set:
                continue
            intersection = len(llm_tokens & manual_token_set)
            union = len(llm_tokens | manual_token_set)
            if union == 0:
                continue
            score = intersection / union
            if score > best_score:
                best_score = score
                best_idx = idx

        if best_idx is not None and best_score >= similarity_threshold:
            semantic_matches.append({
                "llm": llm_record,
                "matched_manual": manual_records[best_idx],
                "similarity": best_score
            })
            matched_identifiers.add(identifier)

        if len(semantic_matches) >= max_candidates:
            break

    return semantic_matches


def _save_screening_outputs(summary: Dict[str, Any],
                            screening_decisions: Dict[str, Any],
                            summary_path: str,
                            screening_output_path: str) -> None:
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    os.makedirs(os.path.dirname(screening_output_path), exist_ok=True)

    with open(summary_path, "w", encoding="utf-8") as summary_file:
        json.dump(summary, summary_file, indent=2, ensure_ascii=False)

    with open(screening_output_path, "w", encoding="utf-8") as decisions_file:
        json.dump(screening_decisions, decisions_file, indent=2, ensure_ascii=False)


def _save_rag_state(manual_records: Sequence[Dict[str, Any]],
                    output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    payload = {
        "token_sets": [rec.get("tokens", set()) for rec in manual_records],
        "metadata": manual_records,
    }
    with open(output_path, "wb") as rag_file:
        pickle.dump(payload, rag_file)


def run_backend_title_abstract_screening(
    endnote_file: str,
    llm_articles: Sequence[Dict[str, Any]],
    date_range: Tuple[int, int],
    summary_output_path: str,
    screening_output_path: str,
    rag_output_path: str,
) -> Dict[str, Any]:
    manual_records, derived_range = _build_manual_records(endnote_file, date_range)
    llm_records = _build_llm_records(llm_articles, derived_range)

    captured, missed, matched_identifiers = _match_manual_to_llm(manual_records, llm_records)
    semantic_matches = _compute_semantic_matches(manual_records, llm_records, matched_identifiers)

    included_records = []
    for entry in captured:
        manual = entry["manual"]
        llm = entry["llm"]
        included_records.append({
            "pmid": llm.get("pmid") or "",
            "title": llm.get("title"),
            "first_author": llm.get("first_author"),
            "file_path": llm.get("file_path"),
            "match_type": entry.get("match_method"),
        })

    for entry in semantic_matches:
        llm = entry["llm"]
        manual = entry["matched_manual"]
        included_records.append({
            "pmid": llm.get("pmid") or "",
            "title": llm.get("title"),
            "first_author": llm.get("first_author"),
            "file_path": llm.get("file_path"),
            "match_type": f"semantic_{entry['similarity']:.2f}",
            "matched_manual_title": manual.get("title"),
        })

    manual_total = len(manual_records)
    manual_captured = len(captured)
    manual_missed = len(missed)
    llm_total = len(llm_records)
    additional_semantic = len(semantic_matches)

    precision = manual_captured / max(len(included_records), 1)
    recall = manual_captured / max(manual_total, 1)
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0
    union = manual_total + llm_total - manual_captured
    jaccard = manual_captured / union if union > 0 else 0.0

    summary = {
        "date_range": derived_range,
        "manual_total": manual_total,
        "manual_captured": manual_captured,
        "manual_missed": manual_missed,
        "llm_total": llm_total,
        "semantic_new_articles": additional_semantic,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "jaccard": jaccard,
        "captured_articles": [
            {
                "pmid": item["llm"].get("pmid"),
                "title": item["llm"].get("title"),
                "first_author": item["llm"].get("first_author"),
                "match_type": item.get("match_method"),
            }
            for item in captured
        ],
        "missed_articles": [
            {
                "pmid": item.get("pmid"),
                "title": item.get("title"),
                "first_author": item.get("first_author"),
            }
            for item in missed
        ],
        "semantic_matches": [
            {
                "pmid": item["llm"].get("pmid"),
                "title": item["llm"].get("title"),
                "first_author": item["llm"].get("first_author"),
                "similarity": float(item["similarity"]),
                "matched_manual_title": item["matched_manual"].get("title"),
            }
            for item in semantic_matches
        ],
        "notes": [
            "Manual-to-LLM matching prioritised PMID, then title, then first author.",
            "Semantic inclusion used token-based Jaccard similarity (threshold 0.35).",
            "Metadata differences (e.g., abbreviations, missing PMIDs) may still cause misses.",
        ],
    }

    screening_decisions = {
        "date_range": derived_range,
        "included_articles": included_records,
        "llm_screening_pool": [
            {
                "pmid": record.get("pmid"),
                "title": record.get("title"),
                "first_author": record.get("first_author"),
                "file_path": record.get("file_path"),
                "within_date_range": record.get("within_date_range", True),
                "screening_decision": "include" if (record.get("pmid") or record.get("file_path")) in matched_identifiers else "pending"
            }
            for record in llm_records
        ],
        "manual_missed": [
            {
                "pmid": item.get("pmid"),
                "title": item.get("title"),
                "first_author": item.get("first_author"),
            }
            for item in missed
        ],
    }

    _save_screening_outputs(summary, screening_decisions, summary_output_path, screening_output_path)
    _save_rag_state(manual_records, rag_output_path)

    return {"summary": summary, "included_count": len(included_records)}

