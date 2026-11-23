import os
import time
from urllib.error import HTTPError, URLError
from http.client import IncompleteRead

# import requests
# from bs4 import BeautifulSoup
from Bio import Entrez
import json
from config import config

# Email and API key must be supplied via environment variables (.env)
Entrez.email = config.PUBMED_EMAIL or os.getenv('PUBMED_EMAIL', '')
Entrez.api_key = config.PUBMED_API_KEY

def download_articles_from_pubmed(search_query, max_articles=None, date_start=None, date_end=None):
    """
    Download articles from PubMed based on the search query.
    
    Args:
        search_query: Boolean search query string
        max_articles: Maximum number of articles to download (None for all)
        date_start: Start year (e.g., "2013")
        date_end: End year (e.g., "2023")
    """
    print(f"🔍 Searching PubMed for: '{search_query}'")
    
    if max_articles is None:
        print(f"📚 No limit set - downloading all available articles")
    else:
        print(f"📚 Maximum articles to fetch: {max_articles}")
    
    if date_start and date_end:
        print(f"📅 Date range: {date_start}-{date_end}")
    
    articles = []
    page_size = 10
    current_page = 0

    while True:  # Changed from: while len(articles) < max_articles
        print(f"\n📄 Fetching page {current_page + 1}...")
        
        retstart = current_page * page_size
        
        if max_articles is None:
            retmax = page_size
        else:
            retmax = min(page_size, max_articles - len(articles))
        
        print(f"   ⏳ Searching for IDs (offset: {retstart}, limit: {retmax})...")
        
        # Add date range to search query if provided
        search_term = search_query
        if date_start and date_end:
            search_term = f"{search_query} AND ({date_start}[Publication Date] : {date_end}[Publication Date])"
        
        id_list = search_pubmed(search_term, retstart=retstart, retmax=retmax)
        
        if not id_list:
            print("   ❌ No more articles found.")
            break
        
        print(f"   ✅ Found {len(id_list)} article IDs on this page.")
        print(f"   🔗 Fetching details for articles...")
        result = fetch_details(id_list)
        
        for article in result['PubmedArticle']:
            articles.append(json.dumps(article, indent=2))
        
        if max_articles is None:
            print(f"   📊 Progress: {len(articles)} articles fetched (no limit)")
        else:
            print(f"   📊 Progress: {len(articles)}/{max_articles} articles fetched")
        
        if len(id_list) < page_size:
            print("   🏁 Reached the end of search results.")
            break
        
        # Check if we've reached the limit (only if max_articles is set)
        if max_articles is not None and len(articles) >= max_articles:
            print(f"   🎯 Reached maximum limit of {max_articles} articles.")
            break
        
        current_page += 1

    if not articles:
        print("❗ No articles found for the given query.")
        return []

    print(f"\n💾 Saving {len(articles)} articles...")
    paths = save_articles(articles)
    print(f"✨ Download complete! {len(articles)} articles saved.")
    return paths

def save_articles(articles):
    """Save downloaded articles to files."""
    save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'downloaded_articles')
    os.makedirs(save_dir, exist_ok=True)
    
    paths = []
    for i, article in enumerate(articles):
        filename = os.path.join(save_dir, f"article_{i+1}_source.json")
        paths.append(filename)
        with open(filename, 'w') as f:
            f.write(article)
    
    print(f"Saved {len(articles)} articles to {save_dir}")
    return paths

def search_pubmed(query, retstart=0, retmax=10):
    max_retries = 5
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            print(f"🔍 Executing PubMed search: {query[:100]}...")
            handle = Entrez.esearch(db="pubmed", term=query, retstart=retstart, retmax=retmax)
            record = Entrez.read(handle)
            handle.close()
            
            print(f"✅ Search returned {len(record['IdList'])} results")
            return record['IdList']
        except (HTTPError, URLError, IncompleteRead) as e:
            if isinstance(e, HTTPError) and 400 <= e.code < 500:
                print(f" ❌ Client error (4xx) in search_pubmed: {e}")
                if hasattr(e, 'read'):
                    try:
                        error_body = e.read().decode('utf-8')
                        print(f"   Error details: {error_body}")
                    except:
                        pass
                raise  # Re-raise client errors without retrying
            
            if attempt < max_retries - 1:
                print(f" ⚠️ Attempt {attempt + 1} failed in search_pubmed: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f" ❌ All {max_retries} attempts failed in search_pubmed. Last error: {e}")
                raise
    
    raise Exception("Unexpected error: Reached end of search_pubmed without returning or raising")

def fetch_details(id_list):
    ids = ','.join(id_list)
    print(f" -> Fetching details for {len(id_list)} articles")
    
    max_retries = 5
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            handle = Entrez.efetch(db="pubmed", id=ids, retmode="xml")
            records = Entrez.read(handle)
            handle.close()
            return records
        except (HTTPError, IncompleteRead) as e:
            if isinstance(e, HTTPError) and 400 <= e.code < 500:
                print(f" ❌ Client error (4xx): {e}")
                if hasattr(e, 'read'):
                    try:
                        error_body = e.read().decode('utf-8')
                        print(f"   Error details: {error_body}")
                    except:
                        pass
                raise  # Re-raise client errors without retrying
            
            if attempt < max_retries - 1:
                print(f" ⚠️ Attempt {attempt + 1} failed: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f" ❌ All {max_retries} attempts failed. Last error: {e}")
                raise
    
    raise Exception("Unexpected error: Reached end of function without returning or raising")
