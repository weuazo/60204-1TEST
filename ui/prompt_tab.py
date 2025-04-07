import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import json
from datetime import datetime
from ui.ui_utils import log_message, select_prompt_tab, update_all_prompt_statuses, show_prompt_preview

# UI 테마 및 색상 가져오기
from ui.ui_utils import (
    PRIMARY_COLOR, SECONDARY_COLOR, BG_COLOR, CARD_COLOR, TEXT_COLOR, 
    SUCCESS_COLOR, WARNING_COLOR, ERROR_COLOR, BORDER_COLOR, HOVER_COLOR
)

# 전역 변수
prompt_editor_name = None
prompt_editor_text = None
prompt_file_list = None
filter_var = None
priority_var = None
type_remark_var = None
type_chat_var = None

def build_prompt_tab(tab):
    """프롬프트 관리 탭 구성"""
    global prompt_editor_name, prompt_editor_text, prompt_file_list, filter_var
    global priority_var, type_remark_var, type_chat_var
    
    # 메인 컨테이너
    container = ttk.Frame(tab)
    container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    # 왼쪽 패널 (목록)
    left_panel = ttk.Frame(container, style="Card.TFrame")
    left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), expand=False)
    
    # 목록 헤더
    list_header = ttk.Frame(left_panel)
    list_header.pack(fill=tk.X, padx=15, pady=(15, 5))
    
    ttk.Label(list_header, text="프롬프트 목록", style="Subtitle.TLabel").pack(side=tk.LEFT)
    
    # 유형 필터링 토글 버튼 추가 - 변수를 전역으로 변경
    filter_var = tk.StringVar(value="all")
    filter_frame = ttk.Frame(left_panel)
    filter_frame.pack(fill=tk.X, padx=15, pady=(0, 5))
    
    # 라디오버튼 이벤트 핸들러를 명시적 함수로 변경
    def on_filter_change():
        refresh_prompt_list(filter_var.get())
    
    ttk.Radiobutton(filter_frame, text="전체", variable=filter_var, value="all", 
                  command=on_filter_change).pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(filter_frame, text="보고서용", variable=filter_var, value="remark", 
                  command=on_filter_change).pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(filter_frame, text="채팅용", variable=filter_var, value="chat", 
                  command=on_filter_change).pack(side=tk.LEFT, padx=5)
    
    # 목록 영역
    list_frame = ttk.Frame(left_panel)
    list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
    
    # 리스트박스와 스크롤바
    list_container = ttk.Frame(list_frame)
    list_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    prompt_file_list = tk.Listbox(
        list_container, 
        width=30, 
        height=20, 
        borderwidth=1,
        highlightthickness=0,
        selectbackground=PRIMARY_COLOR,
        selectforeground="white"
    )
    prompt_file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    list_scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=prompt_file_list.yview)
    prompt_file_list.configure(yscrollcommand=list_scrollbar.set)
    list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # 목록 버튼
    list_buttons = ttk.Frame(list_frame)
    list_buttons.pack(fill=tk.X)
    
    new_btn = ttk.Button(list_buttons, text="새 프롬프트", command=new_prompt)
    new_btn.pack(side=tk.LEFT, padx=5)
    
    refresh_btn = ttk.Button(list_buttons, text="새로고침", command=lambda: refresh_prompt_list())
    refresh_btn.pack(side=tk.LEFT, padx=5)
    
    delete_btn = ttk.Button(list_buttons, text="삭제", command=delete_prompt)
    delete_btn.pack(side=tk.RIGHT, padx=5)
    
    # 정렬 버튼 (UI 개선)
    order_buttons = ttk.Frame(list_frame)
    order_buttons.pack(fill=tk.X, pady=10)
    
    ttk.Label(order_buttons, text="목록 순서 이동:").pack(side=tk.LEFT, padx=5)
    
    up_btn = ttk.Button(order_buttons, text="⬆️", width=3, command=lambda: move_prompt_in_list(-1))
    up_btn.pack(side=tk.LEFT, padx=2)
    
    down_btn = ttk.Button(order_buttons, text="⬇️", width=3, command=lambda: move_prompt_in_list(1))
    down_btn.pack(side=tk.LEFT, padx=2)
    
    # 오른쪽 패널 (편집)
    right_panel = ttk.Frame(container, style="Card.TFrame")
    right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # 편집 헤더
    edit_header = ttk.Frame(right_panel)
    edit_header.pack(fill=tk.X, padx=15, pady=(15, 5))
    
    ttk.Label(edit_header, text="프롬프트 편집", style="Subtitle.TLabel").pack(side=tk.LEFT)
    
    # 편집 영역
    edit_frame = ttk.Frame(right_panel)
    edit_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
    
    # 이름 입력
    name_frame = ttk.Frame(edit_frame)
    name_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(name_frame, text="이름:").grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")
    prompt_editor_name = ttk.Entry(name_frame, width=40)
    prompt_editor_name.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
    # 우선순위
    ttk.Label(name_frame, text="우선순위:").grid(row=0, column=2, padx=(20, 10), pady=5, sticky="w")
    
    priority_var = tk.IntVar(value=10)
    priority_spin = ttk.Spinbox(name_frame, from_=1, to=99, width=5, textvariable=priority_var)
    priority_spin.grid(row=0, column=3, padx=5, pady=5, sticky="w")
    
    # 우선순위 설명 레이블 추가
    priority_info = ttk.Label(name_frame, 
                            text="낮은 숫자가 먼저 적용됨", 
                            font=("Arial", 8, "italic"),
                            foreground="#666666")
    priority_info.grid(row=0, column=4, padx=5, pady=5, sticky="w")
    
    # 유형 선택 (체크박스) - "모두 적용" 체크박스를 완전히 제거
    type_frame = ttk.LabelFrame(edit_frame, text="적용 유형")
    type_frame.pack(fill=tk.X, pady=10)
    
    type_options_frame = ttk.Frame(type_frame)
    type_options_frame.pack(padx=10, pady=10, fill=tk.X)
    
    # 체크박스 변수 - 두 개만 사용
    type_remark_var = tk.BooleanVar(value=True)
    type_chat_var = tk.BooleanVar(value=False)
    
    # 체크박스
    remark_cb = ttk.Checkbutton(type_options_frame, text="보고서 생성", variable=type_remark_var)
    remark_cb.pack(side=tk.LEFT, padx=15)
    
    chat_cb = ttk.Checkbutton(type_options_frame, text="채팅", variable=type_chat_var)
    chat_cb.pack(side=tk.LEFT, padx=15)
    
    # 적용 설명 레이블
    apply_info = ttk.Label(
        type_options_frame,
        text="(하나 이상 선택: 체크된 기능에 프롬프트가 적용됩니다)",
        font=("Arial", 9),
        foreground="#666666"
    )
    apply_info.pack(side=tk.LEFT, padx=15)
    
    # 내용 입력
    content_label = ttk.Label(edit_frame, text="프롬프트 내용:")
    content_label.pack(anchor="w", pady=(10, 5))
    
    prompt_editor_text = scrolledtext.ScrolledText(edit_frame, wrap=tk.WORD, height=12)
    prompt_editor_text.pack(fill=tk.BOTH, expand=True)
    
    # 상태 표시줄
    status_frame = ttk.Frame(edit_frame)
    status_frame.pack(fill=tk.X, pady=(5, 0))
    
    status_label = ttk.Label(status_frame, text="", foreground="gray")
    status_label.pack(side=tk.LEFT)
    
    last_saved_label = ttk.Label(status_frame, text="")
    last_saved_label.pack(side=tk.RIGHT)
    
    # 버튼 영역
    button_frame = ttk.Frame(edit_frame)
    button_frame.pack(fill=tk.X, pady=10)
    
    preview_btn = ttk.Button(button_frame, text="적용 미리보기", command=preview_prompt)
    preview_btn.pack(side=tk.LEFT)
    
    save_btn = ttk.Button(button_frame, text="저장", command=lambda: save_prompt(
        prompt_editor_name.get(),
        [t for t, v in zip(["remark", "chat"], 
                          [type_remark_var.get(), type_chat_var.get()]) 
         if v],
        prompt_editor_text.get("1.0", tk.END),
        priority_var.get(),
        status_label,
        last_saved_label
    ), style="Primary.TButton")
    save_btn.pack(side=tk.RIGHT, padx=5)
    
    # 템플릿 키 설명 (변수 관련 내용 제거)
    help_frame = tk.Frame(edit_frame, bg=HOVER_COLOR, bd=1, relief="solid")
    help_frame.pack(fill=tk.X, pady=(10, 0))
    
    help_text = """
📝 프롬프트 작성 안내:
• 우선순위가 낮은 값(1, 2, 3, ...)일수록 먼저 적용됩니다
• 프롬프트는 자유롭게 작성하여 AI의 응답 방향을 설정할 수 있습니다
• 프롬프트 내에서 다양한 변수를 활용할 수 있습니다
"""
    
    help_label = tk.Label(
        help_frame, 
        text=help_text, 
        justify=tk.LEFT, 
        bg=HOVER_COLOR, 
        fg=TEXT_COLOR, 
        font=("Arial", 9),
        padx=10, 
        pady=10
    )
    help_label.pack(fill=tk.X)
    
    # 이벤트 연결 - 더블클릭 이벤트 별도 처리로 변경
    prompt_file_list.bind("<<ListboxSelect>>", on_prompt_select)
    prompt_file_list.bind("<Double-1>", on_prompt_double_click)  # 더블클릭 이벤트 분리
    
    # 드래그 앤 드롭 설정
    setup_drag_and_drop(prompt_file_list)
    
    # 초기 데이터 로드
    refresh_prompt_list("all")
    
    return container

