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
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        content = response.text
        
        # Look for the most reliable pattern: sheets array in JavaScript
        import json
        
        # Pattern 1: Find the sheets configuration in the page
        sheets_pattern = r'"sheets":\s*(\[[^\]]+\])'
        match = re.search(sheets_pattern, content)
        if match:
            try:
                # Try to parse as JSON
                sheets_json = match.group(1)
                sheets_data = json.loads(sheets_json)
                
                sheet_names = []
                for sheet in sheets_data:
                    if isinstance(sheet, dict) and 'properties' in sheet:
                        title = sheet['properties'].get('title')
                        if title and not title.startswith('_'):
                            sheet_names.append(title)
                
                if sheet_names:
                    print(f"✓ Found sheets via HTML JSON parsing: {sheet_names}")
                    return sheet_names
            except json.JSONDecodeError:
                pass
        
        # Pattern 2: Look for individual sheet name patterns
        name_patterns = [
            r'"name":"([^"]+)","sheetId":\d+',
            r'"title":"([^"]+)","sheetId":\d+',
            r'"sheetName":"([^"]+)"',
            r'data-params="[^"]*sheet=([^"&]+)',
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Filter and clean matches
                sheet_names = []
                for match in matches:
                    # URL decode and clean
                    import urllib.parse
                    decoded = urllib.parse.unquote(match)
                    # Filter out obvious non-sheet names
                    if (decoded and 
                        len(decoded) > 1 and 
                        not decoded.startswith('_') and
                        not decoded.startswith('http') and
                        not decoded in ['true', 'false', 'null']):
                        sheet_names.append(decoded)
                
                if sheet_names:
                    # Remove duplicates while preserving order
                    unique_names = []
                    for name in sheet_names:
                        if name not in unique_names:
                            unique_names.append(name)
                    
                    print(f"✓ Found sheets via pattern '{pattern}': {unique_names}")
                    return unique_names[:20]  # Reasonable limit
                    
    except Exception as e:
        print(f"HTML parsing failed: {e}")
    
    # Method 3: Try the RSS/Atom feeds
    try:
        feed_url = f"https://spreadsheets.google.com/feeds/worksheets/{SHEET_ID}/public/basic"
        response = requests.get(feed_url, timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # Parse XML-like content for sheet titles
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(content)
                sheet_names = []
                
                # Look for entry titles (excluding the main document title)
                for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                    title_elem = entry.find('.//{http://www.w3.org/2005/Atom}title')
                    if title_elem is not None and title_elem.text:
                        title = title_elem.text.strip()
                        if title and title not in sheet_names:
                            sheet_names.append(title)
                
                if len(sheet_names) > 0:
                    print(f"✓ Found sheets via RSS feed: {sheet_names}")
                    return sheet_names
                    
            except ET.ParseError:
                # Try regex on the XML content
                title_pattern = r'<title[^>]*>([^<]+)</title>'
                titles = re.findall(title_pattern, content)
                if len(titles) > 1:  # First is usually document title
                    sheet_names = [t.strip() for t in titles[1:] if t.strip()]
                    if sheet_names:
                        print(f"✓ Found sheets via RSS regex: {sheet_names}")
                        return sheet_names
                        
    except Exception as e:
        print(f"RSS feed method failed: {e}")
    
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
    # URL to export specific sheet as CSV
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
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
        
        return data
    
    except Exception as e:
        print(f"Error fetching sheet '{sheet_name}': {e}")
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
