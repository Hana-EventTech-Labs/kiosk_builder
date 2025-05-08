import os
import shutil
from PySide6.QtWidgets import QFileDialog, QMessageBox

class FileHandler:
    @staticmethod
    def browse_image_file(parent, line_edit):
        """이미지 파일 선택 다이얼로그"""
        file_path, _ = QFileDialog.getOpenFileName(
            parent, 
            "이미지 파일 선택", 
            "resources", 
            "이미지 파일 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            # 리소스 폴더 경로 확인
            resources_img_path = os.path.abspath("resources")
            
            # 파일 경로 정규화하여 비교
            normalized_file_path = os.path.normpath(file_path)
            normalized_resources_path = os.path.normpath(resources_img_path)
            
            # 파일이 리소스 폴더 외부에 있는 경우에만 복사 여부 확인
            if not normalized_file_path.startswith(normalized_resources_path):
                file_name = os.path.basename(file_path)
                target_path = os.path.join(resources_img_path, file_name)
                
                # 경로 구분자를 백슬래시(\)로 통일
                display_file_path = normalized_file_path.replace("/", "\\")
                display_target_path = os.path.normpath(target_path).replace("/", "\\")
                
                # 파일 복사 여부 확인
                reply = QMessageBox.question(
                    parent, 
                    "파일 복사", 
                    f"선택한 파일을 resources 폴더로 복사하시겠습니까?\n\n원본: {display_file_path}\n대상: {display_target_path}",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    try:
                        # 대상 폴더가 없으면 생성
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        
                        # 파일 복사
                        shutil.copy2(file_path, target_path)
                        
                        # 복사 성공 메시지
                        QMessageBox.information(
                            parent,
                            "파일 복사 완료",
                            f"파일이 resources 폴더로 복사되었습니다."
                        )
                        
                        # 파일명만 설정
                        line_edit.setText(file_name)
                    except Exception as e:
                        # 복사 실패 시 오류 메시지
                        QMessageBox.critical(
                            parent,
                            "파일 복사 실패",
                            f"파일 복사 중 오류가 발생했습니다: {str(e)}"
                        )
                        # 전체 경로 설정
                        line_edit.setText(file_path)
                else:
                    # 복사하지 않는 경우 파일명만 설정
                    line_edit.setText(file_name)
                    # 사용자에게 수동 복사 안내
                    QMessageBox.warning(
                        parent, 
                        "파일 경로", 
                        f"파일명만 설정되었습니다. 실제 사용을 위해서는 해당 파일을 resources 폴더로 수동으로 복사해야 합니다."
                    )
            else:
                # 이미 리소스 폴더 내부에 있는 경우 상대 경로 사용
                rel_path = os.path.relpath(file_path, resources_img_path)
                line_edit.setText(rel_path)
    
    @staticmethod
    def browse_background_file(parent, line_edit, screen_key):
        """배경화면 이미지 파일 선택 다이얼로그"""
        file_path, _ = QFileDialog.getOpenFileName(
            parent, 
            "배경화면 이미지 선택", 
            "resources/background", 
            "이미지 파일 (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            # resources/background 폴더 경로 확인
            resources_background_path = os.path.abspath("resources/background")
            
            # 파일 경로 정규화하여 비교
            normalized_file_path = os.path.normpath(file_path)
            normalized_resources_path = os.path.normpath(resources_background_path)
            
            # 화면 번호별 이름으로 복사 (1:카메라, 2:키보드, 3:QR, 4:발급중, 5:발급완료)
            screen_index = screen_key
            if isinstance(screen_key, str) and screen_key in ["splash", "process", "complete"]:
                screen_index = {"splash": "0", "process": "4", "complete": "5"}.get(screen_key, "0")
            
            target_filename = f"{screen_index}.jpg"
            
            # 원본 파일명에서 확장자를 제외한 이름 가져오기
            original_name = os.path.basename(file_path)
            display_name = os.path.splitext(original_name)[0]
            
            # 파일이 리소스 폴더 외부에 있는 경우 복사 여부 확인
            if not normalized_file_path.startswith(normalized_resources_path):
                target_path = os.path.join(resources_background_path, target_filename)
                
                # 경로 구분자를 백슬래시(\)로 통일
                display_file_path = normalized_file_path.replace("/", "\\")
                display_target_path = os.path.normpath(target_path).replace("/", "\\")
                
                # 파일 복사 여부 확인
                reply = QMessageBox.question(
                    parent, 
                    "배경화면 파일 복사", 
                    f"선택한 배경화면을 resources/background/{target_filename}으로 복사하시겠습니까?\n\n원본: {display_file_path}\n대상: {display_target_path}",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    try:
                        # 대상 폴더가 없으면 생성
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        
                        # 파일 복사
                        shutil.copy2(file_path, target_path)
                        
                        # 복사 성공 메시지
                        QMessageBox.information(
                            parent,
                            "파일 복사 완료",
                            f"배경화면이 resources/background/{target_filename}로 복사되었습니다."
                        )
                        
                        # 원본 파일 이름을 표시 및 저장
                        line_edit.setText(display_name)
                    except Exception as e:
                        # 복사 실패 시 오류 메시지
                        QMessageBox.critical(
                            parent,
                            "파일 복사 실패",
                            f"배경화면 파일 복사 중 오류가 발생했습니다: {str(e)}"
                        )
                else:
                    # 복사하지 않는 경우 복사 필요 안내
                    QMessageBox.warning(
                        parent, 
                        "수동 복사 필요", 
                        f"배경화면으로 사용하려면 해당 파일을 resources/background/{target_filename}으로 수동으로 복사해야 합니다."
                    )
            else:
                # 이미 리소스 폴더 내부에 있는 경우, 적절한 이름으로 복사
                file_ext = os.path.splitext(file_path)[1]
                target_path = os.path.join(resources_background_path, target_filename)
                
                # 파일 확장자가 다른 경우에도 적절히 처리
                if file_path != target_path:
                    try:
                        shutil.copy2(file_path, target_path)
                        QMessageBox.information(
                            parent,
                            "파일 복사 완료",
                            f"배경화면이 resources/background/{target_filename}로 복사되었습니다."
                        )
                    except Exception as e:
                        QMessageBox.critical(
                            parent,
                            "파일 복사 실패",
                            f"배경화면 파일 복사 중 오류가 발생했습니다: {str(e)}"
                        )
                
                # 원본 파일 이름을 표시 및 저장
                line_edit.setText(display_name)
    
    @staticmethod
    def browse_font_file(parent, line_edit):
        """폰트 파일 선택 다이얼로그"""
        file_path, _ = QFileDialog.getOpenFileName(
            parent, 
            "폰트 파일 선택", 
            "resources/font", 
            "폰트 파일 (*.ttf *.otf *.woff *.woff2)"
        )
        
        if file_path:
            # 리소스 폰트 폴더 경로 확인
            resources_font_path = os.path.abspath("resources/font")
            
            # 파일 경로 정규화하여 비교
            normalized_file_path = os.path.normpath(file_path)
            normalized_resources_font_path = os.path.normpath(resources_font_path)
            
            # 파일이 리소스 폴더 외부에 있는 경우에만 복사 여부 확인
            if not normalized_file_path.startswith(normalized_resources_font_path):
                file_name = os.path.basename(file_path)
                target_path = os.path.join(resources_font_path, file_name)
                
                # 경로 구분자를 백슬래시(\)로 통일
                display_file_path = normalized_file_path.replace("/", "\\")
                display_target_path = os.path.normpath(target_path).replace("/", "\\")
                
                # 파일 복사 여부 확인
                reply = QMessageBox.question(
                    parent, 
                    "폰트 파일 복사", 
                    f"선택한 폰트 파일을 resources/font 폴더로 복사하시겠습니까?\n\n원본: {display_file_path}\n대상: {display_target_path}",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    try:
                        # 대상 폴더가 없으면 생성
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        
                        # 파일 복사
                        shutil.copy2(file_path, target_path)
                        
                        # 복사 성공 메시지
                        QMessageBox.information(
                            parent,
                            "파일 복사 완료",
                            f"폰트 파일이 resources/font 폴더로 복사되었습니다."
                        )
                        
                        # 파일명만 설정
                        line_edit.setText(file_name)
                    except Exception as e:
                        # 복사 실패 시 오류 메시지
                        QMessageBox.critical(
                            parent,
                            "파일 복사 실패",
                            f"폰트 파일 복사 중 오류가 발생했습니다: {str(e)}"
                        )
                        # 전체 경로 설정
                        line_edit.setText(file_path)
                else:
                    # 복사하지 않는 경우 파일명만 설정
                    line_edit.setText(file_name)
                    # 사용자에게 수동 복사 안내
                    QMessageBox.warning(
                        parent, 
                        "파일 경로", 
                        f"파일명만 설정되었습니다. 실제 사용을 위해서는 해당 폰트 파일을 resources/font 폴더로 수동으로 복사해야 합니다."
                    )
            else:
                # 이미 리소스 폴더 내부에 있는 경우 파일명만 사용
                file_name = os.path.basename(file_path)
                line_edit.setText(file_name)