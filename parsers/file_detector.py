import os
import magic

def detect_file_type(file_path):
    """파일의 실제 형식 감지"""
    try:
        # magic 라이브러리 사용
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        
        # 주요 형식 매핑
        if 'spreadsheet' in file_type or 'excel' in file_type:
            return 'excel'
        elif 'pdf' in file_type:
            return 'pdf'
        elif 'word' in file_type or 'document' in file_type:
            return 'word'
        elif 'text' in file_type:
            return 'text'
        else:
            # 확장자 기반 대체 감지
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.xlsx', '.xls']:
                return 'excel'
            elif ext == '.pdf':
                return 'pdf'
            elif ext in ['.docx', '.doc']:
                return 'word'
            elif ext in ['.txt', '.csv']:
                return 'text'
    except:
        # magic 라이브러리가 없는 경우 확장자로만 판단
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.xlsx', '.xls']:
            return 'excel'
        elif ext == '.pdf':
            return 'pdf'
        elif ext in ['.docx', '.doc']:
            return 'word'
        elif ext in ['.txt', '.csv']:
            return 'text'
    
    return 'unknown'
