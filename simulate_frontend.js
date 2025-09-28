// Simulate the frontend JavaScript code to see what's happening
console.log("=== Simulating Frontend JavaScript Processing ===");

// Sample data that would be returned from the backend
const sampleData = {
  "summary_type": "weekly_summary",
  "weekly_summaries": [
    {
      "week_start": "2023-09-18",
      "date_range": "18 Sep 2023 to 24 Sep 2023",
      "summary": "**ACTIVITY OVERVIEW**: 15 messages from 3 participants during this week",
      "message_count": 15,
      "participant_count": 3,
      "most_active_user": "User A"
    },
    {
      "week_start": "2023-09-25",
      "date_range": "25 Sep 2023 to 01 Oct 2023",
      "summary": "**ACTIVITY OVERVIEW**: 8 messages from 2 participants during this week",
      "message_count": 8,
      "participant_count": 2,
      "most_active_user": "User B"
    },
    {
      "week_start": "2023-10-02",
      "date_range": "02 Oct 2023 to 08 Oct 2023",
      "summary": "Summary temporarily unavailable due to technical issues.",
      "message_count": 12,
      "participant_count": 4,
      "most_active_user": "User C"
    }
  ]
};

console.log(`Backend returned ${sampleData.weekly_summaries.length} weekly summaries`);

// This is the code that should be in the frontend
let content = '';
if (sampleData.weekly_summaries && sampleData.weekly_summaries.length > 0) {
  // Sort weeks by date to ensure proper chronological order
  const sortedWeeks = [...sampleData.weekly_summaries].sort((a, b) => {
    const dateA = new Date(a.week_start);
    const dateB = new Date(b.week_start);
    return dateA - dateB;
  });
  
  console.log(`Sorted weeks: ${sortedWeeks.length}`);
  
  content = sortedWeeks.map((week, index) => {
    // Format the summary content with proper structure
    let formattedSummary = week.summary || 'No summary content available';
    
    // Handle quota exceeded messages
    if (formattedSummary.includes('Summary temporarily unavailable due to technical issues')) {
      formattedSummary = `<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> ${formattedSummary}</div>`;
    } 
    // Handle structured format with sections (fallback summaries and normal AI summaries)
    else if (formattedSummary.includes('**ACTIVITY OVERVIEW**') || formattedSummary.includes('**MAIN DISCUSSION TOPICS**')) {
      // Format structured sections
      formattedSummary = formattedSummary
        .replace(/\*\*([^*]+)\*\*:/g, '<h4 style="color: var(--primary); margin: 1rem 0 0.5rem 0; font-weight: 600;">$1</h4>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong style="color: var(--primary);">$1</strong>')
        .replace(/\n/g, '<br>');
    } else {
      // Convert bullet points to proper HTML list
      if (formattedSummary.includes('*')) {
        const bulletPoints = formattedSummary
          .split('\n')
          .filter(line => line.trim().startsWith('*'))
          .map(line => line.replace(/^\*\s*/, '').trim())
          .filter(line => line.length > 0);
        
        if (bulletPoints.length > 0) {
          formattedSummary = '<ul>' + bulletPoints.map(point => `<li>${point}</li>`).join('') + '</ul>';
        }
      }
    }
    
    return `
      <div class="weekly-summary-item">
        <div class="weekly-summary-header">
          Week ${index + 1}: ${week.date_range} (${week.message_count} messages, ${week.participant_count} participants)
        </div>
        <div class="weekly-summary-content">${formattedSummary}</div>
      </div>
    `;
  }).join('');
  
  console.log("Generated content with", sortedWeeks.length, "weeks");
} else {
  content = '<div class="alert alert-info"><i class="fas fa-info-circle"></i> No weekly summaries available for the selected date range.</div>';
}

console.log("Final content length:", content.length);
console.log("Number of weekly-summary-item divs:", (content.match(/weekly-summary-item/g) || []).length);

// Now let's check what the actual frontend code looks like
console.log("\n=== Checking Actual Frontend Code ===");

// Read the actual frontend file and check the generateWeeklySummary function
const fs = require('fs');
const path = require('path');

const filePath = path.join('whatsapp_django', 'chatapp', 'templates', 'chatapp', 'react_dashboard.html');

try {
  const fileContent = fs.readFileSync(filePath, 'utf8');
  
  // Find the generateWeeklySummary function
  const functionStart = fileContent.indexOf('async function generateWeeklySummary()');
  if (functionStart !== -1) {
    const functionEnd = fileContent.indexOf('      }', functionStart) + 7;
    const functionCode = fileContent.substring(functionStart, functionEnd);
    
    console.log("Found generateWeeklySummary function");
    console.log("Function length:", functionCode.length);
    
    // Check for key components
    const checks = [
      {name: "Sorting", present: functionCode.includes("Sort weeks by date")},
      {name: "Week numbering", present: functionCode.includes("Week ${index + 1}:")},
      {name: "Quota handling", present: functionCode.includes("Summary temporarily unavailable")}
    ];
    
    checks.forEach(check => {
      const status = check.present ? "✅" : "❌";
      console.log(`${status} ${check.name}: ${check.present ? 'Present' : 'Missing'}`);
    });
  } else {
    console.log("❌ Could not find generateWeeklySummary function");
  }
} catch (error) {
  console.log("❌ Error reading frontend file:", error.message);
}