# Beatfield

바이노럴 비트 웹앱(PWA). iPhone Safari에서 열고 공유 › 홈 화면에 추가 하면 앱처럼 설치돼요.

- `app.html` — 앱 본문(HTML/CSS/JS 한 파일). 모든 소리는 Web Audio로 실시간 합성해요.
- `build.py` — `dist/`에 index.html, manifest, service worker, 아이콘을 만들어요. (`python3 build.py`, Pillow 필요)
- `dist/` — 배포용 정적 파일. Vercel 등에 Root Directory를 `beatfield/dist`로 두고 배포해요.