# 더블클릭 이벤트 핸들러 개선
def on_prompt_double_click(event):
    """프롬프트 더블클릭 처리 - 편집하기"""
    global filter_var
    
    if not prompt_file_list:
        return
    
    sel = prompt_file_list.curselection()
    if not sel:
        return
    
    # 선택된 항목 파싱
    selected_text = prompt_file_list.get(sel[0])
    name = selected_text.split(" | ")[1] if " | " in selected_text else selected_text
    
    # 아이콘이 포함된 경우 제거
    if name.startswith("🔄 ") or name.startswith("📊 ") or name.startswith("💬 "):
        name = name[2:]
    
    # 현재 필터 상태 저장
    current_filter = filter_var.get()
    
    # 데이터 로드 처리
    load_prompt_data(name)
    
    # 필터 상태 복원 - 더블클릭으로 인한 의도치 않은 필터 변경 방지
    if filter_var.get() != current_filter:
        filter_var.set(current_filter)
    
    # 이벤트 처리 중단
    return "break"

def setup_drag_and_drop(listbox):
    """리스트박스의 드래그 앤 드롭 기능 설정"""
    listbox.drag_start_index = None
    listbox.dragging = False  # 드래그 중인지 상태 추적 변수 추가
    
    def on_drag_start(event):
        # 드래그 시작 위치 저장
        widget = event.widget
        selection = widget.curselection()
        if selection:
            listbox.drag_start_index = selection[0]
            widget.config(cursor="exchange")
            listbox.dragging = False  # 드래그 시작 시에는 아직 드래그 중이 아님
    
    def on_drag_motion(event):
        # 드래그 움직임이 감지되면 드래그 상태로 설정
        if listbox.drag_start_index is not None:
            listbox.dragging = True
            widget = event.widget
            y = event.y
            current_index = widget.nearest(y)
            # 기존 선택 유지하면서 드래그 중인 위치만 하이라이트
            widget.selection_clear(0, tk.END)
            widget.selection_set(current_index)
    
    def on_drag_release(event):
        # 드래그 종료 처리
        if listbox.drag_start_index is not None:
            widget = event.widget
            end_index = widget.nearest(event.y)
            
            # 실제 드래그가 일어났고 위치가 변경되었으면 항목 이동
            if listbox.dragging and listbox.drag_start_index != end_index:
                move_prompt_in_list_to_position(listbox.drag_start_index, end_index)
            elif not listbox.dragging:
                # 드래그 없이 단순 클릭이었다면 선택만 유지
                pass
                
            # 드래그 상태 초기화
            listbox.drag_start_index = None
            listbox.dragging = False
            widget.config(cursor="")
    
    def on_click(event):
        # 단순 클릭 처리 (드래그가 아닌 경우)
        widget = event.widget
        if widget.identify_region(event.x, event.y) == "selectitem":
            index = widget.nearest(event.y)
            if widget.selection_includes(index):
                return "break"
    
    # 드래그 앤 드롭 관련 이벤트
    listbox.bind("<ButtonPress-1>", on_drag_start)
    listbox.bind("<B1-Motion>", on_drag_motion)
    listbox.bind("<ButtonRelease-1>", on_drag_release)
    listbox.bind("<Button-1>", on_click)
    
    # 리스트박스에서 항목 선택시 키보드 포커스 유지
    listbox.bind("<FocusOut>", lambda e: listbox.config(takefocus=True))

