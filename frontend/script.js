

// CONFIGURATION
const API_BASE_URL = 'http://127.0.0.1:8000/api';
const LOCAL_STORAGE_KEY = 'smart_task_analyzer_tasks';


// STATE MANAGEMENT
let tasks = [];
let analyzedTasks = [];
let currentView = 'table';


// INITIALIZATION
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    attachEventListeners();
    loadTasksFromStorage();
});

function initializeApp() {
    updateTaskCount();
    console.log('Smart Task Analyzer initialized');
}


// EVENT LISTENERS
function attachEventListeners() {
    // Form submissions
    document.getElementById('taskForm').addEventListener('submit', handleAddTask);
    document.getElementById('loadBulkBtn').addEventListener('click', handleLoadBulkTasks);

    // Analysis buttons
    document.getElementById('analyzeBtn').addEventListener('click', handleAnalyzeTasks);
    document.getElementById('suggestBtn').addEventListener('click', handleSuggestTasks);

    // Utility buttons
    document.getElementById('clearAllBtn').addEventListener('click', handleClearAll);

    // View switches
    document.getElementById('tableViewBtn').addEventListener('click', () => switchView('table'));
    document.getElementById('cardViewBtn').addEventListener('click', () => switchView('card'));
    document.getElementById('graphViewBtn').addEventListener('click', () => switchView('graph'));
    document.getElementById('matrixViewBtn').addEventListener('click', () => switchView('matrix'));
}


// TASK MANAGEMENT
function handleAddTask(e) {
    e.preventDefault();

    const task = {
        id: tasks.length + 1,
        title: document.getElementById('taskTitle').value,
        due_date: document.getElementById('taskDueDate').value,
        estimated_hours: parseFloat(document.getElementById('taskHours').value),
        importance: parseInt(document.getElementById('taskImportance').value),
        dependencies: parseDependencies(document.getElementById('taskDependencies').value)
    };

    // Validate task
    if (!validateTask(task)) {
        return;
    }

    tasks.push(task);
    saveTasksToStorage();
    updateCurrentTasksList();
    updateTaskCount();

    // Reset form
    e.target.reset();

    showToast('Task added successfully!', 'success');
}

function handleLoadBulkTasks() {
    const bulkInput = document.getElementById('bulkTasksInput').value.trim();

    if (!bulkInput) {
        showToast('Please paste JSON data', 'warning');
        return;
    }

    try {
        const loadedTasks = JSON.parse(bulkInput);

        if (!Array.isArray(loadedTasks)) {
            throw new Error('Input must be an array of tasks');
        }

        // Add IDs to loaded tasks
        const startId = tasks.length + 1;
        loadedTasks.forEach((task, index) => {
            if (!task.id) {
                task.id = startId + index;
            }
        });

        tasks.push(...loadedTasks);
        saveTasksToStorage();
        updateCurrentTasksList();
        updateTaskCount();

        document.getElementById('bulkTasksInput').value = '';
        showToast(`✅ Loaded ${loadedTasks.length} tasks!`, 'success');

    } catch (error) {
        showToast(`❌ Invalid JSON: ${error.message}`, 'error');
    }
}

function handleClearAll() {
    if (tasks.length === 0) {
        showToast('No tasks to clear', 'info');
        return;
    }

    if (confirm(`Are you sure you want to clear all ${tasks.length} tasks?`)) {
        tasks = [];
        analyzedTasks = [];
        saveTasksToStorage();
        updateCurrentTasksList();
        updateTaskCount();
        hideResults();
        showToast('🗑️ All tasks cleared', 'info');
    }
}

function removeTask(index) {
    tasks.splice(index, 1);
    // Reassign IDs
    tasks.forEach((task, i) => {
        task.id = i + 1;
    });
    saveTasksToStorage();
    updateCurrentTasksList();
    updateTaskCount();
    showToast('🗑️ Task removed', 'info');
}


// VALIDATION


function validateTask(task) {
    const errors = [];

    if (!task.title || task.title.trim().length === 0) {
        errors.push('Title is required');
    }

    if (!task.due_date) {
        errors.push('Due date is required');
    }

    if (!task.estimated_hours || task.estimated_hours <= 0) {
        errors.push('Estimated hours must be greater than 0');
    }

    if (!task.importance || task.importance < 1 || task.importance > 10) {
        errors.push('Importance must be between 1 and 10');
    }

    if (errors.length > 0) {
        showToast(`Validation errors:\n${errors.join('\n')}`, 'error');
        return false;
    }

    return true;
}

function parseDependencies(input) {
    if (!input || input.trim() === '') {
        return [];
    }

    return input.split(',')
        .map(id => parseInt(id.trim()))
        .filter(id => !isNaN(id));
}


