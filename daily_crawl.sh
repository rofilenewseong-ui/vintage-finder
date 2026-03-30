#!/bin/bash
# Daily crawl + build + push to GitHub Pages
# Runs every day at 7:00 AM

cd /Users/ferion/Desktop/ebay-vintage-finder

echo "$(date): Starting daily crawl..."

# Run crawler
/usr/bin/python3 crawl.py >> /tmp/vintage-finder-crawl.log 2>&1

# Build static site
/usr/bin/python3 build_site.py >> /tmp/vintage-finder-crawl.log 2>&1

# Push to GitHub
git add data/ docs/
git commit -m "Daily update: $(date '+%Y-%m-%d %H:%M')"
git push origin main

echo "$(date): Done!"
