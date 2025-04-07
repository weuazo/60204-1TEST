import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import sys

# UI 테마 및 색상 상수 정의
PRIMARY_COLOR = "#3498db"
SECONDARY_COLOR = "#2980b9"
BG_COLOR = "#f5f5f5"
CARD_COLOR = "#ffffff"
TEXT_COLOR = "#333333"
SUCCESS_COLOR = "#2ecc71"
WARNING_COLOR = "#f39c12"
ERROR_COLOR = "#e74c3c"
BORDER_COLOR = "#dcdde1"
HOVER_COLOR = "#ecf0f1"

# 전역 변수
root = None
log_box = None

def set_root(root_window):
    """메인 창 레퍼런스 설정"""
    global root
    root = root_window

def set_log_box(log_text_widget):
    """로그 박스 레퍼런스 설정"""
    global log_box
    log_box = log_text_widget

def log_message(message, tag=None):
    """로그 메시지 추가"""
    global log_box
    
    # 콘솔에 출력
    print(f"[{tag or 'INFO'}] {message}")
    
    # GUI 로그 상자에 추가 (있을 경우)
    if log_box:
        try:
            log_box.config(state=tk.NORMAL)
            log_box.insert(tk.END, f"{message}\n", tag if tag else "")
            log_box.see(tk.END)
            log_box.config(state=tk.DISABLED)
        except tk.TclError:
            # 위젯이 이미 소멸되었거나 유효하지 않은 경우
            pass

def show_api_key_dialog():
    """API 키 설정 다이얼로그"""
    global root
    
    if not root:
        print("오류: root 창이 설정되지 않았습니다.")
        return
        
    current_key = os.environ.get("GEMINI_API_KEY", "")
    
    dialog = tk.Toplevel(root)
    dialog.title("API 키 설정")
    dialog.geometry("500x200")
    dialog.transient(root)
    dialog.grab_set()
    
    # 중앙 배치
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f'{width}x{height}+{x}+{y}')
    
    # 내용 구성
    frame = ttk.Frame(dialog, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="Gemini API 키를 입력하세요:", font=("Arial", 12)).pack(anchor="w", pady=(0, 10))
    
    key_entry = ttk.Entry(frame, width=50, show="•")
    key_entry.pack(fill=tk.X, pady=5)
    key_entry.insert(0, current_key)
    
    # 키 표시/숨기기 체크박스
    show_var = tk.BooleanVar(value=False)
    
    def toggle_show_key():
        if show_var.get():
            key_entry.config(show="")
        else:
            key_entry.config(show="•")
    
    show_check = ttk.Checkbutton(frame, text="API 키 표시", variable=show_var, command=toggle_show_key)
    show_check.pack(anchor="w", pady=5)
    
    info_text = ttk.Label(
        frame, 
        text="API 키는 환경변수로 저장되며 앱 재시작 시 다시 설정해야 합니다.\n" + 
             "https://makersuite.google.com/app/apikey에서 키를 발급받을 수 있습니다.",
        wraplength=450,
        foreground="#666666",
        font=("Arial", 9),
        justify="left"
    )
    info_text.pack(fill=tk.X, pady=10)
    
    # 버튼 영역
    button_frame = ttk.Frame(frame)
    button_frame.pack(fill=tk.X, pady=(10, 0))
    
    def save_api_key():
        key = key_entry.get().strip()
        if key:
            os.environ["GEMINI_API_KEY"] = key
            # 헤더 API 상태 업데이트
            update_api_status()
            messagebox.showinfo("성공", "API 키가 설정되었습니다.")
            dialog.destroy()
        else:
            messagebox.showwarning("입력 오류", "API 키를 입력하세요.")
    
    cancel_btn = ttk.Button(button_frame, text="취소", command=dialog.destroy)
    cancel_btn.pack(side=tk.RIGHT)
    
    save_btn = ttk.Button(button_frame, text="저장", command=save_api_key)
    save_btn.pack(side=tk.RIGHT, padx=5)
    
    # 링크 클릭 처리
    def open_api_link(event):
        import webbrowser
        webbrowser.open("https://makersuite.google.com/app/apikey")
    
    info_text.bind("<Button-1>", open_api_link)
    info_text.config(cursor="hand2")

