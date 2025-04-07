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
                          matching_mode="basic", standard_id=None, cancel_var=None):
    """
    다양한 형식의 문서를 처리하여 보고서 생성
    
    Args:
        source_path: 소스 문서 경로 (검토 시트)
        target_path: 대상 문서 경로 (템플릿)
        source_config: 소스 문서 설정 (예: 시트, 열, 등)
        target_config: 대상 문서 설정 (예: 시트, 열, 등)
        prompt_names: 사용할 프롬프트 이름 목록
        matching_mode: 매칭 모드 ("basic" 또는 "ai")
        standard_id: 규격 ID (None이면 자동 감지)
        cancel_var: 취소 상태를 추적하는 딕셔너리 {'cancelled': bool}
    
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
        raise ValueError(f"문서 파싱 오류: {e}")
    
    # standard_id가 None이면 자동 감지
    if standard_id is None:
        try:
            standard_id = detect_standard_from_file(source_path, source_sheet)
        except Exception as e:
            print(f"규격 자동 감지 중 오류: {e}")
            standard_id = "UNKNOWN"
    
    # 규격 정보 가져오기
    standard_info = get_standard_info(standard_id)
    print(f"적용 규격: {standard_info['title']}")
    
    # 데이터프레임 가져오기
    try:
        if hasattr(source_parser, 'get_dataframe'):
            df_source = source_parser.get_dataframe()
        else:
            raise ValueError("소스 파서가 데이터프레임 형식을 지원하지 않습니다.")
        
        if hasattr(target_parser, 'get_dataframe'):
            df_target = target_parser.get_dataframe()
        else:
            raise ValueError("대상 파서가 데이터프레임 형식을 지원하지 않습니다.")
            
    except Exception as e:
        raise ValueError(f"데이터프레임 변환 오류: {e}")
    
    # 열 검증
    if source_clause_col not in df_source.columns or source_title_col not in df_source.columns:
        raise ValueError(f"소스 문서에 필요한 열이 없습니다: {source_clause_col}, {source_title_col}")
    
    if target_clause_col not in df_target.columns:
        raise ValueError(f"대상 문서에 필요한 열이 없습니다: {target_clause_col}")
    
    # 출력 열이 없으면 생성
    if target_output_col not in df_target.columns:
        df_target[target_output_col] = ""
        print(f"출력 열 '{target_output_col}'이 대상에 없어 새로 생성했습니다.")
    
    # 매처 생성
    matcher = create_matcher(matching_mode)
    
    # 문서 매칭
    print(f"문서 매칭 중... 모드: {matching_mode}")
    mappings = matcher.match_documents(
        df_source, df_target, 
        source_col=source_clause_col, 
        target_col=target_clause_col
    )
    
    print(f"매칭 결과: {len(mappings)}개 항목 매칭됨")
    
    # AI 매칭인 경우 사용량 보고
    if matching_mode == "ai" and hasattr(matcher, 'get_api_usage'):
        usage = matcher.get_api_usage()
        print(f"매칭 API 사용: {usage['calls']}번 호출, 약 {usage['tokens']}개 토큰")
    
    # 프롬프트 검증 및 필터링
    prompts_data = load_prompts_by_type("remark", as_dict=True, include_metadata=True)
    selected_prompts = [name for name in prompt_names if name in prompts_data]
    
    if not selected_prompts:
        raise ValueError("선택한 프롬프트가 없습니다.")
    
    # 매핑된 항목 처리
    processed = 0
    successful = 0
    api_calls = 0
    estimated_tokens = 0
    
    def process_item(source_idx, target_idx, confidence, df_source, df_target, source_clause_col, source_title_col, target_output_col, standard_id, selected_prompts):
        """개별 항목 처리 함수"""
        nonlocal api_calls, estimated_tokens  # 외부 변수 참조 추가
        
        clause = str(df_source.loc[source_idx, source_clause_col]).strip()
        title = str(df_source.loc[source_idx, source_title_col]).strip()
        
        context = build_context(df_source.loc[source_idx], df_source.columns, standard_id)
        
        input_text = (
            f"항목: {clause}, 제목: {title}\n\n"
            f"규격: {standard_info['title']}\n\n"
            f"관련 정보:\n{context}\n\n"
            f"위 항목에 대한 검토 의견을 작성해주세요."
        )
        
        reply = call_gemini_with_prompts(input_text, selected_prompts, standard_info=standard_info)
        
        # API 호출 카운팅
        api_calls += 1
        estimated_tokens += len(input_text.split()) + len(reply.split()) * 1.5
        
        return reply
    
    # 병렬 처리 도입:
    max_workers = min(10, len(mappings))  # 최대 10개 항목을 동시에 처리
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        submitted_count = 0
        
        for source_idx, target_idx, confidence in mappings:
            # 취소 확인 (5개 항목마다 한 번씩)
            if cancel_var and submitted_count % 5 == 0 and cancel_var.get('cancelled', False):
                print("사용자에 의해 작업 취소됨")
                break
                
            # 각 항목을 병렬로 처리
            future = executor.submit(
                process_item, 
                source_idx, target_idx, confidence, 
                df_source, df_target, source_clause_col, source_title_col, target_output_col,
                standard_id, selected_prompts
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
                print(f"항목 {clause_val} 처리 중 오류: {e}")
                df_target.loc[target_idx, target_output_col] = f"[오류] {str(e)}"
                
            processed += 1
            if processed % 5 == 0 or processed == len(mappings):
                print(f"처리 중: {processed}/{len(mappings)} ({int(processed/len(mappings)*100)}%)")
    
    # 결과 저장 및 경로 반환
    result_path = save_result_file(df_target, target_path)
    
    # 사용량 보고
    print(f"API 사용: {api_calls}번 호출, 약 {estimated_tokens}개 토큰")
    print(f"처리 완료: {successful}/{processed} 항목 성공")
    
    return result_path

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
    
    return "\n\n".join(context_parts)

def save_result_file(df, original_path):
    """결과 파일 저장"""
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

