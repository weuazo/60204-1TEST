import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import os
import sys

# UI 유틸리티 임포트 (순환 참조 피하기)
from ui.ui_utils import (
    set_root, log_message, show_api_key_dialog, update_all_prompt_statuses, update_api_status,
    PRIMARY_COLOR, SECONDARY_COLOR, BG_COLOR, CARD_COLOR, TEXT_COLOR, 
    SUCCESS_COLOR, WARNING_COLOR, ERROR_COLOR, BORDER_COLOR, HOVER_COLOR
)

# 전역 변수
root = None
notebook = None

def create_gui():
    global root, notebook
    
    # 메인 창 설정
    root = tk.Tk()
    root.title("Gemini 보고서 자동 생성기")
    root.geometry("1200x800")
    root.configure(bg=BG_COLOR)
    
    # ui_utils.py의 root 참조 설정
    set_root(root)
    
    # 아이콘 설정 (윈도우)
    try:
        if os.path.exists("assets/icon.ico"):
            root.iconbitmap("assets/icon.ico")
    except Exception as e:
        print(f"아이콘 설정 실패: {e}")
        
    # 스타일 설정
    style = ttk.Style()
    style.theme_use("clam")  # 테마 설정
    
    # 프레임 스타일
    style.configure("TFrame", background=BG_COLOR)
    style.configure("Card.TFrame", background=CARD_COLOR, relief="flat")
    
    # 레이블 스타일
    style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=("Arial", 10))
    style.configure("Title.TLabel", font=("Arial", 14, "bold"), foreground=PRIMARY_COLOR)
    style.configure("Subtitle.TLabel", font=("Arial", 12, "bold"))
    style.configure("Success.TLabel", foreground=SUCCESS_COLOR)
    style.configure("Warning.TLabel", foreground=WARNING_COLOR)
    style.configure("Error.TLabel", foreground=ERROR_COLOR)
    
    # 버튼 스타일
    style.configure("TButton", font=("Arial", 10), padding=5)
    style.configure("Primary.TButton", background=PRIMARY_COLOR, foreground="white")
    style.map("Primary.TButton", background=[("active", SECONDARY_COLOR)])
    style.configure("Action.TButton", font=("Arial", 12, "bold"), padding=10)
    
    # 탭 스타일
    style.configure("TNotebook", background=BG_COLOR, tabmargins=[0, 0, 0, 0])
    style.configure("TNotebook.Tab", background=BG_COLOR, padding=[15, 5], font=("Arial", 10))
    style.map("TNotebook.Tab", 
              background=[("selected", PRIMARY_COLOR), ("active", HOVER_COLOR)],
              foreground=[("selected", "#ffffff"), ("active", TEXT_COLOR)])

    # 헤더 프레임
    header_frame = tk.Frame(root, bg=PRIMARY_COLOR, height=70)
    header_frame.pack(fill=tk.X)
    
    # 앱 타이틀
    title_label = tk.Label(
        header_frame, 
        text="Gemini 보고서 자동 생성기", 
        font=("Arial", 18, "bold"), 
        bg=PRIMARY_COLOR,
        fg="white"
    )
    title_label.pack(side=tk.LEFT, padx=20, pady=15)
    
    # API 상태 표시
    api_status_text = "API 연결됨 ✓" if os.environ.get("GEMINI_API_KEY") else "API 연결 안됨 ⚠️"
    
    api_frame = tk.Frame(header_frame, bg=PRIMARY_COLOR)
    api_frame.pack(side=tk.RIGHT, padx=20, pady=15)
    
    api_status = tk.Label(
        api_frame, 
        text=api_status_text, 
        font=("Arial", 10), 
        bg=PRIMARY_COLOR,
        fg="white"
    )
    api_status.pack(side=tk.RIGHT)
    
    # API 키 설정 버튼
    api_button = tk.Button(
        api_frame, 
        text="API 키 설정", 
        font=("Arial", 10), 
        bg=SECONDARY_COLOR,
        fg="white",
        bd=0,
        padx=10,
        pady=3,
        cursor="hand2",
        command=show_api_key_dialog
    )
    api_button.pack(side=tk.RIGHT, padx=(0, 15))

    # 메뉴 설정 (새로고침 메뉴 추가)
    menubar = tk.Menu(root)
    
    # 파일 메뉴
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="새로고침", command=refresh_ui, accelerator="F5")
    file_menu.add_separator()
    file_menu.add_command(label="종료", command=root.destroy)
    menubar.add_cascade(label="파일", menu=file_menu)
    
    # API 설정 메뉴
    setting_menu = tk.Menu(menubar, tearoff=0)
    setting_menu.add_command(label="API 키 설정", command=show_api_key_dialog)
    menubar.add_cascade(label="설정", menu=setting_menu)
    
    root.config(menu=menubar)
    
    # F5 키 바인딩
    root.bind("<F5>", lambda event: refresh_ui())

    # 메인 내용 영역
    content_frame = tk.Frame(root, bg=BG_COLOR)
    content_frame.pack(fill=tk.BOTH, expand=True)
    
    # 탭 인터페이스
    notebook = ttk.Notebook(content_frame)
    
    report_tab = ttk.Frame(notebook, style="TFrame")
    chat_tab = ttk.Frame(notebook, style="TFrame")
    prompt_tab = ttk.Frame(notebook, style="TFrame")
    help_tab = ttk.Frame(notebook, style="TFrame")  # 도움말 탭 추가
    
    notebook.add(report_tab, text=" 📊 보고서 생성 ")
    notebook.add(chat_tab, text=" 💬 AI 채팅 ")
    notebook.add(prompt_tab, text=" ✏️ 프롬프트 관리 ")
    notebook.add(help_tab, text=" ❓ 도움말 ")  # 도움말 탭 추가
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 푸터 프레임 (상태 표시줄)
    footer_frame = tk.Frame(root, bg=BORDER_COLOR, height=25)
    footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
    
    status_label = tk.Label(
        footer_frame, 
        text="준비 완료", 
        font=("Arial", 9), 
        bg=BORDER_COLOR,
        fg=TEXT_COLOR,
        anchor="w"
    )
    status_label.pack(side=tk.LEFT, padx=15, fill=tk.Y)
    
    # 버전 정보
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from main import VERSION
    except ImportError:
        VERSION = "0.1.1"
    
    version_label = tk.Label(
        footer_frame, 
        text=f"v{VERSION}", 
        font=("Arial", 9), 
        bg=BORDER_COLOR,
        fg=TEXT_COLOR,
        anchor="e"
    )
    version_label.pack(side=tk.RIGHT, padx=15, fill=tk.Y)
    
    # 지연 탭 초기화
    init_tabs()
    
    # API 상태 업데이트
    update_api_status()
    
    # 프롬프트 상태 업데이트
    from ui.ui_utils import update_all_prompt_statuses
    root.after(100, update_all_prompt_statuses)
    
    return root

