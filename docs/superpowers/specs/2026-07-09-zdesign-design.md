# zdesign — 설계 문서 (Design Spec)

**날짜:** 2026-07-09
**상태:** 승인 대기 (사용자 리뷰 전)
**한 줄 요약:** djust 앱에 설치하는 pip 패키지. 디자이너가 브라우저에 뜬 실제 화면 위에서 요소를 짚어 비주얼 직접 편집 또는 Claude 자연어 지시로 소스를 고치고, djust 핫리로드로 즉시 반영한다.

---

## 1. 목적 & 배경

### 문제
`djust`(Django용 Phoenix LiveView 스타일 리액티브 SSR 프레임워크) 앱을 개발 중이며, 디자이너(비개발자)가 실행 중인 웹을 보면서 **화면의 특정 부분을 지정하고 그 코드만 수정하거나 Claude와 협업**할 수 있는 도구가 필요하다.

### 왜 새로 만드나 (Tidewave 참고하되 직접 구현)
djust는 이미 이 도구의 **백엔드 절반**을 갖고 있다:
- **MCP 서버** (`djust mcp install --client claude`) — 디렉티브/데코레이터/라이프사이클/라이브 뷰/라우트 구조적 조회
- **LiveView 인트로스펙션 헬퍼** — `get_handler_schema()`, `get_state_snapshot()`, `describe_ui()` (LLM tool-calling 스키마 호환)
- **핫 리로드** — `enable_hot_reload()`, 소스 변경 시 뷰 자동 교체
- **VDOM/패치 파이프라인** — 템플릿의 `dj-view`/`dj-root`, 컴포넌트 `template_name`, Rust `djust_vdom` diff → WebSocket 패치

**비어있는 절반**: djust MCP는 "프로젝트 구조"는 알지만 "지금 화면에서 디자이너가 가리킨 이 버튼"은 모른다. 그 **비주얼 브릿지**가 zdesign의 고유 가치다.

### 성공 기준
- 디자이너가 터미널/코드 없이 브라우저만으로 요소를 선택하고 스타일을 바꿀 수 있다.
- 선택한 요소가 정확한 소스 파일/라인으로 되짚어진다.
- 복잡한 변경은 인앱 채팅으로 Claude에게 맡기고 diff를 확인 후 적용한다.
- 모든 편집은 되돌릴 수 있다(git 스냅샷).
- 프로덕션에는 어떤 흔적도 남지 않는다(dev 전용).

---

## 2. 형태 & 배포

- **pip 패키지**, import 이름 `zdesign`.
- djust 앱의 `settings.py`에서 `INSTALLED_APPS` + 미들웨어로 활성화.
- **`DEBUG=True`(로컬 dev)에서만 로드.** 프로덕션 가드 필수.
- 전제: 디자이너가 로컬에서 `manage.py runserver`로 앱을 띄운 상태(소스 파일 직접 수정 가능).

---

## 3. 아키텍처 — 5개 유닛

각 유닛은 하나의 명확한 책임을 가지며 잘 정의된 인터페이스로 통신하고 독립적으로 테스트 가능하다.

| 유닛 | 책임 | 의존 |
|---|---|---|
| **Instrumenter** | dev에서 템플릿 로드 시 여는 태그에 `data-zd-id` 주입 + 소스맵(`id → 파일:라인:컬럼:태그`) 생성 | Django 템플릿 로더 |
| **Overlay (client)** | 호버 하이라이트, 클릭 선택, 소스 배지, 비주얼 편집 패널, Claude 채팅 패널. Alpine.js + 격리 CSS(Shadow DOM 또는 네임스페이스) | Bridge (WS/HTTP) |
| **Bridge (server)** | 오버레이 ↔ 서버 프로토콜. 선택 요소 해석(A 소스맵 → B 지문 폴백), 컨텍스트 번들 생성 | Instrumenter |
| **Editor** | write-back 엔진. 클래스/속성/텍스트를 소스 파일의 정확한 위치에 안전 수정. git 스냅샷. 경로 제한 | Bridge |
| **Agent** | Anthropic API 에이전트 루프. djust 인트로스펙션 + 선택 컨텍스트를 도구로 Editor 호출. diff 미리보기 산출 | Editor, Anthropic SDK |

**재사용 원칙:** zdesign은 djust의 MCP·인트로스펙션·핫리로드·`dj-root` 경계를 재구현하지 않고 그 위에 얹는다.

---

## 4. 매핑 메커니즘 (C: 하이브리드) — 심장부

djust는 Django 템플릿을 서버 렌더 → Rust VDOM diff 하므로, 렌더 후 결과 DOM에는 원본 템플릿 라인번호가 없다. 이를 두 경로로 해결한다.