def move_prompt_in_list_to_position(start_idx, end_idx):
    """리스트에서 프롬프트 항목을 시작 인덱스에서 끝 인덱스로 이동"""
    if not prompt_file_list:
        return
    
    try:
        # 선택된 항목 정보 가져오기
        selected_text = prompt_file_list.get(start_idx)
        
        # 이동할 항목 이름 추출
        parts = selected_text.split(" | ")
        if len(parts) < 2:
            print(f"항목 형식 오류: {selected_text}")
            return
            
        name = parts[1]
        
        # 아이콘이 포함된 경우 제거
        if name.startswith("🔄 ") or name.startswith("📊 ") or name.startswith("💬 "):
            name = name[2:]
            
        # 현재 필터링 상태 확인 - 전역 변수 사용
        current_filter = "all"  # 기본값
        if 'filter_var' in globals():
            current_filter = filter_var.get()
        
        # 모든 프롬프트 로드 및 정렬 정보 수집
        all_prompts = []
        for file in os.listdir("prompts"):
            if file.endswith(".json"):
                try:
                    with open(os.path.join("prompts", file), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        priority = data.get("priority", 10)
                        prompt_name = data.get("prompt_name", file[:-5])
                        types = data.get("type", [])
                        
                        # 필터링 적용 (all이면 모두 표시)
                        if current_filter == "all" or current_filter in types:
                            all_prompts.append((prompt_name, priority, types, file))
                except:
                    # 오류 파일은 무시
                    pass
        
        # 우선순위로 정렬
        all_prompts.sort(key=lambda x: x[1])
        
        # 현재 위치와 대상 위치 확인
        current_position = -1
        for i, (prompt_name, _, _, _) in enumerate(all_prompts):
            if prompt_name == name:
                current_position = i
                break
                
        if current_position == -1:
            print(f"프롬프트 '{name}'의 위치를 찾을 수 없습니다.")
            return
            
        target_position = min(end_idx, len(all_prompts) - 1)
        
        # 항목 이동
        moved_item = all_prompts.pop(current_position)
        all_prompts.insert(target_position, moved_item)
        
        # 새로운 우선순위 계산하고 저장
        for i, (prompt_name, _, _, filename) in enumerate(all_prompts):
            # 실제 우선순위 값은 인덱스+1
            new_priority = i + 1
            
            # 파일 업데이트
            filepath = os.path.join("prompts", filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                data["priority"] = new_priority
                
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
            except Exception as e:
                print(f"우선순위 업데이트 중 오류: {e}")
        
        # 목록 새로고침
        refresh_prompt_list(current_filter or "all")
        
        # 이동된 항목 선택
        target_idx = target_position
        if 0 <= target_idx < prompt_file_list.size():
            prompt_file_list.selection_clear(0, tk.END)
            prompt_file_list.selection_set(target_idx)
            prompt_file_list.see(target_idx)
            
            # 선택된 항목 데이터 로드
            selected_item = prompt_file_list.get(target_idx)
            load_prompt_data_from_selection(selected_item)
        
        # 상태 메시지
        log_message(f"프롬프트 '{name}'의 순서가 변경되었습니다.", "info")
        
    except Exception as e:
        print(f"순서 변경 중 발생한 오류: {str(e)}")
        messagebox.showerror("순서 변경 오류", f"프롬프트 순서 변경 중 오류 발생: {str(e)}")

def move_prompt_in_list(direction):
    """리스트에서 프롬프트를 위/아래로 이동"""
    if not prompt_file_list:
        return
        
    sel = prompt_file_list.curselection()
    if not sel:
        messagebox.showwarning("선택 오류", "이동할 프롬프트를 선택하세요.")
        return
    
    current_index = sel[0]
    new_index = current_index + direction
    
    # 범위 검사
    if new_index < 0 or new_index >= prompt_file_list.size():
        return
    
    # 위치 이동
    move_prompt_in_list_to_position(current_index, new_index)

def refresh_prompt_list(filter_type="all"):
    """프롬프트 목록 새로고침 (필터링 포함)"""
    if prompt_file_list is None:
        return
    
    # 현재 선택된 항목 기억
    try:
        selected_idx = prompt_file_list.curselection()[0] if prompt_file_list.curselection() else -1
        selected_text = prompt_file_list.get(selected_idx) if selected_idx >= 0 else None
    except:
        selected_idx = -1
        selected_text = None
    
    prompt_file_list.delete(0, tk.END)
    
    if not os.path.exists("prompts"):
        os.makedirs("prompts", exist_ok=True)
        return
    
    # 우선순위에 따라 정렬
    prompts_data = []
    
    for file in os.listdir("prompts"):
        if file.endswith(".json"):
            try:
                with open(os.path.join("prompts", file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 실제 우선순위 값 가져오기
                    priority_value = data.get("priority", 10)
                    name = data.get("prompt_name", file[:-5])
                    types = data.get("type", [])
                    
                    # 필터링 적용
                    if filter_type == "all" or filter_type in types:
                        prompts_data.append((name, priority_value, types))
            except:
                # 오류 파일 처리
                if filter_type == "all":
                    prompts_data.append((file[:-5], 999, []))
    
    # 우선순위로 정렬
    prompts_data.sort(key=lambda x: x[1])
    
    # 목록에 표시
    new_selected_idx = -1
    for idx, (name, priority, types) in enumerate(prompts_data):
        # 타입 아이콘 추가
        icon = ""
        if "remark" in types and "chat" in types:
            icon = "🔄 "  # 양쪽 모두 적용
        elif "remark" in types:
            icon = "📊 "  # 보고서용
        elif "chat" in types:
            icon = "💬 "  # 채팅용
            
        # 우선순위(실제값) | 이름
        display_text = f"{priority}({priority}) | {icon}{name}"
        prompt_file_list.insert(tk.END, display_text)
        
        # 이전에 선택된 항목이 일치하는지 확인
        if selected_text and icon + name in selected_text:
            new_selected_idx = idx

    # 이전 선택 항목 복원
    if new_selected_idx >= 0:
        prompt_file_list.selection_clear(0, tk.END)
        prompt_file_list.selection_set(new_selected_idx)
        prompt_file_list.see(new_selected_idx)

def save_prompt(name, types, content, priority, status_label, last_saved_label):
    """프롬프트 저장"""
    if not name:
        messagebox.showwarning("입력 오류", "프롬프트 이름을 입력하세요.")
        return
        
    if not types:
        messagebox.showwarning("입력 오류", "적용 유형을 하나 이상 선택하세요.")
        return
        
    if not content:
        messagebox.showwarning("입력 오류", "프롬프트 내용을 입력하세요.")
        return
    
    try:
        # 저장 디렉토리 확인
        os.makedirs("prompts", exist_ok=True)
        
        # 저장할 데이터 구성 ("all" 타입 사용하지 않음)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt_data = {
            "prompt_name": name,
            "type": types,  # "remark"와 "chat"만 포함됨
            "template": content.strip(),
            "priority": priority,
            "last_updated": now
        }
        
        # 파일로 저장
        filepath = os.path.join("prompts", f"{name}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(prompt_data, f, ensure_ascii=False, indent=2)
            
        # 상태 업데이트
        if status_label:
            status_label.config(text=f"저장 성공: {filepath}", foreground=SUCCESS_COLOR)
            
        if last_saved_label:
            last_saved_label.config(text=f"마지막 저장: {now}")
        
        # 현재 선택된 필터 확인
        current_filter = filter_var.get() if filter_var else "all"
        
        # 프롬프트 목록 새로고침 (현재 필터 유지)
        refresh_prompt_list(current_filter)
        
        # 채팅탭과 보고서 생성탭의 콤보박스 새로고침
        try:
            # 각 탭의 프롬프트 상태 업데이트 함수 호출
            from ui.gui_main import get_root
            
            root = get_root()
            if root:
                root.after(100, update_all_prompt_statuses)
                
                # 상태 메시지 표시
                if status_label:
                    status_label.config(text=f"저장 성공: {filepath}", foreground=SUCCESS_COLOR)
                    
                if last_saved_label:
                    last_saved_label.config(text=f"마지막 저장: {now}")
                    
                # 성공 메시지를 잠시 표시한 후 사라지게 함
                if status_label:
                    root.after(3000, lambda: status_label.config(text=""))
            
        except Exception as e:
            print(f"프롬프트 상태 업데이트 실패: {e}")
        
        return True
        
    except Exception as e:
        if status_label:
            status_label.config(text=f"저장 실패: {str(e)}", foreground=ERROR_COLOR)
        messagebox.showerror("저장 오류", f"프롬프트 저장 중 오류가 발생했습니다:\n{str(e)}")
        return False

def on_prompt_select(event):
    """프롬프트 선택 처리"""
    if not prompt_file_list:
        return
        
    sel = prompt_file_list.curselection()
    if not sel:
        return
    
    try:    
        # 선택된 항목 파싱
        selected_text = prompt_file_list.get(sel[0])
        
        # 드래그 중에는 데이터 로드 건너뛰기
        if hasattr(prompt_file_list, 'dragging') and prompt_file_list.dragging:
            return "break"
        
        # 우선순위와 이름 추출 - 새 형식 대응 (10(1) | 이름)
        parts = selected_text.split(" | ")
        if len(parts) < 2:
            print(f"항목 형식 오류: {selected_text}")
            return
            
        name = parts[1]
        
        # 아이콘이 포함된 경우 제거
        if name.startswith("🔄 ") or name.startswith("📊 ") or name.startswith("💬 "):
            name = name[2:]
        
        # 프롬프트 데이터 로드
        load_prompt_data(name)
    except Exception as e:
        print(f"프롬프트 선택 처리 중 오류: {str(e)}")

def load_prompt_data(name):
    """프롬프트 데이터 로드"""
    path = os.path.join("prompts", f"{name}.json")
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # 이름 필드 설정
            prompt_editor_name.delete(0, tk.END)
            prompt_editor_name.insert(0, data.get("prompt_name", name))
            
            # 내용 필드 설정
            prompt_editor_text.delete("1.0", tk.END)
            prompt_editor_text.insert("1.0", data.get("template", ""))
            
            # 유형 체크박스 상태 설정 - 두 개만 처리
            types = data.get("type", [])
            if not isinstance(types, list):
                types = [types]
                
            try:
                # 체크박스 변수에 대한 참조 확인 (두 개만 있음)
                if 'type_remark_var' in globals():
                    globals()['type_remark_var'].set("remark" in types)
                if 'type_chat_var' in globals():
                    globals()['type_chat_var'].set("chat" in types)
                    
                # 우선순위 설정
                if 'priority_var' in globals() and 'priority' in data:
                    globals()['priority_var'].set(data['priority'])
            except Exception as e:
                print(f"체크박스 상태 설정 실패: {e}")
            
    except Exception as e:
        log_message(f"프롬프트 불러오기 실패: {str(e)}", "error")

def load_prompt_data_from_selection(selected_text):
    """선택된 항목 텍스트에서 이름을 추출하여 데이터 로딩"""
    if not selected_text:
        return
        
    try:
        parts = selected_text.split(" | ")
        if len(parts) < 2:
            return
            
        name = parts[1]
        
        # 아이콘이 포함된 경우 제거
        if name.startswith("🔄 ") or name.startswith("📊 ") or name.startswith("💬 "):
            name = name[2:]
            
        load_prompt_data(name)
    except Exception as e:
        print(f"선택 항목 처리 오류: {str(e)}")

def new_prompt():
    """새 프롬프트 생성"""
    # 필드 초기화
    prompt_editor_name.delete(0, tk.END)
    prompt_editor_text.delete("1.0", tk.END)
    
    # 기본 템플릿 제공
    prompt_editor_text.insert("1.0", "{clause} 항목과 {title}에 대한 검토 의견을 작성해주세요.")
    
    # 체크박스 기본값 설정
    if 'type_remark_var' in globals():
        globals()['type_remark_var'].set(True)
    if 'type_chat_var' in globals():
        globals()['type_chat_var'].set(False)
    
    # 우선순위 기본값 설정
    if 'priority_var' in globals():
        globals()['priority_var'].set(10)

def delete_prompt():
    """프롬프트 삭제"""
    if not prompt_file_list:
        return
    
    sel = prompt_file_list.curselection()
    if not sel:
        messagebox.showwarning("선택 오류", "삭제할 프롬프트를 선택하세요.")
        return
    
    # 선택된 항목 파싱
    selected_text = prompt_file_list.get(sel[0])
    parts = selected_text.split(" | ")
    
    if len(parts) < 2:
        messagebox.showerror("형식 오류", "프롬프트 항목 형식이 올바르지 않습니다.")
        return
    
    # 이름 추출 (아이콘 제거)
    name = parts[1]
    if name.startswith("🔄 ") or name.startswith("📊 ") or name.startswith("💬 "):
        name = name[2:]
    
    # 삭제 확인
    if not messagebox.askyesno("삭제 확인", f"프롬프트 '{name}'을(를) 정말 삭제하시겠습니까?"):
        return
    
    try:
        # 파일 삭제
        filepath = os.path.join("prompts", f"{name}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            messagebox.showinfo("삭제 완료", f"프롬프트 '{name}'이(가) 삭제되었습니다.")
            
            # 목록 새로고침
            refresh_prompt_list()
            
            # 편집 영역 초기화
            prompt_editor_name.delete(0, tk.END)
            prompt_editor_text.delete(1.0, tk.END)
            
            # 상태 업데이트
            update_all_prompt_statuses()
            
            return True
        else:
            messagebox.showerror("삭제 오류", f"파일을 찾을 수 없습니다: {filepath}")
            
    except Exception as e:
        messagebox.showerror("삭제 오류", f"프롬프트 삭제 중 오류가 발생했습니다:\n{str(e)}")
        
    return False

def preview_prompt():
    """프롬프트 적용 미리보기"""
    name = prompt_editor_name.get().strip()
    content = prompt_editor_text.get("1.0", tk.END).strip()
    
    if not name or not content:
        messagebox.showwarning("입력 오류", "프롬프트 이름과 내용을 입력해주세요.")
        return
    
    # 선택된 유형 가져오기
    types = []
    if 'type_remark_var' in globals() and globals()['type_remark_var'].get():
        types.append("remark")
    if 'type_chat_var' in globals() and globals()['type_chat_var'].get():
        types.append("chat")
    
    # 우선순위 가져오기
    priority = globals()['priority_var'].get() if 'priority_var' in globals() else 10
    
    # 프롬프트 데이터 구성
    data = {
        "type": types,
        "template": content,
        "priority": priority
    }
    
    # 미리보기 창 표시
    show_prompt_preview(name, data)

standards_file = os.path.join("data", "standards.json")
