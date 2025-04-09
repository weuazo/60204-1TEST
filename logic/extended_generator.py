import os
import pandas as pd
from datetime import datetime
from parsers import get_parser_for_file
from matcher import create_matcher
from api.gemini import call_gemini_with_prompts
from utils.prompt_loader import load_prompts_by_type
from utils.standard_detector import detect_standard_from_file, get_standard_info
from concurrent.futures import ThreadPoolExecutor, as_completed

def generate_from_documents(source_path, target_path, source_config, target_config, prompt_names,
                          matching_mode="basic", standard_id=None, cancel_var=None, chat_history=None):
    """
    다양한 형식의 문서를 처리하여 확장 보고서 생성
    
    Args:
        source_path: 소스 문서 경로 (검토 시트)
        target_path: 대상 문서 경로 (템플릿)
        source_config: 소스 문서 설정 (예: 시트, 열, 등)
        target_config: 대상 문서 설정 (예: 시트, 열, 등)
        prompt_names: 사용할 프롬프트 이름 목록
        matching_mode: 매칭 모드 ("basic" 또는 "ai")
        standard_id: 규격 ID (None이면 자동 감지)
        cancel_var: 취소 상태를 추적하는 딕셔너리 {'cancelled': bool}
        chat_history: AI 채팅 히스토리
    
    Returns:
        결과 파일 경로
    """
    # 설정에서 필요한 값 추출
    source_sheet = source_config.get("sheet", 0)
    source_clause_col = source_config.get("clause_col")
    source_title_col = source_config.get("title_col")
    
    target_sheet = target_config.get("sheet", 0)
    target_clause_col = target_config.get("clause_col")
    target_output_col = target_config.get("output_col")
    
    # 필수 입력 확인
    if not source_clause_col or not source_title_col:
        raise ValueError("소스 문서의 항목 열과 제목 열이 필요합니다")
    
    if not target_clause_col or not target_output_col:
        raise ValueError("대상 문서의 항목 열과 결과 저장 열이 필요합니다")
    
    # 파서 생성 및 문서 파싱
    try:
        source_parser = get_parser_for_file(source_path)
        source_parser.parse(source_path, sheet_name=source_sheet)
        
        target_parser = get_parser_for_file(target_path)
        target_parser.parse(target_path, sheet_name=target_sheet)
        
        # 토큰 사용량 추정 및 보고
        source_tokens = source_parser.estimate_tokens()
        target_tokens = target_parser.estimate_tokens()
        print(f"문서 토큰 추정: 소스={source_tokens}, 대상={target_tokens}")
        
    except Exception as e:
        raise ValueError(f"문서 파싱 오류: {str(e)}")
    
    # standard_id가 None이면 자동 감지
    if standard_id is None:
        try:
            standard_id = detect_standard_from_file(source_path, source_sheet)
        except Exception as e:
            print(f"규격 자동 감지 중 오류: {str(e)}")
            standard_id = "UNKNOWN"
    
    # 규격 정보 가져오기
    standard_info = get_standard_info(standard_id)
    print(f"적용 규격: {standard_info['title']}")
    
    # 데이터프레임 가져오기
    try:
        if hasattr(source_parser, 'get_dataframe'):
            df_source = source_parser.get_dataframe()
        else:
            raise ValueError("소스 파서가 데이터프레임 형식을 지원하지 않습니다")
        
        if hasattr(target_parser, 'get_dataframe'):
            df_target = target_parser.get_dataframe()
        else:
            raise ValueError("대상 파서가 데이터프레임 형식을 지원하지 않습니다")
            
    except Exception as e:
        raise ValueError(f"데이터프레임 변환 오류: {str(e)}")
    
    # 열 검증
    if source_clause_col not in df_source.columns or source_title_col not in df_source.columns:
        raise ValueError(f"소스 문서에 필요한 열이 없습니다: {source_clause_col}, {source_title_col}")
    
    if target_clause_col not in df_target.columns:
        raise ValueError(f"대상 문서에 필요한 열이 없습니다: {target_clause_col}")
    
    # 출력 열이 없으면 생성
    if target_output_col not in df_target.columns:
        df_target[target_output_col] = ""
        print(f"출력 열 '{target_output_col}'이 대상에 없어 새로 생성했습니다")
    
    # 채팅 히스토리 처리
    chat_context = None
    if chat_history and len(chat_history) > 0:
        chat_context = build_chat_context(chat_history)
        print(f"AI 채팅 내용 활용: {len(chat_history)}개 대화 내역")
    
    # 매처 생성
    try:
        matcher = create_matcher(matching_mode)
    except ValueError:
        print(f"경고: '{matching_mode}' 매칭 모드가 유효하지 않아 기본 매처를 사용합니다")
        matching_mode = "basic"
        matcher = create_matcher("basic")
    
    # 문서 매칭
    try:
        print(f"문서 매칭 중... 모드: {matching_mode}")
        mappings = matcher.match_documents(
            df_source, df_target, 
            source_col=source_clause_col, 
            target_col=target_clause_col
        )
        
        if not mappings:
            print("경고: 매칭된 항목이 없습니다")
            
        print(f"매칭 결과: {len(mappings)}개 항목 매칭됨")
        
        # AI 매칭인 경우 사용량 보고
        if matching_mode == "ai" and hasattr(matcher, 'get_api_usage'):
            usage = matcher.get_api_usage()
            print(f"매칭 API 사용: {usage['calls']}번 호출, 약 {usage['tokens']}개 토큰")
    except Exception as e:
        raise ValueError(f"문서 매칭 중 오류: {str(e)}")
    
    # 프롬프트 검증 및 필터링
    prompts_data = load_prompts_by_type("remark", as_dict=True, include_metadata=True)
    selected_prompts = [name for name in prompt_names if name in prompts_data]
    
    if not selected_prompts:
        raise ValueError("선택한 프롬프트가 없거나 모두 유효하지 않습니다")
    
    # 매핑된 항목 처리
    processed = 0
    successful = 0
    api_calls = 0
    estimated_tokens = 0
    
    def process_item(source_idx, target_idx, confidence, df_source, df_target, source_clause_col, source_title_col, target_output_col, standard_id, selected_prompts, chat_context):
        """개별 항목 처리 함수"""
        nonlocal api_calls, estimated_tokens
        
        clause = str(df_source.loc[source_idx, source_clause_col]).strip()
        title = str(df_source.loc[source_idx, source_title_col]).strip()
        
        # 항목 관련 컨텍스트 구성
        item_context = build_context(df_source.loc[source_idx], df_source.columns, standard_id)
        
        input_text = (
            f"항목: {clause}, 제목: {title}\n\n"
            f"규격: {standard_info['title']}\n\n"
            f"관련 정보:\n{item_context}\n\n"
        )
        
        # 채팅 내용 컨텍스트 추가
        if chat_context:
            # 항목 번호와 관련된 대화만 필터링
            relevant_chat = find_relevant_chat(chat_context, clause, title)
            if relevant_chat:
                input_text += f"\n\n채팅 내용에서 참조할 정보:\n{relevant_chat}\n\n"
        
        input_text += "위 항목에 대한 검토 의견을 작성해주세요."
        
        # Gemini 호출
        reply = call_gemini_with_prompts(input_text, selected_prompts, standard_info=standard_info)
        
        # API 호출 카운팅
        api_calls += 1
        estimated_tokens += len(input_text.split()) + len(reply.split()) * 1.5
        
        return reply
    
    # 병렬 처리 설정
    max_workers = min(10, len(mappings))  # 최대 10개 항목을 동시에 처리
    if max_workers == 0:
        return save_result_file(df_target, target_path)  # 매칭 결과가 없으면 바로 저장
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        submitted_count = 0
        
        # 작업 제출
        for source_idx, target_idx, confidence in mappings:
            # 취소 확인
            if cancel_var and cancel_var.get('cancelled', False):
                print("사용자에 의해 작업 취소됨")
                break
                
            # 각 항목을 병렬로 처리
            future = executor.submit(
                process_item, 
                source_idx, target_idx, confidence, 
                df_source, df_target, source_clause_col, source_title_col, target_output_col,
                standard_id, selected_prompts, chat_context
            )
            futures[future] = (source_idx, target_idx)
            submitted_count += 1
        
        # 완료된 작업 결과 처리
        for i, future in enumerate(as_completed(futures)):
            # 주기적으로 취소 여부 확인
            if cancel_var and cancel_var.get('cancelled', False) and i % 5 == 0:
                print("사용자에 의해 작업 취소됨 - 남은 작업 건너뜀")
                break
                
            source_idx, target_idx = futures[future]
            try:
                result = future.result()
                df_target.loc[target_idx, target_output_col] = result
                successful += 1
            except Exception as e:
                clause_val = df_source.loc[source_idx, source_clause_col]
                print(f"항목 {clause_val} 처리 중 오류: {str(e)}")
                df_target.loc[target_idx, target_output_col] = f"[오류] {str(e)}"
                
            processed += 1
            if processed % 5 == 0 or processed == len(mappings):
                percent_done = int(processed/len(mappings)*100)
                print(f"처리 중: {processed}/{len(mappings)} ({percent_done}%)")
    
    # 결과 저장 및 경로 반환
    result_path = save_result_file(df_target, target_path)
    
    # 사용량 보고
    print(f"API 사용: {api_calls}번 호출, 약 {estimated_tokens}개 토큰")
    print(f"처리 완료: {successful}/{processed} 항목 성공")
    
    return result_path

