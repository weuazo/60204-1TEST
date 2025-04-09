import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import threading
from functools import partial

# 유틸리티 및 스타일 가져오기
from ui.ui_utils import (
    show_active_prompts, log_message, create_tooltip, 
    PRIMARY_COLOR, SECONDARY_COLOR, BG_COLOR, CARD_COLOR, TEXT_COLOR, 
    SUCCESS_COLOR, WARNING_COLOR, ERROR_COLOR, BORDER_COLOR, HOVER_COLOR
)

# API 및 채팅 컨텍스트 모듈
from api.gemini import call_gemini_with_prompts
from utils import chat_context

def create_chat_tab(parent):
    """채팅 탭 구성"""
    # 메인 프레임
    main_frame = ttk.Frame(parent, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 제목 및 설명
    ttk.Label(
        main_frame, 
        text="AI 채팅 어시스턴트", 
        font=("Arial", 16, "bold"),
        foreground=PRIMARY_COLOR
    ).pack(anchor="w", pady=(0, 10))
    
    ttk.Label(
        main_frame,
        text="기술 문서 검토 관련 질문에 AI가 답변해드립니다. 보고서 내용이나 규격 정보에 대해 물어보세요.",
        wraplength=800
    ).pack(fill=tk.X, pady=(0, 20))
    
    # 채팅 및 입력 영역을 위한 프레임
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(fill=tk.BOTH, expand=True)
    
    # 채팅 표시 영역과 스크롤바
    chat_frame = ttk.Frame(content_frame)
    chat_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
    
    chat_scrollbar = ttk.Scrollbar(chat_frame)
    chat_scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
    
    chat_display = scrolledtext.ScrolledText(
        chat_frame,
        wrap=tk.WORD,
        width=80,
        height=15,
        font=("Arial", 10),
        background="#FFFFFF",
        foreground=TEXT_COLOR,
        padx=10,
        pady=10,
        borderwidth=1,
        relief="solid",
        state=tk.DISABLED,
        yscrollcommand=chat_scrollbar.set
    )
    chat_display.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    chat_scrollbar.config(command=chat_display.yview)
    
    # 채팅 스타일 설정
    chat_display.tag_configure("user", foreground="#0066CC", font=("Arial", 10, "bold"))
    chat_display.tag_configure("assistant", foreground="#006633", font=("Arial", 10))
    chat_display.tag_configure("system", foreground="#666666", font=("Arial", 9, "italic"))
    chat_display.tag_configure("error", foreground=ERROR_COLOR)
    chat_display.tag_configure("info", foreground=PRIMARY_COLOR)
    
    # 초기 안내 메시지
    show_welcome_message(chat_display)
    
    # 입력 영역과 버튼 컨테이너
    input_container = ttk.Frame(content_frame)
    input_container.pack(fill=tk.X, pady=(10, 0))
    
    # 프롬프트 선택 및 컨텍스트 정보
    control_frame = ttk.Frame(input_container)
    control_frame.pack(fill=tk.X, pady=(0, 5))
    
    # 컨텍스트 상태 표시
    context_frame = ttk.Frame(control_frame)
    context_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    context_status = ttk.Label(
        context_frame, 
        text="컨텍스트: 없음", 
        font=("Arial", 9),
        foreground="#666666"
    )
    context_status.pack(side=tk.LEFT)
    create_tooltip(context_status, "현재 로드된 파일 컨텍스트가 표시됩니다.")
    
    # 컨텍스트 표시 버튼
    show_context_btn = ttk.Button(
        context_frame, 
        text="컨텍스트 보기", 
        command=lambda: show_context_in_chat(chat_display),
        width=14
    )
    show_context_btn.pack(side=tk.LEFT, padx=(5, 0))
    
    # 프롬프트 설정 영역 (변경됨)
    prompt_frame = ttk.Frame(control_frame)
    prompt_frame.pack(side=tk.RIGHT)
    
    # 자동 적용된 프롬프트 표시
    selected_prompts_var = tk.StringVar(value="자동 적용중: 없음")
    selected_prompts_label = ttk.Label(
        prompt_frame,
        textvariable=selected_prompts_var,
        font=("Arial", 9),
        foreground=SUCCESS_COLOR
    )
    selected_prompts_label.pack(side=tk.LEFT, padx=(0, 10))
    
    # 프롬프트 관리 버튼
    manage_prompts_btn = ttk.Button(
        prompt_frame,
        text="프롬프트 관리",
        command=lambda: open_prompt_tab(),
        width=12
    )
    manage_prompts_btn.pack(side=tk.RIGHT)
    
    # 입력 영역 프레임
    entry_frame = ttk.Frame(input_container)
    entry_frame.pack(fill=tk.X, expand=True)
    
    # 텍스트 입력 영역
    entry_box = scrolledtext.ScrolledText(
        entry_frame,
        wrap=tk.WORD,
        width=70,
        height=3,
        font=("Arial", 10),
        padx=10,
        pady=5,
        borderwidth=1,
        relief="solid"
    )
    entry_box.pack(fill=tk.X, side=tk.LEFT, expand=True)
    
    # 입력 안내 텍스트
    entry_box.insert(tk.END, "여기에 질문을 입력하세요...")
    entry_box.bind("<FocusIn>", lambda e: clear_placeholder(entry_box, "여기에 질문을 입력하세요..."))
    entry_box.bind("<FocusOut>", lambda e: restore_placeholder(entry_box, "여기에 질문을 입력하세요..."))
    
    # 엔터 키 바인딩
    entry_box.bind("<Return>", lambda e: handle_enter_key(e, entry_box, chat_display, selected_prompts_var))
    entry_box.bind("<Shift-Return>", lambda e: None)  # Shift+Enter는 줄바꿈만
    
    # 전송 버튼
    send_btn = ttk.Button(
        entry_frame,
        text="전송",
        command=lambda: handle_chat_input(entry_box, chat_display, selected_prompts_var),
        width=8
    )
    send_btn.pack(side=tk.RIGHT, padx=(10, 0))
    
    # 하단 버튼 영역
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(10, 0))
    
    # 채팅 초기화 버튼
    clear_btn = ttk.Button(
        button_frame,
        text="대화 초기화",
        command=lambda: reset_chat(chat_display),
        width=12
    )
    clear_btn.pack(side=tk.LEFT)
    
    # 도움말
    help_text = ttk.Label(
        button_frame, 
        text="TIP: Enter 키로 메시지 전송, Shift+Enter로 줄바꿈",
        font=("Arial", 9),
        foreground="#666666"
    )
    help_text.pack(side=tk.RIGHT)
    
    # 컨텍스트 상태 업데이트 초기화
    update_context_status(context_status)
    
    # 주기적으로 컨텍스트 상태 업데이트
    update_context_periodically(context_status)
    
    # 자동으로 선택된 프롬프트 상태 업데이트
    update_selected_prompts(selected_prompts_var)
    
    return main_frame

