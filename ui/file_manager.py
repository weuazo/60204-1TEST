import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from parsers import get_parser_for_file

class FileSelector:
    """파일 선택 및 미리보기 관리 위젯"""
    
    def __init__(self, parent, title="파일 선택", supported_types=None, callback=None):
        """
        파일 선택기 초기화
        
        Args:
            parent: 상위 위젯
            title: 섹션 제목
            supported_types: 지원되는 파일 유형 리스트 [('설명', '*.확장자'), ...]
            callback: 파일 선택 후 호출할 함수
        """
        self.parent = parent
        self.title = title
        self.file_path = ""
        self.parser = None
        self.callback = callback
        
        # 지원되는 파일 유형 (기본값: 엑셀)
        self.supported_types = supported_types or [("Excel 파일", "*.xlsx *.xls")]
        
        # UI 구성
        self.frame = ttk.LabelFrame(parent, text=title)
        self.frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 파일 선택 영역
        self.file_frame = ttk.Frame(self.frame)
        self.file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.entry = ttk.Entry(self.file_frame, width=50)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry.bind("<Enter>", self._show_path_tooltip)
        
        self.browse_btn = ttk.Button(
            self.file_frame, 
            text="찾아보기", 
            command=self.browse_file
        )
        self.browse_btn.pack(side=tk.LEFT, padx=5)
        
        # 파일 정보 영역
        self.info_frame = ttk.Frame(self.frame)
        self.info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 파일 유형 및 크기
        self.file_type_label = ttk.Label(self.info_frame, text="유형: -")
        self.file_type_label.pack(side=tk.LEFT, padx=5)
        
        self.file_size_label = ttk.Label(self.info_frame, text="크기: -")
        self.file_size_label.pack(side=tk.LEFT, padx=5)
        
        # 토큰 추정
        self.token_label = ttk.Label(self.info_frame, text="추정 토큰: -")
        self.token_label.pack(side=tk.RIGHT, padx=5)
        
        # 추가 설정 프레임 (확장 가능)
        self.config_frame = ttk.Frame(self.frame)
        # 설정이 있을 때만 표시
    
    def browse_file(self):
        """파일 찾아보기 대화상자"""
        path = filedialog.askopenfilename(
            title=f"{self.title} 선택",
            filetypes=self.supported_types
        )
        
        if not path:
            return  # 사용자가 취소함
            
        self.set_file(path)
    
    def set_file(self, path):
        """파일 경로 설정 및 정보 업데이트"""
        self.file_path = path
        self.entry.delete(0, tk.END)
        self.entry.insert(0, path)
        
        # 파일 정보 업데이트
        try:
            # 파일 크기
            size_bytes = os.path.getsize(path)
            size_str = self._format_size(size_bytes)
            
            # 파일 유형
            file_ext = os.path.splitext(path)[1].lower()
            file_type = {
                '.xlsx': 'Excel',
                '.xls': 'Excel',
                '.pdf': 'PDF',
                '.docx': 'Word',
                '.doc': 'Word'
            }.get(file_ext, '알 수 없음')
            
            self.file_type_label.config(text=f"유형: {file_type}")
            self.file_size_label.config(text=f"크기: {size_str}")
            
            # 파서 생성 및 파싱
            try:
                self.parser = get_parser_for_file(path)
                self.parser.parse(path)
                
                # 토큰 추정
                tokens = self.parser.estimate_tokens()
                self.token_label.config(text=f"추정 토큰: {tokens:,}개")
                
                # 콜백 호출 (있는 경우)
                if self.callback:
                    self.callback(self)
                    
                # 파일 유형별 추가 설정 UI 구성
                self._build_file_specific_config()
                
            except ImportError as e:
                # 필요한 라이브러리 누락 메시지
                messagebox.showwarning("라이브러리 필요", str(e))
            except Exception as e:
                messagebox.showerror("파싱 오류", f"파일을 분석하는 중 오류가 발생했습니다: {e}")
                
        except Exception as e:
            messagebox.showerror("파일 정보 오류", f"파일 정보를 가져오는 중 오류가 발생했습니다: {e}")
    
    def _format_size(self, size_bytes):
        """바이트 크기를 읽기 쉬운 형식으로 변환"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
    
    def _build_file_specific_config(self):
        """파일 유형에 따른 추가 설정 UI 구성"""
        # 이전 설정 위젯 제거
        for widget in self.config_frame.winfo_children():
            widget.destroy()
            
        # 파서가 없으면 종료
        if not self.parser:
            return
            
        # 설정 프레임 표시
        self.config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 파일 유형별 설정
        if hasattr(self.parser, 'get_sheet_names'):
            # 엑셀 파일 - 시트 선택
            sheet_names = self.parser.get_sheet_names()
            
            if sheet_names:
                sheet_frame = ttk.Frame(self.config_frame)
                sheet_frame.pack(fill=tk.X, pady=2)
                
                ttk.Label(sheet_frame, text="시트:").pack(side=tk.LEFT, padx=5)
                
                sheet_var = tk.StringVar(value=sheet_names[0])
                sheet_cb = ttk.Combobox(
                    sheet_frame, 
                    textvariable=sheet_var, 
                    values=sheet_names, 
                    state="readonly",
                    width=30
                )
                sheet_cb.pack(side=tk.LEFT, padx=5)
                
                # 시트 변경 이벤트
                def on_sheet_change(event):
                    sheet = sheet_var.get()
                    if sheet:
                        self.parser.set_active_sheet(sheet)
                        # 콜백 재호출
                        if self.callback:
                            self.callback(self)
                
                sheet_cb.bind("<<ComboboxSelected>>", on_sheet_change)
        
        elif hasattr(self.parser, 'get_pages'):
            # PDF 파일 - 페이지 범위 선택
            ttk.Label(
                self.config_frame, 
                text=f"전체 페이지 수: {len(self.parser.pages)}", 
                font=("Arial", 9, "italic")
            ).pack(anchor="w", padx=5)
            
            range_frame = ttk.Frame(self.config_frame)
            range_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(range_frame, text="페이지 범위:").pack(side=tk.LEFT, padx=5)
            
            from_page = ttk.Spinbox(range_frame, from_=1, to=len(self.parser.pages), width=5)
            from_page.pack(side=tk.LEFT, padx=5)
            from_page.insert(0, "1")
            
            ttk.Label(range_frame, text="~").pack(side=tk.LEFT)
            
            to_page = ttk.Spinbox(range_frame, from_=1, to=len(self.parser.pages), width=5)
            to_page.pack(side=tk.LEFT, padx=5)
            to_page.insert(0, str(len(self.parser.pages)))
            
            # 페이지 범위 저장
            self.parser.page_range = (1, len(self.parser.pages))
            
            # 페이지 범위 변경 함수
            def update_page_range():
                try:
                    from_val = max(1, int(from_page.get()))
                    to_val = min(len(self.parser.pages), int(to_page.get()))
                    self.parser.page_range = (from_val, to_val)
                except:
                    pass
                    
            from_page.config(command=update_page_range)
            to_page.config(command=update_page_range)
    
    def get_file_path(self):
        """선택된 파일 경로 반환"""
        return self.file_path
    
    def get_parser(self):
        """파서 객체 반환"""
        return self.parser
    
    def get_config(self):
        """현재 설정 반환"""
        config = {
            "file_path": self.file_path
        }
        
        # 파서별 추가 설정
        if self.parser:
            if hasattr(self.parser, 'active_sheet'):
                config["sheet"] = self.parser.active_sheet
                
            if hasattr(self.parser, 'page_range'):
                config["page_range"] = self.parser.page_range
                
        return config

    def _show_path_tooltip(self, event):
        """파일 경로 툴팁 표시"""
        if self.file_path:
            import tkinter.tix as tix
            try:
                # 툴팁 표시
                tip = tix.Balloon()
                tip.bind_widget(self.entry, balloonmsg=self.file_path)
            except:
                # tix를 사용할 수 없는 경우 대체 구현
                pass
