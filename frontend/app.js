/**
 * LegalGuard ID - Frontend Application Logic
 */

// State management
let currentStep = 'upload';
let documentId = null;
let trainingModule = null;
let complianceReport = null;
let cleanupResult = null;
let editorInstance = null;
let currentEditorLanguage = 'indonesian';

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
    initTheme();
    setupDragAndDrop();
    loadLawCategories();
    setupNavigation();
    setupCleanupSection();
    setupHistoryTabs();
    setupDocumentEditor();
});

// --- Theme Management ---
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark-theme';
    document.body.className = savedTheme;
    updateThemeUI(savedTheme);

    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
}

function toggleTheme() {
    const currentTheme = document.body.className;
    const newTheme = currentTheme === 'dark-theme' ? 'light-theme' : 'dark-theme';
    document.body.className = newTheme;
    localStorage.setItem('theme', newTheme);
    updateThemeUI(newTheme);
}

function updateThemeUI(theme) {
    const icon = document.getElementById('theme-icon');
    const text = document.getElementById('theme-text');
    if (theme === 'dark-theme') {
        icon.textContent = '🌙';
        text.textContent = 'Dark Mode';
    } else {
        icon.textContent = '☀️';
        text.textContent = 'Light Mode';
    }
}

// --- Navigation ---
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const nav = item.getAttribute('data-nav');

            // Update UI
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            // Show section
            if (nav === 'upload') showSection('upload');
            else if (nav === 'history') {
                showSection('history');
                loadHistory();
                loadCleanupHistory();
            }
            else if (nav === 'documents') {
                showSection('documents');
                loadDocuments();
            }
        });
    });

    document.getElementById('back-to-new-btn').addEventListener('click', () => {
        document.querySelector('[data-nav="upload"]').click();
    });
}

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

        // 1. Upload Document (this also triggers NDA cleanup analysis)
        const formData = new FormData();
        formData.append('file', file);

        const uploadRes = await fetch(`${API_BASE}/documents/upload`, {
            method: 'POST',
            body: formData
        });

        if (!uploadRes.ok) throw new Error('Upload failed');
        const uploadData = await uploadRes.json();
        documentId = uploadData.id;

        updateProgress(40, 'Running NDA cleanup analysis...');

        // 2. Fetch cleanup results
        try {
            const cleanupRes = await fetch(`${API_BASE}/cleanup/${documentId}`);
            if (cleanupRes.ok) {
                cleanupResult = await cleanupRes.json();
                updateProgress(70, 'Cleanup analysis complete!');
                
                // Show cleanup results first
                setTimeout(() => {
                    renderCleanupResults(cleanupResult);
                    showSection('cleanup');
                }, 500);
                return;
            }
        } catch (cleanupErr) {
            console.warn('Cleanup results not available:', cleanupErr);
        }

        // If no cleanup results, proceed directly to training module
        updateProgress(70, 'Analyzing structure and creating training module...');

        // 3. Create Training Module
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

