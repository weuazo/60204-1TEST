import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import os
from datetime import datetime

# UI 설정 및 유틸리티 임포트
from ui.ui_utils import (
    log_message, show_active_prompts, set_log_box,
    PRIMARY_COLOR, SECONDARY_COLOR, BG_COLOR, CARD_COLOR, TEXT_COLOR, 
    SUCCESS_COLOR, WARNING_COLOR, ERROR_COLOR, BORDER_COLOR, HOVER_COLOR
)

# 전역 상태 변수 
base_template_path = ""
review_sheet_path = ""
sheet_name_selected = None
column_options = []

# UI 요소
clause_cb = None
title_cb = None
remark_cb = None
prompt_cb = None
sheet_preview = None
base_preview = None  # 템플릿 파일 미리보기 트리뷰 추가
preview_notebook = None  # 미리보기 노트북 (탭)
sheet_cb = None
sheet_label = None
output_col_cb = None
base_entry = None
review_entry = None
log_box = None
detected_standard_label = None
match_mode_var = None
preview_status_label = None  # 미리보기 상태 레이블 추가
standard_var = None
standard_combo = None
active_standard_info = None

def create_report_tab(parent):
    """보고서 생성 탭 구성"""
    global sheet_cb, sheet_label, clause_cb, title_cb, remark_cb
    global prompt_cb, log_box, sheet_preview, base_preview, preview_notebook
    global output_col_cb, base_entry, review_entry, preview_status_label
    global detected_standard_label, match_mode_var, standard_var, standard_combo, active_standard_info  # 전역 변수로 추가
    
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
        text="보고서 생성 진행 단계: 파일 선택 → 열 연결 설정 → 미리보기 확인 → AI 프롬프트 적용 → 실행",
        font=("Arial", 10),
        foreground=PRIMARY_COLOR
    )
    workflow_label.pack(anchor="w")
    
    # 1. 파일 선택 섹션
    file_card = ttk.Frame(scrollable_frame, style="Card.TFrame")
    file_card.pack(fill=tk.X, padx=20, pady=10)
    
    # 카드 헤더
    header_frame = ttk.Frame(file_card)
    header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
    
    ttk.Label(header_frame, text="1. 파일 선택", style="Title.TLabel").pack(side=tk.LEFT)
    
    # 파일 선택 설명 추가
    file_desc = ttk.Label(
        file_card,
        text="작업에 사용할 두 개의 파일을 선택해주세요. 올바른 파일이 선택되면 자동으로 규격과 시트를 감지합니다.",
        wraplength=800,
        padding=(15, 5, 15, 5)
    )
    file_desc.pack(fill=tk.X)
    
    # 파일 선택 컨텐츠
    file_content = ttk.Frame(file_card)
    file_content.pack(fill=tk.X, padx=15, pady=(0, 15))
    
    # 템플릿 파일
    base_frame = ttk.Frame(file_content)
    base_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(base_frame, text="템플릿 파일:", width=12).grid(row=0, column=0, padx=5, pady=8, sticky="w")
    base_entry = ttk.Entry(base_frame, width=60)
    base_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
    
    browse_base_btn = ttk.Button(
        base_frame, 
        text="찾아보기", 
        command=browse_base_template,
        style="TButton"
    )
    browse_base_btn.grid(row=0, column=2, padx=5, pady=5)
    
    # 템플릿 파일 설명 레이블
    base_desc = ttk.Label(
        base_frame, 
        text="의견을 저장할 양식 파일", 
        foreground="#666666", 
        font=("Arial", 9)
    )
    base_desc.grid(row=0, column=3, padx=5, pady=5)
    
    # 검토 시트 파일
    review_frame = ttk.Frame(file_content)
    review_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(review_frame, text="검토 시트 파일:", width=12).grid(row=0, column=0, padx=5, pady=8, sticky="w")
    review_entry = ttk.Entry(review_frame, width=60)
    review_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
    
    browse_review_btn = ttk.Button(
        review_frame, 
        text="찾아보기", 
        command=browse_review_sheet,
        style="TButton"
    )
    browse_review_btn.grid(row=0, column=2, padx=5, pady=5)
    
    # 검토 시트 설명 레이블
    review_desc = ttk.Label(
        review_frame, 
        text="검토 대상 항목이 있는 파일", 
        foreground="#666666", 
        font=("Arial", 9)
    )
    review_desc.grid(row=0, column=3, padx=5, pady=5)
    
    # 시트 선택 영역
    sheet_frame = ttk.Frame(file_content)
    sheet_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(sheet_frame, text="시트 선택:", width=12).grid(row=0, column=0, padx=5, pady=5, sticky="w")
    sheet_cb = ttk.Combobox(sheet_frame, width=40, state="readonly")
    sheet_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    sheet_cb.bind("<<ComboboxSelected>>", on_sheet_change)
    
    sheet_label = ttk.Label(sheet_frame, text="선택된 시트: -", style="TLabel")
    sheet_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
    
    # 규격 감지 및 선택 영역 개선
    standard_frame = ttk.LabelFrame(file_content, text="규격 설정")
    standard_frame.pack(fill=tk.X, pady=10, padx=5)
    
    # 규격 설정 안내
    standard_desc = ttk.Label(
        standard_frame,
        text="규격을 자동으로 감지하거나 직접 선택할 수 있습니다. 사용자 선택이 항상 우선합니다.",
        wraplength=700,
        font=("Arial", 9),
        padding=(5, 5, 5, 5)
    )
    standard_desc.pack(fill=tk.X, padx=10, pady=5)
    
    # 규격 선택 및 감지 영역
    standard_controls = ttk.Frame(standard_frame)
    standard_controls.pack(fill=tk.X, padx=10, pady=5)
    
    # 자동 감지 결과 표시
    detected_frame = ttk.Frame(standard_controls)
    detected_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    ttk.Label(detected_frame, text="감지된 규격:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    detected_standard_label = ttk.Label(detected_frame, text="아직 감지되지 않음", foreground=WARNING_COLOR)
    detected_standard_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
    # AI 규격 감지 버튼
    detect_btn = ttk.Button(
        detected_frame, 
        text="AI 규격 감지", 
        command=lambda: detect_standard_with_ai()
    )
    detect_btn.grid(row=0, column=2, padx=5, pady=5)
    
    # 규격 콤보박스 및 커스텀 규격 영역
    standard_selection_frame = ttk.Frame(standard_controls)
    standard_selection_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 0))
    
    ttk.Label(standard_selection_frame, text="선택된 규격:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
    # 규격 선택용 콤보박스 - 기본 규격 + 커스텀 규격 + 자동 감지
    standard_var = tk.StringVar(value="")
    standard_combo = ttk.Combobox(
        standard_selection_frame, 
        textvariable=standard_var, 
        width=40,
        state="readonly"
    )
    standard_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
    # 기본 규격 목록 설정
    standard_options = [
        "",  # 빈 값 = 선택 안함
        "AUTO_DETECT",  # AI 감지 결과 사용
        "IEC_60204-1",
        "IEC_61010",
        "ISO_13849",
        "IEC_62061",
        "ISO_14119",
        "IEC_60335",
        "커스텀 규격 추가..."  # 새 규격 추가 옵션
    ]
    standard_combo["values"] = standard_options
    
    # 규격 편집 버튼
    edit_standard_btn = ttk.Button(
        standard_selection_frame,
        text="규격 관리",
        command=lambda: show_standard_editor()
    )
    edit_standard_btn.grid(row=0, column=2, padx=5, pady=5)
    
    # 표시된 규격 정보 영역
    active_standard_frame = ttk.Frame(standard_frame)
    active_standard_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
    
    ttk.Label(active_standard_frame, text="적용될 규격:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))
    active_standard_info = ttk.Label(
        active_standard_frame,
        text="선택한 규격이 없습니다. 일반적인 기준으로 검토합니다.",
        font=("Arial", 9),
        foreground="#666666"
    )
    active_standard_info.pack(side=tk.LEFT)
    
    # 콤보박스 선택 변경 이벤트 핸들러
    def on_standard_change(event=None):
        selected = standard_var.get()
        if selected == "커스텀 규격 추가...":
            # 커스텀 규격 추가 대화상자 표시
            add_custom_standard()
            # 선택을 이전 값으로 복원
            standard_var.set("")
        elif selected == "AUTO_DETECT":
            # 자동 감지 결과 표시
            from utils.standard_detector import get_standard_info
            detected_id = getattr(detected_standard_label, "standard_id", "UNKNOWN")
            standard_info = get_standard_info(detected_id)
            active_standard_info.config(
                text=f"{standard_info['title']} (AI 감지 결과 사용)",
                foreground=SUCCESS_COLOR
            )
        elif selected:
            # 선택된 규격 정보 표시
            from utils.standard_detector import get_standard_info
            standard_info = get_standard_info(selected)
            active_standard_info.config(
                text=f"{standard_info['title']} (수동 선택됨)",
                foreground=PRIMARY_COLOR
            )
        else:
            # 선택 없음
            active_standard_info.config(
                text="선택한 규격이 없습니다. 일반적인 기준으로 검토합니다.",
                foreground="#666666"
            )
    
    standard_combo.bind("<<ComboboxSelected>>", on_standard_change)

    # 규격 감지 정확도 설정
    matching_options_frame = ttk.Frame(standard_frame)
    matching_options_frame.pack(fill=tk.X, padx=10, pady=5)
    
    ttk.Label(matching_options_frame, text="항목 매칭:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
    match_mode_var = tk.StringVar(value="flexible")
    ttk.Radiobutton(matching_options_frame, text="정확히 일치", variable=match_mode_var, 
                    value="exact").grid(row=0, column=1, padx=5, pady=5, sticky="w")
    ttk.Radiobutton(matching_options_frame, text="유연한 매칭", variable=match_mode_var, 
                    value="flexible").grid(row=0, column=2, padx=5, pady=5, sticky="w")
    
    match_info = ttk.Label(matching_options_frame, text="유연한 매칭은 '8.2.1'과 '8.2'같은 비슷한 항목도 찾습니다", 
                  foreground="#666666", font=("Arial", 9))
    match_info.grid(row=0, column=3, padx=5, pady=5, sticky="w")
    
    # 도움말 텍스트
    help_frame = tk.Frame(file_content, bg=HOVER_COLOR, bd=1, relief="solid")
    help_frame.pack(fill=tk.X, pady=10)
    
    help_text = """
📌 파일 선택 팁:
• 두 개의 다른 엑셀 파일을 선택해주세요.
• 첫 번째는 기본 템플릿 파일로, 항목과 비고란이 포함된 파일입니다.
• 두 번째는 검토 시트로, 검토 의견을 반영할 항목 정보가 있는 파일입니다.
• 두 파일은 항목 번호(Clause)로 서로 매칭됩니다.
"""
    
    help_label = tk.Label(
        help_frame, 
        text=help_text, 
        justify=tk.LEFT, 
        bg=HOVER_COLOR, 
        fg=TEXT_COLOR,
        font=("Arial", 10),
        anchor="w",
        padx=15, 
        pady=15
    )
    help_label.pack(fill=tk.X)
    
    # 2. 파일 간 항목 연결 설정 - 제목 변경하여 더 직관적으로
    column_card = ttk.Frame(scrollable_frame, style="Card.TFrame")
    column_card.pack(fill=tk.X, padx=20, pady=10)
    
    # 카드 헤더
    header_frame = ttk.Frame(column_card)
    header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
    
    ttk.Label(header_frame, text="2. 파일 간 항목 연결 설정", style="Title.TLabel").pack(side=tk.LEFT)
    
    # 열 매핑 컨텐츠
    column_content = ttk.Frame(column_card)
    column_content.pack(fill=tk.X, padx=15, pady=(0, 15))
    
    # 초보자도 이해할 수 있는 매칭 설명 추가
    mapping_desc = ttk.Label(
        column_content,
        text="AI가 두 파일 사이에서 같은 항목을 찾아 의견을 생성하려면 아래 정보가 필요합니다.",
        wraplength=800,
        padding=(0, 5)
    )
    mapping_desc.pack(fill=tk.X, pady=(0, 10))
    
    # 직관적인 매칭 다이어그램 추가
    matching_diagram_frame = tk.Frame(column_content, bg=HOVER_COLOR, bd=1, relief="solid")
    matching_diagram_frame.pack(fill=tk.X, pady=(0, 10))
    
    diagram_content = tk.Frame(matching_diagram_frame, bg=HOVER_COLOR)
    diagram_content.pack(fill=tk.X, padx=15, pady=10)
    
    # 검토 시트 박스
    review_box = tk.Frame(diagram_content, bg="#e1f5fe", bd=1, relief="solid", padx=10, pady=10)
    review_box.grid(row=0, column=0, padx=10)
    
    tk.Label(review_box, text="📊 검토 시트", font=("Arial", 10, "bold"), bg="#e1f5fe").pack()
    tk.Label(review_box, text="항목 열 → 항목 번호 읽기", bg="#e1f5fe").pack()
    tk.Label(review_box, text="제목 열 → 내용 정보 읽기", bg="#e1f5fe").pack()
    
    # 화살표
    arrow_frame = tk.Frame(diagram_content, bg=HOVER_COLOR)
    arrow_frame.grid(row=0, column=1)
    
    tk.Label(arrow_frame, text="→", font=("Arial", 16), bg=HOVER_COLOR).pack(padx=5, pady=15)
    
    # 매칭 프로세스 박스
    process_box = tk.Frame(diagram_content, bg="#fff9c4", bd=1, relief="solid", padx=10, pady=10)
    process_box.grid(row=0, column=2, padx=10)
    
    tk.Label(process_box, text="🔄 항목 매칭", font=("Arial", 10, "bold"), bg="#fff9c4").pack()
    tk.Label(process_box, text="항목 번호로 연결", bg="#fff9c4").pack()
    tk.Label(process_box, text="AI가 의견 생성", bg="#fff9c4").pack()
    
    # 화살표
    arrow_frame2 = tk.Frame(diagram_content, bg=HOVER_COLOR)
    arrow_frame2.grid(row=0, column=3)
    
    tk.Label(arrow_frame2, text="→", font=("Arial", 16), bg=HOVER_COLOR).pack(padx=5, pady=15)
    
    # 템플릿 박스
    template_box = tk.Frame(diagram_content, bg="#e8f5e9", bd=1, relief="solid", padx=10, pady=10)
    template_box.grid(row=0, column=4, padx=10)
    
    tk.Label(template_box, text="📋 템플릿 파일", font=("Arial", 10, "bold"), bg="#e8f5e9").pack()
    tk.Label(template_box, text="항목 번호로 위치 찾기", bg="#e8f5e9").pack()
    tk.Label(template_box, text="결과 저장 열에 의견 저장", bg="#e8f5e9").pack()
    
    # 열 매핑 그리드
    mapping_frame = ttk.Frame(column_content)
    mapping_frame.pack(fill=tk.X, pady=10)
    
    # 라벨 열
    label_frame = ttk.Frame(mapping_frame)
    label_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
    
    ttk.Label(label_frame, text="항목 열 (검토 시트):").pack(anchor="e", pady=10)
    ttk.Label(label_frame, text="제목 열 (검토 시트):").pack(anchor="e", pady=10)
    ttk.Label(label_frame, text="결과 저장 열 (템플릿 파일):").pack(anchor="e", pady=10)
    
    # 콤보박스 열
    combo_frame = ttk.Frame(mapping_frame)
    combo_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    clause_cb = ttk.Combobox(combo_frame, width=50, state="readonly")
    clause_cb.pack(fill=tk.X, pady=5)
    
    title_cb = ttk.Combobox(combo_frame, width=50, state="readonly")
    title_cb.pack(fill=tk.X, pady=5)
    
    output_col_cb = ttk.Combobox(combo_frame, width=50, state="readonly")
    output_col_cb.pack(fill=tk.X, pady=5)
    
    # 추가 정보 레이블 열
    info_frame = ttk.Frame(mapping_frame)
    info_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
    
    clause_info = ttk.Label(info_frame, text="규격 항목 번호가 있는 열", foreground="#666666", font=("Arial", 9))
    clause_info.pack(pady=10)
    
    title_info = ttk.Label(info_frame, text="항목 제목이나 설명이 있는 열", foreground="#666666", font=("Arial", 9))
    title_info.pack(pady=10)
    
    remark_info = ttk.Label(info_frame, text="AI 검토 의견이 저장될 열", foreground="#666666", font=("Arial", 9))
    remark_info.pack(pady=10)
    
    # 매핑 도움말 프레임
    mapping_help_frame = tk.Frame(column_content, bg=HOVER_COLOR, bd=1, relief="solid")
    mapping_help_frame.pack(fill=tk.X, pady=(10, 0))
    
    mapping_help_text = """
📝 열 연결 가이드:
• 항목 열: 검토 시트에서 규격 항목 번호가 있는 열입니다 (예: "8.2.1", "4.3")
• 제목 열: 검토 시트에서 항목의 제목이나 설명이 있는 열입니다
• 결과 저장 열: 템플릿 파일에서 AI가 생성한 검토 의견을 저장할 열입니다

💡 AI는 검토 시트의 항목 번호와 제목을 읽고, 같은 항목 번호를 템플릿 파일에서 찾아 의견을 기입합니다.
"""
    
    mapping_help_label = tk.Label(
        mapping_help_frame, 
        text=mapping_help_text, 
        justify=tk.LEFT, 
        bg=HOVER_COLOR, 
        fg=TEXT_COLOR,
        font=("Arial", 10),
        anchor="w",
        padx=15, 
        pady=15
    )
    mapping_help_label.pack(fill=tk.X)
    
    # 3. 미리보기 섹션
    preview_card = ttk.Frame(scrollable_frame, style="Card.TFrame")
    preview_card.pack(fill=tk.X, padx=20, pady=10)
    
    # 카드 헤더
    header_frame = ttk.Frame(preview_card)
    header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
    
    ttk.Label(header_frame, text="3. 파일 미리보기", style="Title.TLabel").pack(side=tk.LEFT)
    
    # 미리보기 설명 추가
    preview_desc = ttk.Label(
        preview_card,
        text="선택된 파일의 내용을 확인하세요. 좌우로 스크롤하여 모든 열을 볼 수 있습니다.",
        wraplength=800,
        padding=(15, 5)
    )
    preview_desc.pack(fill=tk.X)
    
    # 미리보기 컨텐츠
    preview_content = ttk.Frame(preview_card)
    preview_content.pack(fill=tk.X, padx=15, pady=(0, 15), expand=True)
    
    # 탭으로 두 개의 미리보기 제공 (검토 시트와 템플릿)
    preview_notebook = ttk.Notebook(preview_content)
    preview_notebook.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # 검토 시트 미리보기 탭
    review_preview_frame = ttk.Frame(preview_notebook)
    preview_notebook.add(review_preview_frame, text="📊 검토 시트 미리보기")
    
    # 트리뷰와 스크롤바 (검토 시트)
    review_tree_frame = ttk.Frame(review_preview_frame)
    review_tree_frame.pack(fill=tk.BOTH, expand=True)
    
    review_scroll_y = ttk.Scrollbar(review_tree_frame, orient="vertical")
    review_scroll_x = ttk.Scrollbar(review_tree_frame, orient="horizontal")
    
    sheet_preview = ttk.Treeview(
        review_tree_frame, 
        height=10,
        yscrollcommand=review_scroll_y.set,
        xscrollcommand=review_scroll_x.set
    )
    
    review_scroll_y.config(command=sheet_preview.yview)
    review_scroll_x.config(command=sheet_preview.xview)
    
    sheet_preview.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    review_scroll_y.pack(fill=tk.Y, side=tk.RIGHT)
    review_scroll_x.pack(fill=tk.X, side=tk.BOTTOM)
    
    # 템플릿 파일 미리보기 탭
    template_preview_frame = ttk.Frame(preview_notebook)
    preview_notebook.add(template_preview_frame, text="📋 템플릿 파일 미리보기")
    
    # 트리뷰와 스크롤바 (템플릿 파일)
    template_tree_frame = ttk.Frame(template_preview_frame)
    template_tree_frame.pack(fill=tk.BOTH, expand=True)
    
    template_scroll_y = ttk.Scrollbar(template_tree_frame, orient="vertical")
    template_scroll_x = ttk.Scrollbar(template_tree_frame, orient="horizontal")
    
    base_preview = ttk.Treeview(
        template_tree_frame, 
        height=10,
        yscrollcommand=template_scroll_y.set,
        xscrollcommand=template_scroll_x.set
    )
    
    template_scroll_y.config(command=base_preview.yview)
    template_scroll_x.config(command=base_preview.xview)
    
    base_preview.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    template_scroll_y.pack(fill=tk.Y, side=tk.RIGHT)
    template_scroll_x.pack(fill=tk.X, side=tk.BOTTOM)
    
    # 미리보기 상태 표시줄 추가
    preview_status_frame = ttk.Frame(preview_content)
    preview_status_frame.pack(fill=tk.X, pady=(5, 0))
    
    preview_status_label = ttk.Label(
        preview_status_frame, 
        text="총 0개 열 중 0개 표시 중 (모든 열을 보려면 가로 스크롤 사용)", 
        font=("Arial", 9), 
        foreground="#666666"
    )
    preview_status_label.pack(side=tk.LEFT)
    
    # 4. 프롬프트 및 실행 섹션
    prompt_card = ttk.Frame(scrollable_frame, style="Card.TFrame")
    prompt_card.pack(fill=tk.X, padx=20, pady=10)
    
    # 카드 헤더
    header_frame = ttk.Frame(prompt_card)
    header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
    
    ttk.Label(header_frame, text="4. AI 프롬프트 및 실행", style="Title.TLabel").pack(side=tk.LEFT)
    
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
    
    # 프롬프트 설명 추가
    prompt_desc = ttk.Label(
        prompt_content,
        text="AI가 의견을 생성할 때 적용되는 프롬프트 템플릿입니다. 프롬프트 관리 탭에서 설정할 수 있습니다.",
        wraplength=800,
        padding=(0, 5)
    )
    prompt_desc.pack(fill=tk.X, pady=(0, 10))
    
    # 프롬프트 안내 메시지 (체크박스 영역 대체)
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
    
    # 프롬프트 상태 표시 영역 (몇 개의 프롬프트가 적용되는지)
    active_prompt_status = ttk.Label(
        prompt_info_frame,
        text="현재 적용됨: 프롬프트 0개",
        padding=5
    )
    active_prompt_status.pack(fill=tk.X)
    
    # 프롬프트 상태 업데이트 함수 수정
    def update_prompt_status():
        """프롬프트 상태 업데이트 함수"""
        try:
            from utils.prompt_loader import load_prompts_by_type
            
            prompts = load_prompts_by_type("remark", as_dict=True, include_metadata=True)
            count = len(prompts)
            
            if 'active_prompt_status' in globals() and active_prompt_status:
                try:
                    active_prompt_status.config(
                        text=f"현재 적용됨: 프롬프트 {count}개",
                        foreground=SUCCESS_COLOR if count > 0 else WARNING_COLOR
                    )
                except tk.TclError:
                    print("프롬프트 상태 위젯이 더 이상 유효하지 않습니다.")
        except Exception as e:
            print(f"프롬프트 상태 업데이트 실패: {e}")
    
    # 초기 상태 업데이트
    update_prompt_status()
    
    # 결과 확인 정보 표시 (중복 제거)
    result_info_frame = ttk.Frame(prompt_content)
    result_info_frame.pack(fill=tk.X, pady=10)
    
    result_info = ttk.Label(
        result_info_frame,
        text="위에서 선택한 '결과 저장 열'에 AI가 생성한 검토 의견이 저장됩니다.",
        foreground="#666666",
        font=("Arial", 9)
    )
    result_info.pack(side=tk.LEFT)
    
    # 실행 버튼
    run_frame = ttk.Frame(prompt_content)
    run_frame.pack(fill=tk.X, pady=(15, 5))
    
    run_button = ttk.Button(
        run_frame, 
        text="보고서 생성 실행",
        command=handle_generate,
        style="Action.TButton"
    )
    run_button.pack(fill=tk.X, pady=5)
    
    # 5. 로그 섹션
    log_card = ttk.Frame(scrollable_frame, style="Card.TFrame")
    log_card.pack(fill=tk.X, padx=20, pady=10)
    
    # 카드 헤더
    header_frame = ttk.Frame(log_card)
    header_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
    
    ttk.Label(header_frame, text="5. 실행 로그", style="Title.TLabel").pack(side=tk.LEFT)
    
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
    
    # 전역 로그 박스 설정
    set_log_box(log_box)
    
    # 시작 메시지
    log_message("시스템 준비 완료. 파일을 선택하고 '보고서 생성 실행' 버튼을 누르세요.", "info")

def on_sheet_change(event):
    """시트 선택 변경 시 호출"""
    global sheet_name_selected
    sheet_name_selected = sheet_cb.get()
    refresh_columns()

def browse_base_template():
    """템플릿 파일 선택"""
    global base_template_path
    try:
        filetypes = [("Excel 파일", "*.xlsx *.xls")]
        path = filedialog.askopenfilename(title="템플릿 파일 선택", filetypes=filetypes)
        
        if not path:
            return  # 사용자가 취소함

        # 경로 저장 및 표시
        base_template_path = path
        base_entry.delete(0, tk.END)
        base_entry.insert(0, path)
        
        # 파일 로드 및 확인
        try:
            df = pd.read_excel(path)
            log_message(f"템플릿 파일 로드 성공: {os.path.basename(path)} ({len(df)}행)")
            
            # 템플릿 파일 미리보기 업데이트
            update_base_preview(df)
        except Exception as e:
            log_message(f"템플릿 파일 로드 실패: {str(e)}", "error")
            messagebox.showerror("파일 오류", f"템플릿 파일을 읽을 수 없습니다: {e}")
    except Exception as e:
        log_message(f"파일 선택 오류: {str(e)}", "error")
        messagebox.showerror("오류", f"파일 선택 중 오류 발생: {e}")

def browse_review_sheet():
    """검토 시트 파일 선택"""
    global review_sheet_path
    try:
        filetypes = [("Excel 파일", "*.xlsx *.xls")]
        path = filedialog.askopenfilename(title="검토 시트 파일 선택", filetypes=filetypes)
        
        if not path:
            return  # 사용자가 취소함

        # 경로 저장 및 표시
        review_sheet_path = path
        review_entry.delete(0, tk.END)
        review_entry.insert(0, path)
        
        # 규격 감지 시도
        try:
            from utils.standard_detector import detect_standard_from_file, get_standard_info
            
            standard_id = detect_standard_from_file(path)
            standard_info = get_standard_info(standard_id)
            
            # UI 업데이트
            global detected_standard_label  # 명시적으로 전역 변수 참조
            if 'detected_standard_label' in globals() and detected_standard_label:
                if standard_id != "UNKNOWN":
                    detected_standard_label.config(
                        text=f"{standard_info['title']} (자동 감지됨)",
                        foreground=SUCCESS_COLOR
                    )
                    log_message(f"규격 자동 감지: {standard_info['title']}", "info")
                else:
                    detected_standard_label.config(
                        text="규격을 자동으로 감지할 수 없습니다",
                        foreground=WARNING_COLOR
                    )
        except ImportError:
            log_message("규격 감지 모듈을 불러올 수 없습니다.", "warning")
        except Exception as e:
            log_message(f"규격 감지 중 오류: {e}", "warning")
        
        # 시트 목록 새로고침
        refresh_sheet_list()
    except Exception as e:
        log_message(f"파일 선택 오류: {str(e)}", "error")
        messagebox.showerror("오류", f"파일 선택 중 오류 발생: {e}")

def refresh_sheet_list():
    """시트 목록 새로고침"""
    global sheet_cb, sheet_label, sheet_name_selected
    
    if not review_sheet_path:
        return
        
    try:
        xl = pd.ExcelFile(review_sheet_path)
        sheet_names = xl.sheet_names
        
        if not sheet_names:
            raise ValueError("시트가 존재하지 않습니다.")

        # 콤보박스 업데이트
        sheet_cb["values"] = sheet_names
        sheet_cb.set(sheet_names[0])
        sheet_name_selected = sheet_names[0]
        sheet_label.config(text=f"선택된 시트: {sheet_name_selected}")
        
        # 열 목록 새로고침
        refresh_columns()
        
        log_message(f"검토 시트 파일 로드 성공: {os.path.basename(review_sheet_path)} ({len(sheet_names)}개 시트)")
    except Exception as e:
        log_message(f"시트 목록 로드 실패: {str(e)}", "error")
        messagebox.showerror("시트 목록 오류", str(e))

def refresh_columns():
    """열 목록 새로고침"""
    global column_options
    
    if not review_sheet_path or not sheet_name_selected:
        return
        
    try:
        # 시트에서 열 이름 불러오기
        df = pd.read_excel(review_sheet_path, sheet_name=sheet_name_selected)
        column_options = list(df.columns)
        
        # 콤보박스 업데이트
        if clause_cb:
            clause_cb["values"] = column_options
        if title_cb:
            title_cb["values"] = column_options
        if output_col_cb and base_template_path:
            # 템플릿 파일의 열을 결과 저장 콤보박스에 설정
            try:
                df_base = pd.read_excel(base_template_path)
                output_col_cb["values"] = list(df_base.columns)
            except:
                # 템플릿 파일 오류 시 검토 시트의 열로 설정
                output_col_cb["values"] = column_options
        
        # 자동 매핑 시도
        try:
            # 동적 임포트
            from utils.column_detector import detect_columns
            
            columns = detect_columns(column_options)
            
            if clause_cb and "clause" in columns:
                clause_cb.set(columns["clause"])
                log_message(f"항목 열 자동 감지: {columns['clause']}", "info")
                
            if title_cb and "title" in columns:
                title_cb.set(columns["title"])
                log_message(f"제목 열 자동 감지: {columns['title']}", "info")
                
            if output_col_cb and "remark" in columns:
                output_col_cb.set(columns["remark"])
                log_message(f"결과 열 자동 감지: {columns['remark']}", "info")
        except ImportError:
            log_message("열 탐지 모듈을 불러올 수 없습니다", "warning")
        except Exception as detector_error:
            log_message(f"열 자동 감지 중 오류: {detector_error}", "warning")
        
        # 미리보기 업데이트
        if sheet_preview:
            update_preview(df)
        
    except Exception as e:
        log_message(f"열 정보 로드 실패: {str(e)}", "error")
        messagebox.showerror("열 분석 실패", str(e))

def update_preview(df):
    """검토 시트 미리보기 테이블 업데이트"""
    global preview_status_label
    
    # 기존 항목 삭제
    sheet_preview.delete(*sheet_preview.get_children())
    
    # 컬럼 설정
    sheet_preview["columns"] = column_options
    sheet_preview["show"] = "headings"
    
    for col in column_options:
        sheet_preview.heading(col, text=col)
        sheet_preview.column(col, width=120, anchor="center")
        
        # 중요 열 강조 표시 (자동 감지된 항목 및 제목 열)
        if clause_cb and clause_cb.get() == col:
            sheet_preview.column(col, width=120, anchor="center")
            # 항목 열 배경색 설정
            sheet_preview.tag_configure(f"col_{col}", background="#e3f2fd")
        elif title_cb and title_cb.get() == col:
            sheet_preview.column(col, width=180, anchor="w")
            # 제목 열 배경색 설정
            sheet_preview.tag_configure(f"col_{col}", background="#e8f5e9")
    
    # 데이터 최대 50행 표시
    for i, row in enumerate(df.head(50).values.tolist()):
        item_id = sheet_preview.insert("", tk.END, values=row)
        
        # 중요 열 태그 적용
        if clause_cb and clause_cb.get() in column_options:
            clause_idx = column_options.index(clause_cb.get())
            sheet_preview.item(item_id, tags=(f"col_{clause_cb.get()}",))
        
    # 미리보기 상태 레이블 업데이트
    if preview_status_label:
        preview_status_label.config(
            text=f"총 {len(df.columns)}개 열 중 일부만 표시 중 (모든 {len(df.columns)}개 열을 보려면 가로 스크롤 사용)"
        )
    
    # 미리보기 탭 타이틀 업데이트
    if preview_notebook:
        preview_notebook.tab(0, text=f"📊 검토 시트 미리보기 ({len(df)} 행)")

def update_base_preview(df):
    """템플릿 파일 미리보기 테이블 업데이트"""
    global base_preview, preview_status_label
    
    if not base_preview:
        return
        
    # 기존 항목 삭제
    base_preview.delete(*base_preview.get_children())
    
    # 열 설정
    columns = list(df.columns)
    base_preview["columns"] = columns
    base_preview["show"] = "headings"
    
    for col in columns:
        base_preview.heading(col, text=col)
        base_preview.column(col, width=120, anchor="center")
        
        # 결과 저장 열 강조 표시
        if output_col_cb and output_col_cb.get() == col:
            base_preview.column(col, width=200, anchor="w")
            # 결과 저장 열 배경색 설정
            base_preview.tag_configure(f"col_{col}", background="#fff8e1")
        # 항목 열 강조 표시 (검토 시트와 매칭될 열)
        elif clause_cb and clause_cb.get() == col:
            base_preview.column(col, width=120, anchor="center")
            # 항목 열 배경색 설정
            base_preview.tag_configure(f"col_{col}", background="#e3f2fd")
    
    # 데이터 최대 30행 표시
    for i, row in enumerate(df.head(30).values.tolist()):
        item_id = base_preview.insert("", tk.END, values=row)
        
        # 결과 저장 열 태그 적용
        if output_col_cb and output_col_cb.get() in columns:
            output_idx = columns.index(output_col_cb.get())
            base_preview.item(item_id, tags=(f"col_{output_col_cb.get()}",))
    
    # 미리보기 탭 타이틀 업데이트
    if preview_notebook:
        preview_notebook.tab(1, text=f"📋 템플릿 파일 미리보기 ({len(df)} 행)")

def handle_generate():
    """보고서 생성 실행"""
    global base_template_path, review_sheet_path
    
    try:
        # 동적 임포트로 순환 참조 방지
        from utils.prompt_loader import load_prompts_by_type
        from logic.generator import generate_remarks
        from utils.standard_detector import detect_standard_from_file, get_standard_info
        
        # 입력값 가져오기
        clause_col = clause_cb.get()
        title_col = title_cb.get()
        output_col = output_col_cb.get()
        matching_mode = match_mode_var.get()  # 추가: 매칭 모드
        
        # 선택된 프롬프트 목록 가져오기 (이제 프롬프트 관리에서 설정한 remark 유형 모두 사용)
        prompts = load_prompts_by_type("remark", as_dict=True, include_metadata=True)
        selected_prompts = list(prompts.keys())
        
        # 필수 항목 검증
        if not base_template_path:
            messagebox.showwarning("입력 누락", "템플릿 파일을 선택해주세요.")
            return
            
        if not review_sheet_path:
            messagebox.showwarning("입력 누락", "검토 시트 파일을 선택해주세요.")
            return
        
        if not all([clause_col, title_col, output_col, sheet_name_selected]):
            messagebox.showwarning("입력 누락", "열 매핑을 모두 선택해주세요.")
            return
            
        if not selected_prompts:
            messagebox.showwarning(
                "프롬프트 없음", 
                "적용할 프롬프트가 없습니다.\n\n프롬프트 관리 탭에서 '보고서 생성' 유형의 프롬프트를 추가해주세요."
            )
            return
        
        try:
            # 규격 감지
            try:
                standard_id = detect_standard_from_file(review_sheet_path, sheet_name_selected)
                standard_info = get_standard_info(standard_id)
                
                if standard_id != "UNKNOWN":
                    log_message(f"규격 자동 감지: {standard_info['title']}", "info")
                else:
                    log_message("규격을 자동으로 감지할 수 없습니다. 일반 형식으로 처리합니다.", "warning")
            except Exception as e:
                standard_id = "UNKNOWN"
                standard_info = None
                log_message(f"규격 감지 중 오류: {e}", "warning")
            
            # 작업 시작 로그
            log_message("보고서 생성 시작...", "info")
            log_message(f"템플릿 파일: {os.path.basename(base_template_path)}")
            log_message(f"검토 시트: {os.path.basename(review_sheet_path)} (시트: {sheet_name_selected})")
            log_message(f"선택된 프롬프트: {', '.join(selected_prompts)}")
            log_message(f"항목 매칭 모드: {'정확히 일치' if matching_mode == 'exact' else '유연한 매칭'}")
            
            # 규격 정보 로그
            if standard_id != "UNKNOWN":
                from utils.standard_detector import get_standard_info
                standard_info = get_standard_info(standard_id)
                log_message(f"적용 규격: {standard_info['title']}", "info")
            else:
                log_message("적용 규격 없음: 일반적인 기준으로 처리합니다.", "warning")
            
            # 진행 상태 창 표시
            progress_window = show_progress_dialog("보고서 생성 중", "초기화 중...")
            
            # 백그라운드에서 처리 (Thread 사용이 이상적이나, 간단한 구현을 위해 update 사용)
            from ui.gui_main import get_root
            root = get_root()
            if root:
                root.update()
            
            try:
                # 보고서 생성 실행 (추가 매개변수: 매칭 모드, 규격 정보)
                out_path = generate_remarks(
                    base_template_path, 
                    review_sheet_path,
                    sheet_name_selected,
                    clause_col, 
                    title_col, 
                    output_col,  
                    selected_prompts,
                    matching_mode=matching_mode,
                    standard_id=standard_id  # 선택 또는 감지된 규격 전달
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
                if 'progress_window' in locals() and progress_window:
                    progress_window.destroy()
                
                # 오류 표시
                error_msg = str(e)
                log_message(f"❌ 오류 발생: {error_msg}", "error")
                messagebox.showerror("실행 오류", error_msg)
        except Exception as e:
            log_message(f"처리 초기화 중 오류 발생: {str(e)}", "error")
            messagebox.showerror("시스템 오류", str(e))
    except ImportError as e:
        log_message(f"모듈 로딩 실패: {e}", "error")
        messagebox.showerror("모듈 오류", f"필요한 모듈을 불러올 수 없습니다: {e}")
    except Exception as e:
        log_message(f"처리 초기화 중 오류 발생: {str(e)}", "error")
        messagebox.showerror("시스템 오류", str(e))

def show_progress_dialog(title, message):
    """진행 상태 대화상자 표시"""
    from ui.gui_main import get_root
    root = get_root()
    
    if not root:
        log_message("오류: GUI 창을 찾을 수 없습니다.", "error")
        return None
    
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
    
    # 취소 버튼
    cancel_btn = ttk.Button(
        frame, 
        text="취소",
        command=lambda: progress_window.destroy()
    )
    cancel_btn.pack(pady=10)
    
    return progress_window

# AI로 규격 감지하기
def detect_standard_with_ai():
    """AI를 사용하여 규격을 감지합니다 (API 호출 포함)"""
    global review_sheet_path, sheet_name_selected, detected_standard_label
    
    if not review_sheet_path or not sheet_name_selected:
        messagebox.showwarning("파일 없음", "검토 시트 파일을 먼저 선택해주세요.")
        return
    
    try:
        # 진행 중 표시
        detected_standard_label.config(
            text="AI가 규격을 분석하는 중...",
            foreground="#666666"
        )
        # GUI 갱신
        detected_standard_label.update()
        
        # AI API를 사용하여 규격 감지하는 함수 (실제 구현 필요)
        from api.gemini import call_gemini
        from utils.standard_detector import get_standard_info
        
        # 샘플 텍스트 추출
        try:
            df = pd.read_excel(review_sheet_path, sheet_name=sheet_name_selected)
            sample_text = ""
            
            # 열 이름 추가
            sample_text += "열 이름: " + ", ".join([str(col) for col in df.columns]) + "\n\n"
            
            # 처음 5개 행 추가
            sample_count = min(5, len(df))
            for i in range(sample_count):
                row_text = " | ".join([str(val) for val in df.iloc[i].values if pd.notna(val)])
                sample_text += f"행 {i+1}: {row_text}\n"
                
            # 텍스트 길이 제한
            if len(sample_text) > 3000:
                sample_text = sample_text[:3000] + "..."
                
        except Exception as e:
            log_message(f"샘플 텍스트 추출 중 오류: {e}", "warning")
            sample_text = "샘플 데이터를 추출할 수 없습니다."
        
        # AI 프롬프트 구성
        prompt = f"""
다음은 엑셀 파일의 내용 일부입니다. 이 파일이 어떤 산업 규격 또는 표준에 관련된 것인지 분석해주세요.
특히 다음 규격 중 하나인지 확인해주세요:
- IEC 60204-1 (기계류의 전기장비)
- IEC 61010 (측정, 제어 및 실험실용 전기장비)
- ISO 13849 (안전 관련 제어 시스템)
- IEC 62061 (기계류의 안전성)
- ISO 14119 (인터록 장치)
- IEC 60335 (가정용 및 유사한 전기기기)

샘플 데이터:
{sample_text}

정확히 일치하는 규격이 있다면 해당 규격의 ID만 답변해주세요 (예: "IEC_60204-1").
어떤 규격과도 일치하지 않는다면 "UNKNOWN"이라고 답변해주세요.
답변은 ID만 작성하고 다른 설명은 하지 마세요.
"""
        
        # AI API 호출
        try:
            response = call_gemini(prompt)
            
            # 응답 처리 - 첫 번째 줄만 가져오기
            response = response.strip().split('\n')[0]
            
            # ID 형식인지 확인
            standard_ids = ["IEC_60204-1", "IEC_61010", "ISO_13849", "IEC_62061", "ISO_14119", "IEC_60335", "UNKNOWN"]
            
            detected_id = "UNKNOWN"
            for std_id in standard_ids:
                if std_id in response:
                    detected_id = std_id
                    break
            
            # 규격 정보 가져오기
            standard_info = get_standard_info(detected_id)
            
            # UI 업데이트
            if detected_id != "UNKNOWN":
                detected_standard_label.config(
                    text=f"{standard_info['title']} (AI 감지)",
                    foreground=SUCCESS_COLOR
                )
                log_message(f"AI 규격 감지 성공: {standard_info['title']}", "success")
            else:
                detected_standard_label.config(
                    text="AI가 규격을 감지할 수 없습니다",
                    foreground=WARNING_COLOR
                )
                log_message("AI가 규격을 감지할 수 없습니다", "warning")
            
            # 감지된 ID 저장
            setattr(detected_standard_label, "standard_id", detected_id)
            
            # 현재 선택이 AUTO_DETECT인 경우 표시 업데이트
            if standard_var.get() == "AUTO_DETECT":
                on_standard_change()
                
        except Exception as e:
            detected_standard_label.config(
                text="AI 감지 실패: API 오류",
                foreground=ERROR_COLOR
            )
            log_message(f"AI 규격 감지 중 오류 발생: {e}", "error")
            
    except Exception as e:
        log_message(f"규격 감지 처리 중 오류: {e}", "error")

# 커스텀 규격 추가 대화상자
def add_custom_standard():
    """커스텀 규격을 추가하는 대화상자"""
    global standard_combo, standard_var
    
    dialog = tk.Toplevel()
    dialog.title("커스텀 규격 추가")
    dialog.geometry("450x200")
    dialog.transient(dialog.master)
    dialog.grab_set()
    
    # 대화상자 내용
    frame = ttk.Frame(dialog, padding=15)
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="새 규격 정보를 입력하세요:", font=("Arial", 11)).pack(anchor="w", pady=(0, 10))
    
    # 입력 필드
    input_frame = ttk.Frame(frame)
    input_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(input_frame, text="규격 ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    id_entry = ttk.Entry(input_frame, width=30)
    id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
    
    ttk.Label(input_frame, text="규격 이름:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    name_entry = ttk.Entry(input_frame, width=30)
    name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")
    
    # 버튼
    button_frame = ttk.Frame(frame)
    button_frame.pack(fill=tk.X, pady=(15, 0))
    
    def save_custom_standard():
        """커스텀 규격 저장"""
        std_id = id_entry.get().strip()
        std_name = name_entry.get().strip()
        
        if not std_id or not std_name:
            messagebox.showwarning("입력 오류", "규격 ID와 이름을 모두 입력해주세요.")
            return
            
        try:
            # standards.json 파일에 저장
            import json
            standards_file = os.path.join("data", "standards.json")
            
            # 디렉토리 확인
            os.makedirs(os.path.dirname(standards_file), exist_ok=True)
            
            # 기존 파일 읽기
            standards = {}
            if (os.path.exists(standards_file)):
                try:
                    with open(standards_file, "r", encoding="utf-8") as f:
                        standards = json.load(f)
                except:
                    standards = {}
            
            # 새 규격 추가
            standards[std_id] = {
                "title": std_name,
                "description": "사용자 정의 규격",
                "scope": "사용자 정의",
                "key_sections": [],
                "version": "Custom"
            }
            
            # 파일 저장
            with open(standards_file, "w", encoding="utf-8") as f:
                json.dump(standards, f, ensure_ascii=False, indent=2)
                
            # 콤보박스 업데이트
            values = list(standard_combo["values"])
            # "커스텀 규격 추가..." 앞에 삽입
            insert_idx = values.index("커스텀 규격 추가...")
            values.insert(insert_idx, std_id)
            standard_combo["values"] = values
            
            # 새로 추가된 규격 선택
            standard_var.set(std_id)
            on_standard_change()
            
            # 대화상자 닫기
            dialog.destroy()
            
            # 성공 메시지
            log_message(f"커스텀 규격 추가됨: {std_name} ({std_id})", "success")
            
        except Exception as e:
            messagebox.showerror("저장 오류", f"커스텀 규격을 저장하는 중 오류가 발생했습니다:\n{e}")
    
    cancel_btn = ttk.Button(button_frame, text="취소", command=dialog.destroy)
    cancel_btn.pack(side=tk.RIGHT)
    
    save_btn = ttk.Button(button_frame, text="저장", command=save_custom_standard)
    save_btn.pack(side=tk.RIGHT, padx=5)

# 규격 관리 대화상자
def show_standard_editor():
    """규격 관리 대화상자"""
    global standard_combo, standard_var
    
    dialog = tk.Toplevel()
    dialog.title("규격 관리")
    dialog.geometry("600x400")
    dialog.transient(dialog.master)
    dialog.grab_set()
    
    # 대화상자 내용
    frame = ttk.Frame(dialog, padding=15)
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="규격 목록", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))
    
    # 규격 목록 표시 (트리뷰)
    tree_frame = ttk.Frame(frame)
    tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
    tree_scroll = ttk.Scrollbar(tree_frame)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    standard_tree = ttk.Treeview(
        tree_frame,
        columns=("id", "name", "type"),
        show="headings",
        height=10,
        yscrollcommand=tree_scroll.set
    )
    standard_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tree_scroll.config(command=standard_tree.yview)
    
    # 열 설정
    standard_tree.heading("id", text="규격 ID")
    standard_tree.heading("name", text="규격 이름")
    standard_tree.heading("type", text="유형")
    
    standard_tree.column("id", width=150)
    standard_tree.column("name", width=300)
    standard_tree.column("type", width=100)
    
    # 규격 목록 로드
    def load_standards():
        """규격 목록 로드"""
        # 트리뷰 초기화
        for item in standard_tree.get_children():
            standard_tree.delete(item)
            
        # 기본 규격 표시
        from utils.standard_detector import get_standard_info
        for std_id in ["IEC_60204-1", "IEC_61010", "ISO_13849", "IEC_62061", "ISO_14119", "IEC_60335"]:
            std_info = get_standard_info(std_id)
            standard_tree.insert("", "end", values=(std_id, std_info["title"], "기본"))
            
        # 커스텀 규격 로드
        try:
            import json
            standards_file = os.path.join("data", "standards.json")
            
            if os.path.exists(standards_file):
                with open(standards_file, "r", encoding="utf-8") as f:
                    custom_standards = json.load(f)
                    
                    for std_id, std_info in custom_standards.items():
                        standard_tree.insert("", "end", values=(std_id, std_info["title"], "커스텀"))
        except Exception as e:
            messagebox.showerror("로드 오류", f"커스텀 규격을 로드하는 중 오류가 발생했습니다:\n{e}")
    
    # 초기 규격 목록 로드
    load_standards()
    
    # 버튼 영역
    button_frame = ttk.Frame(frame)
    button_frame.pack(fill=tk.X, pady=(10, 0))
    
    # 규격 삭제 함수
    def delete_selected_standard():
        """선택한 커스텀 규격 삭제"""
        selection = standard_tree.selection()
        if not selection:
            messagebox.showwarning("선택 오류", "삭제할 규격을 선택하세요.")
            return
            
        # 선택한 항목 정보
        item = standard_tree.item(selection[0])
        std_id = item["values"][0]
        std_type = item["values"][2]
        
        # 기본 규격은 삭제 불가
        if std_type != "커스텀":
            messagebox.showwarning("삭제 불가", "기본 규격은 삭제할 수 없습니다.")
            return
            
        # 삭제 확인
        if not messagebox.askyesno("삭제 확인", f"규격 '{std_id}'을(를) 정말 삭제하시겠습니까?"):
            return
            
        # 파일에서 삭제
        try:
            import json
            standards_file = os.path.join("data", "standards.json")
            
            if os.path.exists(standards_file):
                with open(standards_file, "r", encoding="utf-8") as f:
                    standards = json.load(f)
                    
                if std_id in standards:
                    del standards[std_id]
                    
                    # 파일 저장
                    with open(standards_file, "w", encoding="utf-8") as f:
                        json.dump(standards, f, ensure_ascii=False, indent=2)
                    
                    # 트리뷰에서 삭제
                    standard_tree.delete(selection[0])
                    
                    # 콤보박스에서 제거
                    values = list(standard_combo["values"])
                    if std_id in values:
                        values.remove(std_id)
                        standard_combo["values"] = values
                        
                        # 현재 선택이 삭제된 항목이면 선택 초기화
                        if standard_var.get() == std_id:
                            standard_var.set("")
                            on_standard_change()
                    
                    # 성공 메시지
                    log_message(f"커스텀 규격 삭제: {std_id}", "info")
        except Exception as e:
            messagebox.showerror("삭제 오류", f"규격을 삭제하는 중 오류가 발생했습니다:\n{e}")
    
    # 규격 추가 버튼
    add_btn = ttk.Button(
        button_frame, 
        text="규격 추가", 
        command=lambda: [dialog.destroy(), add_custom_standard()]
    )
    add_btn.pack(side=tk.LEFT)
    
    # 규격 삭제 버튼
    delete_btn = ttk.Button(
        button_frame,
        text="규격 삭제",
        command=delete_selected_standard
    )
    delete_btn.pack(side=tk.LEFT, padx=5)
    
    # 닫기 버튼
    close_btn = ttk.Button(button_frame, text="닫기", command=dialog.destroy)
    close_btn.pack(side=tk.RIGHT)