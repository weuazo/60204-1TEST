"""
메인 윈도우 모듈
"""

import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QProgressBar,
    QTextEdit, QComboBox, QTabWidget, QLineEdit, QAction, QMessageBox,
    QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from utils.report_pipeline import generate_report_from_excel
from utils.chatbot import chat_with_ai
import threading
from utils.prompt_loader import PromptLoader
from utils.api_key_manager import load_api_key
from gui.api_key_dialog import ApiKeyDialog
from gui.prompt_management_tab import PromptManagementTab

class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    def __init__(self):
        """생성자"""
        super().__init__()
        self.setWindowTitle("Gemini 규격 보고서 생성기")
        self.setGeometry(100, 100, 800, 600)
        self.current_prompt_path = "data/prompts/prompts.json"
        self.init_ui()
        self.check_api_key()
    
    def init_ui(self):
        """UI 초기화"""
        # 메뉴바
        menubar = self.menuBar()
        file_menu = menubar.addMenu("파일")
        settings_menu = menubar.addMenu("설정")

        api_key_action = QAction("API 키 설정", self)
        api_key_action.triggered.connect(self.show_api_key_dialog)
        settings_menu.addAction(api_key_action)

        exit_action = QAction("종료", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 탭
        tabs = QTabWidget()
        self.report_tab = self.create_report_tab()
        tabs.addTab(self.report_tab, "보고서 생성")
        
        self.chatbot_tab = self.create_chatbot_tab()
        tabs.addTab(self.chatbot_tab, "챗봇")

        self.prompt_management_tab = PromptManagementTab(self.current_prompt_path)
        self.prompt_management_tab.prompts_updated.connect(self.handle_prompts_updated)
        tabs.addTab(self.prompt_management_tab, "프롬프트 관리")
        
        self.setCentralWidget(tabs)
        self.handle_prompts_updated()
    
    def handle_prompts_updated(self):
        """PromptManagementTab에서 프롬프트가 업데이트되었을 때 호출되는 슬롯"""
        new_path = self.prompt_management_tab.path_edit.text().strip()
        if self.current_prompt_path != new_path:
            self.current_prompt_path = new_path

        self.refresh_report_prompt_list()
        self.refresh_chat_prompt_list()

    def check_api_key(self):
        if not load_api_key():
            QMessageBox.information(self, "API 키 필요", "Gemini API 키를 설정해주세요.")
            self.show_api_key_dialog()

    def show_api_key_dialog(self):
        dialog = ApiKeyDialog(self)
        dialog.exec_()
    
    def create_report_tab(self):
        """보고서 생성 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 입력 엑셀 파일
        file_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        input_btn = QPushButton("입력 파일 선택")
        input_btn.clicked.connect(self.select_input_file)
        file_layout.addWidget(QLabel("입력 엑셀:"))
        file_layout.addWidget(self.input_edit)
        file_layout.addWidget(input_btn)
        layout.addLayout(file_layout)

        # 출력 엑셀 파일
        out_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        output_btn = QPushButton("출력 파일 지정")
        output_btn.clicked.connect(self.select_output_file)
        out_layout.addWidget(QLabel("출력 엑셀:"))
        out_layout.addWidget(self.output_edit)
        out_layout.addWidget(output_btn)
        layout.addLayout(out_layout)

        # 프롬프트 선택 리스트 (다중 선택 가능)
        prompt_select_layout = QHBoxLayout()
        prompt_select_layout.addWidget(QLabel("적용 프롬프트 (항목):"))
        
        self.prompt_list = QListWidget()
        self.prompt_list.setSelectionMode(QListWidget.MultiSelection)  # 다중 선택 모드
        self.prompt_list.setMaximumHeight(100)  # 높이 제한
        
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.refresh_report_prompt_list)
        
        prompt_select_layout.addWidget(self.prompt_list)
        prompt_select_layout.addWidget(refresh_btn)
        layout.addLayout(prompt_select_layout)

        # 실행 버튼, 진행바
        run_layout = QHBoxLayout()
        self.run_btn = QPushButton("보고서 생성")
        self.run_btn.clicked.connect(self.run_report)
        self.progress = QProgressBar()
        run_layout.addWidget(self.run_btn)
        run_layout.addWidget(self.progress)
        layout.addLayout(run_layout)

        # 로그/결과
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        return widget
    
    def select_input_file(self):
        """입력 엑셀 파일 선택"""
        path, _ = QFileDialog.getOpenFileName(self, "입력 엑셀 파일 선택", "", "Excel Files (*.xlsx *.xls)")
        if path:
            self.input_edit.setText(path)
    
    def select_output_file(self):
        """출력 엑셀 파일 지정"""
        path, _ = QFileDialog.getSaveFileName(self, "출력 엑셀 파일 지정", "", "Excel Files (*.xlsx)")
        if path:
            self.output_edit.setText(path)
    
    def select_prompt_file(self):
        """프롬프트 JSON 파일 선택 - 이 메서드는 이제 사용되지 않음"""
        pass
    
    def refresh_report_prompt_list(self):
        """보고서 프롬프트 목록 새로고침"""
        prompt_path = self.current_prompt_path
        self.prompt_list.clear()
        try:
            loader = PromptLoader(prompt_path)
            prompts = loader.load_prompts_by_usage(usage_type="report")
            for p in prompts:
                item = QListWidgetItem(p.get("name", "(이름없음)"))
                self.prompt_list.addItem(item)
        except Exception as e:
            self.prompt_list.clear()
            self.prompt_list.addItem("[오류 로딩 실패]")
            print("Error loading report prompts:", e)
    
    def run_report(self):
        """보고서 생성"""
        input_path = self.input_edit.text().strip()
        output_path = self.output_edit.text().strip()
        prompt_path = self.current_prompt_path
        
        # 선택된 프롬프트 ID 목록 얻기
        selected_prompt_ids = []
        for idx in range(self.prompt_list.count()):
            item = self.prompt_list.item(idx)
            if item.isSelected():
                selected_prompt_ids.append(item.text())

        if not input_path or not output_path:
            self.log_text.append("입력/출력 파일을 지정하세요.")
            return
        
        if not selected_prompt_ids:
            self.log_text.append("적용할 프롬프트를 하나 이상 선택하세요.")
            return

        self.run_btn.setEnabled(False)
        self.progress.setRange(0, 0)  # 무한 진행
        self.log_text.append(f"보고서 생성 중... (선택된 프롬프트: {', '.join(selected_prompt_ids)})")
        threading.Thread(
            target=self._run_report_thread, 
            args=(input_path, output_path, prompt_path, selected_prompt_ids)
        ).start()
    
    def _run_report_thread(self, input_path, output_path, prompt_path, prompt_ids):
        try:
            generate_report_from_excel(input_path, output_path, prompt_path, prompt_ids=prompt_ids)
            self.log_text.append(f"완료: {output_path}에 저장됨")
        except Exception as e:
            self.log_text.append(f"[오류] {e}")
        self.progress.setRange(0, 1)
        self.run_btn.setEnabled(True)

    def create_chatbot_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 프롬프트 선택 리스트 (다중 선택 가능)
        prompt_select_layout = QHBoxLayout()
        prompt_select_layout.addWidget(QLabel("적용 프롬프트 (챗봇):"))
        
        self.chat_prompt_list = QListWidget()
        self.chat_prompt_list.setSelectionMode(QListWidget.MultiSelection)  # 다중 선택 모드
        self.chat_prompt_list.setMaximumHeight(100)  # 높이 제한
        
        refresh_chat_btn = QPushButton("새로고침")
        refresh_chat_btn.clicked.connect(self.refresh_chat_prompt_list)
        
        prompt_select_layout.addWidget(self.chat_prompt_list)
        prompt_select_layout.addWidget(refresh_chat_btn)
        layout.addLayout(prompt_select_layout)

        # 엑셀 항목 정보 입력
        info_layout = QHBoxLayout()
        self.clause_edit = QLineEdit()
        self.title_edit = QLineEdit()
        self.remark_edit = QLineEdit()
        self.status_edit = QLineEdit()
        info_layout.addWidget(QLabel("항목/번호:"))
        info_layout.addWidget(self.clause_edit)
        info_layout.addWidget(QLabel("내용/제목:"))
        info_layout.addWidget(self.title_edit)
        info_layout.addWidget(QLabel("코멘트:"))
        info_layout.addWidget(self.remark_edit)
        info_layout.addWidget(QLabel("상태:"))
        info_layout.addWidget(self.status_edit)
        layout.addLayout(info_layout)

        # 질문 입력
        self.question_edit = QLineEdit()
        layout.addWidget(QLabel("질문:"))
        layout.addWidget(self.question_edit)

        # 실행 버튼
        ask_btn = QPushButton("AI에게 질문")
        ask_btn.clicked.connect(self.run_chatbot)
        layout.addWidget(ask_btn)

        # 답변 출력
        self.answer_text = QTextEdit()
        self.answer_text.setReadOnly(True)
        layout.addWidget(QLabel("AI 답변:"))
        layout.addWidget(self.answer_text)

        return widget

    def refresh_chat_prompt_list(self):
        """챗봇 프롬프트 목록 새로고침"""
        prompt_path = self.current_prompt_path
        self.chat_prompt_list.clear()
        try:
            loader = PromptLoader(prompt_path)
            prompts = loader.load_prompts_by_usage(usage_type="chat")
            for p in prompts:
                item = QListWidgetItem(p.get("name", "(이름없음)"))
                self.chat_prompt_list.addItem(item)
        except Exception as e:
            self.chat_prompt_list.clear()
            self.chat_prompt_list.addItem("[오류 로딩 실패]")
            print("Error loading chat prompts:", e)

    def run_chatbot(self):
        prompt_path = self.current_prompt_path
        
        # 선택된 챗봇 프롬프트 ID 목록 얻기
        selected_prompt_ids = []
        for idx in range(self.chat_prompt_list.count()):
            item = self.chat_prompt_list.item(idx)
            if item.isSelected():
                selected_prompt_ids.append(item.text())

        context = {}
        if self.clause_edit.text().strip():
            context["clause"] = self.clause_edit.text().strip()
        if self.title_edit.text().strip():
            context["title"] = self.title_edit.text().strip()
        if self.remark_edit.text().strip():
            context["remark"] = self.remark_edit.text().strip()
        if self.status_edit.text().strip():
            context["status"] = self.status_edit.text().strip()
            
        question = self.question_edit.text().strip()
        
        if not question:
            self.answer_text.setPlainText("질문을 입력하세요.")
            return
            
        if not selected_prompt_ids:
            self.answer_text.setPlainText("적용할 챗봇 프롬프트를 하나 이상 선택하세요.")
            return
            
        self.answer_text.setPlainText("AI 답변 생성 중...")
        threading.Thread(
            target=self._run_chatbot_thread, 
            args=(question, context, prompt_path, selected_prompt_ids)
        ).start()

    def _run_chatbot_thread(self, question, context, prompt_path, prompt_ids):
        try:
            answer = chat_with_ai(question, context, prompt_path, prompt_ids=prompt_ids)
            self.answer_text.setPlainText(answer)
        except Exception as e:
            self.answer_text.setPlainText(f"[오류] {e}")