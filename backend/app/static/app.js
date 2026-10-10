/**
 * Agentic QE Platform - Frontend Application
 * High-performance Vanilla JavaScript presentation layer
 * Pure Local Execution - Zero External API / Zero Cloud Dependency
 */

// =========================================================================
// 1. API Service (Pure Local Endpoints)
// =========================================================================
const api = {
  async getHealth() {
    const res = await fetch('/api/health');
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  async getChanges() {
    const res = await fetch('/api/changes');
    if (!res.ok) throw new Error('Failed to fetch API changes');
    return res.json();
  },

  async getChange(changeId) {
    const res = await fetch(`/api/changes/${encodeURIComponent(changeId)}`);
    if (!res.ok) throw new Error(`Failed to fetch change ${changeId}`);
    return res.json();
  },

  async getTests(service = '') {
    const url = service ? `/api/tests?service=${encodeURIComponent(service)}` : '/api/tests';
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch regression tests');
    return res.json();
  },

  async runPipeline(changeId) {
    const res = await fetch('/api/pipeline/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ change_id: changeId }),
    });
    if (!res.ok) throw new Error('Pipeline execution failed');
    return res.json();
  },

  async submitReview(reviewPayload) {
    const res = await fetch('/api/review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reviewPayload),
    });
    if (!res.ok) throw new Error('Review submission failed');
    return res.json();
  },

  async getAuditTrail() {
    const res = await fetch('/api/audit');
    if (!res.ok) throw new Error('Failed to fetch audit trail');
    return res.json();
  }
};

// =========================================================================
// 2. State
// =========================================================================
const state = {
  activeTab: 'pipeline',
  backendOnline: false,
  changes: [],
  tests: [],
  auditLogs: [],
  selectedChangeId: 'CHG-101',
  pipelineResult: null,
  testInclusions: {},
  reviewSubmitted: false,
  isLoading: false,
  selectedTestForModal: null,
  expandedAuditIds: new Set(),
  filters: {
    matrixSearch: '',
    matrixService: 'ALL',
    repoSearch: '',
    repoCriticality: 'ALL',
    repoType: 'ALL',
    auditEvent: 'ALL'
  }
};

// Helper: Get active change
function getActiveChange() {
  return state.changes.find(c => c.id === state.selectedChangeId) || state.changes[0];
}

// Helper: Check if test is included
function isTestIncluded(testId, defaultVal) {
  if (state.testInclusions[testId] !== undefined) {
    return state.testInclusions[testId];
  }
  return defaultVal;
}

// Helper: Concise reason text
function getConciseReason(test) {
  if (test.impact_type === 'Direct Endpoint Match') {
    return `Direct match with changed ${test.service.replace('Service', '')} endpoint.`;
  }
  if (test.test_type === 'E2E') {
    return `Critical end-to-end integration dependency on modified service.`;
  }
  return `Upstream dependency on ${test.service}.`;
}

// Helper: Modal explanation text
function getModalSentence(test) {
  if (test.impact_type === 'Direct Endpoint Match') {
    return `Direct match with the changed ${test.service.replace('Service', '')} endpoint route.`;
  }
  if (test.test_type === 'E2E') {
    return `Critical end-to-end user checkout dependency on the modified payment service.`;
  }
  return `Upstream integration dependency on ${test.service}.`;
}

// =========================================================================
// 3. UI Rendering & Updates
// =========================================================================

function updateSystemStatus(isOnline) {
  state.backendOnline = isOnline;
  const pulse = document.getElementById('statusPulse');
  const text = document.getElementById('statusText');
  if (isOnline) {
    pulse.classList.add('online');
    text.textContent = 'System: Ready';
  } else {
    pulse.classList.remove('online');
    text.textContent = 'System: Offline';
  }
}

