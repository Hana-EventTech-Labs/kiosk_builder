#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from api_client import login

class AuthManager:
    def __init__(self):
        self.auth_file = "auth_settings.dat"
        self.salt = b'kiosk_builder_salt_2024'  # 고정 솔트 (실제 환경에서는 랜덤 생성 권장)
        self.key = self._generate_key()
        self.cipher = Fernet(self.key)
        
    def _generate_key(self):
        """암호화 키 생성"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(b"kiosk_builder_secret_key"))
        return key
    
    def _encrypt_data(self, data):
        """데이터 암호화"""
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            encrypted_data = self.cipher.encrypt(json_data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            print(f"암호화 실패: {e}")
            return None
    
    def _decrypt_data(self, encrypted_data):
        """데이터 복호화"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"복호화 실패: {e}")
            return None
    
    def save_auth_settings(self, login_id="", password="", remember_id=False, auto_login=False):
        """인증 설정 저장"""
        auth_data = {
            "login_id": login_id if remember_id or auto_login else "",
            "password": password if auto_login else "",
            "remember_id": remember_id,
            "auto_login": auto_login
        }
        
        encrypted_data = self._encrypt_data(auth_data)
        if encrypted_data:
            try:
                with open(self.auth_file, 'w') as f:
                    f.write(encrypted_data)
                return True
            except Exception as e:
                print(f"인증 설정 저장 실패: {e}")
                return False
        return False
    
    def load_auth_settings(self):
        """인증 설정 로드"""
        if not os.path.exists(self.auth_file):
            return {
                "login_id": "",
                "password": "",
                "remember_id": False,
                "auto_login": False
            }
        
        try:
            with open(self.auth_file, 'r') as f:
                encrypted_data = f.read()
            
            auth_data = self._decrypt_data(encrypted_data)
            if auth_data:
                return {
                    "login_id": auth_data.get("login_id", ""),
                    "password": auth_data.get("password", ""),
                    "remember_id": auth_data.get("remember_id", False),
                    "auto_login": auth_data.get("auto_login", False)
                }
        except Exception as e:
            print(f"인증 설정 로드 실패: {e}")
        
        # 기본값 반환
        return {
            "login_id": "",
            "password": "",
            "remember_id": False,
            "auto_login": False
        }
    
    def clear_auth_settings(self):
        """인증 설정 삭제"""
        try:
            if os.path.exists(self.auth_file):
                os.remove(self.auth_file)
            return True
        except Exception as e:
            print(f"인증 설정 삭제 실패: {e}")
            return False
    
    def attempt_auto_login(self):
        """자동 로그인 시도"""
        auth_settings = self.load_auth_settings()
        
        if auth_settings["auto_login"] and auth_settings["login_id"] and auth_settings["password"]:
            try:
                success, message, user_id = login(auth_settings["login_id"], auth_settings["password"])
                if success:
                    # 전역 변수에 사용자 ID 저장
                    import builtins
                    builtins.CURRENT_USER_ID = user_id
                    return True, "자동 로그인 성공", user_id
                else:
                    # 자동 로그인 실패 시 설정 초기화
                    self.save_auth_settings(
                        login_id=auth_settings["login_id"] if auth_settings["remember_id"] else "",
                        password="",
                        remember_id=auth_settings["remember_id"],
                        auto_login=False
                    )
                    return False, f"자동 로그인 실패: {message}", 0
            except Exception as e:
                return False, f"자동 로그인 중 오류 발생: {e}", 0
        
        return False, "자동 로그인 설정이 비활성화되어 있습니다.", 0
    
    def validate_credentials(self, login_id, password):
        """로그인 검증 (자동 로그인 패스 시에도 검증 수행)"""
        try:
            success, message, user_id = login(login_id, password)
            return success, message, user_id
        except Exception as e:
            return False, f"로그인 검증 중 오류 발생: {e}", 0
    
    def logout(self):
        """로그아웃 처리"""
        auth_settings = self.load_auth_settings()
        
        # 자동 로그인 비활성화
        self.save_auth_settings(
            login_id=auth_settings["login_id"] if auth_settings["remember_id"] else "",
            password="",
            remember_id=auth_settings["remember_id"],
            auto_login=False
        )
        
        # 전역 사용자 ID 초기화
        import builtins
        if hasattr(builtins, 'CURRENT_USER_ID'):
            delattr(builtins, 'CURRENT_USER_ID')
        
        return True