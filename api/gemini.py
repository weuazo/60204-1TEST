# api/gemini.py
import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv
from utils.prompt_loader import load_prompts_by_type
from utils.logger import logger

# 채팅 컨텍스트 모듈 추가
from utils import chat_context

# 환경 변수 로드 (한 번만 실행)
load_dotenv()

# API 키 확인 및 초기화를 위한 함수
def initialize_api():
    """Gemini API 초기화 및 설정 확인"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        error_msg = "API 키가 설정되지 않았습니다. 환경 변수 GEMINI_API_KEY를 설정하세요."
        logger.error(error_msg)
        return False, error_msg
        
    try:
        genai.configure(api_key=api_key)
        return True, "API 초기화 성공"
    except Exception as e:
        error_msg = f"API 초기화 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def get_api_status():
    """API 연결 상태 확인"""
    try:
        # API 키 확인
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return False, "API 키가 설정되지 않았습니다."
            
        # 간단한 API 테스트 (짧은 프롬프트로)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hello")
        
        if response and response.text:
            return True, "API 연결 정상"
        return False, "API 응답이 비정상입니다."
    except Exception as e:
        return False, f"API 연결 오류: {str(e)}"

def call_gemini(user_input):
    """기본 Gemini API 호출 함수"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        error_msg = "API 키가 설정되지 않았습니다. 환경 변수 GEMINI_API_KEY를 설정하세요."
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        genai.configure(api_key=api_key)
        # 최신 모델 사용 (필요에 따라 변경 가능)
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(user_input)
        
        if not response.text:
            logger.warning("API에서 빈 응답을 받았습니다.")
            return "응답이 비어있습니다. 다시 시도해주세요."
        
        return response.text.strip()
    except Exception as e:
        error_msg = f"Gemini API 호출 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
def call_gemini_with_prompts(user_input, prompt_names, standard_info=None, additional_context=None):
    """
    선택된 프롬프트를 모두 반영하여 Gemini 호출
    
    Args:
        user_input: 사용자 입력 텍스트
        prompt_names: 적용할 프롬프트 이름 목록
        standard_info: 규격 정보 (선택적)
        additional_context: 추가 컨텍스트 정보 (선택적)
    """
    # 문자열을 리스트로 변환 (단일 프롬프트 호환성)
    if isinstance(prompt_names, str):
        prompt_names = [prompt_names]
        
    # 프롬프트가 없는 경우 기본 호출
    if not prompt_names:
        return call_gemini_with_context(user_input, additional_context)
    
    # 프롬프트 타입 결정 (채팅인지 보고서 생성인지)
    prompt_type = determine_prompt_type()
    
    # 해당 유형의 프롬프트만 가져오기
    try:
        prompts_data = load_prompts_by_type(prompt_type, as_dict=True, include_metadata=True)
    except Exception as e:
        logger.error(f"프롬프트 로드 오류: {e}")
        prompts_data = {}
    
    # 선택된 프롬프트만 필터링
    selected_prompts = {name: data for name, data in prompts_data.items() 
                        if name in prompt_names}
    
    if not selected_prompts:
        logger.warning(f"선택된 '{prompt_type}' 유형의 프롬프트가 없습니다.")
        return call_gemini_with_context(user_input, additional_context)  # 컨텍스트와 함께 호출
    
    # 우선순위에 따라 정렬
    sorted_prompts = sorted(selected_prompts.items(), 
                           key=lambda x: x[1].get('priority', 999))
    
    # 최종 프롬프트 생성
    system_instructions = []
    for i, (name, data) in enumerate(sorted_prompts):
        instruction = data.get('template', '')
        if instruction:
            # 적용 순서를 포함하여 명시적으로 표시
            system_instructions.append(f"# {name} 지침 (우선순위: {data.get('priority', 999)}, {i+1}번째 적용)\n{instruction}")
            logger.info(f"프롬프트 적용: {name} (우선순위: {data.get('priority', 999)}, {i+1}번째)")
    
    # 규격 정보가 있으면 추가
    if standard_info and isinstance(standard_info, dict) and standard_info.get('title', '') != '미확인 규격':
        std_info_text = f"""
# 규격 정보 
- 규격명: {standard_info.get('title', '미확인 규격')}
- 설명: {standard_info.get('description', '')}
- 적용 범위: {standard_info.get('scope', '')}
- 주요 섹션: {', '.join(standard_info.get('key_sections', []))}

위 규격에 맞춰서 검토 의견을 작성해주세요. 규격의 요구사항을 기반으로 의견을 작성하세요.
"""
        system_instructions.append(std_info_text)
    
    # 채팅 및 파일 컨텍스트 추가
    if prompt_type == "chat":
        try:
            context_str = chat_context.get_context_for_prompt()
            if context_str:
                system_instructions.append(f"# 현재 컨텍스트 정보\n{context_str}")
                
            # 분석 요약 정보 추가
            summary = chat_context.get_context_analysis_summary()
            if summary and summary.get('analysis_available') and any(summary['analysis_available'].values()):
                analysis_text = "# 컨텍스트 분석 정보\n"
                for file_type, has_analysis in summary['analysis_available'].items():
                    if has_analysis and file_type == 'review_sheet':
                        analysis = chat_context._cached_file_analysis.get(file_type, {})
                        if analysis:
                            analysis_text += f"- 검토 시트 항목 수: {analysis.get('clause_count', '알 수 없음')}\n"
                            if analysis.get('has_standard_structure'):
                                analysis_text += "- 표준 구조 (예: 1.2.3 형식)가 감지됨\n"
                system_instructions.append(analysis_text)
        except Exception as e:
            logger.error(f"채팅 컨텍스트 추가 중 오류: {e}")
    
    # 추가 컨텍스트가 있으면 포함
    if additional_context and isinstance(additional_context, dict):
        for key, value in additional_context.items():
            if value:
                system_instructions.append(f"# {key}\n{value}")
    
    # 모든 지침 + 사용자 입력 결합
    combined_prompt = "\n\n".join(system_instructions)
    combined_prompt += f"\n\n# 사용자 입력\n{user_input}"
    
    # 디버그용 로그
    prompt_preview = combined_prompt[:200] + "..." if len(combined_prompt) > 200 else combined_prompt
    logger.debug(f"결합된 프롬프트 ({len(prompt_names)}개): {prompt_preview}")
    
    try:
        # API 호출
        response = call_gemini(combined_prompt)
        
        # 채팅 히스토리에 메시지 추가
        if prompt_type == "chat":
            chat_context.add_chat_message("user", user_input)
            chat_context.add_chat_message("assistant", response)
        
        return response
    except Exception as e:
        logger.error(f"API 호출 중 오류: {e}")
        return f"오류가 발생했습니다: {str(e)}"

