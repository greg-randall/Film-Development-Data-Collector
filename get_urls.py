import requests
import itertools
import string
import re
import time
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

def generate_combinations():
    """Generate all combinations from 'aa' to 'zz'"""
    letters = string.ascii_lowercase
    return [''.join(combo) for combo in itertools.product(letters, repeat=2)]

def make_absolute_url(url, base="https://www.digitaltruth.com"):
    """Convert relative URLs to absolute URLs"""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    elif url.startswith("/"):
        return f"{base}{url}"
    else:
        return f"{base}/{url}"

def search_and_extract_hrefs(query):
    """Search for a query and extract all hrefs from the results"""
    url = 'https://www.digitaltruth.com/chart/dbsearch/search.php'
    data = {'query': query}
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        # Parse HTML and extract all href attributes
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [make_absolute_url(a.get('href')) for a in soup.find_all('a', href=True)]
        
        # Filter out None values and empty strings
        links = [link for link in links if link]
        
        print(f"Found {len(links)} links for query '{query}'")
        return {query: links}
    except Exception as e:
        print(f"Error searching for '{query}': {e}")
        return {query: []}
    finally:
        # Be nice to the server
        time.sleep(1)

def main():
    # Generate all combinations
    combinations = generate_combinations()
    print(f"Generated {len(combinations)} combinations to search")
    
    # Store all collected hrefs
    all_results = {}
    
    # Use ThreadPoolExecutor for parallel requests (adjust max_workers as needed)
    with ThreadPoolExecutor(max_workers=10) as executor:
        for result in executor.map(search_and_extract_hrefs, combinations):
            all_results.update(result)
    
    # Deduplicate links across all queries and filter out JavaScript links
    unique_links = set()
    deduped_results = {}
    
    for query, links in all_results.items():
        deduped_links = []
        for link in links:
            # Skip links containing "JavaScript"
            if "javascript" in link.lower():
                continue
                
            if link not in unique_links:
                unique_links.add(link)
                deduped_links.append(link)
        if deduped_links:
            deduped_results[query] = deduped_links
    
    # Save only unique links to file (no headers or query information)
    with open('unique_links.txt', 'w') as f:
        for link in sorted(unique_links):
            f.write(f"{link}\n")
    
    print(f"Search completed.")
    print(f"Found {len(unique_links)} unique links")
    print(f"Unique links saved to 'unique_links.txt'")
    
    # Count total links found before deduplication
    total_links = sum(len(links) for links in all_results.values())
    print(f"Total links found (with duplicates): {total_links}")

if __name__ == "__main__":
    main()