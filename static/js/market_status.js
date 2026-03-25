document.addEventListener("DOMContentLoaded", () => {
  setInterval(() => {
    updateMarketStatus();
  }, 30000); // 30 Seconds
});

function updateMarketStatus() {
  const container = document.getElementById("market-status-container");
  const timeText = document.getElementById("market-status-time");

  if (!container || !timeText) return;

  const timestamp = container.dataset.timestamp;

  const newTime = formatTimeAgo(timestamp);

  // Only update if the text has changed
  if (timeText.textContent !== newTime) {
    // Start fade-out
    timeText.classList.add("fading");

    // Wait for fade-out to finish, then change text
    setTimeout(() => {
      timeText.textContent = newTime;

      // Fade back in
      timeText.classList.remove("fading");
    }, 300); // This duration matches the CSS transition time
  }
}

function formatTimeAgo(timestamp) {
  if (!timestamp) return "";

  const updated = new Date(timestamp);
  const now = new Date();

  const diffMs = now - updated;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);

  if (diffSec < 10) return "Updated just now";
  if (diffSec < 60) return `Updated ${diffSec}s ago`;
  if (diffMin === 1) return "Updated 1 min ago";
  if (diffMin < 60) return `Updated ${diffMin} min ago`;

  const diffHr = Math.floor(diffMin / 60);
  if (diffHr === 1) return "Updated 1 hr ago";
  if (diffHr < 24) return `Updated ${diffHr} hr ago`;

  const diffDay = Math.floor(diffHr / 24);
  return `Updated ${diffDay} day${diffDay > 1 ? "s" : ""} ago`;
}
