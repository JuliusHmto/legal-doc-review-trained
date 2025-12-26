/**
 * LegalGuard ID - Frontend Application Logic
 */

// State management
let currentStep = 'upload';
let documentId = null;
let trainingModule = null;
let complianceReport = null;

// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileStatus = document.getElementById('file-status');
const fileNameDisplay = document.querySelector('.file-name');
const startProcessBtn = document.getElementById('start-process-btn');
const startReviewBtn = document.getElementById('start-review-btn');
const systemStatus = document.getElementById('system-status');

// API Base URL (adjust if needed)
const API_BASE = '/api';

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    setupDragAndDrop();
    loadLawCategories();
});

// --- File Upload Logic ---
function setupDragAndDrop() {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, e => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    dropZone.addEventListener('dragover', () => dropZone.classList.add('drag-over'));
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));

    dropZone.addEventListener('drop', (e) => {
        dropZone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        handleFileSelection(file);
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        handleFileSelection(file);
    });

    document.getElementById('remove-file').addEventListener('click', () => {
        fileInput.value = '';
        fileStatus.classList.add('hidden');
        dropZone.classList.remove('hidden');
    });
}

function handleFileSelection(file) {
    if (!file) return;

    fileNameDisplay.textContent = file.name;
    fileStatus.classList.remove('hidden');
    dropZone.classList.add('hidden');
}

startProcessBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) return;

    try {
        showSection('processing');
        updateProgress(0, 'Uploading document...');

        // 1. Upload Document
        const formData = new FormData();
        formData.append('file', file);

        const uploadRes = await fetch(`${API_BASE}/documents/upload`, {
            method: 'POST',
            body: formData
        });

        if (!uploadRes.ok) throw new Error('Upload failed');
        const uploadData = await uploadRes.json();
        documentId = uploadData.id;

        updateProgress(30, 'Analyzing structure and creating training module...');

        // 2. Create Training Module
        const moduleRes = await fetch(`${API_BASE}/modules/create/${documentId}`, {
            method: 'POST'
        });

        if (!moduleRes.ok) throw new Error('Module creation failed');
        trainingModule = await moduleRes.json();

        updateProgress(100, 'Module ready!');

        setTimeout(() => {
            renderTrainingModule(trainingModule);
            showSection('module');
        }, 500);

    } catch (err) {
        console.error(err);
        alert('Error: ' + err.message);
        showSection('upload');
    }
});

// --- Training Module Logic ---
function renderTrainingModule(module) {
    const content = module.module_content;
    documentId = module.document_id;

    document.getElementById('doc-type-badge').textContent = content.document_type || 'Legal Document';
    document.getElementById('module-summary-text').textContent = content.summary || 'No summary available.';

    const partyList = document.getElementById('party-list');
    partyList.innerHTML = '';
    if (content.key_parties) {
        content.key_parties.forEach(party => {
            const span = document.createElement('span');
            span.className = 'badge';
            span.style.background = 'var(--glass-bg)';
            span.style.border = '1px solid var(--border)';
            span.textContent = party;
            partyList.appendChild(span);
        });
    }

    const clauseList = document.getElementById('clause-list');
    clauseList.innerHTML = '';
    if (content.clauses) {
        content.clauses.forEach(clause => {
            const div = document.createElement('div');
            div.className = 'clause-item';
            div.innerHTML = `
                <h4>${clause.clause_title} <span class="badge" style="font-size: 0.6rem">${clause.category}</span></h4>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem">${clause.clause_text.substring(0, 150)}...</p>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap">
                    ${clause.relevant_laws ? clause.relevant_laws.slice(0, 2).map(law => `<span class="badge" style="background: rgba(99, 102, 241, 0.2); color: var(--primary); text-transform: none">${law}</span>`).join('') : ''}
                </div>
            `;
            clauseList.appendChild(div);
        });
    }
}

async function loadLawCategories() {
    try {
        const res = await fetch(`${API_BASE}/laws/categories`);
        if (!res.ok) return;
        const categories = await res.json();

        const select = document.getElementById('focus-area-select');
        select.innerHTML = '<option value="">All Relevant Laws</option>';

        for (const [key, name] of Object.entries(categories)) {
            const opt = document.createElement('option');
            opt.value = key;
            opt.textContent = name;
            select.appendChild(opt);
        }
    } catch (err) {
        console.error('Failed to load law categories', err);
    }
}

