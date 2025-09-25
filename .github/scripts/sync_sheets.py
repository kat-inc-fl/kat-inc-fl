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

# All sheet names in your Google Sheets document
SHEET_NAMES = [
    "Korean American Adoptee Organizations",
    "International Korean Adoptee Organizations", 
    "Other Facebook Groups",
    "Live Discussion + Support Groups",
    "General Korean Adoptee Organizations",
    "Korean Adoptee Conferences",
    "Language Learning",
    "Birthland Tours",
    "Korean American Organizations",
    "Korean Culture Camps",
    "Korean Government Websites",
    "DNA Testing Companies",
    "Resource Hubs"
]

def get_sheet_names() -> List[str]:
    """Get all sheet names from the Google Sheets document."""
    
    # Method 1: Try to get sheet info from the spreadsheet feed
    try:
        # This endpoint sometimes returns sheet information
        feed_url = f"https://spreadsheets.google.com/feeds/worksheets/{SHEET_ID}/public/basic"
        response = requests.get(feed_url)
        if response.status_code == 200:
            content = response.text
            # Look for sheet titles in the feed
            title_pattern = r'<title[^>]*>([^<]+)</title>'
            titles = re.findall(title_pattern, content)
            if len(titles) > 1:  # First title is usually the document title
                sheet_names = [title.strip() for title in titles[1:] if title.strip()]
                if sheet_names:
                    print(f"Found sheets from feed: {sheet_names}")
                    return sheet_names
    except Exception as e:
        print(f"Feed method failed: {e}")
    
    # Method 2: Try to extract from the main sheet HTML
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        
        # More comprehensive regex patterns
        patterns = [
            r'"name":"([^"]+)","index":\d+,"sheetType":"GRID"',
            r'"sheets":\[[^\]]*"name":"([^"]+)"[^\]]*\]',
            r'data-params="[^"]*sheet=([^"&]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Clean and validate sheet names
                sheet_names = []
                for match in matches:
                    # URL decode if necessary
                    import urllib.parse
                    decoded = urllib.parse.unquote(match)
                    if decoded and not decoded.startswith('_') and len(decoded) > 1:
                        sheet_names.append(decoded)
                
                if sheet_names:
                    # Remove duplicates while preserving order
                    unique_names = []
                    for name in sheet_names:
                        if name not in unique_names:
                            unique_names.append(name)
                    print(f"Found sheets from HTML: {unique_names}")
                    return unique_names
                    
    except Exception as e:
        print(f"HTML parsing failed: {e}")
    
    # Method 3: Test known sheet names and common patterns
    print("Testing known sheet names...")
    potential_names = [
        "Korean American Adoptee Organizations",
        "Korean Adoptee Organizations", 
        "Organizations",
        "Resources",
        "Data",
        "Sheet1",
        "Sheet 1"
    ]
    
    found_sheets = []
    for name in potential_names:
        try:
            test_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={name}"
            response = requests.get(test_url)
            if response.status_code == 200 and response.text.strip():
                # Check if it's actual data (not an error page)
                if not response.text.startswith('Error') and ',' in response.text:
                    found_sheets.append(name)
                    print(f"✓ Found valid sheet: {name}")
        except:
            continue
    
    if found_sheets:
        return found_sheets
    
    # Last resort
    print("Warning: Could not discover any sheets, using fallback")
    return ["Korean American Adoptee Organizations"]

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
    
    # Use the predefined sheet names
    sheet_names = SHEET_NAMES
    print(f"Processing {len(sheet_names)} sheets: {sheet_names}")
    
    # Prepare output structure
    output = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "headings": {}
    }
    
    # Process each sheet
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
                
                # Count entries for this sheet
                sub_heading_entries = sum(len(entries) for entries in processed_data.get("sub_headings", {}).values())
                direct_entries = len(processed_data.get("direct_links", []))
                total_entries = sub_heading_entries + direct_entries
                
                summary_parts = []
                if processed_data.get("sub_headings"):
                    summary_parts.append(f"{sub_heading_entries} entries across {len(processed_data['sub_headings'])} sub-headings")
                if processed_data.get("direct_links"):
                    summary_parts.append(f"{direct_entries} direct entries")
                
                print(f"  - Found {total_entries} total entries ({', '.join(summary_parts)})")
            else:
                print(f"  - No data found for sheet: {sheet_name}")
        else:
            print(f"  - Could not fetch data for sheet: {sheet_name}")
    
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
    print(f"📊 Total headings: {len(output['headings'])}")
    
    # Print summary
    total_entries = 0
    for heading, data in output["headings"].items():
        sub_heading_entries = sum(len(entries) for entries in data.get("sub_headings", {}).values())
        direct_entries = len(data.get("direct_links", []))
        heading_entries = sub_heading_entries + direct_entries
        total_entries += heading_entries
        print(f"   - {heading}: {heading_entries} entries")
    
    print(f"📈 Total entries: {total_entries}")

if __name__ == "__main__":
    main()
