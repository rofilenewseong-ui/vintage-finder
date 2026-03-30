#!/bin/bash
# Daily crawl on Mac → push data to GitHub → GitHub rebuilds site automatically
# Set up as LaunchAgent to run daily

cd /Users/ferion/Desktop/ebay-vintage-finder
LOG="/tmp/vintage-finder.log"

echo "$(date): Starting daily crawl..." >> "$LOG"

# Run crawler (on Mac where Playwright works properly)
/usr/bin/python3 crawl.py >> "$LOG" 2>&1

# Push data to GitHub (this triggers GitHub Actions to rebuild the site)
git add data/
git diff --staged --quiet || git commit -m "Daily data: $(date '+%Y-%m-%d %H:%M')"
git push origin main >> "$LOG" 2>&1

echo "$(date): Done!" >> "$LOG"
