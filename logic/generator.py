import os
import pandas as pd
import re
from datetime import datetime
from api.gemini import call_gemini_with_prompts
from utils.prompt_loader import load_prompts_by_type
from utils.standard_detector import detect_standard_from_file, get_standard_info

def generate_remarks(base_path, review_path, sheet_name, clause_col, title_col, remark_col, prompt_names,
                   matching_mode="ai", standard_id=None):  # standard_id 매개변수 추가
    """
    두 엑셀 파일을 비교하여 선택된 프롬프트로 의견을 생성
    
    Args:
        base_path: 템플릿 파일 경로
        review_path: 검토 시트 파일 경로
        sheet_name: 검토 시트 이름
        clause_col: 항목 열 이름
        title_col: 제목 열 이름
        remark_col: 결과 저장 열 이름
        prompt_names: 사용할 프롬프트 이름 목록
        matching_mode: 항목 매칭 모드 ("ai" 또는 "basic")
        standard_id: 규격 ID (None이면 자동 감지)
    
    Returns:
        결과 파일 경로
    """
    # standard_id가 None이면 자동 감지
    if standard_id is None:
        try:
            standard_id = detect_standard_from_file(review_path, sheet_name)
        except Exception as e:
            print(f"규격 자동 감지 중 오류: {e}")
            standard_id = "UNKNOWN"
    
    print(f"generate_remarks: 템플릿={base_path}, 검토시트={review_path}:{sheet_name}, 매칭모드={matching_mode}")
    
    # 단일 프롬프트 호환성 유지
    if isinstance(prompt_names, str):
        prompt_names = [prompt_names]
    
    # 파일 경로 검증
    validate_paths(base_path, review_path)
    
    # 규격 정보 가져오기
    standard_info = get_standard_info(standard_id)
    print(f"적용 규격: {standard_info['title']}")
    
    # 템플릿 파일과 검토 시트 로드
    df_base, df_review = load_excel_files(base_path, review_path, sheet_name)
    
    # 열 검증
    validate_columns(df_base, df_review, clause_col, title_col)
    
    # 템플릿 파일에 결과 열이 없으면 생성
    if remark_col not in df_base.columns:
        df_base[remark_col] = ""
        print(f"결과 열 '{remark_col}'이 템플릿에 없어 새로 생성했습니다.")
    
    # 프롬프트 검증 및 필터링
    selected_prompts = validate_and_filter_prompts(prompt_names)
    
    # 매처 생성 (AI 또는 기본)
    from matcher import create_matcher
    matcher = create_matcher(matching_mode)
    
    # 매칭 수행
    print(f"문서 매칭 중... 모드: {matching_mode}")
    mappings = matcher.match_documents(
        df_review, 
        df_base, 
        source_col=clause_col, 
        target_col=clause_col
    )
    
    print(f"매칭 결과: {len(mappings)}개 항목 매칭됨")
    
    # AI 매칭인 경우 사용량 보고
    if matching_mode == "ai" and hasattr(matcher, 'get_api_usage'):
        usage = matcher.get_api_usage()
        print(f"매칭 API 사용: {usage['calls']}번 호출, 약 {usage['tokens']}개 토큰")
    
    # 각 행 처리
    processed = 0
    matched = 0
    total_rows = len(df_review)
    
    # 매핑된 항목들을 기반으로 처리
    for review_idx, base_idx, confidence in mappings:
        clause = str(df_review.loc[review_idx, clause_col]).strip()
        title = str(df_review.loc[review_idx, title_col]).strip()
        
        if not clause:
            continue  # 빈 항목은 건너뛰기
            
        matched += 1
            
        # 컨텍스트 구축 (검토 시트의 모든 관련 정보 포함)
        context = build_context_from_row(df_review.loc[review_idx], df_review.columns, standard_id)
        
        # 프롬프트 준비 (규격 정보 포함)
        input_text = (
            f"항목: {clause}, 제목: {title}\n\n"
            f"규격: {standard_info['title']}\n\n"
            f"관련 정보:\n{context}\n\n"
            f"위 항목에 대한 검토 의견을 작성해주세요."
        )
        
        try:
            # Gemini API 호출 (규격 정보 포함)
            reply = call_gemini_with_prompts(input_text, prompt_names, standard_info=standard_info)
            
            # 결과를 템플릿 파일에 저장
            df_base.loc[base_idx, remark_col] = reply
        except Exception as e:
            print(f"항목 {clause} 처리 중 오류: {e}")
            df_base.loc[base_idx, remark_col] = f"[오류] {str(e)}"
        
        processed += 1
        if processed % 5 == 0 or processed == len(mappings):
            print(f"처리 중: {processed}/{len(mappings)} ({int(processed/len(mappings)*100)}%)")
    
    # 결과 저장 및 경로 반환
    return save_result_file(df_base)

