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

# 채팅 컨텍스트 모듈 추가 (AI 채팅과의 연동을 위해)
from utils import chat_context

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

# AI 채팅 히스토리 사용 관련 변수
use_chat_history_var = None
chat_context_status_label = None
chat_status_indicator = None
connect_btn = None

def create_extended_report_tab(parent):
    """확장된 보고서 생성 탭 구성 - 개선된 UI"""
    global source_selector, target_selector
    global source_clause_cb, target_clause_cb, matcher_mode_var
    global source_title_cb, target_output_cb, standard_var
    global use_chat_history_var, chat_context_status_label, chat_status_indicator, connect_btn
    global standard_frame  # 규격 설정 프레임 참조 추가
    
    # 메인 프레임 - 배경 스타일 추가
    main_frame = ttk.Frame(parent, padding=15)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 스타일 설정 시도
    try:
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Arial", 16, "bold"), foreground=PRIMARY_COLOR)
        style.configure("SubHeader.TLabel", font=("Arial", 11), foreground="#555555")
    except Exception as e:
        log_message(f"스타일 설정 오류: {str(e)}", "warning")
    
    # 제목 영역 - 더 시각적으로 두드러지게 만들기
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill=tk.X, padx=5, pady=(0, 15))
    
    header_content = ttk.Frame(header_frame, padding=15)
    header_content.pack(fill=tk.X)
    
    # 상단 아이콘 및 제목
    title_frame = ttk.Frame(header_content)
    title_frame.pack(fill=tk.X)
    
    # AI 아이콘 라벨
    ttk.Label(
        title_frame, 
        text="🤖",  # AI 아이콘 이모티콘
        font=("Arial", 22),
        foreground=PRIMARY_COLOR
    ).pack(side=tk.LEFT, padx=(0, 10))
    
    # 메인 제목
    ttk.Label(
        title_frame, 
        text="확장 보고서 생성기", 
        font=("Arial", 16, "bold"),
        foreground=PRIMARY_COLOR
    ).pack(side=tk.LEFT)
    
    # 구분선
    separator = ttk.Separator(header_content, orient="horizontal")
    separator.pack(fill=tk.X, pady=(10, 10))
    
    # 설명 텍스트
    ttk.Label(
        header_content, 
        text="다양한 문서 형식에서 규격 기반 보고서를 지능적으로 생성합니다. AI 매칭 기능으로 더 정확한 항목 연결을 제공합니다.",
        wraplength=850,
        font=("Arial", 11),
        foreground="#555555"
    ).pack(fill=tk.X)
    
    # 컨텐츠 영역을 2개 컬럼으로 분할
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(fill=tk.BOTH, expand=True)
    
    # 왼쪽 패널 (문서 선택)
    left_frame = ttk.LabelFrame(content_frame, text="문서 설정", padding=10)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
    
    # 오른쪽 패널 (설정 및 실행)
    right_frame = ttk.LabelFrame(content_frame, text="옵션 설정", padding=10)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
    
    # === 왼쪽 패널 내용 ===
    
    # 소스 문서 선택 - 시각적 개선
    source_frame = ttk.LabelFrame(left_frame, text="검토용 문서", padding=10)
    source_frame.pack(fill=tk.X, pady=(0, 10))
    
    # 소스 문서 설명
    ttk.Label(
        source_frame, 
        text="검토할 문서를 선택하세요. Excel, PDF, Word 형식이 지원됩니다.",
        wraplength=400,
        foreground="#555555"
    ).pack(fill=tk.X, pady=(0, 10))
    
    source_selector = FileSelector(
        source_frame, 
        title="검토할 문서", 
        supported_types=[
            ("모든 지원 파일", "*.xlsx *.xls *.pdf *.docx *.doc"),
            ("Excel 파일", "*.xlsx *.xls"),
            ("PDF 파일", "*.pdf"),
            ("Word 파일", "*.docx *.doc")
        ],
        callback=on_source_file_selected
    )
    
    # 소스 파일 작업 버튼 프레임 추가
    source_action_frame = ttk.Frame(source_frame)
    source_action_frame.pack(fill=tk.X, pady=(5, 0))
    
    # 파일 미리보기 버튼
    preview_source_btn = ttk.Button(
        source_action_frame,
        text="미리보기",
        command=lambda: preview_source_file(),
        width=10
    )
    preview_source_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    # 파일 분석 버튼
    analyze_source_btn = ttk.Button(
        source_action_frame,
        text="내용 분석",
        command=lambda: analyze_source_file(),
        width=10
    )
    analyze_source_btn.pack(side=tk.LEFT, padx=5)
    
    # 대상 문서 선택 - 시각적 개선
    target_frame = ttk.LabelFrame(left_frame, text="결과 문서", padding=10)
    target_frame.pack(fill=tk.X)
    
    # 대상 문서 설명
    ttk.Label(
        target_frame, 
        text="검토 결과를 저장할 문서를 선택하세요. Excel 형식만 지원됩니다.",
        wraplength=400,
        foreground="#555555"
    ).pack(fill=tk.X, pady=(0, 10))
    
    target_selector = FileSelector(
        target_frame, 
        title="결과 저장할 문서",
        supported_types=[("Excel 파일", "*.xlsx *.xls")],
        callback=on_target_file_selected
    )
    
    # 대상 파일 작업 버튼 프레임 추가
    target_action_frame = ttk.Frame(target_frame)
    target_action_frame.pack(fill=tk.X, pady=(5, 0))
    
    # 파일 미리보기 버튼
    preview_target_btn = ttk.Button(
        target_action_frame,
        text="미리보기",
        command=lambda: preview_target_file(),
        width=10
    )
    preview_target_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    # 파일 편집 버튼
    edit_target_btn = ttk.Button(
        target_action_frame,
        text="파일 편집",
        command=lambda: edit_target_file(),
        width=10
    )
    edit_target_btn.pack(side=tk.LEFT, padx=5)
    
    # 저장 경로 변경 버튼
    change_output_path_btn = ttk.Button(
        target_action_frame,
        text="저장 경로",
        command=lambda: change_output_path(),
        width=10
    )
    change_output_path_btn.pack(side=tk.LEFT, padx=5)
    
    # === 오른쪽 패널 내용 ===
    
    # 열 매핑 프레임 - 시각적 개선
    mapping_frame = ttk.LabelFrame(right_frame, text="열 매핑", padding=10)
    mapping_frame.pack(fill=tk.X, pady=(0, 10))
    
    # 열 선택 설명
    ttk.Label(
        mapping_frame, 
        text="검토 문서와 결과 문서 간의 열 매핑을 설정합니다. AI 매칭에도 이 설정이 필요합니다.",
        wraplength=400,
        foreground="#555555"
    ).pack(fill=tk.X, pady=(0, 10))
    
    # 소스 문서 열 설정
    source_col_frame = ttk.Frame(mapping_frame)
    source_col_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(source_col_frame, text="검토 문서 항목 열:", width=15).pack(side=tk.LEFT)
    source_clause_cb = ttk.Combobox(source_col_frame, width=25, state="readonly")
    source_clause_cb.pack(side=tk.LEFT, padx=5)
    
    ttk.Label(source_col_frame, text="항목 제목 열:", width=15).pack(side=tk.LEFT, padx=(10, 0))
    source_title_cb = ttk.Combobox(source_col_frame, width=25, state="readonly")
    source_title_cb.pack(side=tk.LEFT, padx=5)
    
    # 대상 문서 열 설정
    target_col_frame = ttk.Frame(mapping_frame)
    target_col_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(target_col_frame, text="결과 문서 항목 열:", width=15).pack(side=tk.LEFT)
    target_clause_cb = ttk.Combobox(target_col_frame, width=25, state="readonly")
    target_clause_cb.pack(side=tk.LEFT, padx=5)
    
    ttk.Label(target_col_frame, text="결과 작성 열:", width=15).pack(side=tk.LEFT, padx=(10, 0))
    target_output_cb = ttk.Combobox(target_col_frame, width=25, state="readonly")
    target_output_cb.pack(side=tk.LEFT, padx=5)
    
    # 규격 설정 영역 - 시각적 개선
    standard_frame = ttk.LabelFrame(right_frame, text="규격 설정", padding=10)
    standard_frame.pack(fill=tk.X, pady=(0, 10))
    
    # 규격 설정 설명
    ttk.Label(
        standard_frame, 
        text="적용할 산업 규격을 선택하거나 자동으로 감지하도록 설정합니다.",
        wraplength=400,
        foreground="#555555"
    ).pack(fill=tk.X, pady=(0, 10))
    
    # 규격 선택 영역
    standard_selection_frame = ttk.Frame(standard_frame)
    standard_selection_frame.pack(fill=tk.X, pady=5)
    
    # 규격 선택
    ttk.Label(standard_selection_frame, text="적용 규격:", width=10).pack(side=tk.LEFT)
    
    standard_var = tk.StringVar(value="AUTO_DETECT")
    standard_dropdown = ttk.Combobox(
        standard_selection_frame, 
        textvariable=standard_var,
        width=25, 
        state="readonly"
    )
    standard_dropdown.pack(side=tk.LEFT, padx=5)
    standard_dropdown["values"] = ["AUTO_DETECT", "IEC_60204-1", "IEC_61010", "ISO_13849", "IEC_62061", "ISO_14119", "UNKNOWN"]
    standard_dropdown.bind("<<ComboboxSelected>>", on_standard_change)
    
    # 규격 버튼 영역 - 시각적 개선
    standard_btn_frame = ttk.Frame(standard_selection_frame)
    standard_btn_frame.pack(side=tk.LEFT, padx=10)
    
    # AI 감지 버튼
    detect_btn = ttk.Button(
        standard_btn_frame, 
        text="AI로 감지", 
        command=detect_standard_with_ai,
        width=12
    )
    detect_btn.pack(side=tk.LEFT, padx=2)
    
    # 규격 관리 버튼 - UI 강조
    manage_btn = ttk.Button(
        standard_btn_frame, 
        text="규격 수동 관리", 
        command=manage_standards,
        width=15
    )
    manage_btn.pack(side=tk.LEFT, padx=2)
    
    # 규격 아이콘 및 설명 - UI 개선
    standard_info_frame = ttk.Frame(standard_frame)
    standard_info_frame.pack(fill=tk.X, pady=(10, 0))
    
    # 아이콘
    standard_icon_label = ttk.Label(standard_info_frame, text="📋", font=("Arial", 18))
    standard_icon_label.pack(side=tk.LEFT, padx=(5, 10))
    
    # 규격 설명
    standard_desc = tk.Text(standard_info_frame, height=4, wrap=tk.WORD)
    standard_desc.pack(side=tk.LEFT, fill=tk.X, expand=True)
    standard_desc.insert(tk.END, "자동 감지 모드: 검토 문서의 내용을 분석하여 적절한 규격을 자동으로 감지합니다.")
    standard_desc.config(state="disabled", background="#f8f8f8", relief="flat")
    
    # 매칭 설정 영역 - UI 개선 및 설명 추가
    match_frame = ttk.LabelFrame(right_frame, text="매칭 설정", padding=10)
    match_frame.pack(fill=tk.X, pady=(0, 10))
    
    # 매칭 설명
    ttk.Label(
        match_frame, 
        text="문서 항목을 연결하는 방법을 선택합니다. AI 매칭은 더 높은 정확도를 제공합니다.",
        wraplength=400,
        foreground="#555555"
    ).pack(fill=tk.X, pady=(0, 10))
    
    matcher_mode_var = tk.StringVar(value="basic")
    
    # 매칭 모드 라디오 버튼
    basic_radio = ttk.Radiobutton(
        match_frame, 
        text="기본 매칭 (유사한 항목 번호 매칭)", 
        variable=matcher_mode_var, 
        value="basic"
    )
    basic_radio.pack(anchor=tk.W, pady=(0, 5))
    
    ai_radio = ttk.Radiobutton(
        match_frame, 
        text="AI 매칭 (내용 분석 기반 지능형 매칭) - 권장", 
        variable=matcher_mode_var, 
        value="ai"
    )
    ai_radio.pack(anchor=tk.W)
    
    # AI 매칭 설명 배지
    ai_badge_frame = ttk.Frame(match_frame)
    ai_badge_frame.pack(fill=tk.X, pady=(5, 0), padx=(20, 0))
    
    ai_badge_label = ttk.Label(
        ai_badge_frame,
        text="※ AI 매칭에도 열 설정이 필요합니다. AI가 글자를 비교하려면 어떤 열을 보아야 할지 알아야 합니다.",
        wraplength=400,
        foreground="#555555",
        font=("Arial", 9)
    )
    ai_badge_label.pack(anchor=tk.W)
    
    # AI 채팅 연결 영역 - UI 개선
    chat_frame = ttk.LabelFrame(right_frame, text="AI 채팅 연결", padding=10)
    chat_frame.pack(fill=tk.X)
    
    # 채팅 연결 설명
    ttk.Label(
        chat_frame, 
        text="AI 채팅 탭의 대화 내용을 보고서 생성에 활용할지 설정합니다.",
        wraplength=400,
        foreground="#555555"
    ).pack(fill=tk.X, pady=(0, 10))
    
    # 채팅 히스토리 사용 체크박스
    use_chat_history_var = tk.BooleanVar(value=False)
    chat_history_check = ttk.Checkbutton(
        chat_frame,
        text="기존 채팅 내역 활용 (채팅 탭의 대화 내용 참조)",
        variable=use_chat_history_var,
        command=update_chat_context_status
    )
    chat_history_check.pack(anchor=tk.W, pady=(0, 5))
    
    # AI 채팅 상태
    chat_status_frame = ttk.Frame(chat_frame)
    chat_status_frame.pack(fill=tk.X)
    
    chat_status_indicator = ttk.Label(
        chat_status_frame,
        text="●",
        font=("Arial", 16, "bold"),
        foreground=ERROR_COLOR,  # 기본값은 연결 안됨
        padding=(0, 0, 5, 0)
    )
    chat_status_indicator.pack(side=tk.LEFT)
    
    chat_context_status_label = ttk.Label(
        chat_status_frame,
        text="연결 안됨",
        font=("Arial", 10),
        foreground="#888888",
        padding=5
    )
    chat_context_status_label.pack(side=tk.LEFT)
    
    connect_btn = ttk.Button(
        chat_status_frame, 
        text="채팅 탭 열기", 
        command=go_to_chat_tab,
        width=15
    )
    connect_btn.pack(side=tk.RIGHT)
    
    # 하단 버튼 영역 - UI 개선
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(15, 0))
    
    # 매핑 미리보기 버튼
    preview_btn = ttk.Button(
        button_frame, 
        text="📊 항목 매칭 미리보기", 
        command=preview_mapping,
        width=20
    )
    preview_btn.pack(side=tk.LEFT)
    
    # 결과 생성 버튼 - 강조
    generate_btn = ttk.Button(
        button_frame, 
        text="✨ 결과 생성", 
        command=handle_generate_extended,
        width=15,
        style="Primary.TButton"  # 강조 스타일 적용
    )
    generate_btn.pack(side=tk.RIGHT)
    
    # AI 채팅 연결 상태 초기화
    update_chat_context_status()
    
    return main_frame

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
                
                # 채팅 컨텍스트에 파일 추가 (AI 채팅과 연동)
                try:
                    from utils.chat_context import add_loaded_file
                    add_loaded_file(
                        file_path=file_selector.file_path,
                        file_type="review_sheet",
                        columns={
                            "clause": cols.get("clause", ""),
                            "title": cols.get("title", "")
                        },
                        sheet_name=file_selector.get_config().get("sheet_name"),
                        detected_standard=standard_var.get() if standard_var.get() not in ["AUTO_DETECT", "UNKNOWN"] else None
                    )
                    log_message("채팅 컨텍스트에 검토 문서 정보가 추가되었습니다.", "info")
                    update_chat_context_status()  # 채팅 연결 상태 업데이트
                except Exception as e:
                    log_message(f"채팅 컨텍스트 업데이트 오류: {e}", "warning")
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
                
                # 채팅 컨텍스트에 파일 추가 (AI 채팅과 연동)
                try:
                    from utils.chat_context import add_loaded_file
                    add_loaded_file(
                        file_path=file_selector.file_path,
                        file_type="target",
                        columns={
                            "clause": cols.get("clause", ""),
                            "remark": cols.get("remark", "")
                        },
                        sheet_name=file_selector.get_config().get("sheet_name")
                    )
                    log_message("채팅 컨텍스트에 결과 문서 정보가 추가되었습니다.", "info")
                    update_chat_context_status()  # 채팅 연결 상태 업데이트
                except Exception as e:
                    log_message(f"채팅 컨텍스트 업데이트 오류: {e}", "warning")
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
    global source_clause_cb, target_clause_cb, matcher_mode_var, source_title_cb
    
    # 필수 선택 확인 - 사용자 친화적 메시지로 개선
    if (not source_selector or not source_selector.file_path):
        messagebox.showwarning("문서가 필요합니다", "검토할 문서를 먼저 선택해주세요.")
        return
        
    if (not target_selector or not target_selector.file_path):
        messagebox.showwarning("결과 문서가 필요합니다", "결과를 저장할 문서를 선택해주세요.")
        return
        
    if not source_clause_cb.get() or not target_clause_cb.get():
        messagebox.showwarning("열 설정이 필요합니다", "두 문서의 '항목 열'을 모두 선택해주세요.")
        return
    
    try:
        # 소스 및 대상 데이터프레임 가져오기
        source_parser = source_selector.get_parser()
        target_parser = target_selector.get_parser()
        
        if not hasattr(source_parser, 'get_dataframe') or not hasattr(target_parser, 'get_dataframe'):
            messagebox.showwarning("지원되지 않는 형식", "현재 선택한 파일 형식에서는 미리보기를 제공할 수 없습니다.")
            return
        
        source_df = source_parser.get_dataframe()
        target_df = target_parser.get_dataframe()
        
        # 매처 생성
        matching_mode = matcher_mode_var.get()
        log_message(f"{'AI 매칭' if matching_mode == "ai" else '기본 매칭'} 방식으로 항목 연결 중...", "info")
        matcher = create_matcher(matching_mode)
        
        # 미리보기 창 생성 - UI 개선
        preview_window = tk.Toplevel()
        preview_window.title("문서 항목 연결 미리보기")
        preview_window.geometry("900x600")
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
        
        # 개선된 헤더
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(header_frame, text="문서 항목 연결 미리보기", 
                 font=("Arial", 14, "bold")).pack(side=tk.LEFT)
        
        if matching_mode == "ai":
            ai_badge = ttk.Label(
                header_frame, 
                text="AI 매칭",
                foreground="white",
                background=PRIMARY_COLOR,
                padding=(5, 2)
            )
            ai_badge.pack(side=tk.LEFT, padx=10)
        
        # 매핑 프로세스 시작
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_label = ttk.Label(
            info_frame, 
            text="항목 연결 작업을 수행하는 중입니다. 잠시만 기다려주세요...",
            font=("Arial", 10),
            foreground="#666666"
        )
        info_label.pack(side=tk.LEFT)
        
        # 미리보기 트리뷰 UI 개선
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tree_scroll_y = ttk.Scrollbar(tree_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 열 구성 개선
        columns = ("source_clause", "source_title", "target_clause", "confidence")
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )
        tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        tree_scroll_y.config(command=tree.yview)
        tree_scroll_x.config(command=tree.xview)
        
        # 열 이름 개선
        tree.heading("source_clause", text="검토 문서 항목")
        tree.heading("source_title", text="검토 문서 제목")
        tree.heading("target_clause", text="결과 문서 항목")
        tree.heading("confidence", text="일치도")
        
        # 열 너비 조정
        tree.column("source_clause", width=200, minwidth=100)
        tree.column("source_title", width=300, minwidth=100)
        tree.column("target_clause", width=200, minwidth=100)
        tree.column("confidence", width=80, minwidth=50)
        
        # 설명 추가
        desc_frame = ttk.Frame(frame)
        desc_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(
            desc_frame, 
            text="* 일치도는 두 항목이 얼마나 유사한지 보여줍니다 (0~1, 높을수록 일치)",
            font=("Arial", 9),
            foreground="#666666"
        ).pack(anchor="w")
        
        # 버튼 영역
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        export_btn = ttk.Button(
            button_frame, 
            text="목록 내보내기",
            command=lambda: export_mapping_list(tree)
        )
        export_btn.pack(side=tk.LEFT)
        
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
            
            # 매핑 결과 표시 - 사용자 친화적으로 변경
            for source_idx, target_idx, confidence in mappings:
                # 항목 값 가져오기
                source_clause_val = str(source_df.loc[source_idx, source_clause_cb.get()])
                target_clause_val = str(target_df.loc[target_idx, target_clause_cb.get()])
                
                # 제목 값 가져오기 (선택 사항)
                if source_title_cb.get() and source_title_cb.get() in source_df.columns:
                    source_title_val = str(source_df.loc[source_idx, source_title_cb.get()])
                else:
                    source_title_val = "-"
                
                # 신뢰도 형식 지정
                confidence_val = f"{confidence:.2f}"
                
                # 행 추가
                tree.insert("", "end", values=(
                    source_clause_val,
                    source_title_val,
                    target_clause_val,
                    confidence_val
                ))
                
                # 신뢰도에 따른 색상 설정
                if confidence >= 0.8:
                    # 높은 신뢰도
                    pass  # 기본 색상 사용
                elif confidence >= 0.5:
                    # 중간 신뢰도
                    pass  # 향후 확장 가능성
                else:
                    # 낮은 신뢰도
                    pass  # 향후 확장 가능성
            
            # 정보 업데이트
            if mappings:
                avg_confidence = sum(conf for _, _, conf in mappings) / len(mappings)
                result_text = f"{len(mappings)}개 항목이 연결되었습니다. 평균 일치도: {avg_confidence:.2f}"
                result_color = SUCCESS_COLOR
            else:
                result_text = "연결된 항목이 없습니다. 설정을 확인하세요."
                result_color = WARNING_COLOR
                
            info_label.config(
                text=result_text, 
                foreground=result_color,
                font=("Arial", 10, "bold")
            )
            
            # AI 매칭인 경우 사용량 표시 (개선)
            if matching_mode == "ai" and hasattr(matcher, 'get_api_usage'):
                usage = matcher.get_api_usage()
                usage_frame = ttk.Frame(frame)
                usage_frame.pack(before=button_frame, fill=tk.X, pady=5)
                
                ttk.Label(
                    usage_frame, 
                    text=f"API 사용 정보: {usage['calls']}번 호출, 약 {usage['tokens']}개 토큰", 
                    font=("Arial", 9), 
                    foreground="#666666"
                ).pack(side=tk.LEFT)
            
            # 작업 완료 로그
            log_message(f"항목 연결 미리보기: {len(mappings)}개 항목 연결됨", "success")
            
        except Exception as e:
            info_label.config(
                text=f"항목 연결 중 오류가 발생했습니다", 
                foreground=ERROR_COLOR,
                font=("Arial", 10, "bold")
            )
            
            error_frame = ttk.Frame(frame)
            error_frame.pack(before=button_frame, fill=tk.X, pady=5)
            
            ttk.Label(
                error_frame,
                text=str(e),
                foreground=ERROR_COLOR,
                wraplength=800
            ).pack(fill=tk.X)
            
            log_message(f"항목 연결 미리보기 오류: {e}", "error")
        
    except Exception as e:
        log_message(f"미리보기 생성 중 오류: {e}", "error")
        messagebox.showerror("미리보기 오류", f"항목 연결 미리보기를 생성하는 중 문제가 발생했습니다:\n\n{e}")