def update_api_status():
    """헤더의 API 상태 표시 업데이트"""
    global root
    
    if not root:
        return
        
    try:    
        # 헤더 프레임 찾기
        for widget in root.winfo_children():
            if isinstance(widget, tk.Frame) and widget.winfo_height() <= 70:
                header_frame = widget
                
                # API 프레임 찾기
                for child in header_frame.winfo_children():
                    if isinstance(child, tk.Frame):
                        for api_widget in child.winfo_children():
                            if isinstance(api_widget, tk.Label) and "API" in api_widget.cget("text"):
                                # API 상태 업데이트
                                api_status_text = "API 연결됨 ✓" if os.environ.get("GEMINI_API_KEY") else "API 연결 안됨 ⚠️"
                                api_widget.config(text=api_status_text)
                                break
    except Exception as e:
        print(f"API 상태 업데이트 중 오류: {e}")

def show_active_prompts(prompt_type):
    """활성화된 프롬프트 목록을 보여주는 대화상자"""
    global root
    
    if not root:
        return
    
    try:
        # 이 함수 내에서만 필요할 때 임포트
        from utils.prompt_loader import load_prompts_by_type
        
        # 프롬프트 유형에 따른 제목 설정
        if prompt_type == "chat":
            title = "채팅 프롬프트"
            description = "현재 채팅에 적용되는 프롬프트"
        else:
            title = "보고서 생성 프롬프트"
            description = "현재 보고서 생성에 적용되는 프롬프트"
        
        # 프롬프트 데이터 로드
        prompts_data = load_prompts_by_type(prompt_type, as_dict=True, include_metadata=True)
        
        if not prompts_data:
            messagebox.showinfo(
                title, 
                f"현재 '{title}'에 적용된 프롬프트가 없습니다.\n\n" +
                "프롬프트 관리 탭에서 프롬프트를 추가하고 유형을 설정해주세요."
            )
            return
            
        # 프롬프트 이름만 표시하는 간소화된 대화상자
        dialog = tk.Toplevel(root)
        dialog.title(f"적용된 {title}")
        dialog.geometry("400x350")
        dialog.transient(root)
        
        # 중앙 배치
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # 컨텐츠 프레임
        content = ttk.Frame(dialog, padding=15)
        content.pack(fill=tk.BOTH, expand=True)
        
        # 헤더
        ttk.Label(
            content, 
            text=description, 
            font=("Arial", 14, "bold"), 
            foreground=PRIMARY_COLOR
        ).pack(anchor="w", pady=(0, 10))
        
        # 안내 메시지
        ttk.Label(
            content,
            text=f"다음 프롬프트들이 {title}에 적용됩니다.\n프롬프트는 우선순위 숫자가 작은 것부터 적용됩니다.",
            wraplength=350,
            justify="left"
        ).pack(anchor="w", pady=(0, 10))
        
        # 프롬프트 목록을 표시할 리스트박스
        list_frame = ttk.Frame(content)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        listbox = tk.Listbox(
            list_frame,
            font=("Arial", 10),
            selectbackground=PRIMARY_COLOR,
            selectforeground="white",
            height=15
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 프롬프트를 우선순위로 정렬
        sorted_prompts = sorted(prompts_data.items(), key=lambda x: x[1].get('priority', 999))
        
        # 프롬프트 이름과 우선순위만 표시
        for name, data in sorted_prompts:
            priority = data.get('priority', 999)
            # 아이콘 추가 (우선순위와 함께)
            if prompt_type == "chat":
                icon = "💬"
            else:  # remark
                icon = "📊"
            # 순서를 더 명확하게 표시
            ordinal = f"{sorted_prompts.index((name, data))+1}번째 적용"
            listbox.insert(tk.END, f"{priority:02d} | {icon} {name} ({ordinal})")
        
        # 프롬프트 관리 바로가기 버튼
        manage_btn = ttk.Button(
            content,
            text="프롬프트 관리",
            command=lambda: [dialog.destroy(), select_prompt_tab()]
        )
        manage_btn.pack(side=tk.LEFT, pady=10)
        
        # 닫기 버튼
        close_btn = ttk.Button(
            content, 
            text="닫기", 
            command=dialog.destroy
        )
        close_btn.pack(side=tk.RIGHT, pady=10)
    except ImportError as e:
        print(f"프롬프트 로더 모듈을 임포트할 수 없습니다: {e}")
        messagebox.showerror("모듈 오류", "프롬프트 로더 모듈을 임포트할 수 없습니다.")
    except Exception as e:
        print(f"프롬프트 목록 표시 오류: {e}")
        messagebox.showerror("오류", f"프롬프트 목록을 표시하는 중 오류가 발생했습니다: {e}")

def select_prompt_tab():
    """프롬프트 관리 탭으로 전환"""
    global root
    
    if not root:
        return
        
    try:
        # notebook은 전역 변수로 정의되어 있지 않아 찾아야 함
        for widget in root.winfo_children():
            if isinstance(widget, tk.Frame):  # content_frame 찾기
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Notebook):  # notebook 찾기
                        child.select(2)  # 프롬프트 탭(인덱스 2)
                        return True
    except Exception as e:
        print(f"탭 전환 중 오류: {e}")
    return False

