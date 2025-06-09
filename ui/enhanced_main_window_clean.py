"""
Enhanced Main Window with Performance Monitoring and Error Handling
성능 모니터링 및 오류 처리가 통합된 향상된 메인 윈도우
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any, Callable
import threading
import os
from datetime import datetime

# 로컬 imports with fallbacks
from utils.logger import get_logger

try:
    from utils.enhanced_error_handling import ErrorHandler, ErrorCategory, ErrorSeverity
except ImportError:
    class ErrorHandler:
        def handle_error(self, error): pass
        def get_error_statistics(self): return {}
        @property
        def error_history(self): return []
    
    class ErrorCategory:
        UNKNOWN = "unknown"
    
    class ErrorSeverity:
        HIGH = "high"
        CRITICAL = "critical"

try:
    from parsers.excel_parser import EnhancedExcelParser, parse_excel_file, MemoryTracker
except ImportError:
    EnhancedExcelParser = None
    parse_excel_file = None
    class MemoryTracker:
        @staticmethod
        def get_instance():
            return MemoryTracker()
        def start_monitoring(self): pass
        def stop_monitoring(self): pass
        def _force_gc(self): pass

try:
    from .enhanced_ui_components import (
        ProgressDialog, ProgressInfo, ErrorDisplayDialog, 
        PerformanceMonitorWidget, setup_progress_styles, ExcelParsingError
    )
except ImportError:
    class ProgressDialog:
        def __init__(self, *args, **kwargs): pass
        def update_progress(self, progress_info): pass
        def add_error(self, error): pass
        def cancel(self): pass
        def close(self): pass
    
    class ProgressInfo:
        def __init__(self, percentage=0, operation="", details=None):
            self.percentage = percentage
            self.operation = operation
            self.details = details or {}
    
    class ErrorDisplayDialog:
        def __init__(self, *args, **kwargs): pass
    
    class PerformanceMonitorWidget:
        def __init__(self, *args, **kwargs): pass
    
    def setup_progress_styles(*args): pass
    
    class ExcelParsingError(Exception):
        def __init__(self, message="", category=None, severity=None, original_exception=None):
            super().__init__(message)
            self.message = message
            self.category = category
            self.severity = severity
            self.original_exception = original_exception
            self.timestamp = datetime.now()
        
        def get_user_friendly_message(self):
            return self.message

try:
    from utils.app_context import AppContext
except ImportError:
    class AppContext:
        @staticmethod
        def get_instance():
            return AppContext()
        def add_event_listener(self, event, callback): pass

logger = get_logger("ui.enhanced_main_window")

class EnhancedMainWindow:
    """향상된 메인 윈도우 클래스 - 성능 모니터링 및 오류 처리 통합"""
    
    def __init__(self):
        """생성자"""
        self.app_context = AppContext.get_instance()
        self.error_handler = ErrorHandler()
        self.memory_tracker = MemoryTracker.get_instance()
        
        self.root = tk.Tk()
        self.root.title("Gemini Report Generator - Enhanced")
        self.root.geometry("1200x800")
        
        # 스타일 설정
        self.style = ttk.Style()
        self.style.theme_use('clam')
        setup_progress_styles(self.style)
        
        # 변수들
        self.excel_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.memory_optimization_var = tk.BooleanVar(value=True)
        self.large_file_mode_var = tk.BooleanVar(value=False)
        self.show_progress_var = tk.BooleanVar(value=True)
        self.detailed_errors_var = tk.BooleanVar(value=False)
        self.auto_retry_var = tk.BooleanVar(value=True)
        self.memory_threshold_var = tk.DoubleVar(value=75.0)
        self.chunk_size_var = tk.DoubleVar(value=10000.0)
        self.operation_progress_var = tk.DoubleVar(value=0.0)
        
        # 상태 변수들
        self.current_progress_dialog = None
        self.is_processing = False
        
        # UI 구성 요소들
        self.setup_ui()
        self.setup_event_listeners()
        
        # 초기 상태 설정
        self.memory_tracker.start_monitoring()
        self._update_time()
        
    def setup_ui(self):
        """UI 구성"""
        # 메인 컨테이너
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 좌측 패널 (입력 및 제어)
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 우측 패널 (모니터링 및 로그)
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 좌측 패널 구성
        self.setup_input_panel(left_frame)
        self.setup_options_panel(left_frame)
        
        # 우측 패널 구성
        self.setup_monitoring_panel(right_frame)
        self.setup_log_panel(right_frame)
        
        # 하단 상태바
        self.setup_status_bar()
        
    def setup_input_panel(self, parent):
        """입력 패널 설정"""
        input_frame = ttk.LabelFrame(parent, text="파일 입력", padding=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Excel 파일 선택
        ttk.Label(input_frame, text="Excel 파일:").grid(row=0, column=0, sticky="w", pady=5)
        excel_frame = ttk.Frame(input_frame)
        excel_frame.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5, padx=(10, 0))
        
        ttk.Entry(excel_frame, textvariable=self.excel_path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(excel_frame, text="찾아보기", command=self.browse_excel_file).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 출력 경로 선택
        ttk.Label(input_frame, text="출력 경로:").grid(row=1, column=0, sticky="w", pady=5)
        output_frame = ttk.Frame(input_frame)
        output_frame.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5, padx=(10, 0))
        
        ttk.Entry(output_frame, textvariable=self.output_path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="찾아보기", command=self.browse_output_path).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 처리 버튼들
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        self.process_button = ttk.Button(button_frame, text="파일 처리 시작", command=self.start_file_processing)
        self.process_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="중지", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # 파일 정보 표시
        info_frame = ttk.LabelFrame(input_frame, text="파일 정보", padding=10)
        info_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        
        self.file_info_text = tk.Text(info_frame, height=8, state=tk.DISABLED, wrap=tk.WORD)
        info_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.file_info_text.yview)
        self.file_info_text.configure(yscrollcommand=info_scrollbar.set)
        
        self.file_info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        input_frame.columnconfigure(1, weight=1)
        
    def setup_options_panel(self, parent):
        """옵션 패널 설정"""
        options_frame = ttk.LabelFrame(parent, text="처리 옵션", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 기본 옵션들
        ttk.Checkbutton(options_frame, text="메모리 최적화", variable=self.memory_optimization_var).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Checkbutton(options_frame, text="대용량 파일 모드", variable=self.large_file_mode_var).grid(row=0, column=1, sticky="w", pady=2)
        ttk.Checkbutton(options_frame, text="상세 진행률 표시", variable=self.show_progress_var).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Checkbutton(options_frame, text="상세 오류 표시", variable=self.detailed_errors_var).grid(row=1, column=1, sticky="w", pady=2)
        ttk.Checkbutton(options_frame, text="자동 재시도", variable=self.auto_retry_var).grid(row=2, column=0, sticky="w", pady=2)
        
        # 고급 설정
        advanced_frame = ttk.LabelFrame(options_frame, text="고급 설정", padding=5)
        advanced_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        # 메모리 임계값
        ttk.Label(advanced_frame, text="메모리 임계값:").grid(row=0, column=0, sticky="w", pady=2)
        memory_frame = ttk.Frame(advanced_frame)
        memory_frame.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        memory_scale = ttk.Scale(memory_frame, from_=50, to=90, orient=tk.HORIZONTAL, variable=self.memory_threshold_var,
                                command=self.update_memory_threshold_label)
        memory_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.memory_threshold_label = ttk.Label(memory_frame, text="75.0%")
        self.memory_threshold_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 청크 크기
        ttk.Label(advanced_frame, text="청크 크기:").grid(row=1, column=0, sticky="w", pady=2)
        chunk_frame = ttk.Frame(advanced_frame)
        chunk_frame.grid(row=1, column=1, sticky="ew", padx=(5, 0))
        chunk_scale = ttk.Scale(chunk_frame, from_=1000, to=50000, orient=tk.HORIZONTAL, variable=self.chunk_size_var,
                               command=self.update_chunk_size_label)
        chunk_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.chunk_size_label = ttk.Label(chunk_frame, text="10,000")
        self.chunk_size_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 설정 저장 버튼
        ttk.Button(advanced_frame, text="설정 저장", command=self.save_settings).grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        advanced_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(1, weight=1)
        
    def setup_monitoring_panel(self, parent):
        """모니터링 패널 설정"""
        monitor_frame = ttk.LabelFrame(parent, text="실시간 모니터링", padding=10)
        monitor_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 작업 진행률
        ttk.Label(monitor_frame, text="작업 진행률:").grid(row=0, column=0, sticky="w", pady=2)
        progress_bar = ttk.Progressbar(monitor_frame, variable=self.operation_progress_var, maximum=100)
        progress_bar.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        
        # 현재 작업
        ttk.Label(monitor_frame, text="현재 작업:").grid(row=1, column=0, sticky="w", pady=2)
        self.current_operation_label = ttk.Label(monitor_frame, text="대기 중")
        self.current_operation_label.grid(row=1, column=1, sticky="w", padx=(5, 0))
        
        # 작업 세부사항
        ttk.Label(monitor_frame, text="세부사항:").grid(row=2, column=0, sticky="w", pady=2)
        self.operation_details_label = ttk.Label(monitor_frame, text="--")
        self.operation_details_label.grid(row=2, column=1, sticky="w", padx=(5, 0))
        
        # 오류 상태
        ttk.Label(monitor_frame, text="오류 상태:").grid(row=3, column=0, sticky="w", pady=2)
        self.error_count_label = ttk.Label(monitor_frame, text="오류 없음")
        self.error_count_label.grid(row=3, column=1, sticky="w", padx=(5, 0))
        
        # 최근 오류
        ttk.Label(monitor_frame, text="최근 오류:").grid(row=4, column=0, sticky="w", pady=2)
        self.last_error_label = ttk.Label(monitor_frame, text="--")
        self.last_error_label.grid(row=4, column=1, sticky="w", padx=(5, 0))
        
        # 시간 표시
        ttk.Label(monitor_frame, text="현재 시간:").grid(row=5, column=0, sticky="w", pady=2)
        self.time_label = ttk.Label(monitor_frame, text="")
        self.time_label.grid(row=5, column=1, sticky="w", padx=(5, 0))
        
        monitor_frame.columnconfigure(1, weight=1)
        
    def setup_log_panel(self, parent):
        """로그 패널 설정"""
        log_frame = ttk.LabelFrame(parent, text="로그", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 로그 필터
        filter_frame = ttk.Frame(log_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(filter_frame, text="필터:").pack(side=tk.LEFT)
        self.log_filter_var = tk.StringVar(value="전체")
        log_filter = ttk.Combobox(filter_frame, textvariable=self.log_filter_var, 
                                 values=["전체", "INFO", "WARNING", "ERROR"], state="readonly")
        log_filter.pack(side=tk.LEFT, padx=(5, 0))
        log_filter.bind("<<ComboboxSelected>>", self.on_log_filter_change)
        
        # 로그 제어 버튼들
        ttk.Button(filter_frame, text="지우기", command=self.clear_log).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(filter_frame, text="저장", command=self.save_log).pack(side=tk.RIGHT)
        
        # 로그 텍스트 영역
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_text_frame, state=tk.DISABLED, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 로그 스타일 설정
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        
    def setup_status_bar(self):
        """상태바 설정"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_bar = ttk.Label(status_frame, text="준비됨", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, padx=2, pady=2)
        
    def setup_event_listeners(self):
        """이벤트 리스너 등록"""
        self.app_context.add_event_listener("status_changed", self.update_status)
        self.app_context.add_event_listener("progress_updated", self.update_progress)
        self.app_context.add_event_listener("error_occurred", self.handle_error)
    
    # 이벤트 핸들러 메서드들
    def browse_excel_file(self):
        """Excel 파일 선택"""
        filename = filedialog.askopenfilename(
            title="Excel 파일 선택",
            filetypes=[
                ("Excel 파일", "*.xlsx *.xls"),
                ("모든 파일", "*.*")
            ]
        )
        if filename:
            self.excel_path_var.set(filename)
            self._analyze_file(filename)
    
    def browse_output_path(self):
        """출력 경로 선택"""
        dirname = filedialog.askdirectory(title="출력 경로 선택")
        if dirname:
            self.output_path_var.set(dirname)
    
    def start_file_processing(self):
        """파일 처리 시작"""
        excel_path = self.excel_path_var.get()
        output_path = self.output_path_var.get()
        
        if not excel_path or not os.path.exists(excel_path):
            messagebox.showerror("오류", "유효한 Excel 파일을 선택해주세요.")
            return
        
        if not output_path:
            messagebox.showerror("오류", "출력 경로를 선택해주세요.")
            return
        
        # UI 상태 변경
        self.process_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_processing = True
        
        # 진행률 대화상자 표시 (옵션에 따라)
        if self.show_progress_var.get():
            self.current_progress_dialog = ProgressDialog(self.root, "Excel 파일 처리 중")
        
        # 별도 스레드에서 처리
        def process_file():
            try:
                # Excel 파서 옵션 설정
                options = {
                    'enable_memory_optimization': self.memory_optimization_var.get(),
                    'large_file_mode': self.large_file_mode_var.get(),
                    'progress_callback': self.on_progress_update if self.current_progress_dialog else None
                }
                
                if parse_excel_file:
                    result = parse_excel_file(excel_path, **options)
                else:
                    # Fallback processing
                    result = {"message": "Excel parsing not available"}
                
                # 결과 저장
                import json
                output_file = os.path.join(output_path, f"parsed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
                
                self.root.after(0, lambda: self._on_processing_complete(output_file))
                
            except Exception as e:
                excel_error = ExcelParsingError(
                    message=str(e),
                    category=ErrorCategory.UNKNOWN,
                    severity=ErrorSeverity.HIGH,
                    original_exception=e
                )
                self.root.after(0, lambda: self._on_processing_error(excel_error))
            finally:
                self.root.after(0, self._reset_ui_state)
        
        thread = threading.Thread(target=process_file)
        thread.daemon = True
        thread.start()
    
    def stop_processing(self):
        """처리 중지"""
        if self.current_progress_dialog:
            self.current_progress_dialog.cancel()
        
        self._reset_ui_state()
    
    def on_progress_update(self, progress_info):
        """진행률 업데이트 콜백"""
        if self.current_progress_dialog:
            self.current_progress_dialog.update_progress(progress_info)
        
        # 모니터링 패널 업데이트
        self.operation_progress_var.set(progress_info.percentage)
        self.current_operation_label.config(text=progress_info.operation)
        
        if progress_info.details:
            details_text = ", ".join(f"{k}: {v}" for k, v in progress_info.details.items())
            self.operation_details_label.config(text=details_text[:50] + "..." if len(details_text) > 50 else details_text)
    
    def handle_error(self, error):
        """오류 처리"""
        # 오류 기록
        self.error_handler.handle_error(error)
        
        # 진행률 대화상자에 오류 표시
        if self.current_progress_dialog:
            self.current_progress_dialog.add_error(error)
        
        # 오류 상태 업데이트
        self._update_error_status()
        
        # 심각한 오류의 경우 별도 대화상자 표시
        if hasattr(error, 'severity') and error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            if self.detailed_errors_var.get():
                self.root.after(100, lambda: ErrorDisplayDialog(self.root, error))
    
    def _analyze_file(self, file_path):
        """파일 분석 및 정보 표시"""
        try:
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            
            info_text = f"""파일 경로: {file_path}
파일 크기: {file_size:.2f} MB

"""
            
            if file_size > 50:
                info_text += "⚠️ 대용량 파일입니다. 처리 시간이 오래 걸릴 수 있습니다.\n"
                self.large_file_mode_var.set(True)
            
            # 간단한 Excel 파일 정보 읽기
            try:
                import pandas as pd
                excel_file = pd.ExcelFile(file_path)
                sheet_names = excel_file.sheet_names
                
                info_text += f"시트 수: {len(sheet_names)}\n"
                info_text += f"시트 목록: {', '.join(sheet_names[:5])}"
                if len(sheet_names) > 5:
                    info_text += f" 외 {len(sheet_names) - 5}개"
                info_text += "\n"
                
                # 첫 번째 시트의 행/열 수
                if sheet_names:
                    first_sheet = pd.read_excel(file_path, sheet_name=sheet_names[0], nrows=0)
                    info_text += f"첫 번째 시트 열 수: {len(first_sheet.columns)}\n"
                    
            except Exception as e:
                info_text += f"파일 미리보기 실패: {str(e)}\n"
            
            # 추천 설정
            if file_size > 100:
                info_text += "\n📋 추천 설정:\n"
                info_text += "- 대용량 파일 모드 활성화\n"
                info_text += "- 메모리 최적화 활성화\n"
                info_text += "- 상세 진행률 표시 활성화\n"
            
            self._update_file_info(info_text)
            
        except Exception as e:
            self._update_file_info(f"파일 분석 실패: {str(e)}")
    
    def _update_file_info(self, text):
        """파일 정보 업데이트"""
        self.file_info_text.config(state=tk.NORMAL)
        self.file_info_text.delete(1.0, tk.END)
        self.file_info_text.insert(tk.END, text)
        self.file_info_text.config(state=tk.DISABLED)
    
    def _on_processing_complete(self, output_file):
        """처리 완료 콜백"""
        if self.current_progress_dialog:
            self.current_progress_dialog.close()
            self.current_progress_dialog = None
        
        messagebox.showinfo(
            "처리 완료",
            f"파일 처리가 완료되었습니다.\n\n출력 파일: {output_file}"
        )
        
        self._add_log(f"INFO: 파일 처리 완료 - {output_file}")
    
    def _on_processing_error(self, error):
        """처리 오류 콜백"""
        if self.current_progress_dialog:
            self.current_progress_dialog.close()
            self.current_progress_dialog = None
        
        self.handle_error(error)
        
        messagebox.showerror(
            "처리 오류",
            f"파일 처리 중 오류가 발생했습니다.\n\n{error.get_user_friendly_message()}"
        )
    
    def _reset_ui_state(self):
        """UI 상태 초기화"""
        self.process_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.operation_progress_var.set(0)
        self.current_operation_label.config(text="대기 중")
        self.operation_details_label.config(text="--")
        self.is_processing = False
    
    def _update_error_status(self):
        """오류 상태 업데이트"""
        stats = self.error_handler.get_error_statistics()
        total_errors = stats.get('total_errors', 0)
        
        if total_errors == 0:
            self.error_count_label.config(text="오류 없음")
            self.last_error_label.config(text="--")
        else:
            self.error_count_label.config(text=f"총 {total_errors}개 오류")
            
            recent_errors = stats.get('recent_errors', [])
            if recent_errors:
                last_error = recent_errors[-1]
                self.last_error_label.config(
                    text=f"최근: {last_error.get_user_friendly_message()[:50]}..."
                )
    
    def _add_log(self, message, level="INFO"):
        """로그 추가"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_message)
        self.log_text.tag_add(level, f"end-{len(log_message)}c", "end-1c")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
    
    def _update_time(self):
        """시간 업데이트"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.time_label.config(text=current_time)
        self.root.after(1000, self._update_time)
    
    # 설정 관련 메서드들
    def update_memory_threshold_label(self, value):
        """메모리 임계값 라벨 업데이트"""
        self.memory_threshold_label.config(text=f"{float(value):.1f}%")
        self.memory_tracker.memory_threshold = float(value) / 100
    
    def update_chunk_size_label(self, value):
        """청크 크기 라벨 업데이트"""
        self.chunk_size_label.config(text=f"{int(float(value)):,}")
    
    def save_settings(self):
        """설정 저장"""
        settings = {
            'memory_threshold': self.memory_threshold_var.get(),
            'chunk_size': self.chunk_size_var.get(),
            'auto_retry': self.auto_retry_var.get(),
            'detailed_errors': self.detailed_errors_var.get()
        }
        
        try:
            import json
            os.makedirs('config', exist_ok=True)
            with open('config/ui_settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
            
            messagebox.showinfo("설정 저장", "설정이 저장되었습니다.")
            self._add_log("설정이 저장되었습니다.")
            
        except Exception as e:
            messagebox.showerror("설정 저장 실패", f"설정 저장에 실패했습니다: {e}")
            self._add_log(f"설정 저장 실패: {e}", "ERROR")
    
    # 로그 관련 메서드들
    def on_log_filter_change(self, event=None):
        """로그 필터 변경"""
        # 로그 필터링 로직 구현
        pass
    
    def clear_log(self):
        """로그 지우기"""
        if messagebox.askyesno("로그 지우기", "모든 로그를 지우시겠습니까?"):
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)
    
    def save_log(self):
        """로그 저장"""
        filename = filedialog.asksaveasfilename(
            title="로그 저장",
            defaultextension=".txt",
            filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("저장 완료", f"로그가 저장되었습니다: {filename}")
            except Exception as e:
                messagebox.showerror("저장 실패", f"로그 저장에 실패했습니다: {e}")
    
    # 기본 이벤트 핸들러들
    def update_status(self, message):
        """상태바 업데이트"""
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    def update_progress(self, current, total, message):
        """진행 상태 업데이트"""
        progress = (current / total) * 100 if total > 0 else 0
        self.operation_progress_var.set(progress)
        self.current_operation_label.config(text=message)
        self.root.update_idletasks()
    
    def run(self):
        """메인 루프 실행"""
        # 초기 상태 설정
        self._add_log("Gemini Report Generator 시작")
        self.update_status("준비됨")
        
        # 메인 루프 시작
        self.root.mainloop()
        
        # 정리 작업
        self.memory_tracker.stop_monitoring()

if __name__ == "__main__":
    app = EnhancedMainWindow()
    app.run()
