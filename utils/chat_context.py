"""
채팅 및 파일 컨텍스트 관리 모듈
불러온 파일에 대한 정보와 채팅 내용을 저장하고 관리합니다.
"""
import os
import json
import datetime
import pandas as pd
import re
import traceback
from typing import Dict, List, Any, Optional, Tuple, Union

# 전역 상태 변수
_loaded_files: Dict[str, Any] = {}  # 불러온 파일 정보 저장
_chat_history: List[Dict[str, str]] = []  # 채팅 내용 저장
_context_cache: Dict[str, Any] = {}  # 컨텍스트 캐시
_file_dataframes: Dict[str, pd.DataFrame] = {}  # 파일 데이터프레임 캐시
_cached_file_analysis: Dict[str, Any] = {}  # 파일 분석 결과 캐시

# 최대 기록 항목 수
MAX_HISTORY_ITEMS = 50
# 캐시된 행 개수 제한 (메모리 효율성을 위해)
MAX_CACHED_ROWS = 200


def has_any_context() -> bool:
    """
    컨텍스트 정보가 있는지 확인합니다.
    
    Returns:
        bool: 컨텍스트 정보가 있으면 True, 없으면 False
    """
    return bool(_loaded_files) or bool(_chat_history)


def add_loaded_file(file_path: str, file_type: str, columns: Dict[str, str] = None, 
                    sheet_name: str = None, detected_standard: str = None) -> bool:
    """
    불러온 파일 정보를 컨텍스트에 추가
    
    Args:
        file_path: 파일 경로
        file_type: 파일 유형 (review_sheet, output_sheet)
        columns: 인식된 열 정보 (선택적)
        sheet_name: 시트 이름 (선택적)
        detected_standard: 감지된 규격 (선택적)
        
    Returns:
        bool: 성공 여부
    """
    # 파일 존재 확인
    if not file_path or not os.path.exists(file_path):
        print(f"[컨텍스트] 파일이 존재하지 않음: {file_path}")
        return False
    
    file_info = {
        'path': file_path,
        'type': file_type,
        'name': os.path.basename(file_path),
        'loaded_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'columns': columns or {},
        'sheet_name': sheet_name,
        'standard': detected_standard
    }
    
    _loaded_files[file_type] = file_info
    
    # 파일 데이터프레임 캐시 초기화 (새로운 파일이 로드되었으므로)
    if file_type in _file_dataframes:
        del _file_dataframes[file_type]
    
    # 파일 분석 결과 캐시 초기화
    if file_type in _cached_file_analysis:
        del _cached_file_analysis[file_type]
    
    # 데이터프레임 미리 로드 (검토 시트인 경우 우선순위 부여)
    if file_type == "review_sheet":
        try:
            get_file_dataframe(file_type, load_if_needed=True)
            
            # 기본 분석 수행
            analyze_review_sheet(file_type)
        except Exception as e:
            print(f"[컨텍스트] 검토 시트 로드 중 오류: {e}")
    
    # 컨텍스트 캐시 업데이트
    update_context_cache()
    
    print(f"[컨텍스트] 파일 추가됨: {file_path} (유형: {file_type})")
    return True


def add_file_context(file_type: str, file_path: str, **metadata) -> bool:
    """
    파일 컨텍스트 추가 (기존 버전과의 호환성을 위한 래퍼 함수)
    
    Args:
        file_type: 파일 종류 (예: 'source', 'target', 'review', 'template')
        file_path: 파일 경로
        **metadata: 추가 메타데이터 (예: sheet_name, columns, standard 등)
        
    Returns:
        bool: 성공 여부
    """
    return add_loaded_file(
        file_path=file_path,
        file_type=file_type,
        columns=metadata.get('columns'),
        sheet_name=metadata.get('sheet_name'),
        detected_standard=metadata.get('standard')
    )


def get_loaded_files() -> Dict[str, Any]:
    """불러온 파일 정보 반환"""
    return _loaded_files


def get_loaded_file(file_type: str) -> Optional[Dict[str, Any]]:
    """특정 유형의 파일 정보 반환"""
    return _loaded_files.get(file_type)


