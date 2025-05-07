from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from api_client import login

class LoginWindow(QWidget):
    def __init__(self, on_login_success=None):
        super().__init__()
        self.setWindowTitle("로그인")
        self.resize(300, 150)
        self.on_login_success = on_login_success

        layout = QVBoxLayout()

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Login ID")
        layout.addWidget(QLabel("아이디"))
        layout.addWidget(self.id_input)

        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("Password")
        self.pw_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("비밀번호"))
        layout.addWidget(self.pw_input)

        self.login_button = QPushButton("로그인")
        self.login_button.clicked.connect(self.attempt_login)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def attempt_login(self):
        login_id = self.id_input.text()
        password = self.pw_input.text()

        try:
            success = login(login_id, password)
            if success:
                self.close()
                if self.on_login_success:
                    self.on_login_success()
            else:
                QMessageBox.warning(self, "로그인 실패", "아이디 또는 비밀번호가 올바르지 않습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"로그인 중 오류 발생: {e}")