// --- Compliance Review Logic ---
startReviewBtn.addEventListener('click', async () => {
    if (!documentId) return;

    const focusArea = document.getElementById('focus-area-select').value;
    const requestBody = focusArea ? { focus_areas: [focusArea] } : {};

    try {
        showSection('processing');
        document.getElementById('process-title').textContent = 'Analyzing Compliance...';
        document.getElementById('process-step').textContent = 'Comparing against up-to-date Indonesian law knowledge base.';
        updateProgress(10, 'Retrieving legal context via RAG...');

        const response = await fetch(`${API_BASE}/review/${documentId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) throw new Error('Compliance review failed');
        complianceReport = await response.json();

        updateProgress(100, 'Analysis complete!');

        setTimeout(() => {
            renderComplianceReport(complianceReport);
            showSection('report');
        }, 800);

    } catch (err) {
        console.error(err);
        alert('Error: ' + err.message);
        showSection('module');
    }
});

function renderComplianceReport(report) {
    // Render Score
    const score = report.compliance_score || 0;
    const circle = document.getElementById('score-circle-path');
    const scoreText = document.getElementById('score-text');
    const statusLabel = document.getElementById('status-label');

    scoreText.textContent = score;
    circle.style.strokeDasharray = `${score}, 100`;

    // Set color and status text
    if (score >= 90) {
        circle.style.stroke = 'var(--success)';
        statusLabel.textContent = 'COMPLIANT';
        statusLabel.style.color = 'var(--success)';
    } else if (score >= 70) {
        circle.style.stroke = 'var(--primary)';
        statusLabel.textContent = 'MOSTLY COMPLIANT';
        statusLabel.style.color = 'var(--primary)';
    } else if (score >= 50) {
        circle.style.stroke = 'var(--warning)';
        statusLabel.textContent = 'NEEDS REVIEW';
        statusLabel.style.color = 'var(--warning)';
    } else {
        circle.style.stroke = 'var(--danger)';
        statusLabel.textContent = 'NON-COMPLIANT';
        statusLabel.style.color = 'var(--danger)';
    }

    // Render Issues
    const issuesContainer = document.getElementById('issues-container');
    issuesContainer.innerHTML = '';

    if (report.issues && report.issues.length > 0) {
        report.issues.forEach(issue => {
            const div = document.createElement('div');
            div.className = `issue-card severity-${issue.severity.toLowerCase()}`;
            div.innerHTML = `
                <div class="issue-label" style="color: var(--${issue.severity === 'HIGH' ? 'danger' : issue.severity === 'MEDIUM' ? 'warning' : 'success'})">
                    ${issue.severity} RISK | ${issue.category}
                </div>
                <p style="font-weight: 600; margin-bottom: 0.5rem">${issue.description}</p>
                <p style="font-size: 0.85rem; color: var(--text-muted)"><strong>How to fix:</strong> ${issue.recommendation}</p>
                <div class="law-tag">${issue.law_reference}</div>
            `;
            issuesContainer.appendChild(div);
        });
    } else {
        issuesContainer.innerHTML = '<p class="glass">No critical issues identified.</p>';
    }

    // Render Recommendations
    const recList = document.getElementById('recommendations-list');
    recList.innerHTML = '';
    if (report.recommendations) {
        report.recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.textContent = rec;
            recList.appendChild(li);
        });
    }

    // Render Law References
    const lawRefContainer = document.getElementById('law-references-container');
    lawRefContainer.innerHTML = '';
    if (report.law_references) {
        report.law_references.forEach(ref => {
            const div = document.createElement('div');
            div.style.marginBottom = '0.5rem';
            div.innerHTML = `
                <strong style="font-size: 0.8rem; color: var(--primary)">${ref.law}</strong>
            `;
            lawRefContainer.appendChild(div);
        });
    }
}

// --- Navigation & UI Utilities ---
function showSection(sectionId) {
    document.querySelectorAll('section').forEach(s => s.classList.add('hidden'));
    document.getElementById(`${sectionId}-section`).classList.remove('hidden');
    document.getElementById(`${sectionId}-section`).classList.add('active');
}

function updateProgress(percent, status) {
    document.getElementById('main-progress').style.width = `${percent}%`;
    if (status) document.getElementById('process-step').textContent = status;
}

// Report Download (Mock)
document.getElementById('download-report-btn').addEventListener('click', () => {
    alert('Preparing PDF export... (Feature coming soon)');
});
