import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from screens.splash_screen import SplashScreen
from screens.process_screen import ProcessScreen
from screens.complete_screen import CompleteScreen
from screens.camera_screen import CameraScreen
from screens.text_input_screen import TextInputScreen
from screens.activation_screen import ActivationScreen  # 활성화 화면 추가
from config import config
from webcam_utils.webcam_controller import release_camera
from PySide6.QtWidgets import QWidget
from screens.QR_screen import QR_screen
from screens.frame_screen import FrameScreen

# 애플리케이션 중복 실행 방지 클래스
class SingleApplication(QApplication):
    def __init__(self, app_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_id = app_id
        self.server = None
        
        # 이미 실행 중인지 확인
        socket = QLocalSocket()
        socket.connectToServer(self.app_id)
        is_running = socket.waitForConnected(500)
        
        if is_running:
            # 이미 실행 중인 경우
            QMessageBox.warning(None, "이미 실행 중", "슈퍼 키오스크가 이미 실행 중입니다.")
            sys.exit(0)
        else:
            # 새로운 인스턴스인 경우, 서버 생성
            self.server = QLocalServer()
            self.server.listen(self.app_id)
            self.aboutToQuit.connect(self.close_server)

    def close_server(self):
        """로컬 서버 정리 - 개선된 버전"""
        try:
            print("로컬 서버 종료 중...")
            if self.server:
                if self.server.isListening():
                    self.server.close()
                self.server.deleteLater()
                self.server = None
            print("로컬 서버 종료 완료")
        except Exception as e:
            print(f"서버 종료 오류: {e}")

class KioskApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_closing = False  # 종료 중 플래그
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

        # 활성화 필요 여부 확인
        self.require_activation = config.get("require_activation", True)

        # 온라인 모드에서 아직 활성화되지 않은 경우: 활성화 화면만 생성
        # (다른 화면들은 config가 없어서 생성 불가)
        needs_activation = self.require_activation and not self.isAlreadyActivated()

        if needs_activation:
            print("활성화 필요: 활성화 화면만 생성")
            # 활성화 화면만 생성
            self.activation_screen = ActivationScreen(self.stack, self.screen_size, self)
            self.stack.addWidget(self.activation_screen)  # 인덱스 0

            # 나머지 화면은 None으로 초기화 (활성화 후 생성됨)
            self.splash_screen = None
            self.photo_screen = None
            self.text_input_screen = None
            self.process_screen = None
            self.complete_screen = None
            self.qr_screen = None
            self.frame_screen = None
        else:
            # 오프라인 모드 또는 이미 활성화된 경우: 모든 화면 생성
            print("전체 화면 생성 (오프라인 모드 또는 이미 활성화됨)")
            self.activation_screen = ActivationScreen(self.stack, self.screen_size, self)
            self.splash_screen = SplashScreen(self.stack, self.screen_size, self)
            self.photo_screen = CameraScreen(self.stack, self.screen_size, self)
            self.text_input_screen = TextInputScreen(self.stack, self.screen_size, self)
            self.process_screen = ProcessScreen(self.stack, self.screen_size, self)
            self.complete_screen = CompleteScreen(self.stack, self.screen_size, self)
            self.qr_screen = QR_screen(self.stack, self.screen_size, self)
            self.frame_screen = FrameScreen(self.stack, self.screen_size, self)

            self.stack.addWidget(self.activation_screen)  # 인덱스 0 (활성화)
            self.stack.addWidget(self.splash_screen)      # 인덱스 1
            self.stack.addWidget(self.photo_screen)       # 인덱스 2
            self.stack.addWidget(self.text_input_screen)  # 인덱스 3
            self.stack.addWidget(self.qr_screen)          # 인덱스 4
            self.stack.addWidget(self.frame_screen)       # 인덱스 5
            self.stack.addWidget(self.process_screen)     # 인덱스 6
            self.stack.addWidget(self.complete_screen)    # 인덱스 7

            # 오프라인 모드 또는 이미 활성화된 경우 활성화 화면 건너뛰기
            if not self.require_activation:
                print("오프라인 모드: 활성화 화면 건너뛰기")
                self.stack.setCurrentIndex(1)  # 스플래시 화면부터 시작
            else:
                print("이미 활성화됨: 활성화 화면 건너뛰기")
                self.stack.setCurrentIndex(1)  # 스플래시 화면부터 시작

    def buildAllScreens(self):
        """활성화 후 모든 화면 생성 (config 다운로드 후 호출)"""
        try:
            print("모든 화면 생성 중...")

            # config 모듈 다시 로드
            import importlib
            import config as config_module
            importlib.reload(config_module)

            # 전역 config 변수 업데이트
            global config
            from config import config as new_config
            config = new_config

            print(f"설정 로드됨: {config.get('app_name', 'Unknown')}")

            # 이미 화면이 생성되어 있으면 스킵
            if self.splash_screen is not None:
                print("화면이 이미 생성되어 있음 - 스킵")
                return True

            # 모든 화면 생성
            self.splash_screen = SplashScreen(self.stack, self.screen_size, self)
            self.photo_screen = CameraScreen(self.stack, self.screen_size, self)
            self.text_input_screen = TextInputScreen(self.stack, self.screen_size, self)
            self.process_screen = ProcessScreen(self.stack, self.screen_size, self)
            self.complete_screen = CompleteScreen(self.stack, self.screen_size, self)
            self.qr_screen = QR_screen(self.stack, self.screen_size, self)
            self.frame_screen = FrameScreen(self.stack, self.screen_size, self)

            # 스택에 추가 (인덱스 1부터)
            self.stack.addWidget(self.splash_screen)      # 인덱스 1
            self.stack.addWidget(self.photo_screen)       # 인덱스 2
            self.stack.addWidget(self.text_input_screen)  # 인덱스 3
            self.stack.addWidget(self.qr_screen)          # 인덱스 4
            self.stack.addWidget(self.frame_screen)       # 인덱스 5
            self.stack.addWidget(self.process_screen)     # 인덱스 6
            self.stack.addWidget(self.complete_screen)    # 인덱스 7

            print(f"모든 화면 생성 완료 (스택 위젯 수: {self.stack.count()})")
            return True
        except Exception as e:
            print(f"화면 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

    def rebuildSplashScreen(self):
        """스플래시 화면 재생성 (활성화 후 config 반영) - 하위 호환성"""
        # buildAllScreens로 대체
        self.buildAllScreens()

    def isAlreadyActivated(self):
        """이미 활성화되었는지 확인 (activation.json 존재 여부)"""
        try:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(os.path.abspath(sys.executable))
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))

            activation_file = os.path.join(base_dir, "activation.json")

            if os.path.exists(activation_file):
                import json
                with open(activation_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get("activated", False):
                        print(f"활성화 정보 확인: {data.get('event_name', 'Unknown')}")
                        return True
            return False
        except Exception as e:
            print(f"활성화 상태 확인 오류: {e}")
            return False

    def getNextScreenIndex(self):
        # screen_order의 다음 인덱스로 이동
        self.current_index = (self.current_index + 1) % len(config["screen_order"])
        # screen_order 값 + 1 = 실제 Stack 인덱스 (activation_screen이 0번이므로)
        # 0=스플래쉬→1, 1=촬영→2, 2=키보드→3, 3=QR→4, 4=프레임→5, 5=발급중→6, 6=완료→7
        return config["screen_order"][self.current_index] + 1

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
    
    def cleanup_resources(self):
        """모든 리소스 정리"""
        self.is_closing = True  # 종료 중 플래그 설정
        print("프로그램 종료 중... 리소스를 정리합니다.")

        # 1. 모든 화면의 리소스 해제
        screens = [
            'activation_screen', 'splash_screen', 'photo_screen', 'text_input_screen',
            'process_screen', 'complete_screen', 'qr_screen', 'frame_screen'
        ]
        
        for screen_name in screens:
            if hasattr(self, screen_name):
                screen = getattr(self, screen_name)
                if hasattr(screen, 'cleanup'):
                    screen.cleanup()
        
        # 2. 카메라 자원 해제
        if hasattr(self, 'photo_screen'):
            if hasattr(self.photo_screen, 'webcam') and self.photo_screen.webcam:
                if hasattr(self.photo_screen.webcam, 'camera') and self.photo_screen.webcam.camera:
                    print("카메라 리소스 해제 중...")
                    release_camera(self.photo_screen.webcam.camera)
                    self.photo_screen.webcam.camera = None
                
                # 웹캠 객체 정리
                if hasattr(self.photo_screen.webcam, 'timer'):
                    self.photo_screen.webcam.timer.stop()
                self.photo_screen.webcam = None

        # 3. QStackedWidget의 모든 위젯 제거
        if hasattr(self, 'stack'):
            while self.stack.count() > 0:
                widget = self.stack.widget(0)
                self.stack.removeWidget(widget)
                if widget:
                    widget.deleteLater()

        # 4. 임시 파일 삭제
        temp_files = [
            "resources/captured_image.jpg",
            "resources/qr_uploaded_image.jpg", 
            "resources/input_texts.json",
            "resources/framed_photo.jpg"
        ]
        
        for file_path in temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"임시 파일 삭제: {file_path}")
            except Exception as e:
                print(f"파일 삭제 실패 {file_path}: {e}")

        # 5. Qt 이벤트 루프 정리
        QCoreApplication.processEvents()
        
        # 6. 강제로 가비지 컬렉션 실행
        import gc
        gc.collect()
        
        print("리소스 정리 완료")

    def closeApplication(self):
        """앱 종료 동작 - 리소스 정리 포함"""
        try:
            self.cleanup_resources()
        except Exception as e:
            print(f"리소스 해제 중 오류: {e}")
        finally:
            # 애플리케이션 종료
            QCoreApplication.instance().quit()

    def closeEvent(self, event):
        """위젯이 닫힐 때 호출되는 이벤트 핸들러 - 개선된 버전"""
        try:
            self.cleanup_resources()
        except Exception as e:
            print(f"리소스 해제 중 오류: {e}")
        finally:
            # 애플리케이션 종료
            QCoreApplication.instance().quit()
            event.accept()

if __name__ == "__main__":
    # 애플리케이션 ID 지정
    app_id = "kiosk_app_unique_id"
    
    try:
        app = SingleApplication(app_id, sys.argv)
        window = KioskApp()
        window.show()
        
        # 애플리케이션 실행
        exit_code = app.exec()
        
        # 종료 시 추가 정리
        print("애플리케이션 종료 중...")
        
        # 윈도우 정리
        if window:
            window.deleteLater()
        
        # 애플리케이션 정리
        app.deleteLater()
        
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"애플리케이션 실행 오류: {e}")
        sys.exit(1)