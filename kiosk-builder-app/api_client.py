### api_client.py
import requests

BASE_URL = "https://port-0-kiosk-builder-m47pn82w3295ead8.sel4.cloudtype.app"

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