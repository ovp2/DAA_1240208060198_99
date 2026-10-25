/**
 * Job Scheduling System - Interactive Visualizer & Controller
 * Features:
 * - Dynamic Gantt Chart Engine with Animation & Tooltips
 * - Execution Step-by-Step Player (Play/Pause/Scrub)
 * - Multi-Algorithm Comparison Canvas Renderer
 * - Resource Utilization Charting
 * - Job Modal Management & Preset Handlers
 */

// Global state
const AppState = {
  currentTimeline: [],
  currentMetrics: {},
  currentTime: 0,
  maxTime: 0,
  isPlaying: false,
  playInterval: null,
  playSpeed: 1000, // ms per tick
};

// ==========================================
// TOAST NOTIFICATIONS
// ==========================================
function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = "toast";
  let icon = "⚡";
  if (type === "success") icon = "✅";
  if (type === "error") icon = "⚠️";

  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ==========================================
// TOOLTIP CONTROLLER
// ==========================================
let tooltipEl = null;

function initTooltip() {
  tooltipEl = document.getElementById("cyber-tooltip");
  if (!tooltipEl) {
    tooltipEl = document.createElement("div");
    tooltipEl.id = "cyber-tooltip";
    tooltipEl.className = "cyber-tooltip";
    document.body.appendChild(tooltipEl);
  }
}

function showTooltip(e, content) {
  if (!tooltipEl) initTooltip();
  tooltipEl.innerHTML = content;
  tooltipEl.style.display = "block";
  updateTooltipPosition(e);
}

function updateTooltipPosition(e) {
  if (!tooltipEl) return;
  const offset = 15;
  let x = e.clientX + offset;
  let y = e.clientY + offset;

  // Prevent overflowing window
  if (x + tooltipEl.offsetWidth > window.innerWidth) {
    x = e.clientX - tooltipEl.offsetWidth - offset;
  }
  if (y + tooltipEl.offsetHeight > window.innerHeight) {
    y = e.clientY - tooltipEl.offsetHeight - offset;
  }

  tooltipEl.style.left = `${x}px`;
  tooltipEl.style.top = `${y}px`;
}

function hideTooltip() {
  if (tooltipEl) tooltipEl.style.display = "none";
}

// ==========================================
// GANTT CHART ENGINE
// ==========================================
function renderGanttChart(timeline, containerId = "gantt-track", axisId = "time-axis") {
  const track = document.getElementById(containerId);
  const axis = document.getElementById(axisId);
  if (!track) return;

  track.innerHTML = "";
  if (axis) axis.innerHTML = "";

  if (!timeline || timeline.length === 0) {
    track.innerHTML = `<div style="text-align: center; color: var(--text-dim); padding: 1.5rem;">No execution timeline available. Run an algorithm to visualize.</div>`;
    return;
  }

  const makespan = Math.max(...timeline.map(t => t.end), 1);
  AppState.maxTime = makespan;

  timeline.forEach((item, index) => {
    const leftPct = (item.start / makespan) * 100;
    const widthPct = (item.duration / makespan) * 100;

    const block = document.createElement("div");
    block.className = `gantt-block ${item.type === 'idle' ? 'idle' : ''}`;
    block.style.left = `${leftPct}%`;
    block.style.width = `max(${widthPct}%, 20px)`;

    if (item.type === "job") {
      const jobColor = item.color || `hsl(${(item.job_id * 67) % 360}, 75%, 55%)`;
      block.style.background = `linear-gradient(135deg, ${jobColor}, adjust-hue(${jobColor}, 20deg))`;
      block.style.borderColor = jobColor;
      block.style.color = "#FFFFFF";
      block.innerText = `${item.job_name} [${item.duration}]`;

      // Tooltip content
      const tooltipContent = `
        <div style="font-weight: 700; color: #38BDF8; margin-bottom: 4px; font-size: 0.95rem;">${item.job_name}</div>
        <div><strong>Job ID:</strong> ${item.job_id}</div>
        <div><strong>Time Window:</strong> [${item.start} → ${item.end}] (Duration: ${item.duration})</div>
        <div><strong>Priority:</strong> Level ${item.priority || 1}</div>
        <div><strong>Profit Value:</strong> $${item.profit || 0}</div>
      `;

      block.addEventListener("mouseenter", (e) => showTooltip(e, tooltipContent));
      block.addEventListener("mousemove", (e) => updateTooltipPosition(e));
      block.addEventListener("mouseleave", hideTooltip);
    } else {
      block.innerText = `Idle (${item.duration})`;
      const tooltipContent = `
        <div style="font-weight: 700; color: #94A3B8;">CPU Idle State</div>
        <div>No scheduled process ready between t=${item.start} and t=${item.end}.</div>
      `;
      block.addEventListener("mouseenter", (e) => showTooltip(e, tooltipContent));
      block.addEventListener("mousemove", (e) => updateTooltipPosition(e));
      block.addEventListener("mouseleave", hideTooltip);
    }

    track.appendChild(block);
  });

  // Render Time Axis Ticks
  if (axis) {
    const tickStep = makespan > 30 ? 5 : (makespan > 15 ? 2 : 1);
    for (let t = 0; t <= makespan; t += tickStep) {
      const tick = document.createElement("div");
      tick.className = "time-tick";
      tick.style.left = `${(t / makespan) * 100}%`;
      tick.innerText = t;
      axis.appendChild(tick);
    }
    // Final tick if not aligned
    if (makespan % tickStep !== 0) {
      const finalTick = document.createElement("div");
      finalTick.className = "time-tick";
      finalTick.style.left = "100%";
      finalTick.innerText = makespan;
      axis.appendChild(finalTick);
    }
  }
}

