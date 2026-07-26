const LOG_INDEX = "factory/log/index.json";
const MAX_ENTRIES = 30;
const DISPLAY_AGENT = { system: "foreman" };
const AGENT_CLASS = new Set(["foreman", "architect", "implementer", "tester", "auditor"]);

const feed = document.querySelector("#activity-feed");
const sourceStatus = document.querySelector("#log-source-status");
const counters = {
  milestones: document.querySelector("#verified-milestones"),
  audits: document.querySelector("#passed-audits"),
  blockers: document.querySelector("#blocker-events"),
  roles: document.querySelector("#active-roles"),
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function parseJsonLines(text) {
  return text.split(/\r?\n/).flatMap((line) => {
    if (!line.trim()) return [];
    try {
      const entry = JSON.parse(line);
      return entry.timestamp && entry.action && entry.summary ? [entry] : [];
    } catch {
      return [];
    }
  });
}

function normalizedAgent(agent) {
  const value = DISPLAY_AGENT[agent] || agent || "hook";
  return AGENT_CLASS.has(value) ? value : "hook";
}

function eventLabel(entry) {
  const action = entry.action.replaceAll("_", " ").toUpperCase();
  const passed = entry.action === "audited" && /\bpass(?:ed)?\b/i.test(entry.summary);
  const label = passed ? "✓ PASSED" : action;
  return entry.milestone ? `${label} · ${entry.milestone}` : label;
}

function timeLabel(timestamp) {
  const date = new Date(timestamp);
  return Number.isNaN(date.valueOf())
    ? "—"
    : new Intl.DateTimeFormat(undefined, {
        hour: "2-digit",
        minute: "2-digit",
        month: "short",
        day: "numeric",
      }).format(date);
}

function renderEntry(entry) {
  const agent = normalizedAgent(entry.agent);
  const assignment = entry.assignment_id
    ? `<code>${escapeHtml(entry.assignment_id)}</code>`
    : "";
  const passed = entry.action === "audited" && /\bpass(?:ed)?\b/i.test(entry.summary);
  const done = entry.action === "milestone_updated" && /\bdone\b/i.test(entry.summary);
  const labelClass = passed ? "pass-label" : done ? "done-label" : "";

  return `
    <article class="log-entry ${agent}-entry">
      <time datetime="${escapeHtml(entry.timestamp)}">${escapeHtml(timeLabel(entry.timestamp))}</time>
      <div class="timeline-dot" aria-hidden="true"></div>
      <div class="log-content">
        <div class="log-meta">
          <span class="agent-label ${agent}-label">${escapeHtml(agent.toUpperCase())}</span>
          <span class="event-label ${labelClass}">${escapeHtml(eventLabel(entry))}</span>
        </div>
        <p>${escapeHtml(entry.summary)}</p>
        ${assignment}
      </div>
    </article>`;
}

function updateCounters(entries) {
  const finishedMilestones = new Set(
    entries
      .filter((entry) => entry.action === "milestone_updated" && /\bdone\b/i.test(entry.summary))
      .map((entry) => entry.milestone)
      .filter(Boolean),
  );
  counters.milestones.textContent = String(finishedMilestones.size);
  counters.audits.textContent = String(
    entries.filter((entry) => entry.action === "audited" && /\bpass(?:ed)?\b/i.test(entry.summary)).length,
  );
  counters.blockers.textContent = String(entries.filter((entry) => entry.action === "blocked").length);
  counters.roles.textContent = String(
    new Set(entries.map((entry) => normalizedAgent(entry.agent)).filter((agent) => agent !== "hook")).size,
  );
}

async function loadActivity() {
  try {
    const indexResponse = await fetch(LOG_INDEX, { cache: "no-store" });
    if (!indexResponse.ok) throw new Error(`Could not load ${LOG_INDEX}`);
    const index = await indexResponse.json();
    const logs = Array.isArray(index.logs)
      ? index.logs.filter((name) => /^\d{4}-\d{2}-\d{2}\.jsonl$/.test(name))
      : [];

    const entries = (await Promise.all(
      logs.map(async (name) => {
        const response = await fetch(`factory/log/${name}`, { cache: "no-store" });
        return response.ok ? parseJsonLines(await response.text()) : [];
      }),
    ))
      .flat()
      .sort((left, right) => new Date(right.timestamp) - new Date(left.timestamp));

    updateCounters(entries);
    sourceStatus.textContent = `${entries.length} events from ${logs.length} log file${logs.length === 1 ? "" : "s"}`;
    feed.innerHTML = entries.length
      ? entries.slice(0, MAX_ENTRIES).map(renderEntry).join("")
      : '<p class="feed-status">No activity has been logged yet.</p>';
  } catch (error) {
    sourceStatus.textContent = "Log feed unavailable";
    feed.innerHTML = `<p class="feed-status error">Unable to load the log index. Serve this folder over HTTP (for example, <code>python -m http.server</code>) and refresh.</p>`;
  }
}

loadActivity();
