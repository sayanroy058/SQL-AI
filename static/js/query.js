// JavaScript for database query form

document.addEventListener('DOMContentLoaded', function() {
  const queryForm = document.getElementById('queryForm');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const resultContainer = document.getElementById('resultContainer');
  const sqlQuery = document.getElementById('sqlQuery');
  const resultData = document.getElementById('resultData');
  const resultExplanation = document.getElementById('resultExplanation');
  const copySqlBtn = document.getElementById('copySql');
  
  if (!queryForm) return;
  
  // Handle form submission
  queryForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Show loading indicator
    loadingIndicator.classList.remove('d-none');
    resultContainer.classList.add('d-none');
    
    // Get form data
    const formData = new FormData(queryForm);
    const csrfToken = formData.get('csrf_token');
    
    // Send query request
    fetch(queryForm.action, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken
      },
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      // Hide loading indicator
      loadingIndicator.classList.add('d-none');
      
      if (data.success) {
        // Display results
        resultContainer.classList.remove('d-none');
        
        // Display SQL query
        sqlQuery.textContent = data.sql;
        
        // Display result data
        if (Array.isArray(data.result) && data.result.length > 0) {
          // Create table for result data
          const table = document.createElement('table');
          table.className = 'table table-dark table-striped table-hover';
          
          // Create table header
          const thead = document.createElement('thead');
          const headerRow = document.createElement('tr');
          
          // Get column names from first result object
          const columns = Object.keys(data.result[0]);
          columns.forEach(column => {
            const th = document.createElement('th');
            th.textContent = column;
            headerRow.appendChild(th);
          });
          
          thead.appendChild(headerRow);
          table.appendChild(thead);
          
          // Create table body
          const tbody = document.createElement('tbody');
          
          // Add data rows
          data.result.forEach(row => {
            const tr = document.createElement('tr');
            
            columns.forEach(column => {
              const td = document.createElement('td');
              td.textContent = row[column] !== null ? row[column] : 'NULL';
              tr.appendChild(td);
            });
            
            tbody.appendChild(tr);
          });
          
          table.appendChild(tbody);
          
          // Add responsive wrapper
          const tableResponsive = document.createElement('div');
          tableResponsive.className = 'table-responsive';
          tableResponsive.appendChild(table);
          
          // Clear previous results and add new table
          resultData.innerHTML = '';
          resultData.appendChild(tableResponsive);
        } else if (data.result && data.result.affected_rows !== undefined) {
          // Display affected rows for non-SELECT queries
          resultData.innerHTML = `<div class="alert alert-info">
            <i class="bi bi-info-circle me-2"></i>
            Query executed successfully. ${data.result.affected_rows} rows affected.
          </div>`;
        } else {
          // No results
          resultData.innerHTML = `<div class="alert alert-warning">
            <i class="bi bi-exclamation-triangle me-2"></i>
            Query executed successfully, but returned no results.
          </div>`;
        }
        
        // Display explanation
        resultExplanation.textContent = data.explanation;
        
        // Add query to recent list
        addQueryToRecentList(data.query_id, formData.get('query'));
      } else {
        // Show error
        resultContainer.classList.add('d-none');
        showToast(data.error, 'danger');
      }
    })
    .catch(error => {
      // Hide loading indicator
      loadingIndicator.classList.add('d-none');
      
      // Show error toast
      showToast('Error processing query: ' + error.message, 'danger');
    });
  });
  
  // Copy SQL button handler
  if (copySqlBtn) {
    copySqlBtn.addEventListener('click', function() {
      const sql = sqlQuery.textContent;
      copyToClipboard(sql);
      showToast('SQL query copied to clipboard!');
    });
  }
  
  // Function to add a query to the recent list
  function addQueryToRecentList(queryId, queryText) {
    const recentQueries = document.getElementById('recentQueries');
    if (!recentQueries) return;
    
    // Truncate query text if too long
    const truncatedText = queryText.length > 40 ? queryText.substring(0, 40) + '...' : queryText;
    
    // Create new entry
    const listItem = document.createElement('a');
    listItem.href = `#query-${queryId}`;
    listItem.className = 'list-group-item list-group-item-action bg-dark border-secondary text-light px-0';
    
    // Format current time
    const now = new Date();
    const timeStr = now.getHours().toString().padStart(2, '0') + ':' + 
                   now.getMinutes().toString().padStart(2, '0');
    
    listItem.innerHTML = `
      <div class="d-flex w-100 justify-content-between">
        <span class="text-truncate">${truncatedText}</span>
        <small class="text-muted ms-2">${timeStr}</small>
      </div>
    `;
    
    // Add to the beginning of the list
    if (recentQueries.firstChild) {
      recentQueries.insertBefore(listItem, recentQueries.firstChild);
    } else {
      recentQueries.appendChild(listItem);
    }
    
    // Remove oldest if more than 5
    if (recentQueries.children.length > 5) {
      recentQueries.removeChild(recentQueries.lastChild);
    }
  }
});
