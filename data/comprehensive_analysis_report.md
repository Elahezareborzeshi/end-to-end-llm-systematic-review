# Comprehensive Query and Article Analysis Report

## Executive Summary

This report compares the manual systematic review search strategy with the LLM-generated query and analyzes article overlap using improved matching techniques.

## Key Findings

### Article Matching Results

- **Total Manual Included Articles (2013-2024)**: 1151
- **Total LLM Articles (2013-2024)**: 9881
- **Total Matched**: 1151
  - Matched by PMID: 1
  - Matched by DOI: 0
  - Matched by Title: 1150
- **Missed Articles**: 0
- **Match Rate**: 100.00%

### Query Comparison

#### Query Lengths
- **Manual Query**: 0 characters
- **LLM Query**: 4134 characters

#### MeSH Terms
- **Manual MeSH Terms**: 0
- **LLM MeSH Terms**: 90
- **Common MeSH Terms**: 0
- **Manual-Only MeSH Terms**: 0
- **LLM-Only MeSH Terms**: 84

#### Title/Abstract Terms
- **Manual Title/Abstract Terms**: 0
- **LLM Title/Abstract Terms**: 7
- **Common Terms**: 0

#### Date Ranges
- **Manual Date Range**: None
- **LLM Date Range**: ['2013', '2023']

## Important Observations

1. **Title Matching Success**: With improved fuzzy title matching (threshold: 75%), we found 1150 matches by title, indicating that the articles ARE present in the LLM dataset but weren't matching by PMID.

2. **PMID Matching Limitation**: Only 1 articles matched by PMID, suggesting:
   - PMIDs may be missing or different between sources
   - The same articles may have different identifiers
   - Title matching is crucial for accurate comparison

3. **Query Differences**: The manual and LLM queries differ significantly in:
   - Number of MeSH terms
   - Query structure
   - Date range (manual: None, LLM: ['2013', '2023'])

## Recommendations

1. **Use Improved Title Matching**: The comparison workflow should use the improved fuzzy title matching algorithm (threshold: 75%) to capture more articles.

2. **Update Date Range**: The LLM query uses 2013:2023[pdat] but should use 2013:2024[Publication Date] to match the manual review period.

3. **Query Optimization**: Consider incorporating terms from the manual query that are missing in the LLM query to improve recall.

4. **PMID Verification**: Investigate why PMIDs don't match - this could indicate:
   - Different database versions
   - Missing metadata
   - Identifier mapping issues

## LLM Query

```
("hypertension"[Title/Abstract] OR "Hypertension"[MeSH Terms] OR "Blood Pressure, High"[MeSH Terms] OR "Blood Pressures, High"[MeSH Terms] OR "High Blood Pressure"[MeSH Terms] OR "High Blood Pressures"[MeSH Terms] OR "blood pressure"[Title/Abstract] OR "Blood Pressure"[MeSH Terms] OR "Pressure, Blood"[MeSH Terms] OR "Pulse Pressure"[MeSH Terms] OR "Pressure, Pulse"[MeSH Terms] OR "Diastolic Pressure"[MeSH Terms] OR "Pressure, Diastolic"[MeSH Terms] OR "Systolic Pressure"[MeSH Terms] OR "Pressure...
```

## Next Steps

1. Update the comparison workflow (`run_workflow_with_existing_data.py`) to use improved title matching
2. Test multiple query variations using the comprehensive evaluation pipeline
3. Analyze patterns in the matched articles to understand query effectiveness
4. Generate improved queries based on manual query analysis

---
*Report generated from comprehensive analysis*
