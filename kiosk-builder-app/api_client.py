### api_client.py
import requests
import os
import json

BASE_URL = "https://port-0-kiosk-builder-m47pn82w3295ead8.sel4.cloudtype.app"
# ProjectManager (키오스크 매니저) API URL
PROJECT_MANAGER_URL = "https://kiosk-manager-production.up.railway.app"

def login(login_id: str, password: str) -> tuple[bool, str, int]:
    """
    로그인 함수

    Args:
        login_id: 사용자 아이디
        password: 비밀번호

    Returns:
        tuple: (성공 여부, 메시지, 사용자 ID)
    """
    url = f"{BASE_URL}/api/auth/login"
    payload = {"login_id": login_id, "password": password}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            # 로그인 성공 시 사용자 ID 반환 추가
            user_data = response.json()
            user_id = user_data.get("user_id", 0)
            return True, "", user_id
        else:
            detail = response.json().get("detail", "로그인 실패")
            return False, detail, 0
    except Exception as e:
        return False, f"서버 통신 실패: {e}", 0

def log_distribution_creation(user_id: int, app_name: str) -> tuple[bool, str]:
    """
    배포용 생성 액션을 로그에 기록하는 함수

    Args:
        user_id: 사용자 ID
        app_name: 앱 이름

    Returns:
        tuple: (성공 여부, 메시지)
    """
    url = f"{BASE_URL}/api/logs/create"
    payload = {
        "user_id": user_id,
        "app_name": app_name,
        "action": "button_click"
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return True, "로그 기록 성공"
        else:
            detail = response.json().get("detail", "로그 기록 실패")
            return False, detail
    except Exception as e:
        return False, f"서버 통신 실패: {e}"


def register_event_with_resources(
    event_name: str,
    kiosk_count: int,
    expired_at: str,
    config: dict,
    resources_dir: str,
    progress_callback=None
) -> tuple[bool, dict]:
    """
    이벤트를 ProjectManager에 등록하고 리소스를 Supabase에 업로드

    Args:
        event_name: 행사명
        kiosk_count: 키오스크 대수
        expired_at: 만료일 (ISO 형식)
        config: 설정 딕셔너리
        resources_dir: 리소스 폴더 경로
        progress_callback: 진행 상황 콜백 (percent, message)

    Returns:
        tuple: (성공 여부, 결과 딕셔너리)
    """
    try:
        # 1단계: 이벤트 등록
        if progress_callback:
            progress_callback(10, "이벤트 등록 중...")

        register_url = f"{PROJECT_MANAGER_URL}/api/events/register"
        register_payload = {
            "event_name": event_name,
            "kiosk_count": kiosk_count,
            "expired_at": expired_at
        }

        response = requests.post(register_url, json=register_payload, timeout=30)
        if response.status_code != 200 and response.status_code != 201:
            error_detail = response.json().get("detail", "이벤트 등록 실패")
            return False, {"error": f"이벤트 등록 실패: {error_detail}"}

        result = response.json()
        event_number = result.get("event_number")
        activation_codes = result.get("activation_codes", [])

        if not event_number:
            return False, {"error": "이벤트 번호를 받지 못했습니다."}

        if progress_callback:
            progress_callback(30, f"이벤트 등록 완료 (번호: {event_number})")

        # 2단계: config.json 업로드
        if progress_callback:
            progress_callback(40, "설정 파일 업로드 중...")

        config_json = json.dumps(config, ensure_ascii=False, indent=2)
        config_upload_url = f"{PROJECT_MANAGER_URL}/api/storage/upload/{event_number}"

        files = {
            "file": ("config.json", config_json.encode('utf-8'), "application/json")
        }
        data = {"file_type": "config"}

        response = requests.post(config_upload_url, files=files, data=data, timeout=60)
        if response.status_code != 200:
            print(f"config.json 업로드 실패: {response.text}")
            # 계속 진행 (경고만)

        if progress_callback:
            progress_callback(50, "설정 파일 업로드 완료")

        # 3단계: resources 폴더 내 파일 업로드
        if resources_dir and os.path.exists(resources_dir):
            if progress_callback:
                progress_callback(55, "리소스 파일 업로드 준비 중...")

            # 업로드할 파일 목록 수집
            files_to_upload = []
            for root, dirs, files_list in os.walk(resources_dir):
                for filename in files_list:
                    filepath = os.path.join(root, filename)
                    relative_path = os.path.relpath(filepath, resources_dir)
                    files_to_upload.append((filepath, relative_path))

            total_files = len(files_to_upload)
            uploaded_count = 0

            for filepath, relative_path in files_to_upload:
                try:
                    if progress_callback:
                        percent = 55 + int((uploaded_count / max(total_files, 1)) * 40)
                        progress_callback(percent, f"업로드 중: {relative_path}")

                    # 파일 읽기
                    with open(filepath, 'rb') as f:
                        file_content = f.read()

                    # 파일 확장자로 MIME 타입 추정
                    ext = os.path.splitext(filename)[1].lower()
                    mime_types = {
                        '.png': 'image/png',
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.gif': 'image/gif',
                        '.svg': 'image/svg+xml',
                        '.mp3': 'audio/mpeg',
                        '.wav': 'audio/wav',
                        '.mp4': 'video/mp4',
                        '.json': 'application/json',
                        '.txt': 'text/plain',
                    }
                    mime_type = mime_types.get(ext, 'application/octet-stream')

                    # 업로드
                    upload_url = f"{PROJECT_MANAGER_URL}/api/storage/upload/{event_number}"
                    files = {
                        "file": (relative_path.replace('\\', '/'), file_content, mime_type)
                    }
                    data = {"file_type": "resource"}

                    response = requests.post(upload_url, files=files, data=data, timeout=120)
                    if response.status_code == 200:
                        uploaded_count += 1
                    else:
                        print(f"파일 업로드 실패: {relative_path} - {response.text}")

                except Exception as e:
                    print(f"파일 업로드 오류: {relative_path} - {e}")

            if progress_callback:
                progress_callback(95, f"리소스 업로드 완료 ({uploaded_count}/{total_files}개)")

        if progress_callback:
            progress_callback(100, "등록 완료!")

        return True, {
            "event_name": event_name,
            "event_number": event_number,
            "activation_codes": activation_codes
        }

    except requests.exceptions.Timeout:
        return False, {"error": "서버 응답 시간 초과"}
    except requests.exceptions.ConnectionError:
        return False, {"error": "서버 연결 실패. 인터넷 연결을 확인하세요."}
    except Exception as e:
        return False, {"error": f"오류 발생: {str(e)}"}