def get_file_context(file_type: str) -> Optional[Dict[str, Any]]:
    """특정 타입의 파일 컨텍스트 반환 (기존 버전과의 호환성을 위한 래퍼 함수)"""
    return get_loaded_file(file_type)


def get_file_dataframe(file_type: str, load_if_needed: bool = False) -> Optional[pd.DataFrame]:
    """
    파일의 데이터프레임 가져오기
    
    Args:
        file_type: 파일 유형 (review_sheet, output_sheet)
        load_if_needed: 필요한 경우 로드 여부
        
    Returns:
        Optional[pd.DataFrame]: 데이터프레임 또는 None
    """
    # 이미 캐시에 있는 경우 반환
    if file_type in _file_dataframes:
        return _file_dataframes[file_type]
        
    # 캐시에 없고 로드하지 않을 경우 None 반환
    if not load_if_needed:
        return None
        
    # 파일 정보 확인
    file_info = _loaded_files.get(file_type)
    if not file_info:
        return None
        
    # 파일 로드 시도
    try:
        file_path = file_info['path']
        sheet_name = file_info.get('sheet_name')
        
        if file_path.lower().endswith(('.xlsx', '.xls')):
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path)
                
            # 행 수 제한 (메모리 효율성)
            if len(df) > MAX_CACHED_ROWS:
                print(f"[컨텍스트] 행 수 제한 적용: {len(df)}행 -> {MAX_CACHED_ROWS}행")
                df = df.head(MAX_CACHED_ROWS)
                
            # 캐시에 저장
            _file_dataframes[file_type] = df
            return df
            
    except Exception as e:
        print(f"[컨텍스트] 파일 '{file_path}' 데이터프레임 로드 오류: {e}")
        
    return None


def analyze_review_sheet(file_type: str) -> Dict[str, Any]:
    """
    검토 시트 분석 수행
    
    Args:
        file_type: 파일 유형 (주로 review_sheet)
        
    Returns:
        Dict[str, Any]: 분석 결과
    """
    if file_type in _cached_file_analysis:
        return _cached_file_analysis[file_type]
        
    analysis_result = {
        'clause_count': 0,
        'clauses': [],
        'has_standard_structure': False,
        'identified_patterns': {},
        'columns_summary': {}
    }
    
    df = get_file_dataframe(file_type, load_if_needed=True)
    if df is None:
        return analysis_result
        
    file_info = _loaded_files.get(file_type)
    if not file_info:
        return analysis_result
        
    try:
        # 열 정보 가져오기
        columns_info = file_info.get('columns', {})
        clause_col = columns_info.get('clause')
        
        # 기본 항목 수 분석
        if clause_col and clause_col in df.columns:
            # 항목 번호 칼럼 파싱
            clauses = df[clause_col].dropna().astype(str).tolist()
            analysis_result['clause_count'] = len(clauses)
            
            # 대표 항목 샘플 저장 (최대 10개)
            analysis_result['clauses'] = clauses[:10]
            
            # 항목 패턴 감지
            patterns = {
                'numeric': 0,  # 숫자 형식 (예: 1, 2, 3)
                'dotted': 0,   # 점 형식 (예: 1.2.3)
                'mixed': 0     # 혼합 형식
            }
            
            for clause in clauses:
                if re.match(r'^\d+\.\d+(\.\d+)*$', str(clause)):
                    patterns['dotted'] += 1
                elif re.match(r'^\d+$', str(clause)):
                    patterns['numeric'] += 1
                else:
                    patterns['mixed'] += 1
                    
            analysis_result['identified_patterns'] = patterns
            
            # 표준 구조 확인
            if patterns['dotted'] > patterns['numeric'] and patterns['dotted'] > patterns['mixed']:
                analysis_result['has_standard_structure'] = True
                
        # 열 요약 정보
        analysis_result['columns_summary'] = {
            'total': len(df.columns),
            'names': df.columns.tolist(),
            'sample_rows': min(10, len(df))
        }
        
        # 분석 결과 캐시 저장
        _cached_file_analysis[file_type] = analysis_result
        
    except Exception as e:
        print(f"[컨텍스트] 검토 시트 분석 중 오류: {e}")
    
    return analysis_result


