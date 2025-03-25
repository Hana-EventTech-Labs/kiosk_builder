import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt, QCoreApplication
from screens.splash_screen import SplashScreen
from screens.process_screen import ProcessScreen
from screens.complete_screen import CompleteScreen
from screens.camera_screen import CameraScreen
from screens.text_input_screen import TextInputScreen  # 추가된 부분
from config import config
from webcam_utils.webcam_controller import release_camera
from PySide6.QtWidgets import QWidget
from screens.QR_screen import QR_screen
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
            # _internal을 쓸 경우
            # program_directory = os.path.join(program_directory, "_internal")
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
        
        # 2번 화면 (텍스트 입력)
        self.text_input_screen = TextInputScreen(self.stack, self.screen_size, self)
        
        self.process_screen = ProcessScreen(self.stack, self.screen_size, self)
        self.complete_screen = CompleteScreen(self.stack, self.screen_size, self)
        self.qr_screen = QR_screen(self.stack, self.screen_size, self)

        self.stack.addWidget(self.splash_screen)      # 인덱스 0
        self.stack.addWidget(self.photo_screen)       # 인덱스 1
        self.stack.addWidget(self.text_input_screen)  # 인덱스 2
        self.stack.addWidget(self.qr_screen)         # 인덱스 3
        self.stack.addWidget(self.process_screen)     # 인덱스 4
        self.stack.addWidget(self.complete_screen)    # 인덱스 5

    def getNextScreenIndex(self):
        # screen_order의 다음 인덱스로 이동
        self.current_index = (self.current_index + 1) % len(config["screen_order"])
        return config["screen_order"][self.current_index]

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
    
    def closeApplication(self):
        """앱 종료 동작"""
        QCoreApplication.instance().quit()  # 전체 애플리케이션 종료

    def closeEvent(self, event):
        """위젯이 닫힐 때 호출되는 이벤트 핸들러"""
        try:
            # 카메라 자원 해제
            if hasattr(self, 'photo_screen') and hasattr(self.photo_screen, 'webcam'):
                if hasattr(self.photo_screen.webcam, 'camera'):
                    release_camera(self.photo_screen.webcam.camera)

                #임시 이미지 파일 삭제
                temp_files = [
                    "resources/captured_image.jpg",
                    "resources/input_texts.json"
                ]
                
                for file_path in temp_files:
                    if os.path.exists(file_path):
                        os.remove(file_path)

        except Exception as e:
            print(f"카메라 자원 해제 오류: {e}")
        self.closeApplication()  # close_application 호출
        event.accept()
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KioskApp()
    window.show()
    sys.exit(app.exec())