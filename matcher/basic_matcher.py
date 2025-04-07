import re
import pandas as pd
from .matcher_base import DocumentMatcher

class BasicMatcher(DocumentMatcher):
    """기존 유연 매칭 알고리즘 기반 매처"""
    
    def __init__(self):
        super().__init__()
        self.match_mode = "flexible"  # "exact" 또는 "flexible"
    
    def match_documents(self, source_doc, target_doc, source_col=None, target_col=None, match_mode="flexible", **kwargs):
        """두 문서 간 항목 매칭"""
        self.source_doc = source_doc
        self.target_doc = target_doc
        self.match_mode = match_mode
        self.mappings = []
        
        # 소스 및 대상이 DataFrame인지 확인
        if not isinstance(source_doc, pd.DataFrame) or not isinstance(target_doc, pd.DataFrame):
            raise ValueError("source_doc과 target_doc는 pandas DataFrame이어야 합니다")
            
        if source_col not in source_doc.columns or target_col not in target_doc.columns:
            raise ValueError(f"매칭 열이 문서에 존재하지 않습니다: {source_col}, {target_col}")
        
        # 각 소스 행에 대해 대상 행 매칭
        for idx, row in source_doc.iterrows():
            source_value = str(row.get(source_col, "")).strip()
            if not source_value:
                continue
                
            target_idx = self._find_matching_row(source_value, target_doc, target_col)
            if target_idx is not None:
                confidence = 1.0 if self.match_mode == "exact" else 0.8
                self.mappings.append((idx, target_idx, confidence))
                
        return self.mappings
    
    def match_item(self, source_item, target_doc, target_col=None, match_mode="flexible", **kwargs):
        """단일 항목과 대상 문서의 항목들 매칭"""
        self.target_doc = target_doc
        self.match_mode = match_mode
        
        if not isinstance(target_doc, pd.DataFrame):
            raise ValueError("target_doc는 pandas DataFrame이어야 합니다")
            
        if target_col not in target_doc.columns:
            raise ValueError(f"매칭 열이 대상 문서에 존재하지 않습니다: {target_col}")
            
        target_idx = self._find_matching_row(source_item, target_doc, target_col)
        if target_idx is not None:
            confidence = 1.0 if self.match_mode == "exact" else 0.8
            return (target_idx, confidence)
            
        return (None, 0.0)
    
    def _find_matching_row(self, source_value, target_df, target_col):
        """대상 데이터프레임에서 매칭되는 행 찾기"""
        if self.match_mode == "exact":
            # 정확히 일치하는 항목만 찾기
            matches = target_df[target_df[target_col].astype(str).str.strip() == source_value]
            return matches.index[0] if not matches.empty else None
        else:
            # 유연한 매칭 사용
            return self._flexible_match(source_value, target_df, target_col)
    
    def _flexible_match(self, source_value, target_df, target_col):
        """유연한 매칭 알고리즘"""
        # 1. 정확한 일치 검색
        exact_matches = target_df[target_df[target_col].astype(str).str.strip() == source_value]
        if not exact_matches.empty:
            return exact_matches.index[0]
        
        # 2. 항목 번호 정규화
        normalized_source = self._normalize_clause_id(source_value)
        target_normalized = target_df[target_col].astype(str).apply(self._normalize_clause_id)
        
        # 정규화된 항목으로 정확히 일치하는 항목 검색
        normalized_matches = target_df[target_normalized == normalized_source]
        if not normalized_matches.empty:
            return normalized_matches.index[0]
        
        # 3. 접두어 매칭 (예: "8.2.1"은 "8.2"로 시작하는 항목과 매칭 가능)
        if "." in normalized_source:
            prefix = normalized_source.rsplit(".", 1)[0]
            prefix_matches = target_df[target_normalized.str.startswith(prefix)]
            if not prefix_matches.empty:
                return prefix_matches.index[0]
        
        # 4. 가장 유사한 항목 찾기
        if len(source_value) > 2:  # 최소한 의미있는 길이여야 함
            similarities = target_normalized.apply(
                lambda x: self._calculate_similarity(normalized_source, x) if isinstance(x, str) else 0
            )
            if similarities.max() > 0.7:  # 70% 이상 유사하면 매칭
                return similarities.idxmax()
        
        return None
    
    def _normalize_clause_id(self, clause_id):
        """항목 ID 정규화"""
        if not isinstance(clause_id, str):
            clause_id = str(clause_id)
        
        # 공백 및 특수문자 제거
        clause_id = clause_id.lower().strip()
        clause_id = re.sub(r'[^\d\w\.]', '', clause_id)
        
        return clause_id
    
    def _calculate_similarity(self, str1, str2):
        """두 문자열 간의 유사도 계산"""
        if not str1 or not str2:
            return 0
        
        # 최장 공통 접두어 길이
        i = 0
        min_len = min(len(str1), len(str2))
        while i < min_len and str1[i] == str2[i]:
            i += 1
        
        # 유사도 계산 (공통 접두어 비율)
        return i / max(len(str1), len(str2))
