# 언어 선택 기능 및 미리보기 로직 분석 및 계획

## 현재 시스템 분석

### 1. 키오스크 앱 (main.py + screens/splash_screen.py)

**언어 버튼 활성화 조건:**
- `config.json`의 `language.enabled = true`일 때 언어 버튼 표시
- `language_manager.is_enabled()` → `config["language"]["enabled"]` 확인

**언어 버튼 활성화 시 흐름:**
```
스플래쉬 화면
├─ 언어 버튼 표시 (한글/English)
├─ 배경: language_manager.get_background_path(0) → resources/background_ko/0.png 또는 background_en/0.png
├─ 버튼 클릭 시: onLanguageSelected(lang_code) → language_manager.current_language = lang_code
└─ 다음 화면들: 선택된 언어에 맞는 배경 사용
```

**언어 버튼 비활성화 시 흐름:**
```
스플래쉬 화면
├─ 언어 버튼 없음
├─ 배경: resources/background/0.png (기본 경로)
├─ 화면 터치 시: 다음 화면으로 이동
└─ 다음 화면들: 기본 배경 사용
```

### 2. 배경화면 경로 구조

```
resources/
├─ background/           # 기본 배경 (언어 선택 비활성화 시 사용)
│  ├─ 0.png (splash)
│  ├─ 1.png (camera)
│  ├─ 2.png (keyboard)
│  └─ ...
├─ background_ko/        # 한국어 배경 (언어 선택 활성화 + 한국어 선택 시)
│  ├─ 0.png
│  ├─ 1.png
│  └─ ...
└─ background_en/        # 영어 배경 (언어 선택 활성화 + 영어 선택 시)
   ├─ 0.png
   ├─ 1.png
   └─ ...
```

### 3. 설정 빌더 앱 (kiosk-builder-app)의 현재 문제

**현재 미리보기 로직:**
- 라디오 버튼으로 "기본/한국어/영어" 선택
- 선택된 언어의 배경 파일이 **없으면 기본 배경**을 표시
- 문제: 사용자가 언어 버튼 **비활성화** 상태인데도 한국어/영어 미리보기를 볼 수 있음

**원하는 동작:**
- 언어 버튼 **활성화** 시: 한국어/영어 배경만 사용 (기본 배경 무시)
- 언어 버튼 **비활성화** 시: 기본 배경만 사용 (한국어/영어 미리보기 불필요)

## 구현 계획

### Phase 1: 언어 선택 활성화 설정 연동

**1.1. 스플래쉬 화면 설정에서 언어 버튼 활성화 체크박스 확인**
- 현재 `splash_tab.py`에 언어 버튼 활성화 체크박스가 있는지 확인
- 없다면 추가 필요

**1.2. 촬영 화면(capture_tab) 미리보기 라디오 버튼 동작 변경**
- 언어 버튼 **활성화** 시:
  - "기본" 라디오 버튼 숨김 또는 비활성화
  - "한국어", "English" 라디오 버튼만 표시
  - 미리보기는 해당 언어 배경 또는 빈 배경 표시

- 언어 버튼 **비활성화** 시:
  - "기본" 라디오 버튼만 표시 (또는 라디오 버튼 섹션 전체 숨김)
  - 기본 배경만 미리보기

### Phase 2: 미리보기 로직 수정

**2.1. `_update_screen_preview()` 수정**
```python
# 언어 버튼 활성화 여부 확인
lang_enabled = self.config.get("language", {}).get("enabled", False)

if lang_enabled:
    # 활성화: 선택된 언어(ko/en)의 배경만 사용
    lang = self._current_lang_preview  # "ko" 또는 "en"
    if lang:
        bg_path = FileHandler.resolve_background_path(screen_key, lang=lang)
    else:
        bg_path = None  # 기본 선택 시 빈 배경 또는 첫 번째 언어 배경
else:
    # 비활성화: 기본 배경만 사용
    bg_path = FileHandler.resolve_background_path(screen_key, lang=None)
```

**2.2. 라디오 버튼 동적 표시/숨김**
```python
def _update_preview_radio_visibility(self):
    """언어 버튼 활성화 상태에 따라 라디오 버튼 표시/숨김"""
    lang_enabled = self.config.get("language", {}).get("enabled", False)

    if lang_enabled:
        self.radio_default.hide()  # 기본 숨김
        self.radio_ko.show()
        self.radio_en.show()
        # 기본 선택이면 한국어로 변경
        if self.radio_default.isChecked():
            self.radio_ko.setChecked(True)
            self._current_lang_preview = "ko"
    else:
        self.radio_default.show()
        self.radio_default.setChecked(True)
        self.radio_ko.hide()
        self.radio_en.hide()
        self._current_lang_preview = None
```

### Phase 3: 다른 탭에도 동일 로직 적용

각 화면 탭(splash_tab, qr_tab, frame_tab, complete_tab 등)에도 동일한 로직 적용 필요

### Phase 4: 테스트

1. 언어 버튼 활성화 → 한국어/영어 배경 미리보기 확인
2. 언어 버튼 비활성화 → 기본 배경만 미리보기 확인
3. 언어 버튼 토글 시 라디오 버튼 동적 변경 확인

## 파일 수정 목록

1. `ui/screens/config_editor/capture_tab.py`
   - `_init_camera_settings()`: 라디오 버튼 동적 표시 로직 추가
   - `_update_screen_preview()`: 언어 활성화 상태 확인 로직 추가
   - `_on_preview_lang_changed()`: 활성화 상태에 따른 처리

2. `ui/screens/config_editor/splash_tab.py`
   - 언어 버튼 활성화 체크박스 변경 시 capture_tab에 알림

3. (필요시) 다른 탭들도 동일 패턴 적용

## 질문/확인 필요

1. 언어 버튼 활성화 설정은 어느 탭에서 관리되나요? (splash_tab? basic_tab?)
2. 언어 버튼 활성화 시 "기본" 미리보기가 필요한가요? 아니면 한국어/영어만 필요한가요?
