import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import webbrowser
import os
import sys
import traceback

# UI 유틸리티 임포트 (순환 참조 피하기)
from ui.ui_utils import (
    set_root, set_log_box, log_message, show_api_key_dialog, update_all_prompt_statuses, update_api_status,
    PRIMARY_COLOR, SECONDARY_COLOR, BG_COLOR, CARD_COLOR, TEXT_COLOR, 
    SUCCESS_COLOR, WARNING_COLOR, ERROR_COLOR, BORDER_COLOR, HOVER_COLOR
)

# 전역 변수
root = None
notebook = None

# 콜백 시스템 추가 (새로 추가)
callback_registry = {}

def register_callback(name, callback_fn):
    """콜백 함수 등록 (새로 추가)"""
    global callback_registry
    callback_registry[name] = callback_fn
    log_message(f"콜백 등록됨: {name}", "debug")

def trigger_callback(name, *args, **kwargs):
    """등록된 콜백 함수 호출 (새로 추가)"""
    global callback_registry
    if name in callback_registry:
        try:
            return callback_registry[name](*args, **kwargs)
        except Exception as e:
            log_message(f"콜백 실행 중 오류 ({name}): {e}", "error")
            return None
    return None

def on_close():
    """애플리케이션 종료 처리"""
    global root
    if messagebox.askokcancel("종료 확인", "프로그램을 종료하시겠습니까?"):
        log_message("프로그램 종료 중...", "info")
        if root:
            root.destroy()

def apply_theme():
    """스타일 테마 적용"""
    style = ttk.Style()
    
    # 스타일 초기화 - 기본 테마 적용 후 커스텀 설정
    style.theme_use('default')
    
    # 기본 색상 및 폰트 설정
    style.configure(".", font=("Arial", 10))
    style.configure("TFrame", background=BG_COLOR)
    style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR)
    
    # 기본 버튼 스타일 - 가시성 향상을 위해 개선
    style.configure("TButton", 
                   background="#1976D2", 
                   foreground="white", 
                   relief="raised",
                   borderwidth=2,  
                   padding=(10, 5),
                   font=("Arial", 10))
    
    # 호버 및 누름 효과 강화 - 플랫폼 간 호환성 강화
    style.map("TButton",
        background=[("active", "#2196F3"), ("pressed", "#0D47A1"), ("focus", "#2196F3")],
        foreground=[("active", "white"), ("pressed", "white"), ("disabled", "#888888")],
        relief=[("pressed", "sunken")]
    )
    
    # Tkinter 기본 버튼을 위한 스타일도 설정
    root.option_add('*Button.background', '#1976D2')
    root.option_add('*Button.foreground', 'white')
    root.option_add('*Button.relief', 'raised')
    root.option_add('*Button.borderWidth', 2)
    root.option_add('*Button.padX', 10)
    root.option_add('*Button.padY', 5)
    root.option_add('*Button.font', ('Arial', 10))
    
    # 타이틀 레이블 스타일
    style.configure("Title.TLabel", font=("Arial", 14, "bold"), foreground=PRIMARY_COLOR)
    style.configure("Subtitle.TLabel", font=("Arial", 12, "bold"), foreground=PRIMARY_COLOR)
    
    # 카드 스타일
    style.configure("Card.TFrame", background=CARD_COLOR, relief="solid", borderwidth=1)
    
    # 프로그레스바 색상 - 명시적 색상 정의 강화
    style.configure("TProgressbar", 
                   background=PRIMARY_COLOR, 
                   troughcolor=BG_COLOR,
                   bordercolor=BORDER_COLOR,
                   lightcolor=PRIMARY_COLOR,
                   darkcolor=SECONDARY_COLOR)
    
    # 특별한 액션 버튼 스타일 - 더 눈에 띄는 색상으로 개선
    style.configure("Action.TButton", 
                   background="#FF5722",
                   foreground="white", 
                   relief="raised",
                   borderwidth=2,
                   padding=(10, 5),
                   font=("Arial", 10, "bold"))
    
    style.map("Action.TButton",
        background=[("active", "#FF7043"), ("pressed", "#E64A19"), ("focus", "#FF7043")],
        foreground=[("active", "white"), ("pressed", "white"), ("disabled", "#888888")]
    )
    
    # 파일 찾아보기 버튼을 위한 특별 스타일 (눈에 더 잘 띔)
    style.configure("Browse.TButton", 
                   background="#009688",
                   foreground="white", 
                   relief="ridge",
                   borderwidth=2,
                   padding=(10, 5),
                   font=("Arial", 10))
    
    style.map("Browse.TButton",
        background=[("active", "#4DB6AC"), ("pressed", "#00796B"), ("focus", "#4DB6AC")],
        foreground=[("active", "white"), ("pressed", "white"), ("disabled", "#888888")]
    )
    
    # 강조 버튼 스타일 (결과 생성 같은 주요 액션용)
    style.configure("Primary.TButton", 
                   background="#4CAF50",
                   foreground="white", 
                   relief="raised",
                   borderwidth=2,
                   padding=(10, 5),
                   font=("Arial", 11, "bold"))
    
    style.map("Primary.TButton",
        background=[("active", "#66BB6A"), ("pressed", "#2E7D32"), ("focus", "#66BB6A")],
        foreground=[("active", "white"), ("pressed", "white"), ("disabled", "#888888")]
    )
    
    # 노트북(탭) 스타일
    style.configure("TNotebook", background=BG_COLOR)
    style.configure("TNotebook.Tab", padding=[10, 5], font=("Arial", 10))
    style.map("TNotebook.Tab",
        background=[("selected", CARD_COLOR), ("active", HOVER_COLOR)],
        foreground=[("selected", PRIMARY_COLOR), ("active", TEXT_COLOR)]
    )
    
    # 콤보박스 및 체크버튼 스타일
    style.configure("TCombobox", padding=5)
    style.configure("TCheckbutton", background=BG_COLOR)
    
    # 구분선
    style.configure("TSeparator", background=BORDER_COLOR)
    
    # 라벨프레임
    style.configure("TLabelframe", background=BG_COLOR)
    style.configure("TLabelframe.Label", background=BG_COLOR, foreground=PRIMARY_COLOR, font=("Arial", 10, "bold"))
    
    # 강제 업데이트로 스타일 즉시 적용
    try:
        style.theme_use('default')  # 테마를 한 번 더 적용하여 변경사항 강제 적용
    except Exception as e:
        print(f"스타일 강제 적용 중 오류: {e}")

