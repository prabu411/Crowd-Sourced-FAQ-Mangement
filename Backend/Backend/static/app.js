// Crowd FAQs - Developer Frontend Testing client
// Developed as a companion tool for Mohd Warish's Backend REST API module

let activeTab = 'voting'; // 'voting' or 'moderation'
let clustersData = [];

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    // Event listeners for tabs
    document.getElementById('tab-voting').addEventListener('click', () => switchTab('voting'));
    document.getElementById('tab-moderation').addEventListener('click', () => switchTab('moderation'));

    // Question form submission
    document.getElementById('question-form').addEventListener('submit', handleQuestionSubmit);

    // Clear console button
    document.getElementById('clear-console').addEventListener('click', () => {
        const consoleEl = document.getElementById('json-console');
        consoleEl.innerHTML = '<div class="text-gray-500">// Console cleared. Ready.</div>';
    });

    // Load initial database records
    loadClusters();
}

function switchTab(tab) {
    activeTab = tab;
    
    // Update active tab buttons visually
    const tabVoting = document.getElementById('tab-voting');
    const tabMod = document.getElementById('tab-moderation');
    
    if (tab === 'voting') {
        tabVoting.classList.add('active', 'border-cyan-400', 'text-white');
        tabVoting.classList.remove('border-transparent', 'text-gray-400');
        tabMod.classList.add('border-transparent', 'text-gray-400');
        tabMod.classList.remove('active', 'border-cyan-400', 'text-white');
    } else {
        tabMod.classList.add('active', 'border-cyan-400', 'text-white');
        tabMod.classList.remove('border-transparent', 'text-gray-400');
        tabVoting.classList.add('border-transparent', 'text-gray-400');
        tabVoting.classList.remove('active', 'border-cyan-400', 'text-white');
    }
    
    // Rerender lists
    renderFeed();
}

// Log requests/responses to the glowing UI terminal
function logToConsole(type, title, data) {
    const consoleEl = document.getElementById('json-console');
    const timestamp = new Date().toLocaleTimeString();
    
    let colorClass = "text-green-400";
    if (type === 'REQUEST') colorClass = "text-yellow-400";
    if (type === 'ERROR') colorClass = "text-red-400";

    const logBlock = document.createElement('div');
    logBlock.className = "border-b border-[#171a35] pb-2 mb-2 fade-in";
    logBlock.innerHTML = `
        <div class="flex items-center justify-between font-bold text-[10px]">
            <span class="${colorClass}">[${type}] ${title}</span>
            <span class="text-gray-600">${timestamp}</span>
        </div>
        <pre class="text-[11px] overflow-x-auto mt-1 whitespace-pre-wrap select-all text-gray-300 bg-[#07080f]/50 p-2 rounded">${JSON.stringify(data, null, 2)}</pre>
    `;
    
    consoleEl.appendChild(logBlock);
    // Auto-scroll to bottom of console
    consoleEl.scrollTop = consoleEl.scrollHeight;
}

// Global notification system
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toast-message');
    const toastIcon = document.getElementById('toast-icon');
    
    toastMsg.textContent = message;
    if (type === 'success') {
        toastIcon.textContent = '✨';
        toast.className = toast.className.replace(/from-\w+ to-\w+/, 'from-violet-900 to-cyan-950').replace('border-red-500', 'border-violet-500');
    } else {
        toastIcon.textContent = '⚠️';
        toast.className = toast.className.replace(/from-\w+ to-\w+/, 'from-red-950 to-orange-950').replace('border-violet-500', 'border-red-500');
    }
    
    // Sliding micro-animation
    toast.classList.remove('translate-y-20', 'opacity-0');
    toast.classList.add('translate-y-0', 'opacity-100');
    
    setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
        toast.classList.remove('translate-y-0', 'opacity-100');
    }, 4000);
}

// FETCH: GET all clusters from Mohd Warish's REST endpoint
async function loadClusters() {
    try {
        logToConsole('REQUEST', 'GET /api/questions', {});
        
        const response = await fetch('/api/questions');
        if (!response.ok) throw new Error('API server returned error');
        
        clustersData = await response.json();
        logToConsole('RESPONSE', 'GET /api/questions', clustersData);
        
        renderFeed();
    } catch (err) {
        logToConsole('ERROR', 'Failed to retrieve questions', err.message);
        document.getElementById('feed-container').innerHTML = `
            <div class="glass-card p-8 rounded-2xl border border-red-500/20 text-center text-red-400">
                <p class="font-bold">⚠️ Connection Error</p>
                <p class="text-xs text-gray-500 mt-2">Could not reach the FastAPI server. Please verify uvicorn is running.</p>
            </div>
        `;
    }
}