def show_welcome_message(chat_display):
    """웰컴 메시지 표시"""
    chat_display.config(state=tk.NORMAL)
    chat_display.insert(tk.END, "🤖 AI 어시스턴트에 오신 것을 환영합니다!\n", "system")
    chat_display.insert(tk.END, "기술 문서 검토와 관련된 질문에 답변해드립니다. 아래와 같은 질문을 해보세요:\n", "system")
    chat_display.insert(tk.END, "- 규격 요구사항에 대해 설명해주세요\n", "info")
    chat_display.insert(tk.END, "- 이 테스트 결과가 적합한지 확인해주세요\n", "info")
    chat_display.insert(tk.END, "- 검토 의견 작성에 도움이 필요해요\n\n", "info")
    
    # 파일 컨텍스트가 있는지 확인하고 안내
    from utils import chat_context
    if chat_context.has_any_context():
        context_summary = chat_context.get_context_summary()
        if context_summary:
            chat_display.insert(tk.END, "📁 현재 로드된 컨텍스트 정보가 있습니다:\n", "system")
            for file_type, info in context_summary.items():
                if info.get('loaded', False):
                    chat_display.insert(tk.END, f"- {info.get('description', file_type)}\n", "info")
            chat_display.insert(tk.END, "컨텍스트에 대해 질문하시거나 '컨텍스트 보기' 버튼을 눌러 상세 정보를 확인하세요.\n\n", "system")
    else:
        chat_display.insert(tk.END, "📂 현재 로드된 파일 컨텍스트가 없습니다. 파일을 업로드하거나 엑셀 시트를 선택하면 더 정확한 답변을 받을 수 있습니다.\n\n", "system")
    
    chat_display.config(state=tk.DISABLED)
    chat_display.see(tk.END)

