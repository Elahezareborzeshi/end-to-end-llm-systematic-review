# Security Checklist for Repository Publication

Use this checklist before making the repository public or uploading a ZIP to Zenodo.

## Pre-publication checks

### 1. Environment variables and API keys
- [ ] No real API keys in tracked files
- [ ] `.env` is listed in `.gitignore` and is **not** included in any Zenodo ZIP
- [ ] `.env.example` / `.env.dist` contain placeholders only
- [ ] No hardcoded personal email addresses in code

### 2. Personal information
- [ ] No personal absolute paths (`/Users/...`, `OneDrive`, etc.) in code or evaluation JSON
- [ ] Optional local paths come from environment variables (`ENDNOTE_FILE_PATH`, `MANUAL_QUERY_PATH`, `MANUAL_PDF_DIR`)

### 3. Data files
- [ ] Large raw downloads under `data/downloaded_articles/` are empty except `.gitkeep`
- [ ] Evaluation JSON/CSV needed for the paper remain in `data/`
- [ ] Debug caches (`.pkl`, `vector_store.txt`, `user_feedback.jsonl`) are excluded

### 4. Suggested commands

```bash
# Should find no live sk- keys outside a local .env (which must stay untracked)
rg -n 'sk-' --glob '!.env' --glob '!.venv/**' .

# Should find no personal home paths
rg -n '/Users/|OneDrive|C:\\Users|/home/' --glob '!.venv/**' --glob '!.git/**' .

# Confirm .env is ignored
git check-ignore -v .env
```

### 5. Git history warning

If secrets or personal paths were committed in earlier revisions, making the GitHub repo public can still expose them via history. Consider cleaning history with `git filter-repo` / BFG **before** the first public push, or publish a fresh orphan branch that contains only the sanitized tree.