def export_mapping_list(tree):
    """항목 연결 목록 내보내기"""
    try:
        # 저장 파일 위치 선택
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV 파일", "*.csv"), ("텍스트 파일", "*.txt"), ("Excel 파일", "*.xlsx")],
            title="항목 연결 목록 저장"
        )
        
        if not filename:
            return
            
        # 파일 확장자에 따른 처리
        ext = os.path.splitext(filename)[1].lower()
        
        # 트리뷰 데이터 수집
        data = []
        columns = ['검토 문서 항목', '검토 문서 제목', '결과 문서 항목', '일치도']
        
        for item_id in tree.get_children():
            values = tree.item(item_id, 'values')
            data.append(values)
            
        if ext == '.csv' or ext == '.txt':
            # CSV 형식으로 저장
            import csv
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for row in data:
                    writer.writerow(row)
                    
        elif ext == '.xlsx':
            # Excel 형식으로 저장
            try:
                import pandas as pd
                df = pd.DataFrame(data, columns=columns)
                df.to_excel(filename, index=False)
            except ImportError:
                messagebox.showwarning("모듈 없음", "Excel 파일 저장을 위한 pandas 모듈이 필요합니다.")
                return
                
        log_message(f"항목 연결 목록이 저장되었습니다: {filename}", "success")
        messagebox.showinfo("저장 완료", f"항목 연결 목록이 저장되었습니다:\n{filename}")
        
    except Exception as e:
        log_message(f"항목 연결 목록 내보내기 오류: {e}", "error")
        messagebox.showerror("내보내기 오류", f"항목 연결 목록을 저장하는 중 오류가 발생했습니다:\n\n{e}")

