/**
 * SKYsense AI - Image Upload & Prediction Interaction Script
 * Master's Degree Final Project Demonstration Grade
 */

document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('upload-dropzone');
    const fileInput = document.getElementById('image-file-input');
    const previewContainer = document.getElementById('preview-container');
    const previewImage = document.getElementById('preview-image');
    const filenameDisplay = document.getElementById('filename-display');
    const filesizeDisplay = document.getElementById('filesize-display');
    const dimensionDisplay = document.getElementById('dimension-display');
    const uploadPlaceholder = document.getElementById('upload-placeholder');
    const dropzoneErrorMsg = document.getElementById('dropzone-error-msg');
    const errorTextContent = document.getElementById('error-text-content');
    const removeBtn = document.getElementById('remove-image-btn');
    const submitBtn = document.getElementById('submit-predict-btn');
    const submitSpinner = document.getElementById('submit-spinner');
    const submitText = document.getElementById('submit-text');
    const predictForm = document.getElementById('prediction-form');
    const inferenceOverlay = document.getElementById('inference-loading-overlay');
    const modalStep1 = document.getElementById('modal-step-1');
    const modalStep2 = document.getElementById('modal-step-2');
    const modalStep3 = document.getElementById('modal-step-3');

    if (!dropzone || !fileInput) return;

    function showInlineError(msg) {
        if (dropzoneErrorMsg && errorTextContent) {
            errorTextContent.textContent = msg;
            dropzoneErrorMsg.classList.remove('hidden');
        }
    }

    function clearInlineError() {
        if (dropzoneErrorMsg) {
            dropzoneErrorMsg.classList.add('hidden');
        }
    }

    // Trigger file dialog on dropzone click
    dropzone.addEventListener('click', (e) => {
        if (e.target !== removeBtn && !removeBtn?.contains(e.target)) {
            fileInput.click();
        }
    });

    // Drag and drop event handlers
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dropzone-active');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dropzone-active');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            fileInput.files = files; // Sync input
            handleFile(files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFile(fileInput.files[0]);
        }
    });

    function handleFile(file) {
        clearInlineError();

        // Validate format
        const validExtensions = ['image/jpeg', 'image/png', 'image/jpg'];
        if (!validExtensions.includes(file.type)) {
            showInlineError(`Unsupported file format "${file.type || 'unknown'}". Please select a JPEG or PNG image.`);
            return;
        }

        // Validate size (15MB)
        const maxBytes = 15 * 1024 * 1024;
        if (file.size > maxBytes) {
            showInlineError(`File size (${(file.size / 1024 / 1024).toFixed(1)} MB) exceeds maximum permitted limit of 15 MB.`);
            return;
        }

        // Read and show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            filenameDisplay.textContent = file.name;
            filesizeDisplay.textContent = file.size > 1024 * 1024 
                ? `${(file.size / (1024 * 1024)).toFixed(2)} MB`
                : `${(file.size / 1024).toFixed(1)} KB`;

            // Extract dimensions
            previewImage.onload = () => {
                if (dimensionDisplay) {
                    dimensionDisplay.textContent = `${previewImage.naturalWidth} \u00D7 ${previewImage.naturalHeight} px`;
                }
            };

            uploadPlaceholder.classList.add('hidden');
            previewContainer.classList.remove('hidden');
            if (submitBtn) submitBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.value = '';
            previewImage.src = '';
            previewContainer.classList.add('hidden');
            uploadPlaceholder.classList.remove('hidden');
            clearInlineError();
            if (submitBtn) submitBtn.disabled = true;
        });
    }

    // Function to trigger full animated inference state
    function startInferenceAnimation(specimenLabel) {
        if (inferenceOverlay) {
            inferenceOverlay.classList.remove('hidden');

            // Staged progress indicators for demonstration
            setTimeout(() => {
                if (modalStep2) {
                    modalStep2.className = 'flex items-center gap-2 text-sky-400';
                    modalStep2.firstElementChild.className = 'w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse';
                }
            }, 600);

            setTimeout(() => {
                if (modalStep3) {
                    modalStep3.className = 'flex items-center gap-2 text-sky-400';
                    modalStep3.firstElementChild.className = 'w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse';
                }
            }, 1400);
        }
    }

    // Submit loading animation & state transition on upload form
    if (predictForm && submitBtn) {
        predictForm.addEventListener('submit', () => {
            if (submitSpinner) submitSpinner.classList.remove('hidden');
            if (submitText) submitText.textContent = 'Executing Inference...';
            submitBtn.style.pointerEvents = 'none';
            submitBtn.classList.add('opacity-80', 'cursor-wait');

            startInferenceAnimation('User Specimen');
        });
    }

    // Attach loading state to sample specimen forms as well
    const sampleForms = document.querySelectorAll('.sample-specimen-form');
    sampleForms.forEach(form => {
        form.addEventListener('submit', () => {
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="animate-spin inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full mr-1.5"></span> Analyzing...';
            }
            startInferenceAnimation(form.dataset.specimen || 'Sample Specimen');
        });
    });
});
