"""
Daily crawler for eBay & Depop vintage clothing.
Run once a day: python3 crawl.py
Results saved to data/ebay.json and data/depop.json
"""

import json
import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Configurable search queries - add/remove as needed
SEARCH_QUERIES = [
    "vintage jacket",
    "vintage levis",
    "vintage nike",
    "vintage carhartt",
    "vintage ralph lauren",
    "vintage 90s clothing",
    "vintage band tee",
    "vintage denim",
]

MAX_ITEMS_PER_QUERY = 60


def crawl_ebay(page, query):
    """Crawl eBay search results for a query."""
    items = []
    url = f"https://www.ebay.com/sch/i.html?_nkw={query.replace(' ', '+')}&_sop=10&_ipg=60"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait for listings to appear
        page.wait_for_selector("li.s-card, li.s-item", timeout=15000)
        time.sleep(2)  # Let images load

        # Try new UI (s-card)
        cards = page.query_selector_all("li.s-card")
        if cards:
            for card in cards[:MAX_ITEMS_PER_QUERY]:
                try:
                    item = parse_ebay_card(card)
                    if item:
                        items.append(item)
                except Exception:
                    continue
        else:
            # Fallback to old UI (s-item)
            listings = page.query_selector_all("li.s-item")
            for listing in listings[:MAX_ITEMS_PER_QUERY]:
                try:
                    item = parse_ebay_item(listing)
                    if item:
                        items.append(item)
                except Exception:
                    continue

        print(f"  eBay [{query}]: {len(items)} items")
    except Exception as e:
        print(f"  eBay [{query}] ERROR: {e}")

    return items


def parse_ebay_card(card):
    """Parse new eBay s-card element."""
    title_el = card.query_selector(".s-card__title span")
    if not title_el:
        return None
    title = title_el.inner_text().strip()
    if not title or title == "Shop on eBay":
        return None

    link_el = card.query_selector("a.s-card__link")
    link = link_el.get_attribute("href") if link_el else ""
    if "?" in link:
        link = link.split("?")[0]

    img_el = card.query_selector("img")
    image = ""
    if img_el:
        image = img_el.get_attribute("src") or img_el.get_attribute("data-src") or ""

    price_el = card.query_selector(".s-card__price")
    price = price_el.inner_text().strip() if price_el else "N/A"

    subtitle_el = card.query_selector(".s-card__subtitle")
    condition = subtitle_el.inner_text().strip() if subtitle_el else ""

    attr_rows = card.query_selector_all(".s-card__attribute-row")
    shipping = ""
    extra_info = []
    for row in attr_rows:
        text = row.inner_text().strip()
        if not text or text == price:
            continue
        if any(k in text.lower() for k in ["배송", "shipping", "free"]):
            shipping = text
        else:
            extra_info.append(text)

    seller_el = card.query_selector(".s-card__footer")
    seller = seller_el.inner_text().strip() if seller_el else ""

    return {
        "title": title,
        "price": price,
        "link": link,
        "image": image,
        "seller": seller,
        "shipping": shipping,
        "condition": condition,
        "extra": " | ".join(extra_info),
        "platform": "ebay",
    }


def parse_ebay_item(listing):
    """Parse old eBay s-item element."""
    title_el = listing.query_selector(".s-item__title")
    if not title_el:
        return None
    title = title_el.inner_text().strip()
    if title == "Shop on eBay":
        return None

    link_el = listing.query_selector("a.s-item__link")
    link = link_el.get_attribute("href") if link_el else ""

    img_el = listing.query_selector("img")
    image = ""
    if img_el:
        image = img_el.get_attribute("src") or ""

    price_el = listing.query_selector(".s-item__price")
    price = price_el.inner_text().strip() if price_el else "N/A"

    seller_el = listing.query_selector(".s-item__seller-info-text")
    seller = seller_el.inner_text().strip() if seller_el else ""

    shipping_el = listing.query_selector(".s-item__shipping")
    shipping = shipping_el.inner_text().strip() if shipping_el else ""

    condition_el = listing.query_selector(".SECONDARY_INFO")
    condition = condition_el.inner_text().strip() if condition_el else ""

    return {
        "title": title,
        "price": price,
        "link": link,
        "image": image,
        "seller": seller,
        "shipping": shipping,
        "condition": condition,
        "extra": "",
        "platform": "ebay",
    }


def slug_to_title(href):
    """Extract readable title from Depop product URL slug."""
    # /products/username-some-product-description-abc123/
    import re
    parts = href.rstrip("/").split("/")
    slug = parts[-1] if parts else ""
    # Remove trailing hash (e.g., -abc123)
    slug = re.sub(r"-[a-f0-9]{4}$", "", slug)
    # Remove username prefix (first segment before -)
    segments = slug.split("-")
    if len(segments) > 1:
        # Username is typically the first segment
        slug = "-".join(segments[1:])
    return slug.replace("-", " ").title()


