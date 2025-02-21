# Film Development Data Scraper

This tool scrapes and processes film development data from the Massive Dev Chart website. It extracts development times and conditions for various film and developer combinations, providing clean, structured data.

## Files and Execution Order

Execute the scripts in this order:

1. `get_urls.py`
2. `download_tables.py` 
3. `parse_tables.py`
4. `clean_data.py`

## File Descriptions

### 1. get_urls.py

Systematically searches the Massive Dev Chart website to collect URLs containing film development data.

**Features:**
- Generates all two-letter combinations ('aa' to 'zz') as search queries
- Uses multithreading for efficient searching
- Deduplicates and filters out JavaScript links
- Outputs unique development chart URLs to `unique_links.txt`

### 2. download_tables.py

Downloads HTML content from the collected URLs with robust error handling.

**Features:**
- Implements caching to avoid redundant downloads
- Respects server load with rate limiting and exponential backoff
- Handles encoding issues gracefully
- Stores downloaded pages in a `cache` directory

### 3. parse_tables.py  

Extracts structured data from the downloaded HTML pages.

**Features:**
- Handles malformed tables and inconsistent HTML
- Normalizes column count and headers
- Preserves source URLs for data provenance
- Consolidates all data into `all-film-all-developer.csv`

### 4. clean_data.py

Processes the raw scraped data into a clean, standardized format.

Do note, duplicates are expected, we are collecting records using both developer name and film name which will point to the same record so 50% duplication is expected. 

**Features:**
- Validates entries based on multiple criteria
- Standardizes temperature values to Celsius
- Handles development time ranges and two-stage development processes
- Separates valid and invalid data for quality control
- Provides summary statistics on data cleaning results

## Output Files

The process generates these files:
- `unique_links.txt`: All unique chart URLs
- `all-film-all-developer.csv`: Raw scraped data
- `valid_all-film-all-developer.csv`: Clean, validated development data
- `invalid_data.csv`: Rejected entries with validation failure reasons

## Use Cases

This tool is valuable for:
- Analyzing film development trends across different combinations
- Research on film development parameters and their relationships
