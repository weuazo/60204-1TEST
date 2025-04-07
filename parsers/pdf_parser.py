from .parser_base import DocumentParser

class PdfParser(DocumentParser):
    """PDF 파일 파서"""
    
    def __init__(self):
        super().__init__()
        self.pages = []
        self.tables = []
        
    def parse(self, file_path, **kwargs):
        """PDF 파일 파싱"""
        self.file_path = file_path
        try:
            # PDF 처리 라이브러리 동적 임포트 (필요할 때만 설치 요구)
            try:
                import pdfplumber
            except ImportError:
                raise ImportError("PDF 파싱을 위해 'pdfplumber' 라이브러리가 필요합니다.\n" +
                                 "'pip install pdfplumber' 명령으로 설치하거나\n" +
                                 "알려진 종속성 패키지를 모두 설치하려면 'pip install -r requirements.txt'를 실행하세요.")
            
            # PDF 열기
            with pdfplumber.open(file_path) as pdf:
                # 페이지 범위 제한 옵션
                page_limit = kwargs.get('page_limit', 0)
                max_pages = min(len(pdf.pages), page_limit) if page_limit > 0 else len(pdf.pages)
                
                # 페이지별 텍스트 추출 (메모리 효율성 개선)
                for i, page in enumerate(pdf.pages[:max_pages]):
                    page_text = page.extract_text() or ""
                    self.pages.append(page_text)
                    
                    # 메모리 부담을 줄이기 위해 큰 텍스트는 요약
                    if len(page_text) > 10000:  # 10K 문자 이상
                        self.pages[-1] = page_text[:5000] + "..." + page_text[-3000:]
                    
                    # 테이블 추출 시도 (가능한 경우)
                    try:
                        tables = page.extract_tables()
                        if tables:
                            self.tables.extend(tables)
                    except:
                        pass  # 테이블 추출 실패 무시
            
            # 메타데이터 설정
            self.metadata = {
                'file_type': 'pdf',
                'pages': len(self.pages),
                'has_tables': len(self.tables) > 0
            }
            
            # 토큰 추정
            self.estimate_tokens()
            
            return True
        except ImportError as e:
            raise e
        except Exception as e:
            print(f"PDF 파싱 오류: {e}")
            return False
    
    def get_text_content(self):
        """모든 페이지의 텍스트 반환"""
        return "\n\n".join(self.pages)
    
    def get_structure(self):
        """PDF 파일의 구조 정보 반환"""
        if not self.pages:
            return None
            
        structure = {
            'type': 'pdf',
            'page_count': len(self.pages),
            'has_tables': len(self.tables) > 0,
            'page_lengths': [len(page) for page in self.pages]
        }
        
        # 테이블 정보 추가 (있는 경우)
        if self.tables:
            structure['table_count'] = len(self.tables)
            structure['table_sizes'] = [
                [len(table), len(table[0]) if table else 0] for table in self.tables
            ]
        
        return structure
    
    def get_page(self, page_num):
        """특정 페이지 텍스트 반환"""
        if 0 <= page_num < len(self.pages):
            return self.pages[page_num]
        return ""
    
    def get_tables(self):
        """추출된 모든 테이블 반환"""
        return self.tables

    def get_dataframe(self):
        """PDF 내용을 데이터프레임으로 변환 (기본 구현)"""
        import pandas as pd
        import re
        
        # 텍스트에서 항목 번호와 내용을 추출하는 간단한 구현
        text = self.get_text_content()
        
        # 항목 번호 패턴: 숫자.숫자 또는 숫자.숫자.숫자 형태
        pattern = r'(\d+\.\d+(?:\.\d+)?)\s+(.*?)(?=\d+\.\d+|\Z)'
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            df = pd.DataFrame(matches, columns=['항목번호', '내용'])
            return df
        
        # 항목을 찾지 못한 경우 텍스트를 한 줄씩 분리하여 반환
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        df = pd.DataFrame({'내용': lines})
        return df
