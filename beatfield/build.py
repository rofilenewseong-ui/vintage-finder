import json, pathlib, math
from PIL import Image, ImageDraw, ImageFilter
root = pathlib.Path(__file__).parent; dist = root / "dist"; dist.mkdir(exist_ok=True)
body = (root / "app.html").read_text()
head = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0D121B">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Beatfield">
<link rel="manifest" href="manifest.json">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-192.png">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:0}body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>
</head>
<body>
"""
(dist / "index.html").write_text(head + body + "\n</body>\n</html>\n")
(dist / "manifest.json").write_text(json.dumps({
  "name": "Beatfield", "short_name": "Beatfield", "lang": "ko", "start_url": "./", "scope": "./",
  "display": "standalone", "background_color": "#0D121B", "theme_color": "#0D121B",
  "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]
}, ensure_ascii=False, indent=2))
(dist / "sw.js").write_text("""const C = "beatfield-v1";
const FILES = ["./", "index.html", "manifest.json", "icon-180.png", "icon-192.png", "icon-512.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(C).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  e.respondWith(fetch(e.request).then(r => { const copy = r.clone(); caches.open(C).then(c => c.put(e.request, copy)).catch(() => {}); return r; }).catch(() => caches.match(e.request)));
});
""")
(dist / "vercel.json").write_text(json.dumps({"headers": [{"source": "/sw.js", "headers": [{"key": "Cache-Control", "value": "no-cache"}]}]}, indent=2))
# icon: night field with amber rings and two drifting waves
def icon(n):
    S = n * 4; im = Image.new("RGB", (S, S), (13, 18, 27)); d = ImageDraw.Draw(im)
    cx, cy = S / 2, S * 0.44
    for i, (r, a) in enumerate([(0.36, 70), (0.29, 110), (0.22, 255)]):
        rr = S * r; col = tuple(int(13 + (c - 13) * a / 255) for c in (232, 180, 106))
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=col, width=max(2, int(S * (0.012 if i < 2 else 0.02))))
    d = ImageDraw.Draw(im)
    for col, ph in [((121, 184, 204), 0), ((232, 180, 106), 1.4)]:
        pts = [(x, S * 0.78 + math.sin(x / S * 4 * 2 * math.pi + ph) * S * 0.035) for x in range(int(S * 0.16), int(S * 0.84), 4)]
        d.line(pts, fill=col, width=int(S * 0.016), joint="curve")
    return im.resize((n, n), Image.LANCZOS)
for n in (180, 192, 512): icon(n).save(dist / f"icon-{n}.png")
print("built", sorted(p.name for p in dist.iterdir()))