// --- History & Documents Logic ---
async function loadHistory() {
    const tbody = document.getElementById('history-table-body');
    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem">Loading history...</td></tr>';

    try {
        const res = await fetch(`${API_BASE}/history`);
        const history = await res.json();

        if (history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state"><div class="empty-state-icon">📂</div>No history found. Start a new analysis!</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        history.forEach(item => {
            const tr = document.createElement('tr');
            const date = new Date(item.reviewed_at).toLocaleDateString();

            let badgeClass = 'status-review';
            if (item.status === 'COMPLIANT') badgeClass = 'status-compliant';
            else if (item.status === 'NON-COMPLIANT') badgeClass = 'status-danger';

            tr.innerHTML = `
                <td><strong>${item.filename}</strong></td>
                <td>${item.compliance_score}</td>
                <td><span class="status-badge ${badgeClass}">${item.status}</span></td>
                <td>${date}</td>
                <td><button class="btn btn-text" onclick="viewExistingReport('${item.document_id}')">View Report</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="5" style="color: var(--danger); text-align: center; padding: 2rem">Failed to load history</td></tr>';
    }
}

async function loadDocuments() {
    const tbody = document.getElementById('documents-table-body');
    tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 2rem">Loading documents...</td></tr>';

    try {
        const res = await fetch(`${API_BASE}/documents`);
        const docs = await res.json();

        if (docs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-state"><div class="empty-state-icon">📄</div>No documents uploaded yet.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        docs.forEach(doc => {
            const tr = document.createElement('tr');
            const date = new Date(doc.uploaded_at).toLocaleDateString();
            tr.innerHTML = `
                <td><strong>${doc.filename}</strong></td>
                <td>${doc.file_type.toUpperCase()}</td>
                <td>${date}</td>
                <td><button class="btn btn-text" onclick="reAnalyzeDocument('${doc.id}')">Analyze Again</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="4" style="color: var(--danger); text-align: center; padding: 2rem">Failed to load documents</td></tr>';
    }
}

window.viewExistingReport = async (docId) => {
    try {
        showSection('processing');
        document.getElementById('process-title').textContent = 'Loading Report...';
        document.getElementById('process-step').textContent = 'Fetching analysis from database.';

        documentId = docId;
        const res = await fetch(`${API_BASE}/review/${docId}/report`);
        if (!res.ok) throw new Error('Report not found');

        complianceReport = await res.json();
        renderComplianceReport(complianceReport);
        showSection('report');
    } catch (err) {
        alert(err.message);
        document.querySelector('[data-nav="history"]').click();
    }
};

window.reAnalyzeDocument = async (docId) => {
    try {
        showSection('processing');
        documentId = docId;

        const res = await fetch(`${API_BASE}/modules/${docId}`);
        if (!res.ok) throw new Error('Could not load document module');

        trainingModule = await res.json();
        renderTrainingModule(trainingModule);
        showSection('module');
    } catch (err) {
        alert(err.message);
        document.querySelector('[data-nav="documents"]').click();
    }
};

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
    document.querySelectorAll('section').forEach(s => {
        s.classList.add('hidden');
        s.classList.remove('active');
    });
    const section = document.getElementById(`${sectionId}-section`);
    if (section) {
        section.classList.remove('hidden');
        section.classList.add('active');
    }
}

function updateProgress(percent, status) {
    document.getElementById('main-progress').style.width = `${percent}%`;
    if (status) document.getElementById('process-step').textContent = status;
}

// Report Download (Mock)
document.getElementById('download-report-btn').addEventListener('click', () => {
    alert('Preparing PDF export... (Feature coming soon)');
});

// --- NDA Cleanup Section Logic ---

function setupCleanupSection() {
    // Language tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const lang = btn.getAttribute('data-lang');
            
            // Update active tab
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show corresponding content
            document.getElementById('cleaned-content-indonesian').classList.toggle('hidden', lang !== 'indonesian');
            document.getElementById('cleaned-content-english').classList.toggle('hidden', lang !== 'english');
        });
    });

    // Skip to module button
    document.getElementById('skip-to-module-btn').addEventListener('click', async () => {
        if (!documentId) return;
        
        try {
            showSection('processing');
            document.getElementById('process-title').textContent = 'Creating Training Module...';
            updateProgress(30, 'Analyzing document structure...');

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
            showSection('cleanup');
        }
    });

    // Re-run cleanup button
    document.getElementById('rerun-cleanup-btn').addEventListener('click', async () => {
        if (!documentId) return;
        
        try {
            showSection('processing');
            document.getElementById('process-title').textContent = 'Re-running Cleanup Analysis...';
            updateProgress(30, 'Analyzing document with LLM...');

            const res = await fetch(`${API_BASE}/cleanup/${documentId}/rerun`, {
                method: 'POST'
            });

            if (!res.ok) throw new Error('Cleanup failed');
            cleanupResult = await res.json();

            updateProgress(100, 'Analysis complete!');

            setTimeout(() => {
                renderCleanupResults(cleanupResult);
                showSection('cleanup');
            }, 500);
        } catch (err) {
            console.error(err);
            alert('Error: ' + err.message);
            showSection('cleanup');
        }
    });
}

