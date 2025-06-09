"""
Enhanced UI Components for Performance Monitoring and Error Handling
성능 모니터링 및 오류 처리를 위한 향상된 UI 구성요소
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

# 로컬 imports with fallbacks
try:
    from utils.logger import get_logger
except ImportError:
    def get_logger(name):
        import logging
        return logging.getLogger(name)

try:
    from utils.memory_tracker import MemoryTracker
except ImportError:
    class MemoryTracker:
        @staticmethod
        def get_instance():
            return MemoryTracker()
        def start_monitoring(self): pass
        def stop_monitoring(self): pass
        def get_memory_usage(self): return 0.0
        def get_memory_stats(self): return {}

try:
    from parsers.excel_parser import ExcelParsingError
except ImportError:
    class ExcelParsingError(Exception):
        def __init__(self, message, category=None, severity=None, details=None):
            super().__init__(message)
            self.message = message
            self.category = category or "parsing"
            self.severity = severity or "error"
            self.details = details or {}
            self.timestamp = datetime.now()
            self.original_exception = None
        
        def get_user_friendly_message(self):
            return str(self.message)
        
        def get_suggestions(self):
            return ["파일을 다시 확인해보세요", "지원팀에 문의하세요"]
        
        def to_dict(self):
            return {"message": self.message, "category": self.category}

logger = get_logger("ui.enhanced_components")

# 필요한 클래스들 정의
@dataclass
class ProgressInfo:
    """진행률 정보 데이터 클래스"""
    current: int
    total: int
    percentage: float
    operation: str
    details: Optional[Dict[str, Any]] = None

class ErrorCategory(Enum):
    """오류 카테고리"""
    FILE_ACCESS = "file_access"
    MEMORY = "memory"
    PARSING = "parsing"
    NETWORK = "network"
    VALIDATION = "validation"

class ErrorSeverity(Enum):
    """오류 심각도"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EnhancedProgressBar:
    """향상된 진행률 표시 바"""
    
    def __init__(self, parent, width=300, height=25):
        """향상된 진행률 바 초기화"""
        self.parent = parent
        self.width = width
        self.height = height
        
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        
        self.current_value = 0
        self.max_value = 100
        self.start_time = None
        
    def _create_widgets(self):
        """위젯 생성"""
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progressbar = ttk.Progressbar(
            self.frame,
            variable=self.progress_var,
            maximum=100,
            length=self.width,
            mode='determinate'
        )
        self.progressbar.pack(pady=2)
        
        # 정보 표시 프레임
        info_frame = ttk.Frame(self.frame)
        info_frame.pack(fill=tk.X, pady=2)
        
        # 퍼센트 표시
        self.percent_label = ttk.Label(info_frame, text="0%")
        self.percent_label.pack(side=tk.RIGHT)
        
        # 작업 설명
        self.operation_label = ttk.Label(info_frame, text="준비 중...")
        self.operation_label.pack(side=tk.LEFT)
        
        # 예상 시간 표시
        self.eta_label = ttk.Label(info_frame, text="")
        self.eta_label.pack(side=tk.LEFT, padx=(10, 0))
    
    def update(self, current: int, total: int, operation: str = ""):
        """진행률 업데이트"""
        if total <= 0:
            return
            
        if self.start_time is None:
            self.start_time = datetime.now()
        
        self.current_value = current
        self.max_value = total
        percentage = (current / total) * 100
        
        # 진행률 바 업데이트
        self.progress_var.set(percentage)
        self.percent_label.config(text=f"{percentage:.1f}%")
        
        if operation:
            self.operation_label.config(text=operation)
        
        # 예상 완료 시간 계산
        if current > 0:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            rate = current / elapsed
            remaining = (total - current) / rate if rate > 0 else 0
            self.eta_label.config(text=f"예상 완료: {remaining:.0f}초")
    
    def reset(self):
        """진행률 초기화"""
        self.progress_var.set(0)
        self.percent_label.config(text="0%")
        self.operation_label.config(text="준비 중...")
        self.eta_label.config(text="")
        self.start_time = None
    
    def pack(self, **kwargs):
        """프레임 패킹"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """프레임 그리드"""
        self.frame.grid(**kwargs)

class EnhancedFileSelector:
    """향상된 파일 선택기"""
    
    def __init__(self, parent, title="파일 선택", filetypes=None):
        """파일 선택기 초기화"""
        self.parent = parent
        self.title = title
        self.filetypes = filetypes or [("모든 파일", "*.*")]
        
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        
        self.selected_files = []
        self.callback = None
    
    def _create_widgets(self):
        """위젯 생성"""
        # 파일 경로 표시
        self.path_var = tk.StringVar(value="파일을 선택하세요...")
        self.path_label = ttk.Label(
            self.frame, 
            textvariable=self.path_var,
            background="white",
            relief="sunken",
            anchor="w"
        )
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 찾아보기 버튼
        self.browse_button = ttk.Button(
            self.frame,
            text="찾아보기",
            command=self._browse_files
        )
        self.browse_button.pack(side=tk.RIGHT)
    
    def _browse_files(self):
        """파일 찾아보기"""
        from tkinter import filedialog
        
        files = filedialog.askopenfilenames(
            title=self.title,
            filetypes=self.filetypes
        )
        
        if files:
            self.selected_files = list(files)
            if len(files) == 1:
                self.path_var.set(files[0])
            else:
                self.path_var.set(f"{len(files)}개 파일 선택됨")
            
            if self.callback:
                self.callback(self.selected_files)
    
    def set_callback(self, callback: Callable):
        """파일 선택 콜백 설정"""
        self.callback = callback
    
    def get_selected_files(self):
        """선택된 파일 반환"""
        return self.selected_files
    
    def clear(self):
        """선택 초기화"""
        self.selected_files = []
        self.path_var.set("파일을 선택하세요...")
    
    def pack(self, **kwargs):
        """프레임 패킹"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """프레임 그리드"""
        self.frame.grid(**kwargs)

class EnhancedConfigPanel:
    """향상된 설정 패널"""
    
    def __init__(self, parent, config_data: Dict[str, Any] = None):
        """설정 패널 초기화"""
        self.parent = parent
        self.config_data = config_data or {}
        self.widgets = {}
        
        self.frame = ttk.LabelFrame(parent, text="설정", padding="10")
        self._create_widgets()
    
    def _create_widgets(self):
        """위젯 생성"""
        # 기본 설정들
        self._add_boolean_option("청크 처리 사용", "use_chunks", True)
        self._add_number_option("청크 크기", "chunk_size", 1000, 100, 10000)
        self._add_boolean_option("메모리 모니터링", "monitor_memory", True)
        self._add_boolean_option("상세 로깅", "verbose_logging", False)
        
        # 저장 버튼
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="기본값 복원",
            command=self._reset_to_defaults
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            button_frame,
            text="적용",
            command=self._apply_config
        ).pack(side=tk.RIGHT)
    
    def _add_boolean_option(self, label: str, key: str, default: bool):
        """불린 옵션 추가"""
        frame = ttk.Frame(self.frame)
        frame.pack(fill=tk.X, pady=2)
        
        var = tk.BooleanVar(value=self.config_data.get(key, default))
        checkbox = ttk.Checkbutton(frame, text=label, variable=var)
        checkbox.pack(side=tk.LEFT)
        
        self.widgets[key] = var
    
    def _add_number_option(self, label: str, key: str, default: int, min_val: int, max_val: int):
        """숫자 옵션 추가"""
        frame = ttk.Frame(self.frame)
        frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame, text=label).pack(side=tk.LEFT)
        
        var = tk.IntVar(value=self.config_data.get(key, default))
        scale = ttk.Scale(
            frame,
            from_=min_val,
            to=max_val,
            variable=var,
            orient=tk.HORIZONTAL
        )
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        
        value_label = ttk.Label(frame, text=str(default))
        value_label.pack(side=tk.RIGHT)
        
        # 값 변경 시 라벨 업데이트
        def update_label(*args):
            value_label.config(text=str(var.get()))
        var.trace('w', update_label)
        
        self.widgets[key] = var
    
    def _reset_to_defaults(self):
        """기본값으로 초기화"""
        defaults = {
            "use_chunks": True,
            "chunk_size": 1000,
            "monitor_memory": True,
            "verbose_logging": False
        }
        
        for key, default_value in defaults.items():
            if key in self.widgets:
                self.widgets[key].set(default_value)
    
    def _apply_config(self):
        """설정 적용"""
        config = self.get_config()
        logger.info(f"설정 적용: {config}")
        messagebox.showinfo("설정", "설정이 적용되었습니다.")
    
    def get_config(self) -> Dict[str, Any]:
        """현재 설정 반환"""
        config = {}
        for key, widget in self.widgets.items():
            config[key] = widget.get()
        return config
    
    def set_config(self, config: Dict[str, Any]):
        """설정 값 설정"""
        for key, value in config.items():
            if key in self.widgets:
                self.widgets[key].set(value)
    
    def pack(self, **kwargs):
        """프레임 패킹"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """프레임 그리드"""
        self.frame.grid(**kwargs)

class EnhancedLogViewer:
    """향상된 로그 뷰어"""
    
    def __init__(self, parent, height=10):
        """로그 뷰어 초기화"""
        self.parent = parent
        self.height = height
        
        self.frame = ttk.LabelFrame(parent, text="로그", padding="5")
        self._create_widgets()
        
        self.log_levels = {
            "DEBUG": {"color": "gray", "prefix": "🔍"},
            "INFO": {"color": "black", "prefix": "ℹ️"},
            "WARNING": {"color": "orange", "prefix": "⚠️"},
            "ERROR": {"color": "red", "prefix": "❌"},
            "CRITICAL": {"color": "darkred", "prefix": "🚨"}
        }
    
    def _create_widgets(self):
        """위젯 생성"""
        # 로그 텍스트 위젯
        text_frame = ttk.Frame(self.frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_widget = tk.Text(
            text_frame,
            height=self.height,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 컨트롤 버튼
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(button_frame, text="지우기", command=self.clear).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="저장", command=self._save_log).pack(side=tk.LEFT, padx=(5, 0))
        
        # 필터 옵션
        filter_frame = ttk.Frame(button_frame)
        filter_frame.pack(side=tk.RIGHT)
        
        ttk.Label(filter_frame, text="필터:").pack(side=tk.LEFT)
        
        self.filter_var = tk.StringVar(value="ALL")
        filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=["ALL", "ERROR", "WARNING", "INFO", "DEBUG"],
            state="readonly",
            width=10
        )
        filter_combo.pack(side=tk.LEFT, padx=(5, 0))
        filter_combo.bind('<<ComboboxSelected>>', self._apply_filter)
        
        # 색상 태그 설정
        for level, config in self.log_levels.items():
            self.text_widget.tag_configure(
                f"level_{level}",
                foreground=config["color"]
            )
    
    def add_log(self, message: str, level: str = "INFO"):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_config = self.log_levels.get(level.upper(), self.log_levels["INFO"])
        
        formatted_message = f"[{timestamp}] {level_config['prefix']} {message}\n"
        
        self.text_widget.config(state=tk.NORMAL)
        
        # 메시지 삽입
        start_index = self.text_widget.index(tk.END)
        self.text_widget.insert(tk.END, formatted_message)
        end_index = self.text_widget.index(tk.END)
        
        # 색상 태그 적용
        self.text_widget.tag_add(f"level_{level.upper()}", start_index, end_index)
        
        self.text_widget.config(state=tk.DISABLED)
        self.text_widget.see(tk.END)
        
        # 필터 적용
        self._apply_filter()
    
    def _apply_filter(self, event=None):
        """로그 필터 적용"""
        # 현재는 단순히 표시만, 실제 필터링은 추가 구현 필요
        pass
    
    def clear(self):
        """로그 지우기"""
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)
    
    def _save_log(self):
        """로그 저장"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    content = self.text_widget.get(1.0, tk.END)
                    f.write(content)
                messagebox.showinfo("저장 완료", f"로그가 저장되었습니다: {filename}")
            except Exception as e:
                messagebox.showerror("저장 실패", f"로그 저장에 실패했습니다: {e}")
    
    def pack(self, **kwargs):
        """프레임 패킹"""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """프레임 그리드"""
        self.frame.grid(**kwargs)