def init_tabs():
    """탭 모듈들을 지연 로딩하여 초기화합니다"""
    global root
    
    try:
        # 먼저 content_frame과 notebook 찾기
        content_frame = None
        notebook = None
        
        for widget in root.winfo_children():
            if isinstance(widget, tk.Frame) and widget.cget("bg") == BG_COLOR:
                content_frame = widget
                for child in content_frame.winfo_children():
                    if isinstance(child, ttk.Notebook):
                        notebook = child
                        break
                break
        
        if not content_frame or not notebook:
            log_message("UI 요소를 찾을 수 없습니다.", "error")
            return
            
        # 각 탭 모듈 임포트하고 초기화
        tab_frames = notebook.winfo_children()
        if len(tab_frames) < 3:
            log_message("탭 프레임이 충분하지 않습니다.", "error")
            return
            
        try:
            # 1. 보고서 생성 탭
            from ui.report_tab import create_report_tab
            create_report_tab(tab_frames[0])
        except Exception as e:
            log_message(f"보고서 탭 초기화 오류: {e}", "error")
            
        try:
            # 2. 채팅 탭
            from ui.chat_tab import create_chat_tab
            create_chat_tab(tab_frames[1])
        except Exception as e:
            log_message(f"채팅 탭 초기화 오류: {e}", "error")
            
        try:
            # 3. 프롬프트 관리 탭
            from ui.prompt_tab import build_prompt_tab
            build_prompt_tab(tab_frames[2])
        except Exception as e:
            log_message(f"프롬프트 탭 초기화 오류: {e}", "error")
        
        try:
            # 4. 도움말 탭
            create_help_tab(tab_frames[3])
        except Exception as e:
            log_message(f"도움말 탭 초기화 오류: {e}", "error")
    
    except Exception as e:
        log_message(f"탭 초기화 중 오류 발생: {e}", "error")

