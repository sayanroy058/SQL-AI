// Main JavaScript file for common functionality

// Initialize tooltips and popovers if Bootstrap is present
document.addEventListener('DOMContentLoaded', function() {
  // Initialize Bootstrap tooltips
  if (typeof bootstrap !== 'undefined') {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
      return new bootstrap.Popover(popoverTriggerEl);
    });
  }

  // Animate flash messages to fade out after 5 seconds
  const flashMessages = document.querySelectorAll('.alert:not(.alert-error)');
  if (flashMessages.length > 0) {
    setTimeout(() => {
      flashMessages.forEach(message => {
        message.classList.remove('show');
        setTimeout(() => {
          message.remove();
        }, 500);
      });
    }, 5000);
  }
});

// Handle form validation errors with Bootstrap styling
function handleFormErrors(form, errors) {
  // Clear previous errors
  const errorElements = form.querySelectorAll('.is-invalid');
  errorElements.forEach(el => el.classList.remove('is-invalid'));
  const feedbackElements = form.querySelectorAll('.invalid-feedback');
  feedbackElements.forEach(el => el.remove());

  // Add new errors
  Object.keys(errors).forEach(field => {
    const inputElement = form.querySelector(`[name="${field}"]`);
    if (inputElement) {
      inputElement.classList.add('is-invalid');
      
      // Create error feedback element
      const feedbackElement = document.createElement('div');
      feedbackElement.classList.add('invalid-feedback');
      feedbackElement.textContent = errors[field];
      
      // Insert after input
      inputElement.parentNode.insertBefore(feedbackElement, inputElement.nextSibling);
    }
  });
}

// Function to copy text to clipboard
function copyToClipboard(text) {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'absolute';
  textarea.style.left = '-9999px';
  document.body.appendChild(textarea);
  
  textarea.select();
  document.execCommand('copy');
  
  document.body.removeChild(textarea);
}

// Function to display a toast notification
function showToast(message, type = 'success') {
  // Create toast container if it doesn't exist
  let toastContainer = document.querySelector('.toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.classList.add('toast-container', 'position-fixed', 'bottom-0', 'end-0', 'p-3');
    document.body.appendChild(toastContainer);
  }
  
  // Create toast
  const toast = document.createElement('div');
  toast.classList.add('toast', 'align-items-center', 'text-white', `bg-${type}`, 'border-0');
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');
  toast.setAttribute('aria-atomic', 'true');
  
  // Create toast content
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        ${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;
  
  // Add to container
  toastContainer.appendChild(toast);
  
  // Initialize and show toast
  const bsToast = new bootstrap.Toast(toast);
  bsToast.show();
  
  // Remove after it's hidden
  toast.addEventListener('hidden.bs.toast', () => {
    toast.remove();
  });
}