def show_context_in_chat(chat_display):
    """현재 컨텍스트 정보를 채팅 화면에 표시"""
    # 채팅창에 메시지 표시
    chat_display.config(state=tk.NORMAL)
    chat_display.insert(tk.END, "🔍 현재 컨텍스트 정보:\n", "system")
    
    try:
        # 컨텍스트 모듈에서 컨텍스트 정보 가져오기
        from utils import chat_context
        context_summary = chat_context.get_context_summary()
        
        if not context_summary or not any(info.get('loaded', False) for info in context_summary.values()):
            chat_display.insert(tk.END, "현재 로드된 컨텍스트 정보가 없습니다.\n\n", "system")
        else:
            # 각 컨텍스트 정보 표시
            for file_type, info in context_summary.items():
                if info.get('loaded', False):
                    chat_display.insert(tk.END, f"📄 {info.get('description', file_type)}:\n", "info")
                    
                    # 파일 정보 표시
                    file_info = info.get('file_info', {})
                    if file_info:
                        for key, value in file_info.items():
                            if value:
                                chat_display.insert(tk.END, f"- {key}: {value}\n", "system")
                    
                    # 내용 요약 표시
                    content_summary = info.get('content_summary', '')
                    if content_summary:
                        chat_display.insert(tk.END, f"{content_summary}\n", "system")
                    
                    chat_display.insert(tk.END, "\n", "system")
            
            # 분석 정보 표시
            try:
                analysis = chat_context.get_context_analysis_summary()
                if analysis and analysis.get('analysis_available'):
                    chat_display.insert(tk.END, "📊 컨텍스트 분석 정보:\n", "info")
                    
                    # 엑셀 분석 정보
                    if analysis['analysis_available'].get('review_sheet', False):
                        excel_analysis = chat_context._cached_file_analysis.get('review_sheet', {})
                        if excel_analysis:
                            chat_display.insert(tk.END, f"- 검토 시트 항목 수: {excel_analysis.get('clause_count', '알 수 없음')}\n", "system")
                            if excel_analysis.get('has_standard_structure'):
                                chat_display.insert(tk.END, "- 표준 구조 (예: 1.2.3 형식)가 감지됨\n", "system")
                    
                    chat_display.insert(tk.END, "\n", "system")
            except Exception as e:
                log_message(f"분석 정보 표시 중 오류: {str(e)}", "error")
    
    except Exception as e:
        chat_display.insert(tk.END, f"컨텍스트 정보를 가져오는 중 오류가 발생했습니다: {str(e)}\n\n", "error")
        log_message(f"컨텍스트 정보 조회 오류: {str(e)}", "error")
    
    chat_display.insert(tk.END, "컨텍스트 정보에 대해 질문하세요. 예: '검토 시트의 주요 항목을 요약해줘'\n\n", "system")
    chat_display.config(state=tk.DISABLED)
    chat_display.see(tk.END)

def handle_chat_input(entry_box, chat_display, selected_prompts_var=None):
    """채팅 입력 처리"""
    # 사용자 입력 가져오기
    user_input = entry_box.get("1.0", tk.END).strip()
    
    # 입력이 없거나 기본 안내 메시지인 경우 무시
    if not user_input or user_input == "여기에 질문을 입력하세요...":
        return
        
    # 사용자 입력을 채팅창에 표시
    chat_display.config(state=tk.NORMAL)
    chat_display.insert(tk.END, f"👤 나: {user_input}\n", "user")
    chat_display.see(tk.END)
    chat_display.config(state=tk.DISABLED)
    
    # 입력 필드 초기화
    entry_box.delete("1.0", tk.END)
    
    # 응답 생성 중 표시
    chat_display.config(state=tk.NORMAL)
    chat_display.insert(tk.END, "🤖 AI: 응답 생성 중...\n", "system")
    chat_display.see(tk.END)
    chat_display.config(state=tk.DISABLED)
    
    # 자동으로 적용된 프롬프트 가져오기
    selected_prompts = get_auto_selected_prompts()
    
    # 백그라운드에서 AI 응답 생성
    threading.Thread(
        target=generate_ai_response,
        args=(user_input, chat_display, selected_prompts),
        daemon=True
    ).start()

