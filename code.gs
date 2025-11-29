var SPREADSHEET_ID = '1l0VjIg6YsqpFHGK_3AOdr-kPpN9ZtbmnChlNGO3JyHY';
var SHEET_NAME = 'created_accounts';

function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('index')
      .setTitle('Scratch Account Generator')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
      .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(SHEET_NAME);
    
    // Append row: kapan_dibuat, username, password, status
    sheet.appendRow([
      new Date(),
      data.username,
      data.password,
      'belum verifikasi'
    ]);
    
    return ContentService.createTextOutput(JSON.stringify({status: 'success'})).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({status: 'error', message: error.toString()})).setMimeType(ContentService.MimeType.JSON);
  }
}

function getAccounts() {
  var sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(SHEET_NAME);
  var data = sheet.getDataRange().getValues();
  // Remove header if exists, assuming row 1 is header
  if (data.length > 0) {
    data.shift(); 
  }
  return data;
}

function triggerExecutor() {
  var scriptProperties = PropertiesService.getScriptProperties();
  var githubToken = scriptProperties.getProperty('GITHUB_TOKEN');
  var repoOwner = 'ProjectAlpha'; // Update this to your actual GitHub username/org
  var repoName = 'scratch_maker'; // Update this to your actual repo name
  
  var url = 'https://api.github.com/repos/' + repoOwner + '/' + repoName + '/dispatches';
  
  var payload = {
    "event_type": "trigger_executor"
  };
  
  var options = {
    'method': 'post',
    'headers': {
      'Authorization': 'token ' + githubToken,
      'Accept': 'application/vnd.github.v3+json'
    },
    'contentType': 'application/json',
    'payload': JSON.stringify(payload)
  };
  
  try {
    UrlFetchApp.fetch(url, options);
    return { success: true, message: 'GitHub Action triggered successfully!' };
  } catch (e) {
    return { success: false, message: 'Failed to trigger GitHub Action: ' + e.message };
  }
}

function processVerification() {
  var logs = [];
  var sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(SHEET_NAME);
  var data = sheet.getDataRange().getValues();
  var verifiedEmails = [];

  try {
    // 1. Kriteria Pencarian
    var query = 'from:no-reply@scratch.mit.edu subject:"Confirm your Scratch account" is:unread';
    var threads = GmailApp.search(query, 0, 20);
    
    if (threads.length === 0) {
      logs.push("Tidak ada email verifikasi Scratch baru.");
      return { success: true, logs: logs };
    }

    // 2. Loop setiap email yang ditemukan
    for (var i = 0; i < threads.length; i++) {
      var messages = threads[i].getMessages();
      var message = messages[messages.length - 1]; 
      var body = message.getBody(); 
      var recipient = message.getTo(); // This might be the alias email
      
      // 3. Ekstrak Link menggunakan Regex
      var linkPattern = /https:\/\/scratch\.mit\.edu\/accounts\/email_verify\/[a-zA-Z0-9\-_]+(\?[a-zA-Z0-9=&]+)?/g;
      var match = body.match(linkPattern);
      
      if (match && match.length > 0) {
        var verifyUrl = match[0];
        
        try {
          // 4. "Kunjungi" link tersebut secara virtual
          var response = UrlFetchApp.fetch(verifyUrl);
          
          if (response.getResponseCode() == 200) {
            logs.push("Sukses verifikasi untuk email: " + recipient);
            threads[i].markRead();
            
            // Extract username from email alias if possible, or just mark based on timing/logic
            // Assuming email format: kalanantiacademics+username@gmail.com
            var usernameMatch = recipient.match(/\+(.*?)@/);
            if (usernameMatch && usernameMatch[1]) {
               verifiedEmails.push(usernameMatch[1]);
            }
            
          } else {
            logs.push("Gagal verifikasi (Status bukan 200): " + verifyUrl);
          }
          
        } catch (e) {
          logs.push("Error saat membuka link: " + e.message);
        }
      } else {
        logs.push("Link verifikasi tidak ditemukan di email ini.");
      }
    }
    
    // Update Spreadsheet Status
    if (verifiedEmails.length > 0) {
       for (var r = 1; r < data.length; r++) { // Start from 1 to skip header
         var rowUsername = data[r][1]; // Column B is username
         if (verifiedEmails.includes(rowUsername)) {
           sheet.getRange(r + 1, 4).setValue('email_verified'); // Column D is status
           logs.push("Updated status for " + rowUsername);
         }
       }
    }

  } catch (error) {
    logs.push("CRITICAL ERROR: " + error.toString());
    return { success: false, logs: logs };
  }
  
  return { success: true, logs: logs };
}