class ProgressDialog:
    """진행률 대화상자"""
    
    def __init__(self, parent, title="작업 진행 중"):
        """진행률 대화상자 초기화"""
        self.parent = parent
        self.cancelled = False
        
        # 대화상자 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 창 닫기 이벤트 처리
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        self._create_widgets()
        self._center_dialog()
        
        # 메모리 트래커 초기화
        self.memory_tracker = MemoryTracker.get_instance()
        self._start_monitoring()
    
    def _center_dialog(self):
        """대화상자 중앙 정렬"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")
    
    def _create_widgets(self):
        """위젯 생성"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 진행률 표시
        progress_frame = ttk.LabelFrame(main_frame, text="진행 상황", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 작업 설명
        self.operation_label = ttk.Label(progress_frame, text="작업을 준비하는 중...")
        self.operation_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # 퍼센트 표시
        self.percentage_label = ttk.Label(progress_frame, text="0%")
        self.percentage_label.pack(anchor=tk.E)
        
        # 메모리 모니터링
        memory_frame = ttk.LabelFrame(main_frame, text="시스템 모니터링", padding="10")
        memory_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 메모리 사용량
        memory_info_frame = ttk.Frame(memory_frame)
        memory_info_frame.pack(fill=tk.X)
        
        ttk.Label(memory_info_frame, text="메모리 사용량:").pack(side=tk.LEFT)
        self.memory_label = ttk.Label(memory_info_frame, text="0%")
        self.memory_label.pack(side=tk.RIGHT)
        
        self.memory_var = tk.DoubleVar()
        self.memory_bar = ttk.Progressbar(
            memory_frame,
            variable=self.memory_var,
            maximum=100,
            length=400
        )
        self.memory_bar.pack(fill=tk.X, pady=(5, 0))
        
        # 성능 통계
        stats_frame = ttk.Frame(memory_frame)
        stats_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="처리 시간: -- | 처리 속도: --")
        self.stats_label.pack(anchor=tk.W)
        
        # 로그 및 오류 표시 프레임
        log_frame = ttk.LabelFrame(main_frame, text="상태 로그", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 로그 텍스트 위젯
        self.log_text = tk.Text(log_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        self.cancel_button = ttk.Button(button_frame, text="취소", command=self.cancel)
        self.cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.minimize_button = ttk.Button(button_frame, text="최소화", command=self.minimize)
        self.minimize_button.pack(side=tk.RIGHT)
        
        # 시작 시간 기록
        self.start_time = datetime.now()
    
    def _start_monitoring(self):
        """메모리 모니터링 시작"""
        self.memory_tracker.start_monitoring()
        self._update_memory_display()
    
    def _update_memory_display(self):
        """메모리 사용량 표시 업데이트"""
        if not self.cancelled:
            try:
                memory_usage = self.memory_tracker.get_memory_usage()
                memory_percent = memory_usage * 100
                
                self.memory_var.set(memory_percent)
                self.memory_label.config(text=f"{memory_percent:.1f}%")
                
                # 메모리 사용량에 따른 색상 변경 (가능한 경우)
                if memory_percent > 80:
                    self.memory_bar.configure(style="Danger.Horizontal.TProgressbar")
                elif memory_percent > 60:
                    self.memory_bar.configure(style="Warning.Horizontal.TProgressbar")
                else:
                    self.memory_bar.configure(style="Success.Horizontal.TProgressbar")
                
                # 500ms 후 다시 업데이트
                self.dialog.after(500, self._update_memory_display)
                
            except Exception as e:
                logger.warning(f"메모리 모니터링 업데이트 실패: {e}")
                self.dialog.after(1000, self._update_memory_display)
    
    def update_progress(self, progress_info: ProgressInfo):
        """진행률 정보 업데이트"""
        if self.cancelled:
            return
            
        try:
            # 진행률 업데이트
            self.progress_var.set(progress_info.percentage)
            self.percentage_label.config(text=f"{progress_info.percentage:.1f}%")
            self.operation_label.config(text=progress_info.operation)
            
            # 성능 통계 업데이트
            elapsed_time = (datetime.now() - self.start_time).total_seconds()
            if progress_info.current > 0:
                speed = progress_info.current / elapsed_time
                eta = (progress_info.total - progress_info.current) / speed if speed > 0 else 0
                self.stats_label.config(
                    text=f"처리 시간: {elapsed_time:.1f}초 | 처리 속도: {speed:.1f}/초 | 예상 완료: {eta:.1f}초"
                )
            
            # 로그 추가
            self._add_log(f"[{datetime.now().strftime('%H:%M:%S')}] {progress_info.operation}")
            
        except Exception as e:
            logger.error(f"진행률 업데이트 중 오류: {e}")
    
    def add_error(self, error: ExcelParsingError):
        """오류 표시"""
        error_color = {
            "low": "blue",
            "medium": "orange", 
            "high": "red",
            "critical": "darkred"
        }.get(str(error.severity).lower(), "black")
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        error_msg = f"[{timestamp}] ❌ {error.get_user_friendly_message()}"
        
        self._add_log(error_msg, error_color)
        
        # 심각한 오류의 경우 별도 알림
        if str(error.severity).lower() in ["high", "critical"]:
            self.dialog.bell()  # 시스템 소리
    
    def _add_log(self, message: str, color: str = "black"):
        """로그 메시지 추가"""
        try:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            
            # 색상 태그 적용
            if color != "black":
                start_line = f"{int(self.log_text.index(tk.END).split('.')[0]) - 1}.0"
                end_line = f"{int(self.log_text.index(tk.END).split('.')[0]) - 1}.end"
                tag_name = f"color_{color}"
                
                self.log_text.tag_add(tag_name, start_line, end_line)
                self.log_text.tag_config(tag_name, foreground=color)
            
            self.log_text.config(state=tk.DISABLED)
            self.log_text.see(tk.END)
            
        except Exception as e:
            logger.error(f"로그 추가 중 오류: {e}")
    
    def cancel(self):
        """작업 취소"""
        if messagebox.askyesno("작업 취소", "진행 중인 작업을 취소하시겠습니까?"):
            self.cancelled = True
            self.cancel_button.config(state=tk.DISABLED, text="취소 중...")
            self._add_log("[사용자] 작업 취소 요청", "orange")
    
    def minimize(self):
        """대화상자 최소화"""
        self.dialog.iconify()
    
    def close(self):
        """대화상자 닫기"""
        self.memory_tracker.stop_monitoring()
        self.dialog.destroy()
    
    def is_cancelled(self) -> bool:
        """취소 상태 확인"""
        return self.cancelled

def setup_progress_styles(root):
    """진행률 바 스타일 설정"""
    try:
        style = ttk.Style()
        
        # 성공 스타일 (녹색)
        style.configure(
            "Success.Horizontal.TProgressbar",
            background="green",
            troughcolor="lightgray"
        )
        
        # 경고 스타일 (주황색)
        style.configure(
            "Warning.Horizontal.TProgressbar",
            background="orange",
            troughcolor="lightgray"
        )
        
        # 위험 스타일 (빨간색)
        style.configure(
            "Danger.Horizontal.TProgressbar",
            background="red",
            troughcolor="lightgray"
        )
    except Exception as e:
        logger.warning(f"스타일 설정 실패: {e}")

# 사용 예제 함수들
def show_progress_dialog_example(parent):
    """진행률 대화상자 사용 예제"""
    dialog = ProgressDialog(parent, "Excel 파일 처리 중")
    
    def simulate_work():
        """작업 시뮬레이션"""
        for i in range(101):
            if dialog.is_cancelled():
                break
                
            progress = ProgressInfo(
                current=i,
                total=100,
                percentage=(i/100)*100,
                operation=f"데이터 처리 중... ({i}/100)",
                details={'stage': 'parsing' if i < 50 else 'generating'}
            )
            
            dialog.update_progress(progress)
            time.sleep(0.1)
        
        dialog.close()
    
    # 별도 스레드에서 작업 실행
    thread = threading.Thread(target=simulate_work)
    thread.daemon = True
    thread.start()
    
    return dialog

def show_error_dialog_example(parent):
    """오류 대화상자 사용 예제"""
    error = ExcelParsingError(
        message="파일을 찾을 수 없습니다: example.xlsx",
        category="file_access",
        severity="high",
        details={
            'file_path': 'C:/example.xlsx',
            'attempted_operation': 'read_excel'
        }
    )
    
    # 간단한 에러 표시
    messagebox.showerror("오류", error.get_user_friendly_message())
    return None