def refresh_ui():
    """UI 요소들 새로고침"""
    global root
    
    if not root:
        log_message("GUI가 아직 초기화되지 않았습니다.", "error")
        return
        
    try:
        # 가장 먼저 refreshable 함수들을 동적으로 가져옴
        refresh_functions = {}
        
        try:
            from ui.report_tab import refresh_columns, review_sheet_path, sheet_name_selected
            refresh_functions['report'] = {
                'refresh_columns': refresh_columns,
                'review_sheet_path': review_sheet_path,
                'sheet_name_selected': sheet_name_selected
            }
        except ImportError:
            log_message("보고서 탭 함수를 가져올 수 없습니다.", "warning")
        except Exception as e:
            log_message(f"보고서 탭 함수 가져오기 오류: {e}", "error")
            
        try:
            from ui.prompt_tab import refresh_prompt_list, filter_var
            refresh_functions['prompt'] = {
                'refresh_prompt_list': refresh_prompt_list,
                'filter_var': filter_var if 'filter_var' in locals() else None
            }
        except ImportError:
            log_message("프롬프트 탭 함수를 가져올 수 없습니다.", "warning")
        except Exception as e:
            log_message(f"프롬프트 탭 함수 가져오기 오류: {e}", "error")
        
        # 현재 선택된 탭 찾기
        notebook = None
        current_tab_idx = 0
        
        for widget in root.winfo_children():
            if isinstance(widget, tk.Frame):  # content_frame 찾기
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Notebook):  # notebook 찾기
                        notebook = child
                        current_tab_idx = notebook.index(notebook.select())
                        break
                if notebook:
                    break
        
        if notebook:
            # 탭에 따른 새로고침
            if current_tab_idx == 0:  # 보고서 생성 탭
                if 'report' in refresh_functions:
                    rf = refresh_functions['report']
                    if (rf.get('review_sheet_path') and rf.get('sheet_name_selected') and 
                        rf.get('refresh_columns')):
                        rf['refresh_columns']()
                        log_message("보고서 생성 탭 새로고침 완료", "info")
            
            elif current_tab_idx == 2:  # 프롬프트 관리 탭
                if 'prompt' in refresh_functions:
                    rf = refresh_functions['prompt']
                    if rf.get('refresh_prompt_list'):
                        filter_type = "all"
                        if rf.get('filter_var'):
                            filter_type = rf['filter_var'].get()
                        rf['refresh_prompt_list'](filter_type)
                        log_message("프롬프트 목록 새로고침 완료", "info")
        
        # 프롬프트 상태 업데이트 - 마지막에 시도
        update_all_prompt_statuses()
        
    except Exception as e:
        log_message(f"새로고침 중 오류 발생: {str(e)}", "error")
        messagebox.showerror("시스템 오류", f"UI 새로고침 실패: {str(e)}")

def get_root():
    """현재 설정된 root 윈도우 반환"""
    global root
    return root