function renderLocalScenarios() {
  const container = document.getElementById('changeCardsGrid');
  if (!container) return;

  container.innerHTML = state.changes.map(c => {
    const isSelected = c.id === state.selectedChangeId;
    const critClass = c.business_criticality === 'Critical' ? 'badge-critical' : 'badge-high';

    return `
      <div class="scenario-card ${isSelected ? 'active' : ''}" data-change-id="${c.id}">
        <div class="scenario-card-header">
          <span class="scenario-id">${escapeHtml(c.id)}</span>
          <span class="badge ${critClass}">${escapeHtml(c.business_criticality)}</span>
        </div>
        <div class="scenario-title">${escapeHtml(c.title)}</div>
        <div class="scenario-endpoint">${escapeHtml(c.endpoint)}</div>
      </div>
    `;
  }).join('');

  // Add click listeners to cards
  container.querySelectorAll('.scenario-card').forEach(card => {
    card.addEventListener('click', () => {
      const id = card.dataset.changeId;
      state.selectedChangeId = id;
      resetPipelineUI();
      renderLocalScenarios();
      renderActiveChangeSummary();
    });
  });
}

function resetPipelineUI() {
  state.pipelineResult = null;
  state.testInclusions = {};
  state.reviewSubmitted = false;

  const section = document.getElementById('pipelineResultsSection');
  if (section) section.style.display = 'none';

  // Reset displayed metrics
  const kpiEvaluated = document.getElementById('kpiEvaluated');
  const kpiImpacted = document.getElementById('kpiImpacted');
  const kpiHigh = document.getElementById('kpiHigh');
  const kpiMedium = document.getElementById('kpiMedium');
  if (kpiEvaluated) kpiEvaluated.textContent = '0';
  if (kpiImpacted) kpiImpacted.textContent = '0';
  if (kpiHigh) kpiHigh.textContent = '0';
  if (kpiMedium) kpiMedium.textContent = '0';

  // Reset Stepper & Execution Pipeline status
  const pipelineIdLabel = document.getElementById('pipelineIdLabel');
  if (pipelineIdLabel) pipelineIdLabel.textContent = 'ID: Pending Run';
  const stepperImpactTitle = document.getElementById('stepperImpactTitle');
  if (stepperImpactTitle) stepperImpactTitle.textContent = 'Candidates Found';
  const stepperReview = document.getElementById('stepperReviewStatus');
  if (stepperReview) {
    stepperReview.textContent = 'Pending Action';
    stepperReview.className = 'step-status';
  }

  // Reset Prioritized tests table
  const tbody = document.getElementById('prioritizedTestsBody');
  if (tbody) tbody.innerHTML = '';
  const totalRuntimeLabel = document.getElementById('totalRuntimeLabel');
  if (totalRuntimeLabel) totalRuntimeLabel.textContent = 'Total Runtime: 0.0s';

  // Reset Review Gate
  const reviewSelectedCount = document.getElementById('reviewSelectedCount');
  if (reviewSelectedCount) reviewSelectedCount.textContent = '0';
  const reviewTotalCount = document.getElementById('reviewTotalCount');
  if (reviewTotalCount) reviewTotalCount.textContent = '0';
  const banner = document.getElementById('reviewSubmittedBanner');
  if (banner) banner.style.display = 'none';
  const form = document.getElementById('reviewActionsForm');
  if (form) form.style.display = 'flex';
}

function renderActiveChangeSummary() {
  const activeChange = getActiveChange();
  if (!activeChange) return;

  document.getElementById('summaryEndpoint').textContent = activeChange.endpoint || '';
  document.getElementById('summaryService').textContent = activeChange.service || '';
  
  const sourceBadge = document.getElementById('summarySourceBadge');
  if (sourceBadge) {
    sourceBadge.textContent = activeChange.id;
    sourceBadge.className = 'badge badge-version';
  }

  const critEl = document.getElementById('summaryCriticality');
  critEl.textContent = activeChange.business_criticality || 'Medium';
  critEl.className = 'badge mt-1 ' + (activeChange.business_criticality === 'Critical' ? 'badge-critical' : 'badge-high');

  const breakingEl = document.getElementById('summaryBreaking');
  if (activeChange.is_breaking) {
    breakingEl.textContent = 'Breaking (Yes)';
    breakingEl.className = 'meta-value font-semibold text-rose';
  } else {
    breakingEl.textContent = 'Compatible (No)';
    breakingEl.className = 'meta-value font-semibold text-teal';
  }
}

