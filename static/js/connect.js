// JavaScript for database connection form

document.addEventListener('DOMContentLoaded', function() {
  const testConnectionBtn = document.getElementById('testConnection');
  const connectionForm = document.getElementById('connectionForm');
  const connectionStatus = document.getElementById('connectionStatus');
  const connectionSpinner = document.getElementById('connectionSpinner');
  const connectionMessage = document.getElementById('connectionMessage');
  const dbTypeSelect = document.getElementById('dbTypeSelect');
  const portInput = connectionForm ? connectionForm.querySelector('[name="port"]') : null;
  
  if (!testConnectionBtn || !connectionForm) return;
  
  // Update default port based on database type selection
  if (dbTypeSelect && portInput) {
    // Set initial port based on selected database type
    updateDefaultPort(dbTypeSelect.value);
    
    // Update port when database type changes
    dbTypeSelect.addEventListener('change', function() {
      updateDefaultPort(this.value);
    });
  }
  
  function updateDefaultPort(dbType) {
    // Set appropriate default port based on database type
    if (dbType === 'postgresql') {
      portInput.value = '5432';
    } else if (dbType === 'mysql') {
      portInput.value = '3306';
    }
  }
  
  // Test connection button click handler
  testConnectionBtn.addEventListener('click', function() {
    // Validate required fields
    const host = connectionForm.querySelector('[name="host"]').value.trim();
    const username = connectionForm.querySelector('[name="username"]').value.trim();
    const password = connectionForm.querySelector('[name="password"]').value;
    const dbName = connectionForm.querySelector('[name="database_name"]').value.trim();
    const dbType = connectionForm.querySelector('[name="db_type"]').value;
    
    if (!host || !username || !dbName) {
      // Show error for missing fields
      connectionStatus.classList.remove('d-none');
      connectionSpinner.classList.add('d-none');
      connectionMessage.textContent = 'Please fill in all required fields (host, username, and database name).';
      connectionMessage.className = 'text-danger';
      return;
    }
    
    // Show connection status
    connectionStatus.classList.remove('d-none');
    connectionSpinner.classList.remove('d-none');
    connectionMessage.textContent = `Testing ${dbType.toUpperCase()} connection...`;
    connectionMessage.className = '';
    
    // Get form data
    const formData = new FormData(connectionForm);
    const csrfToken = formData.get('csrf_token');
    
    // Create connection data object
    const connectionData = {
      host: formData.get('host'),
      port: formData.get('port'),
      username: formData.get('username'),
      password: formData.get('password'),
      database_name: formData.get('database_name'),
      db_type: dbType
    };
    
    // Test connection via AJAX
    fetch('/test-connection', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify(connectionData)
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok: ' + response.status);
      }
      return response.json();
    })
    .then(data => {
      connectionSpinner.classList.add('d-none');
      
      if (data.success) {
        // Connection successful
        connectionMessage.innerHTML = `
          <div class="alert alert-success mb-0">
            <i class="bi bi-check-circle me-2"></i>
            ${data.message || `Connection successful! ${dbType.toUpperCase()} database contains ${data.tables.length} tables.`}
          </div>
        `;
        connectionMessage.className = '';
      } else {
        // Connection failed
        connectionMessage.innerHTML = `
          <div class="alert alert-danger mb-0">
            <i class="bi bi-exclamation-triangle me-2"></i>
            <strong>${dbType.toUpperCase()} connection failed:</strong> ${data.error}
          </div>
        `;
        connectionMessage.className = '';
        
        // Add specific tips based on database type and error
        if (dbType === 'mysql' && data.error && data.error.includes('Access denied')) {
          connectionMessage.innerHTML += `
            <div class="mt-2 small text-muted">
              <strong>Tip:</strong> If you're using a managed MySQL service (like Aiven, AWS RDS, etc.), 
              you might need to whitelist the Replit server's IP address in your database security settings.
            </div>
          `;
        } else if (dbType === 'postgresql' && data.error && data.error.includes('password authentication failed')) {
          connectionMessage.innerHTML += `
            <div class="mt-2 small text-muted">
              <strong>Tip:</strong> Check your PostgreSQL username and password. For Replit's built-in PostgreSQL, 
              the default credentials can be found in the environment variables (PGUSER, PGPASSWORD).
            </div>
          `;
        }
      }
    })
    .catch(error => {
      // Error during test
      connectionSpinner.classList.add('d-none');
      connectionMessage.innerHTML = `
        <div class="alert alert-danger mb-0">
          <i class="bi bi-exclamation-circle me-2"></i>
          Error testing connection: ${error.message}
        </div>
      `;
      connectionMessage.className = '';
    });
  });
  
  // Prevent form submission on Enter key in fields except textarea
  connectionForm.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
      e.preventDefault();
      return false;
    }
  });
});
