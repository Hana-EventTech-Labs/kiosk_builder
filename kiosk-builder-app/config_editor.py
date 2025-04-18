#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, 
                              QFormLayout, QLineEdit, QSpinBox, QColorDialog, QPushButton, 
                              QLabel, QListWidget, QMessageBox, QGroupBox, QScrollArea, QSizePolicy,
                              QFileDialog)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QIntValidator, QFont
import json
import copy
import os
import shutil
from config_handler import ConfigHandler

class NumberLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setValidator(QIntValidator())
    
    def setValue(self, value):
        self.setText(str(value))
    
    def value(self):
        try:
            return int(self.text())
        except ValueError:
            return 0

class ColorPickerButton(QPushButton):
    def __init__(self, color="#000000", parent=None):
        super().__init__(parent)
        self.color = color
        self.setMinimumSize(40, 25)
        self.update_color(color)
        self.clicked.connect(self.pick_color)

    def update_color(self, color):
        self.color = color
        self.setStyleSheet(f"background-color: {color}; min-width: 40px; min-height: 25px;")

    def pick_color(self):
        color = QColorDialog.getColor(QColor(self.color), self)
        if color.isValid():
            self.update_color(color.name())

class ConfigEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_handler = ConfigHandler()
        self.config = copy.deepcopy(self.config_handler.config)
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("슈퍼 키오스크 프로그램")
        self.setMinimumSize(800, 600)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 기본 설정 탭
        self.create_basic_tab()
        
        # 스플래쉬 탭
        self.create_splash_tab()
        
        # 촬영 탭
        self.create_capture_tab()
        
        # 키보드 탭
        self.create_keyboard_input_tab()
        
        # QR 코드 탭
        self.create_qr_tab()
        
        # 발급중 탭
        self.create_processing_tab()
        
        # 발급완료 탭
        self.create_complete_tab()
        
        # 화면 순서에 따라 탭 활성화/비활성화 설정
        self.update_tab_enabled_states()
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        
        # 배포용 생성 버튼 (미리보기 생성 대체)
        build_button = QPushButton("배포용 생성")
        build_button.clicked.connect(self.create_distribution)
        button_layout.addWidget(build_button)
        
        # 저장 버튼
        save_button = QPushButton("저장")
        save_button.clicked.connect(self.save_config)
        button_layout.addWidget(save_button)
                
        # 다시 로드 버튼
        reload_button = QPushButton("다시 로드")
        reload_button.clicked.connect(self.reload_config)
        button_layout.addWidget(reload_button)

    def create_basic_tab(self):
        basic_tab = QWidget()
        self.tab_widget.addTab(basic_tab, "기본 설정")
        
        # 스크롤 영역 추가
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # 스크롤 내용 위젯
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 단위 안내 레이블 추가
        unit_label = QLabel("모든 크기와 위치의 단위는 px(픽셀)입니다.")
        unit_label.setStyleSheet("color: #555;")
        content_layout.addWidget(unit_label)
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        content_layout.addLayout(form_layout)
        
        # 앱 이름
        self.app_name_edit = QLineEdit(self.config["app_name"])
        form_layout.addRow("앱 이름:", self.app_name_edit)
        
        # 화면 순서
        screen_order_group = QGroupBox("화면 순서")
        screen_order_layout = QVBoxLayout(screen_order_group)
        
        screen_order_label = QLabel("화면 순서 (쉼표로 구분):")
        screen_order_layout.addWidget(screen_order_label)
        
        self.screen_order_edit = QLineEdit(",".join(map(str, self.config["screen_order"])))
        self.screen_order_edit.textChanged.connect(self.on_screen_order_changed)
        screen_order_layout.addWidget(self.screen_order_edit)
        
        screen_order_info = QLabel("0: 스플래쉬, 1: 촬영, 2: 키보드, 3: QR코드, 4: 발급중, 5: 발급완료")
        screen_order_info.setStyleSheet("color: gray;")
        screen_order_layout.addWidget(screen_order_info)
        
        content_layout.addWidget(screen_order_group)
        
        # 모니터 크기
        screen_group = QGroupBox("모니터 크기")
        screen_layout = QFormLayout(screen_group)
        
        self.screen_width_edit = NumberLineEdit()
        self.screen_width_edit.setValue(self.config["screen_size"]["width"])
        screen_layout.addRow("너비:", self.screen_width_edit)
        
        self.screen_height_edit = NumberLineEdit()
        self.screen_height_edit.setValue(self.config["screen_size"]["height"])
        screen_layout.addRow("높이:", self.screen_height_edit)
        
        content_layout.addWidget(screen_group)
        
        # 카메라 해상도
        camera_group = QGroupBox("카메라 해상도")
        camera_layout = QFormLayout(camera_group)
        
        self.camera_width_edit = NumberLineEdit()
        self.camera_width_edit.setValue(self.config["camera_size"]["width"])
        camera_layout.addRow("너비:", self.camera_width_edit)
        
        self.camera_height_edit = NumberLineEdit()
        self.camera_height_edit.setValue(self.config["camera_size"]["height"])
        camera_layout.addRow("높이:", self.camera_height_edit)
        
        content_layout.addWidget(camera_group)
        
        # 실제 인쇄 영역은 촬영 화면 탭으로 이동
        
        # 이미지 설정 - 촬영 탭에서 이동
        images_group = QGroupBox("이미지 설정")
        images_layout = QVBoxLayout(images_group)
        
        # 이미지 개수 설정
        image_count_layout = QHBoxLayout()
        image_count_label = QLabel("이미지 개수:")
        self.image_count_spinbox = QSpinBox()
        self.image_count_spinbox.setRange(0, 10)
        self.image_count_spinbox.setValue(self.config["images"]["count"])
        self.image_count_spinbox.valueChanged.connect(self.update_image_items)
        image_count_layout.addWidget(image_count_label)
        image_count_layout.addWidget(self.image_count_spinbox)
        image_count_layout.addStretch()
        
        images_layout.addLayout(image_count_layout)
        
        # 이미지 항목 컨테이너
        self.image_items_container = QWidget()
        self.image_items_layout = QVBoxLayout(self.image_items_container)
        self.image_items_layout.setContentsMargins(0, 0, 0, 0)
        
        # 이미지 항목 필드 초기화
        self.image_item_fields = []
        self.update_image_items(self.config["images"]["count"])
        
        images_layout.addWidget(self.image_items_container)
        content_layout.addWidget(images_group)

        # 스트레치 추가
        content_layout.addStretch()
        
        # 스크롤 영역에 컨텐츠 설정
        scroll.setWidget(content_widget)
        
        # 탭에 스크롤 영역 추가
        layout = QVBoxLayout(basic_tab)
        layout.addWidget(scroll)

    def create_splash_tab(self):
        """스플래쉬 탭 생성 - splash 설정"""
        splash_tab = QWidget()
        self.tab_widget.addTab(splash_tab, "스플래쉬 화면")
        
        # 스크롤 영역 추가
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # 스크롤 내용 위젯
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 단위 안내 레이블 추가
        unit_label = QLabel("모든 크기와 위치의 단위는 px(픽셀)입니다.")
        unit_label.setStyleSheet("color: #555;")
        content_layout.addWidget(unit_label)
        
        # 스플래시 화면 설정
        splash_group = self.create_screen_group("스플래쉬 화면 설정", "splash")
        content_layout.addWidget(splash_group)
        
        # 스트레치 추가
        content_layout.addStretch()
        
        # 스크롤 영역에 컨텐츠 설정
        scroll.setWidget(content_widget)
        
        # 탭에 스크롤 영역 추가
        layout = QVBoxLayout(splash_tab)
        layout.addWidget(scroll)

    def create_capture_tab(self):
        """촬영 탭 생성 - frame, images 설정"""
        capture_tab = QWidget()
        self.tab_widget.addTab(capture_tab, "촬영 화면")
        
        # 스크롤 영역 추가
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # 스크롤 내용 위젯
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 단위 안내 레이블 추가
        unit_label = QLabel("모든 크기와 위치의 단위는 px(픽셀)입니다.")
        unit_label.setStyleSheet("color: #555;")
        content_layout.addWidget(unit_label)
        
        # 프레임 설정
        frame_group = self.create_position_size_group("카메라", "frame")
        content_layout.addWidget(frame_group)
        
        # 실제 인쇄 영역 추가
        crop_group = QGroupBox("실제 인쇄 영역(예시: 945, 1080, 487, 0)")
        crop_layout = QFormLayout(crop_group)
        
        self.crop_fields = {}
        
        for key in ["width", "height", "x", "y"]:
            # QSpinBox 대신 NumberLineEdit 사용
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["crop_area"][key])
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            crop_layout.addRow(f"{label_text}:", line_edit)
            self.crop_fields[key] = line_edit
        
        content_layout.addWidget(crop_group)
        
        # 사진 설정 추가 (photo)
        photo_group = QGroupBox("촬영 사진 설정")
        photo_layout = QFormLayout(photo_group)
        
        self.photo_fields = {}
        
        # 위치 및 크기
        for key in ["width", "height", "x", "y"]:
            # QSpinBox 대신 NumberLineEdit 사용
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["photo"][key])
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            photo_layout.addRow(f"{label_text}:", line_edit)
            self.photo_fields[key] = line_edit
        
        content_layout.addWidget(photo_group)
        
        # 카메라 카운트 설정
        camera_count_group = QGroupBox("카메라 카운트 설정")
        camera_count_layout = QFormLayout(camera_count_group)
        
        self.camera_count_fields = {}
        
        # 숫자 필드
        number_spin = QSpinBox()
        number_spin.setRange(0, 10)
        number_spin.setValue(self.config["camera_count"]["number"])
        camera_count_layout.addRow("카메라 카운트:", number_spin)
        self.camera_count_fields["number"] = number_spin
        
        # 폰트 크기
        font_size_spin = NumberLineEdit()
        font_size_spin.setValue(self.config["camera_count"]["font_size"])
        camera_count_layout.addRow("폰트 크기:", font_size_spin)
        self.camera_count_fields["font_size"] = font_size_spin
        
        # 폰트 색상
        font_color_button = ColorPickerButton(self.config["camera_count"]["font_color"])
        camera_count_layout.addRow("폰트 색상:", font_color_button)
        self.camera_count_fields["font_color"] = font_color_button
        
        content_layout.addWidget(camera_count_group)
        
        # 스트레치 추가
        content_layout.addStretch()
        
        # 스크롤 영역에 컨텐츠 설정
        scroll.setWidget(content_widget)
        
        # 탭에 스크롤 영역 추가
        layout = QVBoxLayout(capture_tab)
        layout.addWidget(scroll)

    def create_keyboard_input_tab(self):
        """키보드 탭 생성 - texts, text_input, keyboard, confirm_button 설정"""
        keyboard_tab = QWidget()
        self.tab_widget.addTab(keyboard_tab, "키보드 화면")
        
        # 스크롤 영역 추가
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # 스크롤 내용 위젯
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 단위 안내 레이블 추가
        unit_label = QLabel("모든 크기와 위치의 단위는 px(픽셀)입니다.")
        unit_label.setStyleSheet("color: #555;")
        content_layout.addWidget(unit_label)

        # 키보드 위치 및 크기
        position_group = QGroupBox("키보드 위치 및 크기")
        position_layout = QFormLayout(position_group)
        
        self.keyboard_position_fields = {}
        
        for key in ["width", "height", "x", "y"]:
            # QSpinBox 대신 NumberLineEdit 사용
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["keyboard"][key])
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            position_layout.addRow(f"{label_text}:", line_edit)
            self.keyboard_position_fields[key] = line_edit
        
        content_layout.addWidget(position_group)

        # 텍스트 설정 (텍스트 입력 설정 뒤에 배치)
        texts_group = QGroupBox("고정 텍스트 설정")
        texts_layout = QVBoxLayout(texts_group)
        
        # 텍스트 개수 설정
        text_count_layout = QHBoxLayout()
        text_count_label = QLabel("고정 텍스트 개수:")
        self.text_count_spinbox = QSpinBox()
        self.text_count_spinbox.setRange(0, 10)
        self.text_count_spinbox.setValue(self.config["texts"]["count"])
        self.text_count_spinbox.valueChanged.connect(self.update_text_items)
        text_count_layout.addWidget(text_count_label)
        text_count_layout.addWidget(self.text_count_spinbox)
        text_count_layout.addStretch()
        
        texts_layout.addLayout(text_count_layout)
        
        # 텍스트 항목 컨테이너
        self.text_items_container = QWidget()
        self.text_items_layout = QVBoxLayout(self.text_items_container)
        self.text_items_layout.setContentsMargins(0, 0, 0, 0)
        
        # 텍스트 항목 필드 초기화
        self.text_item_fields = []
        self.update_text_items(self.config["texts"]["count"])
        
        texts_layout.addWidget(self.text_items_container)
        content_layout.addWidget(texts_group)
        
        # 텍스트 입력 설정 (먼저 배치)
        text_input_group = QGroupBox("사용자 입력 필드 설정")
        text_input_layout = QVBoxLayout(text_input_group)
        
        # 텍스트 입력 기본 설정
        basic_settings_layout = QFormLayout()
        self.text_input_fields = {}
        
        # 공통 설정 필드 (각 항목별 설정이 아닌 전체 설정)
        settings_map = {
            "margin_top": "상단 여백",
            "margin_left": "왼쪽 여백",
            "margin_right": "오른쪽 여백",
            "spacing": "간격"
        }
        
        for key in ["margin_top", "margin_left", "margin_right", "spacing"]:
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["text_input"][key])
            basic_settings_layout.addRow(f"{settings_map[key]}:", line_edit)
            self.text_input_fields[key] = line_edit
            
        text_input_layout.addLayout(basic_settings_layout)
        
        # 텍스트 입력 개수 설정
        text_input_count_layout = QHBoxLayout()
        text_input_count_label = QLabel("사용자 입력 필드 개수:")
        self.text_input_count_spinbox = QSpinBox()
        self.text_input_count_spinbox.setRange(0, 10)
        self.text_input_count_spinbox.setValue(self.config["text_input"]["count"])
        self.text_input_count_spinbox.valueChanged.connect(self.update_text_input_items)
        text_input_count_layout.addWidget(text_input_count_label)
        text_input_count_layout.addWidget(self.text_input_count_spinbox)
        text_input_count_layout.addStretch()
        
        text_input_layout.addLayout(text_input_count_layout)
        
        # 텍스트 입력 항목 컨테이너
        self.text_input_items_container = QWidget()
        self.text_input_items_layout = QVBoxLayout(self.text_input_items_container)
        self.text_input_items_layout.setContentsMargins(0, 0, 0, 0)
        
        # 텍스트 입력 항목 필드 초기화
        self.text_input_item_fields = []
        self.update_text_input_items(self.config["text_input"]["count"])
        
        text_input_layout.addWidget(self.text_input_items_container)
        content_layout.addWidget(text_input_group)
        
        # 키보드 스타일
        style_group = QGroupBox("키보드 스타일")
        style_layout = QFormLayout(style_group)
        
        self.keyboard_style_fields = {}
        
        # 색상 필드
        color_keys = ["bg_color", "border_color", "button_bg_color", "button_text_color", 
                      "button_pressed_color", "hangul_btn_color", "shift_btn_color", 
                      "backspace_btn_color", "next_btn_color"]
        
        # 색상 필드 이름 매핑
        color_labels = {
            "bg_color": "배경 색상",
            "border_color": "테두리 색상",
            "button_bg_color": "버튼 배경 색상",
            "button_text_color": "버튼 텍스트 색상",
            "button_pressed_color": "버튼 누름 색상",
            "hangul_btn_color": "한글 버튼 색상",
            "shift_btn_color": "시프트 버튼 색상",
            "backspace_btn_color": "지우기 버튼 색상",
            "next_btn_color": "다음 버튼 색상"
        }
                      
        for key in color_keys:
            color_button = ColorPickerButton(self.config["keyboard"][key])
            style_layout.addRow(f"{color_labels[key]}:", color_button)
            self.keyboard_style_fields[key] = color_button
        
        # 숫자 필드
        number_keys = ["border_width", "border_radius", "padding", "font_size", 
                       "button_radius", "special_btn_width", "max_hangul", 
                       "max_lowercase", "max_uppercase"]
        
        # 숫자 필드 이름 매핑
        number_labels = {
            "border_width": "테두리 두께",
            "border_radius": "테두리 둥글기",
            "padding": "내부 여백",
            "font_size": "폰트 크기",
            "button_radius": "버튼 둥글기",
            "special_btn_width": "특수 버튼 너비",
            "max_hangul": "최대 한글 자수",
            "max_lowercase": "최대 소문자 자수",
            "max_uppercase": "최대 대문자 자수"
        }
                       
        for key in number_keys:
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["keyboard"][key])
            style_layout.addRow(f"{number_labels[key]}:", line_edit)
            self.keyboard_style_fields[key] = line_edit
        
        content_layout.addWidget(style_group)
        
        # 스트레치 추가
        content_layout.addStretch()
        
        # 스크롤 영역에 컨텐츠 설정
        scroll.setWidget(content_widget)
        
        # 탭에 스크롤 영역 추가
        layout = QVBoxLayout(keyboard_tab)
        layout.addWidget(scroll)

    def create_qr_tab(self):
        """QR 코드 탭 생성 - qr 설정"""
        qr_tab = QWidget()
        self.tab_widget.addTab(qr_tab, "QR코드 화면")
        
        # 스크롤 영역 추가
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # 스크롤 내용 위젯
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 단위 안내 레이블 추가
        unit_label = QLabel("모든 크기와 위치의 단위는 px(픽셀)입니다.")
        unit_label.setStyleSheet("color: #555;")
        content_layout.addWidget(unit_label)
        
        # QR 코드 설정 그룹
        qr_group = QGroupBox("QR 코드 설정")
        qr_layout = QFormLayout(qr_group)
        
        self.qr_fields = {}
        
        # 미리보기 영역 위치 및 크기 설정
        preview_width_edit = NumberLineEdit()
        preview_width_edit.setValue(self.config["qr"]["preview_width"])
        qr_layout.addRow("미리보기 너비:", preview_width_edit)
        self.qr_fields["preview_width"] = preview_width_edit
        
        preview_height_edit = NumberLineEdit()
        preview_height_edit.setValue(self.config["qr"]["preview_height"])
        qr_layout.addRow("미리보기 높이:", preview_height_edit)
        self.qr_fields["preview_height"] = preview_height_edit
        
        x_edit = NumberLineEdit()
        x_edit.setValue(self.config["qr"]["x"])
        qr_layout.addRow("X 위치:", x_edit)
        self.qr_fields["x"] = x_edit
        
        y_edit = NumberLineEdit()
        y_edit.setValue(self.config["qr"]["y"])
        qr_layout.addRow("Y 위치:", y_edit)
        self.qr_fields["y"] = y_edit
        
        content_layout.addWidget(qr_group)
        
        # 업로드 이미지 설정 그룹박스 추가
        qr_uploaded_group = QGroupBox("업로드 이미지 설정")
        qr_uploaded_layout = QFormLayout(qr_uploaded_group)
        
        self.qr_uploaded_fields = {}
        
        # 이미지 위치 및 크기 설정
        for key in ["width", "height", "x", "y"]:
            # QSpinBox 대신 NumberLineEdit 사용
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config["qr_uploaded_image"][key])
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            qr_uploaded_layout.addRow(f"{label_text}:", line_edit)
            self.qr_uploaded_fields[key] = line_edit
        
        content_layout.addWidget(qr_uploaded_group)
        
        # 스트레치 추가
        content_layout.addStretch()
        
        # 스크롤 영역에 컨텐츠 설정
        scroll.setWidget(content_widget)
        
        # 탭에 스크롤 영역 추가
        layout = QVBoxLayout(qr_tab)
        layout.addWidget(scroll)

    def create_processing_tab(self):
        """발급중 탭 생성 - process 설정"""
        processing_tab = QWidget()
        self.tab_widget.addTab(processing_tab, "발급중 화면")
        
        # 스크롤 영역 추가
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # 스크롤 내용 위젯
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 단위 안내 레이블 추가
        unit_label = QLabel("모든 크기와 위치의 단위는 px(픽셀)입니다.")
        unit_label.setStyleSheet("color: #555;")
        content_layout.addWidget(unit_label)
        
        # 프로세스 화면 설정
        process_group = self.create_screen_group("발급중 화면 설정", "process", True)
        content_layout.addWidget(process_group)
        
        # 스트레치 추가
        content_layout.addStretch()
        
        # 스크롤 영역에 컨텐츠 설정
        scroll.setWidget(content_widget)
        
        # 탭에 스크롤 영역 추가
        layout = QVBoxLayout(processing_tab)
        layout.addWidget(scroll)

    def create_complete_tab(self):
        """발급완료 탭 생성 - complete 설정"""
        complete_tab = QWidget()
        self.tab_widget.addTab(complete_tab, "발급완료 화면")
        
        # 스크롤 영역 추가
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # 스크롤 내용 위젯
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 단위 안내 레이블 추가
        unit_label = QLabel("모든 크기와 위치의 단위는 px(픽셀)입니다.")
        unit_label.setStyleSheet("color: #555;")
        content_layout.addWidget(unit_label)
        
        # 완료 화면 설정
        complete_group = self.create_screen_group("발급완료 화면 설정", "complete", True)
        content_layout.addWidget(complete_group)
        
        # 스트레치 추가
        content_layout.addStretch()
        
        # 스크롤 영역에 컨텐츠 설정
        scroll.setWidget(content_widget)
        
        # 탭에 스크롤 영역 추가
        layout = QVBoxLayout(complete_tab)
        layout.addWidget(scroll)

    def create_position_size_group(self, title, config_key):
        group = QGroupBox(f"{title} 위치 및 크기")
        layout = QFormLayout(group)
        
        fields = {}
        setattr(self, f"{config_key}_fields", fields)
        
        for key in ["width", "height", "x", "y"]:
            # QSpinBox 대신 NumberLineEdit 사용
            line_edit = NumberLineEdit()
            line_edit.setValue(self.config[config_key][key])
            label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
            layout.addRow(f"{label_text}:", line_edit)
            fields[key] = line_edit
        
        return group

    def create_screen_group(self, title, config_key, has_time=False):
        group = QGroupBox(title)
        layout = QFormLayout(group)
        
        fields = {}
        setattr(self, f"{config_key}_fields", fields)
        
        # 기본 필드
        # 폰트 선택 레이아웃 추가
        font_layout = QHBoxLayout()
        font_edit = QLineEdit(self.config[config_key]["font"])
        font_layout.addWidget(font_edit, 1)  # 1은 stretch factor로, 남은 공간을 차지하도록 함
        fields["font"] = font_edit
        
        # 폰트 파일 선택 버튼 추가
        browse_button = QPushButton("찾기...")
        browse_button.clicked.connect(lambda checked, edit=font_edit: self.browse_font_file(edit))
        font_layout.addWidget(browse_button)
        
        layout.addRow("폰트:", font_layout)
        
        phrase_edit = QLineEdit(self.config[config_key]["phrase"])
        layout.addRow("문구:", phrase_edit)
        fields["phrase"] = phrase_edit
        
        font_size_edit = NumberLineEdit()
        font_size_edit.setValue(self.config[config_key]["font_size"])
        layout.addRow("폰트 크기:", font_size_edit)
        fields["font_size"] = font_size_edit
        
        font_color_button = ColorPickerButton(self.config[config_key]["font_color"])
        layout.addRow("폰트 색상:", font_color_button)
        fields["font_color"] = font_color_button
        
        x_edit = NumberLineEdit()
        x_edit.setValue(self.config[config_key]["x"])
        layout.addRow("X 위치:", x_edit)
        fields["x"] = x_edit
        
        y_edit = NumberLineEdit()
        y_edit.setValue(self.config[config_key]["y"])
        layout.addRow("Y 위치:", y_edit)
        fields["y"] = y_edit
        
        # 시간 필드 (필요한 경우)
        if has_time:
            time_key = f"{config_key}_time"
            time_edit = NumberLineEdit()
            time_edit.setValue(self.config[config_key][time_key])
            layout.addRow(f"시간 (ms):", time_edit)
            fields[time_key] = time_edit
        
        return group

    def browse_font_file(self, line_edit):
        """폰트 파일 선택 다이얼로그를 띄우고 선택된 파일명을 입력란에 설정합니다."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
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
                    self, 
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
                            self,
                            "파일 복사 완료",
                            f"폰트 파일이 resources/font 폴더로 복사되었습니다."
                        )
                        
                        # 파일명만 설정
                        line_edit.setText(file_name)
                    except Exception as e:
                        # 복사 실패 시 오류 메시지
                        QMessageBox.critical(
                            self,
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
                        self, 
                        "파일 경로", 
                        f"파일명만 설정되었습니다. 실제 사용을 위해서는 해당 폰트 파일을 resources/font 폴더로 수동으로 복사해야 합니다."
                    )
            else:
                # 이미 리소스 폴더 내부에 있는 경우 파일명만 사용
                file_name = os.path.basename(file_path)
                line_edit.setText(file_name)

    def save_config(self):
        # 텍스트 항목의 폰트 파일 존재 여부 확인
        missing_fonts = []
        
        # 텍스트 항목 폰트 확인
        for i, fields in enumerate(self.text_item_fields):
            font_file = fields["font"].text()
            # 폰트가 빈 문자열이면 확인 건너뛰기
            if font_file and font_file.strip():  # 빈 문자열이 아니면 체크
                font_path = os.path.join("resources/font", font_file)
                if not os.path.exists(font_path):
                    missing_fonts.append(f"텍스트 {i+1}: {font_file}")
        
        # 스플래시, 프로세스, 완료 화면의 폰트 확인
        for section in ["splash", "process", "complete"]:
            fields = getattr(self, f"{section}_fields")
            font_file = fields["font"].text()
            # 폰트가 빈 문자열이면 확인 건너뛰기
            if font_file and font_file.strip():  # 빈 문자열이 아니면 체크
                font_path = os.path.join("resources/font", font_file)
                if not os.path.exists(font_path):
                    missing_fonts.append(f"{section} 화면: {font_file}")
        
        # 누락된 폰트가 있으면 경고 메시지 표시
        if missing_fonts:
            error_msg = "다음 폰트 파일을 찾을 수 없습니다:\n\n" + "\n".join(missing_fonts)
            QMessageBox.warning(self, "폰트 파일 누락", error_msg)
            return
        
        
        # UI의 값들을 self.config에 업데이트
        if not self.update_config_from_ui():
            QMessageBox.warning(self, "입력 오류", "입력 값에 오류가 있어 저장할 수 없습니다.")
            return
        
        # 설정 저장
        if self.config_handler.save_config(self.config):
            QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다.")
        else:
            QMessageBox.warning(self, "저장 실패", "설정 저장 중 오류가 발생했습니다.")

    def create_distribution(self):
        """배포용 파일 생성 및 복사"""
        # 배포용 파일 처리
        try:
            import subprocess
            import sys
            
            # 앱 이름으로 폴더 생성
            app_name = self.app_name_edit.text()
            if not app_name:
                app_name = "Kiosk_App"  # 기본 이름
            
            # 특수문자 및 공백 처리
            app_folder_name = app_name.replace(" ", "_").replace(".", "_")
            
            # 실행 파일 경로 확인 (PyInstaller)
            if getattr(sys, 'frozen', False):
                # PyInstaller로 패키징된 경우
                base_path = sys._MEIPASS
                parent_dir = os.path.dirname(sys.executable)
            else:
                # 일반 Python 스크립트로 실행된 경우
                base_path = os.getcwd()
                parent_dir = os.getcwd()
            
            # 앱 폴더 경로
            target_dir = os.path.join(parent_dir, app_folder_name)
            
            # "저장" 버튼과 동일한 기능 수행하지만, 외부 config.json에는 저장하지 않음
            # 설정 업데이트 (모든 UI 항목의 값들을 self.config에 업데이트)
            self.update_config_from_ui()
            
            # 폴더가 이미 존재하는지 확인하고 사용자에게 확인
            if os.path.exists(target_dir):
                reply = QMessageBox.question(
                    self, 
                    "폴더 이미 존재", 
                    f"'{app_folder_name}' 폴더가 이미 존재합니다. 내용을 덮어쓰시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
                
                # 기존 폴더 내용 삭제
                for item in os.listdir(target_dir):
                    item_path = os.path.join(target_dir, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
            else:
                # 폴더 생성
                os.makedirs(target_dir, exist_ok=True)
            
            # 배포 폴더 내에 config.json 파일 생성
            target_config_path = os.path.join(target_dir, "config.json")
            with open(target_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            
            # resources 폴더 안에 필요한 하위 폴더 확인 및 생성
            resources_path = os.path.join(base_path, "resources")
            font_path = os.path.join(resources_path, "font")
            background_path = os.path.join(resources_path, "background")
            
            # 폴더 생성 여부를 저장할 변수
            created_dirs = []
            
            # font 폴더가 없으면 생성
            if not os.path.exists(font_path):
                os.makedirs(font_path, exist_ok=True)
                created_dirs.append("resources/font")
                print(f"resources/font 폴더를 생성했습니다: {font_path}")
            
            # background 폴더가 없으면 생성
            if not os.path.exists(background_path):
                os.makedirs(background_path, exist_ok=True)
                created_dirs.append("resources/background")
                print(f"resources/background 폴더를 생성했습니다: {background_path}")
            
            # json-reader 실행 파일 찾기 및 복사
            super_kiosk_program_exe = os.path.join(parent_dir, "super-kiosk-program.exe")
            super_kiosk_program_copied = False
            
            if os.path.exists(super_kiosk_program_exe):
                # super-kiosk-program.exe 파일을 대상 폴더로 복사
                shutil.copy2(super_kiosk_program_exe, os.path.join(target_dir, "super-kiosk-program.exe"))
                super_kiosk_program_copied = True
            else:
                # 다른 경로에서 super-kiosk-program.exe 찾기
                possible_paths = [
                    os.path.join(parent_dir, "dist", "super-kiosk-program.exe"),
                    os.path.join(parent_dir, "build", "super-kiosk-program.exe"),
                    os.path.join(os.path.dirname(parent_dir), "super-kiosk-program.exe")
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        shutil.copy2(path, os.path.join(target_dir, "super-kiosk-program.exe"))
                        super_kiosk_program_copied = True
                        break
            
            # 필요한 파일들 목록
            required_files = [
                {"name": "kiosk_preview.exe", "source": os.path.join(base_path, "kiosk_preview.exe")},
                {"name": "kiosk_print.exe", "source": os.path.join(base_path, "kiosk_print.exe")}
            ]
            
            # 폴더 목록
            required_folders = [
                {"name": "resources", "source": os.path.join(base_path, "resources")}
            ]
            
            # 파일들을 대상 폴더로 복사
            copied_files = []
            missing_files = []
            
            for file_info in required_files:
                source_path = file_info["source"]
                target_path = os.path.join(target_dir, file_info["name"])
                
                if os.path.exists(source_path):
                    shutil.copy2(source_path, target_path)
                    copied_files.append(file_info["name"])
                else:
                    missing_files.append(file_info["name"])
            
            
            # 폴더들을 대상 폴더로 복사
            copied_folders = []
            missing_folders = []
            
            for folder_info in required_folders:
                source_path = folder_info["source"]
                target_path = os.path.join(target_dir, folder_info["name"])
                
                if os.path.exists(source_path):
                    # 대상 폴더가 존재하면 삭제 후 복사
                    if os.path.exists(target_path):
                        shutil.rmtree(target_path)
                    
                    shutil.copytree(source_path, target_path)
                    copied_folders.append(folder_info["name"])
                else:
                    missing_folders.append(folder_info["name"])
            
            # 결과 메시지 구성
            result_message = f"배포 폴더 '{app_folder_name}'이(가) 생성되었습니다.\n\n"
            
            # 폴더 생성 메시지 추가
            if created_dirs:
                result_message += "다음 폴더를 자동으로 생성했습니다:\n- " + "\n- ".join(created_dirs) + "\n\n"
            
            if copied_files or copied_folders or super_kiosk_program_copied:
                result_message += "다음 항목이 성공적으로 복사되었습니다:\n\n"
                
                if super_kiosk_program_copied:
                    result_message += "실행 파일:\n- super-kiosk-program.exe\n\n"
                
                if copied_files:
                    result_message += "파일:\n- " + "\n- ".join(copied_files) + "\n\n"
                
                if copied_folders:
                    result_message += "폴더:\n- " + "\n- ".join(copied_folders) + "\n\n"
            
            if not super_kiosk_program_copied:
                result_message += "super-kiosk-program.exe 파일을 찾을 수 없습니다. 수동으로 복사해야 합니다.\n\n"
            
            if missing_files or missing_folders:
                result_message += "다음 항목을 찾을 수 없어 복사하지 못했습니다:\n\n"
                
                if missing_files:
                    result_message += "파일:\n- " + "\n- ".join(missing_files) + "\n\n"
                
                if missing_folders:
                    result_message += "폴더:\n- " + "\n- ".join(missing_folders) + "\n\n"
            
            # 사용자에게 결과 알림
            if copied_files or copied_folders or super_kiosk_program_copied:
                QMessageBox.information(
                    self, 
                    "배포용 파일 생성 완료", 
                    result_message
                )
            else:
                QMessageBox.warning(
                    self, 
                    "배포용 파일 생성 실패", 
                    result_message + "필요한 파일을 찾을 수 없습니다."
                )
                
        except Exception as e:
            QMessageBox.warning(self, "오류", f"배포용 파일 처리 중 오류가 발생했습니다: {str(e)}")

    def reload_config(self):
        """설정을 다시 로드하고 UI를 업데이트합니다."""
        self.config = copy.deepcopy(self.config_handler.load_config())
        self.update_ui_from_config()
        QMessageBox.information(self, "설정 로드", "설정이 다시 로드되었습니다.")
    
    def update_ui_from_config(self):
        """현재 설정에 따라 UI 요소들을 업데이트합니다."""
        # 기본 설정 업데이트
        self.app_name_edit.setText(self.config["app_name"])
        self.screen_width_edit.setValue(self.config["screen_size"]["width"])
        self.screen_height_edit.setValue(self.config["screen_size"]["height"])
        self.camera_width_edit.setValue(self.config["camera_size"]["width"])
        self.camera_height_edit.setValue(self.config["camera_size"]["height"])
        
        # 크롭 영역 설정 업데이트
        for key, widget in self.crop_fields.items():
            widget.setValue(self.config["crop_area"][key])
        
        # 카메라 카운트 설정 업데이트
        self.camera_count_fields["number"].setValue(self.config["camera_count"]["number"])
        self.camera_count_fields["font_size"].setValue(self.config["camera_count"]["font_size"])
        self.camera_count_fields["font_color"].update_color(self.config["camera_count"]["font_color"])
        
        # QR 코드 설정 업데이트
        self.qr_fields["preview_width"].setValue(self.config["qr"]["preview_width"])
        self.qr_fields["preview_height"].setValue(self.config["qr"]["preview_height"])
        self.qr_fields["x"].setValue(self.config["qr"]["x"])
        self.qr_fields["y"].setValue(self.config["qr"]["y"])
        
        # QR 업로드 이미지 설정 업데이트
        for key in ["x", "y", "width", "height"]:
            self.qr_uploaded_fields[key].setValue(self.config["qr_uploaded_image"][key])
        
        # screen_order 업데이트 (textChanged 시그널이 연결되어 있으므로 마지막에 업데이트)
        screen_order_text = ",".join(map(str, self.config["screen_order"]))
        if self.screen_order_edit.text() != screen_order_text:
            self.screen_order_edit.setText(screen_order_text)
            # 탭 활성화 상태 업데이트
            self.update_tab_enabled_states()
        
        # 프레임 설정 업데이트
        for key, widget in self.frame_fields.items():
            widget.setValue(self.config["frame"][key])
        
        # 촬영 사진 설정 업데이트
        for key in ["x", "y", "width", "height"]:
            self.photo_fields[key].setValue(self.config["photo"][key])
        
        # 이미지 설정 업데이트
        if self.image_count_spinbox.value() != self.config["images"]["count"]:
            self.image_count_spinbox.setValue(self.config["images"]["count"])
        else:
            self.update_image_items(self.config["images"]["count"])
            
        # 텍스트 설정 업데이트
        if self.text_count_spinbox.value() != self.config["texts"]["count"]:
            self.text_count_spinbox.setValue(self.config["texts"]["count"])
        else:
            self.update_text_items(self.config["texts"]["count"])
            
        # 이미지 항목 업데이트
        for i, fields in enumerate(self.image_item_fields):
            if i < len(self.config["images"]["items"]):
                item = self.config["images"]["items"][i]
                fields["filename"].setText(item["filename"])
                fields["x"].setValue(item["x"])
                fields["y"].setValue(item["y"])
                fields["width"].setValue(item["width"])
                fields["height"].setValue(item["height"])
        
        # 텍스트 항목 업데이트
        for i, fields in enumerate(self.text_item_fields):
            if i < len(self.config["texts"]["items"]):
                item = self.config["texts"]["items"][i]
                fields["content"].setText(item["content"])
                fields["x"].setValue(item["x"])
                fields["y"].setValue(item["y"])
                fields["width"].setValue(item["width"])
                fields["height"].setValue(item["height"])
                fields["font"].setText(item["font"])
                fields["font_size"].setValue(item["font_size"])
                fields["font_color"].update_color(item["font_color"])
        
        # 텍스트 입력 설정 업데이트
        for key, widget in self.text_input_fields.items():
            if key != "count":  # count는 spinbox에서 별도로 처리
                widget.setValue(self.config["text_input"][key])
        
        # 텍스트 입력 개수 업데이트
        if self.text_input_count_spinbox.value() != self.config["text_input"]["count"]:
            self.text_input_count_spinbox.setValue(self.config["text_input"]["count"])
        else:
            self.update_text_input_items(self.config["text_input"]["count"])
        
        # 텍스트 입력 항목 업데이트
        for i, fields in enumerate(self.text_input_item_fields):
            if i < len(self.config["text_input"]["items"]):
                item = self.config["text_input"]["items"][i]
                fields["label"].setText(item.get("label", ""))
                fields["placeholder"].setText(item.get("placeholder", ""))
                fields["x"].setValue(item.get("x", 0))
                fields["y"].setValue(item.get("y", 0))
                fields["width"].setValue(item.get("width", 800))
                fields["height"].setValue(item.get("height", 80))
                fields["font_size"].setValue(item.get("font_size", 36))
                # 출력용 폰트 설정 불러오기
                fields["output_font"].setText(item.get("output_font", ""))
                fields["output_font_size"].setValue(item.get("output_font_size", 16))
                fields["output_font_color"].update_color(item.get("output_font_color", "#000000"))
        
        # 키보드 설정 업데이트
        # 위치 및 크기
        for key, widget in self.keyboard_position_fields.items():
            widget.setValue(self.config["keyboard"][key])
        
        # 스타일
        for key, widget in self.keyboard_style_fields.items():
            if isinstance(widget, ColorPickerButton):
                widget.update_color(self.config["keyboard"][key])
            else:
                widget.setValue(self.config["keyboard"][key])
        
        # 화면 설정 업데이트
        for section in ["splash", "process", "complete"]:
            fields = getattr(self, f"{section}_fields")
            for key, widget in fields.items():
                if isinstance(widget, ColorPickerButton):
                    widget.update_color(self.config[section][key])
                else:
                    if isinstance(widget, QSpinBox) or isinstance(widget, NumberLineEdit):
                        widget.setValue(self.config[section][key])
                    else:
                        widget.setText(self.config[section][key])
    
    def load_config(self):
        """이전 버전과의 호환성을 위해 남겨둔 메소드"""
        self.reload_config() 

    def on_screen_order_changed(self):
        """화면 순서가 변경되었을 때 호출되는 메소드"""
        try:
            # 입력값 파싱 시도
            screen_order = [int(x.strip()) for x in self.screen_order_edit.text().split(",")]
            # 유효한 화면 순서인지 확인
            for order in screen_order:
                if order < 0 or order > 5:
                    return  # 유효하지 않은 값이 있으면 업데이트하지 않음
                    
            # 화면 순서에 따라 탭 활성화/비활성화 설정
            self.update_tab_enabled_states()
        except ValueError:
            # 숫자로 변환할 수 없는 값이 있으면 무시
            pass
    
    def update_tab_enabled_states(self):
        """현재 screen_order 설정에 따라 탭 활성화/비활성화 상태를 업데이트"""
        try:
            # 입력값 파싱
            screen_order = [int(x.strip()) for x in self.screen_order_edit.text().split(",")]
            
            # config_editor.py의 탭 인덱스 순서:
            # 인덱스 0: 기본 설정 탭 (항상 표시)
            # 인덱스 1: 스플래쉬 탭 (화면 타입 0)
            # 인덱스 2: 촬영 탭 (화면 타입 1)
            # 인덱스 3: 키보드 탭 (화면 타입 2) 
            # 인덱스 4: QR코드 탭 (화면 타입 3)
            # 인덱스 5: 발급중 탭 (화면 타입 4)
            # 인덱스 6: 발급완료 탭 (화면 타입 5)
            
            tab_indices = {
                0: 1,  # 화면 타입 0 (스플래쉬) -> 탭 인덱스 1
                1: 2,  # 화면 타입 1 (촬영) -> 탭 인덱스 2
                2: 3,  # 화면 타입 2 (키보드) -> 탭 인덱스 3
                3: 4,  # 화면 타입 3 (QR코드) -> 탭 인덱스 4
                4: 5,  # 화면 타입 4 (발급중) -> 탭 인덱스 5
                5: 6   # 화면 타입 5 (발급완료) -> 탭 인덱스 6
            }
            
            # 모든 화면 탭 비활성화
            for i in range(1, 7):  # 1부터 6까지 (기본 설정 탭 제외)
                self.tab_widget.setTabEnabled(i, False)
            
            # screen_order에 있는 탭만 활성화
            for screen_type in screen_order:
                if 0 <= screen_type <= 5:  # 유효한 화면 타입인지 확인
                    tab_index = tab_indices.get(screen_type)
                    if tab_index is not None:
                        self.tab_widget.setTabEnabled(tab_index, True)
                        
            # 탭 활성화 상태에 따라 시각적 표시 업데이트
            for i in range(1, 7):
                tab_text = self.tab_widget.tabText(i)
                if not self.tab_widget.isTabEnabled(i):
                    if not tab_text.startswith("[비활성] "):
                        self.tab_widget.setTabText(i, f"[비활성] {tab_text}")
                else:
                    if tab_text.startswith("[비활성] "):
                        self.tab_widget.setTabText(i, tab_text[6:])
                        
        except ValueError:
            # 숫자로 변환할 수 없는 값이 있으면 모든 탭 활성화
            for i in range(1, 7):
                self.tab_widget.setTabEnabled(i, True)
                tab_text = self.tab_widget.tabText(i)
                if tab_text.startswith("[비활성] "):
                    self.tab_widget.setTabText(i, tab_text[6:])

    def update_image_items(self, count):
        """이미지 항목 UI 업데이트"""
        # 이전 이미지 개수 확인
        prev_count = len(self.image_item_fields)
        
        # 기존 이미지 데이터 저장
        prev_image_data = []
        for i, fields in enumerate(self.image_item_fields):
            prev_data = {
                "filename": fields["filename"].text(),
                "x": fields["x"].value(),
                "y": fields["y"].value(),
                "width": fields["width"].value(),
                "height": fields["height"].value()
            }
            prev_image_data.append(prev_data)
        
        # 기존 위젯 제거
        for i in reversed(range(self.image_items_layout.count())):
            item = self.image_items_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # 이미지 항목 필드 초기화
        self.image_item_fields = []
        
        # 새 항목 추가
        for i in range(count):
            # 기본값 설정
            item_data = {
                "filename": "file_name.jpg",
                "x": 0,
                "y": 0,
                "width": 300,
                "height": 300
            }
            
            # 기존 이미지 데이터 유지
            if i < prev_count:
                item_data = prev_image_data[i]
            # 저장된 config에서 데이터 가져오기
            elif i < len(self.config["images"]["items"]):
                item_data = self.config["images"]["items"][i]
            
            # 항목 그룹 생성
            item_group = QGroupBox(f"이미지 {i+1}")
            item_layout = QFormLayout(item_group)
            
            # 항목 필드 생성
            item_fields = {}
            
            # 파일명 입력란과 파일 선택 버튼을 담을 레이아웃
            filename_layout = QHBoxLayout()
            
            # 파일명 입력란
            filename_edit = QLineEdit(item_data["filename"])
            filename_layout.addWidget(filename_edit, 1)  # 1은 stretch factor로, 남은 공간을 차지하도록 함
            item_fields["filename"] = filename_edit
            
            # 파일 선택 버튼
            browse_button = QPushButton("찾기...")
            browse_button.clicked.connect(lambda checked, edit=filename_edit: self.browse_image_file(edit))
            filename_layout.addWidget(browse_button)
            
            item_layout.addRow("파일명:", filename_layout)
            
            # 위치 및 크기
            for key in ["width", "height", "x", "y"]:
                # QSpinBox 대신 NumberLineEdit 사용
                line_edit = NumberLineEdit()
                line_edit.setValue(item_data.get(key, 0))
                label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
                item_layout.addRow(f"{label_text}:", line_edit)
                item_fields[key] = line_edit
            
            self.image_items_layout.addWidget(item_group)
            self.image_item_fields.append(item_fields)
        
        # UI 업데이트
        self.image_items_container.updateGeometry()
        
    def browse_image_file(self, line_edit):
        """이미지 파일 선택 다이얼로그를 띄우고 선택된 파일명을 입력란에 설정합니다."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
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
                    self, 
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
                            self,
                            "파일 복사 완료",
                            f"파일이 resources 폴더로 복사되었습니다."
                        )
                        
                        # 파일명만 설정
                        line_edit.setText(file_name)
                    except Exception as e:
                        # 복사 실패 시 오류 메시지
                        QMessageBox.critical(
                            self,
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
                        self, 
                        "파일 경로", 
                        f"파일명만 설정되었습니다. 실제 사용을 위해서는 해당 파일을 resources 폴더로 수동으로 복사해야 합니다."
                    )
            else:
                # 이미 리소스 폴더 내부에 있는 경우 상대 경로 사용
                rel_path = os.path.relpath(file_path, resources_img_path)
                line_edit.setText(rel_path)

    def update_text_items(self, count):
        """텍스트 항목 UI 업데이트"""
        # 기존 위젯 제거
        for i in reversed(range(self.text_items_layout.count())):
            item = self.text_items_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # 텍스트 항목 필드 초기화
        self.text_item_fields = []
        
        # 새 항목 추가
        for i in range(count):
            # 기본값 설정
            item_data = {
                "content": "텍스트",
                "x": 0,
                "y": 0,
                "width": 300,
                "height": 100,
                "font": "LAB디지털.ttf",
                "font_size": 16,
                "font_color": "#000000"
            }
            
            # 기존 데이터가 있으면 사용
            if i < len(self.config["texts"]["items"]):
                item_data = self.config["texts"]["items"][i]
            
            # 항목 그룹 생성
            item_group = QGroupBox(f"텍스트 {i+1}")
            item_layout = QFormLayout(item_group)
            
            # 항목 필드 생성
            item_fields = {}
            
            # 내용
            content_edit = QLineEdit(item_data["content"])
            item_layout.addRow("문구:", content_edit)
            item_fields["content"] = content_edit
            
            # 위치 및 크기
            for key in ["width", "height", "x", "y"]:
                # QSpinBox 대신 NumberLineEdit 사용
                line_edit = NumberLineEdit()
                line_edit.setValue(item_data[key])
                label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
                item_layout.addRow(f"{label_text}:", line_edit)
                item_fields[key] = line_edit
            
            # 폰트 선택 레이아웃
            font_layout = QHBoxLayout()
            font_edit = QLineEdit(item_data["font"])
            font_layout.addWidget(font_edit, 1)  # 1은 stretch factor로, 남은 공간을 차지하도록 함
            item_fields["font"] = font_edit
            
            # 폰트 파일 선택 버튼
            browse_button = QPushButton("찾기...")
            browse_button.clicked.connect(lambda checked, edit=font_edit: self.browse_font_file(edit))
            font_layout.addWidget(browse_button)
            
            item_layout.addRow("폰트:", font_layout)
            
            # 폰트 크기
            font_size_spin = NumberLineEdit()
            font_size_spin.setValue(item_data["font_size"])
            item_layout.addRow("폰트 크기:", font_size_spin)
            item_fields["font_size"] = font_size_spin
            
            # 폰트 색상
            font_color_button = ColorPickerButton(item_data["font_color"])
            item_layout.addRow("폰트 색상:", font_color_button)
            item_fields["font_color"] = font_color_button
            
            self.text_items_layout.addWidget(item_group)
            self.text_item_fields.append(item_fields)
        
        # UI 업데이트
        self.text_items_container.updateGeometry()

    def update_text_input_items(self, count):
        """텍스트 입력 항목 UI 업데이트"""
        # 카운트 저장
        self.text_input_fields["count"] = self.text_input_count_spinbox
        
        # 기존 위젯 제거
        for i in reversed(range(self.text_input_items_layout.count())):
            item = self.text_input_items_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # 텍스트 입력 항목 필드 초기화
        self.text_input_item_fields = []
        
        # 새 항목 추가
        for i in range(count):
            # 기본값 설정
            item_data = {
                "label": f"입력 {i+1}",
                "placeholder": "입력하세요",
                "width": 800,
                "height": 80,
                "x": 100,
                "y": 100 + i * 100,
                "font_size": 36
            }
            
            # 기존 데이터가 있으면 사용
            if i < len(self.config["text_input"]["items"]):
                item_data = self.config["text_input"]["items"][i]
            
            # 항목 그룹 생성
            item_group = QGroupBox(f"텍스트 입력 {i+1}")
            item_layout = QFormLayout(item_group)
            
            # 항목 필드 생성
            item_fields = {}
            
            # 레이블
            label_edit = QLineEdit(item_data.get("label", ""))
            item_layout.addRow("항목 이름:", label_edit)
            item_fields["label"] = label_edit
            
            # 플레이스홀더
            placeholder_edit = QLineEdit(item_data.get("placeholder", ""))
            item_layout.addRow("입력 예시:", placeholder_edit)
            item_fields["placeholder"] = placeholder_edit
            
            # 위치 및 크기
            for key in ["width", "height", "x", "y"]:
                # QSpinBox 대신 NumberLineEdit 사용
                line_edit = NumberLineEdit()
                line_edit.setValue(item_data.get(key, 0))
                label_text = "너비" if key == "width" else "높이" if key == "height" else "X 위치" if key == "x" else "Y 위치"
                item_layout.addRow(f"{label_text}:", line_edit)
                item_fields[key] = line_edit
            
            # 폰트 크기
            font_size_spin = NumberLineEdit()
            font_size_spin.setValue(item_data.get("font_size", 36))
            item_layout.addRow("폰트 크기:", font_size_spin)
            item_fields["font_size"] = font_size_spin
            
            # 출력용 폰트 설정 - 폰트 선택 레이아웃
            output_font_layout = QHBoxLayout()
            output_font_edit = QLineEdit(item_data.get("output_font", ""))
            output_font_layout.addWidget(output_font_edit, 1)
            item_fields["output_font"] = output_font_edit
            
            # 폰트 파일 선택 버튼 추가
            browse_button = QPushButton("찾기...")
            browse_button.clicked.connect(lambda checked, edit=output_font_edit: self.browse_font_file(edit))
            output_font_layout.addWidget(browse_button)
            
            item_layout.addRow("출력용 폰트:", output_font_layout)
            
            # 출력용 폰트 크기
            output_font_size_spin = NumberLineEdit()
            output_font_size_spin.setValue(item_data.get("output_font_size", 16))
            item_layout.addRow("출력용 폰트 크기:", output_font_size_spin)
            item_fields["output_font_size"] = output_font_size_spin
            
            # 출력용 폰트 색상
            output_font_color_button = ColorPickerButton(item_data.get("output_font_color", "#000000"))
            item_layout.addRow("출력용 폰트 색상:", output_font_color_button)
            item_fields["output_font_color"] = output_font_color_button
            
            self.text_input_items_layout.addWidget(item_group)
            self.text_input_item_fields.append(item_fields)
        
        # UI 업데이트
        self.text_input_items_container.updateGeometry()

    def update_config_from_ui(self):
        """UI 항목의 값들을 self.config에 업데이트합니다. (파일에는 저장하지 않음)"""
        # 기본 설정
        self.config["app_name"] = self.app_name_edit.text()
        self.config["screen_size"]["width"] = self.screen_width_edit.value()
        self.config["screen_size"]["height"] = self.screen_height_edit.value()
        self.config["camera_size"]["width"] = self.camera_width_edit.value()
        self.config["camera_size"]["height"] = self.camera_height_edit.value()
        
        # 크롭 영역 설정 저장
        for key, widget in self.crop_fields.items():
            self.config["crop_area"][key] = widget.value()
        
        # 카메라 카운트 설정 저장
        self.config["camera_count"]["number"] = self.camera_count_fields["number"].value()
        self.config["camera_count"]["font_size"] = self.camera_count_fields["font_size"].value()
        self.config["camera_count"]["font_color"] = self.camera_count_fields["font_color"].color
        
        # 화면 순서
        try:
            screen_order = [int(x.strip()) for x in self.screen_order_edit.text().split(",")]
            
            # 유효한 화면 타입 (0~5) 확인
            valid_screen_types = [0, 1, 2, 3, 4, 5]
            invalid_screen_types = [x for x in screen_order if x not in valid_screen_types]
            
            if invalid_screen_types:
                error_msg = f"유효하지 않은 화면 번호가 포함되어 있습니다: {', '.join(map(str, invalid_screen_types))}\n\n유효한 화면 번호는 0~5입니다."
                QMessageBox.warning(self, "화면 순서 오류", error_msg)
                return False
                
            self.config["screen_order"] = screen_order
            
            # 화면 순서에 따른 photo와 qr_uploaded_image 존재 여부 설정
            if "photo" in self.config:
                if 1 in screen_order:
                    self.config["photo"]["exists"] = True
                else:
                    self.config["photo"]["exists"] = False
            
            if "qr_uploaded_image" in self.config:
                if 3 in screen_order:
                    self.config["qr_uploaded_image"]["exists"] = True
                else:
                    self.config["qr_uploaded_image"]["exists"] = False
                
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "화면 순서는 쉼표로 구분된 숫자여야 합니다.")
            return False
        
        # 프레임 설정 저장
        for key, widget in self.frame_fields.items():
            self.config["frame"][key] = widget.value()
        
        # 촬영 사진 설정 저장
        self.config["photo"]["filename"] = "captured_image.jpg"
        for key in ["x", "y", "width", "height"]:
            self.config["photo"][key] = self.photo_fields[key].value()
        
        # 이미지 설정 저장
        self.config["images"]["count"] = self.image_count_spinbox.value()
        self.config["images"]["items"] = []
        
        for i, fields in enumerate(self.image_item_fields):
            item = {
                "filename": fields["filename"].text(),
                "x": fields["x"].value(),
                "y": fields["y"].value(),
                "width": fields["width"].value(),
                "height": fields["height"].value()
            }
            self.config["images"]["items"].append(item)
        
        # 텍스트 설정 저장
        self.config["texts"]["count"] = self.text_count_spinbox.value()
        self.config["texts"]["items"] = []
        
        for i, fields in enumerate(self.text_item_fields):
            item = {
                "content": fields["content"].text(),
                "x": fields["x"].value(),
                "y": fields["y"].value(),
                "width": fields["width"].value(),
                "height": fields["height"].value(),
                "font": fields["font"].text(),
                "font_size": fields["font_size"].value(),
                "font_color": fields["font_color"].color
            }
            self.config["texts"]["items"].append(item)
        
        # 텍스트 입력 설정 저장
        for key, widget in self.text_input_fields.items():
            self.config["text_input"][key] = widget.value()
        
        # 텍스트 입력 개수 설정 저장
        self.config["text_input"]["count"] = self.text_input_count_spinbox.value()
        self.config["text_input"]["items"] = []
        
        for i, fields in enumerate(self.text_input_item_fields):
            item = {
                "label": fields["label"].text(),
                "placeholder": fields["placeholder"].text(),
                "x": fields["x"].value(),
                "y": fields["y"].value(),
                "width": fields["width"].value(),
                "height": fields["height"].value(),
                "font_size": fields["font_size"].value(),
                "output_font": fields["output_font"].text(),
                "output_font_size": fields["output_font_size"].value(),
                "output_font_color": fields["output_font_color"].color
            }
            self.config["text_input"]["items"].append(item)
        
        # 키보드 설정 저장
        # 위치 및 크기
        for key, widget in self.keyboard_position_fields.items():
            self.config["keyboard"][key] = widget.value()
        
        # 스타일
        for key, widget in self.keyboard_style_fields.items():
            if isinstance(widget, ColorPickerButton):
                self.config["keyboard"][key] = widget.color
            else:
                self.config["keyboard"][key] = widget.value()
        
        # QR 코드 설정 저장
        self.config["qr"]["preview_width"] = self.qr_fields["preview_width"].value()
        self.config["qr"]["preview_height"] = self.qr_fields["preview_height"].value()
        self.config["qr"]["x"] = self.qr_fields["x"].value()
        self.config["qr"]["y"] = self.qr_fields["y"].value()
        
        # QR 업로드 이미지 설정 저장
        for key in ["x", "y", "width", "height"]:
            self.config["qr_uploaded_image"][key] = self.qr_uploaded_fields[key].value()
        
        # 화면 설정 저장
        for section in ["splash", "process", "complete"]:
            fields = getattr(self, f"{section}_fields")
            for key, widget in fields.items():
                if isinstance(widget, ColorPickerButton):
                    self.config[section][key] = widget.color
                else:
                    if isinstance(widget, QSpinBox) or isinstance(widget, NumberLineEdit):
                        self.config[section][key] = widget.value()
                    else:
                        self.config[section][key] = widget.text()
        
        return True