def update_all_prompt_statuses():
    """모든 탭의 프롬프트 상태 업데이트"""
    global root
    
    if not root:
        return
        
    try:    
        # 각 탭에 정의된 업데이트 함수 찾기
        for widget in root.winfo_children():
            if isinstance(widget, tk.Frame):  # content_frame 찾기
                for notebook in widget.winfo_children():
                    if isinstance(notebook, ttk.Notebook):
                        # 각 탭의 프레임 순회
                        try:
                            for tab_id in range(notebook.index("end")):
                                tab = notebook.winfo_children()[tab_id]
                                
                                # 보고서 탭의 업데이트 함수 찾기 
                                if tab_id == 0:  # 보고서 탭
                                    for frame in find_widgets_by_class(tab, ttk.LabelFrame):
                                        if hasattr(frame, 'cget') and frame.cget("text") == "프롬프트 설정":
                                            for label in find_widgets_by_class(frame, ttk.Label):
                                                if hasattr(label, 'cget') and label.cget("text").startswith("현재 적용됨:"):
                                                    update_label_with_prompt_count(label, "remark")
                                
                                # 채팅 탭의 업데이트 함수 찾기
                                elif tab_id == 1:  # 채팅 탭
                                    for frame in find_widgets_by_class(tab, ttk.Frame):
                                        for label in find_widgets_by_class(frame, ttk.Label):
                                            if hasattr(label, 'cget') and label.cget("text").startswith("현재 적용됨:"):
                                                update_label_with_prompt_count(label, "chat")
                        except Exception as inner_e:
                            print(f"탭 상태 업데이트 중 내부 오류: {inner_e}")
    except Exception as e:
        print(f"프롬프트 상태 업데이트 중 오류: {e}")

def find_widgets_by_class(parent, widget_class):
    """특정 클래스의 위젯을 모두 찾아 반환"""
    result = []
    
    try:
        for widget in parent.winfo_children():
            if isinstance(widget, widget_class):
                result.append(widget)
            try:
                result.extend(find_widgets_by_class(widget, widget_class))
            except:
                # 일부 위젯이 문제를 일으키면 그냥 넘어감
                pass
    except:
        # 위젯이 더 이상 존재하지 않거나 다른 문제가 있으면 현재 결과 반환
        pass
    return result

def update_label_with_prompt_count(label, prompt_type):
    """레이블 위젯에 프롬프트 개수 업데이트"""
    try:
        # 동적 임포트로 순환 참조 방지
        from utils.prompt_loader import load_prompts_by_type
        prompts = load_prompts_by_type(prompt_type, as_dict=True)
        count = len(prompts)
        try:
            label.config(
                text=f"현재 적용됨: 프롬프트 {count}개",
                foreground=SUCCESS_COLOR if count > 0 else WARNING_COLOR
            )
        except tk.TclError:
            # 위젯이 더 이상 존재하지 않음
            pass
    except ImportError:
        print("프롬프트 로더 모듈을 불러올 수 없습니다.")
    except Exception as e:
        print(f"프롬프트 개수 업데이트 중 오류: {e}")