function renderPipelineResults() {
  const section = document.getElementById('pipelineResultsSection');
  if (!state.pipelineResult) {
    resetPipelineUI();
    return;
  }
  section.style.display = 'block';

  const res = state.pipelineResult;

  // Header & Stepper
  document.getElementById('pipelineIdLabel').textContent = `ID: ${res.pipeline_id || 'PIPELINE-RUN'}`;
  document.getElementById('stepperImpactTitle').textContent = `${res.impacted_count || 0} Candidates Found`;
  
  const stepperReview = document.getElementById('stepperReviewStatus');
  if (state.reviewSubmitted) {
    stepperReview.textContent = 'Approved';
    stepperReview.className = 'step-status text-emerald';
  } else {
    stepperReview.textContent = 'Pending Action';
    stepperReview.className = 'step-status text-amber';
  }

  // KPIs
  document.getElementById('kpiEvaluated').textContent = res.total_tests_evaluated || 0;
  document.getElementById('kpiImpacted').textContent = res.impacted_count || 0;
  document.getElementById('kpiHigh').textContent = res.high_priority_count || 0;
  document.getElementById('kpiMedium').textContent = res.medium_priority_count || 0;

  // Runtime
  document.getElementById('totalRuntimeLabel').textContent = `Total Runtime: ${res.total_execution_time_seconds || 0}s`;

  // Tests Table
  const tbody = document.getElementById('prioritizedTestsBody');
  tbody.innerHTML = (res.impacted_tests || []).map(test => {
    const included = isTestIncluded(test.id, test.is_included_in_run);
    const priorityClass = test.priority === 'High' ? 'badge-priority-high' : test.priority === 'Medium' ? 'badge-priority-medium' : 'badge-priority-low';

    return `
      <tr class="${!included ? 'row-excluded' : ''}" data-test-id="${test.id}">
        <td class="text-center">
          <input type="checkbox" class="checkbox-custom test-toggle-checkbox" data-test-id="${test.id}" ${included ? 'checked' : ''}>
        </td>
        <td class="text-center">
          <span class="badge ${priorityClass}">${escapeHtml(test.priority)}</span>
        </td>
        <td class="font-mono font-bold text-slate">${escapeHtml(test.id)}</td>
        <td>
          <div class="font-medium text-slate">${escapeHtml(test.name)}</div>
          <div class="font-mono text-muted text-xs mt-0-5">${escapeHtml(test.target_endpoints?.[0] || '')} • ${escapeHtml(test.service || '')}</div>
        </td>
        <td class="text-center font-mono font-bold text-teal">${test.score}</td>
        <td class="text-xs text-secondary">${escapeHtml(getConciseReason(test))}</td>
        <td class="text-right">
          <button class="btn btn-secondary btn-xs btn-why" data-test-id="${test.id}">Why This Test?</button>
        </td>
      </tr>
    `;
  }).join('');

  // Attach table event listeners
  tbody.querySelectorAll('.test-toggle-checkbox').forEach(cb => {
    cb.addEventListener('change', (e) => {
      const testId = cb.dataset.testId;
      state.testInclusions[testId] = e.target.checked;
      renderPipelineResults();
    });
  });

  tbody.querySelectorAll('.btn-why').forEach(btn => {
    btn.addEventListener('click', () => {
      const testId = btn.dataset.testId;
      const test = res.impacted_tests.find(t => t.id === testId);
      if (test) openScoreModal(test);
    });
  });

  // Human Review Gate status
  updateReviewGateUI();
}

function updateReviewGateUI() {
  if (!state.pipelineResult) return;
  const tests = state.pipelineResult.impacted_tests || [];
  const selectedCount = tests.filter(t => isTestIncluded(t.id, t.is_included_in_run)).length;
  document.getElementById('reviewSelectedCount').textContent = selectedCount;
  document.getElementById('reviewTotalCount').textContent = tests.length;

  const banner = document.getElementById('reviewSubmittedBanner');
  const form = document.getElementById('reviewActionsForm');

  if (state.reviewSubmitted) {
    banner.style.display = 'flex';
    form.style.display = 'none';
  } else {
    banner.style.display = 'none';
    form.style.display = 'flex';
  }
}

