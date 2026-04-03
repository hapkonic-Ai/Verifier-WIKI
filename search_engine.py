from ddgs import DDGS
from typing import List, Dict

def perform_search(entity_name: str, max_results: int = 15) -> List[Dict[str, str]]:
    """
    Search DuckDuckGo for relevant media links based on an entity's name.
    Returns a list of dicts: [{'title': '...', 'href': '...', 'body': '...'}, ...]
    """
    try:
        results = []
        # We append keywords to surface biographical/notability-relevant content
        query = f'"{entity_name}" (news OR article OR profile NOT wikipedia)'
        
        with DDGS() as ddgs:
            # We use text search because it is less rate-limited and covers massive ground
            raw_results = ddgs.text(query, max_results=max_results)
            
            for r in raw_results:
                # the ddgs.text returns dicts with 'title', 'href', 'body'
                if 'href' in r and r['href']:
                    results.append(r)
                    
        return results
    except Exception as e:
        print(f"Error searching DuckDuckGo: {e}")
        return []
