// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    // Drag-and-drop and file preview
    const dropArea = document.getElementById('drop-area');
    let fileInput = document.getElementById('file-input'); // made 'let' so we can reassign after clone
    const filePreview = document.getElementById('file-preview');

    if (dropArea && fileInput && filePreview) {
        dropArea.addEventListener('click', () => fileInput.click());

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.add('highlight'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.remove('highlight'), false);
        });

        dropArea.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            try {
                fileInput.files = files;
            } catch (err) {
                console.warn('Could not set file input programmatically', err);
            }
            showPreview();
        }

        fileInput.addEventListener('change', showPreview);

        function showPreview() {
            if (fileInput.files && fileInput.files.length > 0) {
                const file = fileInput.files[0];
                const size = (file.size / 1024 / 1024).toFixed(2);
                filePreview.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <span>${file.name} (${size} MB)</span>
                        <button type="button" class="btn btn-sm btn-outline-danger" id="remove-file-btn">Remove</button>
                    </div>
                `;
                const removeBtn = document.getElementById('remove-file-btn');
                if (removeBtn) {
                    removeBtn.addEventListener('click', () => {
                        fileInput.value = '';
                        const newInput = fileInput.cloneNode(true);
                        fileInput.parentNode.replaceChild(newInput, fileInput);
                        newInput.addEventListener('change', showPreview);
                        fileInput = newInput; // reassign reference
                        filePreview.innerHTML = '';
                    });
                }
            } else {
                filePreview.innerHTML = '';
            }
        }
    }

    // Form validation with file size check (UPDATED)
    const form = document.getElementById('document-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            const fi = document.getElementById('file-input');
            if (fi && fi.files && fi.files.length > 0) {
                const file = fi.files[0];
                const ext = file.name.split('.').pop().toLowerCase();
                const size = file.size / 1024 / 1024; // MB
                const MAX_FILE_SIZE_MB = 1024; // 1 GB limit

                if (!['pdf', 'doc', 'docx'].includes(ext)) {
                    alert('Invalid file type. Only PDF, DOC, DOCX allowed.');
                    e.preventDefault();
                    return;
                }
                if (size > MAX_FILE_SIZE_MB) {
                    alert(`File too large. Maximum ${MAX_FILE_SIZE_MB}MB allowed.`);
                    e.preventDefault();
                    return;
                }
            } else if (fi && fi.hasAttribute('required')) {
                alert('Please select a file.');
                e.preventDefault();
                return;
            }
        });
    }

    // Enhanced search with grid filtering
    const searchBar = document.getElementById('search-bar');
    if (searchBar) {
        searchBar.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const cards = document.querySelectorAll('.document-card');
            cards.forEach(card => {
                const text = card.textContent.toLowerCase();
                card.parentElement.style.display = text.includes(term) ? '' : 'none';
            });
            const emptyState = document.querySelector('.empty-state');
            if (emptyState) emptyState.style.display = term ? 'none' : '';
        });
    }

    // Delete confirmation
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            if (confirm('Are you sure? This action cannot be undone.')) {
                btn.closest('form').submit();
            }
        });
    });

    // Card hover animation
    document.querySelectorAll('.document-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-4px)';
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
        });
    });

    // Mobile sidebar auto-close
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            try {
                const sidebarEl = document.getElementById('sidebar');
                if (!sidebarEl) return;
                const sidebar = bootstrap.Offcanvas.getInstance(sidebarEl);
                if (sidebar) sidebar.hide();
            } catch (err) {
                // ignore
            }
        });
    });
});