// ==========================================
// STEP-BY-STEP TIMELINE PLAYER
// ==========================================
function startPlayback() {
  if (AppState.isPlaying) return;
  AppState.isPlaying = true;
  const playBtn = document.getElementById("btn-play");
  if (playBtn) playBtn.innerHTML = "⏸ Pause";

  AppState.playInterval = setInterval(() => {
    if (AppState.currentTime >= AppState.maxTime) {
      pausePlayback();
      return;
    }
    stepPlayback(1);
  }, AppState.playSpeed);
}

function pausePlayback() {
  AppState.isPlaying = false;
  if (AppState.playInterval) clearInterval(AppState.playInterval);
  const playBtn = document.getElementById("btn-play");
  if (playBtn) playBtn.innerHTML = "▶ Play";
}

function togglePlayback() {
  if (AppState.isPlaying) {
    pausePlayback();
  } else {
    if (AppState.currentTime >= AppState.maxTime) {
      AppState.currentTime = 0;
    }
    startPlayback();
  }
}

function stepPlayback(stepSize = 1) {
  AppState.currentTime = Math.min(AppState.maxTime, AppState.currentTime + stepSize);
  updatePlaybackUI();
}

function resetPlayback() {
  pausePlayback();
  AppState.currentTime = 0;
  updatePlaybackUI();
}

function updatePlaybackUI() {
  const scrubber = document.getElementById("timeline-scrubber");
  const timeDisplay = document.getElementById("current-time-display");
  const playhead = document.getElementById("gantt-playhead");

  if (scrubber) scrubber.value = AppState.currentTime;
  if (timeDisplay) timeDisplay.innerText = `t = ${AppState.currentTime} / ${AppState.maxTime}`;

  if (playhead && AppState.maxTime > 0) {
    const leftPct = (AppState.currentTime / AppState.maxTime) * 100;
    playhead.style.left = `${leftPct}%`;
    playhead.style.display = "block";
  }

  // Highlight currently active job in results table
  const activeItem = AppState.currentTimeline.find(
    t => t.start <= AppState.currentTime && AppState.currentTime < t.end
  );
  highlightActiveJobRow(activeItem ? activeItem.job_id : null);
}

function highlightActiveJobRow(jobId) {
  document.querySelectorAll(".job-row").forEach(row => {
    if (jobId && row.dataset.jobId === String(jobId)) {
      row.style.background = "rgba(99, 102, 241, 0.25)";
      row.style.boxShadow = "inset 0 0 10px rgba(99, 102, 241, 0.5)";
    } else {
      row.style.background = "";
      row.style.boxShadow = "";
    }
  });
}

