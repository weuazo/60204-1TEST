# 파서 패키지 초기화
from .parser_base import DocumentParser
from .excel_parser import ExcelParser
from .pdf_parser import PdfParser
from .word_parser import WordParser

def get_parser_for_file(file_path):
    """파일 확장자에 따른 적절한 파서 반환"""
    import os
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.xlsx', '.xls']:
        return ExcelParser()
    elif ext in ['.pdf']:
        return PdfParser()
    elif ext in ['.docx', '.doc']:
        return WordParser()
    else:
        raise ValueError(f"지원되지 않는 파일 형식: {ext}")
