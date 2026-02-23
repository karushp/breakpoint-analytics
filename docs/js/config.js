/**
 * API base URL for Breakpoint Analytics backend.
 * When opened from localhost we use the local API so "Last 5" and stats work after running the pipeline.
 * Override window.BREAKPOINT_API_BASE before this script loads to force a different URL.
 */
(function () {
  var isLocal = /^(localhost|127\.0\.0\.1)(:\d+)?$/i.test(window.location.host + (window.location.port ? ":" + window.location.port : ""));
  window.BREAKPOINT_API_BASE = window.BREAKPOINT_API_BASE || (isLocal ? "http://127.0.0.1:8000" : "https://breakpoint-analytics.onrender.com");
})();