def generate_ai_response(user_input, chat_display, selected_prompts=None):
    """백그라운드에서 AI 응답 생성"""
    try:
        # API 호출
        if selected_prompts:
            response = call_gemini_with_prompts(user_input, selected_prompts)
        else:
            response = call_gemini_with_prompts(user_input, [])
        
        # 응답이 없는 경우 처리
        if not response or not response.strip():
            response = "죄송합니다, 응답을 생성할 수 없었습니다. 다시 시도해주세요."
        
        # 현재 스레드가 메인 스레드가 아닌 경우, 메인 스레드에서 UI 업데이트
        if threading.current_thread() != threading.main_thread():
            # 구현 방식에 따라 다름 - tkinter는 thread safe하지 않음
            from ui.gui_main import get_root
            root = get_root()
            if root:
                root.after(0, partial(update_chat_display, chat_display, response))
            else:
                update_chat_display(chat_display, response)
        else:
            update_chat_display(chat_display, response)
            
    except Exception as e:
        error_message = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
        log_message(error_message, "error")
        
        # UI 업데이트
        from ui.gui_main import get_root
        root = get_root()
        if root:
            root.after(0, partial(update_chat_display, chat_display, f"오류: {error_message}"))
        else:
            update_chat_display(chat_display, f"오류: {error_message}")

def update_chat_display(chat_display, response):
    """채팅 화면에 응답 업데이트"""
    if not chat_display:
        return
        
    # 임시 '응답 생성 중...' 메시지 제거
    chat_display.config(state=tk.NORMAL)
    
    # 마지막 줄이 시스템 메시지인 경우 삭제
    last_line_start = chat_display.index("end-2l linestart")
    last_line = chat_display.get(last_line_start, "end-1c")
    
    if "응답 생성 중..." in last_line:
        chat_display.delete(last_line_start, "end-1c")
    
    # 응답 추가
    chat_display.insert(tk.END, f"🤖 AI: {response}\n\n", "assistant")
    chat_display.see(tk.END)
    chat_display.config(state=tk.DISABLED)

def reset_chat(chat_display):
    """채팅 내용 초기화"""
    if messagebox.askyesno("확인", "채팅 내용을 모두 지우시겠습니까?"):
        chat_display.config(state=tk.NORMAL)
        chat_display.delete("1.0", tk.END)
        chat_display.config(state=tk.DISABLED)
        
        # 채팅 컨텍스트 초기화
        from utils import chat_context
        chat_context.clear_chat_history()
        
        # 웰컴 메시지 다시 표시
        show_welcome_message(chat_display)
        log_message("채팅 내용이 초기화되었습니다.", "info")

def select_chat_prompts(selected_prompts_var):
    """채팅용 프롬프트 선택 대화상자 표시"""
    # 프롬프트 선택 대화상자 표시
    selected = show_active_prompts("chat")
    
    # 선택된 프롬프트 표시
    if selected:
        prompt_names = [p["name"] for p in selected]
        if prompt_names:
            selected_prompts_var.set(f"선택된 프롬프트: {', '.join(prompt_names)}")
        else:
            selected_prompts_var.set("선택된 프롬프트: 없음")
    else:
        selected_prompts_var.set("선택된 프롬프트: 없음")

def handle_enter_key(event, entry_box, chat_display, selected_prompts_var):
    """엔터 키 처리"""
    # Shift+Enter가 아닌 경우에만 전송
    if not event.state & 0x1:  # Shift 키가 눌리지 않은 경우
        handle_chat_input(entry_box, chat_display, selected_prompts_var)
        return "break"  # 이벤트 전파 방지