def load_data():
    """초기 데이터 로드 및 설정"""
    try:
        # 환경 변수 확인
        if not os.environ.get("GEMINI_API_KEY"):
            log_message("API 키가 설정되지 않았습니다.", "warning")
        
        # 프롬프트 데이터 로드 확인
        try:
            from utils.prompt_loader import count_prompts
            prompt_count = count_prompts()
            if (prompt_count > 0):
                log_message(f"프롬프트 {prompt_count}개를 로드했습니다.", "info")
            else:
                log_message("사용 가능한 프롬프트가 없습니다.", "warning")
        except ImportError:
            log_message("프롬프트 로더를 가져올 수 없습니다.", "error")
        
    except Exception as e:
        log_message(f"데이터 로드 중 오류 발생: {e}", "error")

def check_api_key():
    """API 키 설정 여부 확인 및 처리"""
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        log_message("API 키가 설정되지 않았습니다. 설정 대화상자를 표시합니다.", "warning")
        # API 키 설정 대화상자를 1초 후에 표시 (UI가 완전히 로드된 후)
        if root:
            root.after(1000, show_api_key_dialog)
    else:
        log_message("API 키가 설정되었습니다.", "info")
        # API 연결 상태 업데이트
        update_api_status()

def create_main_window():
    """메인 창 생성"""
    global root, notebook, log_box, close_window, status_bar
    
    # 루트 윈도우 설정
    root = tk.Tk()
    root.title("Gemini 보고서 생성기")
    
    # 화면 크기 조정: 사용자 화면 크기에 맞게 설정
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # 화면 크기의 80%로 창 크기 설정 (90%에서 80%로 줄임)
    window_width = int(screen_width * 0.8)
    window_height = int(screen_height * 0.8)
    
    # 창 위치 계산 (화면 중앙)
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    
    # 창 크기와 위치 설정
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.minsize(800, 600)  # 최소 창 크기 감소 (1000, 700에서 조정)
    
    # 창 닫기 핸들러 등록
    root.protocol("WM_DELETE_WINDOW", on_close)
    
    # 스타일 설정
    apply_theme()
    
    # 헤더 영역 추가 (API 상태 표시 및 설정 버튼)
    header_frame = ttk.Frame(root)
    header_frame.pack(fill=tk.X, padx=10, pady=5)
    
    # API 키 상태 및 설정 버튼
    api_frame = ttk.Frame(header_frame)
    api_frame.pack(side=tk.RIGHT)
    
    # API 상태 표시
    api_status_text = "API 연결 안됨 ⚠️"
    if os.environ.get("GEMINI_API_KEY"):
        api_status_text = "API 연결됨 ✓"
    
    api_status_label = ttk.Label(
        api_frame, 
        text=api_status_text,
        padding=(5, 0)
    )
    api_status_label.pack(side=tk.LEFT, padx=5)
    
    # API 키 설정 버튼
    api_key_btn = ttk.Button(
        api_frame,
        text="API 키 설정",
        command=show_api_key_dialog,
        width=12
    )
    api_key_btn.pack(side=tk.LEFT, padx=5)
    
    # 메인 프레임 설정
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    # 탭 구성 - 개선된 스타일 적용
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # 탭 생성 시 스타일 적용
    style = ttk.Style()
    style.configure("Active.TFrame", background=BG_COLOR)
    style.configure("Disabled.TFrame", background="#f0f0f0")
    style.configure("Tab.TLabel", font=("Arial", 10, "bold"), padding=5)
    
    # 확장 보고서 생성 탭 (새로운 디자인으로 강화)
    advanced_tab = ttk.Frame(notebook, style="Active.TFrame")
    from ui.extended_report_tab import create_extended_report_tab
    create_extended_report_tab(advanced_tab)
    notebook.add(advanced_tab, text="✨ 확장 보고서 생성")
    
    # 기본 보고서 생성 탭 (기존 기능, 명확하게 비활성화 표시)
    basic_tab = ttk.Frame(notebook, style="Disabled.TFrame")
    from ui.report_tab import create_report_tab
    create_report_tab(basic_tab)
    notebook.add(basic_tab, text="📄 기본 보고서 (비활성화됨)")
    
    # AI 채팅 탭
    chat_tab = ttk.Frame(notebook)
    from ui.chat_tab import create_chat_tab
    create_chat_tab(chat_tab)
    notebook.add(chat_tab, text="💬 AI 채팅")
    
    # 프롬프트 관리 탭
    prompt_tab = ttk.Frame(notebook)
    from ui.prompt_tab import build_prompt_tab  # create_prompt_tab에서 build_prompt_tab으로 수정
    build_prompt_tab(prompt_tab)
    notebook.add(prompt_tab, text="⚙️ 프롬프트 관리")
    
    # 도움말 탭
    help_tab = ttk.Frame(notebook)
    create_help_tab(help_tab)
    notebook.add(help_tab, text="❓ 도움말")
    
    # 사용자 피드백을 위한 탭 변경 이벤트 연결
    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    
    # 로그 영역 높이 줄이기
    log_frame = ttk.Frame(main_frame)
    log_frame.pack(fill=tk.X, pady=5)
    
    # 로그 영역
    log_inner_frame = ttk.LabelFrame(log_frame, text="로그 및 상태 메시지")
    log_inner_frame.pack(fill=tk.X)
    
    log_box = scrolledtext.ScrolledText(
        log_inner_frame, wrap=tk.WORD, height=3, width=10,  # 높이 4에서 3으로 줄임
        state="disabled", background="#f8f8f8"
    )
    log_box.pack(fill=tk.X, padx=5, pady=5)
    
    # Gemini API 키 설정 버튼
    config_frame = ttk.Frame(main_frame)
    config_frame.pack(fill=tk.X, pady=5)
    
    ttk.Button(
        config_frame,
        text="API 키 설정",
        command=show_api_key_dialog,
        width=15
    ).pack(side=tk.LEFT, padx=5)
    
    # 버전 정보
    version_label = ttk.Label(config_frame, text="v2.0", foreground="#999999")
    version_label.pack(side=tk.RIGHT, padx=5)
    
    # 상태바
    status_bar = ttk.Label(
        root, text="준비됨", relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2)
    )
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # 로그 박스 참조 저장
    set_log_box(log_box)
    
    # 루트 참조 저장 (대화 상자 제어용)
    set_root(root)
    
    # 초기 데이터 로드
    load_data()
    
    # 시작 로그
    log_message("프로그램이 시작되었습니다", "info")
    log_message("확장 보고서 생성 탭이 활성화되었습니다", "info")
    
    # 초기 API 키 확인
    check_api_key()
    
    return root

