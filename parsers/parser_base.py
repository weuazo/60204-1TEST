from abc import ABC, abstractmethod

class DocumentParser(ABC):
    """문서 파서의 기본 추상 클래스"""
    
    def __init__(self):
        self.file_path = None
        self.content = None
        self.structure = None
        self.metadata = {}
        self.tokens_estimate = 0
        
    @abstractmethod
    def parse(self, file_path, **kwargs):
        """문서를 파싱하여 내용과 구조를 추출"""
        pass
    
    @abstractmethod
    def get_text_content(self):
        """추출된 텍스트 콘텐츠 반환"""
        pass
    
    @abstractmethod
    def get_structure(self):
        """문서의 구조 정보(섹션, 표, 등) 반환"""
        pass
    
    def estimate_tokens(self):
        """추출된 텍스트의 토큰 수 추정"""
        text = self.get_text_content()
        if not text:
            return 0
            
        # 영어 텍스트의 경우 단어 수 * 1.3으로 토큰 추정
        # 한글 텍스트의 경우 문자 수 * 0.5으로 토큰 추정
        english_ratio = sum(1 for c in text if ord('a') <= ord(c.lower()) <= ord('z')) / len(text)
        
        if english_ratio > 0.5:  # 영어 위주 텍스트
            words = len(text.split())
            self.tokens_estimate = int(words * 1.3)
        else:  # 한글 위주 텍스트
            self.tokens_estimate = int(len(text) * 0.5)
            
        return self.tokens_estimate
    
    def get_metadata(self):
        """문서 메타데이터 반환"""
        return self.metadata
