import os
import time
import requests
from urllib.parse import urlparse

def read_links():
    """Read the URLs from unique_links.txt"""
    with open('unique_links.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

def download_page(url, cache_dir):
    """Download a webpage and save to cache directory"""
    # Create filename from URL (sanitize for filesystem)
    safe_filename = url.replace('://', '_').replace('/', '_')
    safe_filename = ''.join(c for c in safe_filename if c.isalnum() or c in '_-.')
    filename = os.path.join(cache_dir, safe_filename)
    
    # Check if already cached and not too old
    if os.path.exists(filename):
        print("\tcached")
        # Check file age
        file_age_days = (time.time() - os.path.getmtime(filename)) / (60 * 60 * 24)
        if file_age_days < 30:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                # Try different encoding if utf-8 fails
                with open(filename, 'r', encoding='latin-1') as f:
                    return f.read()
    # Download the page with timeout and retry
    max_retries = 3
    for attempt in range(max_retries):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Try to detect encoding
            if response.encoding:
                content = response.text
            else:
                content = response.content.decode('utf-8', errors='replace')
            
            # Save to cache
            with open(filename, 'w', encoding='utf-8', errors='replace') as f:
                f.write(content)
            
            # Pause to be polite to the server (longer after retries)
            time.sleep(1 + attempt)
            
            return content
            
        except (requests.RequestException, UnicodeError) as e:
            print(f"Attempt {attempt+1} failed for {url}: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 * (attempt + 1))  # Exponential backoff
    
    raise Exception(f"Failed to download {url} after {max_retries} attempts")

def main():
    # Setup
    cache_dir = 'cache'
    os.makedirs(cache_dir, exist_ok=True)
    
    # Get all links
    links = read_links()
    print(f"Found {len(links)} links to download")
    
    for i, url in enumerate(links, 1):
        try:
            download_page(url, cache_dir)
            print(f"Downloading page {i}/{len(links)}")
        except Exception as e:
            print(f"Error processing {url}: {e}")


if __name__ == "__main__":
    main()