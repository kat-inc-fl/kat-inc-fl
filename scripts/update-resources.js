const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

// Configuration
const SPREADSHEET_ID = process.env.SPREADSHEET_ID;
const API_KEY = process.env.GOOGLE_SHEETS_API_KEY;

async function fetchSheetData() {
  try {
    console.log('Fetching data from Google Sheet...');
    
    // Initialize Google Sheets API
    const sheets = google.sheets({ version: 'v4', auth: API_KEY });
    
    // Get spreadsheet info to find all sheet names
    const spreadsheetInfo = await sheets.spreadsheets.get({
      spreadsheetId: SPREADSHEET_ID,
    });
    
    console.log(`Loaded spreadsheet: ${spreadsheetInfo.data.properties.title}`);
    
    const allData = {};
    
    // Process each sheet
    for (const sheet of spreadsheetInfo.data.sheets) {
      const sheetName = sheet.properties.title;
      console.log(`Processing sheet: ${sheetName}`);
      
      try {
        // Get data from this sheet
        const response = await sheets.spreadsheets.values.get({
          spreadsheetId: SPREADSHEET_ID,
          range: `'${sheetName}'!A:C`, // Get columns A, B, C
        });
        
        const rows = response.data.values || [];
        
        if (rows.length === 0) {
          console.log(`  No data found in ${sheetName}`);
          continue;
        }
        
        // Skip header row and process data
        const dataRows = rows.slice(1);
        const sheetData = [];
        
        for (const row of dataRows) {
          // Skip empty rows
          if (!row[0] && !row[1]) continue;
          
          const entry = {
            name: row[0] || '',
            url: row[1] || '',
            category: row[2] || ''
          };
          
          // Only add entries with at least a name or URL
          if (entry.name || entry.url) {
            sheetData.push(entry);
          }
        }
        
        console.log(`  Found ${sheetData.length} entries in ${sheetName}`);
        allData[sheetName] = sheetData;
        
      } catch (sheetError) {
        console.error(`Error processing sheet ${sheetName}:`, sheetError.message);
        continue;
      }
    }
    
    return allData;
    
  } catch (error) {
    console.error('Error fetching sheet data:', error);
    throw error;
  }
}

function generateYAML(data) {
  console.log('Generating YAML data file...');
  
  const yamlData = {
    last_updated: new Date().toISOString(),
    spreadsheet_id: SPREADSHEET_ID,
    sections: data
  };
  
  // Convert to YAML format manually (simple approach)
  let yamlContent = `# Auto-generated from Google Sheet
# Last updated: ${yamlData.last_updated}
# Spreadsheet ID: ${yamlData.spreadsheet_id}

last_updated: "${yamlData.last_updated}"
spreadsheet_id: "${yamlData.spreadsheet_id}"
sections:
`;

  Object.entries(data).forEach(([sheetName, entries]) => {
    if (entries.length === 0) return;
    
    yamlContent += `  "${sheetName}":\n`;
    
    entries.forEach(entry => {
      yamlContent += `    - name: "${entry.name}"\n`;
      yamlContent += `      url: "${entry.url}"\n`;
      yamlContent += `      category: "${entry.category}"\n`;
    });
  });
  
  return yamlContent;
}

async function main() {
  try {
    // Fetch data from Google Sheet
    const data = await fetchSheetData();
    
    // Generate YAML data file
    const yaml = generateYAML(data);
    const yamlPath = '_data/resources.yml';
    
    // Create _data directory if it doesn't exist
    const dataDir = path.dirname(yamlPath);
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
      console.log(`Created directory: ${dataDir}`);
    }
    
    fs.writeFileSync(yamlPath, yaml);
    console.log(`✅ Generated ${yamlPath}`);
    
    // Log summary
    const totalEntries = Object.values(data).reduce((sum, entries) => sum + entries.length, 0);
    console.log(`📊 Summary: ${Object.keys(data).length} sheets, ${totalEntries} total entries`);
    
  } catch (error) {
    console.error('❌ Error updating resources:', error);
    process.exit(1);
  }
}

// Run the script
main();
