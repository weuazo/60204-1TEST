import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pandas as pd
import os
from datetime import datetime

# UI 설정 및 유틸리티 임포트
from ui.ui_utils import (
    log_message, show_active_prompts, set_log_box, handle_exception,
    PRIMARY_COLOR, SECONDARY_COLOR, BG_COLOR, CARD_COLOR, TEXT_COLOR, 
    SUCCESS_COLOR, WARNING_COLOR, ERROR_COLOR, BORDER_COLOR, HOVER_COLOR
)

from ui.file_manager import FileSelector
from parsers import get_parser_for_file
from matcher import create_matcher
from logic.extended_generator import generate_from_documents

# 전역 변수
source_selector = None
target_selector = None
matcher_mode_var = None
source_clause_cb = None
source_title_cb = None
target_clause_cb = None
target_output_cb = None
log_box = None
standard_var = None

def create_extended_report_tab(parent):
    """확장된 보고서 생성 탭 구성"""
    global source_selector, target_selector, matcher_mode_var
    global source_clause_cb, source_title_cb, target_clause_cb, target_output_cb
    global log_box, standard_var
    
    # 스크롤 가능한 메인 프레임
    main_canvas = tk.Canvas(parent, bg=BG_COLOR, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=main_canvas.yview)
    scrollable_frame = ttk.Frame(main_canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
    )
    
    main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    main_canvas.configure(yscrollcommand=scrollbar.set)
    
    main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # 진행 단계를 명확하게 보여주는 워크플로우 헤더
    workflow_frame = ttk.Frame(scrollable_frame)
    workflow_frame.pack(fill=tk.X, padx=20, pady=10)
    
    workflow_label = ttk.Label(
        workflow_frame, 
        text="확장 보고서 생성: 문서 선택 → 항목 매핑 설정 → AI 프롬프트 적용 → 결과 생성",
        font=("Arial", 10),
        foreground=PRIMARY_COLOR
    )
    workflow_label.pack(anchor="w")
    
    # 1. 문서 선택 섹션
    file_card = ttk.Frame(scrollable_frame, style="Card.TFrame")
    file_card.pack(fill=tk.X, padx=20, pady=10)
    
    # 카드 헤더
    header_frame = ttk.Frame(file_card)
    header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
    
    ttk.Label(header_frame, text="1. 문서 선택", style="Title.TLabel").pack(side=tk.LEFT)
    
    # 설명
    desc = ttk.Label(
        file_card,
        text="작업에 필요한 소스 문서(검토 항목)와 대상 문서(결과 저장)를 선택하세요. 여러 형식의 문서를 지원합니다.",
        wraplength=800,
        padding=(15, 5)
    )
    desc.pack(fill=tk.X)
    
    # 파일 선택 컨테이너
    file_container = ttk.Frame(file_card)
    file_container.pack(fill=tk.X, padx=15, pady=15)
    
    # 소스 파일 선택기
    source_selector = FileSelector(
        file_container, 
        title="소스 문서 (검토 항목)", 
        supported_types=[
            ("모든 지원 파일", "*.xlsx *.xls *.pdf *.docx *.doc"),
            ("Excel 파일", "*.xlsx *.xls"),
            ("PDF 파일", "*.pdf"),
            ("Word 파일", "*.docx *.doc")
        ],
        callback=on_source_file_selected
    )
    
    # 대상 파일 선택기
    target_selector = FileSelector(
        file_container, 
        title="대상 문서 (결과 저장)",
        supported_types=[("Excel 파일", "*.xlsx *.xls")],
        callback=on_target_file_selected
    )
    
    # 규격 선택 영역
    standard_frame = ttk.LabelFrame(file_container, text="규격 설정")
    standard_frame.pack(fill=tk.X, pady=10)
    
    standard_desc = ttk.Label(
        standard_frame,
        text="적용할 규격을 선택하세요. 자동 감지가 가능하지만, 정확한 규격을 직접 선택하는 것이 좋습니다.",
        wraplength=700,
        padding=(5, 5)
    )
    standard_desc.pack(fill=tk.X, padx=10, pady=5)
    
    standard_selection = ttk.Frame(standard_frame)
    standard_selection.pack(fill=tk.X, padx=10, pady=5)
    
    ttk.Label(standard_selection, text="적용 규격:").pack(side=tk.LEFT, padx=5)
    
    # 규격 선택용 콤보박스
    standard_var = tk.StringVar(value="AUTO_DETECT")
    standard_combo = ttk.Combobox(
        standard_selection, 
        textvariable=standard_var, 
        width=40,
        state="readonly"
    )
    standard_combo.pack(side=tk.LEFT, padx=5)
    
    # 기본 규격 목록 설정
    standard_options = [
        "AUTO_DETECT",  # AI 감지 결과 사용
        "IEC_60204-1",
        "IEC_61010",
        "ISO_13849",
        "IEC_62061",
        "ISO_14119",
        "IEC_60335",
        "UNKNOWN"  # 알 수 없음/해당없음
    ]
    standard_combo["values"] = standard_options
    
    # AI 규격 감지 버튼
    detect_btn = ttk.Button(
        standard_selection, 
        text="AI 규격 감지", 
        command=lambda: detect_standard_with_ai()
    )
    detect_btn.pack(side=tk.LEFT, padx=5)
    
    # 매칭 옵션 선택
    matching_frame = ttk.Frame(standard_frame)
    matching_frame.pack(fill=tk.X, padx=10, pady=5)
    
    ttk.Label(matching_frame, text="매칭 방식:").pack(side=tk.LEFT, padx=5)
    
    matcher_mode_var = tk.StringVar(value="basic")
    ttk.Radiobutton(matching_frame, text="일반 매칭", variable=matcher_mode_var, 
                  value="basic").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(matching_frame, text="AI 매칭 (정확도 향상)", variable=matcher_mode_var, 
                  value="ai").pack(side=tk.LEFT, padx=5)
    
    match_info = ttk.Label(
        matching_frame, 
        text="AI 매칭은 추가 API 호출이 필요하지만 다양한 문서 형식에서 더 정확한 결과를 제공합니다", 
        foreground="#666666", 
        font=("Arial", 9)
    )
    match_info.pack(side=tk.LEFT, padx=10)
    
    # 2. 항목 매핑 설정 섹션
    mapping_card = ttk.Frame(scrollable_frame, style="Card.TFrame")
    mapping_card.pack(fill=tk.X, padx=20, pady=10)
    
    # 카드 헤더
    header_frame = ttk.Frame(mapping_card)
    header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
    
    ttk.Label(header_frame, text="2. 항목 매핑 설정", style="Title.TLabel").pack(side=tk.LEFT)
    
    # 매핑 설명
    mapping_desc = ttk.Label(
        mapping_card,
        text="두 문서 간에 항목을 연결하는 방법을 설정합니다. 각 문서에서 매칭할 열이나 항목을 선택하세요.",
        wraplength=800,
        padding=(15, 5)
    )
    mapping_desc.pack(fill=tk.X)
    
    # 매핑 컨테이너
    mapping_container = ttk.Frame(mapping_card)
    mapping_container.pack(fill=tk.X, padx=15, pady=15)
    
    # 매핑 영역 - 왼쪽 (소스)
    source_mapping_frame = ttk.LabelFrame(mapping_container, text="소스 문서 설정")
    source_mapping_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
    
    source_mapping = ttk.Frame(source_mapping_frame)
    source_mapping.pack(fill=tk.X, padx=10, pady=10)
    
    ttk.Label(source_mapping, text="항목 열:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    source_clause_cb = ttk.Combobox(source_mapping, width=30, state="readonly")
    source_clause_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
    ttk.Label(source_mapping, text="제목 열:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    source_title_cb = ttk.Combobox(source_mapping, width=30, state="readonly")
    source_title_cb.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    
    # 매핑 영역 - 오른쪽 (타겟)
    target_mapping_frame = ttk.LabelFrame(mapping_container, text="대상 문서 설정")
    target_mapping_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
    
    target_mapping = ttk.Frame(target_mapping_frame)
    target_mapping.pack(fill=tk.X, padx=10, pady=10)
    
    ttk.Label(target_mapping, text="항목 열:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    target_clause_cb = ttk.Combobox(target_mapping, width=30, state="readonly")
    target_clause_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
    ttk.Label(target_mapping, text="결과 저장 열:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    target_output_cb = ttk.Combobox(target_mapping, width=30, state="readonly")
    target_output_cb.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    
    # 항목 연결 미리보기 버튼
    preview_mapping_btn = ttk.Button(
        mapping_container,
        text="항목 연결 미리보기",
        command=preview_mapping
    )
    preview_mapping_btn.pack(pady=10)
    
    # 3. AI 프롬프트 및 실행 섹션
    prompt_card = ttk.Frame(scrollable_frame, style="Card.TFrame")
    prompt_card.pack(fill=tk.X, padx=20, pady=10)
    
    # 카드 헤더
    header_frame = ttk.Frame(prompt_card)
    header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
    
    ttk.Label(header_frame, text="3. AI 프롬프트 및 실행", style="Title.TLabel").pack(side=tk.LEFT)
    
    # 프롬프트 상태 표시 버튼
    view_prompts_btn = ttk.Button(
        header_frame, 
        text="적용된 프롬프트 보기",
        command=lambda: show_active_prompts("remark")
    )
    view_prompts_btn.pack(side=tk.RIGHT, padx=5)
    
    # 프롬프트 컨텐츠
    prompt_content = ttk.Frame(prompt_card)
    prompt_content.pack(fill=tk.X, padx=15, pady=(0, 15))
    
    # 프롬프트 설명
    prompt_desc = ttk.Label(
        prompt_content,
        text="AI가 의견을 생성할 때 적용되는 프롬프트 템플릿입니다. 프롬프트 관리 탭에서 설정할 수 있습니다.",
        wraplength=800,
        padding=(0, 5)
    )
    prompt_desc.pack(fill=tk.X, pady=(0, 10))
    
    # 프롬프트 안내 메시지
    prompt_info_frame = ttk.LabelFrame(prompt_content, text="프롬프트 설정")
    prompt_info_frame.pack(fill=tk.X, pady=10, padx=5)
    
    prompt_info_text = ttk.Label(
        prompt_info_frame, 
        text="프롬프트는 '프롬프트 관리' 탭에서 관리할 수 있습니다.\n" +
             "'보고서 생성' 유형으로 설정된 프롬프트만 이 기능에 적용됩니다.",
        wraplength=600,
        padding=10
    )
    prompt_info_text.pack(fill=tk.X)
    
    # 프롬프트 상태 표시 영역
    active_prompt_status = ttk.Label(
        prompt_info_frame,
        text="현재 적용됨: 프롬프트 0개",
        padding=5
    )
    active_prompt_status.pack(fill=tk.X)
    
    # 프롬프트 상태 업데이트
    try:
        from utils.prompt_loader import load_prompts_by_type
        
        prompts = load_prompts_by_type("remark", as_dict=True, include_metadata=True)
        count = len(prompts)
        
        active_prompt_status.config(
            text=f"현재 적용됨: 프롬프트 {count}개",
            foreground=SUCCESS_COLOR if count > 0 else WARNING_COLOR
        )
    except Exception as e:
        print(f"프롬프트 상태 업데이트 실패: {e}")
    
    # 실행 버튼
    run_frame = ttk.Frame(prompt_content)
    run_frame.pack(fill=tk.X, pady=(15, 5))
    
    run_button = ttk.Button(
        run_frame, 
        text="확장 보고서 생성 실행",
        command=handle_generate_extended,
        style="Action.TButton"
    )
    run_button.pack(fill=tk.X, pady=5)
    
    # 4. 로그 섹션
    log_card = ttk.Frame(scrollable_frame, style="Card.TFrame")
    log_card.pack(fill=tk.X, padx=20, pady=10)
    
    # 카드 헤더
    header_frame = ttk.Frame(log_card)
    header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
    
    ttk.Label(header_frame, text="4. 실행 로그", style="Title.TLabel").pack(side=tk.LEFT)
    
    # 로그 컨텐츠
    log_content = ttk.Frame(log_card)
    log_content.pack(fill=tk.X, padx=15, pady=(0, 15), expand=True)
    
    # 로그 텍스트 영역
    global log_box
    log_box = scrolledtext.ScrolledText(log_content, height=8, wrap=tk.WORD)
    log_box.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # 로그 스타일 설정
    log_box.tag_configure("success", foreground=SUCCESS_COLOR)
    log_box.tag_configure("error", foreground=ERROR_COLOR)
    log_box.tag_configure("warning", foreground=WARNING_COLOR)
    log_box.tag_configure("info", foreground=PRIMARY_COLOR)
    
    # 시작 메시지
    log_message("확장 보고서 생성 탭이 준비되었습니다. 문서를 선택하고 설정을 완료한 후 실행 버튼을 누르세요.", "info")
    
    # 규격 콤보박스 변경 핸들러 바인딩
    standard_combo.bind("<<ComboboxSelected>>", on_standard_change)
    
    return scrollable_frame

def on_source_file_selected(file_selector):
    """소스 파일 선택 시 호출"""
    global source_clause_cb, source_title_cb
    
    # 파서 가져오기
    parser = file_selector.get_parser()
    if not parser:
        return
        
    # 소스 파일 데이터프레임 가져오기 (가능한 경우)
    if hasattr(parser, 'get_dataframe'):
        df = parser.get_dataframe()
        if df is not None:
            # 열 목록 업데이트
            columns = list(df.columns)
            
            source_clause_cb["values"] = columns
            source_title_cb["values"] = columns
            
            # 자동 감지 시도
            try:
                from utils.column_detector import detect_columns
                cols = detect_columns(columns)
                
                if "clause" in cols:
                    source_clause_cb.set(cols["clause"])
                if "title" in cols:
                    source_title_cb.set(cols["title"])
                    
                log_message(f"소스 문서에서 {len(columns)}개 열을 감지했습니다.", "info")
            except Exception as e:
                log_message(f"열 자동 감지 중 오류: {e}", "warning")
    else:
        # 데이터프레임을 지원하지 않는 경우
        log_message("선택한 파일 형식은 현재 열 매핑을 지원하지 않습니다.", "warning")

def on_target_file_selected(file_selector):
    """대상 파일 선택 시 호출"""
    global target_clause_cb, target_output_cb
    
    # 파서 가져오기
    parser = file_selector.get_parser()
    if not parser:
        return
        
    # 대상 파일 데이터프레임 가져오기 (가능한 경우)
    if hasattr(parser, 'get_dataframe'):
        df = parser.get_dataframe()
        if df is not None:
            # 열 목록 업데이트
            columns = list(df.columns)
            
            target_clause_cb["values"] = columns
            target_output_cb["values"] = columns
            
            # 자동 감지 시도
            try:
                from utils.column_detector import detect_columns
                cols = detect_columns(columns)
                
                if "clause" in cols:
                    target_clause_cb.set(cols["clause"])
                if "remark" in cols:
                    target_output_cb.set(cols["remark"])
                    
                log_message(f"대상 문서에서 {len(columns)}개 열을 감지했습니다.", "info")
            except Exception as e:
                log_message(f"열 자동 감지 중 오류: {e}", "warning")
    else:
        # 데이터프레임을 지원하지 않는 경우
        log_message("대상 파일은 반드시 Excel 형식이어야 합니다.", "error")

def detect_standard_with_ai():
    """AI를 사용하여 규격 감지"""
    global source_selector, standard_var
    
    if not source_selector or not source_selector.file_path:
        messagebox.showwarning("파일 없음", "소스 문서 파일을 먼저 선택해주세요.")
        return
    
    try:
        # 진행 중임을 알림
        log_message("AI로 규격 감지 중...", "info")
        
        # 파서 가져오기
        parser = source_selector.get_parser()
        if not parser:
            log_message("문서 파서를 가져올 수 없습니다.", "error")
            return
            
        # 텍스트 내용 가져오기
        text_content = parser.get_text_content()
        if not text_content or len(text_content) < 50:
            log_message("문서에서 충분한 텍스트를 추출할 수 없습니다.", "warning")
            return
            
        # 텍스트 샘플링 (너무 길면 AI가 처리하기 어려움)
        if len(text_content) > 5000:
            text_sample = text_content[:5000] + "..."
        else:
            text_sample = text_content
        
        # AI 호출
        from api.gemini import call_gemini
        
        prompt = f"""
다음은 기술 문서의 내용 일부입니다. 이 문서가 어떤 산업 규격 또는 표준에 관련된 것인지 분석해주세요.
특히 다음 규격 중 하나인지 확인해주세요:
- IEC 60204-1 (기계류의 전기장비)
- IEC 61010 (측정, 제어 및 실험실용 전기장비)
- ISO 13849 (안전 관련 제어 시스템)
- IEC 62061 (기계류의 안전성)
- ISO 14119 (인터록 장치)
- IEC 60335 (가정용 및 유사한 전기기기)

샘플 데이터:
{text_sample}

정확히 일치하는 규격이 있다면 해당 규격의 ID만 답변해주세요 (예: "IEC_60204-1").
어떤 규격과도 일치하지 않는다면 "UNKNOWN"이라고 답변해주세요.
답변은 ID만 작성하고 다른 설명은 하지 마세요.
"""

        # 응답 처리
        response = call_gemini(prompt)
        
        # 응답에서 ID 추출
        response = response.strip().split('\n')[0]
        
        # ID 형식인지 확인
        standard_ids = ["IEC_60204-1", "IEC_61010", "ISO_13849", "IEC_62061", "ISO_14119", "IEC_60335", "UNKNOWN"]
        
        detected_id = "UNKNOWN"
        for std_id in standard_ids:
            if std_id in response:
                detected_id = std_id
                break
        
        # UI 업데이트
        if detected_id != "UNKNOWN":
            from utils.standard_detector import get_standard_info
            standard_info = get_standard_info(detected_id)
            log_message(f"AI 규격 감지 성공: {standard_info['title']}", "success")
            standard_var.set(detected_id)
        else:
            log_message("AI가 특정 규격을 감지할 수 없습니다.", "warning")
            standard_var.set("UNKNOWN")
            
    except Exception as e:
        log_message(f"AI 규격 감지 중 오류: {e}", "error")

def preview_mapping():
    """항목 연결 미리보기"""
    global source_selector, target_selector
    global source_clause_cb, target_clause_cb, matcher_mode_var
    
    # 필수 선택 확인
    if (not source_selector or not source_selector.file_path or
        not target_selector or not target_selector.file_path):
        messagebox.showwarning("파일 없음", "소스 및 대상 문서를 먼저 선택해주세요.")
        return
        
    if not source_clause_cb.get() or not target_clause_cb.get():
        messagebox.showwarning("열 선택 필요", "매핑할 항목 열을 선택해주세요.")
        return
    
    try:
        # 소스 및 대상 데이터프레임 가져오기
        source_parser = source_selector.get_parser()
        target_parser = target_selector.get_parser()
        
        if not hasattr(source_parser, 'get_dataframe') or not hasattr(target_parser, 'get_dataframe'):
            messagebox.showwarning("지원되지 않음", "선택한 파일 형식은 미리보기를 지원하지 않습니다.")
            return
        
        source_df = source_parser.get_dataframe()
        target_df = target_parser.get_dataframe()
        
        # 매처 생성
        matching_mode = matcher_mode_var.get()
        matcher = create_matcher(matching_mode)
        
        # 매핑 미리보기 창 생성
        preview_window = tk.Toplevel()
        preview_window.title("항목 연결 미리보기")
        preview_window.geometry("800x600")
        preview_window.transient(preview_window.master)
        preview_window.grab_set()
        
        # 중앙 배치
        preview_window.update_idletasks()
        width = preview_window.winfo_width()
        height = preview_window.winfo_height()
        x = (preview_window.winfo_screenwidth() // 2) - (width // 2)
        y = (preview_window.winfo_screenheight() // 2) - (height // 2)
        preview_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # 내용 구성
        frame = ttk.Frame(preview_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="항목 매핑 미리보기", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 10))
        
        # 매핑 프로세스 시작
        info_label = ttk.Label(frame, text="매핑 작업 중... 잠시 기다려주세요.")
        info_label.pack(fill=tk.X, pady=10)
        
        # 미리보기 트리뷰
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        columns = ("source_idx", "source_clause", "source_title", "target_idx", "target_clause", "confidence")
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=tree_scroll.set
        )
        tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        tree_scroll.config(command=tree.yview)
        
        # 열 설정
        tree.heading("source_idx", text="소스 인덱스")
        tree.heading("source_clause", text="소스 항목")
        tree.heading("source_title", text="소스 제목")
        tree.heading("target_idx", text="대상 인덱스")
        tree.heading("target_clause", text="대상 항목")
        tree.heading("confidence", text="신뢰도")
        
        tree.column("source_idx", width=70)
        tree.column("source_clause", width=120)
        tree.column("source_title", width=200)
        tree.column("target_idx", width=70)
        tree.column("target_clause", width=120)
        tree.column("confidence", width=70)
        
        # 버튼
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        close_btn = ttk.Button(button_frame, text="닫기", command=preview_window.destroy)
        close_btn.pack(side=tk.RIGHT)
        
        # 백그라운드 처리를 위한 업데이트
        preview_window.update()
        
        try:
            # 매핑 수행
            mappings = matcher.match_documents(
                source_df, 
                target_df,
                source_col=source_clause_cb.get(),
                target_col=target_clause_cb.get()
            )
            
            # 매핑 결과 표시
            for source_idx, target_idx, confidence in mappings:
                source_clause_val = source_df.loc[source_idx, source_clause_cb.get()]
                source_title_val = source_df.loc[source_idx, source_title_cb.get()] if source_title_cb.get() else ""
                target_clause_val = target_df.loc[target_idx, target_clause_cb.get()]
                
                tree.insert("", "end", values=(
                    source_idx,
                    source_clause_val,
                    source_title_val,
                    target_idx,
                    target_clause_val,
                    f"{confidence:.2f}"
                ))
            
            # 정보 업데이트
            info_label.config(text=f"{len(mappings)}개의 항목이 매칭되었습니다.")
            
            # AI 매칭인 경우 사용량 표시
            if matching_mode == "ai" and hasattr(matcher, 'get_api_usage'):
                usage = matcher.get_api_usage()
                usage_label = ttk.Label(frame, text=f"API 사용: {usage['calls']}번 호출, 약 {usage['tokens']}개 토큰", font=("Arial", 9), foreground="#666666")
                usage_label.pack(before=button_frame)
                
        except Exception as e:
            info_label.config(text=f"매핑 중 오류가 발생했습니다: {e}", foreground=ERROR_COLOR)
            log_message(f"매핑 미리보기 중 오류: {e}", "error")
        
    except Exception as e:
        log_message(f"미리보기 생성 중 오류: {e}", "error")
        messagebox.showerror("미리보기 오류", f"항목 연결 미리보기를 생성하는 중 오류가 발생했습니다:\n{e}")

def handle_generate_extended():
    """확장 보고서 생성 실행"""
    global source_selector, target_selector
    global source_clause_cb, source_title_cb, target_clause_cb, target_output_cb
    global matcher_mode_var, standard_var
    
    # 필수 입력값 확인
    if not source_selector or not source_selector.file_path:
        messagebox.showwarning("입력 누락", "소스 문서를 선택해주세요.")
        return
        
    if not target_selector or not target_selector.file_path:
        messagebox.showwarning("입력 누락", "대상 문서를 선택해주세요.")
        return
        
    if not all([source_clause_cb.get(), source_title_cb.get(), target_clause_cb.get(), target_output_cb.get()]):
        messagebox.showwarning("입력 누락", "매핑할 열을 모두 선택해주세요.")
        return
    
    # 소스 및 대상 설정 구성
    source_config = {
        **source_selector.get_config(),
        "clause_col": source_clause_cb.get(),
        "title_col": source_title_cb.get()
    }
    
    target_config = {
        **target_selector.get_config(),
        "clause_col": target_clause_cb.get(),
        "output_col": target_output_cb.get()
    }
    
    # 매칭 모드
    matching_mode = matcher_mode_var.get()
    
    # 선택된 규격
    standard_id = standard_var.get()
    if standard_id == "AUTO_DETECT":
        standard_id = None  # generate_from_documents 함수에서 자동 감지
    
    try:
        # 프롬프트 목록 가져오기
        from utils.prompt_loader import load_prompts_by_type
        
        prompts = load_prompts_by_type("remark", as_dict=True, include_metadata=True)
        selected_prompts = list(prompts.keys())
        
        if not selected_prompts:
            messagebox.showwarning(
                "프롬프트 없음", 
                "적용할 프롬프트가 없습니다.\n\n프롬프트 관리 탭에서 '보고서 생성' 유형의 프롬프트를 추가해주세요."
            )
            return
        
        # 작업 시작 로그
        log_message("확장 보고서 생성 시작...", "info")
        log_message(f"소스 문서: {os.path.basename(source_selector.file_path)}")
        log_message(f"대상 문서: {os.path.basename(target_selector.file_path)}")
        log_message(f"매칭 모드: {matching_mode}")
        log_message(f"적용 규격: {standard_id if standard_id else '자동 감지'}")
        log_message(f"선택된 프롬프트: {', '.join(selected_prompts)}")
        
        # 진행 상태 창 표시
        progress_window, cancel_var = show_progress_dialog("확장 보고서 생성 중", "초기화 중...")
        
        # 백그라운드에서 처리 (Thread 사용이 이상적이나, 간단한 구현을 위해 update 사용)
        from ui.gui_main import get_root
        root = get_root()
        if root:
            root.update()
        
        try:
            # 보고서 생성 실행
            out_path = generate_from_documents(
                source_selector.file_path,
                target_selector.file_path,
                source_config,
                target_config,
                selected_prompts,
                matching_mode=matching_mode,
                standard_id=standard_id,
                cancel_var=cancel_var
            )
            
            # 진행 상태 창 닫기
            if progress_window:
                progress_window.destroy()
            
            # 결과 로그
            log_message(f"✅ 성공! 결과 파일 저장 완료: {out_path}", "success")
            
            # 결과 파일 열기 확인
            if messagebox.askyesno("작업 완료", f"파일이 저장되었습니다:\n{out_path}\n\n파일을 열어보시겠습니까?"):
                try:
                    os.startfile(out_path)
                except:
                    try:
                        import subprocess
                        subprocess.Popen(['xdg-open', out_path])
                    except:
                        log_message("파일을 열 수 없습니다. 직접 열어주세요.", "warning")
        except Exception as e:
            # 진행 상태 창 닫기
            if progress_window and progress_window.winfo_exists():
                progress_window.destroy()
            
            # 오류 표시
            error_msg = str(e)
            log_message(f"❌ 오류 발생: {error_msg}", "error")
            messagebox.showerror("실행 오류", error_msg)
    except Exception as e:
        log_message(f"처리 초기화 중 오류 발생: {str(e)}", "error")
        messagebox.showerror("시스템 오류", str(e))

def show_progress_dialog(title, message):
    """진행 상태 대화상자 표시"""
    from ui.gui_main import get_root
    root = get_root()
    
    if not root:
        log_message("오류: GUI 창을 찾을 수 없습니다.", "error")
        return None, None
    
    progress_window = tk.Toplevel(root)
    progress_window.title(title)
    progress_window.geometry("400x150")
    progress_window.transient(root)
    progress_window.grab_set()
    
    # 중앙 배치
    progress_window.update_idletasks()
    width = progress_window.winfo_width()
    height = progress_window.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    progress_window.geometry(f'{width}x{height}+{x}+{y}')
    
    # 내용 구성
    frame = ttk.Frame(progress_window, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # 메시지 라벨
    message_label = ttk.Label(frame, text=message, font=("Arial", 12))
    message_label.pack(pady=(0, 20))
    
    # 진행바
    progress = ttk.Progressbar(frame, mode="indeterminate", length=300)
    progress.pack(fill=tk.X, pady=10)
    progress.start(15)
    
    # 공유 변수로 취소 상태 추적
    cancel_var = {"cancelled": False}
    
    # 취소 버튼
    cancel_btn = ttk.Button(
        frame, 
        text="취소",
        command=lambda: set_cancelled(cancel_var, progress_window)
    )
    cancel_btn.pack(pady=10)
    
    return progress_window, cancel_var

def set_cancelled(var, window):
    """취소 버튼 클릭 시 처리"""
    var["cancelled"] = True
    window.title(f"{window.title()} (취소 중...)")

def on_standard_change(event=None):
    """규격 콤보박스 변경 핸들러"""
    standard_id = standard_var.get()
    log_message(f"규격 선택: {standard_id}", "info")