def crawl_depop(page, query):
    """Crawl Depop search results for a query."""
    items = []
    url = f"https://www.depop.com/search/?q={query.replace(' ', '+')}&sort=newlyListed"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)  # Wait for JS rendering

        # Use productCardRoot which contains all info
        cards = page.query_selector_all('[class*="productCardRoot"]')
        if not cards:
            # Fallback: try scrolling
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            time.sleep(2)
            cards = page.query_selector_all('[class*="productCardRoot"]')

        seen_links = set()
        for card in cards[:MAX_ITEMS_PER_QUERY]:
            try:
                # Link
                link_el = card.query_selector('a[href*="/products/"]')
                if not link_el:
                    continue
                href = link_el.get_attribute("href") or ""
                full_link = href if href.startswith("http") else f"https://www.depop.com{href}"
                if full_link in seen_links:
                    continue
                seen_links.add(full_link)

                # Title from slug
                title = slug_to_title(href)

                # Image
                img_el = card.query_selector("img._mainImage_e5j9l_11, img[class*='mainImage']")
                if not img_el:
                    img_el = card.query_selector("img")
                image = ""
                if img_el:
                    image = img_el.get_attribute("src") or ""

                # Price - look for bold price text
                price = "N/A"
                price_el = card.query_selector('[class*="price"], [class*="Price"], p[class*="bold"]')
                if price_el:
                    price = price_el.inner_text().strip()

                # Brand and size from attributes
                attr_texts = card.evaluate("""el => {
                    let texts = [];
                    el.querySelectorAll('p').forEach(p => {
                        let t = p.textContent.trim();
                        if (t && t.length < 50 && !t.startsWith('$')) texts.push(t);
                    });
                    return texts;
                }""")
                brand = attr_texts[0] if attr_texts else ""
                size = attr_texts[1] if len(attr_texts) > 1 else ""
                condition = f"{brand} {size}".strip() if (brand or size) else ""

                # Seller from URL slug (first part)
                slug_parts = href.rstrip("/").split("/")[-1].split("-")
                seller = slug_parts[0] if slug_parts else ""

                items.append({
                    "title": title,
                    "price": price,
                    "link": full_link,
                    "image": image,
                    "seller": f"@{seller}" if seller else "",
                    "shipping": "",
                    "condition": condition,
                    "extra": "",
                    "platform": "depop",
                })
            except Exception:
                continue

        print(f"  Depop [{query}]: {len(items)} items")
    except Exception as e:
        print(f"  Depop [{query}] ERROR: {e}")

    return items


def main():
    print(f"=== Vintage Finder Daily Crawl ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Queries: {len(SEARCH_QUERIES)}")
    print()

    all_ebay = []
    all_depop = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )

        page = context.new_page()

        # Crawl eBay
        print("--- eBay ---")
        for query in SEARCH_QUERIES:
            items = crawl_ebay(page, query)
            for item in items:
                item["query"] = query
            all_ebay.extend(items)
            time.sleep(2)  # Be polite

        # Crawl Depop
        print("\n--- Depop ---")
        for query in SEARCH_QUERIES:
            items = crawl_depop(page, query)
            for item in items:
                item["query"] = query
            all_depop.extend(items)
            time.sleep(2)

        browser.close()

    # Deduplicate by link
    def dedup(items):
        seen = set()
        result = []
        for item in items:
            if item["link"] not in seen:
                seen.add(item["link"])
                result.append(item)
        return result

    all_ebay = dedup(all_ebay)
    all_depop = dedup(all_depop)

    # Save results
    timestamp = datetime.now().isoformat()

    ebay_data = {
        "crawled_at": timestamp,
        "total": len(all_ebay),
        "queries": SEARCH_QUERIES,
        "items": all_ebay,
    }
    with open(os.path.join(DATA_DIR, "ebay.json"), "w", encoding="utf-8") as f:
        json.dump(ebay_data, f, ensure_ascii=False, indent=2)

    depop_data = {
        "crawled_at": timestamp,
        "total": len(all_depop),
        "queries": SEARCH_QUERIES,
        "items": all_depop,
    }
    with open(os.path.join(DATA_DIR, "depop.json"), "w", encoding="utf-8") as f:
        json.dump(depop_data, f, ensure_ascii=False, indent=2)

    print(f"\n=== Done ===")
    print(f"eBay: {len(all_ebay)} items saved")
    print(f"Depop: {len(all_depop)} items saved")
    print(f"Data: {DATA_DIR}/")


if __name__ == "__main__":
    main()
