import os
import csv
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def read_links():
    """Read the URLs from unique_links.txt"""
    with open('unique_links.txt', 'r') as f:
        return [line.strip() for line in f if line.strip()]

def read_cached_page(url, cache_dir):
    """Read a webpage from cache directory"""
    # Create filename from URL (sanitize for filesystem)
    safe_filename = url.replace('://', '_').replace('/', '_')
    safe_filename = ''.join(c for c in safe_filename if c.isalnum() or c in '_-.')
    filename = os.path.join(cache_dir, safe_filename)
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try different encoding if utf-8 fails
        with open(filename, 'r', encoding='latin-1') as f:
            return f.read()
    except FileNotFoundError:
        raise Exception(f"Cache file not found for {url}")

def parse_table(html, source_url=""):
    """Extract table data from HTML with handling for malformed tables"""
    # First, try to fix missing </tr> tags
    html = html.replace('<tr>', '</tr><tr>')
    # Remove the first occurrence which would be incorrect
    html = html.replace('</tr>', '', 1)
    
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='mdctable')
    
    if not table:
        return []
    
    # Expected column count
    expected_columns = 9
    
    # Standard headers
    standard_headers = ['Film', 'Developer', 'Dilution', 'ASA/ISO', '35mm', '120', 'Sheet', 'Temp', 'Notes']
    
    # Extract headers
    headers = []
    thead = table.find('thead')
    if thead:
        header_row = thead.find('tr')
        if header_row:
            for th in header_row.find_all('th'):
                headers.append(th.text.strip())
    
    # If headers don't match expected count, use standard headers
    if len(headers) != expected_columns:
        headers = standard_headers
    
    # Extract rows - handle tables with or without tbody
    rows = []
    tbody = table.find('tbody')
    
    # If tbody exists, get rows from it
    if tbody:
        row_elements = tbody.find_all('tr')
    else:
        # If no tbody, get all rows and skip header
        all_rows = table.find_all('tr')
        row_elements = all_rows[1:] if len(all_rows) > 1 else []
    
    for tr in row_elements:
        cells = tr.find_all('td')
        if not cells:
            continue
            
        row = []
        for td in cells:
            # Clean cell text
            cell_text = td.text.strip()
            # Remove [notes] text but keep link if present
            if '[notes]' in cell_text:
                cell_text = ''
                # Try to get href if available
                note_link = td.find('a')
                if note_link and note_link.has_attr('href'):
                    # Make link absolute
                    href = note_link['href']
                    if href.startswith('http'):
                        cell_text = href
                    else:
                        # Extract base URL from source_url if available
                        if source_url:
                            # Get the domain part
                            parsed_source = urlparse(source_url)
                            base_url = f"{parsed_source.scheme}://{parsed_source.netloc}"
                            # Handle paths that start with or without slash
                            if href.startswith('/'):
                                cell_text = f"{base_url}{href}"
                            else:
                                path_dir = '/'.join(parsed_source.path.split('/')[:-1])
                                if path_dir:
                                    cell_text = f"{base_url}{path_dir}/{href}"
                                else:
                                    cell_text = f"{base_url}/{href}"
                        else:
                            cell_text = f"https://www.digitaltruth.com{href}"
            row.append(cell_text)
            
        # Ensure row has exactly expected_columns
        if len(row) < expected_columns:
            row.extend([''] * (expected_columns - len(row)))
        elif len(row) > expected_columns:
            row = row[:expected_columns]
            
        # Add source URL to each row
        row.append(source_url)
        rows.append(row)
    
    # Add source URL to headers too
    headers.append('Source URL')
    return [headers] + rows

def write_to_csv(data, filename, append=False):
    """Write or append data to CSV file"""
    mode = 'a' if append else 'w'
    
    with open(filename, mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)

def main():
    # Setup
    cache_dir = 'cache'
    csv_file = 'all-film-all-developer.csv'
    os.makedirs(cache_dir, exist_ok=True)
    
    
    # Get all links
    links = read_links()
    print(f"Found {len(links)} links to process")
    
    # Process first page to get headers
    try:
        first_url = links[0]
        first_page = read_cached_page(first_url, cache_dir)
        first_data = parse_table(first_page, first_url)
        
        if not first_data:
            print(f"No table found on first page: {first_url}")
            return
        
        
        # Write headers and first page data
        write_to_csv(first_data, csv_file)
        print(f"Processed page 1/{len(links)}: {first_url}")
        
        # Process remaining pages
        for i, url in enumerate(links[1:], 2):
            try:
                html = read_cached_page(url, cache_dir)
                data = parse_table(html, url)
                          
                if data and len(data) > 1:  # Skip header row, append only data rows
                    write_to_csv(data[1:], csv_file, append=True)
                    print(f"Processed page {i}/{len(links)}: {url}")
                else:
                    print(f"No table found on page {i}/{len(links)}: {url}")
                    
            except Exception as e:
                print(f"Error processing {url}: {e}")
        
        print(f"All done! Results saved to {csv_file}")
        
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()