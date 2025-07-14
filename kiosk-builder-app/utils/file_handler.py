import os
import shutil
import json
from datetime import datetime
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
    def _remove_existing_background_files(background_path, screen_index, exclude_ext=None):
        """같은 이름의 기존 배경화면 파일들 삭제 (새로 추가된 파일 제외)"""
        supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.mp4']
        
        for ext in supported_extensions:
            # 새로 추가된 파일의 확장자는 제외
            if exclude_ext and ext.lower() == exclude_ext.lower():
                continue
                
            existing_file = os.path.join(background_path, f"{screen_index}{ext}")
            if os.path.exists(existing_file):
                try:
                    os.remove(existing_file)
                    print(f"기존 파일 삭제: {existing_file}")
                except Exception as e:
                    print(f"기존 파일 삭제 실패: {existing_file}, 오류: {e}")

    @staticmethod
    def browse_background_file(parent, line_edit, screen_key):
        """배경화면 파일 선택 다이얼로그 (이미지, 동영상, GIF 지원)"""
        file_path, _ = QFileDialog.getOpenFileName(
            parent, 
            "배경화면 파일 선택", 
            "resources/background", 
            "배경화면 파일 (*.png *.jpg *.jpeg *.bmp *.gif *.mp4)"
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
            
            # 원본 파일 확장자 유지
            original_ext = os.path.splitext(file_path)[1].lower()
            target_filename = f"{screen_index}{original_ext}"
            
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
                        
                        # 복사 성공 후 기존 파일들 삭제 (새 파일 제외)
                        FileHandler._remove_existing_background_files(resources_background_path, screen_index, original_ext)
                        
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
                target_path = os.path.join(resources_background_path, target_filename)
                
                # 파일 확장자가 다른 경우에도 적절히 처리
                if file_path != target_path:
                    try:
                        shutil.copy2(file_path, target_path)
                        
                        # 복사 성공 후 기존 파일들 삭제 (새 파일 제외)
                        FileHandler._remove_existing_background_files(resources_background_path, screen_index, original_ext)
                        
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
                else:
                    # 같은 파일인 경우에도 기존 다른 확장자 파일들 삭제 (새 파일 제외)
                    FileHandler._remove_existing_background_files(resources_background_path, screen_index, original_ext)
                
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

    @staticmethod
    def export_config_to_json(parent, config):
        """설정을 JSON 파일로 내보내기"""
        # 기본 파일명 생성 (현재 날짜 및 시간 포함)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"config_backup_{current_time}.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            "설정 파일 내보내기",
            default_filename,
            "JSON 파일 (*.json)"
        )
        
        if file_path:
            try:
                # JSON 파일로 저장
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                
                QMessageBox.information(
                    parent,
                    "내보내기 완료",
                    f"설정이 성공적으로 저장되었습니다:\n{file_path}"
                )
                return True
                
            except Exception as e:
                QMessageBox.critical(
                    parent,
                    "내보내기 실패",
                    f"설정 파일 저장 중 오류가 발생했습니다:\n{str(e)}"
                )
                return False
        
        return False
    
    @staticmethod
    def import_config_from_json(parent):
        """JSON 파일에서 설정 가져오기"""
        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            "설정 파일 가져오기",
            "",
            "JSON 파일 (*.json)"
        )
        
        if file_path:
            try:
                # JSON 파일 읽기
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                
                # 설정 유효성 검사 (기본적인 키 체크)
                required_keys = ['screen_size', 'frame', 'photo', 'camera_count']
                missing_keys = [key for key in required_keys if key not in imported_config]
                
                if missing_keys:
                    QMessageBox.warning(
                        parent,
                        "가져오기 경고",
                        f"설정 파일에 일부 필수 키가 누락되었습니다:\n{', '.join(missing_keys)}\n\n가져오기를 계속하시겠습니까?"
                    )
                
                # 사용자 확인
                reply = QMessageBox.question(
                    parent,
                    "설정 가져오기 확인",
                    f"선택한 파일에서 설정을 가져오시겠습니까?\n\n{file_path}\n\n현재 설정은 덮어씌워집니다.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 디버그 정보 출력
                    print(f"JSON 가져오기: {len(imported_config)} 개의 설정 항목을 가져왔습니다.")
                    print(f"주요 설정 확인 - screen_size: {imported_config.get('screen_size')}")
                    print(f"주요 설정 확인 - frame: {imported_config.get('frame')}")
                    print(f"주요 설정 확인 - photo: {imported_config.get('photo')}")
                    
                    QMessageBox.information(
                        parent,
                        "가져오기 완료",
                        "설정이 성공적으로 가져와졌습니다.\n변경사항을 적용하려면 '저장' 버튼을 클릭하세요."
                    )
                    return imported_config
                
            except json.JSONDecodeError as e:
                QMessageBox.critical(
                    parent,
                    "가져오기 실패",
                    f"JSON 파일 형식이 올바르지 않습니다:\n{str(e)}"
                )
            except Exception as e:
                QMessageBox.critical(
                    parent,
                    "가져오기 실패",
                    f"설정 파일 읽기 중 오류가 발생했습니다:\n{str(e)}"
                )
        
        return None