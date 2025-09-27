#!/usr/bin/env python3
"""
Fetch data from Google Sheets and convert to YAML for Jekyll site.
"""

import requests
import yaml
import re
from datetime import datetime
import os
from typing import Dict, List, Any, Optional

# Your Google Sheets document ID
SHEET_ID = "11OpF8wS5vUyeX4gAJZrMpB57RQ1vgmwygudmsffDQVQ"

def get_sheet_names() -> List[str]:
    """Get all sheet names from the Google Sheets document using multiple detection methods."""
    
    print("Attempting to discover sheet names...")
    
    # Method 1: Try the Sheets API-like endpoints
    try:
        # This endpoint sometimes works for public sheets
        api_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}?key=DUMMY&fields=sheets.properties.title"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'sheets' in data:
                sheet_names = [sheet['properties']['title'] for sheet in data['sheets']]
                if sheet_names:
                    print(f"✓ Found sheets via API endpoint: {sheet_names}")
                    return sheet_names
    except Exception as e:
        print(f"API method failed: {e}")
    
    # Method 2: Parse the main HTML page more thoroughly
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
        print(f"Fetching HTML from: {url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        content = response.text
        print(f"HTML content length: {len(content)} characters")
        
        # Modern approach: Look for the data structure that Google Sheets actually uses
        # Let's search for various patterns that might contain sheet information
        
        # Pattern 1: Look for sheet data in script tags or data attributes
        script_patterns = [
            r'window\._docs_chrome_config\s*=\s*({.+?});',
            r'window\._docs_wiz_model\s*=\s*({.+?});',
            r'bootstrapData:\s*({.+?}),',
            r'"sheets":\s*(\[.+?\])',
            r'"worksheets":\s*(\[.+?\])',
        ]
        
        for i, pattern in enumerate(script_patterns):
            print(f"Trying script pattern {i+1}: {pattern[:50]}...")
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                print(f"  Found {len(matches)} matches")
                for j, match in enumerate(matches[:3]):  # Check first 3 matches
                    print(f"  Match {j+1} preview: {match[:100]}...")
                    try:
                        # Try to parse as JSON
                        import json
                        data = json.loads(match)
                        
                        # Recursively search for sheet names in the JSON
                        def find_sheet_names(obj, path=""):
                            names = []
                            if isinstance(obj, dict):
                                # Look for sheet-like structures
                                if ('title' in obj or 'name' in obj) and ('sheetId' in obj or 'index' in obj or 'sheetType' in obj):
                                    # This looks like a sheet object
                                    title = obj.get('title') or obj.get('name')
                                    if isinstance(title, str) and len(title.strip()) > 0:
                                        title = title.strip()
                                        if not title.startswith('_'):  # Skip hidden sheets
                                            names.append(title)
                                            print(f"    Found sheet at {path}: '{title}'")
                                
                                # Continue searching recursively
                                for key, value in obj.items():
                                    if key in ['sheets', 'worksheets', 'tabs', 'sheetData'] and isinstance(value, list):
                                        for idx, item in enumerate(value):
                                            names.extend(find_sheet_names(item, f"{path}.{key}[{idx}]"))
                                    elif isinstance(value, (dict, list)):
                                        names.extend(find_sheet_names(value, f"{path}.{key}"))
                            elif isinstance(obj, list):
                                for idx, item in enumerate(obj):
                                    names.extend(find_sheet_names(item, f"{path}[{idx}]"))
                            return names
                        
                        found_names = find_sheet_names(data)
                        if found_names:
                            # Remove duplicates while preserving order
                            sheet_names = []
                            for name in found_names:
                                if name not in sheet_names:
                                    sheet_names.append(name)
                            
                            if sheet_names:
                                print(f"✓ Found sheet names: {sheet_names}")
                                return sheet_names
                        
                    except json.JSONDecodeError as e:
                        print(f"    JSON parsing failed: {e}")
                        continue
        
        # Pattern 2: Look for sheet names in HTML structure
        print("Trying HTML structure patterns...")
        specific_patterns = [
            (r'data-sheet-name="([^"]+)"', "data-sheet-name attribute"),
            (r'sheet-tab[^>]*>([^<]+)<', "sheet tab content"),
            (r'aria-label="[^"]*sheet[^"]*([^"]+)"', "aria-label with sheet"),
            (r'"title":"([^"]+)",".*?"sheetType":"GRID"', "title with sheetType"),
            (r'"name":"([^"]+)",".*?"sheetId":\d+', "name with sheetId"),
        ]
        
        for pattern, description in specific_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            print(f"Pattern '{description}': found {len(matches)} matches")
            if matches:
                print(f"  Sample matches: {matches[:10]}")
                
                # Filter matches that look like valid sheet names
                sheet_names = []
                for match in matches:
                    cleaned = match.strip()
                    if (len(cleaned) > 0 and 
                        not cleaned.startswith('_') and  # Skip hidden sheets
                        not cleaned.startswith('http') and  # Skip URLs
                        not cleaned.startswith('javascript:') and  # Skip JavaScript
                        not cleaned in ['true', 'false', 'null', 'undefined'] and  # Skip literals
                        not cleaned.isdigit() and  # Skip pure numbers
                        len(cleaned) < 200):  # Skip overly long strings that aren't sheet names
                        if cleaned not in sheet_names:
                            sheet_names.append(cleaned)
                
                if sheet_names:
                    print(f"✓ Found sheets via pattern '{description}': {sheet_names}")
                    return sheet_names[:20]  # Reasonable limit
                    
    except Exception as e:
        print(f"HTML parsing failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    # Method 3: Try the RSS/Atom feeds
    try:
        feed_url = f"https://spreadsheets.google.com/feeds/worksheets/{SHEET_ID}/public/basic"
        print(f"Trying RSS feed: {feed_url}")
        response = requests.get(feed_url, timeout=10)
        print(f"RSS response status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"RSS content length: {len(content)} characters")
            print(f"RSS content preview: {content[:300]}...")
            
            # Parse XML-like content for sheet titles
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(content)
                sheet_names = []
                
                # Look for entry titles (excluding the main document title)
                entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                print(f"Found {len(entries)} RSS entries")
                
                for i, entry in enumerate(entries):
                    title_elem = entry.find('.//{http://www.w3.org/2005/Atom}title')
                    if title_elem is not None and title_elem.text:
                        title = title_elem.text.strip()
                        print(f"  Entry {i+1}: '{title}'")
                        if title and title not in sheet_names:
                            sheet_names.append(title)
                
                if len(sheet_names) > 0:
                    print(f"✓ Found sheets via RSS feed: {sheet_names}")
                    return sheet_names
                    
            except ET.ParseError as e:
                print(f"XML parsing failed: {e}")
                # Try regex on the XML content
                title_pattern = r'<title[^>]*>([^<]+)</title>'
                titles = re.findall(title_pattern, content)
                print(f"Regex found {len(titles)} titles: {titles}")
                if len(titles) > 1:  # First is usually document title
                    sheet_names = [t.strip() for t in titles[1:] if t.strip()]
                    if sheet_names:
                        print(f"✓ Found sheets via RSS regex: {sheet_names}")
                        return sheet_names
        else:
            print(f"RSS feed returned status {response.status_code}")
                        
    except Exception as e:
        print(f"RSS feed method failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    # If we get here, all detection methods failed
    print("❌ ERROR: Could not detect any sheet names!")
    print("All auto-detection methods failed:")
    print("  - Google Sheets API endpoint")
    print("  - HTML page parsing") 
    print("  - RSS/Atom feed parsing")
    print("")
    print("This could be due to:")
    print("  - Network connectivity issues")
    print("  - Changes in Google Sheets structure") 
    print("  - The spreadsheet becoming private/restricted")
    print("  - Invalid spreadsheet ID")
    print("")
    print("Please check:")
    print("  1. That the spreadsheet is publicly accessible")
    print("  2. That the SHEET_ID is correct")
    print("  3. Your internet connection")
    
    # Return empty list to indicate failure
    return []

def fetch_sheet_data(sheet_name: str) -> List[List[str]]:
    """Fetch data from a specific sheet as CSV."""
    # First, decode any HTML entities in the sheet name
    import html
    decoded_name = html.unescape(sheet_name)
    
    # Then properly encode for URL
    import urllib.parse
    encoded_name = urllib.parse.quote(decoded_name, safe='')
    
    # URL to export specific sheet as CSV
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    
    print(f"  Original sheet name: '{sheet_name}'")
    if decoded_name != sheet_name:
        print(f"  HTML-decoded name: '{decoded_name}'")
    print(f"  URL-encoded name: '{encoded_name}'")
    print(f"  Fetching data from URL: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Check if we got an error response
        if response.text.strip().startswith('Error') or 'Invalid query' in response.text:
            print(f"  Error response from Google Sheets: {response.text[:100]}")
            return []
        
        # Parse CSV content
        lines = response.text.strip().split('\n')
        data = []
        
        for line in lines:
            # Simple CSV parsing (handles quoted fields)
            row = []
            in_quote = False
            current_field = ""
            
            i = 0
            while i < len(line):
                char = line[i]
                
                if char == '"':
                    if in_quote and i + 1 < len(line) and line[i + 1] == '"':
                        # Escaped quote
                        current_field += '"'
                        i += 1
                    else:
                        # Toggle quote state
                        in_quote = not in_quote
                elif char == ',' and not in_quote:
                    # End of field
                    row.append(current_field.strip())
                    current_field = ""
                else:
                    current_field += char
                
                i += 1
            
            # Add the last field
            row.append(current_field.strip())
            data.append(row)
        
        print(f"  Successfully fetched {len(data)} rows")
        return data
    
    except Exception as e:
        print(f"  Error fetching sheet '{sheet_name}': {e}")
        return []

def clean_url(url: str) -> Optional[str]:
    """Clean and validate URL."""
    if not url or url.strip() == "":
        return None
    
    url = url.strip()
    
    # Remove any surrounding quotes
    if url.startswith('"') and url.endswith('"'):
        url = url[1:-1]
    
    # Ensure URL starts with http:// or https://
    if not url.startswith(('http://', 'https://')):
        if url.startswith('www.'):
            url = 'https://' + url
        else:
            # Assume it's a valid URL without protocol
            url = 'https://' + url
    
    return url

def process_sheet_data(sheet_name: str, data: List[List[str]]) -> Dict[str, Any]:
    """Process raw sheet data into structured format."""
    if not data or len(data) < 2:  # Need at least header + one data row
        return {}
    
    # Skip header row
    rows = data[1:]
    
    sub_headings = {}
    direct_links = []
    
    for row in rows:
        if len(row) == 0 or not row[0].strip():
            continue  # Skip empty rows
        
        name = row[0].strip()
        if not name:
            continue
        
        # Get URL (column 2) if present
        url = None
        if len(row) > 1 and row[1].strip():
            url = clean_url(row[1])
        
        # Create entry
        entry = {"name": name}
        if url:
            entry["url"] = url
        
        # Check if there's a sub-heading (column 3)
        if len(row) > 2 and row[2].strip():
            sub_heading = row[2].strip()
            
            # Initialize sub-heading if it doesn't exist
            if sub_heading not in sub_headings:
                sub_headings[sub_heading] = []
            
            sub_headings[sub_heading].append(entry)
        else:
            # No sub-heading, add to direct links
            direct_links.append(entry)
    
    # Build result based on what we found
    result = {}
    if sub_headings:
        result["sub_headings"] = sub_headings
    if direct_links:
        result["direct_links"] = direct_links
    
    return result

def main():
    """Main function to fetch and convert Google Sheets data."""
    print("Starting Google Sheets sync...")
    
    # Try to automatically detect sheet names
    sheet_names = get_sheet_names()
    
    # Check if detection failed
    if not sheet_names:
        print("💥 FATAL ERROR: Sheet name detection failed!")
        print("Cannot proceed without knowing which sheets to process.")
        print("Please check the error messages above and fix the issues.")
        exit(1)
    
    print(f"✅ Successfully detected {len(sheet_names)} sheets: {sheet_names}")
    
    # Prepare output structure
    output = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "headings": {}
    }
    
    # Process each sheet
    successful_sheets = 0
    for sheet_name in sheet_names:
        if not sheet_name.strip():
            continue
            
        print(f"Processing sheet: {sheet_name}")
        
        # Fetch sheet data
        data = fetch_sheet_data(sheet_name)
        
        if data:
            # Process the data
            processed_data = process_sheet_data(sheet_name, data)
            if processed_data:  # Only add if there's actual data
                output["headings"][sheet_name] = processed_data
                successful_sheets += 1
                
                # Count entries for this sheet
                sub_heading_entries = sum(len(entries) for entries in processed_data.get("sub_headings", {}).values())
                direct_entries = len(processed_data.get("direct_links", []))
                total_entries = sub_heading_entries + direct_entries
                
                summary_parts = []
                if processed_data.get("sub_headings"):
                    summary_parts.append(f"{sub_heading_entries} entries across {len(processed_data['sub_headings'])} sub-headings")
                if processed_data.get("direct_links"):
                    summary_parts.append(f"{direct_entries} direct entries")
                
                print(f"  ✅ Found {total_entries} total entries ({', '.join(summary_parts)})")
            else:
                print(f"  ⚠️  No data found for sheet: {sheet_name}")
        else:
            print(f"  ❌ Could not fetch data for sheet: {sheet_name}")
    
    # Check if we got any data at all
    if successful_sheets == 0:
        print("💥 FATAL ERROR: No sheets were successfully processed!")
        print("All sheets either had no data or could not be fetched.")
        exit(1)
    
    # Ensure _data directory exists
    os.makedirs("_data", exist_ok=True)
    
    # Write to YAML file
    output_file = "_data/resources.yml"
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header comment
        f.write("# Auto-generated from Google Sheet\n")
        f.write(f"# Last updated: {output['last_updated']}\n")
        f.write("# DO NOT EDIT MANUALLY - This file is automatically generated\n\n")
        
        # Write YAML content
        yaml.dump(output, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"✅ Successfully wrote data to {output_file}")
    print(f"📊 Successfully processed {successful_sheets} of {len(sheet_names)} sheets")
    
    # Print summary
    total_entries = 0
    for heading, data in output["headings"].items():
        sub_heading_entries = sum(len(entries) for entries in data.get("sub_headings", {}).values())
        direct_entries = len(data.get("direct_links", []))
        heading_entries = sub_heading_entries + direct_entries
        total_entries += heading_entries
        print(f"   - {heading}: {heading_entries} entries")
    
    print(f"📈 Total entries: {total_entries}")
    
    if successful_sheets < len(sheet_names):
        print(f"⚠️  Warning: {len(sheet_names) - successful_sheets} sheets were not processed successfully")

if __name__ == "__main__":
    main()
