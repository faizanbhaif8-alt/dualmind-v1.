let currentTaskId = null;
let currentProjectId = null;
let eventSource = null;

const historyList = document.getElementById('historyList');
const chatArea = document.getElementById('chatArea');
const commandInput = document.getElementById('commandInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const pushGithubBtn = document.getElementById('pushGithubBtn');
const repoNameInput = document.getElementById('repoNameInput');
const projectTitle = document.getElementById('projectTitle');
const analysisResult = document.getElementById('analysisResult');
const progressArea = document.getElementById('progressArea');
const modelStatus = document.getElementById('modelStatus');
const hostBadge = document.getElementById('hostBadge');

// Set host badge
hostBadge.innerHTML = '🏠 Replit Ready';

// ==================== ANALYZE BUTTON (Model 1) ====================
analyzeBtn.addEventListener('click', async () => {
    const command = commandInput.value.trim();
    if (!command) {
        alert('Please enter a command!');
        return;
    }
    
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '⚡ Model 1: Analyzing...';
    modelStatus.innerHTML = '<span style="color: #3b82f6;">⚡ Model 1 Active</span> - Analyzing project...';
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentTaskId = data.task_id;
            displayAnalysis(data.analysis, data.host_env);
        } else {
            alert('Analysis failed: ' + data.detail);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '🔍 Analyze (Model 1)';
        modelStatus.innerHTML = '<span>🧠 DualMindAI v1.0 | ⚡ Model 1 Ready | 🧠 Model 2 Standby</span>';
    }
});

function displayAnalysis(analysis, hostEnv) {
    const benefitsHtml = analysis.benefits ? analysis.benefits.map(b => `<span class="benefit-tag">✅ ${b}</span>`).join('') : '';
    
    analysisResult.style.display = 'block';
    analysisResult.innerHTML = `
        <div class="analysis-card">
            <h3 style="color: #667eea;">📊 Analysis Complete (Model 1 - Fast)</h3>
            <div class="analysis-detail">
                <p>
                    <span class="language-tag">🏷️ ${analysis.detected_language}</span>
                    <span class="language-tag">📚 ${analysis.framework}</span>
                    <span class="language-tag">🎯 ${analysis.project_type}</span>
                </p>
                <p><strong>🏠 Host Environment:</strong> ${hostEnv === 'replit' ? 'Replit ✓' : 'Local'}</p>
                <p><strong>🚀 Start Command:</strong> <code style="background:#1a1a2a; padding:2px 6px; border-radius:4px;">${analysis.start_command}</code></p>
                <p><strong>📁 Files Needed:</strong> ${analysis.files_needed.join(' → ')}</p>
                <p><strong>💭 Reasoning:</strong> ${analysis.reasoning}</p>
                ${benefitsHtml ? `<p><strong>⭐ Benefits:</strong></p><div class="benefits-list">${benefitsHtml}</div>` : ''}
                <p><strong>⚡ Complexity:</strong> ${analysis.complexity}</p>
            </div>
            <button class="confirm-btn" onclick="confirmAndGenerate()">
                🧠 Generate with Model 2 (Deep Coder)
            </button>
        </div>
    `;
    
    analysisResult.scrollIntoView({ behavior: 'smooth' });
}

// ==================== CONFIRM & GENERATE (Model 2) ====================
window.confirmAndGenerate = async function() {
    if (!currentTaskId) return;
    
    analysisResult.style.display = 'none';
    progressArea.style.display = 'block';
    progressArea.innerHTML = `
        <div class="progress-container">
            <h4 style="color: #8b5cf6;">🧠 Model 2 (Deep Coder) - Generating...</h4>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div id="progressPercentage" style="text-align: center; margin: 10px 0; font-weight: bold;">0%</div>
            <div class="progress-messages" id="progressMessages"></div>
        </div>
    `;
    
    modelStatus.innerHTML = '<span style="color: #8b5cf6;">🧠 Model 2 Active</span> - Deep reasoning & code generation...';
    
    eventSource = new EventSource(`/api/progress/${currentTaskId}`);
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.type === 'progress') {
            updateProgress(data.message, data.percentage);
        } else if (data.type === 'complete') {
            eventSource.close();
            currentProjectId = data.project.project_id;
            showGeneratedProject(data.project);
            modelStatus.innerHTML = '<span>🧠 DualMindAI v1.0 | ⚡ Model 1 Ready | 🧠 Model 2 Ready</span>';
        } else if (data.type === 'error') {
            eventSource.close();
            showError(data.message);
            modelStatus.innerHTML = '<span style="color: #f87171;">❌ Error occurred</span>';
        }
    };
    
    // Start generation
    fetch(`/api/generate/${currentTaskId}`, { method: 'POST' });
};

