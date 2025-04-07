# 열 이름 키워드 매핑 정의 (확장됨)
COLUMN_KEYWORDS = {
    'clause': ['clause', '항목', '조항', 'id', 'no', '번호', 'item', 'subclause', 'paragraph'],
    'title': ['title', '제목', 'name', '내용', 'description', '항목명', 'requirement', '요구사항'],
    'remark': ['remark', 'comment', '의견', '비고', '결과', '검토의견', '검토결과', 'review', 'note'],
    'status': ['결과', 'status', '상태', '진행상태', 'progress', 'compliance'],
    'details': ['세부', '내용', 'detail', 'description', '설명', 'content'],
    'hint': ['hint', '지침', '가이드', 'guide', '참고', 'reference', 'standard'],
    'standard': ['standard', '규격', '표준', 'regulation', 'iec', 'iso', '기준']
}

def detect_columns(columns: list) -> dict:
    """
    열 이름 자동 감지 함수
    
    Args:
        columns: 열 이름 목록
        
    Returns:
        dict: 감지된 열 매핑 {'clause': '감지된열이름', ...}
    """
    if not columns:
        return {}
        
    result = {}
    
    # 모든 열을 소문자로 변환하여 검사
    lower_columns = [col.lower() if isinstance(col, str) else str(col).lower() for col in columns]
    
    # 각 유형별 키워드 검색
    for col_type, keywords in COLUMN_KEYWORDS.items():
        # 이미 이 유형이 발견되었다면 건너뜀
        if col_type in result:
            continue
            
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # 정확히 일치하는 열 이름 우선 검색
            for idx, col in enumerate(lower_columns):
                if col == keyword_lower and col_type not in result:
                    result[col_type] = columns[idx]
                    break
                    
            # 정확히 일치하는 열을 찾지 못했다면 부분 일치 검색
            if col_type not in result:
                for idx, col in enumerate(lower_columns):
                    if keyword_lower in col and col_type not in result:
                        result[col_type] = columns[idx]
                        break
    
    # 특별한 처리가 필요한 경우
    # 1. 항목 번호 열 (clause) 처리
    if 'clause' not in result:
        for idx, col in enumerate(lower_columns):
            if '번호' in col or 'no.' in col or 'no ' in col:
                result['clause'] = columns[idx]
                break
    
    # 2. 열 제목에 숫자가 포함된 경우 (예: "8.2 안전 기능")
    if 'clause' not in result:
        import re
        for idx, col in enumerate(lower_columns):
            if re.search(r'\d+\.\d+', col):  # 숫자.숫자 패턴 (예: 8.2)
                result['clause'] = columns[idx]
                break

    # 3. 위치 기반 추측 - 일반적으로 처음 몇 개 열이 주요 정보
    if len(columns) >= 3:
        if 'clause' not in result:
            result['clause'] = columns[0]  # 첫 번째 열은 보통 항목 번호
            
        if 'title' not in result and 'clause' in result:
            # 항목 다음 열은 보통 제목
            clause_idx = columns.index(result['clause'])
            if clause_idx + 1 < len(columns):
                result['title'] = columns[clause_idx + 1]
    
    return result

def enhanced_column_detection(df, standard=None):
    """
    규격 정보를 활용한 향상된 열 감지
    
    Args:
        df: DataFrame - 분석할 데이터프레임
        standard: str - 감지된 규격 (있는 경우)
    
    Returns:
        dict: 감지된 열 매핑
    """
    columns = list(df.columns)
    result = detect_columns(columns)
    
    # 규격별 특화 감지 로직
    if standard:
        if standard == "IEC_60204-1":
            # IEC 60204-1 특화 열 감지
            for idx, col in enumerate(columns):
                col_lower = str(col).lower()
                if "안전" in col_lower and "기능" in col_lower:
                    result['safety_function'] = col
                if "위험" in col_lower or "risk" in col_lower:
                    result['risk'] = col
        
        elif standard == "ISO_13849":
            # ISO 13849 특화 열 감지
            for idx, col in enumerate(columns):
                col_lower = str(col).lower()
                if "pl" in col_lower or "성능" in col_lower:
                    result['performance_level'] = col
                if "카테고리" in col_lower or "category" in col_lower:
                    result['category'] = col
    
    return result
