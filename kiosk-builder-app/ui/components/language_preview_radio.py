# 언어별 미리보기 라디오 버튼 컴포넌트
# 모든 탭에서 재사용 가능한 언어 선택 라디오 버튼

from PySide6.QtWidgets import QWidget, QHBoxLayout, QRadioButton, QButtonGroup, QLabel
from PySide6.QtCore import Signal


class LanguagePreviewRadio(QWidget):
    """언어별 미리보기 선택을 위한 라디오 버튼 그룹 컴포넌트"""

    # 언어 변경 시그널: 선택된 언어 코드 (None, "ko", "en")
    language_changed = Signal(object)

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config
        self._current_lang = None  # 현재 선택된 언어 (None=기본, "ko", "en")
        self._init_ui()

    def _init_ui(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 라디오 버튼 그룹
        self.button_group = QButtonGroup(self)

        # 라디오 버튼 생성
        self.radio_default = QRadioButton("기본")
        self.radio_ko = QRadioButton("한국어")
        self.radio_en = QRadioButton("English")

        # 기본 선택
        self.radio_default.setChecked(True)

        # 버튼 그룹에 추가
        self.button_group.addButton(self.radio_default, 0)
        self.button_group.addButton(self.radio_ko, 1)
        self.button_group.addButton(self.radio_en, 2)

        # 시그널 연결
        self.button_group.buttonClicked.connect(self._on_button_clicked)

        # 레이아웃에 추가
        layout.addWidget(self.radio_default)
        layout.addWidget(self.radio_ko)
        layout.addWidget(self.radio_en)
        layout.addStretch()

    def _on_button_clicked(self, button):
        """라디오 버튼 클릭 시 호출"""
        if button == self.radio_default:
            self._current_lang = None
        elif button == self.radio_ko:
            self._current_lang = "ko"
        else:
            self._current_lang = "en"

        # 시그널 emit
        self.language_changed.emit(self._current_lang)

    def get_current_language(self):
        """현재 선택된 언어 반환"""
        return self._current_lang

    def set_config(self, config):
        """config 참조 설정"""
        self.config = config

    def update_visibility(self, lang_enabled: bool = None):
        """언어 활성화 상태에 따라 라디오 버튼 활성화/비활성화

        Args:
            lang_enabled: 언어 활성화 여부. None이면 config에서 읽음
        """
        if lang_enabled is None:
            if self.config:
                lang_enabled = self.config.get("language", {}).get("enabled", False)
            else:
                lang_enabled = False

        # 모든 라디오 버튼 항상 표시
        self.radio_default.show()
        self.radio_ko.show()
        self.radio_en.show()

        if lang_enabled:
            # 언어 활성화: 기본 비활성화, 한국어/영어 활성화
            self.radio_default.setEnabled(False)
            self.radio_ko.setEnabled(True)
            self.radio_en.setEnabled(True)

            # 기본이 선택되어 있으면 한국어로 변경
            if self.radio_default.isChecked():
                self.radio_ko.setChecked(True)

            # 현재 선택된 라디오박스에 맞게 _current_lang 동기화
            if self.radio_ko.isChecked():
                self._current_lang = "ko"
            elif self.radio_en.isChecked():
                self._current_lang = "en"
        else:
            # 언어 비활성화: 기본 활성화, 한국어/영어 비활성화
            self.radio_default.setEnabled(True)
            self.radio_ko.setEnabled(False)
            self.radio_en.setEnabled(False)

            # 한국어/영어가 선택되어 있으면 기본으로 변경
            if not self.radio_default.isChecked():
                self.radio_default.setChecked(True)

            self._current_lang = None

    def sync_language_state(self):
        """현재 라디오 버튼 상태에 맞게 _current_lang 동기화 및 시그널 emit"""
        if self.radio_default.isChecked():
            self._current_lang = None
        elif self.radio_ko.isChecked():
            self._current_lang = "ko"
        elif self.radio_en.isChecked():
            self._current_lang = "en"

        # 시그널 emit하여 미리보기 업데이트
        self.language_changed.emit(self._current_lang)