def build_chat_context(chat_history):
    """
    채팅 히스토리에서 컨텍스트 구성
    
    Args:
        chat_history: 채팅 기록 리스트
        
    Returns:
        str or None: 포맷팅된 채팅 컨텍스트 문자열 또는 None
    """
    if not chat_history:
        return None
        
    chat_context = []
    
    # 대화 내용 포맷팅 (신규 형식과 기존 형식 모두 지원)
    for entry in chat_history:
        # 신규 형식 지원 (role, content)
        if 'role' in entry and 'content' in entry:
            if entry['role'] == 'user':
                chat_context.append(f"사용자: {entry['content']}")
            elif entry['role'] == 'assistant':
                chat_context.append(f"AI: {entry['content']}")
        # 기존 형식 지원 (user, bot)
        elif 'user' in entry and entry['user'] and 'bot' in entry and 'bot':
            chat_context.append(f"사용자: {entry['user']}")
            chat_context.append(f"AI: {entry['bot']}")
            
    return "\n".join(chat_context) if chat_context else None

def find_relevant_chat(chat_context, clause, title):
    """
    항목 번호나 제목과 관련된 채팅 내용 찾기
    
    Args:
        chat_context: 채팅 컨텍스트 문자열
        clause: 항목 번호
        title: 항목 제목
        
    Returns:
        str or None: 관련된 채팅 내용 또는 None
    """
    if not chat_context:
        return None
        
    # 검색어 준비
    clause_clean = str(clause).strip().lower()
    title_clean = str(title).strip().lower()
    
    # 검색어에서 핵심 키워드 추출
    clause_keywords = set(clause_clean.split())
    
    # 제목에서 불용어 제거 및 중요 키워드 추출
    stop_words = {'a', 'an', 'the', 'and', 'or', 'of', 'to', 'in', 'for', 'with', 'by', 'as', '및', '등', '를', '을', '이', '가'}
    title_keywords = set([word for word in title_clean.split() if len(word) > 1 and word not in stop_words])
    
    # 라인 단위로 분리
    lines = chat_context.split('\n')
    relevant_sections = []
    current_section = []
    in_relevant_section = False
    relevance_score = 0
    
    for line in lines:
        line_lower = line.lower()
        
        # 새로운 대화 시작인지 확인
        is_new_user_message = line.startswith("사용자:")
        
        if is_new_user_message and current_section:
            # 이전 섹션이 관련 있다면 저장
            if in_relevant_section:
                relevant_sections.append({
                    'text': "\n".join(current_section),
                    'score': relevance_score
                })
            # 새 섹션 시작
            current_section = []
            in_relevant_section = False
            relevance_score = 0
        
        # 현재 라인 추가
        current_section.append(line)
        
        # 관련성 점수 계산
        score = 0
        
        # 1. 정확한 항목 번호 매칭 (가장 높은 점수)
        if clause_clean in line_lower:
            score += 10
        
        # 2. 제목 완전 포함 (두 번째로 높은 점수)
        if title_clean in line_lower:
            score += 8
        
        # 3. 항목 번호 키워드 매칭 (중간 점수)
        clause_match_count = sum(1 for k in clause_keywords if k in line_lower)
        if clause_match_count > 0:
            score += clause_match_count * 2
        
        # 4. 제목 키워드 매칭 (낮은 점수)
        title_match_count = sum(1 for k in title_keywords if k in line_lower)
        if title_match_count > 0:
            score += title_match_count
        
        # 관련성 임계값 이상이면 관련 섹션으로 표시
        if score >= 3:
            in_relevant_section = True
            relevance_score = max(relevance_score, score)  # 섹션 내 최고 점수 저장
    
    # 마지막 섹션 처리
    if in_relevant_section and current_section:
        relevant_sections.append({
            'text': "\n".join(current_section),
            'score': relevance_score
        })
    
    # 관련성 점수로 정렬
    relevant_sections.sort(key=lambda x: x['score'], reverse=True)
    
    # 상위 2개 섹션만 선택 (너무 많은 내용은 컨텍스트 윈도우에 포함시키지 않도록)
    top_sections = [section['text'] for section in relevant_sections[:2]]
    
    # 결과 결합
    if top_sections:
        result = "\n\n".join(top_sections)
        # 토큰 제한을 고려한 길이 제한 (약 500단어)
        if len(result) > 2500:
            words = result.split()
            result = " ".join(words[:500]) + "...(이하 생략)..."
        return result
        
    return None

def build_context(row, columns, standard):
    """행 데이터에서 AI에게 제공할 컨텍스트 구성"""
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
    
    return "\n\n".join(context_parts) if context_parts else "정보 없음"

def save_result_file(df, original_path):
    """결과 파일 저장"""
    try:
        os.makedirs("output", exist_ok=True)
        filename = os.path.basename(original_path)
        name, ext = os.path.splitext(filename)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 파일 형식에 맞게 저장
        if ext.lower() in ['.xlsx', '.xls']:
            output_path = os.path.join("output", f"{name}_result_{timestamp}{ext}")
            df.to_excel(output_path, index=False)
        else:
            # 기본적으로 엑셀로 저장
            output_path = os.path.join("output", f"{name}_result_{timestamp}.xlsx")
            df.to_excel(output_path, index=False)
        
        return output_path
    except Exception as e:
        print(f"결과 파일 저장 중 오류: {str(e)}")
        # 실패 시 임시 파일로 저장 시도
        try:
            emergency_path = os.path.join("output", f"emergency_save_{timestamp}.xlsx")
            df.to_excel(emergency_path, index=False)
            return emergency_path
        except:
            raise ValueError("결과 파일을 저장할 수 없습니다. 디스크 공간이 충분한지 확인하세요.")

