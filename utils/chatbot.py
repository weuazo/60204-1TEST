from utils.prompt_loader import PromptLoader
from api.gemini import call_gemini
from typing import Optional, Dict

def chat_with_ai(
    user_question: str,
    context: Optional[Dict] = None,
    prompt_path: str = "data/prompts/prompts.json",
    prompt_ids: Optional[list] = None,
    prompt_id: Optional[str] = None  # 하위 호환성 유지
) -> str:
    """
    챗봇 프롬프트를 적용해 LLM에게 자유롭게 질문/답변
    context: {"clause": "...", "title": "...", "remark": "...", "status": "..."} 등 원하는 정보
    prompt_ids: 적용할 프롬프트 id 목록 (없으면 첫 번째 활성 프롬프트 사용)
    prompt_id: (이전 버전 호환용) 단일 프롬프트 id
    """
    prompt_loader = PromptLoader(prompt_path)
    all_prompts = prompt_loader.load_prompts_by_usage(usage_type="chat")
    
    # 단일 ID가 전달된 경우 리스트로 변환 (하위 호환)
    if prompt_id and not prompt_ids:
        prompt_ids = [prompt_id]
        
    # 선택된 프롬프트 템플릿들을 리스트로 가져옴
    selected_prompts = []
    if prompt_ids:
        for p_id in prompt_ids:
            for p in all_prompts:
                if p.get("name") == p_id:
                    selected_prompts.append(p["template"])
                    break
    
    # 선택된 프롬프트가 없으면 첫 번째 활성 프롬프트 사용
    if not selected_prompts:
        if all_prompts:
            selected_prompts.append(all_prompts[0]["template"])
        else:
            raise ValueError("활성화된 chat 타입 프롬프트가 없습니다.")    # context dict를 문자열로 변환
    context_str = ""
    if context:
        for k, v in context.items():
            context_str += f"[{k}] {v}\n"
            
    combined_answers = []
    
    # 모든 선택된 프롬프트에 대해 처리
    for prompt_template in selected_prompts:
        prompt_text = prompt_template + "\n" + context_str + f"\n[질문] {user_question}"
        
        try:
            answer = call_gemini(prompt_text)
            combined_answers.append(answer)
        except Exception as e:
            combined_answers.append(f"[AI 오류] {e}")
    
    # 모든 응답 결합
    final_answer = "\n\n====================\n\n".join(combined_answers)
    return final_answer