def clear_placeholder(entry_box, placeholder):
    """입력 필드 플레이스홀더 제거"""
    if entry_box.get("1.0", tk.END).strip() == placeholder:
        entry_box.delete("1.0", tk.END)

def restore_placeholder(entry_box, placeholder):
    """입력 필드 플레이스홀더 복원"""
    if not entry_box.get("1.0", tk.END).strip():
        entry_box.insert("1.0", placeholder)

def update_context_status(status_label):
    """컨텍스트 상태 표시 업데이트"""
    try:
        from utils import chat_context
        
        # 컨텍스트 요약 정보 가져오기
        context_summary = chat_context.get_context_summary()
        
        if not context_summary or not any(info.get('loaded', False) for info in context_summary.values()):
            status_label.config(text="컨텍스트: 없음", foreground="#666666")
            return
            
        # 로드된 컨텍스트 개수
        loaded_count = sum(1 for info in context_summary.values() if info.get('loaded', False))
        
        context_types = []
        for file_type, info in context_summary.items():
            if info.get('loaded', False):
                short_name = {
                    'review_sheet': '검토시트',
                    'base_template': '템플릿',
                    'report': '보고서',
                    'pdf_document': 'PDF'
                }.get(file_type, file_type)
                
                context_types.append(short_name)
        
        if context_types:
            status_text = f"컨텍스트: {', '.join(context_types)}"
            status_label.config(text=status_text, foreground=SUCCESS_COLOR)
        else:
            status_label.config(text="컨텍스트: 없음", foreground="#666666")
            
    except Exception as e:
        status_label.config(text=f"컨텍스트: 오류", foreground=ERROR_COLOR)
        log_message(f"컨텍스트 상태 업데이트 중 오류: {str(e)}", "error")

def update_context_periodically(status_label):
    """주기적으로 컨텍스트 상태 업데이트"""
    update_context_status(status_label)
    
    # 1초마다 상태 업데이트
    from ui.gui_main import get_root
    root = get_root()
    if root:
        root.after(1000, lambda: update_context_periodically(status_label))

def get_auto_selected_prompts():
    """프롬프트 관리 탭에서 채팅용으로 체크된 프롬프트 자동 가져오기"""
    selected_prompts = []
    
    try:
        # 프롬프트 폴더 확인
        if not os.path.exists("prompts"):
            return []
        
        # 프롬프트 파일 로드 및 채팅용 필터링
        for file in os.listdir("prompts"):
            if not file.endswith(".json"):
                continue
                
            try:
                with open(os.path.join("prompts", file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # types 필드가 배열인지 확인 (하위 호환성)
                    types = data.get("type", [])
                    if not isinstance(types, list):
                        types = [types]
                    
                    # 채팅용 프롬프트인지 확인
                    if "chat" in types:
                        prompt_name = data.get("prompt_name", file[:-5])
                        selected_prompts.append({
                            "name": prompt_name,
                            "template": data.get("template", ""),
                            "priority": data.get("priority", 10)
                        })
            except:
                # 오류 파일 무시
                pass
        
        # 우선순위로 정렬 (낮은 번호가 먼저)
        selected_prompts.sort(key=lambda x: x.get("priority", 10))
        
    except Exception as e:
        print(f"프롬프트 로드 중 오류: {e}")
    
    return selected_prompts

def update_selected_prompts(selected_prompts_var):
    """자동 적용된 프롬프트 상태 표시 업데이트"""
    try:
        prompts = get_auto_selected_prompts()
        
        if prompts:
            # 이름만 추출하여 문자열로 결합
            names = [p["name"] for p in prompts]
            selected_prompts_var.set(f"자동 적용중: {', '.join(names)}")
        else:
            selected_prompts_var.set("자동 적용중: 없음")
            
        # 주기적으로 업데이트 (5초마다)
        from ui.gui_main import get_root
        root = get_root()
        if root:
            root.after(5000, lambda: update_selected_prompts(selected_prompts_var))
            
    except Exception as e:
        print(f"프롬프트 상태 업데이트 오류: {e}")

def open_prompt_tab():
    """프롬프트 관리 탭으로 이동"""
    # 프롬프트 탭으로 포커스 이동
    from ui.ui_utils import select_prompt_tab
    select_prompt_tab()