function openScoreModal(test) {
  state.selectedTestForModal = test;
  const breakdown = test.score_breakdown || {};

  document.getElementById('modalTestIdSubtitle').textContent = `${test.id} - ${test.name}`;
  document.getElementById('modalSentence').textContent = getModalSentence(test);

  const endpointPts = breakdown.direct_endpoint_points || breakdown.service_coupling_points || 0;
  document.getElementById('ptsEndpoint').innerHTML = `+${Number(endpointPts).toFixed(1)} <small>/ 35</small>`;
  document.getElementById('ptsCriticality').innerHTML = `+${Number(breakdown.criticality_points || 0).toFixed(1)} <small>/ 25</small>`;
  document.getElementById('ptsFailure').innerHTML = `+${Number(breakdown.failure_history_points || 0).toFixed(1)} <small>/ 25</small>`;
  document.getElementById('ptsBreaking').innerHTML = `+${Number(breakdown.breaking_change_points || 0).toFixed(1)} <small>/ 10</small>`;
  document.getElementById('ptsFlakiness').innerHTML = `+${Number(breakdown.flakiness_points || 0).toFixed(1)} <small>/ 5</small>`;
  document.getElementById('ptsTotal').innerHTML = `${test.score} <small>/ 100</small>`;

  const badge = document.getElementById('modalPriorityBadge');
  badge.textContent = `${test.priority} Priority`;
  badge.className = 'badge font-mono ' + (test.priority === 'High' ? 'badge-priority-high' : test.priority === 'Medium' ? 'badge-priority-medium' : 'badge-priority-low');

  document.getElementById('scoreModal').style.display = 'flex';
}

function closeScoreModal() {
  document.getElementById('scoreModal').style.display = 'none';
  state.selectedTestForModal = null;
}

// Render Impact Matrix
function renderImpactMatrix() {
  const serviceFilter = state.filters.matrixService;
  const searchTerm = state.filters.matrixSearch.toLowerCase();

  // Populate services dropdown if not populated
  const select = document.getElementById('matrixServiceFilter');
  if (select.children.length <= 1) {
    const services = ['ALL', ...new Set(state.tests.map(t => t.service))];
    select.innerHTML = services.map(s => `<option value="${s}">${s === 'ALL' ? 'All Services' : s}</option>`).join('');
  }

  // Filter tests
  const filteredTests = state.tests.filter(t => {
    const matchesSearch = t.name.toLowerCase().includes(searchTerm) ||
      t.id.toLowerCase().includes(searchTerm) ||
      t.target_endpoints.some(ep => ep.toLowerCase().includes(searchTerm));
    const matchesService = serviceFilter === 'ALL' || t.service === serviceFilter;
    return matchesSearch && matchesService;
  });

  // Table header
  const thead = document.getElementById('matrixHead');
  thead.innerHTML = `
    <tr>
      <th>Test Identifier</th>
      <th>Service</th>
      <th>Target Endpoints</th>
      ${state.changes.map(c => `
        <th class="text-center" style="border-left: 1px solid var(--border-color);">
          <span class="font-mono text-teal block">${escapeHtml(c.id)}</span>
          <span class="text-muted block text-xs" style="text-transform: none; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(c.service)}</span>
        </th>
      `).join('')}
    </tr>
  `;

  // Table body
  const tbody = document.getElementById('matrixBody');
  tbody.innerHTML = filteredTests.map(test => {
    return `
      <tr>
        <td class="font-mono font-medium text-slate">
          <div>${escapeHtml(test.id)}</div>
          <div class="text-muted font-sans text-xs mt-0-5" style="max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(test.name)}</div>
        </td>
        <td>
          <span class="badge badge-version">${escapeHtml(test.service)}</span>
        </td>
        <td class="font-mono text-muted text-xs">
          ${(test.target_endpoints || []).map(ep => `<div>${escapeHtml(ep)}</div>`).join('')}
        </td>
        ${state.changes.map(c => {
          const isDirect = (test.target_endpoints || []).includes(c.endpoint);
          const isServiceMatch = test.service.toLowerCase() === c.service.toLowerCase();

          if (isDirect) {
            return `<td class="text-center" style="border-left: 1px solid var(--border-color);"><span class="badge" style="background-color: var(--teal-950); color: var(--teal-500); border: 1px solid var(--teal-700);">Direct</span></td>`;
          } else if (isServiceMatch) {
            return `<td class="text-center" style="border-left: 1px solid var(--border-color);"><span class="badge badge-version">Service Dep</span></td>`;
          } else {
            return `<td class="text-center text-muted font-mono" style="border-left: 1px solid var(--border-color);">-</td>`;
          }
        }).join('')}
      </tr>
    `;
  }).join('');
}