def handle_generate_extended():
    """확장 보고서 생성 실행"""
    global source_selector, target_selector
    global source_clause_cb, source_title_cb, target_clause_cb, target_output_cb
    global matcher_mode_var, standard_var, use_chat_history_var, log_box
    
    # 필수 입력값 확인 - 사용자 친화적 메시지로 개선
    if not source_selector or not source_selector.file_path:
        messagebox.showwarning("문서가 필요합니다", "검토할 문서를 먼저 선택해주세요.")
        return
        
    if not target_selector or not target_selector.file_path:
        messagebox.showwarning("결과 문서가 필요합니다", "결과를 저장할 문서를 선택해주세요.")
        return
        
    # 열 설정 확인을 더 친절한 메시지로 표시
    missing_cols = []
    if not source_clause_cb.get():
        missing_cols.append("검토할 문서의 '항목 열'")
    if not source_title_cb.get():
        missing_cols.append("검토할 문서의 '제목 열'")
    if not target_clause_cb.get():
        missing_cols.append("결과 문서의 '항목 열'")
    if not target_output_cb.get():
        missing_cols.append("결과 문서의 '결과 저장 열'")
    
    if missing_cols:
        messagebox.showwarning("열 설정이 필요합니다", 
                               f"다음 항목을 선택해주세요:\n\n• " + "\n• ".join(missing_cols))
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
                "프롬프트가 필요합니다", 
                "적용할 프롬프트가 없습니다.\n\n'프롬프트 관리' 탭에서 '보고서 생성' 유형의 프롬프트를 추가하세요."
            )
            return
        
        # AI 채팅 컨텍스트 처리
        chat_history = None
        if use_chat_history_var.get():
            try:
                # 채팅 컨텍스트 가져오기
                chat_files = chat_context.get_loaded_files()
                chat_history = chat_context.get_chat_history()
                
                if chat_files:
                    log_message(f"AI 채팅 연결: {len(chat_files)}개 파일 컨텍스트 활용", "info")
                
                if chat_history:
                    log_message(f"AI 채팅 연결: {len(chat_history)}개 대화 내용 활용", "info")
                else:
                    log_message("AI 채팅 연결: 활용할 대화 내용이 없습니다", "warning")
            except Exception as e:
                log_message(f"채팅 연결 중 문제 발생: {str(e)}", "error")
                chat_history = None
        
        # 작업 시작 로그
        log_message("✨ 확장 보고서 생성 시작...", "info")
        log_message(f"📄 검토 문서: {os.path.basename(source_selector.file_path)}")
        log_message(f"💾 결과 문서: {os.path.basename(target_selector.file_path)}")
        log_message(f"🔄 연결 방식: {'AI 매칭' if matching_mode == 'ai' else '기본 매칭'}")
        log_message(f"📏 적용 규격: {standard_id if standard_id else '자동 감지'}")
        log_message(f"📋 프롬프트: {len(selected_prompts)}개")
        
        # 진행 상태 창 표시
        progress_window, cancel_var = show_progress_dialog("확장 보고서 생성 중...", "파일을 분석하는 중입니다...")
        
        # 백그라운드에서 처리 (Thread 사용이 이상적이나, 간단한 구현을 위해 update 사용)
        from ui.gui_main import get_root
        root = get_root()
        if root:
            root.update()
        
        try:
            # 보고서 생성 실행
            from logic.extended_generator import generate_from_documents
            
            out_path = generate_from_documents(
                source_selector.file_path,
                target_selector.file_path,
                source_config,
                target_config,
                selected_prompts,
                matching_mode=matching_mode,
                standard_id=standard_id,
                cancel_var=cancel_var,
                chat_history=chat_history  # 채팅 히스토리 전달
            )
            
            # 진행 상태 창 닫기
            if progress_window and progress_window.winfo_exists():
                progress_window.destroy()
            
            # 결과 로그
            log_message(f"✅ 작업 완료! 파일이 저장되었습니다: {out_path}", "success")
            
            # 결과 파일 열기 확인
            if messagebox.askyesno("작업 완료", f"확장 보고서가 생성되었습니다.\n\n저장 위치:\n{out_path}\n\n지금 파일을 열어보시겠습니까?"):
                try:
                    os.startfile(out_path)
                except:
                    try:
                        import subprocess
                        subprocess.Popen(['xdg-open', out_path])
                    except Exception as e:
                        log_message(f"파일을 열지 못했습니다: {str(e)}", "warning")
                        messagebox.showinfo("안내", f"파일 위치: {out_path}\n\n파일 탐색기에서 직접 열어주세요.")
        except Exception as e:
            # 진행 상태 창 닫기
            if progress_window and progress_window.winfo_exists():
                progress_window.destroy()
            
            # 오류 표시 - 자세한 오류 메시지 개선
            error_msg = str(e)
            error_type = "알 수 없는 오류"
            
            if "api" in error_msg.lower() or "key" in error_msg.lower():
                error_type = "API 연결 오류"
            elif "file" in error_msg.lower() or "permission" in error_msg.lower():
                error_type = "파일 접근 오류"
            elif "match" in error_msg.lower():
                error_type = "문서 매칭 오류"
            elif "prompt" in error_msg.lower():
                error_type = "프롬프트 오류"
            
            log_message(f"❌ {error_type}: {error_msg}", "error")
            messagebox.showerror(f"{error_type}", f"보고서 생성 중 문제가 발생했습니다:\n\n{error_msg}")
    except Exception as e:
        log_message(f"시스템 오류: {str(e)}", "error")
        messagebox.showerror("시스템 오류", f"처리 초기화 중 문제가 발생했습니다:\n\n{str(e)}\n\n개발자에게 문의하세요.")

