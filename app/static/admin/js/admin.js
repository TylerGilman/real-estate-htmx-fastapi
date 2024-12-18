// static/admin/js/admin.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all sections
    initializeSections();
    
    // Add keyboard handlers
    initializeKeyboardHandlers();
    
    // Add click outside handlers
    initializeClickOutsideHandlers();
});

function initializeSections() {
    document.querySelectorAll('.admin-section').forEach(section => {
        const toggle = section.querySelector('.toggle-button');
        const content = document.getElementById(toggle.dataset.target);
        
        // Set initial state
        toggle.setAttribute('aria-expanded', 'true');
        content.classList.remove('collapsed');
        
        // Add toggle handler
        toggle.addEventListener('click', () => toggleSection(toggle, content));
    });
}

function toggleSection(button, content) {
    const isExpanded = button.getAttribute('aria-expanded') === 'true';
    
    button.setAttribute('aria-expanded', !isExpanded);
    content.classList.toggle('collapsed');
    
    // Update icon
    const icon = button.querySelector('.toggle-icon');
    icon.style.transform = isExpanded ? 'rotate(0deg)' : 'rotate(-180deg)';
    
    // If collapsing, also hide any visible forms
    if (isExpanded) {
        content.querySelectorAll('.form-container').forEach(form => {
            form.classList.add('hidden');
        });
    }
}

function toggleForm(containerId, formType, propertyId = null) {
    const container = document.getElementById(containerId);
    
    // If closing the form
    if (container.classList.contains('hidden')) {
        // Show container and load appropriate form
        container.classList.remove('hidden');
        
        const url = `/admin/properties/form?form_type=${formType}` + 
                   (propertyId ? `&property_id=${propertyId}` : '');
                   
        htmx.ajax('GET', url, {target: `#${containerId}`});
    } else {
        // If opening add form while edit form is open, or vice versa,
        // load the new form
        const currentFormType = container.querySelector('input[name="form_type"]').value;
        if (currentFormType !== formType) {
            const url = `/admin/properties/form?form_type=${formType}`;
            htmx.ajax('GET', url, {target: `#${containerId}`});
        }
        
        // Otherwise just hide the container
        container.classList.add('hidden');
    }
}

function cancelForm(containerId, defaultFormType) {
    const container = document.getElementById(containerId);
    
    // Load the default (add) form
    const url = `/admin/properties/form?form_type=${defaultFormType}`;
    htmx.ajax('GET', url, {
        target: `#${containerId}`,
        swap: 'innerHTML'
    });
    
    // Hide the container
    container.classList.add('hidden');
}

function initializeKeyboardHandlers() {
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            // Hide all forms
            document.querySelectorAll('.form-container').forEach(form => {
                form.classList.add('hidden');
            });
        }
    });
}

function initializeClickOutsideHandlers() {
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.form-container') && 
            !event.target.closest('.action-button')) {
            document.querySelectorAll('.form-container').forEach(form => {
                form.classList.add('hidden');
            });
        }
    });
}

// Handle form submission success
document.body.addEventListener('htmx:afterSwap', function(event) {
    if (event.detail.target.id === 'toast-container') {
        const toast = event.detail.target.querySelector('.toast');
        if (toast && toast.classList.contains('success')) {
            // Hide all forms on successful submission
            document.querySelectorAll('.form-container').forEach(form => {
                form.classList.add('hidden');
                if (form instanceof HTMLFormElement) {
                    form.reset();
                }
            });
        }
    }
});

function togglePropertyDetails(propertyType) {
    const residentialDetails = document.getElementById('residential-details');
    const commercialDetails = document.getElementById('commercial-details');
    
    if (propertyType === 'RESIDENTIAL') {
        residentialDetails.classList.remove('hidden');
        commercialDetails.classList.add('hidden');
    } else if (propertyType === 'COMMERCIAL') {
        residentialDetails.classList.add('hidden');
        commercialDetails.classList.remove('hidden');
    } else {
        residentialDetails.classList.add('hidden');
        commercialDetails.classList.add('hidden');
    }
}

// Price formatter
function formatPrice(input) {
    let value = input.value.replace(/[^\d]/g, '');
    if (value) {
        value = parseInt(value).toLocaleString('en-US');
        input.value = value;
    }
}

function togglePropertyTypeFields() {
    const propertyType = document.getElementById("propertyType");
    const residentialFields = document.getElementById("residentialFields");
    const commercialFields = document.getElementById("commercialFields");

    if (propertyType) {
        if (propertyType.value === "RESIDENTIAL") {
            residentialFields.classList.remove("hidden");
            commercialFields.classList.add("hidden");
        } else if (propertyType.value === "COMMERCIAL") {
            residentialFields.classList.add("hidden");
            commercialFields.classList.remove("hidden");
        } else {
            residentialFields.classList.add("hidden");
            commercialFields.classList.add("hidden");
        }
    }
}

// HTMX event handlers
document.addEventListener('htmx:afterSwap', function(evt) {
    // Toggle property type fields after form swap
    if (evt.detail.target.id === 'add-property-form') {
        const propertyType = document.getElementById("propertyType");
        if (propertyType) {
            togglePropertyTypeFields();
        }
        // Show form when editing
        evt.detail.target.classList.remove('hidden');
    }

    if (evt.detail.target.id === 'add-agent-form') {
        // Show form when editing
        evt.detail.target.classList.remove('hidden');
    }
});