def get_context_analysis_summary() -> Dict[str, Any]:
    """
    컨텍스트 분석 요약 정보 반환
    """
    summary = {
        'file_types': list(_loaded_files.keys()),
        'chat_messages': len(_chat_history),
        'analysis_available': {}
    }
    
    for file_type in _loaded_files:
        has_analysis = file_type in _cached_file_analysis
        summary['analysis_available'][file_type] = has_analysis
        
    return summary


def add_chat_message(role: str, content: str) -> None:
    """
    채팅 메시지를 기록에 추가
    
    Args:
        role: 메시지 역할 (user 또는 assistant)
        content: 메시지 내용
    """
    # 기록 크기 제한
    if len(_chat_history) >= MAX_HISTORY_ITEMS:
        _chat_history.pop(0)  # 가장 오래된 항목 제거
    
    message = {
        'role': role,
        'content': content,
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    _chat_history.append(message)
    
    # 컨텍스트 캐시 업데이트
    update_context_cache()


def add_chat_entry(user_input: str, ai_response: str) -> bool:
    """
    채팅 기록에 새 항목 추가 (기존 버전과의 호환성을 위한 래퍼 함수)
    
    Args:
        user_input: 사용자 입력 텍스트
        ai_response: AI 응답 텍스트
        
    Returns:
        bool: 성공 여부
    """
    # 사용자 메시지 추가
    add_chat_message('user', user_input)
    
    # AI 응답 추가
    add_chat_message('assistant', ai_response)
    
    return True


def get_chat_history() -> List[Dict[str, str]]:
    """전체 채팅 기록 반환"""
    return _chat_history


def clear_chat_history() -> bool:
    """
    채팅 기록 초기화
    
    Returns:
        bool: 성공 여부
    """
    global _chat_history
    _chat_history = []
    
    # 컨텍스트 캐시 업데이트
    update_context_cache()
    
    print("[컨텍스트] 채팅 기록이 초기화되었습니다.")
    return True


def clear_file_context(file_type: str = None) -> bool:
    """
    파일 컨텍스트 초기화
    
    Args:
        file_type: 제거할 파일 타입 (None이면 모두 제거)
        
    Returns:
        bool: 성공 여부
    """
    global _loaded_files, _file_dataframes, _cached_file_analysis
    
    if file_type is None:
        _loaded_files = {}
        _file_dataframes = {}
        _cached_file_analysis = {}
        
        # 컨텍스트 캐시 업데이트
        update_context_cache()
        
        print("[컨텍스트] 파일 컨텍스트가 초기화되었습니다.")
        return True
    
    if file_type in _loaded_files:
        del _loaded_files[file_type]
        
        if file_type in _file_dataframes:
            del _file_dataframes[file_type]
            
        if file_type in _cached_file_analysis:
            del _cached_file_analysis[file_type]
            
        # 컨텍스트 캐시 업데이트
        update_context_cache()
        
        print(f"[컨텍스트] 파일 컨텍스트 '{file_type}'이 제거되었습니다.")
        return True
        
    return False


def update_context_cache() -> None:
    """컨텍스트 캐시 업데이트"""
    _context_cache.clear()
    
    # 파일 정보 추가
    _context_cache['loaded_files'] = _loaded_files
    
    # 최근 채팅 내용 추가 (최대 10개)
    _context_cache['recent_chat'] = _chat_history[-10:] if _chat_history else []
    
    # 파일 분석 정보 추가
    _context_cache['file_analysis'] = {k: v for k, v in _cached_file_analysis.items()}


def get_context_for_prompt() -> str:
    """
    AI 프롬프트용 컨텍스트 문자열 생성
    AI에게 제공할 컨텍스트를 포매팅하여 반환합니다.
    """
    context_parts = []
    
    # 파일 정보 포함
    if _loaded_files:
        file_info = []
        
        # 검토시트를 먼저 처리
        review_file = _loaded_files.get('review_sheet')
        if review_file:
            file_desc = build_file_context_desc('review_sheet', review_file)
            file_info.append(file_desc)
            
            # 검토시트 분석 결과 추가
            analysis = _cached_file_analysis.get('review_sheet')
            if analysis:
                analysis_desc = [
                    "## 검토시트 분석",
                    f"- 항목 수: {analysis['clause_count']}개",
                ]
                
                if analysis['clauses']:
                    sample_clauses = ', '.join(str(c) for c in analysis['clauses'][:5])
                    analysis_desc.append(f"- 항목 샘플: {sample_clauses}")
                
                if analysis['has_standard_structure']:
                    analysis_desc.append("- 표준 항목 구조가 감지됨 (예: 1.2.3 형식)")
                    
                file_info.append("\n".join(analysis_desc))
        
        # 그 외 파일들 처리
        for file_type, details in _loaded_files.items():
            if file_type != 'review_sheet':
                file_desc = build_file_context_desc(file_type, details)
                file_info.append(file_desc)
                
        if file_info:
            context_parts.append("# 불러온 파일 정보\n" + "\n\n".join(file_info))
    
    # 최근 채팅 내용 추가 (최대 5개, 너무 길어지지 않도록)
    if _chat_history:
        recent_chats = _chat_history[-5:]
        chat_texts = []
        
        for msg in recent_chats:
            if 'role' in msg and msg['role'] == 'user' and 'content' in msg:
                content = msg['content']
                chat_texts.append(f"사용자: {content[:100]}" + ("..." if len(content) > 100 else ""))
            elif 'user' in msg:  # 이전 형식 지원
                content = msg['user']
                chat_texts.append(f"사용자: {content[:100]}" + ("..." if len(content) > 100 else ""))
            elif 'role' in msg and msg['role'] == 'assistant' and 'content' in msg:
                content = msg['content']
                chat_texts.append(f"AI: {content[:100]}" + ("..." if len(content) > 100 else ""))
            elif 'bot' in msg:  # 이전 형식 지원
                content = msg['bot']
                chat_texts.append(f"AI: {content[:100]}" + ("..." if len(content) > 100 else ""))
                
        if chat_texts:
            context_parts.append("# 최근 대화 내용\n" + "\n".join(chat_texts))
    
    return "\n\n".join(context_parts)


def build_file_context_desc(file_type: str, details: Dict[str, Any]) -> str:
    """파일 컨텍스트 설명 생성 헬퍼 함수"""
    file_desc = [f"## {file_type.upper()}: {details.get('name', '알 수 없는 파일')}"]
    
    if 'sheet_name' in details and details['sheet_name']:
        file_desc.append(f"- 시트: {details['sheet_name']}")
        
    if 'standard' in details and details['standard']:
        file_desc.append(f"- 규격: {details['standard']}")
        
    if 'columns' in details and details['columns']:
        cols_list = []
        for k, v in details['columns'].items():
            cols_list.append(f"{k}열: {v}")
        if cols_list:
            file_desc.append(f"- 인식된 열: {', '.join(cols_list)}")
    
    return "\n".join(file_desc)


def get_excel_data_for_chat(query: str) -> Optional[Dict[str, Any]]:
    """
    채팅을 위한 엑셀 데이터 추출
    쿼리와 관련된 검토시트 데이터를 추출하여 반환합니다.
    
    Args:
        query: 사용자 쿼리
        
    Returns:
        Optional[Dict[str, Any]]: 추출된 데이터 또는 None
    """
    # 검토 시트 먼저 확인
    review_df = get_file_dataframe('review_sheet', load_if_needed=True)
    
    # 검토 시트가 없으면 소스 시트 확인
    if review_df is None:
        review_df = get_file_dataframe('source', load_if_needed=True)
    
    if review_df is None:
        return None
    
    # 열 정보 확인
    file_type = 'review_sheet' if 'review_sheet' in _loaded_files else 'source'
    file_info = _loaded_files.get(file_type, {})
    columns_info = file_info.get('columns', {})
    clause_col = columns_info.get('clause')
    title_col = columns_info.get('title')
    
    # 열 정보가 없으면 자동 감지 시도
    if not clause_col or clause_col not in review_df.columns:
        try:
            from utils.column_detector import detect_columns
            detected_cols = detect_columns(review_df.columns)
            clause_col = detected_cols.get('clause')
            if not title_col:
                title_col = detected_cols.get('title')
        except Exception:
            pass
    
    if not clause_col or clause_col not in review_df.columns:
        return None
    
    try:
        result = {
            'query': query,
            'found_items': [],
            'sample_data': review_df.head(3).to_dict(orient='records')
        }
        
        # 쿼리에서 패턴 검색 (예: "1.2.3")
        clause_patterns = re.findall(r'\d+\.\d+(\.\d+)*', query)
        
        # 패턴이 있을 경우 일치하는 항목 검색 (패턴 기반 매칭)
        if clause_patterns:
            for pattern in clause_patterns:
                matches = review_df[review_df[clause_col].astype(str).str.contains(pattern, regex=False)]
                
                for _, row in matches.iterrows():
                    item = {'clause': str(row[clause_col])}
                    
                    if title_col and title_col in row:
                        item['title'] = str(row[title_col])
                        
                    # 나머지 열도 추가
                    for col in row.index:
                        if col != clause_col and col != title_col and pd.notna(row[col]):
                            item[col] = str(row[col])
                            
                    result['found_items'].append(item)
                    
                    # 최대 5개까지만
                    if len(result['found_items']) >= 5:
                        break
                        
                if result['found_items']:
                    break
        
        # 키워드 기반 매칭 (패턴이 없거나 패턴으로 찾지 못한 경우)
        if not result['found_items']:
            # 검색어 토큰화
            query_tokens = set(query.lower().split())
            
            for idx, row in review_df.iterrows():
                relevance_score = 0
                
                # 항목 번호 검색
                clause_val = str(row.get(clause_col, "")).lower()
                if clause_val:
                    # 정확히 일치하는지 확인
                    if clause_val in query.lower():
                        relevance_score += 10
                    # 부분 일치 확인
                    elif any(token in clause_val or clause_val in token for token in query_tokens):
                        relevance_score += 5
                
                # 제목 검색
                title_val = ""
                if title_col and title_col in row:
                    title_val = str(row.get(title_col, "")).lower()
                    
                    # 제목에 검색어가 포함되는지 확인
                    if title_val:
                        # 정확한 문구 일치
                        if title_val in query.lower():
                            relevance_score += 8
                        # 단어 일치 개수
                        title_tokens = set(title_val.split())
                        common_tokens = query_tokens.intersection(title_tokens)
                        if common_tokens:
                            relevance_score += len(common_tokens) * 2
                
                # 관련성이 있으면 결과에 추가
                if relevance_score >= 5:
                    item_data = {
                        'clause': str(row.get(clause_col, "")),
                        'relevance': relevance_score
                    }
                    
                    # 제목이 있으면 추가
                    if title_col and title_col in row:
                        item_data['title'] = str(row.get(title_col, ""))
                    
                    # 기타 유용한 열 추가
                    for col in row.index:
                        col_lower = str(col).lower()
                        if col != clause_col and col != title_col:
                            if ('remark' in col_lower or 
                                'note' in col_lower or 
                                'desc' in col_lower or
                                'review' in col_lower or
                                'comment' in col_lower):
                                value = row.get(col)
                                if pd.notna(value) and value:
                                    item_data[col] = str(value)
                    
                    result['found_items'].append(item_data)
                    
                    # 최대 10개까지만
                    if len(result['found_items']) >= 10:
                        break
            
            # 관련성에 따라 결과 정렬
            if result['found_items']:
                result['found_items'] = sorted(result['found_items'], 
                                            key=lambda x: x['relevance'], 
                                            reverse=True)
        
        return result if result['found_items'] or result['sample_data'] else None
    
    except Exception as e:
        print(f"[컨텍스트] 엑셀 데이터 추출 중 오류: {e}")
        if os.getenv('DEBUG'):
            traceback.print_exc()
        return None


def export_context_to_json(file_path: str) -> bool:
    """
    현재 컨텍스트를 JSON 파일로 내보내기
    
    Args:
        file_path: 저장할 파일 경로
        
    Returns:
        bool: 성공 여부
    """
    try:
        export_data = {
            'loaded_files': _loaded_files,
            'chat_history': _chat_history,
            'file_analysis': {k: v for k, v in _cached_file_analysis.items()},
            'exported_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'version': "1.0"
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
            
        print(f"[컨텍스트] 성공적으로 내보냄: {file_path}")
        return True
    except Exception as e:
        print(f"[컨텍스트] 내보내기 오류: {e}")
        return False


def import_context_from_json(file_path: str) -> bool:
    """
    JSON 파일에서 컨텍스트 가져오기
    
    Args:
        file_path: 불러올 파일 경로
        
    Returns:
        bool: 성공 여부
    """
    global _loaded_files, _chat_history, _cached_file_analysis
    
    try:
        if not os.path.exists(file_path):
            print(f"[컨텍스트] 파일이 존재하지 않음: {file_path}")
            return False
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if 'loaded_files' in data:
            _loaded_files = data['loaded_files']
            
        if 'chat_history' in data:
            _chat_history = data['chat_history']
        elif 'files' in data and 'chat_history' in data:
            # 이전 버전 형식 지원
            _loaded_files = data['files']
            _chat_history = data['chat_history']
            
        if 'file_analysis' in data:
            _cached_file_analysis = data['file_analysis']
            
        # 데이터프레임 캐시 초기화 (파일 경로가 달라질 수 있음)
        _file_dataframes.clear()
        
        # 캐시 업데이트
        update_context_cache()
        
        print(f"[컨텍스트] 성공적으로 가져옴: {file_path}")
        return True
    except Exception as e:
        print(f"[컨텍스트] 가져오기 오류: {e}")
        return False


def get_context_summary() -> Dict[str, Any]:
    """
    컨텍스트 요약 정보 반환
    챗 UI에서 현재 로드된 컨텍스트의 요약 정보를 표시하기 위한 함수
    
    Returns:
        Dict[str, Any]: 컨텍스트 요약 정보
    """
    summary = {}
    
    # 각 파일 유형별 요약 정보 구성
    for file_type, details in _loaded_files.items():
        file_info = {
            'loaded': True,
            'description': get_file_type_description(file_type),
            'file_info': {
                '파일명': details.get('name', '알 수 없음'),
            }
        }
        
        # 시트 정보가 있으면 추가
        if details.get('sheet_name'):
            file_info['file_info']['시트'] = details['sheet_name']
            
        # 규격 정보가 있으면 추가
        if details.get('standard'):
            file_info['file_info']['규격'] = details['standard']
            
        # 열 정보가 있으면 추가
        if details.get('columns'):
            columns_str = ', '.join([f"{k}: {v}" for k, v in details['columns'].items()])
            file_info['file_info']['열 정보'] = columns_str
            
        # 분석 정보가 있으면 추가
        if file_type in _cached_file_analysis:
            analysis = _cached_file_analysis[file_type]
            
            # 항목 수 추가
            if 'clause_count' in analysis and analysis['clause_count'] > 0:
                file_info['content_summary'] = f"총 {analysis['clause_count']}개의 항목이 있습니다."
                
                # 항목 샘플이 있으면 추가
                if 'clauses' in analysis and analysis['clauses']:
                    samples = ', '.join(str(c) for c in analysis['clauses'][:3])
                    file_info['content_summary'] += f" 예시 항목: {samples}..."
            
        summary[file_type] = file_info
        
    return summary


def get_file_type_description(file_type: str) -> str:
    """
    파일 유형에 대한 사용자 친화적인 설명 반환
    
    Args:
        file_type: 파일 유형 키
        
    Returns:
        str: 사용자 친화적인 설명
    """
    descriptions = {
        'review_sheet': '검토 시트',
        'source': '소스 문서',
        'target': '결과 문서',
        'base_template': '기본 템플릿',
        'report': '보고서',
        'pdf_document': 'PDF 문서',
    }
    
    return descriptions.get(file_type, file_type)


def get_chat_context_info() -> Dict[str, Any]:
    """
    채팅 컨텍스트 정보 반환
    채팅 UI에서 현재 상태를 표시하기 위한 간소화된 정보
    
    Returns:
        Dict[str, Any]: 컨텍스트 정보
    """
    return {
        'files': list(_loaded_files.keys()),
        'messages': len(_chat_history),
        'has_chat_history': len(_chat_history) > 0,
        'has_files': len(_loaded_files) > 0
    }