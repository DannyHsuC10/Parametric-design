"use strict";

(async function showCrawlStatus() {
  const status = document.querySelector("#last-successful-crawl");
  try {
    const response = await fetch("data/crawl_metadata.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const { last_successful_crawl: timestamp } = await response.json();
    if (timestamp === null) return;
    const date = new Date(timestamp);
    if (typeof timestamp !== "string" || !Number.isFinite(date.getTime())) {
      throw new Error("Invalid crawl timestamp");
    }

    const time = document.createElement("time");
    time.dateTime = date.toISOString();
    time.textContent = new Intl.DateTimeFormat("en-GB", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "Asia/Taipei",
      timeZoneName: "short",
    }).format(date);
    status.replaceChildren(time);
  } catch {
    status.textContent = "Unavailable";
  }
})();