function renderCleanupResults(result) {
    // Update stats badges
    const issues = result.issues || [];
    const changes = result.change_summary || [];
    const openItems = result.open_items || [];

    document.getElementById('cleanup-issue-count').textContent = `${issues.length} Issue${issues.length !== 1 ? 's' : ''}`;
    document.getElementById('cleanup-change-count').textContent = `${changes.length} Change${changes.length !== 1 ? 's' : ''}`;

    // Show/hide open items alert
    const openItemsAlert = document.getElementById('open-items-alert');
    if (openItems.length > 0) {
        openItemsAlert.classList.remove('hidden');
        const placeholders = openItems.map(item => item.placeholder).join(', ');
        document.getElementById('open-items-text').textContent = 
            `The following placeholders need your attention: ${placeholders}`;
    } else {
        openItemsAlert.classList.add('hidden');
    }

    // Render original content with highlighted issues
    const originalContent = document.getElementById('original-content');
    let originalText = result.original_content || '';
    
    // Highlight issues in original text
    issues.forEach(issue => {
        if (issue.original_text) {
            const escapedText = escapeHtml(issue.original_text);
            const highlightClass = getIssueHighlightClass(issue.type);
            originalText = originalText.replace(
                issue.original_text,
                `<mark class="${highlightClass}" title="${escapeHtml(issue.rule)}">${escapedText}</mark>`
            );
        }
    });
    
    originalContent.innerHTML = `<pre class="document-text">${formatDocumentText(originalText)}</pre>`;

    // Render cleaned Indonesian content
    const cleanedIndonesian = document.getElementById('cleaned-content-indonesian');
    cleanedIndonesian.innerHTML = `<pre class="document-text">${formatDocumentText(result.cleaned_indonesian || 'No Indonesian text available.')}</pre>`;

    // Render cleaned English content
    const cleanedEnglish = document.getElementById('cleaned-content-english');
    cleanedEnglish.innerHTML = `<pre class="document-text">${formatDocumentText(result.cleaned_english || 'No English text available.')}</pre>`;

    // Render issues list
    const issuesList = document.getElementById('cleanup-issues-list');
    issuesList.innerHTML = '';
    
    if (issues.length === 0) {
        issuesList.innerHTML = '<div class="empty-issues glass"><p>No issues found in this document.</p></div>';
    } else {
        issues.forEach(issue => {
            const div = document.createElement('div');
            div.className = `cleanup-issue-card issue-type-${issue.type || 'general'}`;
            div.innerHTML = `
                <div class="issue-type-badge">${formatIssueType(issue.type)}</div>
                <div class="issue-location">${escapeHtml(issue.location || 'Unknown location')}</div>
                <div class="issue-original-text">"${escapeHtml(truncateText(issue.original_text, 100))}"</div>
                <div class="issue-rule">${escapeHtml(issue.rule || 'General cleanup rule')}</div>
            `;
            issuesList.appendChild(div);
        });
    }

    // Render change summary
    const changeSummaryList = document.getElementById('change-summary-list');
    changeSummaryList.innerHTML = '';
    
    if (changes.length === 0) {
        changeSummaryList.innerHTML = '<li class="no-changes">No changes were necessary.</li>';
    } else {
        changes.forEach(change => {
            const li = document.createElement('li');
            li.innerHTML = `<span class="change-icon">✓</span> ${escapeHtml(change)}`;
            changeSummaryList.appendChild(li);
        });
    }
}

function getIssueHighlightClass(type) {
    const typeMap = {
        'terminology': 'highlight-terminology',
        'deletion': 'highlight-deletion',
        'formatting': 'highlight-formatting',
        'party_label': 'highlight-party',
        'arbitration': 'highlight-arbitration',
        'signature': 'highlight-signature'
    };
    return typeMap[type] || 'highlight-general';
}

function formatIssueType(type) {
    const typeMap = {
        'terminology': 'Terminology',
        'deletion': 'Deletion Required',
        'formatting': 'Formatting',
        'party_label': 'Party Label',
        'arbitration': 'Arbitration Clause',
        'signature': 'Signature'
    };
    return typeMap[type] || 'General';
}

function formatDocumentText(text) {
    if (!text) return '';
    // Preserve line breaks and basic formatting
    return text
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>')
        .replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// View cleanup results for existing document
window.viewCleanupResults = async (docId) => {
    try {
        showSection('processing');
        document.getElementById('process-title').textContent = 'Loading Cleanup Results...';
        document.getElementById('process-step').textContent = 'Fetching analysis from database.';

        documentId = docId;
        const res = await fetch(`${API_BASE}/cleanup/${docId}`);
        if (!res.ok) throw new Error('Cleanup results not found');

        cleanupResult = await res.json();
        renderCleanupResults(cleanupResult);
        showSection('cleanup');
    } catch (err) {
        alert(err.message);
        document.querySelector('[data-nav="documents"]').click();
    }
};

// ============ History Tabs Logic ============

function setupHistoryTabs() {
    document.querySelectorAll('.history-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.getAttribute('data-history-tab');
            
            // Update active tab
            document.querySelectorAll('.history-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Show corresponding content
            document.querySelectorAll('.history-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            if (tabName === 'compliance') {
                document.getElementById('compliance-history-content').classList.add('active');
            } else if (tabName === 'cleanup') {
                document.getElementById('cleanup-history-content').classList.add('active');
            }
        });
    });
}