// API COMMUNICATION


async function handleAnalyzeTasks() {
    if (tasks.length === 0) {
        showToast('Please add some tasks first', 'warning');
        return;
    }

    const strategy = document.getElementById('strategySelect').value;

    showLoading();
    hideWarnings();

    try {
        const response = await fetch(`${API_BASE_URL}/tasks/analyze/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tasks: tasks,
                strategy: strategy
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Analysis failed');
        }

        analyzedTasks = data.tasks;

        // Show warnings if any
        if (data.warnings && data.warnings.length > 0) {
            showWarnings(data.warnings);
        }

        // Show circular dependency warning
        if (data.has_circular_dependencies) {
            showWarnings([{
                type: 'circular_dependency',
                message: 'Circular dependencies detected!',
                details: data.circular_dependency_details
            }]);
        }

        hideLoading();
        displayResults();
        showToast('✅ Analysis complete!', 'success');

    } catch (error) {
        hideLoading();
        showToast(`❌ Analysis error: ${error.message}`, 'error');
        console.error('Analysis error:', error);
    }
}

async function handleSuggestTasks() {
    if (tasks.length === 0) {
        showToast('Please add some tasks first', 'warning');
        return;
    }

    const strategy = document.getElementById('strategySelect').value;

    showLoading();
    hideWarnings();

    try {
        const response = await fetch(`${API_BASE_URL}/tasks/suggest/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tasks: tasks,
                strategy: strategy
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Suggestion failed');
        }

        analyzedTasks = data.top_tasks;

        // Show warnings
        if (data.warnings && data.warnings.length > 0) {
            showWarnings(data.warnings);
        }

        hideLoading();
        displaySuggestions();
        showToast('✅ Top suggestions ready!', 'success');

    } catch (error) {
        hideLoading();
        showToast(`❌ Suggestion error: ${error.message}`, 'error');
        console.error('Suggestion error:', error);
    }
}


// UI UPDATES
function updateCurrentTasksList() {
    const container = document.getElementById('currentTasksList');

    if (tasks.length === 0) {
        container.innerHTML = '<p class="empty-state">No tasks added yet. Add tasks using the form above.</p>';
        return;
    }

    container.innerHTML = tasks.map((task, index) => `
        <div class="task-item">
            <div class="task-item-info">
                <div class="task-item-title">${task.title}</div>
                <div class="task-item-meta">
                    <span>📅 ${task.due_date}</span>
                    <span>⏱️ ${task.estimated_hours}h</span>
                    <span>⭐ ${task.importance}/10</span>
                </div>
            </div>
            <button class="task-item-remove" onclick="removeTask(${index})">✕</button>
        </div>
    `).join('');
}

function updateTaskCount() {
    document.getElementById('taskCount').textContent = tasks.length;
}

