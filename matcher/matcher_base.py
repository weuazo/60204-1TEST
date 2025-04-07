from abc import ABC, abstractmethod

class DocumentMatcher(ABC):
    """문서 간 항목 매칭을 위한 기본 추상 클래스"""
    
    def __init__(self):
        self.source_doc = None
        self.target_doc = None
        self.mappings = []
    
    @abstractmethod
    def match_documents(self, source_doc, target_doc, source_col=None, target_col=None, **kwargs):
        """
        두 문서 간 항목 매칭
        
        Args:
            source_doc: 소스 문서 (일반적으로 검토 시트)
            target_doc: 대상 문서 (일반적으로 템플릿)
            source_col: 소스 문서에서 매칭할 열
            target_col: 대상 문서에서 매칭할 열
        
        Returns:
            list: (소스 인덱스, 대상 인덱스, 신뢰도) 튜플의 리스트
        """
        pass
    
    @abstractmethod
    def match_item(self, source_item, target_doc, target_col=None, **kwargs):
        """
        단일 항목과 대상 문서의 항목들 매칭
        
        Args:
            source_item: 소스 항목
            target_doc: 대상 문서
            target_col: 대상 문서에서 매칭할 열
        
        Returns:
            tuple: (대상 인덱스, 신뢰도)
        """
        pass
    
    def get_mappings(self):
        """생성된 매핑 결과 반환"""
        return self.mappings
    
    def clear_mappings(self):
        """매핑 결과 초기화"""
        self.mappings = []
        self.source_doc = None
        self.target_doc = None
