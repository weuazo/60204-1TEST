import pandas as pd
from .parser_base import DocumentParser

class ExcelParser(DocumentParser):
    """엑셀 파일 파서"""
    
    def __init__(self):
        super().__init__()
        self.sheets = {}
        self.active_sheet = None
        self.df = None
        
    def parse(self, file_path, sheet_name=0, **kwargs):
        """엑셀 파일 파싱"""
        self.file_path = file_path
        try:
            # 큰 파일일 경우 일부만 로드하는 옵션 추가
            chunk_size = kwargs.get("chunk_size", None)
            nrows = kwargs.get("nrows", None)
            
            # 모든 시트 로드 (기본 동작)
            if not chunk_size and not nrows:
                excel_file = pd.ExcelFile(file_path)
                sheet_names = excel_file.sheet_names
                
                for sheet in sheet_names:
                    self.sheets[sheet] = pd.read_excel(file_path, sheet_name=sheet)
            else:
                # 대용량 파일 처리 모드
                excel_file = pd.ExcelFile(file_path)
                sheet_names = excel_file.sheet_names
                
                for sheet in sheet_names:
                    self.sheets[sheet] = pd.read_excel(
                        file_path, 
                        sheet_name=sheet,
                        nrows=nrows
                    )
            
            # 활성 시트 설정 (기본값 또는 지정된 시트)
            if isinstance(sheet_name, int) and sheet_name < len(sheet_names):
                self.active_sheet = sheet_names[sheet_name]
            elif sheet_name in sheet_names:
                self.active_sheet = sheet_name
            else:
                self.active_sheet = sheet_names[0]
            
            # 현재 활성 시트의 데이터프레임
            self.df = self.sheets[self.active_sheet]
            
            # 메타데이터 추출
            self.metadata = {
                'file_type': 'excel',
                'sheets': sheet_names,
                'active_sheet': self.active_sheet,
                'columns': list(self.df.columns),
                'rows': len(self.df)
            }
            
            # 토큰 추정
            self.estimate_tokens()
            
            return True
        except Exception as e:
            print(f"Excel 파싱 오류: {e}")
            return False
    
    def get_text_content(self):
        """엑셀 내용을 텍스트로 변환"""
        if self.df is None:
            return ""
        
        # 각 행을 문자열로 변환
        rows = []
        for _, row in self.df.iterrows():
            # None 값 제거 및 문자열 변환
            row_values = [str(val) if pd.notna(val) else "" for val in row.values]
            rows.append(" | ".join(row_values))
        
        # 열 이름과 함께 반환
        header = " | ".join([str(col) for col in self.df.columns])
        return header + "\n" + "\n".join(rows)
    
    def get_structure(self):
        """엑셀 파일의 구조 정보 반환"""
        if not self.sheets:
            return None
            
        structure = {
            'type': 'excel',
            'sheets': {}
        }
        
        # 각 시트의 기본 구조 정보
        for sheet_name, df in self.sheets.items():
            structure['sheets'][sheet_name] = {
                'columns': list(df.columns),
                'rows': len(df),
                'has_header': True,
                'column_types': {str(col): str(dtype) for col, dtype in zip(df.columns, df.dtypes)}
            }
        
        return structure
    
    def get_sheet_names(self):
        """시트 이름 목록 반환"""
        return list(self.sheets.keys())
    
    def set_active_sheet(self, sheet_name):
        """활성 시트 변경"""
        if sheet_name in self.sheets:
            self.active_sheet = sheet_name
            self.df = self.sheets[sheet_name]
            return True
        return False
    
    def get_dataframe(self):
        """현재 활성 시트의 데이터프레임 반환"""
        return self.df
