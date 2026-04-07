document.addEventListener('DOMContentLoaded', () => {
    const dropArea = document.getElementById('drop-area');
    const fileElem = document.getElementById('fileElem');
    const browseBtn = document.querySelector('.browse-btn');
    
    const uploadCard = document.querySelector('.upload-card');
    const loadingUI = document.getElementById('loading');
    const loadingTitle = document.getElementById('loading-title');
    const loadingSubtitle = document.getElementById('loading-subtitle');
    const loadingProgress = document.getElementById('loading-progress');
    const resultCard = document.getElementById('result-card');
    const resetBtn = document.getElementById('reset-btn');
    let loadingTimer = null;
    let loadingStartTime = 0;
    let loadingProgressValue = 8;

    // Drag and drop event listeners
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.classList.add('highlight');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.classList.remove('highlight');
        }, false);
    });

    dropArea.addEventListener('drop', handleDrop, false);
    
    // File input change logic
    fileElem.addEventListener('change', function() {
        if(this.files.length) handleFiles(this.files);
    });

    // Make browse button click the hidden input
    browseBtn.addEventListener('click', (e) => {
        e.preventDefault();
        fileElem.click();
    });

    resetBtn.addEventListener('click', resetUI);

    function handleDrop(e) {
        let dt = e.dataTransfer;
        let files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        const file = files[0];
        if (!file) return;
        
        // Basic validation
        const isTxt = file.type === "text/plain" || file.name.toLowerCase().endsWith('.txt');
        const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith('.pdf');
        const isImage = file.type.startsWith("image/") || /\.(png|jpg|jpeg)$/i.test(file.name);

        if (!isTxt && !isPdf && !isImage) {
            alert("Only PDF, TXT, PNG, JPG, and JPEG files are accepted.");
            return;
        }

        uploadFile(file);
    }

    async function uploadFile(file) {
        // Toggle UI
        dropArea.classList.add('hidden');
        loadingUI.classList.remove('hidden');
        startLoadingAnimation();

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/authenticate', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error || 'Server error occurred');

            await ensureMinimumLoadingTime(2200);
            stopLoadingAnimation();
            displayResult(data);
        } catch (error) {
            await ensureMinimumLoadingTime(1400);
            stopLoadingAnimation();
            alert("Analysis Failed: " + error.message);
            resetUI();
        }
    }

    function startLoadingAnimation() {
        const loadingPhases = [
            { title: 'Reading document...', subtitle: 'OCR and text extraction in progress' },
            { title: 'Building AI features...', subtitle: 'Validating fields and dosage consistency' },
            { title: 'Scoring authenticity...', subtitle: 'Running hybrid ML + rule checks' }
        ];
        loadingStartTime = Date.now();
        loadingProgressValue = 8;
        loadingProgress.style.width = loadingProgressValue + '%';
        loadingTitle.textContent = loadingPhases[0].title;
        loadingSubtitle.textContent = loadingPhases[0].subtitle;

        loadingTimer = setInterval(() => {
            if (loadingProgressValue < 92) {
                loadingProgressValue += 1.2;
                loadingProgress.style.width = Math.min(loadingProgressValue, 92) + '%';
            }

            if (loadingProgressValue < 34) {
                loadingTitle.textContent = loadingPhases[0].title;
                loadingSubtitle.textContent = loadingPhases[0].subtitle;
            } else if (loadingProgressValue < 68) {
                loadingTitle.textContent = loadingPhases[1].title;
                loadingSubtitle.textContent = loadingPhases[1].subtitle;
            } else {
                loadingTitle.textContent = loadingPhases[2].title;
                loadingSubtitle.textContent = loadingPhases[2].subtitle;
            }
        }, 180);
    }

    function stopLoadingAnimation() {
        if (loadingTimer) {
            clearInterval(loadingTimer);
            loadingTimer = null;
        }
        loadingProgress.style.width = '100%';
    }

    function ensureMinimumLoadingTime(minDurationMs) {
        const elapsed = Date.now() - loadingStartTime;
        const remaining = minDurationMs - elapsed;
        if (remaining > 0) {
            return new Promise((resolve) => setTimeout(resolve, remaining));
        }
        return Promise.resolve();
    }

    function displayResult(data) {
        // Hide loading
        uploadCard.classList.add('hidden');
        resultCard.classList.remove('hidden');

        // Set Badge
        const badge = document.getElementById('auth-badge');
        const isAuthentic = data.result === 'PROFESSIONAL';
        
        if (isAuthentic) {
            badge.className = 'badge professional';
            badge.innerHTML = '<i class="fa-solid fa-check-circle"></i> AUTHENTIC';
        } else {
            badge.className = 'badge suspicious';
            badge.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> SUSPICIOUS';
        }

        // Setup extracted data grid
        const grid = document.getElementById('data-grid');
        grid.innerHTML = ''; // Clear previous
        
        for (const [key, value] of Object.entries(data.extracted_data)) {
            const div = document.createElement('div');
            div.className = 'data-item';
            div.innerHTML = `
                <span class="label">${key.replace('_', ' ')}</span>
                <span class="value">${value}</span>
            `;
            grid.appendChild(div);
        }

        const reasonGrid = document.getElementById('reason-grid');
        reasonGrid.innerHTML = '';
        const reasonItems = Array.isArray(data.reasons) ? data.reasons : ['No explanation available'];

        reasonItems.forEach((reason) => {
            const div = document.createElement('div');
            div.className = 'data-item';
            div.innerHTML = `
                <span class="label">Reason</span>
                <span class="value">${reason}</span>
            `;
            reasonGrid.appendChild(div);
        });

        const scoreDiv = document.createElement('div');
        scoreDiv.className = 'data-item';
        scoreDiv.innerHTML = `
            <span class="label">ML Confidence</span>
            <span class="value">${(Number(data.confidence || 0) * 100).toFixed(2)}%</span>
        `;
        reasonGrid.appendChild(scoreDiv);

        const ruleDiv = document.createElement('div');
        ruleDiv.className = 'data-item';
        ruleDiv.innerHTML = `
            <span class="label">Rule Score</span>
            <span class="value">${data.rule_score ?? 'N/A'}</span>
        `;
        reasonGrid.appendChild(ruleDiv);
    }

    function resetUI() {
        stopLoadingAnimation();
        resultCard.classList.add('hidden');
        uploadCard.classList.remove('hidden');
        loadingUI.classList.add('hidden');
        dropArea.classList.remove('hidden');
        fileElem.value = ""; // Clear selected file
        loadingTitle.textContent = 'Analyzing report...';
        loadingSubtitle.textContent = 'Extracting text and validating medical structure';
        loadingProgress.style.width = '8%';
    }
});