def show_prompt_preview(name, data):
    """프롬프트 미리보기 창"""
    global root
    
    if not root:
        return
    
    try:    
        preview = tk.Toplevel(root)
        preview.title(f"프롬프트 미리보기: {name}")
        preview.geometry("600x400")
        preview.transient(root)
        
        # 중앙에 배치
        preview.update_idletasks()
        screen_width = preview.winfo_screenwidth()
        screen_height = preview.winfo_screenheight()
        size = (600, 400)
        x = (screen_width - size[0]) // 2
        y = (screen_height - size[1]) // 2
        preview.geometry(f"{size[0]}x{size[1]}+{x}+{y}")
        
        # 컨텐츠 프레임
        content = ttk.Frame(preview, padding=15)
        content.pack(fill=tk.BOTH, expand=True)
        
        # 헤더
        header = ttk.Frame(content)
        header.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            header, 
            text=name, 
            font=("Arial", 14, "bold"), 
            foreground=PRIMARY_COLOR
        ).pack(side=tk.LEFT)
        
        # 우선순위 표시
        priority = data.get('priority', 10)
        ttk.Label(
            header,
            text=f"우선순위: {priority}",
            foreground=PRIMARY_COLOR
        ).pack(side=tk.RIGHT)
        
        # 구분선
        ttk.Separator(content, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # 유형 정보
        types = data.get('type', [])
        type_frame = ttk.Frame(content)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="적용 유형:").pack(side=tk.LEFT)
        type_label = ttk.Label(
            type_frame,
            text=", ".join(types),
            foreground=SUCCESS_COLOR
        )
        type_label.pack(side=tk.LEFT, padx=5)
        
        # 프롬프트 내용
        ttk.Label(content, text="내용:", anchor="w").pack(fill=tk.X, pady=(10, 5))
        template_frame = ttk.Frame(content)
        template_frame.pack(fill=tk.BOTH, expand=True)
        template_text = scrolledtext.ScrolledText(template_frame, wrap=tk.WORD)
        template_text.pack(fill=tk.BOTH, expand=True)
        template_text.insert("1.0", data.get('template', ''))
        template_text.config(state=tk.DISABLED)
        
        # 샘플 적용 미리보기
        preview_frame = ttk.LabelFrame(content, text="샘플 적용 결과")
        preview_frame.pack(fill=tk.X, pady=10)
        
        preview_text = tk.Text(preview_frame, height=4, wrap=tk.WORD)
        preview_text.pack(fill=tk.X, padx=5, pady=5)
        sample_applied = data.get('template', '').replace(
            "{clause}", "5.3.2"
        ).replace(
            "{title}", "기계 안전성 검토"
        )
        preview_text.insert("1.0", sample_applied)
        preview_text.config(state=tk.DISABLED)
        
        # 닫기 버튼
        ttk.Button(
            content, 
            text="닫기", 
            command=preview.destroy
        ).pack(side=tk.RIGHT, pady=10)
    except Exception as e:
        print(f"프롬프트 미리보기 표시 중 오류: {e}")
        messagebox.showerror("미리보기 오류", f"프롬프트 미리보기를 표시하는 중 오류가 발생했습니다: {e}")

def handle_exception(e, title="오류", message_prefix="작업 중 오류가 발생했습니다", log_error=True):
    """예외를 일관되게 처리"""
    error_message = str(e)
    
    if log_error:
        try:
            from utils.logger import logger
            logger.error(f"{message_prefix}: {error_message}")
        except ImportError:
            print(f"ERROR: {message_prefix}: {error_message}")
    
    try:
        messagebox.showerror(title, f"{message_prefix}:\n{error_message}")
    except:
        # TK가 초기화되지 않았을 수 있음
        print(f"메시지 박스를 표시할 수 없습니다: {error_message}")
    
    return error_message