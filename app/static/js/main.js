// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }
});

// Flash message auto-dismiss
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (!alert.classList.contains('alert-error')) {
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }, 5000);
        }
    });
});

// Dropdown menu positioning
document.addEventListener('DOMContentLoaded', function() {
    const userMenus = document.querySelectorAll('.user-menu');
    
    userMenus.forEach(menu => {
        const dropdown = menu.querySelector('.dropdown');
        if (dropdown) {
            // Ensure dropdown doesn't go off-screen
            function positionDropdown() {
                const rect = dropdown.getBoundingClientRect();
                if (rect.right > window.innerWidth) {
                    dropdown.style.right = '0';
                }
                if (rect.bottom > window.innerHeight) {
                    dropdown.style.bottom = '100%';
                    dropdown.style.top = 'auto';
                }
            }
            
            menu.addEventListener('mouseenter', positionDropdown);
        }
    });
});

// Form validation helpers
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            showError(input, 'This field is required');
        } else {
            clearError(input);
        }
    });
    
    return isValid;
}

function showError(input, message) {
    const formGroup = input.closest('.form-group');
    let errorDiv = formGroup.querySelector('.validation-message');
    
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'validation-message error';
        formGroup.appendChild(errorDiv);
    }
    
    errorDiv.textContent = message;
    input.classList.add('error');
}

function clearError(input) {
    const formGroup = input.closest('.form-group');
    const errorDiv = formGroup.querySelector('.validation-message');
    
    if (errorDiv) {
        errorDiv.remove();
    }
    input.classList.remove('error');
}

// Image preview helper
function createImagePreview(input, previewContainer) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.style.maxWidth = '200px';
            img.style.maxHeight = '200px';
            img.style.objectFit = 'contain';
            
            const removeBtn = document.createElement('button');
            removeBtn.textContent = 'Remove';
            removeBtn.className = 'btn-remove';
            removeBtn.onclick = function() {
                input.value = '';
                previewContainer.innerHTML = '';
            };
            
            previewContainer.innerHTML = '';
            previewContainer.appendChild(img);
            previewContainer.appendChild(removeBtn);
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

// AJAX helper
async function fetchJSON(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
} 