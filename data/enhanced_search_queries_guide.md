# Enhanced Search Query Variations

## Overview

This document contains enhanced search queries with wildcards and improved PubMed syntax based on PubMed search best practices.

## Key Improvements

### 1. Date Range Syntax
- **Old**: `2013:2024[Publication Date]`
- **New**: `2013:2024[dp]` (date of publication)
- **Alternative**: `2013/01/01:2024/12/31[dp]` for specific dates

### 2. Wildcards Added
- `hypertens*` - captures hypertension, hypertensive, etc.
- `metabolom*` - captures metabolomics, metabolomic, etc.
- `metabonom*` - captures metabonomics, metabonomic, etc.
- `antihypertens*` - captures antihypertensive, antihypertensives, etc.
- `vasodilat*` - captures vasodilator, vasodilation, vasodilatory, etc.
- `diuretic*` - captures diuretic, diuretics, etc.
- `profil*` - captures profile, profiles, profiling, etc.

### 3. Missing MeSH Terms Added
- **Vasodilator Agents**[MeSH Terms]
- **Calcium Channel Blockers**[MeSH Terms]
- **Angiotensin Receptor Antagonists**[MeSH Terms]
- **Metabolomics**[MeSH Terms] (expanded from just Metabolome)
- **Metabonomics**[MeSH Terms]

### 4. Expanded Terms
- Added "metabolic signatur*" for metabolomics
- Added "lipidom*" and "Lipidomics"[MeSH Terms]
- Added "ARB" as abbreviation for Angiotensin Receptor Blockers
- Added "beta-blocker*" and "beta blocker*"

## Query Variations


### Query 1: enhanced_v1_wildcards_recall

**Strategy**: Recall-oriented with wildcards (*) for term variations

**Description**: Enhanced query with wildcards for maximum recall

**Query**:
```
(     "Hypertension"[MeSH Terms] OR     "hypertens*"[Title/Abstract] OR     "high blood pressure"[Title/Abstract] OR     "Blood Pressure"[MeSH Terms] OR     "blood pressure"[Title/Abstract] OR     "Blood Pressure, High"[MeSH Terms]   ) AND (     "Metabolomics"[MeSH Terms] OR     "Metabolome"[MeSH Terms] OR     "Metabonomics"[MeSH Terms] OR     "metabolom*"[Title/Abstract] OR     "metabonom*"[Title/Abstract] OR     "metabolic profil*"[Title/Abstract] OR     "metabolic signatur*"[Title/Abstract] OR     "metabol* profil*"[Title/Abstract]   ) AND (     "Antihypertensive Agents"[MeSH Terms] OR     "antihypertens*"[Title/Abstract] OR     "anti-hypertens*"[Title/Abstract] OR     "Vasodilator Agents"[MeSH Terms] OR     "vasodilat*"[Title/Abstract] OR     "Calcium Channel Blockers"[MeSH Terms] OR     "calcium channel block*"[Title/Abstract] OR     "Angiotensin Receptor Antagonists"[MeSH Terms] OR     "angiotensin receptor block*"[Title/Abstract] OR     "ARB"[Title/Abstract] OR     "Angiotensin-Converting Enzyme Inhibitors"[MeSH Terms] OR     "ACE inhibitor*"[Title/Abstract] OR     "angiotensin converting enzyme inhibitor*"[Title/Abstract] OR     "Diuretics"[MeSH Terms] OR     "diuretic*"[Title/Abstract] OR     "beta-blocker*"[Title/Abstract] OR     "beta blocker*"[Title/Abstract] OR     "Adrenergic beta-Antagonists"[MeSH Terms]   ) AND humans[MeSH Terms] AND   english[Language] AND   (clinicaltrial[Filter] OR observationalstudy[Filter] OR randomizedcontrolledtrial[Filter]) AND   (2013:2024[dp])
```

**Key Features**:
- Extensive use of wildcards (*) for term variations


### Query 2: enhanced_v2_mesh_precision

**Strategy**: Precision-oriented with primary MeSH terms

**Description**: MeSH-focused query for precision

**Query**:
```
(     "Hypertension"[MeSH Terms] OR     "hypertens*"[Title/Abstract]   ) AND (     "Metabolomics"[MeSH Terms] OR     "Metabolome"[MeSH Terms] OR     "metabolom*"[Title/Abstract]   ) AND (     "Antihypertensive Agents"[MeSH Terms] OR     "Vasodilator Agents"[MeSH Terms] OR     "Calcium Channel Blockers"[MeSH Terms] OR     "Angiotensin Receptor Antagonists"[MeSH Terms] OR     "Angiotensin-Converting Enzyme Inhibitors"[MeSH Terms] OR     "Diuretics"[MeSH Terms]   ) AND   humans[MeSH Terms] AND   english[Language] AND   (clinicaltrial[Filter] OR observationalstudy[Filter] OR randomizedcontrolledtrial[Filter]) AND   (2013:2024[dp])
```

**Key Features**:
- Primary focus on MeSH terms for precision


### Query 3: enhanced_v3_broadest_recall

