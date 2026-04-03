import requests
from bs4 import BeautifulSoup
import re
from typing import Optional

def scrape_url(url: str, timeout: int = 25) -> Optional[str]:
    """
    Fetches the content of a URL and extracts readable text.
    Uses r.jina.ai as a primary proxy to bypass bot protections (403s on news sites),
    and falls back to standard requests if it fails.
    """
    jina_url = f"https://r.jina.ai/{url}"
    headers_jina = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    headers_fallback = {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
    }
    
    try:
        # Step 1: Try Jina Reader
        response = requests.get(jina_url, headers=headers_jina, timeout=timeout)
        if response.status_code == 200 and len(response.text) > 100:
            text = response.text
            if len(text) > 100000:
                return text[:100000] + "... [TRUNCATED]"
            return text
            
        # Step 2: Fallback using Googlebot User-Agent
        response = requests.get(url, headers=headers_fallback, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
            
        text = soup.get_text(separator=' ')
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) > 100000:
            return text[:100000] + "... [TRUNCATED]"
            
        return text
    
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None