def find_matching_clause_idx(df, clause_col, clause_id):
    """
    유연한 항목 매칭 함수 - 클래스 번호가 정확히 일치하지 않아도 찾을 수 있음
    
    Args:
        df: DataFrame - 템플릿 파일 데이터
        clause_col: str - 항목 열 이름
        clause_id: str - 찾을 항목 ID (예: "8.2.1")
        
    Returns:
        int: 매칭된 행 인덱스 또는 None
    """
    # 1. 정확한 일치 검색
    exact_matches = df[df[clause_col].astype(str).str.strip() == clause_id]
    if not exact_matches.empty:
        return exact_matches.index[0]
    
    # 2. 항목 번호 정규화
    normalized_clause = normalize_clause_id(clause_id)
    df_clause_normalized = df[clause_col].astype(str).apply(normalize_clause_id)
    
    # 정규화된 항목으로 정확히 일치하는 항목 검색
    normalized_matches = df[df_clause_normalized == normalized_clause]
    if not normalized_matches.empty:
        return normalized_matches.index[0]
    
    # 3. 접두어 매칭 (예: "8.2.1"은 "8.2"로 시작하는 항목과 매칭 가능)
    if "." in normalized_clause:
        prefix = normalized_clause.rsplit(".", 1)[0]
        prefix_matches = df[df_clause_normalized.str.startswith(prefix)]
        if not prefix_matches.empty:
            return prefix_matches.index[0]
    
    # 4. 가장 유사한 항목 찾기
    if len(clause_id) > 2:  # 최소한 의미있는 길이여야 함
        similarities = df_clause_normalized.apply(
            lambda x: calculate_similarity(normalized_clause, x) if isinstance(x, str) else 0
        )
        if similarities.max() > 0.7:  # 70% 이상 유사하면 매칭
            return similarities.idxmax()
    
    return None  # 매칭 실패

def normalize_clause_id(clause_id):
    """
    항목 ID 정규화 (공백 제거, 소문자 변환, 앞뒤 문자 정리)
    예: " 8.2 " -> "8.2", "8.2)" -> "8.2"
    """
    if not isinstance(clause_id, str):
        clause_id = str(clause_id)
    
    # 공백 및 특수문자 제거
    clause_id = clause_id.lower().strip()
    clause_id = re.sub(r'[^\d\w\.]', '', clause_id)
    
    # 불필요한 접미사 제거
    return clause_id

def calculate_similarity(str1, str2):
    """
    두 문자열 간의 간단한 유사도 계산 (0~1 사이 값 반환)
    """
    if not str1 or not str2:
        return 0
    
    # 최장 공통 접두어 길이
    i = 0
    min_len = min(len(str1), len(str2))
    while i < min_len and str1[i] == str2[i]:
        i += 1
    
    # 유사도 계산 (공통 접두어 비율)
    return i / max(len(str1), len(str2))

