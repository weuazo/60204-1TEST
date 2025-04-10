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
    
    def _batch_process(self, items, batch_size=50):
        """Helper function to split items into batches."""
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]

    def match_documents(self, source_doc, target_doc, source_col=None, target_col=None, **kwargs):
        """
        Match items between two documents using AI in batches.
        """
        self.source_doc = source_doc
        self.target_doc = target_doc
        self.mappings = []
        self.mappings_with_details = []

        # API usage initialization
        self.api_usage = {"calls": 0, "tokens": 0}

        # Validate inputs
        if not isinstance(source_doc, pd.DataFrame) or not isinstance(target_doc, pd.DataFrame):
            raise ValueError("source_doc and target_doc must be pandas DataFrames")

        if source_col not in source_doc.columns or target_col not in target_doc.columns:
            raise ValueError(f"Columns not found in documents: {source_col}, {target_col}")

        # Extract source and target items
        source_items = source_doc[source_col].astype(str).tolist()
        target_items = target_doc[target_col].astype(str).tolist()

        # Batch processing for source items
        from api.gemini import call_gemini

        for source_batch in self._batch_process(source_items):
            source_context = [f"{i+1}. {item}" for i, item in enumerate(source_batch) if item.strip()]
            target_context = [f"{i+1}. {item}" for i, item in enumerate(target_items) if item.strip()]

            # Construct prompt
            prompt = f"""
            Match the following items from Document A to Document B:

            Document A:
            {chr(10).join(source_context)}

            Document B:
            {chr(10).join(target_context)}

            Return matches in JSON format as:
            [
              {{"source_index": 0, "target_index": 5, "confidence": 0.95}},
              {{"source_index": 1, "target_index": 2, "confidence": 0.8}}
            ]
            """

            try:
                # Call Gemini API
                response = call_gemini(prompt)
                self.api_usage["calls"] += 1
                self.api_usage["tokens"] += len(prompt.split()) + len(response.split()) * 1.5

                # Parse JSON response
                json_start = response.find('[')
                json_end = response.rfind(']') + 1

                if json_start >= 0 and json_end > 0:
                    json_str = response[json_start:json_end]
                    mappings_data = json.loads(json_str)

                    for item in mappings_data:
                        source_idx = item.get("source_index")
                        target_idx = item.get("target_index")
                        confidence = item.get("confidence", 0.0)

                        if source_idx < len(source_doc) and target_idx < len(target_doc):
                            real_source_idx = source_doc.index[source_idx]
                            real_target_idx = target_doc.index[target_idx]

                            self.mappings.append((real_source_idx, real_target_idx, confidence))
                            self.mappings_with_details.append({
                                "source_idx": real_source_idx,
                                "target_idx": real_target_idx,
                                "confidence": confidence
                            })
                else:
                    raise ValueError("Invalid JSON response from AI")

            except Exception as e:
                print(f"Error during AI matching: {e}")
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
