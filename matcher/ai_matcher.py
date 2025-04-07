import pandas as pd
import json
from .matcher_base import DocumentMatcher

class AIMatcher(DocumentMatcher):
    """Gemini API를 사용한 AI 기반 매처"""
    
    def __init__(self):
        super().__init__()
        self.mappings_with_details = []  # 매핑 결과 (상세 정보 포함)
        self.api_usage = {
            "calls": 0,
            "tokens": 0
        }
    
    def match_documents(self, source_doc, target_doc, source_col=None, target_col=None, **kwargs):
        """두 문서 간 항목 매칭 (AI 기반)"""
        self.source_doc = source_doc
        self.target_doc = target_doc
        self.mappings = []
        self.mappings_with_details = []
        
        # API 사용량 초기화
        self.api_usage = {"calls": 0, "tokens": 0}
        
        # 소스 및 대상이 DataFrame인지 확인
        if not isinstance(source_doc, pd.DataFrame) or not isinstance(target_doc, pd.DataFrame):
            raise ValueError("source_doc과 target_doc는 pandas DataFrame이어야 합니다")
            
        if source_col not in source_doc.columns or target_col not in target_doc.columns:
            raise ValueError(f"매칭 열이 문서에 존재하지 않습니다: {source_col}, {target_col}")
        
        # 소스 항목 추출 (최대 100개로 제한)
        source_items = source_doc[source_col].astype(str).tolist()
        if len(source_items) > 100:
            source_items = source_items[:100]
            
        # 대상 항목 추출 (최대 100개로 제한)
        target_items = target_doc[target_col].astype(str).tolist()
        if len(target_items) > 100:
            target_items = target_items[:100]
        
        # AI 호출을 위한 데이터 준비
        source_context = [
            f"{i+1}. {item}" for i, item in enumerate(source_items) if item.strip()
        ]
        
        target_context = [
            f"{i+1}. {item}" for i, item in enumerate(target_items) if item.strip()
        ]
        
        # API 호출에 너무 많은 토큰을 사용하지 않도록 문맥 제한
        if len("\n".join(source_context)) > 5000:
            source_context = source_context[:50]
        
        if len("\n".join(target_context)) > 5000:
            target_context = target_context[:50]
        
        # Gemini API 호출
        from api.gemini import call_gemini
        
        prompt = f"""
두 문서의 항목 번호(또는 ID) 목록이 있습니다. 두 목록에서 서로 매칭되는 항목을 찾아주세요.

문서 A의 항목 목록:
{chr(10).join(source_context)}

문서 B의 항목 목록:
{chr(10).join(target_context)}

위 두 목록에서 서로 매칭되는 항목들을 찾아서 JSON 형식으로 반환해주세요. 
매칭이 확실하지 않은 경우 confidence 값을 낮게 설정하세요.

다음 형식으로 응답해주세요:
[
  {{"source_index": 0, "target_index": 5, "source_item": "항목A", "target_item": "항목B", "confidence": 0.95}},
  {{"source_index": 1, "target_index": 2, "source_item": "항목C", "target_item": "항목D", "confidence": 0.8}}
]

주의: 응답은 반드시 유효한 JSON 형식이어야 합니다. 추가 설명 없이 JSON 배열만 반환해주세요.
"""
        
        try:
            # AI 응답 받기
            response = call_gemini(prompt)
            self.api_usage["calls"] += 1
            self.api_usage["tokens"] += len(prompt.split()) + len(response.split()) * 1.5  # 응답 토큰 추정
            
            # JSON 파싱
            # 응답에서 JSON 부분만 추출 (설명 텍스트가 있을 경우 제거)
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start >= 0 and json_end > 0:
                json_str = response[json_start:json_end]
                mappings_data = json.loads(json_str)
                
                # 매핑 결과 처리
                for item in mappings_data:
                    source_idx = item.get("source_index")
                    target_idx = item.get("target_index")
                    confidence = item.get("confidence", 0.0)
                    
                    # DataFrame 인덱스로 변환
                    if source_idx < len(source_doc) and target_idx < len(target_doc):
                        real_source_idx = source_doc.index[source_idx]
                        real_target_idx = target_doc.index[target_idx]
                        
                        self.mappings.append((real_source_idx, real_target_idx, confidence))
                        self.mappings_with_details.append({
                            "source_idx": real_source_idx,
                            "target_idx": real_target_idx,
                            "source_item": item.get("source_item"),
                            "target_item": item.get("target_item"),
                            "confidence": confidence
                        })
                
            else:
                raise ValueError("AI 응답에서 유효한 JSON을 찾을 수 없습니다")
                
        except Exception as e:
            print(f"AI 매칭 중 오류 발생: {e}")
            # 오류 발생 시 기본 매처로 대체
            from .basic_matcher import BasicMatcher
            basic = BasicMatcher()
            return basic.match_documents(source_doc, target_doc, source_col, target_col, **kwargs)
        
        return self.mappings
    
    def match_item(self, source_item, target_doc, target_col=None, **kwargs):
        """단일 항목과 대상 문서의 항목들 매칭"""
        self.target_doc = target_doc
        
        if not isinstance(target_doc, pd.DataFrame):
            raise ValueError("target_doc는 pandas DataFrame이어야 합니다")
            
        if target_col not in target_doc.columns:
            raise ValueError(f"매칭 열이 대상 문서에 존재하지 않습니다: {target_col}")
        
        # 대상 항목 추출 (최대 50개로 제한)
        target_items = target_doc[target_col].astype(str).tolist()[:50]
        
        # AI 호출을 위한 데이터 준비
        target_context = [f"{i+1}. {item}" for i, item in enumerate(target_items) if item.strip()]
        
        # Gemini API 호출
        from api.gemini import call_gemini
        
        prompt = f"""
다음 항목과 가장 잘 매칭되는 항목을 목록에서 찾아주세요:

검색할 항목: {source_item}

매칭 대상 목록:
{chr(10).join(target_context)}

위 목록에서 "{source_item}"와 가장 잘 매칭되는 항목의 인덱스와 신뢰도를 JSON 형식으로 반환해주세요:
{{"target_index": 5, "target_item": "가장 유사한 항목", "confidence": 0.95}}

주의: 응답은 반드시 유효한 JSON 형식이어야 합니다.
매칭되는 항목이 없다면 confidence를 0으로 설정하세요.
"""
        
        try:
            # AI 응답 받기
            response = call_gemini(prompt)
            self.api_usage["calls"] += 1
            self.api_usage["tokens"] += len(prompt.split()) + len(response.split()) * 1.5
            
            # JSON 파싱
            # 응답에서 JSON 부분만 추출
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > 0:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                
                target_idx = result.get("target_index")
                confidence = result.get("confidence", 0.0)
                
                # DataFrame 인덱스로 변환
                if target_idx < len(target_doc):
                    real_target_idx = target_doc.index[target_idx]
                    return (real_target_idx, confidence)
                
            return (None, 0.0)
                
        except Exception as e:
            print(f"AI 단일 항목 매칭 중 오류 발생: {e}")
            # 오류 발생 시 기본 매처로 대체
            from .basic_matcher import BasicMatcher
            basic = BasicMatcher()
            return basic.match_item(source_item, target_doc, target_col, **kwargs)
    
    def get_api_usage(self):
        """API 사용량 정보 반환"""
        return self.api_usage
    
    def get_mappings_with_details(self):
        """상세 정보가 포함된 매핑 결과 반환"""
        return self.mappings_with_details
