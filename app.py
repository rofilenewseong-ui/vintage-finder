from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_data(platform):
    path = os.path.join(DATA_DIR, f"{platform}.json")
    if not os.path.exists(path):
        return {"crawled_at": None, "total": 0, "queries": [], "items": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/items")
def get_items():
    platform = request.args.get("platform", "all")  # ebay, depop, all
    query = request.args.get("query", "")
    sort = request.args.get("sort", "newest")
    min_price = request.args.get("min_price", "")
    max_price = request.args.get("max_price", "")
    search = request.args.get("search", "").lower()
    page = int(request.args.get("page", "1"))
    per_page = 48

    items = []
    crawled_at = {}

    if platform in ("ebay", "all"):
        data = load_data("ebay")
        crawled_at["ebay"] = data.get("crawled_at")
        for item in data.get("items", []):
            item["_platform"] = "ebay"
            items.append(item)

    if platform in ("depop", "all"):
        data = load_data("depop")
        crawled_at["depop"] = data.get("crawled_at")
        for item in data.get("items", []):
            item["_platform"] = "depop"
            items.append(item)

    # Filter by query tag
    if query:
        items = [i for i in items if i.get("query") == query]

    # Filter by search text
    if search:
        items = [i for i in items if search in i.get("title", "").lower()]

    # Filter by price
    def extract_price(price_str):
        import re
        nums = re.findall(r"[\d,]+\.?\d*", price_str.replace(",", ""))
        if nums:
            try:
                return float(nums[0])
            except ValueError:
                pass
        return None

    if min_price:
        try:
            min_val = float(min_price)
            items = [i for i in items if (extract_price(i.get("price", "")) or 0) >= min_val]
        except ValueError:
            pass

    if max_price:
        try:
            max_val = float(max_price)
            items = [i for i in items if (p := extract_price(i.get("price", ""))) is not None and p <= max_val]
        except ValueError:
            pass

    # Sort
    if sort == "price_low":
        items.sort(key=lambda i: extract_price(i.get("price", "")) or 999999)
    elif sort == "price_high":
        items.sort(key=lambda i: extract_price(i.get("price", "")) or 0, reverse=True)

    # Pagination
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    paged_items = items[start:start + per_page]

    # Get available queries
    all_queries = set()
    for p in ("ebay", "depop"):
        d = load_data(p)
        all_queries.update(d.get("queries", []))

    return jsonify({
        "items": paged_items,
        "total": total,
        "page": page,
        "total_pages": total_pages,
        "crawled_at": crawled_at,
        "queries": sorted(all_queries),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5050)
