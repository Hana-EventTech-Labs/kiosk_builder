#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
import tkinter as tk
from tkinter import messagebox

class ConfigHandler:
    def __init__(self):
        self.config_paths = [
            "config.json",                    # 현재 폴더
            "config/config.json",             # config 폴더
            "../config/config.json",          # 상위 폴더의 config 폴더
            "bin/config.json",                # bin 폴더 (배포용)
        ]
        self.config_path = self.find_config_file()
        self.default_config = {
            "app_name": "Kiosk App",
            "screen_size": {
                "width": 1920,
                "height": 1080
            },
            "camera_size": {
                "width": 1920,
                "height": 1080
            },
            "crop_area": {
                "width": 1920,
                "height": 1080,
                "x": 0,
                "y": 0
            },
            "camera_count": {
                "number": 3,
                "font_size": 350,
                "font_color": "#ffffff"
            },
            "screen_order": [
                0,
                1,
                2,
                3,
                4,
                5
            ],
            "frame": {
                "x": 0,
                "y": 0,
                "width": 1080,
                "height": 720
            },
            "photo": {
                "exists": True,
                "filename": "captured_image.jpg",
                "x": 143,
                "y": 314,
                "width": 350,
                "height": 400,
                "background": ""
            },
            "qr_uploaded_image": {
                "exists": True,
                "filename": "qr_uploaded_image.jpg",
                "x": 143,
                "y": 314,
                "width": 350,
                "height": 400
            },
            "images": {
                "count": 0,
                "items": []
            },
            "texts": {
                "count": 0,
                "items": []
            },
            "text_input": {
                "margin_top": 200,
                "margin_left": 0,
                "margin_right": 0,
                "spacing": 30,
                "count": 0,
                "items": [],
                "background": ""
            },
            "keyboard": {
                "x": 320,
                "y": 400,
                "width": 1280,
                "height": 400,
                "bg_color": "#1B2838",
                "border_color": "#00FFC2",
                "border_width": 2,
                "border_radius": 15,
                "padding": 10,
                "font_size": 28,
                "button_bg_color": "#2D3748",
                "button_text_color": "white",
                "button_pressed_color": "#4A5568",
                "button_radius": 10,
                "hangul_btn_color": "#4299E1",
                "shift_btn_color": "#3182CE",
                "backspace_btn_color": "#6ae517",
                "next_btn_color": "#48BB78",
                "special_btn_width": 100,
                "max_hangul": 100,
                "max_lowercase": 100,
                "max_uppercase": 100
            },
            "confirm_button": {
                "width": 200,
                "height": 80,
                "margin_bottom": 100,
                "font_size": 30
            },
            "qr": {
                "preview_width": 600,
                "preview_height": 600,
                "x": 240,
                "y": 660,
                "background": ""
            },
            "splash": {
                "font": "",
                "phrase": "",
                "font_size": 0,
                "font_color": "black",
                "x": 0,
                "y": 0,
                "background": ""
            },
            "process": {
                "font": "",
                "phrase": "",
                "font_size": 0,
                "font_color": "black",
                "x": 0,
                "y": 0,
                "process_time": 3000,
                "background": ""
            },
            "complete": {
                "font": "",
                "phrase": "",
                "font_size": 0,
                "font_color": "black",
                "x": 0,
                "y": 0,
                "complete_time": 2000,
                "background": ""
            }
        }
        self.config = self.load_config()

    def find_config_file(self):
        """사용 가능한 설정 파일 찾기"""
        for path in self.config_paths:
            if os.path.exists(path):
                return path
        
        # 설정 파일이 없으면 기본 경로 반환
        return self.config_paths[0]

    def load_config(self):
        """기존 config.json 파일을 로드하거나 없으면 기본 설정을 반환"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # images, texts 구조가 새로운 형식인지 확인하고 변환
                if "image" in config and "images" not in config:
                    # 이전 버전에서 업그레이드
                    config["images"] = {
                        "count": 1,
                        "items": [
                            {
                                "filename": "captured_image.jpg",
                                "x": config["image"]["x"],
                                "y": config["image"]["y"],
                                "width": config["image"]["width"],
                                "height": config["image"]["height"]
                            }
                        ]
                    }
                    del config["image"]
                
                if "text" in config and "texts" not in config:
                    # 이전 버전에서 업그레이드
                    config["texts"] = {
                        "count": 1,
                        "items": [
                            {
                                "content": "텍스트",
                                "x": config["text"]["x"],
                                "y": config["text"]["y"],
                                "width": config["text"]["width"],
                                "height": config["text"]["height"],
                                "font": "LAB디지털.ttf",
                                "font_size": 16,
                                "font_color": "#000000"
                            }
                        ]
                    }
                    del config["text"]
                
                return config
            except Exception as e:
                print(f"설정 파일 로드 오류: {e}")
                self.show_error_and_exit(f"설정 파일 로드 오류: {e}")
        else:
            print("config.json 파일이 없습니다. 기본 설정을 사용합니다.")
            return self.default_config.copy()

    def show_error_and_exit(self, message):
        """오류 메시지를 표시하고 프로그램 종료"""
        root = tk.Tk()
        root.withdraw()  # 기본 창 숨기기
        messagebox.showerror("오류", message)
        sys.exit(1)

    def save_config(self, config_data):
        """설정을 JSON 파일로 저장"""
        try:
            # 폴더가 존재하는지 확인하고 필요하면 생성
            directory = os.path.dirname(self.config_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"설정 파일 저장 오류: {e}")
            return False