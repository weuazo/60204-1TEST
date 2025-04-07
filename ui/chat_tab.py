import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
from ui.ui_utils import show_active_prompts, log_message  # log_message 추가

# UI 테마 및 색상 가져오기
from ui.ui_utils import (
    PRIMARY_COLOR, SECONDARY_COLOR, BG_COLOR, CARD_COLOR, TEXT_COLOR, 
    SUCCESS_COLOR, WARNING_COLOR, ERROR_COLOR, BORDER_COLOR, HOVER_COLOR
)

def create_chat_tab(parent):
    """채팅 탭 구성"""
    # 동적 임포트 - 필요할 때만
    try:
        from utils.prompt_loader import load_prompts_by_type
    except ImportError:
        log_message("프롬프트 로더 모듈을 불러올 수 없습니다", "error")
        messagebox.showerror("모듈 오류", "프롬프트 로더 모듈을 불러올 수 없습니다.")
        return

    # 채팅 영역 프레임
    chat_container = ttk.Frame(parent)
    chat_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    # 채팅 설정 영역 (프롬프트 요약으로 변경)
    settings_card = ttk.Frame(chat_container, style="Card.TFrame")
    settings_card.pack(fill=tk.X, pady=(0, 10))
    
    settings_header = ttk.Frame(settings_card)
    settings_header.pack(fill=tk.X, padx=15, pady=(15, 5))
    
    ttk.Label(settings_header, text="AI 채팅 설정", style="Subtitle.TLabel").pack(side=tk.LEFT)
    
    # 프롬프트 상태 표시 버튼
    view_chat_prompts_btn = ttk.Button(
        settings_header, 
        text="적용된 프롬프트 보기",
        command=lambda: show_active_prompts("chat")
    )
    view_chat_prompts_btn.pack(side=tk.RIGHT, padx=5)
    
    # 프롬프트 안내 영역
    prompt_select_frame = ttk.Frame(settings_card)
    prompt_select_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
    
    # 프롬프트 안내 메시지
    prompt_info = ttk.Label(
        prompt_select_frame,
        text="프롬프트는 '프롬프트 관리' 탭에서 관리할 수 있습니다.\n" +
             "'채팅' 유형으로 설정된 프롬프트만 이 기능에 적용됩니다.",
        wraplength=600,
        padding=(0, 5)
    )
    prompt_info.pack(fill=tk.X)
    
    # 프롬프트 상태 표시
    chat_prompt_status = ttk.Label(
        prompt_select_frame,
        text="현재 적용됨: 프롬프트 0개",
        padding=5
    )
    chat_prompt_status.pack(fill=tk.X)
    
    # 프롬프트 상태 업데이트 함수
    def update_chat_prompt_status():
        """채팅 프롬프트 상태 업데이트 함수"""
        try:
            from utils.prompt_loader import load_prompts_by_type
            
            prompts = load_prompts_by_type("chat", as_dict=True, include_metadata=True)
            count = len(prompts)
            
            if 'chat_prompt_status' in globals() and chat_prompt_status:
                try:
                    chat_prompt_status.config(
                        text=f"현재 적용됨: 프롬프트 {count}개",
                        foreground=SUCCESS_COLOR if count > 0 else WARNING_COLOR
                    )
                except tk.TclError:
                    print("채팅 프롬프트 상태 위젯이 더 이상 유효하지 않습니다.")
        except Exception as e:
            print(f"채팅 프롬프트 상태 업데이트 오류: {e}")
    
    # 초기 상태 업데이트
    try:
        update_chat_prompt_status()
    except Exception as e:
        print(f"초기 채팅 프롬프트 상태 업데이트 오류: {e}")
    
    # 채팅 표시 영역
    chat_display_card = ttk.Frame(chat_container, style="Card.TFrame")
    chat_display_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    chat_header = ttk.Frame(chat_display_card)
    chat_header.pack(fill=tk.X, padx=15, pady=(15, 5))
    
    ttk.Label(chat_header, text="AI와 대화하기", style="Title.TLabel").pack(side=tk.LEFT)
    
    chat_area = ttk.Frame(chat_display_card)
    chat_area.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
    
    chat_display = scrolledtext.ScrolledText(chat_area, wrap=tk.WORD)
    chat_display.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # 스타일 설정
    chat_display.tag_configure("user", foreground="#0066cc", font=("Arial", 10, "bold"))
    chat_display.tag_configure("bot", foreground="#006633")
    chat_display.tag_configure("system", foreground="#666666", font=("Arial", 9, "italic"))
    
    # 시스템 메시지
    chat_display.insert(tk.END, "💬 AI 어시스턴트와 대화를 시작합니다.\n", "system")
    chat_display.insert(tk.END, "💡 질문이나 요청 사항을 아래에 입력하세요.\n\n", "system")
    chat_display.config(state=tk.DISABLED)
    
    # 입력 영역
    input_card = ttk.Frame(chat_container, style="Card.TFrame")
    input_card.pack(fill=tk.X, pady=10)
    
    input_area = ttk.Frame(input_card)
    input_area.pack(fill=tk.X, padx=15, pady=15)
    
    chat_entry = scrolledtext.ScrolledText(input_area, height=4, wrap=tk.WORD)
    chat_entry.pack(fill=tk.X, pady=(0, 10))
    
    button_frame = ttk.Frame(input_area)
    button_frame.pack(fill=tk.X)
    
    clear_btn = ttk.Button(
        button_frame, 
        text="대화 초기화", 
        command=lambda: reset_chat(chat_display)
    )
    clear_btn.pack(side=tk.LEFT)
    
    send_btn = ttk.Button(
        button_frame, 
        text="전송", 
        command=lambda: handle_chat_input(chat_entry, chat_display),
        style="Primary.TButton"
    )
    send_btn.pack(side=tk.RIGHT)
    
    # 단축키 바인딩 (Ctrl+Enter)
    def on_ctrl_enter(event):
        if event.state & 0x4 and event.keysym == "Return":
            handle_chat_input(chat_entry, chat_display)
            return "break"
    
    chat_entry.bind("<Key>", on_ctrl_enter)