// ==========================================
// PRESET & JOB MANAGEMENT HANDLERS
// ==========================================
async function loadPreset(presetName) {
  try {
    const response = await fetch("/api/jobs/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ preset: presetName })
    });
    const data = await response.json();
    if (data.success) {
      showToast(`Loaded preset: ${presetName}`, "success");
      setTimeout(() => window.location.reload(), 600);
    }
  } catch (err) {
    showToast("Failed to load preset.", "error");
  }
}

async function deleteJob(jobId) {
  if (!confirm(`Are you sure you want to delete Job #${jobId}?`)) return;
  try {
    const response = await fetch(`/api/jobs/${jobId}`, { method: "DELETE" });
    const data = await response.json();
    if (data.success) {
      showToast("Job removed successfully.", "success");
      const row = document.getElementById(`job-row-${jobId}`);
      if (row) row.remove();
      setTimeout(() => window.location.reload(), 600);
    }
  } catch (err) {
    showToast("Error deleting job.", "error");
  }
}

// ==========================================
// ALGORITHM RUNNER
// ==========================================
async function runSelectedAlgorithm() {
  const selectEl = document.getElementById("algo-select");
  const capacityEl = document.getElementById("knapsack-capacity");
  if (!selectEl) return;

  const algoKey = selectEl.value;
  const capacity = capacityEl ? capacityEl.value : null;

  showToast(`Running ${selectEl.options[selectEl.selectedIndex].text}...`, "info");

  try {
    const response = await fetch("/api/schedule/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ algorithm: algoKey, capacity: capacity })
    });

    const data = await response.json();
    if (data.success && data.result) {
      const res = data.result;
      AppState.currentTimeline = res.timeline;
      AppState.currentMetrics = res.metrics;
      AppState.currentTime = 0;

      // Render Gantt
      renderGanttChart(res.timeline);

      // Update Metric Cards
      updateMetricCards(res.metrics);

      // Update Breakdown Table
      updateJobResultsTable(res.job_results);

      // Handle DP Visualization
      renderDPDetails(res);

      // Reset timeline player
      const scrubber = document.getElementById("timeline-scrubber");
      if (scrubber) {
        scrubber.max = res.metrics.makespan;
        scrubber.value = 0;
      }
      updatePlaybackUI();

      showToast(`${res.algorithm_name} scheduled successfully!`, "success");
    }
  } catch (err) {
    showToast("Failed to execute scheduling algorithm.", "error");
    console.error(err);
  }
}

function updateMetricCards(m) {
  const map = {
    "metric-makespan": m.makespan,
    "metric-cpu-util": `${m.cpu_utilization}%`,
    "metric-avg-wt": `${m.avg_waiting_time} units`,
    "metric-avg-tat": `${m.avg_turnaround_time} units`,
    "metric-profit": `$${m.total_profit}`,
    "metric-deadline-rate": `${m.deadline_compliance_rate}% (${m.deadlines_met}/${m.total_jobs})`,
    "metric-throughput": `${m.throughput} jobs/t`
  };

  for (const [id, val] of Object.entries(map)) {
    const el = document.getElementById(id);
    if (el) el.innerText = val;
  }
}

function updateJobResultsTable(results) {
  const tbody = document.getElementById("results-tbody");
  if (!tbody) return;

  tbody.innerHTML = "";
  results.forEach(j => {
    const isCompleted = j.start_time !== null;
    const row = document.createElement("tr");
    row.className = "job-row";
    row.dataset.jobId = j.id;

    row.innerHTML = `
      <td><strong>${j.name}</strong></td>
      <td>${j.arrival_time}</td>
      <td>${j.burst_time}</td>
      <td><span class="badge ${j.priority <= 2 ? 'badge-danger' : 'badge-warning'}">P${j.priority}</span></td>
      <td>${j.deadline}</td>
      <td><strong style="color: var(--accent-emerald)">$${j.profit}</strong></td>
      <td>${isCompleted ? j.start_time : '-'}</td>
      <td>${isCompleted ? j.completion_time : '-'}</td>
      <td>${isCompleted ? j.waiting_time : '-'}</td>
      <td>${isCompleted ? j.turnaround_time : '-'}</td>
      <td>
        <span class="badge ${j.met_deadline ? 'badge-success' : 'badge-danger'}">
          ${j.met_deadline ? '✓ On Time' : `+${j.tardiness} Late`}
        </span>
      </td>
      <td>
        <span class="badge ${isCompleted ? 'badge-success' : 'badge-danger'}">
          ${j.status}
        </span>
      </td>
    `;
    tbody.appendChild(row);
  });
}

