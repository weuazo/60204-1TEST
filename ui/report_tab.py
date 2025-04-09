import tkinter as tk
from tkinter import ttk, messagebox

# 빈 함수만 남겨두어 임포트 오류를 방지합니다
def create_report_tab(parent):
    """보고서 생성 탭 구성 (비활성화됨)"""
    frame = ttk.Frame(parent, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # 비활성화 메시지
    ttk.Label(frame, text="보고서 생성 기능이 비활성화되었습니다.", font=("Arial", 14, "bold")).pack(pady=30)
    ttk.Label(frame, text="이 기능은 현재 개발 중이거나 제거되었습니다.", font=("Arial", 10)).pack()
    ttk.Label(frame, text="자세한 내용은 관리자에게 문의하세요.", font=("Arial", 10)).pack(pady=10)
    
    return frame

# 호환성을 위한 간단한 더미 함수들
def on_sheet_change(*args, **kwargs):
    pass

def browse_base_template(*args, **kwargs):
    pass

def browse_review_sheet(*args, **kwargs):
    pass

def refresh_sheet_list(*args, **kwargs):
    pass

def refresh_columns(*args, **kwargs):
    pass

def update_preview(*args, **kwargs):
    pass

def update_base_preview(*args, **kwargs):
    pass

def handle_generate(*args, **kwargs):
    messagebox.showinfo("기능 비활성화", "보고서 생성 기능이 비활성화되었습니다.")

def show_progress_dialog(*args, **kwargs):
    return None

def detect_standard_with_ai(*args, **kwargs):
    pass

def add_custom_standard(*args, **kwargs):
    pass

def show_standard_editor(*args, **kwargs):
    pass

def run_ai_column_detection(*args, **kwargs):
    messagebox.showinfo("기능 비활성화", "보고서 생성 기능이 비활성화되었습니다.")

def run_batch_analysis(*args, **kwargs):
    messagebox.showinfo("기능 비활성화", "보고서 생성 기능이 비활성화되었습니다.")

def create_ai_status_indicator(*args, **kwargs):
    return ttk.Frame()

def create_column_confidence_display(*args, **kwargs):
    return ttk.Frame()

def create_prompt_selector(*args, **kwargs):
    return ttk.Frame()

def show_prompt_manager(*args, **kwargs):
    pass

# 전역 변수도 최소한으로 유지
base_template_path = ""
review_sheet_path = ""
sheet_name_selected = None
column_options = []