**Strategy**: Maximum recall with wildcards and lipidomics

**Description**: Broadest query with wildcards and expanded metabolomics

**Query**:
```
(     "Hypertension"[MeSH Terms] OR     "hypertens*"[Title/Abstract] OR     "high blood pressure"[Title/Abstract] OR     "Blood Pressure"[MeSH Terms] OR     "blood pressure"[Title/Abstract] OR     "Blood Pressure, High"[MeSH Terms]   ) AND (   "Metabolomics"[MeSH Terms] OR   "Metabolome"[MeSH Terms] OR   "Metabonomics"[MeSH Terms] OR   "metabolom*"[Title/Abstract] OR   "metabonom*"[Title/Abstract] OR   "metabolic profil*"[Title/Abstract] OR   "metabolic signatur*"[Title/Abstract] OR   "metabol*"[Title/Abstract] OR   "lipidom*"[Title/Abstract] OR   "Lipidomics"[MeSH Terms] ) AND (     "Antihypertensive Agents"[MeSH Terms] OR     "antihypertens*"[Title/Abstract] OR     "anti-hypertens*"[Title/Abstract] OR     "Vasodilator Agents"[MeSH Terms] OR     "vasodilat*"[Title/Abstract] OR     "Calcium Channel Blockers"[MeSH Terms] OR     "calcium channel block*"[Title/Abstract] OR     "Angiotensin Receptor Antagonists"[MeSH Terms] OR     "angiotensin receptor block*"[Title/Abstract] OR     "ARB"[Title/Abstract] OR     "Angiotensin-Converting Enzyme Inhibitors"[MeSH Terms] OR     "ACE inhibitor*"[Title/Abstract] OR     "angiotensin converting enzyme inhibitor*"[Title/Abstract] OR     "Diuretics"[MeSH Terms] OR     "diuretic*"[Title/Abstract] OR     "beta-blocker*"[Title/Abstract] OR     "beta blocker*"[Title/Abstract] OR     "Adrenergic beta-Antagonists"[MeSH Terms]   ) AND humans[MeSH Terms] AND   english[Language] AND   (clinicaltrial[Filter] OR observationalstudy[Filter] OR randomizedcontrolledtrial[Filter]) AND   (2013:2024[dp])
```

**Key Features**:
- Broadest coverage with multiple synonyms


### Query 4: enhanced_v4_balanced

**Strategy**: Balanced approach combining MeSH and wildcard terms

**Description**: Balanced query with wildcards and MeSH terms

**Query**:
```
(     "Hypertension"[MeSH Terms] OR     "hypertens*"[Title/Abstract] OR     "blood pressure"[Title/Abstract]   ) AND (     "Metabolomics"[MeSH Terms] OR     "metabolom*"[Title/Abstract] OR     "metabolic profil*"[Title/Abstract]   ) AND (     "Antihypertensive Agents"[MeSH Terms] OR     "Vasodilator Agents"[MeSH Terms] OR     "Calcium Channel Blockers"[MeSH Terms] OR     "Angiotensin Receptor Antagonists"[MeSH Terms] OR     "Angiotensin-Converting Enzyme Inhibitors"[MeSH Terms] OR     "Diuretics"[MeSH Terms] OR     "antihypertens*"[Title/Abstract] OR     "vasodilat*"[Title/Abstract] OR     "calcium channel block*"[Title/Abstract] OR     "ACE inhibitor*"[Title/Abstract] OR     "diuretic*"[Title/Abstract]   ) AND   humans[MeSH Terms] AND   english[Language] AND   (clinicaltrial[Filter] OR observationalstudy[Filter] OR randomizedcontrolledtrial[Filter]) AND   (2013:2024[dp])
```

**Key Features**:


## Recommendations

1. **Start with Query 1 (Wildcards Recall)**: Best for comprehensive retrieval
2. **Use Query 2 (MeSH Precision)**: If you need more precise results
3. **Try Query 3 (Broadest Recall)**: If Query 1 misses relevant articles
4. **Query 4 (Balanced)**: Good middle ground between recall and precision

## Testing

Use the comprehensive evaluation pipeline to test these queries:

```python
from comprehensive_evaluation_pipeline import ComprehensiveEvaluationPipeline

pipeline = ComprehensiveEvaluationPipeline(endnote_file)
results = pipeline.run_comprehensive_evaluation(
    llm_queries=queries,
    max_articles=100,
    date_range=(2013, 2024)
)
```

## Wildcard Usage Guidelines

According to PubMed:
- Wildcard (*) substitutes for 0 or more characters
- Terms must begin with at least 4 characters before the first wildcard
- Multiple wildcards can be used: `organi*ation*`
- Works in phrase searches: `"breast feed*"` or `breast feed*[tiab]`

## Date Range Guidelines

- Use `[dp]` for date of publication
- Format: `2013:2024[dp]` for year range
- Format: `2013/01/01:2024/12/31[dp]` for specific dates
- For full year: `2013:2013[dp]` to `2024:2024[dp]`
- Includes both print and electronic publication dates

---
*Generated based on PubMed search best practices*