function displayResults() {
    document.getElementById('resultsSection').style.display = 'block';
    switchView(currentView);
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

function displaySuggestions() {
    document.getElementById('resultsSection').style.display = 'block';
    renderCardView(); // Always show suggestions in card view
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

function hideResults() {
    document.getElementById('resultsSection').style.display = 'none';
}

function switchView(view) {
    currentView = view;

    // Update button states
    document.querySelectorAll('.view-btn').forEach(btn => btn.classList.remove('active'));

    // Hide all views
    document.getElementById('resultsContainer').innerHTML = '';
    document.getElementById('graphContainer').style.display = 'none';
    document.getElementById('matrixContainer').style.display = 'none';

    switch (view) {
        case 'table':
            document.getElementById('tableViewBtn').classList.add('active');
            renderTableView();
            break;
        case 'card':
            document.getElementById('cardViewBtn').classList.add('active');
            renderCardView();
            break;
        case 'graph':
            document.getElementById('graphViewBtn').classList.add('active');
            renderDependencyGraph();
            break;
        case 'matrix':
            document.getElementById('matrixViewBtn').classList.add('active');
            renderEisenhowerMatrix();
            break;
    }
}


// RENDER VIEWS
function renderTableView() {
    const container = document.getElementById('resultsContainer');

    if (analyzedTasks.length === 0) {
        container.innerHTML = '<p class="empty-state">No results to display</p>';
        return;
    }

    const html = `
        <div class="card">
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Task</th>
                        <th>Due Date</th>
                        <th>Hours</th>
                        <th>Importance</th>
                        <th>Score</th>
                        <th>Priority</th>
                    </tr>
                </thead>
                <tbody>
                    ${analyzedTasks.map((task, index) => `
                        <tr>
                            <td><strong>#${index + 1}</strong></td>
                            <td>${task.title}</td>
                            <td>${formatDate(task.due_date)}</td>
                            <td>${task.estimated_hours}h</td>
                            <td>${task.importance}/10</td>
                            <td><span class="score-display">${task.priority_score.toFixed(2)}</span></td>
                            <td><span class="priority-badge priority-${task.priority_level.toLowerCase()}">${task.priority_level}</span></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;

    container.innerHTML = html;
}

function renderCardView() {
    const container = document.getElementById('resultsContainer');

    if (analyzedTasks.length === 0) {
        container.innerHTML = '<p class="empty-state">No results to display</p>';
        return;
    }

    const html = `
        <div class="results-grid">
            ${analyzedTasks.map((task, index) => `
                <div class="task-card ${task.priority_level.toLowerCase()}-priority">
                    <div class="task-card-header">
                        <div>
                            <div style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.25rem;">
                                Rank #${index + 1}
                            </div>
                            <h3 class="task-card-title">${task.title}</h3>
                        </div>
                        <div class="task-card-score">${task.priority_score.toFixed(1)}</div>
                    </div>
                    
                    <div class="task-card-details">
                        <div>📅 <strong>Due:</strong> ${formatDate(task.due_date)}</div>
                        <div>⏱️ <strong>Hours:</strong> ${task.estimated_hours}h</div>
                        <div>⭐ <strong>Importance:</strong> ${task.importance}/10</div>
                        <div><strong>Priority:</strong> <span class="priority-badge priority-${task.priority_level.toLowerCase()}">${task.priority_level}</span></div>
                    </div>
                    
                    ${task.recommendation ? `
                        <div style="background: var(--bg-tertiary); padding: var(--spacing-sm); border-radius: var(--radius-sm); margin-bottom: var(--spacing-sm); color: var(--text-secondary);">
                            ${task.recommendation}
                        </div>
                    ` : ''}
                    
                    <details style="margin-top: var(--spacing-sm);">
                        <summary style="cursor: pointer; color: var(--primary); font-weight: 600;">📊 Score Breakdown</summary>
                        <div class="task-card-explanation">${task.score_explanation}</div>
                    </details>
                </div>
            `).join('')}
        </div>
    `;

    container.innerHTML = html;
}

function renderDependencyGraph() {
    const container = document.getElementById('graphContainer');
    container.style.display = 'block';

    const canvas = document.getElementById('dependencyGraph');
    const ctx = canvas.getContext('2d');

    // Set canvas size
    canvas.width = container.clientWidth - 40;
    canvas.height = Math.max(500, analyzedTasks.length * 80);

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (analyzedTasks.length === 0) {
        ctx.fillStyle = '#7a7a9d';
        ctx.font = '16px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('No tasks to display', canvas.width / 2, canvas.height / 2);
        return;
    }

    // Calculate node positions
    const nodeRadius = 30;
    const padding = 80;
    const nodes = [];

    analyzedTasks.forEach((task, index) => {
        const x = padding + (index % 3) * ((canvas.width - 2 * padding) / 2);
        const y = padding + Math.floor(index / 3) * 120;
        nodes.push({ task, x, y });
    });

    // Draw edges (dependencies)
    ctx.strokeStyle = 'rgba(102, 126, 234, 0.5)';
    ctx.lineWidth = 2;

    nodes.forEach(node => {
        const deps = node.task.dependencies || [];
        deps.forEach(depId => {
            const depNode = nodes.find(n => n.task.id === depId);
            if (depNode) {
                drawArrow(ctx, node.x, node.y, depNode.x, depNode.y);
            }
        });
    });

    // Draw nodes
    nodes.forEach(node => {
        const priorityColor = getPriorityColor(node.task.priority_level);

        // Draw circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI);
        ctx.fillStyle = priorityColor;
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 3;
        ctx.stroke();

        // Draw score
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 16px Inter';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(node.task.priority_score.toFixed(1), node.x, node.y);

        // Draw title
        ctx.fillStyle = '#ffffff';
        ctx.font = '12px Inter';
        ctx.fillText(truncateText(node.task.title, 20), node.x, node.y + nodeRadius + 20);
    });
}

function renderEisenhowerMatrix() {
    const container = document.getElementById('matrixContainer');
    container.style.display = 'block';

    // Clear quadrants
    for (let i = 1; i <= 4; i++) {
        document.getElementById(`quadrant${i}`).innerHTML = '';
    }

    if (analyzedTasks.length === 0) {
        document.getElementById('quadrant1').innerHTML = '<p style="color: var(--text-muted);">No tasks</p>';
        return;
    }

    // Categorize tasks into quadrants
    analyzedTasks.forEach(task => {
        const urgencyScore = task.score_breakdown?.urgency || 5;
        const importanceScore = task.score_breakdown?.importance || 5;

        let quadrant;
        if (urgencyScore >= 6 && importanceScore >= 6) {
            quadrant = 1; // Urgent & Important
        } else if (urgencyScore < 6 && importanceScore >= 6) {
            quadrant = 2; // Not urgent but important
        } else if (urgencyScore >= 6 && importanceScore < 6) {
            quadrant = 3; // Urgent but less important
        } else {
            quadrant = 4; // Neither
        }

        const quadrantEl = document.getElementById(`quadrant${quadrant}`);
        const taskItem = document.createElement('div');
        taskItem.className = 'quadrant-task-item';
        taskItem.innerHTML = `
            <strong>${task.title}</strong><br>
            <small>Score: ${task.priority_score.toFixed(1)} | U: ${urgencyScore.toFixed(1)} | I: ${importanceScore.toFixed(1)}</small>
        `;
        quadrantEl.appendChild(taskItem);
    });
}


// HELPER FUNCTIONS
function drawArrow(ctx, fromX, fromY, toX, toY) {
    const headLength = 10;
    const angle = Math.atan2(toY - fromY, toX - fromX);

    // Adjust start and end points to be at edge of circles
    const nodeRadius = 30;
    const startX = fromX + nodeRadius * Math.cos(angle);
    const startY = fromY + nodeRadius * Math.sin(angle);
    const endX = toX - nodeRadius * Math.cos(angle);
    const endY = toY - nodeRadius * Math.sin(angle);

    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.stroke();

    // Draw arrowhead
    ctx.beginPath();
    ctx.moveTo(endX, endY);
    ctx.lineTo(
        endX - headLength * Math.cos(angle - Math.PI / 6),
        endY - headLength * Math.sin(angle - Math.PI / 6)
    );
    ctx.moveTo(endX, endY);
    ctx.lineTo(
        endX - headLength * Math.cos(angle + Math.PI / 6),
        endY - headLength * Math.sin(angle + Math.PI / 6)
    );
    ctx.stroke();
}

function getPriorityColor(level) {
    switch (level?.toLowerCase()) {
        case 'high': return '#ff6b6b';
        case 'medium': return '#ffa500';
        case 'low': return '#43e97b';
        default: return '#667eea';
    }
}

function truncateText(text, maxLength) {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const today = new Date();
    const diffDays = Math.ceil((date - today) / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
        return `${dateStr} (${Math.abs(diffDays)}d overdue)`;
    } else if (diffDays === 0) {
        return `${dateStr} (TODAY)`;
    } else if (diffDays === 1) {
        return `${dateStr} (tomorrow)`;
    } else {
        return `${dateStr} (in ${diffDays}d)`;
    }
}

function showLoading() {
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('resultsContainer').innerHTML = '';
}

function hideLoading() {
    document.getElementById('loadingIndicator').style.display = 'none';
}

function showWarnings(warnings) {
    const container = document.getElementById('warningsContainer');
    container.style.display = 'block';

    container.innerHTML = warnings.map(warning => {
        let content = `<strong>${warning.message || warning.type}</strong>`;
        if (warning.details) {
            if (Array.isArray(warning.details)) {
                content += '<ul>' + warning.details.map(d => `<li>${d}</li>`).join('') + '</ul>';
            } else {
                content += `<div>${warning.details}</div>`;
            }
        }

        const className = warning.type === 'circular_dependency' ? 'warning-item' : 'warning-item info';
        return `<div class="${className}">${content}</div>`;
    }).join('');
}

function hideWarnings() {
    document.getElementById('warningsContainer').style.display = 'none';
    document.getElementById('warningsContainer').innerHTML = '';
}

function showToast(message, type = 'info') {
    // Simple alert for now - can be enhanced with a toast library
    console.log(`[${type.toUpperCase()}] ${message}`);

    // Show in UI (simple implementation)
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#ff6b6b' : type === 'success' ? '#43e97b' : '#667eea'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        z-index: 1000;
        animation: fadeIn 0.3s ease;
        max-width: 300px;
        font-weight: 600;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}


// LOCAL STORAGE
function saveTasksToStorage() {
    try {
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(tasks));
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
    }
}

function loadTasksFromStorage() {
    try {
        const stored = localStorage.getItem(LOCAL_STORAGE_KEY);
        if (stored) {
            tasks = JSON.parse(stored);
            updateCurrentTasksList();
            updateTaskCount();
            console.log(`📦 Loaded ${tasks.length} tasks from storage`);
        }
    } catch (error) {
        console.error('Failed to load from localStorage:', error);
    }
}

// Make removeTask available globally
window.removeTask = removeTask;