def call_gemini_with_context(user_input, context_data=None):
    """
    파일 컨텍스트를 포함한 Gemini API 호출
    
    Args:
        user_input: 사용자 입력 텍스트
        context_data: 추가 컨텍스트 정보
    """
    # 기본 프롬프트 구성
    prompt_parts = ["기술 문서 검토 전문가로서 다음 질문에 답변해주세요."]
    
    try:
        # 채팅 컨텍스트 추가
        context_str = chat_context.get_context_for_prompt()
        if context_str:
            prompt_parts.append(context_str)
        
        # 검토 시트 관련 텍스트 분석 및 추가
        excel_data = chat_context.get_excel_data_for_chat(user_input)
        if excel_data and excel_data.get('found_items'):
            items_text = []
            items_text.append("# 검토 시트에서 발견된 관련 항목")
            
            for idx, item in enumerate(excel_data['found_items']):
                item_desc = [f"## 항목 {idx+1}:"]
                for key, val in item.items():
                    if val:
                        item_desc.append(f"- {key}: {val}")
                items_text.append("\n".join(item_desc))
                
            prompt_parts.append("\n\n".join(items_text))
            
            # 분석 지침 추가
            prompt_parts.append("""
    # 분석 지침
    위 항목들을 참조하여 사용자의 질문에 답변해주세요. 
    항목 번호와 제목을 인용하면서 명확하게 설명하세요.
    특정 항목에 대한 질문이라면 해당 항목의 내용을 중심으로 답변하세요.
    """)
    except Exception as e:
        logger.error(f"컨텍스트 처리 중 오류: {e}")
    
    # 추가 컨텍스트 데이터가 있으면 포함
    if context_data and isinstance(context_data, dict):
        for key, value in context_data.items():
            if value:
                prompt_parts.append(f"# {key}\n{value}")
    
    # 사용자 질문 추가
    prompt_parts.append(f"# 사용자 질문\n{user_input}")
    
    # 최종 프롬프트 결합
    prompt = "\n\n".join(prompt_parts)
    
    # 디버그용 로그
    prompt_preview = prompt[:200] + "..." if len(prompt) > 200 else prompt
    logger.debug(f"컨텍스트 프롬프트: {prompt_preview}")
    
    try:
        # API 호출
        response = call_gemini(prompt)
        
        # 채팅 히스토리에 메시지 추가
        chat_context.add_chat_message("user", user_input)
        chat_context.add_chat_message("assistant", response)
        
        return response
    except Exception as e:
        logger.error(f"API 호출 중 오류: {e}")
        return f"오류가 발생했습니다: {str(e)}"

def determine_prompt_type():
    """현재 호출 컨텍스트에서 프롬프트 타입 결정"""
    import inspect
    stack = inspect.stack()
    for frame in stack:
        if 'handle_chat_input' in frame.function:
            return "chat"
        elif 'handle_generate' in frame.function or 'generate_remarks' in frame.function:
            return "remark"
    
    # 기본값
    return "remark"
