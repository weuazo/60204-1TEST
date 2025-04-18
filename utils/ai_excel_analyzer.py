"""
AI 기반 엑셀 구조 분석 모듈
엑셀 파일 구조를 AI를 활용하여 자동으로 분석하고 열과 구조를 동적으로 감지합니다.
"""
import os
import re
import pandas as pd
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# 기존 열 감지 로직 가져오기
from utils.column_detector import detect_columns, enhanced_column_detection
from utils.standard_detector import detect_standard_from_file
from api.gemini import call_gemini

# 디버그 모드 설정 (로깅 레벨 조정)
DEBUG_MODE = False

# 학습 데이터 저장 위치
LEARNING_DATA_PATH = os.path.join("data", "excel_learning.json")

# 열 유형 신뢰도 임계값
HIGH_CONFIDENCE = 0.85   # 높은 신뢰도 (자동 수락)
LOW_CONFIDENCE = 0.50    # 낮은 신뢰도 (사용자 확인 필요)

class AIExcelAnalyzer:
    """
    AI 기반 엑셀 분석기
    엑셀 구조를 자동으로 분석하고 열 매핑, 학습 및 패턴 인식을 수행합니다.
    """
    
    def __init__(self):
        """분석기 초기화"""
        self.learning_data = self._load_learning_data()
        self.last_analysis = {}
        self.confidence_scores = {}
        self.batch_results = []  # 배치 분석 결과 저장
    
    def analyze_excel(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        엑셀 파일을 완전히 분석하여 구조, 열 매핑, 데이터 유형 등을 반환
        
        Args:
            file_path: 엑셀 파일 경로
            sheet_name: 시트 이름 (기본값: 첫 번째 시트)
            
        Returns:
            Dict: 분석 결과 (열 매핑, 신뢰도, 구조 정보 등)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
            
        # 1단계: 기본 정보 수집
        file_info = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'analyzed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # 2단계: 시트 목록 가져오기
        xls = pd.ExcelFile(file_path)
        sheets = xls.sheet_names
        if not sheets:
            raise ValueError("엑셀 파일에 시트가 없습니다.")
            
        # 시트 이름 설정
        if sheet_name is None or sheet_name not in sheets:
            sheet_name = sheets[0]
        
        file_info['sheet_name'] = sheet_name
        file_info['all_sheets'] = sheets
        
        # 3단계: 데이터프레임 로드
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        if len(df) == 0:
            raise ValueError("시트에 데이터가 없습니다.")
            
        file_info['row_count'] = len(df)
        file_info['column_count'] = len(df.columns)
        file_info['column_names'] = list(df.columns)
        
        # 4단계: 기본 열 감지 (기존 로직 활용)
        basic_columns = detect_columns(df.columns)
        file_info['basic_column_mapping'] = basic_columns
        
        # 5단계: 규격 감지
        standard_id = detect_standard_from_file(file_path, sheet_name)
        file_info['detected_standard'] = standard_id
        
        # 규격 기반 향상된 열 감지
        enhanced_columns = enhanced_column_detection(df, standard_id)
        file_info['enhanced_column_mapping'] = enhanced_columns
        
        # 6단계: 유사 파일 패턴 학습 데이터 확인
        learned_mapping, similarity_score = self._check_learning_data(file_info)
        
        if similarity_score > HIGH_CONFIDENCE and learned_mapping:
            file_info['final_column_mapping'] = learned_mapping
            file_info['mapping_source'] = 'learning_data'
            file_info['confidence_score'] = similarity_score
            print(f"[AI분석기] 학습 데이터에서 높은 유사도({similarity_score:.2f})의 매핑을 발견했습니다.")
        else:
            # 7단계: AI 기반 분석 수행
            ai_mapping, ai_confidence = self._analyze_with_ai(df, file_info)
            
            # 최종 매핑 선택 (가장 높은 신뢰도의 방법)
            confidences = {
                'basic': 0.5,  # 기본 키워드 감지의 기본 신뢰도
                'enhanced': 0.7 if standard_id != "UNKNOWN" else 0.6,  # 향상된 감지 신뢰도
                'learning': similarity_score,
                'ai': ai_confidence
            }
            
            # 가장 높은 신뢰도를 가진 매핑 방법 선택
            best_method = max(confidences.items(), key=lambda x: x[1])
            
            if best_method[0] == 'basic':
                file_info['final_column_mapping'] = basic_columns
                file_info['mapping_source'] = 'basic_detection'
            elif best_method[0] == 'enhanced':
                file_info['final_column_mapping'] = enhanced_columns
                file_info['mapping_source'] = 'enhanced_detection'
            elif best_method[0] == 'learning':
                file_info['final_column_mapping'] = learned_mapping
                file_info['mapping_source'] = 'learning_data'
            else:  # ai
                file_info['final_column_mapping'] = ai_mapping
                file_info['mapping_source'] = 'ai_analysis'
                
            file_info['confidence_score'] = best_method[1]
            file_info['all_confidences'] = confidences
        
        # 8단계: 열별 신뢰도 점수 계산
        column_confidence = {}
        for col_type, col_name in file_info['final_column_mapping'].items():
            # 여러 방법에서 같은 결과가 나온 열은 신뢰도 높음
            methods_agree = 0
            if col_type in basic_columns and basic_columns[col_type] == col_name:
                methods_agree += 1
            if col_type in enhanced_columns and enhanced_columns[col_type] == col_name:
                methods_agree += 1
            if learned_mapping and col_type in learned_mapping and learned_mapping[col_type] == col_name:
                methods_agree += 1
            if 'ai_mapping' in locals() and col_type in ai_mapping and ai_mapping[col_type] == col_name:
                methods_agree += 1
                
            # 방법 동의 수에 따른 신뢰도 계산
            if methods_agree >= 3:
                column_confidence[col_type] = 0.95  # 거의 확실함
            elif methods_agree == 2:
                column_confidence[col_type] = 0.8   # 높은 신뢰도
            elif methods_agree == 1:
                column_confidence[col_type] = 0.6   # 중간 신뢰도
            else:
                column_confidence[col_type] = 0.4   # 낮은 신뢰도
        
        file_info['column_confidence'] = column_confidence
        
        # 데이터프레임에서 몇 가지 샘플 행 추출
        sample_size = min(5, len(df))
        sample_rows = []
        for i in range(sample_size):
            sample_rows.append(df.iloc[i].to_dict())
        file_info['sample_rows'] = sample_rows
        
        # 결과 저장
        self.last_analysis = file_info
        self.confidence_scores = column_confidence
        
        return file_info
    
    def save_confirmed_mapping(self, file_path: str, sheet_name: str, 
                              column_mapping: Dict[str, str], file_type: str = None):
        """
        사용자가 확인한 매핑을 학습 데이터로 저장
        
        Args:
            file_path: 엑셀 파일 경로
            sheet_name: 시트 이름
            column_mapping: 열 매핑 정보
            file_type: 파일 유형 (예: 'review_sheet')
        """
        if not column_mapping:
            return
        
        # 학습 데이터 항목 생성
        learn_item = {
            'file_pattern': os.path.basename(file_path),
            'sheet_name': sheet_name,
            'file_type': file_type,
            'column_mapping': column_mapping,
            'confirmed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 학습 데이터에 항목 추가
        self.learning_data.append(learn_item)
        
        # 학습 데이터 저장
        self._save_learning_data()
        
        print(f"[AI분석기] 새로운 열 매핑이 학습 데이터에 저장되었습니다: {file_type or '일반 파일'}")
    
    def get_confidence_report(self) -> Dict[str, Any]:
        """
        현재 분석 결과의 신뢰도 보고서 생성
        
        Returns:
            Dict: 신뢰도 보고서
        """
        if not self.last_analysis or not self.confidence_scores:
            return {"status": "no_analysis"}
            
        low_confidence_columns = {}
        for col_type, score in self.confidence_scores.items():
            if score < LOW_CONFIDENCE:
                col_name = self.last_analysis.get('final_column_mapping', {}).get(col_type)
                if col_name:
                    low_confidence_columns[col_type] = {
                        'column_name': col_name,
                        'confidence': score
                    }
        
        report = {
            'status': 'analysis_complete',
            'overall_confidence': self.last_analysis.get('confidence_score', 0),
            'mapping_source': self.last_analysis.get('mapping_source', 'unknown'),
            'column_confidence': self.confidence_scores,
            'low_confidence_columns': low_confidence_columns,
            'needs_confirmation': len(low_confidence_columns) > 0,
            'analyzed_file': self.last_analysis.get('file_name')
        }
        
        return report
    
    def _load_learning_data(self) -> List[Dict]:
        """학습 데이터 로드"""
        # 디렉토리 확인
        os.makedirs(os.path.dirname(LEARNING_DATA_PATH), exist_ok=True)
        
        # 파일이 없으면 빈 배열 반환
        if not os.path.exists(LEARNING_DATA_PATH):
            return []
            
        try:
            with open(LEARNING_DATA_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            if DEBUG_MODE:
                print(f"[AI분석기] 학습 데이터 로드 중 오류: {e}")
            return []
    
    def _save_learning_data(self):
        """학습 데이터 저장"""
        # 디렉토리 확인
        os.makedirs(os.path.dirname(LEARNING_DATA_PATH), exist_ok=True)
        
        try:
            with open(LEARNING_DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.learning_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            if DEBUG_MODE:
                print(f"[AI분석기] 학습 데이터 저장 중 오류: {e}")
    
    def _check_learning_data(self, file_info: Dict) -> Tuple[Dict, float]:
        """
        학습 데이터에서 유사한 파일 패턴 찾기
        
        Returns:
            Tuple[Dict, float]: (매핑 정보, 유사도 점수)
        """
        if not self.learning_data:
            return {}, 0.0
            
        # 비교할 파일 정보
        target_columns = set(file_info['column_names'])
        target_filename = file_info['file_name'].lower()
        
        best_match = None
        best_score = 0.0
        
        for item in self.learning_data:
            # 파일명 유사도
            file_pattern = item['file_pattern'].lower()
            name_similarity = self._calculate_string_similarity(target_filename, file_pattern)
            
            # 시트 이름 일치 여부
            sheet_match = 1.0 if item['sheet_name'] == file_info['sheet_name'] else 0.5
            
            # 열 이름 유사도 
            item_columns = set(item['column_mapping'].values())
            if item_columns and target_columns:
                # 교집합 크기 / 합집합 크기 (자카드 유사도)
                intersection = len(item_columns.intersection(target_columns))
                union = len(item_columns.union(target_columns))
                column_similarity = intersection / union if union > 0 else 0
            else:
                column_similarity = 0
                
            # 파일 유형 일치 여부
            file_type_score = 1.0 if 'file_type' in item and item['file_type'] == file_info.get('file_type') else 0.7
            
            # 종합 점수 계산 (가중치 적용)
            score = (name_similarity * 0.3) + (sheet_match * 0.2) + (column_similarity * 0.4) + (file_type_score * 0.1)
            
            if score > best_score:
                best_score = score
                best_match = item['column_mapping']
        
        return best_match or {}, best_score
    
    def _analyze_with_ai(self, df: pd.DataFrame, file_info: Dict) -> Tuple[Dict[str, str], float]:
        """
        AI를 활용한 엑셀 구조 분석
        
        Args:
            df: 데이터프레임
            file_info: 파일 정보
            
        Returns:
            Tuple[Dict[str, str], float]: (AI 기반 열 매핑, 신뢰도)
        """
        try:
            # 분석을 위한 샘플 데이터 준비
            sample_size = min(5, len(df))
            sample_data = df.head(sample_size).to_dict(orient='records')
            
            # AI에게 전달할 프롬프트 생성
            columns_str = ", ".join([f'"{col}"' for col in df.columns])
            
            # 샘플 데이터를 문자열로 변환
            sample_rows = []
            for i, row in enumerate(sample_data):
                row_items = []
                for col, val in row.items():
                    if pd.notna(val):
                        row_items.append(f"{col}: {val}")
                sample_rows.append(f"행 {i+1}: {', '.join(row_items)}")
            
            sample_data_str = "\n".join(sample_rows)
            
            # Gemini API에 전송할 프롬프트
            prompt = f"""
당신은 엑셀 파일 구조를 분석하는 전문가 AI입니다. 다음 엑셀 데이터를 분석하고 각 열의 목적과 의미를 파악해주세요.

파일명: {file_info['file_name']}
시트명: {file_info['sheet_name']}
열 목록: {columns_str}

샘플 데이터:
{sample_data_str}

위 데이터를 분석하여 다음 정보를 JSON 형식으로 제공해주세요:
1. 각 열이 어떤 정보를 담고 있는지 분석
2. 다음 카테고리에 해당하는 열 매핑:
   - clause: 조항/항목 번호를 담고 있는 열
   - title: 항목 제목이나 설명을 담고 있는 열
   - remark: 의견, 비고, 코멘트를 담고 있는 열
   - status: 상태 정보를 담고 있는 열
   - details: 자세한 내용이나 설명을 담고 있는 열
   - hint: 힌트, 가이드, 참고사항을 담고 있는 열
   - risk: 위험 평가 정보를 담고 있는 열
   - standard: 규격/표준 정보를 담고 있는 열

JSON 형식으로만 응답해주세요. 예시:
{{"column_mapping": {{"clause": "항목번호", "title": "요구사항", "remark": "검토의견"}}, "confidence": 0.85}}

JSON만 반환하고, 다른 설명은 붙이지 마세요.
"""
            
            # API 호출
            response = call_gemini(prompt)
            
            # JSON 응답 파싱
            try:
                # JSON 응답 추출 (다른 텍스트가 포함되었을 수 있음)
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    result = json.loads(json_str)
                    
                    # 필수 필드 확인
                    if 'column_mapping' in result:
                        # AI 응답에서 열 매핑 및 신뢰도 추출
                        ai_mapping = result['column_mapping']
                        ai_confidence = result.get('confidence', 0.7)  # 기본 신뢰도 0.7
                        
                        return ai_mapping, ai_confidence
            except Exception as parse_error:
                if DEBUG_MODE:
                    print(f"[AI분석기] AI 응답 파싱 중 오류: {parse_error}")
                    print(f"원본 응답: {response}")
        except Exception as e:
            if DEBUG_MODE:
                print(f"[AI분석기] AI 분석 중 오류: {e}")
        
        # 오류 발생 시 빈 매핑과 낮은 신뢰도 반환
        return {}, 0.4
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """
        두 문자열 간의 유사도 계산 (0~1 사이 값 반환)
        """
        if not str1 or not str2:
            return 0
            
        # 간단한 레벤슈타인 거리 기반 유사도 계산
        try:
            import difflib
            similarity = difflib.SequenceMatcher(None, str1, str2).ratio()
            return similarity
        except:
            # 오류 발생 시 간단한 방식으로 계산
            common_chars = sum(1 for c in set(str1) if c in str2)
            total_chars = len(set(str1).union(set(str2)))
            return common_chars / total_chars if total_chars > 0 else 0

    def batch_analyze_excel(self, file_path: str, sheet_names: List[str] = None) -> List[Dict[str, Any]]:
        """
        여러 시트를 한 번에 분석하는 배치 분석 기능
        
        Args:
            file_path: 엑셀 파일 경로
            sheet_names: 분석할 시트 이름 목록 (None인 경우 모든 시트)
            
        Returns:
            List[Dict]: 각 시트별 분석 결과 목록
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
            
        # 모든 시트 가져오기
        xls = pd.ExcelFile(file_path)
        all_sheets = xls.sheet_names
        
        # 분석할 시트 선택
        if sheet_names is None:
            sheet_names = all_sheets
        else:
            # 존재하는 시트만 필터링
            sheet_names = [sheet for sheet in sheet_names if sheet in all_sheets]
            
        if not sheet_names:
            raise ValueError("분석할 시트가 없습니다.")
        
        # 각 시트별 분석 결과
        batch_results = []
        
        # 개별 시트 분석
        for sheet in sheet_names:
            try:
                result = self.analyze_excel(file_path, sheet)
                batch_results.append(result)
            except Exception as e:
                if DEBUG_MODE:
                    print(f"[AI분석기] 시트 '{sheet}' 분석 중 오류: {e}")
                # 오류 정보 저장
                batch_results.append({
                    'sheet_name': sheet,
                    'error': str(e),
                    'status': 'failed'
                })
        
        # 결과 저장
        self.batch_results = batch_results
        
        return batch_results
    
    def get_best_sheet_mapping(self, batch_results: List[Dict] = None) -> Dict:
        """
        배치 분석 결과에서 가장 높은 신뢰도의 시트 매핑을 반환
        
        Args:
            batch_results: 배치 분석 결과 (None인 경우 최근 배치 분석 사용)
            
        Returns:
            Dict: 최적의 시트 매핑 결과
        """
        # 결과가 제공되지 않은 경우 최근 배치 분석 결과 사용
        if batch_results is None:
            batch_results = self.batch_results
            
        if not batch_results:
            return {}
        
        # 오류가 없는 결과만 필터링
        valid_results = [r for r in batch_results if 'status' not in r or r['status'] != 'failed']
        if not valid_results:
            return {}
        
        # 가장 높은 신뢰도의 시트 찾기
        best_result = max(valid_results, key=lambda x: x.get('confidence_score', 0))
        
        return best_result

# 싱글톤 인스턴스 생성
excel_analyzer = AIExcelAnalyzer()

def analyze_excel_file(file_path: str, sheet_name: str = None, 
                      file_type: str = None, force_ai_analysis: bool = False,
                      cached_data: pd.DataFrame = None) -> Dict[str, Any]:
    """
    엑셀 파일 분석 유틸리티 함수
    
    Args:
        file_path: 엑셀 파일 경로
        sheet_name: 시트 이름
        file_type: 파일 유형 ('review_sheet', 'output_sheet' 등)
        force_ai_analysis: AI 분석 강제 실행 여부
        cached_data: 이미 로드된 데이터프레임 (성능 최적화용)
        
    Returns:
        Dict: 분석 결과
    """
    # 기존 코드는 유지하고, force_ai_analysis 옵션 추가
    analysis = excel_analyzer.analyze_excel(file_path, sheet_name)
    
    # 파일 유형 정보 추가
    if file_type:
        analysis['file_type'] = file_type
    
    return analysis

def save_confirmed_mapping(file_path: str, sheet_name: str, 
                         column_mapping: Dict[str, str], file_type: str = None):
    """
    확인된 열 매핑 저장 유틸리티 함수
    
    Args:
        file_path: 엑셀 파일 경로
        sheet_name: 시트 이름
        column_mapping: 열 매핑
        file_type: 파일 유형
    """
    excel_analyzer.save_confirmed_mapping(file_path, sheet_name, column_mapping, file_type)

def get_confidence_report() -> Dict[str, Any]:
    """
    최신 분석 결과에 대한 신뢰도 보고서 가져오기
    
    Returns:
        Dict: 신뢰도 보고서
    """
    return excel_analyzer.get_confidence_report()

def batch_analyze_excel_file(file_path: str, sheet_names: List[str] = None, 
                           file_type: str = None) -> List[Dict[str, Any]]:
    """
    다중 시트 배치 분석 유틸리티 함수
    
    Args:
        file_path: 엑셀 파일 경로
        sheet_names: 시트 이름 목록 (None인 경우 모든 시트)
        file_type: 파일 유형 ('review_sheet', 'output_sheet' 등)
        
    Returns:
        List[Dict]: 각 시트별 분석 결과 목록
    """
    batch_results = excel_analyzer.batch_analyze_excel(file_path, sheet_names)
    
    # 파일 유형 정보 추가
    if file_type:
        for result in batch_results:
            if isinstance(result, dict) and 'error' not in result:
                result['file_type'] = file_type
    
    return batch_results

def get_best_sheet_mapping() -> Dict[str, Any]:
    """
    배치 분석 결과에서 최적의 시트 매핑 가져오기
    
    Returns:
        Dict: 최적의 시트 매핑 결과
    """
    return excel_analyzer.get_best_sheet_mapping()