async function loadCleanupHistory() {
    const tbody = document.getElementById('cleanup-history-table-body');
    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem">Loading cleanup history...</td></tr>';

    try {
        const res = await fetch(`${API_BASE}/cleanup/history`);
        const history = await res.json();

        if (history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state"><div class="empty-state-icon">📋</div>No NDA cleanup analyses found. Upload a document to get started!</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        history.forEach(item => {
            const tr = document.createElement('tr');
            const date = new Date(item.created_at).toLocaleDateString();

            tr.innerHTML = `
                <td><strong>${item.filename}</strong></td>
                <td><span class="cleanup-issue-badge">${item.issue_count} Issue${item.issue_count !== 1 ? 's' : ''}</span></td>
                <td><span class="cleanup-change-badge">${item.change_count} Change${item.change_count !== 1 ? 's' : ''}</span></td>
                <td>${date}</td>
                <td>
                    <button class="btn btn-text" onclick="viewCleanupResults('${item.document_id}')">View Cleanup</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="5" style="color: var(--danger); text-align: center; padding: 2rem">Failed to load cleanup history</td></tr>';
    }
}

// ============ Document Editor Logic ============

function setupDocumentEditor() {
    // Edit document button
    document.getElementById('edit-document-btn').addEventListener('click', () => {
        if (!cleanupResult) return;
        openDocumentEditor();
    });

    // Back to cleanup button
    document.getElementById('back-to-cleanup-btn').addEventListener('click', () => {
        destroyEditor();
        showSection('cleanup');
    });

    // Save document button
    document.getElementById('save-document-btn').addEventListener('click', saveEditedDocument);

    // Export DOCX button
    document.getElementById('export-docx-btn').addEventListener('click', exportToDocx);

    // Editor language tabs
    document.querySelectorAll('.editor-lang-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const lang = btn.getAttribute('data-editor-lang');
            switchEditorLanguage(lang);
        });
    });
}

function openDocumentEditor() {
    showSection('editor');
    currentEditorLanguage = 'indonesian';
    
    // Update language tab UI
    document.querySelectorAll('.editor-lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-editor-lang') === currentEditorLanguage);
    });
    
    // Initialize Quill with the cleaned content
    initQuillEditor();
}

function initQuillEditor() {
    // Destroy existing instance if any
    destroyEditor();
    
    // Get the content to load
    const content = currentEditorLanguage === 'indonesian' 
        ? (cleanupResult.edited_indonesian || cleanupResult.cleaned_indonesian || '')
        : (cleanupResult.edited_english || cleanupResult.cleaned_english || '');
    
    // Convert plain text to HTML if needed
    const htmlContent = convertTextToHtml(content);
    
    // Initialize Quill
    editorInstance = new Quill('#document-editor', {
        theme: 'snow',
        modules: {
            toolbar: [
                [{ 'header': [1, 2, 3, false] }],
                ['bold', 'italic', 'underline', 'strike'],
                [{ 'align': [] }],
                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                [{ 'indent': '-1'}, { 'indent': '+1' }],
                ['blockquote'],
                [{ 'color': [] }, { 'background': [] }],
                ['link', 'image'],
                ['clean']
            ]
        }
    });

    // Set content
    editorInstance.clipboard.dangerouslyPasteHTML(htmlContent);
    
    // Setup event handlers
    editorInstance.on('text-change', function() {
        updateWordCount();
        updateEditorStatus('Unsaved changes');
    });

    updateWordCount();
    updateEditorStatus('Ready');
}

function destroyEditor() {
    if (editorInstance) {
        // Quill doesn't have a formal destroy method like TinyMCE, 
        // but we can clear the container and remove the toolbar
        const editorContainer = document.getElementById('document-editor');
        if (editorContainer) {
            editorContainer.innerHTML = '';
            // Remove the toolbar added by Quill
            const toolbar = document.querySelector('.ql-toolbar');
            if (toolbar) {
                toolbar.remove();
            }
        }
        editorInstance = null;
    }
}

function switchEditorLanguage(lang) {
    // Save current content before switching
    if (editorInstance && cleanupResult) {
        const currentContent = editorInstance.root.innerHTML;
        if (currentEditorLanguage === 'indonesian') {
            cleanupResult.edited_indonesian = currentContent;
        } else {
            cleanupResult.edited_english = currentContent;
        }
    }
    
    currentEditorLanguage = lang;
    
    // Update language tab UI
    document.querySelectorAll('.editor-lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-editor-lang') === lang);
    });
    
    // Reinitialize editor with new language content
    initQuillEditor();
}

async function saveEditedDocument() {
    if (!editorInstance || !documentId) return;
    
    updateEditorStatus('Saving...', 'saving');
    
    try {
        const content = editorInstance.root.innerHTML;
        
        const res = await fetch(`${API_BASE}/cleanup/${documentId}/save`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content_html: content,
                language: currentEditorLanguage
            })
        });
        
        if (!res.ok) throw new Error('Failed to save document');
        
        // Update local state
        const savedResult = await res.json();
        if (currentEditorLanguage === 'indonesian') {
            cleanupResult.edited_indonesian = content;
        } else {
            cleanupResult.edited_english = content;
        }
        
        updateEditorStatus('Saved successfully', 'saved');
        
        // Reset status after 3 seconds
        setTimeout(() => updateEditorStatus('Ready'), 3000);
        
    } catch (err) {
        console.error(err);
        updateEditorStatus('Error saving', 'error');
        alert('Failed to save document: ' + err.message);
    }
}

function exportToDocx() {
    if (!editorInstance) return;
    
    const content = editorInstance.root.innerHTML;
    const filename = `document_${currentEditorLanguage}_${new Date().toISOString().split('T')[0]}.html`;
    
    // Create a complete HTML document
    const htmlDoc = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Legal Document</title>
    <style>
        body {
            font-family: 'Times New Roman', Times, serif;
            font-size: 12pt;
            line-height: 1.6;
            margin: 1in;
        }
        h1 { font-size: 18pt; font-weight: bold; }
        h2 { font-size: 14pt; font-weight: bold; }
        h3 { font-size: 12pt; font-weight: bold; }
        p { text-align: justify; }
        table { border-collapse: collapse; width: 100%; }
        table td, table th { border: 1px solid #000; padding: 6pt; }
    </style>
</head>
<body>
${content}
</body>
</html>`;
    
    // Create download
    const blob = new Blob([htmlDoc], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    // Show instructions for converting to DOCX
    alert('HTML file downloaded. To convert to DOCX:\n\n1. Open the HTML file in Microsoft Word\n2. Save As > Word Document (.docx)\n\nOr use an online converter like CloudConvert.');
}

function convertTextToHtml(text) {
    if (!text) return '<p></p>';
    
    // If it already looks like HTML, return as is
    if (text.trim().startsWith('<')) {
        return text;
    }
    
    // Convert plain text to HTML
    const paragraphs = text.split(/\n\n+/);
    let html = '';
    
    paragraphs.forEach(para => {
        para = para.trim();
        if (!para) return;
        
        // Check if it's a heading (all caps or numbered)
        if (/^[A-Z][A-Z\s]+$/.test(para) || /^(PASAL|ARTICLE|BAB|CHAPTER)\s*\d+/i.test(para)) {
            html += `<h2>${escapeHtml(para)}</h2>\n`;
        } else if (/^\d+\.\s/.test(para)) {
            // Numbered paragraph
            html += `<p>${escapeHtml(para)}</p>\n`;
        } else {
            html += `<p>${escapeHtml(para.replace(/\n/g, '<br>'))}</p>\n`;
        }
    });
    
    return html || '<p></p>';
}

function updateWordCount() {
    if (!editorInstance) return;
    
    const content = editorInstance.getText();
    const words = content.trim().split(/\s+/).filter(w => w.length > 0).length;
    document.getElementById('editor-word-count').textContent = `${words} word${words !== 1 ? 's' : ''}`;
}

function updateEditorStatus(status, className = '') {
    const statusEl = document.getElementById('editor-status');
    statusEl.textContent = status;
    statusEl.className = 'editor-status ' + className;
}