def on_tab_changed(event):
    """탭 변경 시 발생하는 이벤트 핸들러"""
    try:
        # 현재 선택된 탭 확인
        current_tab = event.widget.select()
        tab_index = event.widget.index(current_tab)
        
        # 각 탭별로 필요한 처리 (보고서 탭에 대한 특별 처리 삭제)
        pass
    except Exception as e:
        log_message(f"탭 변경 처리 중 오류: {e}", "error")

def check_and_fix_tabs():
    """탭 초기화 상태를 확인하고 수정"""
    # 보고서 탭에 대한 특별 처리 삭제
    pass

def force_recreate_report_tab():
    """보고서 탭 강제 재생성 (메뉴용)"""
    try:
        if notebook and len(notebook.tabs()) > 0:
            # 첫 번째 탭(보고서 탭) 선택
            tab_id = notebook.tabs()[0]
            tab_frame = notebook.nametowidget(tab_id)
            
            # 기존 위젯 모두 제거
            for widget in tab_frame.winfo_children():
                widget.destroy()
            
            # 보고서 탭 재생성
            from ui.report_tab import create_report_tab
            create_report_tab(tab_frame)
            
            # UI 강제 업데이트
            root.update_idletasks()
            
            log_message("보고서 탭 재생성 완료", "success")
            messagebox.showinfo("완료", "보고서 탭이 재생성되었습니다.\n(이 기능은 비활성화되었습니다)")
        else:
            log_message("노트북 또는 탭을 찾을 수 없음", "error")
            messagebox.showerror("오류", "탭을 찾을 수 없습니다.")
    except Exception as e:
        log_message(f"보고서 탭 강제 재생성 중 오류: {e}", "error")
        messagebox.showerror("오류", f"보고서 탭 재생성 중 오류가 발생했습니다:\n{str(e)}")

