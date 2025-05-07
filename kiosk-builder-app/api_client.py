### api_client.py
import requests

BASE_URL = "https://port-0-kiosk-builder-m47pn82w3295ead8.sel4.cloudtype.app"

def login(login_id: str, password: str) -> tuple[bool, str]:
    url = f"{BASE_URL}/api/auth/login"
    payload = {"login_id": login_id, "password": password}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return True, ""
        else:
            detail = response.json().get("detail", "로그인 실패")
            return False, detail
    except Exception as e:
        return False, f"서버 통신 실패: {e}"


### settings_window.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("설정 화면")
        self.resize(400, 300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("로그인 성공! 설정을 변경하세요."))
        self.setLayout(layout)