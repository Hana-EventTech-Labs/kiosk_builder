import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt, QCoreApplication
from screens.splash_screen import SplashScreen
from screens.process_screen import ProcessScreen
from screens.complete_screen import CompleteScreen
from screens.camera_screen import CameraScreen
from config import config

class KioskApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config["app_name"])
        self.screen_size = (config["screen_size"]["width"], config["screen_size"]["height"])
        self.setFixedSize(*self.screen_size)
        self.showFullScreen()
        
        if getattr(sys, 'frozen', False):
            # 실행파일로 실행한 경우,해당 파일을 보관한 디렉토리의 full path를 취득
            program_directory = os.path.dirname(os.path.abspath(sys.executable))
            program_directory = os.path.join(program_directory, "_internal")
        else:
            # 파이썬 파일로 실행한 경우,해당 파일을 보관한 디렉토리의 full path를 취득
            program_directory = os.path.dirname(os.path.abspath(__file__))
        os.chdir(program_directory)

        self.current_index = 0

        self.setupStack()

        self.setCentralWidget(self.stack)

    def setupStack(self):
        self.stack = QStackedWidget()
        self.splash_screen = SplashScreen(self.stack, self.screen_size, self)
        self.photo_screen = CameraScreen(self.stack, self.screen_size, self)
        self.process_screen = ProcessScreen(self.stack, self.screen_size, self)
        self.complete_screen = CompleteScreen(self.stack, self.screen_size, self)

        self.stack.addWidget(self.splash_screen)
        self.stack.addWidget(self.photo_screen)
        self.stack.addWidget(self.process_screen)
        self.stack.addWidget(self.complete_screen)

    def getNextScreenIndex(self):
        # 중앙 상태와 screen_order를 이용해 다음 스크린 인덱스를 결정하는 로직
        if self.current_index + 1 < len(config["screen_order"]):
            self.current_index += 1
        else:
            self.current_index = 0
        return config["screen_order"][self.current_index]

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
    
    def closeApplication(self):
        """앱 종료 동작"""
        QCoreApplication.instance().quit()  # 전체 애플리케이션 종료

    def closeEvent(self, event):
        """위젯이 닫힐 때 호출되는 이벤트 핸들러"""
        self.closeApplication()  # close_application 호출
        event.accept()
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KioskApp()
    window.show()
    sys.exit(app.exec())