#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
import copy

class ConfigManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if ConfigManager._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            self.config_paths = [
                "config.json",
                "config/config.json",
                "../config/config.json",
                "bin/config.json",
            ]
            self.config_path = self._find_config_file()
            self.default_config = self._get_default_config()
            self.config = self._load_config()
            ConfigManager._instance = self

    def _find_config_file(self):
        for path in self.config_paths:
            if os.path.exists(path):
                return path
        return self.config_paths[0]

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 병합 로직: 기본 설정에 없는 키를 추가
                default_copy = copy.deepcopy(self.default_config)
                self._merge_configs(config, default_copy)

                # 이전 버전 호환성 처리
                self._ensure_compatibility(config)
                return config
            except Exception as e:
                print(f"설정 파일 로드 오류: {e}. 기본 설정으로 복원합니다.")
                return copy.deepcopy(self.default_config)
        else:
            print("config.json 파일이 없습니다. 기본 설정을 사용합니다.")
            return copy.deepcopy(self.default_config)
            
    def _merge_configs(self, loaded_config, default_config):
        """ 재귀적으로 설정을 병합. 로드된 설정에 없는 키를 기본 설정에서 추가 """
        for key, value in default_config.items():
            if key not in loaded_config:
                loaded_config[key] = value
            elif isinstance(value, dict) and isinstance(loaded_config.get(key), dict):
                self._merge_configs(loaded_config[key], value)

    def _ensure_compatibility(self, config):
        if "image" in config and "images" not in config:
            config["images"] = {
                "count": 1,
                "items": [{
                    "filename": "captured_image.jpg",
                    "x": config["image"]["x"], "y": config["image"]["y"],
                    "width": config["image"]["width"], "height": config["image"]["height"]
                }]
            }
            del config["image"]
        
        if "text" in config and "texts" not in config:
            config["texts"] = {
                "count": 1,
                "items": [{
                    "content": "텍스트", "x": config["text"]["x"], "y": config["text"]["y"],
                    "width": config["text"]["width"], "height": config["text"]["height"],
                    "font": "LAB디지털.ttf", "font_size": 16, "font_color": "#000000"
                }]
            }
            del config["text"]

    def get_config(self):
        return self.config

    def reload_config(self):
        """설정 파일에서 설정을 다시 로드합니다."""
        self.config = self._load_config()
        return self.config

    def save_config(self):
        try:
            directory = os.path.dirname(self.config_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"설정 파일 저장 오류: {e}")
            return False
            
    def _get_default_config(self):
        return {
            "app_name": "",
            "screen_size": { "width": 1920, "height": 1080 },
            "camera_size": { "width": 1920, "height": 1080 },
            "crop_area": { "width": 1920, "height": 1080, "x": 0, "y": 0 },
            "camera_count": { "number": 3, "font_size": 350, "font_color": "#ffffff" },
            "screen_order": [0, 1, 2, 3, 4, 5, 6],
            "frame": { "x": 0, "y": 0, "width": 1080, "height": 720 },
            "photo": {
                "filename": "captured_image.jpg", "x": 143, "y": 314,
                "width": 350, "height": 400, "background": ""
            },
            "qr_uploaded_image": {
                "filename": "qr_uploaded_image.jpg", "x": 143, "y": 314,
                "width": 350, "height": 400
            },
            "framed_photo": {
                "filename": "framed_photo.jpg", "x": 143, "y": 314,
                "width": 350, "height": 400
            },
            "images": { "count": 0, "items": [] },
            "texts": { "count": 0, "items": [] },
            "text_input": {
                "margin_top": 200, "margin_left": 0, "margin_right": 0, "spacing": 30,
                "count": 0, "items": [], "background": ""
            },
            "keyboard": {
                "x": 320, "y": 400, "width": 1280, "height": 400, "bg_color": "#1B2838",
                "border_color": "#00FFC2", "border_width": 2, "border_radius": 15, "padding": 10,
                "font_size": 28, "button_bg_color": "#2D3748", "button_text_color": "white",
                "button_pressed_color": "#4A5568", "button_radius": 10, "hangul_btn_color": "#4299E1",
                "shift_btn_color": "#3182CE", "backspace_btn_color": "#6ae517", "next_btn_color": "#48BB78",
                "special_btn_width": 100, "max_hangul": 100, "max_lowercase": 100, "max_uppercase": 100
            },
            "confirm_button": { "width": 200, "height": 80, "margin_bottom": 100, "font_size": 30 },
            "qr": {
                "preview_width": 600, "preview_height": 600, "x": 240, "y": 660, "background": ""
            },
            "splash": {
                "font": "", "phrase": "", "font_size": 0, "font_color": "black", "x": 0, "y": 0, "background": ""
            },
            "process": {
                "font": "", "phrase": "", "font_size": 0, "font_color": "black", "x": 0, "y": 0,
                "process_time": 3000, "background": ""
            },
            "complete": {
                "font": "", "phrase": "", "font_size": 0, "font_color": "black", "x": 0, "y": 0,
                "complete_time": 2000, "background": ""
            },
            "printer": {"print_mode": False, "panel_id": 1},
            "photo_frame": {"font_size": 32, "font_color": "green", "width": 800, "height": 600, "font": "", "background": ""},
            "card": {"orientation": "portrait"}
        }

def get_config_manager():
    return ConfigManager.get_instance() 