// FETCH: POST a new question via REST endpoint
async function handleQuestionSubmit(e) {
    e.preventDefault();
    
    const textEl = document.getElementById('question-text');
    const catEl = document.getElementById('question-category');
    const userEl = document.getElementById('user-identifier');
    
    const payload = {
        question_text: textEl.value.trim(),
        category: catEl.value,
        user_identifier: userEl.value.trim()
    };
    
    try {
        logToConsole('REQUEST', 'POST /api/questions', payload);
        
        const response = await fetch('/api/questions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (!response.ok) throw new Error(result.detail || 'Failed to submit question');
        
        logToConsole('RESPONSE', 'POST /api/questions', result);
        
        // Success feedback
        showToast('Question submitted successfully!');
        textEl.value = ''; // Reset input
        
        // Reload list to see clustered state
        loadClusters();
    } catch (err) {
        logToConsole('ERROR', 'POST /api/questions failed', err.message);
        showToast(err.message, 'error');
    }
}

// FETCH: POST an upvote via REST endpoint
async function upvoteCluster(clusterId) {
    const userEl = document.getElementById('user-identifier');
    
    const payload = {
        cluster_id: clusterId,
        user_identifier: userEl.value.trim()
    };
    
    try {
        logToConsole('REQUEST', 'POST /api/votes', payload);
        
        const response = await fetch('/api/votes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (!response.ok) throw new Error(result.detail || 'Failed to register vote');
        
        logToConsole('RESPONSE', 'POST /api/votes', result);
        showToast(result.message);
        
        // Reload list to view new priority ordering
        loadClusters();
    } catch (err) {
        logToConsole('ERROR', 'POST /api/votes failed', err.message);
        showToast(err.message, 'error');
    }
}

// FETCH: POST approval for integration testing
async function approveCluster(clusterId, textareaId) {
    const answerText = document.getElementById(textareaId).value.trim();
    
    try {
        const url = `/api/moderation/approve?cluster_id=${clusterId}&answer_text=${encodeURIComponent(answerText)}`;
        logToConsole('REQUEST', `POST /api/moderation/approve`, { cluster_id: clusterId, answer_text: answerText });
        
        const response = await fetch(url, { method: 'POST' });
        const result = await response.json();
        
        if (!response.ok) throw new Error(result.detail || 'Failed to approve cluster');
        
        logToConsole('RESPONSE', `POST /api/moderation/approve`, result);
        showToast(`Cluster #${clusterId} approved & answer published!`);
        
        loadClusters();
    } catch (err) {
        logToConsole('ERROR', 'Approving cluster failed', err.message);
        showToast(err.message, 'error');
    }
}

// Render dynamic elements to feed panel
function renderFeed() {
    const container = document.getElementById('feed-container');
    container.innerHTML = '';
    
    if (clustersData.length === 0) {
        container.innerHTML = `
            <div class="glass-card p-12 rounded-2xl border border-dashed border-[#23284f] text-center text-gray-500">
                <p>No question clusters in database.</p>
                <p class="text-xs mt-2">Submit your first question using the submission panel!</p>
            </div>
        `;
        return;
    }
    
    clustersData.forEach(cluster => {
        // Compute category accent colors
        let badgeColor = "bg-gray-900 border-gray-700 text-gray-400";
        if (cluster.category === 'Bug') badgeColor = "bg-red-950/40 border-red-500/30 text-red-400";
        if (cluster.category === 'Feature Request') badgeColor = "bg-violet-950/40 border-violet-500/30 text-violet-400";
        if (cluster.category === 'Account') badgeColor = "bg-cyan-950/40 border-cyan-500/30 text-cyan-400";

        const card = document.createElement('div');
        card.className = "glass-card p-6 rounded-2xl border border-[#23284f] flex flex-col gap-4 relative overflow-hidden fade-in";
        
        if (activeTab === 'voting') {
            // Render Voting tab visual view
            const hasVerifiedAnswer = cluster.answer_text ? true : false;
            
            card.innerHTML = `
                <!-- Header -->
                <div class="flex items-start justify-between">
                    <div class="flex items-center space-x-2">
                        <span class="px-2.5 py-1 text-xs font-semibold rounded-lg border ${badgeColor}">${cluster.category || 'General'}</span>
                        <span class="text-xs font-mono text-gray-500">Cluster #${cluster.id}</span>
                    </div>
                    <div class="flex items-center space-x-4">
                        <div class="text-right">
                            <span class="block text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Priority Score</span>
                            <span class="text-sm font-bold font-mono text-cyan-300">${cluster.priority_score}</span>
                        </div>
                    </div>
                </div>

                <!-- Representative Question Title -->
                <div>
                    <h3 class="text-base font-bold text-white leading-snug">${cluster.representative_text || 'Unnamed Question'}</h3>
                    
                    <!-- Nested Questions List (Stage 2 proof) -->
                    ${cluster.questions.length > 1 ? `
                        <div class="mt-2.5 pl-4 border-l-2 border-[#1c203b] space-y-1">
                            <span class="block text-[10px] text-violet-400 font-mono font-semibold uppercase tracking-wider">Merged similar queries (${cluster.questions.length - 1}):</span>
                            ${cluster.questions.slice(1).map(q => `
                                <p class="text-xs text-gray-400 italic">" ${q.question_text} "</p>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>

                <!-- Verified Answer / AI Draft Answer -->
                <div class="bg-[#090b12] border border-[#1b1e3a] p-4 rounded-xl text-xs space-y-1.5">
                    ${hasVerifiedAnswer ? `
                        <span class="text-[9px] font-bold text-green-400 tracking-widest uppercase flex items-center">
                            <span class="w-1.5 h-1.5 rounded-full bg-green-500 mr-1.5"></span> Verified Answer
                        </span>
                        <p class="text-gray-300 leading-relaxed">${cluster.answer_text}</p>
                    ` : `
                        <span class="text-[9px] font-bold text-yellow-400 tracking-widest uppercase flex items-center">
                            <span class="w-1.5 h-1.5 rounded-full bg-yellow-500 mr-1.5"></span> AI Generated Draft
                        </span>
                        <p class="text-gray-400 leading-relaxed italic">${cluster.ai_draft_text || 'Draft pending generation...'}</p>
                    `}
                </div>

                <!-- Actions -->
                <div class="flex items-center justify-between mt-2 pt-3 border-t border-[#171a35]">
                    <span class="text-[10px] font-mono text-gray-600">Created: ${new Date(cluster.created_at).toLocaleDateString()}</span>
                    
                    <button onclick="upvoteCluster(${cluster.id})" class="glow-btn bg-[#181d3d] border border-[#2d346b] hover:bg-violet-900/20 hover:border-violet-500/50 text-white hover:text-cyan-300 px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition">
                        <span>👍</span> <span>Upvote (${cluster.votes_count})</span>
                    </button>
                </div>
            `;
        } else {
            // Render Moderation Dashboard Tab
            const isApproved = cluster.answer_text ? true : false;
            const textareaId = `answer-input-${cluster.id}`;
            
            card.innerHTML = `
                <!-- Header -->
                <div class="flex items-start justify-between">
                    <div class="flex items-center space-x-2">
                        <span class="px-2.5 py-1 text-xs font-semibold rounded-lg border ${badgeColor}">${cluster.category || 'General'}</span>
                        <span class="text-xs font-mono text-gray-500">Cluster #${cluster.id}</span>
                        ${isApproved ? 
                            `<span class="px-2 py-0.5 text-[9px] bg-green-950/40 border border-green-500/30 text-green-400 rounded">Published</span>` : 
                            `<span class="px-2 py-0.5 text-[9px] bg-yellow-950/40 border border-yellow-500/30 text-yellow-400 rounded">Pending Moderation</span>`
                        }
                    </div>
                    <div class="text-right">
                        <span class="block text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Rank Priority</span>
                        <span class="text-sm font-bold font-mono text-violet-400">${cluster.priority_score}</span>
                    </div>
                </div>

                <!-- Question -->
                <div>
                    <h3 class="text-base font-bold text-white">${cluster.representative_text || 'Unnamed Question'}</h3>
                    <p class="text-xs text-gray-500 mt-1 font-mono">User ID: ${cluster.questions[0]?.user_identifier || 'unknown'}</p>
                </div>

                <!-- AI Draft Editor Panel -->
                <div class="space-y-2">
                    <label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest">Verify & Edit Answer (Stage 5):</label>
                    <textarea id="${textareaId}" rows="3" class="w-full bg-[#080a13] border border-[#1d2244] rounded-xl p-3 text-xs text-[#e0e2ed] focus:outline-none focus:border-violet-500 transition" placeholder="Write or edit the verified answer here...">${cluster.answer_text || cluster.ai_draft_text || ''}</textarea>
                </div>

                <!-- Actions -->
                <div class="flex items-center justify-between pt-2 border-t border-[#171a35]">
                    <span class="text-[10px] font-mono text-gray-600">Total Upvotes: ${cluster.votes_count}</span>
                    
                    <div class="flex space-x-2">
                        <button onclick="approveCluster(${cluster.id}, '${textareaId}')" class="bg-gradient-to-r from-emerald-600 to-green-500 hover:from-emerald-700 hover:to-green-600 text-white px-4 py-2 rounded-xl text-xs font-semibold transition">
                            Approve & Publish FAQ
                        </button>
                    </div>
                </div>
            `;
        }
        
        container.appendChild(card);
    });
}
