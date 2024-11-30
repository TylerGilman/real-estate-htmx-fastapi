// Format SSN as user types
function formatSSN(input) {
    // Strip any non-numeric characters
    let value = input.value.replace(/\D/g, '');
    
    // Add hyphens at appropriate positions
    if (value.length > 5) {
        value = value.slice(0,3) + '-' + value.slice(3,5) + '-' + value.slice(5);
    } else if (value.length > 3) {
        value = value.slice(0,3) + '-' + value.slice(3);
    }
    
    // Limit to correct SSN length
    value = value.slice(0,11);
    
    input.value = value;
}

// Format phone number as user types
function formatPhoneNumber(input) {
    // Strip any non-numeric characters
    let value = input.value.replace(/\D/g, '');
    
    // Format as (XXX) XXX-XXXX
    if (value.length > 6) {
        value = '(' + value.slice(0,3) + ') ' + value.slice(3,6) + '-' + value.slice(6);
    } else if (value.length > 3) {
        value = '(' + value.slice(0,3) + ') ' + value.slice(3);
    } else if (value.length > 0) {
        value = '(' + value;
    }
    
    // Limit to correct phone number length
    value = value.slice(0,14);
    
    input.value = value;
}

// Add data validation before form submission
function validateAgentForm(form) {
    const ssn = form.querySelector('input[name="SSN"]');
    const nrds = form.querySelector('input[name="NRDS"]');
    const phone = form.querySelector('input[name="agent_phone"]');
    
    // Validate SSN format
    if (!/^\d{3}-\d{2}-\d{4}$/.test(ssn.value)) {
        showError(ssn, 'Please enter a valid SSN (XXX-XX-XXXX)');
        return false;
    }
    
    // Validate NRDS (7 digits)
    if (!/^\d{7}$/.test(nrds.value)) {
        showError(nrds, 'Please enter a valid 7-digit NRDS number');
        return false;
    }
    
    // Validate phone number
    if (!/^\(\d{3}\) \d{3}-\d{4}$/.test(phone.value)) {
        showError(phone, 'Please enter a valid phone number');
        return false;
    }
    
    return true;
}

function showError(input, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    // Remove any existing error messages
    const existing = input.parentNode.querySelector('.error-message');
    if (existing) {
        existing.remove();
    }
    
    input.parentNode.appendChild(errorDiv);
    input.focus();
    
    // Remove error message when input changes
    input.addEventListener('input', function() {
        errorDiv.remove();
    }, { once: true });
}


function formatSSN(input) {
    // Remove any non-numeric characters
    let value = input.value.replace(/\D/g, '');
    
    // Add dashes at appropriate positions
    if (value.length > 5) {
        value = value.slice(0,3) + '-' + value.slice(3,5) + '-' + value.slice(5);
    } else if (value.length > 3) {
        value = value.slice(0,3) + '-' + value.slice(3);
    }
    
    // Limit to correct SSN length
    value = value.slice(0,11);
    
    input.value = value;
}

function formatPhoneNumber(input) {
    // Remove any non-numeric characters
    let value = input.value.replace(/\D/g, '');
    
    // Format as (XXX) XXX-XXXX
    if (value.length > 6) {
        value = '(' + value.slice(0,3) + ') ' + value.slice(3,6) + '-' + value.slice(6);
    } else if (value.length > 3) {
        value = '(' + value.slice(0,3) + ') ' + value.slice(3);
    } else if (value.length > 0) {
        value = '(' + value;
    }
    
    // Limit to correct phone number length
    value = value.slice(0,14);
    
    input.value = value;
}

function validateClientForm(form) {
    // Get form elements
    const phone = form.querySelector('input[name="client_phone"]');
    const ssn = form.querySelector('input[name="SSN"]');
    const email = form.querySelector('input[name="client_email"]');
    
    // Validate phone format
    if (!/^\(\d{3}\) \d{3}-\d{4}$/.test(phone.value)) {
        showError(phone, 'Please enter a valid phone number');
        return false;
    }
    
    // Validate SSN format
    if (!/^\d{3}-\d{2}-\d{4}$/.test(ssn.value)) {
        showError(ssn, 'Please enter a valid SSN (XXX-XX-XXXX)');
        return false;
    }
    
    // Validate email format
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
        showError(email, 'Please enter a valid email address');
        return false;
    }
    
    return true;
}

function showError(input, message) {
    // Remove any existing error messages
    const existingError = input.parentNode.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Create and add new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    input.parentNode.appendChild(errorDiv);
    
    // Focus the input
    input.focus();
    
    // Remove error when input changes
    input.addEventListener('input', function() {
        errorDiv.remove();
    }, { once: true });
}

// Handle form toggling
function toggleForm(formId) {
    const form = document.getElementById(formId);
    form.classList.toggle('hidden');
}

function cancelForm() {
    document.querySelectorAll('.form-container').forEach(form => {
        form.classList.add('hidden');
    });
}

// Initialize all forms when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Add form validation to all client forms
    document.querySelectorAll('.client-form').forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateClientForm(this)) {
                event.preventDefault();
            }
        });
    });
});

// Add to your JavaScript file
document.body.addEventListener('htmx:afterSettle', function(evt) {
    if (evt.detail.elt.matches('form.client-form') && evt.detail.xhr.status === 200) {
        // Hide the form
        document.querySelector('.form-container').classList.add('hidden');
        
        // Show success message
        const toast = document.createElement('div');
        toast.className = 'toast success';
        toast.innerHTML = `
            <div class="toast-content">
                Client created successfully
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">×</button>
        `;
        document.getElementById('toast-container').appendChild(toast);
        
        // Remove toast after 3 seconds
        setTimeout(() => toast.remove(), 3000);
    }
});