def create_help_tab(parent):
    """도움말 탭 구성"""
    help_container = ttk.Frame(parent)
    help_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    # 기본 도움말 카드
    basic_help_card = ttk.Frame(help_container, style="Card.TFrame")
    basic_help_card.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(basic_help_card, text="사용 가이드", style="Title.TLabel", padding=15).pack(anchor="w")
    
    # 주요 기능 설명
    help_content = tk.Text(basic_help_card, wrap=tk.WORD, height=20, 
                          font=("Arial", 10), padx=15, pady=10,
                          highlightthickness=0, relief="flat")
    help_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    
    help_content.insert("1.0", """Gemini 보고서 자동 생성기 사용 가이드

1. 보고서 생성 기능
   • 템플릿 파일: 항목 번호와 결과가 들어갈 열이 있는 엑셀 파일을 선택합니다.
   • 검토 시트: 항목 번호와 제목이 있는 파일을 선택합니다.
   • 유연한 매칭: 항목 번호가 완벽히 일치하지 않아도 유사한 항목(예: "8.2"와 "8.2.1")을 매칭합니다.
   • 규격 자동 감지: 검토 시트에서 규격(IEC 60204-1 등)을 자동으로 감지하여 적용합니다.

2. 채팅 기능
   • AI와 자유롭게 대화하며 기술 문서 검토와 관련된 질문을 할 수 있습니다.
   • 프롬프트 관리 탭에서 채팅 유형으로 설정된 프롬프트가 적용됩니다.

3. 프롬프트 관리
   • 보고서 생성과 채팅에 적용할 프롬프트를 생성하고 관리합니다.
   • 우선순위가 낮은 값(1, 2, 3...)이 먼저 적용됩니다.

4. 유연한 항목 매칭 알고리즘
   • 정확히 일치하는 항목 검색
   • 정규화된 항목으로 비교 (공백, 특수문자 제거)
   • 접두어 매칭 (예: "8.2.1"은 "8.2"로 시작하는 항목과 매칭)
   • 유사도 기반 매칭 (70% 이상 유사하면 매칭)

5. 규격 자동 감지
   • IEC 60204-1 (기계류의 전기장비)
   • IEC 61010 (측정, 제어 및 실험실용 전기장비)
   • ISO 13849 (안전 관련 제어 시스템)
   • IEC 62061 (기계류의 안전성)
   • ISO 14119 (인터록 장치) 등이 자동 감지됩니다.
""")
    
    help_content.config(state="disabled")
    
    # 규격 정보 카드
    standard_card = ttk.Frame(help_container, style="Card.TFrame")
    standard_card.pack(fill=tk.X, pady=10)
    
    ttk.Label(standard_card, text="지원되는 규격 정보", style="Title.TLabel", padding=15).pack(anchor="w")
    
    # 규격 정보 테이블 형태로 보여주기
    std_content = tk.Text(standard_card, wrap=tk.WORD, height=15, 
                         font=("Arial", 10), padx=15, pady=10,
                         highlightthickness=0, relief="flat")
    std_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    
    std_content.insert("1.0", """프로그램에서 자동으로 감지하고 지원하는 규격 목록:

1. IEC 60204-1: 기계류의 전기장비
   • 산업용 기계의 전기 장비 및 시스템에 대한 안전 요구사항
   • 주요 섹션: 위험 평가, 보호 접지, 비상 정지, 제어 회로, 문서화

2. IEC 61010: 측정, 제어 및 실험실용 전기장비
   • 측정, 제어 및 실험실용 전기장비의 안전 요구사항
   • 주요 섹션: 감전 보호, 기계적 위험, 확산된 에너지, 문서화

3. ISO 13849: 안전 관련 제어 시스템
   • 기계류의 안전 관련 제어 시스템 설계 원칙
   • 주요 섹션: 위험 평가, 성능 수준(PL), 카테고리, 검증 및 유효성 확인

4. IEC 62061: 기계류의 안전성
   • 기계류의 안전 관련 전기, 전자 및 프로그래머블 제어 시스템
   • 주요 섹션: 안전 무결성 수준(SIL), 하드웨어 고장 확률, 진단 범위, 소프트웨어 요구사항

5. ISO 14119: 인터록 장치
   • 가드 관련 인터록 장치의 설계 및 선택 원칙
   • 주요 섹션: 락킹 장치, 이스케이핑, 마스킹, 오류 배제 원칙

검토 파일에서 이러한 규격이 자동으로 감지되면, AI는 해당 규격에 맞는 전문적인 검토 의견을 생성합니다.
""")
    
    std_content.config(state="disabled")
    
    # 버전 정보
    version_card = ttk.Frame(help_container, style="Card.TFrame")
    version_card.pack(fill=tk.X, pady=10)
    
    version_frame = ttk.Frame(version_card)
    version_frame.pack(fill=tk.X, padx=15, pady=15)
    
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from main import VERSION
    except ImportError:
        VERSION = "0.1.3"
    
    ttk.Label(version_frame, text=f"Gemini 보고서 자동 생성기 v{VERSION}", 
             font=("Arial", 12, "bold")).pack(side=tk.LEFT)
    
    # 연락처 정보
    ttk.Label(version_frame, text="© 2023", font=("Arial", 9)).pack(side=tk.RIGHT)

    # 탭2: 확장 보고서 생성 (새로 추가)
    try:
        from ui.extended_report_tab import create_extended_report_tab
        ext_report_tab = tk.Frame(notebook, bg=BG_COLOR)
        create_extended_report_tab(ext_report_tab)
        notebook.add(ext_report_tab, text="확장 보고서")
    except Exception as e:
        print(f"확장 보고서 탭 로딩 오류: {e}")
        ext_report_tab = tk.Frame(notebook, bg=BG_COLOR)
        tk.Label(ext_report_tab, text=f"탭 로드 실패: {e}").pack()
        notebook.add(ext_report_tab, text="확장 보고서")

def show_help():
    """도움말 표시"""
    try:
        help_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "README.md")
        if os.path.exists(help_path):
            try:
                webbrowser.open(help_path)
                return
            except:
                pass
        
        # 웹 도움말로 대체
        webbrowser.open("https://github.com/yourusername/gemini-report-generator")
    except Exception as e:
        messagebox.showerror("도움말 오류", f"도움말을 열 수 없습니다: {e}")

if __name__ == "__main__":
    try:
        app = create_gui()
        app.mainloop()
    except Exception as e:
        print(f"애플리케이션 초기화 오류: {e}")
        sys.exit(1)
