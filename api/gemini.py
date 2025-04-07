# api/gemini.py
import os
import google.generativeai as genai
from dotenv import load_dotenv
from utils.prompt_loader import load_prompts_by_type

load_dotenv()

def call_gemini(user_input):
    """기본 Gemini API 호출 함수"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API 키가 설정되지 않았습니다. .env 파일에 GEMINI_API_KEY를 추가하세요.")

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(user_input)
        if not response.text:
            return "응답이 비어있습니다. 다시 시도해주세요."
        return response.text.strip()
    except Exception as e:
        print(f"API 오류: {str(e)}")
        raise ValueError(f"Gemini API 호출 중 오류가 발생했습니다: {str(e)}")
        
def call_gemini_with_prompts(user_input, prompt_names, standard_info=None):
    """
    선택된 프롬프트를 모두 반영하여 Gemini 호출
    
    Args:
        user_input: 사용자 입력 텍스트
        prompt_names: 적용할 프롬프트 이름 목록
        standard_info: 규격 정보 (선택적)
    """
    # 프롬프트가 없는 경우 기본 호출
    if not prompt_names:
        return call_gemini(user_input)
    
    # 프롬프트 타입 결정 (채팅인지 보고서 생성인지)
    prompt_type = determine_prompt_type()
    
    # 해당 유형의 프롬프트만 가져오기
    prompts_data = load_prompts_by_type(prompt_type, as_dict=True, include_metadata=True)
    
    # 선택된 프롬프트만 필터링
    selected_prompts = {name: data for name, data in prompts_data.items() 
                        if name in prompt_names}
    
    if not selected_prompts:
        print(f"선택된 '{prompt_type}' 유형의 프롬프트가 없습니다.")
        return call_gemini(user_input)  # 기본 호출로 대체
    
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
            print(f"프롬프트 적용: {name} (우선순위: {data.get('priority', 999)}, {i+1}번째)")
    
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
    
    # 모든 지침 + 사용자 입력 결합
    combined_prompt = "\n\n".join(system_instructions)
    combined_prompt += f"\n\n# 사용자 입력\n{user_input}"
    
    # 디버그용 로그
    prompt_preview = combined_prompt[:200] + "..." if len(combined_prompt) > 200 else combined_prompt
    print(f"[DEBUG] 결합된 프롬프트 ({len(prompt_names)}개): {prompt_preview}")
    
    # API 호출
    return call_gemini(combined_prompt)

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