def handle_chat_input(entry_box, chat_display):
    """채팅 입력 처리"""
    user_input = entry_box.get("1.0", tk.END).strip()
    if not user_input:
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
    
    # 백그라운드 처리를 위한 업데이트
    from ui.gui_main import get_root
    
    root = get_root()
    if root:
        root.update_idletasks()
    
    # 동적 임포트로 순환 참조 방지
    from utils.prompt_loader import load_prompts_by_type
    from api.gemini import call_gemini_with_prompts
    
    # 선택된 프롬프트들 가져오기 (이제 프롬프트 관리에서 설정한 chat 유형 모두 사용)
    try:
        # 프롬프트 개수 확인
        prompts = load_prompts_by_type("chat", as_dict=True, include_metadata=True)
        prompt_names = list(prompts.keys())
        
        # 선택된 프롬프트가 있다면 정보 표시
        if prompt_names:
            chat_display.config(state=tk.NORMAL)
            chat_display.delete("end-2l", "end-1l")  # '응답 생성 중' 메시지 삭제
            count_text = f"{len(prompt_names)}개 프롬프트" if len(prompt_names) > 1 else "1개 프롬프트"
            chat_display.insert(tk.END, f"🤖 AI: [{count_text} 적용] 응답 생성 중...\n", "system")
            chat_display.see(tk.END)
            chat_display.config(state=tk.DISABLED)
            root.update_idletasks()
        
        reply = call_gemini_with_prompts(user_input, prompt_names)
        
        # 이전 '응답 생성 중' 메시지 삭제
        chat_display.config(state=tk.NORMAL)
        chat_display.delete("end-2l", "end-1l")
        
        # 실제 응답 표시
        chat_display.insert(tk.END, f"🤖 AI: {reply}\n\n", "bot")
        chat_display.see(tk.END)
        chat_display.config(state=tk.DISABLED)
    except Exception as e:
        # 오류 메시지 표시
        chat_display.config(state=tk.NORMAL)
        chat_display.delete("end-2l", "end-1l")  # '응답 생성 중' 메시지 삭제
        chat_display.insert(tk.END, f"❌ 오류: {str(e)}\n\n", "error")
        chat_display.see(tk.END)
        chat_display.config(state=tk.DISABLED)

def reset_chat(chat_display):
    """채팅 내용 초기화"""
    chat_display.config(state=tk.NORMAL)
    chat_display.delete("1.0", tk.END)
    chat_display.insert(tk.END, "💬 AI 어시스턴트와 대화를 시작합니다.\n", "system")
    chat_display.insert(tk.END, "💡 질문이나 요청 사항을 아래에 입력하세요.\n\n", "system")
    chat_display.config(state=tk.DISABLED)