function renderDPDetails(res) {
  const dpSection = document.getElementById("dp-visualizer-section");
  if (!dpSection) return;

  if (res.algorithm_key === "dp_interval" && res.dp_table && res.dp_table.length > 0) {
    dpSection.style.display = "block";
    const container = document.getElementById("dp-table-container");
    if (!container) return;

    let html = `
      <div style="margin-bottom: 1rem; color: var(--accent-cyan); font-weight: 600;">
        Recurrence: <code>OPT(j) = max(OPT(j - 1), v_j + OPT(p(j)))</code>
      </div>
      <div class="table-container">
        <table class="cyber-table">
          <thead>
            <tr>
              <th>Step (j)</th>
              <th>Job Name</th>
              <th>Interval [s, f]</th>
              <th>Profit (v_j)</th>
              <th>Compatible Job p(j)</th>
              <th>Include: v_j + OPT(p)</th>
              <th>Exclude: OPT(j-1)</th>
              <th>Decision</th>
              <th>Optimal OPT(j)</th>
            </tr>
          </thead>
          <tbody>
    `;

    res.dp_table.forEach(step => {
      html += `
        <tr>
          <td><strong>j = ${step.step}</strong></td>
          <td>${step.job_name}</td>
          <td>[${step.start}, ${step.end}]</td>
          <td>$${step.profit}</td>
          <td>${step.compatible_prior_job} (p=${step.p_index})</td>
          <td>$${step.include_val}</td>
          <td>$${step.exclude_val}</td>
          <td><span class="badge ${step.chosen === 'Include' ? 'badge-success' : 'badge-warning'}">${step.chosen}</span></td>
          <td><strong style="color: var(--accent-emerald)">$${step.dp_value}</strong></td>
        </tr>
      `;
    });

    html += `</tbody></table></div>`;
    container.innerHTML = html;
  } else if (res.algorithm_key === "dp_knapsack" && res.dp_grid) {
    dpSection.style.display = "block";
    const container = document.getElementById("dp-table-container");
    if (!container) return;

    let html = `
      <div style="margin-bottom: 1rem; color: var(--accent-rose); font-weight: 600;">
        Capacity Budget: <code>W = ${res.capacity} units</code> | Maximum Profit Achieved: <code>$${res.metrics.total_profit}</code>
      </div>
      <div class="table-container">
        <table class="cyber-table">
          <thead>
            <tr>
              ${res.dp_grid.headers.map(h => `<th>${h}</th>`).join('')}
            </tr>
          </thead>
          <tbody>
    `;

    res.dp_grid.rows.forEach(r => {
      html += `<tr>${r.map((cell, idx) => idx === 0 ? `<td><strong>${cell}</strong></td>` : `<td>$${cell}</td>`).join('')}</tr>`;
    });

    html += `</tbody></table></div>`;
    container.innerHTML = html;
  } else {
    dpSection.style.display = "none";
  }
}