### A 경로 (주 사용) — 소스맵 주입
- Instrumenter가 **dev 렌더 파이프라인**에서 각 여는 태그에 `data-zd-id="t7"` 주입.
- 동시에 `sourcemap[t7] = {file, line, col, tag}` 기록.
- `data-zd-id`는 템플릿 원문에 심긴 리터럴 속성이므로 렌더/패치를 거쳐도 DOM에 살아남는다.
- 오버레이 클릭 → `data-zd-id` 읽기 → 소스맵 조회 → **정확한 파일:라인**.
- 선행 기술 참고: React dev-inspector, Vite plugin-inspector, Locator.js (모두 빌드/로드 시 `data-*` 주입 + 소스맵).

### B 경로 (폴백) — 컴포넌트 경계 + 지문
- `data-zd-id`가 없는 요소(서드파티 위젯, 동적 include 조각 등)는:
  - 가장 가까운 `dj-root`/컴포넌트 래퍼로 **파일까지** 좁힌다.
  - 태그명 + 주요 속성 + 텍스트로 **지문(fingerprint)** 생성.
  - Editor/Agent가 해당 파일 내에서 유일 매칭으로 라인 확정(모호하면 Claude에게 위임).

### 프로덕션
- Instrumenter 완전 비활성 → `data-zd-id` 미출력, 소스맵 미생성.

### 리스크 & 완화
- **리스크:** djust 렌더 파이프라인(Rust VDOM)이 임의 속성 주입/라인 추적을 어디서 허용하는지 확인 필요.
  - **완화(P1):** Django 템플릿 로더 래퍼에서 로드 시점에 원문 HTML을 파싱(라인 유지)하여 `data-zd-id` 주입 + 소스맵 생성. VDOM 이전 단계라 라인번호 확보 가능. Rust 계층 수정 불필요.
  - Instrumenter가 로더 계측으로 불가능한 경우 B 경로 비중을 높이는 것으로 우아하게 저하(graceful degrade).

---

## 5. 편집 & 안전 모델

- **비주얼 편집**(Tailwind 클래스·간격·색·폰트): 슬라이더/피커 조작 → 디바운스 후 소스에 **즉시 write-back** → 핫리로드로 반영. 브라우저 devtools처럼 즉각적이되 영구 저장.
- **Claude 편집**(레이아웃 변경·로직): 채팅 지시 → Agent가 **diff 미리보기** 제시 → 디자이너가 "적용"/"취소".
- **모든 편집 전 자동 스냅샷**: git 저장소면 stash/커밋 스냅샷, 아니면 `.zdesign/backups/`에 원본 백업 → 원클릭 되돌리기.

---

## 6. 설정 & 보안

- `INSTALLED_APPS += ["zdesign"]` + 미들웨어. **`DEBUG=True`에서만** 활성(prod 가드).
- `ANTHROPIC_API_KEY`는 환경변수. 없으면 채팅 패널 비활성(비주얼 편집은 계속 동작).
- **경로 제한:** 편집 대상은 프로젝트 템플릿/정적 루트 화이트리스트 밖으로 못 나감(디렉토리 탈출 방지).
- 모델: 최신 Claude(예: `claude-opus-4-8` 또는 `claude-sonnet-4-6`) 사용, 설정으로 교체 가능.

---

## 7. 테스트 전략

- **Instrumenter:** 템플릿 픽스처 → 주입/소스맵 정확도 (단위).
- **Editor:** 라인 정확 write-back, 지문 폴백, 경로 제한/탈출 방지 (단위).
- **Bridge/Agent:** 선택→컨텍스트 번들 스냅샷, 에이전트 도구 호출 목킹 (통합).
- **E2E:** djust 데모 앱 실행 후 브라우저로 클릭→편집→핫리로드 확인 (browse 스킬 활용).

---

## 8. 단계 (Phasing)

- **P1 (MVP):** Instrumenter + Overlay(선택/하이라이트/소스 배지) + **비주얼 클래스 편집** write-back + git 스냅샷. *Claude 없이도 완결된 가치.*
- **P2:** Agent 인앱 채팅 + diff 미리보기 + 적용/취소.
- **P3:** 지문 폴백 견고화, 컴포넌트 트리 네비게이터, 다중 선택.

---

## 9. 미해결/향후 확인 사항

- djust 템플릿 로더/렌더 훅 지점의 정확한 확장 API (P1 착수 시 djust 소스/문서로 확정).
- 비주얼 편집이 Tailwind 임의 클래스까지 자유 입력을 허용할지, 큐레이션된 컨트롤(간격/색/폰트 스케일)만 제공할지 — P1에서 큐레이션 우선, 자유 입력은 옵션.
- 오버레이 CSS 격리 방식(Shadow DOM vs 프리픽스 네임스페이스) — Alpine 호환성 확인 후 결정.