def get_version():
    """현재 버전 반환"""
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from main import VERSION
        return VERSION
    except ImportError:
        return "0.1.5"

def init_tabs():
    """탭 모듈들을 지연 로딩하여 초기화합니다"""
    global root, notebook
    
    try:
        # 각 탭 모듈 임포트하고 초기화
        tab_frames = notebook.winfo_children()
        if len(tab_frames) < 3:
            log_message("탭 프레임이 충분하지 않습니다.", "error")
            return
            
        try:
            # 1. 보고서 생성 탭 - 간단한 초기화만 수행
            log_message("보고서 생성 탭 초기화 시작", "info")
            from ui.report_tab import create_report_tab
            
            # 기존 위젯들 모두 제거
            for widget in tab_frames[0].winfo_children():
                widget.destroy()
                
            # 보고서 탭 생성 (비활성화 메시지)
            create_report_tab(tab_frames[0])
            log_message("보고서 생성 탭 초기화 완료", "info")
        except Exception as e:
            log_message(f"보고서 탭 초기화 오류: {e}", "error")
            ttk.Label(tab_frames[0], text=f"보고서 탭 기능이 비활성화되었습니다: {e}", foreground=WARNING_COLOR).pack(pady=20)
            
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
    
        # 채팅 탭(두 번째 탭) 강제 선택 및 표시
        notebook.select(1)
        root.update_idletasks()
        log_message("모든 탭 초기화 및 선택 완료", "info")
    
    except Exception as e:
        log_message(f"탭 초기화 중 오류 발생: {e}", "error")
        traceback.print_exc()

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
        
        # API 상태 업데이트
        update_api_status()
        
        # 프롬프트 상태 업데이트 - 마지막에 시도
        update_all_prompt_statuses()
        
    except Exception as e:
        log_message(f"새로고침 중 오류 발생: {str(e)}", "error")
        messagebox.showerror("시스템 오류", f"UI 새로고침 실패: {str(e)}")

def get_root():
    """현재 설정된 root 윈도우 반환"""
    global root
    return root

def get_notebook():
    """현재 설정된 notebook 객체 반환"""
    global notebook
    return notebook

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
        version = get_version()
    except:
        version = "0.1.5"
    
    ttk.Label(version_frame, text=f"Gemini 보고서 자동 생성기 v{version}", 
             font=("Arial", 12, "bold")).pack(side=tk.LEFT)
    
    # 연락처 정보
    ttk.Label(version_frame, text="© 2023-2025", font=("Arial", 9)).pack(side=tk.RIGHT)

def show_help():
    """도움말 표시"""
    if notebook:
        # 도움말 탭이 존재하는 경우 해당 탭 선택
        for i, tab_id in enumerate(notebook.tabs()):
            if i == 3:  # 도움말 탭은 일반적으로 4번째 탭
                notebook.select(i)
                return

if __name__ == "__main__":
    try:
        app = create_main_window()
        app.mainloop()
    except Exception as e:
        print(f"애플리케이션 초기화 오류: {e}")
        sys.exit(1)
