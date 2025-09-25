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
    """Get all sheet names from the Google Sheets document."""
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Extract sheet names from the HTML
        # This is a simple approach - in production you might want to use the Google Sheets API
        content = response.text
        
        # Look for sheet names in the HTML structure
        # This regex finds sheet names in the Google Sheets interface
        sheet_pattern = r'"sheets":\[([^\]]+)\]'
        name_pattern = r'"name":"([^"]+)"'
        
        sheets_match = re.search(sheet_pattern, content)
        if sheets_match:
            sheets_data = sheets_match.group(1)
            sheet_names = re.findall(name_pattern, sheets_data)
            return sheet_names
        
        # Fallback: try to get sheet names from tab structure
        tab_pattern = r'<div[^>]*class="[^"]*waffle-sheet-tab[^"]*"[^>]*>([^<]+)</div>'
        sheet_names = re.findall(tab_pattern, content)
        
        if sheet_names:
            return [name.strip() for name in sheet_names]
        
        # If we can't parse sheet names, default to the first sheet
        print("Warning: Could not parse sheet names, using default sheet")
        return ["Sheet1"]
        
    except Exception as e:
        print(f"Error getting sheet names: {e}")
        return ["Sheet1"]

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
        return {"sub_headings": {}}
    
    # Skip header row
    rows = data[1:]
    
    result = {"sub_headings": {}}
    
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
        
        # Get sub-heading (column 3) if present
        sub_heading = "General"  # Default sub-heading
        if len(row) > 2 and row[2].strip():
            sub_heading = row[2].strip()
        
        # Initialize sub-heading if it doesn't exist
        if sub_heading not in result["sub_headings"]:
            result["sub_headings"][sub_heading] = []
        
        # Create entry
        entry = {"name": name}
        if url:
            entry["url"] = url
        
        result["sub_headings"][sub_heading].append(entry)
    
    return result

def main():
    """Main function to fetch and convert Google Sheets data."""
    print("Starting Google Sheets sync...")
    
    # Get sheet names
    sheet_names = get_sheet_names()
    print(f"Found sheets: {sheet_names}")
    
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
            output["headings"][sheet_name] = processed_data
            
            # Count entries for this sheet
            total_entries = sum(len(entries) for entries in processed_data["sub_headings"].values())
            print(f"  - Found {total_entries} entries across {len(processed_data['sub_headings'])} sub-headings")
        else:
            print(f"  - No data found for sheet: {sheet_name}")
    
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
        heading_entries = sum(len(entries) for entries in data["sub_headings"].values())
        total_entries += heading_entries
        print(f"   - {heading}: {heading_entries} entries")
    
    print(f"📈 Total entries: {total_entries}")

if __name__ == "__main__":
    main()
