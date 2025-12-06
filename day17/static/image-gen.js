// ===========================================
// Day 17: Image Generation
// ===========================================

// Mode switching
document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const mode = btn.dataset.mode;

        // Update buttons
        document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update content
        document.querySelectorAll('.mode-content').forEach(c => c.classList.remove('active'));
        const modeContent = document.getElementById(`${mode}-mode`);
        if (modeContent) {
            modeContent.classList.add('active');
            modeContent.style.display = 'block';
        }

        // Hide non-active modes
        const otherMode = mode === 'rag' ? 'image' : 'rag';
        const otherContent = document.getElementById(`${otherMode}-mode`);
        if (otherContent) {
            otherContent.style.display = 'none';
        }
    });
});

// Image options toggle
const imageOptionsToggle = document.getElementById('image-options-toggle');
const imageOptionsContent = document.getElementById('image-options-content');

if (imageOptionsToggle && imageOptionsContent) {
    imageOptionsToggle.addEventListener('click', () => {
        imageOptionsContent.classList.toggle('visible');
        const arrow = imageOptionsToggle.querySelector('.arrow');
        if (arrow) {
            arrow.textContent = imageOptionsContent.classList.contains('visible') ? '▼' : '▶';
        }
    });
}

// Steps slider update
const stepsSlider = document.getElementById('image-steps');
const stepsValue = document.getElementById('steps-value');

if (stepsSlider && stepsValue) {
    stepsSlider.addEventListener('input', (e) => {
        const value = e.target.value;
        stepsValue.textContent = value === '0' ? 'default' : value;
    });
}

// Seed checkbox toggle
const useSeedCheckbox = document.getElementById('use-seed');
const seedInput = document.getElementById('image-seed');

if (useSeedCheckbox && seedInput) {
    useSeedCheckbox.addEventListener('change', (e) => {
        seedInput.disabled = !e.target.checked;
        if (e.target.checked) {
            seedInput.focus();
        }
    });
}

// Generate Image
const generateImageBtn = document.getElementById('generate-image-btn');
const imagePrompt = document.getElementById('image-prompt');

if (generateImageBtn && imagePrompt) {
    generateImageBtn.addEventListener('click', async () => {
        const prompt = imagePrompt.value.trim();

        if (!prompt) {
            showNotification('error', 'Please enter a prompt');
            return;
        }

        const model = document.getElementById('image-model').value;
        const size = document.getElementById('image-size').value;
        const steps = parseInt(document.getElementById('image-steps').value);
        const useSeed = document.getElementById('use-seed').checked;
        const seed = useSeed ? parseInt(document.getElementById('image-seed').value) : null;

        // Show loading state
        const originalText = generateImageBtn.innerHTML;
        generateImageBtn.disabled = true;
        generateImageBtn.innerHTML = '<span class="loading-spinner"></span> Generating...';

        // Clear previous results
        const resultsGrid = document.getElementById('results-grid');
        resultsGrid.innerHTML = '<div class="empty-state-full"><h3>Generating image...</h3><p>This may take 5-30 seconds depending on the model</p></div>';

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

            const payload = {
                prompt,
                model,
                size
            };

            if (steps > 0) {
                payload.steps = steps;
            }

            if (useSeed && seed) {
                payload.seed = seed;
            }

            const response = await fetch('/api/image/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (result.success && result.data) {
                displayImageResult(result.data);
                showNotification('success', 'Image generated successfully!');
            } else {
                throw new Error(result.error || 'Generation failed');
            }

        } catch (error) {
            console.error('Error generating image:', error);
            showNotification('error', `Failed to generate image: ${error.message}`);
            resultsGrid.innerHTML = `
                <div class="empty-state-full">
                    <h3>❌ Generation Failed</h3>
                    <p>${error.message}</p>
                </div>
            `;
        } finally {
            generateImageBtn.disabled = false;
            generateImageBtn.innerHTML = originalText;
        }
    });
}

// Display image result
function displayImageResult(data) {
    const resultsGrid = document.getElementById('results-grid');

    const imageHtml = `
        <div class="image-result">
            <img src="${data.image_url}" alt="${data.prompt}" />

            <div class="image-metadata">
                <div class="image-metadata-item">
                    <span class="image-metadata-label">Model</span>
                    <span class="image-metadata-value">${data.model}</span>
                </div>
                <div class="image-metadata-item">
                    <span class="image-metadata-label">Dimensions</span>
                    <span class="image-metadata-value">${data.image_dimensions.width}×${data.image_dimensions.height}</span>
                </div>
                <div class="image-metadata-item">
                    <span class="image-metadata-label">Latency</span>
                    <span class="image-metadata-value">${data.latency_seconds}s</span>
                </div>
                <div class="image-metadata-item">
                    <span class="image-metadata-label">Cost</span>
                    <span class="image-metadata-value">$${data.cost_estimate_usd.toFixed(4)}</span>
                </div>
                <div class="image-metadata-item">
                    <span class="image-metadata-label">Seed</span>
                    <span class="image-metadata-value">${data.parameters.actual_seed}</span>
                </div>
            </div>

            <div style="margin-top: 16px;">
                <strong>Prompt:</strong> ${data.prompt}
            </div>
        </div>
    `;

    resultsGrid.innerHTML = imageHtml;
}

// View Stats
const viewStatsBtn = document.getElementById('view-stats-btn');

if (viewStatsBtn) {
    viewStatsBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/image/stats');
            const result = await response.json();

            if (result.success && result.stats) {
                displayImageStats(result.stats);
                showNotification('success', 'Stats loaded');
            } else {
                throw new Error('Failed to load stats');
            }
        } catch (error) {
            console.error('Error loading stats:', error);
            showNotification('error', 'Failed to load stats');
        }
    });
}

// Display image stats
function displayImageStats(stats) {
    const resultsGrid = document.getElementById('results-grid');

    const statsHtml = `
        <div style="width: 100%;">
            <h3>📊 Generation Statistics</h3>
            <div class="image-stats">
                <div class="stat-card">
                    <div class="stat-card-value">${stats.total_requests}</div>
                    <div class="stat-card-label">Total Requests</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-value">${stats.successful_requests}</div>
                    <div class="stat-card-label">Successful</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-value">${stats.average_latency_seconds.toFixed(2)}s</div>
                    <div class="stat-card-label">Avg Latency</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-value">$${stats.total_cost_estimate_usd.toFixed(4)}</div>
                    <div class="stat-card-label">Total Cost</div>
                </div>
            </div>

            <div style="margin-top: 20px; padding: 20px; background: var(--card-bg); border-radius: 12px;">
                <h4>Models Used:</h4>
                <pre>${JSON.stringify(stats.models_used, null, 2)}</pre>
            </div>
        </div>
    `;

    resultsGrid.innerHTML = statsHtml;
}
