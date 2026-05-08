// Google Apps Script — Deploy as Web App
// 1. Tạo Google Sheet mới
// 2. Extensions → Apps Script → paste code này
// 3. Deploy → New deployment → Web app → Anyone can access
// 4. Copy URL → thay vào GOOGLE_SHEETS_WEBHOOK_URL trong index.html

function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var data = JSON.parse(e.postData.contents);
    
    // Header row (chạy 1 lần)
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(['Timestamp', 'Persona', 'Tên', 'Email', 'Công ty']);
    }
    
    sheet.appendRow([
      data.timestamp || new Date().toISOString(),
      data.persona || '',
      data.name || '',
      data.email || '',
      data.company || ''
    ]);
    
    return ContentService.createTextOutput(JSON.stringify({status: 'ok'}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch(err) {
    return ContentService.createTextOutput(JSON.stringify({status: 'error', message: err.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput('AI Literacy Webhook Active');
}