def show_progress_dialog(title, message):
    """진행 상태 대화상자 표시"""
    from ui.gui_main import get_root
    root = get_root()
    
    if not root:
        log_message("오류: GUI 창을 찾을 수 없습니다.", "error")
        return None, None
    
    # 개선된 UI 디자인의 진행 대화상자
    progress_window = tk.Toplevel(root)
    progress_window.title(title)
    progress_window.geometry("450x200")
    progress_window.transient(root)
    progress_window.grab_set()
    progress_window.resizable(False, False)
    
    # 중앙 배치
    progress_window.update_idletasks()
    width = progress_window.winfo_width()
    height = progress_window.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    progress_window.geometry(f'{width}x{height}+{x}+{y}')
    
    # 내용 구성 - 보다 시각적인 디자인
    frame = ttk.Frame(progress_window, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # 상단 안내 텍스트
    info_label = ttk.Label(
        frame, 
        text="AI가 문서를 분석하고 있습니다",
        font=("Arial", 13, "bold"),
        foreground=PRIMARY_COLOR
    )
    info_label.pack(pady=(0, 5))
    
    # 상세 메시지 라벨
    message_label = ttk.Label(
        frame, 
        text=message,
        font=("Arial", 10),
        wraplength=400
    )
    message_label.pack(pady=(0, 15))
    
    # 단계별 처리 프레임
    steps_frame = ttk.Frame(frame)
    steps_frame.pack(fill=tk.X, pady=5)
    
    # 각 단계 레이블 (초기 단계 활성화)
    step_labels = []
    
    step1 = ttk.Label(steps_frame, text="① 문서 분석", foreground=PRIMARY_COLOR, font=("Arial", 9, "bold"))
    step1.pack(side=tk.LEFT, padx=(0, 10))
    step_labels.append(step1)
    
    ttk.Label(steps_frame, text="→").pack(side=tk.LEFT, padx=5)
    
    step2 = ttk.Label(steps_frame, text="② 항목 연결", foreground="#888888", font=("Arial", 9))
    step2.pack(side=tk.LEFT, padx=5)
    step_labels.append(step2)
    
    ttk.Label(steps_frame, text="→").pack(side=tk.LEFT, padx=5)
    
    step3 = ttk.Label(steps_frame, text="③ AI 분석", foreground="#888888", font=("Arial", 9))
    step3.pack(side=tk.LEFT, padx=5)
    step_labels.append(step3)
    
    ttk.Label(steps_frame, text="→").pack(side=tk.LEFT, padx=5)
    
    step4 = ttk.Label(steps_frame, text="④ 결과 저장", foreground="#888888", font=("Arial", 9))
    step4.pack(side=tk.LEFT, padx=5)
    step_labels.append(step4)
    
    # 진행바
    progress = ttk.Progressbar(frame, mode="indeterminate", length=400)
    progress.pack(fill=tk.X, pady=15)
    progress.start(15)
    
    # 취소 변수 및 버튼
    cancel_var = tk.BooleanVar(value=False)
    
    def on_cancel():
        cancel_var.set(True)
        # 취소 버튼 비활성화
        cancel_btn.config(state="disabled", text="취소 중...")
        message_label.config(text="작업을 취소하는 중입니다...")
        progress_window.update()
    
    # 취소 버튼
    cancel_btn = ttk.Button(frame, text="취소", command=on_cancel)
    cancel_btn.pack(pady=(5, 0))
    
    # 단계 업데이트 메서드 추가
    def update_step(step_num):
        for i, label in enumerate(step_labels):
            if i == step_num - 1:  # 현재 단계
                label.config(foreground=PRIMARY_COLOR, font=("Arial", 9, "bold"))
                message_label.config(text=get_step_message(step_num))
            elif i < step_num - 1:  # 완료된 단계
                label.config(foreground=SUCCESS_COLOR, font=("Arial", 9))
            else:  # 아직 시작되지 않은 단계
                label.config(foreground="#888888", font=("Arial", 9))
        
        # 강제 업데이트
        progress_window.update()
    
    def get_step_message(step):
        if step == 1:
            return "문서 내용을 분석하고 항목을 추출하는 중입니다..."
        elif step == 2:
            return "두 문서 간 항목을 연결하고 매칭하는 중입니다..."
        elif step == 3:
            return "AI를 활용하여 내용을 분석하고 권장사항을 생성중입니다..."
        elif step == 4:
            return "결과를 문서에 저장하고 있습니다..."
        return message
    
    # 단계 업데이트 메서드 연결
    progress_window.update_step = update_step
    
    return progress_window, cancel_var

def manage_standards():
    """규격 수동 관리 창"""
    # 상위 창 가져오기
    from ui.gui_main import get_root
    root = get_root()
    if not root:
        log_message("UI가 초기화되지 않았습니다.", "error")
        return
        
    # 규격 관리 창 생성
    std_window = tk.Toplevel(root)
    std_window.title("규격 관리")
    std_window.geometry("800x600")
    std_window.transient(root)
    std_window.grab_set()
    
    # 중앙 배치
    std_window.update_idletasks()
    width = std_window.winfo_width()
    height = std_window.winfo_height()
    x = (std_window.winfo_screenwidth() // 2) - (width // 2)
    y = (std_window.winfo_screenheight() // 2) - (height // 2)
    std_window.geometry(f'{width}x{height}+{x}+{y}')
    
    # 메인 프레임
    main_frame = ttk.Frame(std_window, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 제목
    ttk.Label(
        main_frame, 
        text="규격 관리", 
        font=("Arial", 16, "bold"),
        foreground=PRIMARY_COLOR
    ).pack(anchor="w", pady=(0, 20))
    
    # 설명
    ttk.Label(
        main_frame,
        text="규격을 수동으로 관리하고 편집할 수 있습니다. 검토 문서 내용을 기반으로 AI가 자동으로 규격을 식별합니다.",
        wraplength=700
    ).pack(fill=tk.X, pady=(0, 20))
    
    # 규격 목록 프레임
    list_frame = ttk.LabelFrame(main_frame, text="규격 목록")
    list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
    
    # 규격 트리뷰
    tree_frame = ttk.Frame(list_frame)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    tree_scroll = ttk.Scrollbar(tree_frame)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    tree = ttk.Treeview(
        tree_frame,
        columns=("id", "name", "description"),
        show="headings",
        selectmode="browse",
        yscrollcommand=tree_scroll.set
    )
    tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    tree_scroll.config(command=tree.yview)
    
    # 열 구성
    tree.heading("id", text="규격 ID")
    tree.heading("name", text="규격명")
    tree.heading("description", text="설명")
    
    tree.column("id", width=150, minwidth=100)
    tree.column("name", width=200, minwidth=150)
    tree.column("description", width=400, minwidth=200)
    
    # 규격 정보 가져오기
    try:
        from utils.standard_detector import get_all_standards
        standards = get_all_standards()
        
        # 트리뷰에 규격 정보 추가
        for std_id, std_info in standards.items():
            tree.insert("", "end", values=(
                std_id,
                std_info.get("title", ""),
                std_info.get("description", "")
            ))
    except Exception as e:
        log_message(f"규격 정보를 가져오는 중 오류: {e}", "error")
    
    # 상세 정보 프레임
    detail_frame = ttk.LabelFrame(main_frame, text="규격 상세 정보")
    detail_frame.pack(fill=tk.X, pady=(0, 20))
    
    detail_inner = ttk.Frame(detail_frame, padding=10)
    detail_inner.pack(fill=tk.X, expand=True)
    
    ttk.Label(detail_inner, text="규격 ID:").grid(row=0, column=0, sticky="w", pady=5)
    id_var = tk.StringVar()
    id_entry = ttk.Entry(detail_inner, textvariable=id_var, width=30)
    id_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
    
    ttk.Label(detail_inner, text="규격명:").grid(row=1, column=0, sticky="w", pady=5)
    name_var = tk.StringVar()
    name_entry = ttk.Entry(detail_inner, textvariable=name_var, width=30)
    name_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
    
    ttk.Label(detail_inner, text="설명:").grid(row=2, column=0, sticky="w", pady=5)
    desc_var = tk.StringVar()
    desc_entry = ttk.Entry(detail_inner, textvariable=desc_var, width=50)
    desc_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
    
    ttk.Label(detail_inner, text="핵심 키워드:").grid(row=3, column=0, sticky="w", pady=5)
    keywords_var = tk.StringVar()
    keywords_entry = ttk.Entry(detail_inner, textvariable=keywords_var, width=50)
    keywords_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
    
    # 트리뷰 선택 시 이벤트 처리
    def on_tree_select(event):
        selected_items = tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        values = tree.item(item, 'values')
        if not values:
            return
            
        # 선택된 규격 정보 표시
        std_id = values[0]
        
        try:
            from utils.standard_detector import get_standard_info
            std_info = get_standard_info(std_id)
            
            id_var.set(std_id)
            name_var.set(std_info.get("title", ""))
            desc_var.set(std_info.get("description", ""))
            keywords_var.set(", ".join(std_info.get("keywords", [])))
        except Exception as e:
            log_message(f"규격 정보를 표시하는 중 오류: {e}", "error")
    
    tree.bind("<<TreeviewSelect>>", on_tree_select)
    
    # 버튼 프레임
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X)
    
    # 규격 업데이트 함수
    def update_standard():
        std_id = id_var.get().strip()
        name = name_var.get().strip()
        desc = desc_var.get().strip()
        keywords = [k.strip() for k in keywords_var.get().split(",") if k.strip()]
        
        if not std_id:
            messagebox.showwarning("입력 오류", "규격 ID는 필수입니다.")
            return
            
        if not name:
            messagebox.showwarning("입력 오류", "규격명은 필수입니다.")
            return
        
        try:
            from utils.standard_detector import update_standard_info
            updated = update_standard_info(std_id, {
                "title": name,
                "description": desc,
                "keywords": keywords
            })
            
            if updated:
                log_message(f"규격 정보가 업데이트되었습니다: {std_id}", "success")
                messagebox.showinfo("성공", "규격 정보가 업데이트되었습니다.")
                
                # 트리뷰 갱신
                for item in tree.get_children():
                    if tree.item(item, 'values')[0] == std_id:
                        tree.item(item, values=(std_id, name, desc))
                        break
            else:
                log_message(f"규격 정보 업데이트에 실패했습니다: {std_id}", "error")
                messagebox.showerror("오류", "규격 정보 업데이트에 실패했습니다.")
        except Exception as e:
            log_message(f"규격 정보 업데이트 중 오류: {e}", "error")
            messagebox.showerror("오류", f"규격 정보 업데이트 중 오류가 발생했습니다:\n{str(e)}")
    
    # 버튼 추가
    update_btn = ttk.Button(
        button_frame,
        text="정보 업데이트",
        command=update_standard,
        width=15
    )
    update_btn.pack(side=tk.LEFT, padx=5)
    
    close_btn = ttk.Button(
        button_frame,
        text="닫기",
        command=std_window.destroy,
        width=10
    )
    close_btn.pack(side=tk.RIGHT)
    
    # 도움말
    help_text = "* 규격 정보를 수정하고 '정보 업데이트' 버튼을 클릭하면 변경사항이 저장됩니다.\n"
    help_text += "* 키워드는 AI가 문서에서 규격을 감지할 때 사용하는 주요 단어입니다."
    
    help_label = ttk.Label(
        main_frame, 
        text=help_text,
        foreground="#666666",
        font=("Arial", 9),
        wraplength=700
    )
    help_label.pack(pady=(20, 0), anchor="w")
    
    # 창이 닫힐 때 규격 드롭다운 업데이트
    def on_close():
        # 규격 변수 및 드롭다운이 있는 경우 갱신
        global standard_var
        if standard_var:
            current_value = standard_var.get()
            try:
                from utils.standard_detector import get_all_standards
                standards = get_all_standards()
                std_ids = list(standards.keys())
                
                # 현재 표시된 드롭다운 찾기
                for widget in root.winfo_children():
                    if isinstance(widget, ttk.Combobox) and widget.get() == current_value:
                        widget["values"] = ["AUTO_DETECT"] + std_ids + ["UNKNOWN"]
                        break
            except:
                pass
        
        std_window.destroy()
    
    std_window.protocol("WM_DELETE_WINDOW", on_close)

def go_to_chat_tab():
    """채팅 탭으로 이동"""
    from ui.gui_main import get_notebook
    notebook = get_notebook()
    if notebook:
        # 두 번째 탭(AI 채팅)으로 이동
        notebook.select(1)

def on_standard_change(event=None):
    """규격 선택 변경 시 호출"""
    global standard_var
    
    try:
        std_id = standard_var.get()
        
        # 규격 정보 가져오기
        from utils.standard_detector import get_standard_info
        
        std_info = get_standard_info(std_id)
        if std_info:
            # 규격 설명 텍스트 업데이트
            for widget in standard_frame.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Text):
                            child.config(state="normal")
                            child.delete("1.0", tk.END)
                            child.insert(tk.END, std_info.get("description", "설명 없음"))
                            child.config(state="disabled")
                            break
    except Exception as e:
        log_message(f"규격 정보 업데이트 중 오류: {e}", "error")

def update_chat_context_status():
    """채팅 컨텍스트 상태 업데이트"""
    global use_chat_history_var, chat_context_status_label, chat_status_indicator
    
    if not chat_context_status_label or not chat_status_indicator:
        return
        
    try:
        # 채팅 컨텍스트 가져오기
        from utils.chat_context import get_chat_context_info
        
        context_info = get_chat_context_info()
        
        if use_chat_history_var.get():
            # 채팅 내역 사용 활성화 상태
            if context_info and context_info.get("messages", []):
                # 활성 채팅 내역이 있음
                msg_count = len(context_info.get("messages", []))
                chat_context_status_label.config(
                    text=f"채팅 내역 활성화: {msg_count}개 메시지 참조",
                    foreground=SUCCESS_COLOR
                )
                chat_status_indicator.config(foreground=SUCCESS_COLOR)
            else:
                # 활성 채팅 내역이 없음
                chat_context_status_label.config(
                    text="채팅 내역 활성화: 참조할 메시지 없음",
                    foreground=WARNING_COLOR
                )
                chat_status_indicator.config(foreground=WARNING_COLOR)
        else:
            # 채팅 내역 사용 비활성화 상태
            chat_context_status_label.config(
                text="채팅 내역 비활성화: 채팅 참조 안함",
                foreground="#888888"
            )
            chat_status_indicator.config(foreground=ERROR_COLOR)
    except Exception as e:
        log_message(f"채팅 컨텍스트 상태 업데이트 중 오류: {str(e)}", "warning")
        chat_context_status_label.config(text=f"상태 확인 오류", foreground=ERROR_COLOR)
        chat_status_indicator.config(foreground=ERROR_COLOR)
```