def build_context_from_row(row, columns, standard):
    """
    행 데이터에서 AI에게 제공할 풍부한 컨텍스트 구성
    
    Args:
        row: Series - 검토 시트의 한 행
        columns: list - 열 이름 목록
        standard: str - 감지된 표준/규격
        
    Returns:
        str: 컨텍스트 정보
    """
    context_parts = []
    
    # 주요 열 그룹화 (항목, 내용, 검토 관련, 기타)
    key_columns = {
        '항목 정보': ['clause', 'no', 'item', '번호', '항목', '조항'],
        '내용 정보': ['title', '제목', 'name', 'description', '내용', '요구사항'],
        '검토 관련': ['review', '검토', 'remark', '비고', '의견', '결과', '검토의견'],
        '참고 정보': ['reference', '참고', 'note', '비고']
    }
    
    # 각 열 그룹에 해당하는 값 추출
    for group_name, keywords in key_columns.items():
        group_data = []
        for col in columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in keywords):
                value = row.get(col, "")
                if pd.notna(value) and value != "":
                    group_data.append(f"{col}: {value}")
        
        if group_data:
            context_parts.append(f"# {group_name}\n" + "\n".join(group_data))
    
    # 규격별 특화 정보 추가
    if standard != "UNKNOWN":
        context_parts.append(f"# 적용 규격 정보\n규격: {standard}")
    
    return "\n\n".join(context_parts)

def validate_paths(base_path, review_path):
    """파일 경로 검증"""
    if not base_path:
        raise ValueError("템플릿 파일 경로가 비어있습니다.")
        
    if not review_path:
        raise ValueError("검토 시트 파일 경로가 비어있습니다.")
    
    if not os.path.exists(base_path):
        raise ValueError(f"템플릿 파일을 찾을 수 없습니다: {base_path}")
    
    if not os.path.exists(review_path):
        raise ValueError(f"검토 시트 파일을 찾을 수 없습니다: {review_path}")

def load_excel_files(base_path, review_path, sheet_name):
    """엑셀 파일 로드"""
    try:
        df_base = pd.read_excel(base_path)
        print(f"템플릿 파일 로드 성공: {len(df_base)}행, 열: {list(df_base.columns)}")
    except Exception as e:
        raise ValueError(f"템플릿 파일 읽기 실패: {e}")
        
    try:    
        df_review = pd.read_excel(review_path, sheet_name=sheet_name)
        print(f"검토 시트 로드 성공: {len(df_review)}행, 열: {list(df_review.columns)}")
    except Exception as e:
        raise ValueError(f"검토 시트 파일 읽기 실패: {e}")
    
    return df_base, df_review

def validate_columns(df_base, df_review, clause_col, title_col):
    """필수 열이 존재하는지 확인"""
    if clause_col not in df_base.columns:
        raise ValueError(f"템플릿 파일에 항목 열({clause_col})이 없습니다.")
    
    for col_name in [clause_col, title_col]:
        if col_name not in df_review.columns:
            raise ValueError(f"검토 시트에 필수 열을 찾을 수 없습니다: {col_name}")

def validate_and_filter_prompts(prompt_names):
    """프롬프트 검증 및 필터링"""
    # 프롬프트 로드 - 우선순위 정보 포함하여 로드
    prompt_dict = load_prompts_by_type("remark", as_dict=True, include_metadata=True)
    
    # 선택된 프롬프트 필터링
    selected_prompts = {name: data for name, data in prompt_dict.items() 
                      if name in prompt_names}
    
    if not selected_prompts:
        raise ValueError(f"선택한 프롬프트를 찾을 수 없습니다: {prompt_names}")
    
    return selected_prompts

def save_result_file(df):
    """결과 파일 저장"""
    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join("output", f"report_{timestamp}.xlsx")
    df.to_excel(output_path, index=False)
    
    return output_path

# 이전 processor.py에서 사용하던 함수를 여기로 통합
def load_prompt_by_name(name):
    """이름으로 프롬프트 템플릿 불러오기"""
    prompts = load_prompts_by_type("remark", as_dict=True, include_metadata=True)
    if name in prompts:
        return prompts[name].get('template', '')
    return None