// Render Test Repository
function renderTestRepository() {
  const searchTerm = state.filters.repoSearch.toLowerCase();
  const critFilter = state.filters.repoCriticality;
  const typeFilter = state.filters.repoType;

  const filteredTests = state.tests.filter(t => {
    const matchesSearch = t.name.toLowerCase().includes(searchTerm) ||
      t.id.toLowerCase().includes(searchTerm) ||
      t.service.toLowerCase().includes(searchTerm);
    const matchesCrit = critFilter === 'ALL' || t.business_criticality === critFilter;
    const matchesType = typeFilter === 'ALL' || t.test_type === typeFilter;
    return matchesSearch && matchesCrit && matchesType;
  });

  const tbody = document.getElementById('repoTestsBody');
  tbody.innerHTML = filteredTests.map(test => {
    const critClass = test.business_criticality === 'Critical' ? 'badge-critical' : test.business_criticality === 'High' ? 'badge-high' : 'badge-version';
    const statusClass = test.last_run_status === 'PASSED' ? 'badge-emerald' : 'badge-critical';
    const failureRate = (test.historical_failure_rate * 100).toFixed(0);

    return `
      <tr>
        <td>
          <span class="font-mono font-bold text-teal">${escapeHtml(test.id)}</span>
          <div class="font-medium text-slate mt-0-5">${escapeHtml(test.name)}</div>
          <div class="text-muted text-xs mt-0-5" style="max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(test.description || '')}</div>
        </td>
        <td class="font-mono text-secondary">${escapeHtml(test.service)}</td>
        <td class="font-mono">${escapeHtml(test.test_type)}</td>
        <td><span class="badge ${critClass}">${escapeHtml(test.business_criticality)}</span></td>
        <td class="text-center font-mono ${test.historical_failure_rate > 0.25 ? 'text-rose font-bold' : 'text-slate'}">${failureRate}%</td>
        <td class="text-center font-mono text-muted">${test.execution_time_seconds}s</td>
        <td class="text-center font-mono text-muted">${(test.flakiness_score * 100).toFixed(0)}%</td>
        <td><span class="badge ${statusClass}">${escapeHtml(test.last_run_status)}</span></td>
        <td>
          <div style="display: flex; flex-wrap: wrap; gap: 0.25rem;">
            ${(test.tags || []).map(tg => `<span class="badge badge-version">${escapeHtml(tg)}</span>`).join('')}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

// Render Audit Trail
function renderAuditTrail() {
  const eventFilter = state.filters.auditEvent;
  const filtered = state.auditLogs.filter(log => {
    return eventFilter === 'ALL' || log.event_type === eventFilter;
  });

  const tbody = document.getElementById('auditTableBody');
  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted" style="padding: 2rem;">No audit events recorded yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(log => {
    const isExpanded = state.expandedAuditIds.has(log.id);
    
    let status = 'Completed';
    let statusClass = 'badge-emerald';

    if (log.event_type === 'HUMAN_REVIEW') {
      status = log.details?.decision || 'Approved';
      statusClass = status === 'APPROVED' ? 'badge-emerald' : status === 'MODIFIED' ? 'badge-amber' : 'badge-critical';
    }

    let timeStr = log.timestamp;
    try {
      timeStr = new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {}

    return `
      <tr>
        <td class="font-mono text-muted">${escapeHtml(timeStr)}</td>
        <td class="font-mono text-teal font-medium">${escapeHtml(log.event_type)}</td>
        <td class="text-center">
          <span class="badge ${statusClass}">${escapeHtml(status)}</span>
        </td>
        <td class="font-medium text-slate" style="max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(log.actor || '')}</td>
        <td class="text-secondary text-xs" style="max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(log.action || '')}</td>
        <td class="text-right">
          <button class="btn btn-secondary btn-xs btn-audit-expand" data-log-id="${log.id}">
            ${isExpanded ? '▲' : '▼'}
          </button>
        </td>
      </tr>
      ${isExpanded && log.details ? `
        <tr style="background-color: var(--bg-card-inner);">
          <td colspan="6" style="padding: 0.75rem 1rem;">
            <div style="background-color: var(--bg-app); border: 1px solid var(--border-color); border-radius: 0.25rem; padding: 0.75rem; font-family: var(--font-mono); font-size: 11px; overflow-x: auto; color: var(--text-secondary);">
              <pre>${escapeHtml(JSON.stringify(log.details, null, 2))}</pre>
            </div>
          </td>
        </tr>
      ` : ''}
    `;
  }).join('');

  tbody.querySelectorAll('.btn-audit-expand').forEach(btn => {
    btn.addEventListener('click', () => {
      const logId = btn.dataset.logId;
      if (state.expandedAuditIds.has(logId)) {
        state.expandedAuditIds.delete(logId);
      } else {
        state.expandedAuditIds.add(logId);
      }
      renderAuditTrail();
    });
  });
}

// Utility: HTML escaping
function escapeHtml(str) {
  if (typeof str !== 'string') return String(str || '');
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// =========================================================================
// 4. Action Handlers
// =========================================================================

async function triggerPipelineRun() {
  const activeChange = getActiveChange();
  if (!activeChange) return;

  const btn = document.getElementById('btnRunPipeline');
  const btnText = document.getElementById('btnRunPipelineText');
  
  try {
    state.isLoading = true;
    btn.disabled = true;
    btnText.textContent = 'Analyzing...';
    hideErrorBanner();

    const result = await api.runPipeline(activeChange.id);
    state.pipelineResult = result;
    state.testInclusions = {}; // Reset overrides for new run

    renderPipelineResults();

    // Refresh audit logs
    const logs = await api.getAuditTrail();
    state.auditLogs = logs;
    renderAuditTrail();
  } catch (err) {
    showErrorBanner('Failed to execute pipeline: ' + err.message);
  } finally {
    state.isLoading = false;
    btn.disabled = false;
    btnText.textContent = 'Analyze Change & Prioritize Tests';
  }
}

async function submitHumanReview(decision) {
  if (!state.pipelineResult) return;
  const activeChange = getActiveChange();
  const justification = document.getElementById('reviewJustificationInput').value.trim();

  const selectedIds = state.pipelineResult.impacted_tests
    .filter(t => isTestIncluded(t.id, t.is_included_in_run))
    .map(t => t.id);

  const payload = {
    change_id: activeChange ? activeChange.id : 'CHG-101',
    decision: decision,
    reviewed_by: 'QA Lead',
    comments: justification || `Human review action: ${decision}`,
    selected_test_ids: selectedIds
  };

  try {
    await api.submitReview(payload);
    state.reviewSubmitted = true;
    updateReviewGateUI();

    // Stepper review step update
    const stepperReview = document.getElementById('stepperReviewStatus');
    stepperReview.textContent = 'Approved';
    stepperReview.className = 'step-status text-emerald';

    // Refresh audit trail
    const logs = await api.getAuditTrail();
    state.auditLogs = logs;
    renderAuditTrail();
  } catch (err) {
    showErrorBanner('Failed to submit human review: ' + err.message);
  }
}

function showErrorBanner(message) {
  const banner = document.getElementById('errorBanner');
  const msgEl = document.getElementById('errorMessage');
  msgEl.textContent = message;
  banner.style.display = 'flex';
}

function hideErrorBanner() {
  document.getElementById('errorBanner').style.display = 'none';
}

// =========================================================================
// 5. Tab Navigation
// =========================================================================
function switchTab(tabId) {
  state.activeTab = tabId;

  // Update navbar tab styling
  document.querySelectorAll('.nav-tab').forEach(btn => {
    if (btn.dataset.tab === tabId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Show corresponding tab section
  const tabMap = {
    pipeline: 'tabContentPipeline',
    matrix: 'tabContentMatrix',
    repository: 'tabContentRepository',
    audit: 'tabContentAudit',
    architecture: 'tabContentArchitecture'
  };

  Object.keys(tabMap).forEach(key => {
    const el = document.getElementById(tabMap[key]);
    if (el) {
      el.style.display = key === tabId ? 'block' : 'none';
    }
  });

  // Re-render specific views on tab activation
  if (tabId === 'matrix') renderImpactMatrix();
  if (tabId === 'repository') renderTestRepository();
  if (tabId === 'audit') renderAuditTrail();
}

// =========================================================================
// 6. Application Initialization
// =========================================================================
async function initApp() {
  try {
    hideErrorBanner();
    
    // Check health
    await api.getHealth();
    updateSystemStatus(true);

    // Fetch changes, tests, and audit trail in parallel
    const [fetchedChanges, fetchedTests, fetchedAudit] = await Promise.all([
      api.getChanges(),
      api.getTests(),
      api.getAuditTrail()
    ]);

    state.changes = fetchedChanges;
    state.tests = fetchedTests;
    state.auditLogs = fetchedAudit;

    if (fetchedChanges.length > 0) {
      state.selectedChangeId = fetchedChanges[0].id;
    }

    renderLocalScenarios();
    renderActiveChangeSummary();
    resetPipelineUI();
    renderImpactMatrix();
    renderTestRepository();
    renderAuditTrail();

    // Do NOT automatically run pipeline on initial load.
    // Analysis is executed ONLY when the user clicks "Analyze Change & Prioritize Tests".
  } catch (err) {
    console.error('Initialization error:', err);
    updateSystemStatus(false);
    showErrorBanner('Unable to connect to the Agentic QE backend. Ensure FastAPI server is running.');
  }
}

// Attach DOM Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  // Tab switching
  document.getElementById('navTabs').addEventListener('click', (e) => {
    const tabBtn = e.target.closest('.nav-tab');
    if (tabBtn && tabBtn.dataset.tab) {
      switchTab(tabBtn.dataset.tab);
    }
  });

  // Retry connection
  document.getElementById('btnRetryConnection').addEventListener('click', initApp);

  // Run pipeline button
  document.getElementById('btnRunPipeline').addEventListener('click', triggerPipelineRun);

  // Human Review Buttons
  document.getElementById('btnReviewReject').addEventListener('click', () => submitHumanReview('REJECTED'));
  document.getElementById('btnReviewModify').addEventListener('click', () => submitHumanReview('MODIFIED'));
  document.getElementById('btnReviewApprove').addEventListener('click', () => submitHumanReview('APPROVED'));
  document.getElementById('btnEditReview').addEventListener('click', () => {
    state.reviewSubmitted = false;
    updateReviewGateUI();
  });

  // Modal controls
  document.getElementById('btnModalClose').addEventListener('click', closeScoreModal);
  document.getElementById('btnModalFooterClose').addEventListener('click', closeScoreModal);
  document.getElementById('scoreModal').addEventListener('click', (e) => {
    if (e.target.id === 'scoreModal') closeScoreModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeScoreModal();
  });

  // Impact Matrix search & filter
  document.getElementById('matrixSearchInput').addEventListener('input', (e) => {
    state.filters.matrixSearch = e.target.value;
    renderImpactMatrix();
  });
  document.getElementById('matrixServiceFilter').addEventListener('change', (e) => {
    state.filters.matrixService = e.target.value;
    renderImpactMatrix();
  });

  // Test Repository search & filters
  document.getElementById('repoSearchInput').addEventListener('input', (e) => {
    state.filters.repoSearch = e.target.value;
    renderTestRepository();
  });
  document.getElementById('repoCriticalityFilter').addEventListener('change', (e) => {
    state.filters.repoCriticality = e.target.value;
    renderTestRepository();
  });
  document.getElementById('repoTypeFilter').addEventListener('change', (e) => {
    state.filters.repoType = e.target.value;
    renderTestRepository();
  });

  // Audit trail filter & refresh
  document.getElementById('auditEventFilter').addEventListener('change', (e) => {
    state.filters.auditEvent = e.target.value;
    renderAuditTrail();
  });
  document.getElementById('btnRefreshAudit').addEventListener('click', async () => {
    try {
      state.auditLogs = await api.getAuditTrail();
      renderAuditTrail();
    } catch (err) {
      console.error('Audit refresh error:', err);
    }
  });

  // Start app
  initApp();
});
