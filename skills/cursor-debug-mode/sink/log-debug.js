#!/usr/bin/env node
/**
 * Agent debug log sink for Cursor-style debugging.
 *
 * Writes compact NDJSON lines to a project-local debug log. The log path is
 * deterministic relative to the current working directory so agents and humans
 * can find it easily after reproduction.
 *
 * Usage:
 *   const logDebug = require("./skills/cursor-debug-mode/sink/log-debug.js");
 *   logDebug({ location: "src/store.js:42", message: "cart total", data: { total }, hypothesisId: "A" });
 *
 * Output lines are appended to `.agent-debug.ndjson` in the working directory.
 */
const fs = require("fs");
const path = require("path");

const LOG_FILE = process.env.AGENT_DEBUG_LOG || ".agent-debug.ndjson";

function makeId() {
  return `log_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function logDebug(entry) {
  const record = {
    id: entry.id || makeId(),
    timestamp: Date.now(),
    location: entry.location || "unknown",
    message: entry.message || "",
    data:
      entry.data && typeof entry.data === "object" ? entry.data : { value: entry.data },
    hypothesisId: entry.hypothesisId || "?",
  };

  // Avoid accidentally logging secrets if an allow-list is provided.
  const denyKeys = (process.env.AGENT_DEBUG_DENY_KEYS || "")
    .split(",")
    .map((k) => k.trim().toLowerCase())
    .filter(Boolean);
  if (denyKeys.length > 0) {
    const scrubbed = {};
    for (const [key, value] of Object.entries(record.data)) {
      scrubbed[key] = denyKeys.some((d) => key.toLowerCase().includes(d)) ? "[REDACTED]" : value;
    }
    record.data = scrubbed;
  }

  const line = JSON.stringify(record) + "\n";
  const logPath = path.resolve(LOG_FILE);
  fs.appendFileSync(logPath, line, "utf-8");
  return record;
}

module.exports = logDebug;

if (require.main === module) {
  // CLI mode for quick manual tests.
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.error("Usage: node log-debug.js '<json>' or --clear");
    process.exit(1);
  }
  if (args[0] === "--clear") {
    try {
      fs.unlinkSync(path.resolve(LOG_FILE));
      console.log(`Cleared ${LOG_FILE}`);
    } catch (err) {
      if (err.code !== "ENOENT") throw err;
      console.log(`${LOG_FILE} did not exist`);
    }
    process.exit(0);
  }
  const raw = args[0];
  try {
    logDebug(JSON.parse(raw));
    console.log("Logged to", LOG_FILE);
  } catch (err) {
    console.error("Invalid JSON entry:", err.message);
    process.exit(1);
  }
}