function updateProgress(message, percentage) {
    const messagesDiv = document.getElementById('progressMessages');
    const progressFill = document.getElementById('progressFill');
    const percentageSpan = document.getElementById('progressPercentage');
    
    const msgDiv = document.createElement('div');
    msgDiv.className = 'progress-message';
    msgDiv.innerHTML = message;
    messagesDiv.appendChild(msgDiv);
    
    if (percentage !== null && percentage !== undefined) {
        progressFill.style.width = percentage + '%';
        percentageSpan.textContent = percentage + '%';
    }
    
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function showGeneratedProject(project) {
    progressArea.style.display = 'none';
    pushGithubBtn.disabled = false;
    
    projectTitle.innerHTML = `✅ ${project.language.toUpperCase()} Project | ${project.total_files} files`;
    
    let filesHtml = '<div class="files-card"><div class="files-header">📄 Generated Files</div><div class="files-list">';
    project.files.forEach(file => {
        filesHtml += `
            <div class="file-item">
                <div class="file-name">📁 ${escapeHtml(file.path)}</div>
                <pre class="file-content">${escapeHtml(file.content)}</pre>
            </div>
        `;
    });
    filesHtml += '</div></div>';
    
    chatArea.innerHTML = `
        <div style="max-width: 900px; margin: 0 auto;">
            <div class="summary-card">
                <h4>✅ ${escapeHtml(project.summary)}</h4>
                <p>🎉 ${project.total_files} files created | 🚀 Run: <code style="background:#1a1a2a; padding:2px 6px; border-radius:4px;">${project.start_command}</code></p>
            </div>
            ${filesHtml}
        </div>
    `;
    
    loadHistory();
}

function showError(message) {
    progressArea.innerHTML = `
        <div class="progress-container" style="border-color: #f87171;">
            <h4 style="color: #f87171;">❌ Generation Failed</h4>
            <p>${escapeHtml(message)}</p>
            <button onclick="location.reload()" style="margin-top: 10px; padding: 8px 16px; background: #f87171; border: none; border-radius: 6px; cursor: pointer;">Try Again</button>
        </div>
    `;
}

// ==================== PUSH TO GITHUB ====================
pushGithubBtn.addEventListener('click', async () => {
    const repoName = repoNameInput.value.trim();
    if (!repoName) {
        alert('Please enter a repository name!');
        return;
    }
    if (!currentProjectId) {
        alert('Please generate a project first!');
        return;
    }
    
    pushGithubBtn.disabled = true;
    pushGithubBtn.innerHTML = '⏫ Pushing to GitHub...';
    
    try {
        const response = await fetch(`/api/push-to-github?project_id=${currentProjectId}&repo_name=${repoName}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            alert(`✅ Success! Repository created:\n${data.repo_url}`);
            repoNameInput.value = '';
        } else {
            alert('Error: ' + data.detail);
        }
    } catch (error) {
        alert('Push failed: ' + error.message);
    } finally {
        pushGithubBtn.disabled = false;
        pushGithubBtn.innerHTML = '🐙 Push to GitHub';
    }
});

// ==================== HISTORY FUNCTIONS ====================
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        renderHistory(data.history);
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

function renderHistory(history) {
    if (!history || history.length === 0) {
        historyList.innerHTML = '<div style="color: #666; text-align: center; padding: 20px;">No projects yet</div>';
        return;
    }
    
    historyList.innerHTML = history.map(proj => `
        <div class="history-item" data-id="${proj.id}">
            <div class="history-command">${escapeHtml(proj.command.substring(0, 45))}${proj.command.length > 45 ? '...' : ''}</div>
            <div class="history-date">${new Date(proj.timestamp).toLocaleString()}</div>
            <div style="font-size: 0.6rem; margin-top: 4px; color: #667eea;">${proj.language || 'code'}</div>
        </div>
    `).join('');
    
    document.querySelectorAll('.history-item').forEach(el => {
        el.addEventListener('click', () => {
            document.querySelectorAll('.history-item').forEach(item => item.classList.remove('active'));
            el.classList.add('active');
        });
    });
}

// ==================== NEW PROJECT ====================
document.getElementById('newProjectBtn').addEventListener('click', () => {
    currentTaskId = null;
    currentProjectId = null;
    analysisResult.style.display = 'none';
    progressArea.style.display = 'none';
    commandInput.value = '';
    repoNameInput.value = '';
    pushGithubBtn.disabled = true;
    projectTitle.innerHTML = '✨ Create a New Project';
    
    chatArea.innerHTML = `
        <div class="welcome-card">
            <div class="welcome-icon">🧠</div>
            <h3>DualMindAI v1.0</h3>
            <p>
                ⚡ <span class="highlight">Model 1 (Fast)</span> - Smart Analyzer (1-2 sec)<br>
                🧠 <span class="highlight">Model 2 (Deep)</span> - Code Generator (8-12 sec)<br>
                🏠 <span class="highlight">Replit Optimized</span> - Auto-adjusted for hosting
            </p>
            <div class="example-commands">
                <strong>📝 Try these commands:</strong>
                <ul>
                    <li>• "Mujhe ek Telegram bot banvana hai jo weather update de"</li>
                    <li>• "FastAPI se REST API banao with 3 endpoints"</li>
                    <li>• "Automation bot jo daily news scrape kare"</li>
                    <li>• "React mein todo app banao"</li>
                </ul>
            </div>
        </div>
    `;
    
    document.querySelectorAll('.history-item').forEach(item => item.classList.remove('active'));
});

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ==================== INITIAL LOAD ====================
loadHistory();