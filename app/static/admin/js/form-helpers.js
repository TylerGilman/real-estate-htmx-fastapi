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