// ==========================================
// COMPARISON CANVAS ENGINE
// ==========================================
function renderComparisonCharts(algorithms) {
  const canvas = document.getElementById("comparison-bar-chart");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const width = canvas.width = canvas.parentElement.clientWidth || 900;
  const height = canvas.height = 360;

  ctx.clearRect(0, 0, width, height);

  const padding = { top: 40, right: 30, bottom: 80, left: 60 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const validAlgos = algorithms.filter(a => a.metrics.makespan > 0);
  if (validAlgos.length === 0) return;

  // Render Average Waiting Time vs Average Turnaround Time
  const maxVal = Math.max(...validAlgos.map(a => Math.max(a.metrics.avg_waiting_time, a.metrics.avg_turnaround_time)), 5);
  const barGroupWidth = chartW / validAlgos.length;
  const barWidth = Math.min(22, (barGroupWidth - 20) / 2);

  // Background Grid Lines
  ctx.strokeStyle = "rgba(255, 255, 255, 0.06)";
  ctx.lineWidth = 1;
  const gridSteps = 5;
  for (let i = 0; i <= gridSteps; i++) {
    const y = padding.top + (chartH / gridSteps) * i;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();

    const labelVal = Math.round(maxVal - (maxVal / gridSteps) * i);
    ctx.fillStyle = "#64748B";
    ctx.font = "11px var(--font-sans)";
    ctx.textAlign = "right";
    ctx.fillText(labelVal, padding.left - 10, y + 4);
  }

  // Render Bars
  validAlgos.forEach((algo, index) => {
    const groupX = padding.left + index * barGroupWidth + (barGroupWidth / 2);

    // Waiting Time Bar (Indigo)
    const wtH = (algo.metrics.avg_waiting_time / maxVal) * chartH;
    const wtX = groupX - barWidth - 3;
    const wtY = padding.top + chartH - wtH;

    const gradWT = ctx.createLinearGradient(0, wtY, 0, padding.top + chartH);
    gradWT.addColorStop(0, "#6366F1");
    gradWT.addColorStop(1, "#4338CA");
    ctx.fillStyle = gradWT;
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(wtX, wtY, barWidth, wtH, [4, 4, 0, 0]) : ctx.fillRect(wtX, wtY, barWidth, wtH);
    ctx.fill();

    // Turnaround Time Bar (Cyan)
    const tatH = (algo.metrics.avg_turnaround_time / maxVal) * chartH;
    const tatX = groupX + 3;
    const tatY = padding.top + chartH - tatH;

    const gradTAT = ctx.createLinearGradient(0, tatY, 0, padding.top + chartH);
    gradTAT.addColorStop(0, "#38BDF8");
    gradTAT.addColorStop(1, "#0284C7");
    ctx.fillStyle = gradTAT;
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(tatX, tatY, barWidth, tatH, [4, 4, 0, 0]) : ctx.fillRect(tatX, tatY, barWidth, tatH);
    ctx.fill();

    // Algorithm Label rotated
    ctx.save();
    ctx.translate(groupX, height - padding.bottom + 15);
    ctx.rotate(-Math.PI / 4);
    ctx.fillStyle = "#CBD5E1";
    ctx.font = "11px var(--font-sans)";
    ctx.textAlign = "right";
    ctx.fillText(algo.name.split("(")[0].trim(), 0, 0);
    ctx.restore();
  });

  // Chart Legend
  ctx.fillStyle = "#6366F1";
  ctx.fillRect(width - 250, 15, 12, 12);
  ctx.fillStyle = "#E2E8F0";
  ctx.font = "12px var(--font-sans)";
  ctx.textAlign = "left";
  ctx.fillText("Avg Waiting Time (AWT)", width - 232, 25);

  ctx.fillStyle = "#38BDF8";
  ctx.fillRect(width - 90, 15, 12, 12);
  ctx.fillStyle = "#E2E8F0";
  ctx.fillText("Avg Turnaround (ATAT)", width - 72, 25);
}

function applyColorDots() {
  document.querySelectorAll(".color-dot[data-color]").forEach((dot) => {
    const c = dot.getAttribute("data-color");
    if (c) {
      dot.style.backgroundColor = c;
      dot.style.color = c;
    }
  });
}

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  initTooltip();
  applyColorDots();

  // If on schedule page, trigger initial run
  const algoSelect = document.getElementById("algo-select");
  if (algoSelect) {
    runSelectedAlgorithm();
  }

  // Timeline Scrubber Listener
  const scrubber = document.getElementById("timeline-scrubber");
  if (scrubber) {
    scrubber.addEventListener("input", (e) => {
      AppState.currentTime = parseInt(e.target.value);
      updatePlaybackUI();
    });
  }

  // Algorithm select change trigger knapsack input toggle
  if (algoSelect) {
    algoSelect.addEventListener("change", (e) => {
      const capGroup = document.getElementById("capacity-form-group");
      if (capGroup) {
        capGroup.style.display = e.target.value === "dp_knapsack" ? "block" : "none";
      }
    });
  }
});
