# Beatfield iPhone 앱 (Xcode 프로젝트)

`../dist`의 웹앱을 Capacitor로 감싼 네이티브 iOS 앱이에요. 웹 버전과 달리 아래 두 가지가 들어 있어요.

- 무음 스위치를 켜도 소리가 나요 (`AppDelegate.swift`에서 AVAudioSession을 `.playback`으로 설정)
- 화면을 잠가도 계속 재생돼요 (`Info.plist`의 `UIBackgroundModes` → `audio`)

## Mac에서 iPhone에 설치하기

준비물: Xcode(App Store에서 무료), Node.js 22 이상, Apple ID, USB 케이블

```bash
git clone -b claude/beatfield-app https://github.com/rofilenewseong-ui/vintage-finder.git
cd vintage-finder/beatfield/ios-app
npm install
npm run ios        # 웹 파일을 복사하고 Xcode를 열어요
```

Xcode가 열리면:

1. 왼쪽에서 **App** 프로젝트 → **Signing & Capabilities** 탭 → **Team**에서 내 Apple ID를 고르세요. (없으면 *Add an Account…*)
2. Bundle Identifier가 이미 쓰인다는 오류가 나오면 `com.rofilenewseong.beatfield` 끝에 아무 글자나 붙여서 바꾸세요.
3. iPhone을 USB로 연결하고, 위쪽 기기 선택 메뉴에서 내 iPhone을 고른 뒤 ▶︎ 버튼을 누르세요.
4. iPhone에서 처음 한 번은 **설정 › 일반 › VPN 및 기기 관리**에서 내 개발자 앱을 *신뢰*해야 열려요.
   iOS 16 이상이면 **설정 › 개인정보 보호 및 보안 › 개발자 모드**도 켜야 해요.

무료 Apple ID로 설치한 앱은 7일 뒤에 만료돼요. 다시 ▶︎를 누르면 7일이 연장돼요. 유료 개발자 계정(연 $99)이면 1년 동안 쓸 수 있고 App Store에도 올릴 수 있어요.

## 앱 내용을 고친 뒤

```bash
cd ..          # beatfield/
python3 build.py
cd ios-app && npm run sync
```
