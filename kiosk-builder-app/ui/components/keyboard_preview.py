"""
키보드 스타일 미리보기 위젯

키보드 스타일 설정을 실시간으로 미리볼 수 있는 미니 키보드 위젯
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
from PySide6.QtCore import Qt, QSize, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QFontMetrics


class KeyboardStylePreview(QWidget):
    """
    키보드 스타일 미리보기 위젯

    실제 VirtualKeyboard의 스타일을 미리볼 수 있도록
    간소화된 키보드 레이아웃을 표시합니다.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 180)

        # 기본 스타일 설정
        self._style = {
            "bg_color": "#1B2838",
            "border_color": "#00FFC2",
            "border_width": 2,
            "border_radius": 15,
            "padding": 10,
            "font_size": 14,
            "button_bg_color": "#2D3748",
            "button_text_color": "white",
            "button_pressed_color": "#4A5568",
            "button_radius": 10,
            "hangul_btn_color": "#4299E1",
            "shift_btn_color": "#3182CE",
            "backspace_btn_color": "#6ae517",
            "next_btn_color": "#48BB78",
        }

        # 키 레이아웃 (간소화)
        self._keys = [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            ["ㅂ", "ㅈ", "ㄷ", "ㄱ", "ㅅ", "ㅛ", "ㅕ", "ㅑ", "ㅐ", "ㅔ"],
            ["ㅁ", "ㄴ", "ㅇ", "ㄹ", "ㅎ", "ㅗ", "ㅓ", "ㅏ", "ㅣ"],
            ["ㅋ", "ㅌ", "ㅊ", "ㅍ", "ㅠ", "ㅜ", "ㅡ"],
        ]

        self._special_keys = ["한/영", "Shift", "Space", "←", "다음"]

    def update_style(self, style_config: dict):
        """스타일 설정 업데이트"""
        self._style.update(style_config)
        self.update()

    def set_style_value(self, key: str, value):
        """개별 스타일 값 설정"""
        self._style[key] = value
        self.update()

    def paintEvent(self, event):
        """키보드 미리보기 렌더링"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 위젯 크기
        w = self.width()
        h = self.height()

        # 키보드 컨테이너 영역
        padding = 8
        kb_rect = self.rect().adjusted(padding, padding, -padding, -padding)

        # 키보드 배경
        border_width = max(1, self._style.get("border_width", 2) // 2)
        border_radius = min(self._style.get("border_radius", 15), 20)

        # 배경 그리기
        painter.setPen(QPen(QColor(self._style["border_color"]), border_width))
        painter.setBrush(QBrush(QColor(self._style["bg_color"])))
        painter.drawRoundedRect(kb_rect, border_radius, border_radius)

        # 키보드 내부 영역
        inner_padding = self._style.get("padding", 10) // 2 + border_width
        inner_rect = kb_rect.adjusted(inner_padding, inner_padding, -inner_padding, -inner_padding)

        # 키 버튼 그리기
        key_spacing = 3
        button_radius = min(self._style.get("button_radius", 10), 8)

        # 전체 행 수 (일반 키 + 특수 키)
        total_rows = len(self._keys) + 1
        row_height = (inner_rect.height() - key_spacing * (total_rows - 1)) / total_rows

        # 폰트 설정 (미리보기용 작은 폰트)
        font_size = max(8, min(self._style.get("font_size", 14) // 3, 12))
        font = QFont("맑은 고딕", font_size)
        painter.setFont(font)

        current_y = inner_rect.top()

        # 일반 키 그리기
        for row_idx, row in enumerate(self._keys):
            key_count = len(row)
            key_width = (inner_rect.width() - key_spacing * (key_count - 1)) / key_count

            current_x = inner_rect.left()
            for key in row:
                key_rect = QRectF(current_x, current_y, key_width - 1, row_height - 1)

                # 버튼 배경
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(self._style["button_bg_color"])))
                painter.drawRoundedRect(key_rect, button_radius, button_radius)

                # 버튼 텍스트
                painter.setPen(QColor(self._style["button_text_color"]))
                painter.drawText(key_rect, Qt.AlignCenter, key)

                current_x += key_width + key_spacing

            current_y += row_height + key_spacing

        # 특수 키 그리기
        special_colors = [
            self._style["hangul_btn_color"],  # 한/영
            self._style["shift_btn_color"],   # Shift
            self._style["button_bg_color"],   # Space
            self._style["backspace_btn_color"], # ←
            self._style["next_btn_color"],    # 다음
        ]

        # 특수 키 너비 비율: 한/영(2), Shift(2), Space(4), ←(2), 다음(2)
        widths = [2, 2, 4, 2, 2]
        total_width_units = sum(widths)
        unit_width = (inner_rect.width() - key_spacing * (len(self._special_keys) - 1)) / total_width_units

        current_x = inner_rect.left()
        for i, (key, color, width_units) in enumerate(zip(self._special_keys, special_colors, widths)):
            key_width = unit_width * width_units
            key_rect = QRectF(current_x, current_y, key_width - 1, row_height - 1)

            # 버튼 배경
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawRoundedRect(key_rect, button_radius, button_radius)

            # 버튼 텍스트
            painter.setPen(QColor(self._style["button_text_color"]))
            painter.drawText(key_rect, Qt.AlignCenter, key)

            current_x += key_width + key_spacing

    def sizeHint(self):
        return QSize(300, 200)


class KeyboardPreviewInScreen(QWidget):
    """
    화면 미리보기 내에 표시되는 키보드 스타일 미리보기

    LivePreviewWidget과 함께 사용하여 화면 내 키보드 위치에
    스타일이 적용된 키보드를 표시합니다.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 기본 스타일
        self._style = {}
        self._keyboard_rect = None  # 키보드 영역 (원본 좌표)

    def set_keyboard_rect(self, x, y, width, height):
        """키보드 영역 설정"""
        self._keyboard_rect = (x, y, width, height)
        self.update()

    def update_style(self, style_config: dict):
        """스타일 업데이트"""
        self._style.update(style_config)
        self.update()
