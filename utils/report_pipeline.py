import pandas as pd
from utils.excel_parser import parse_checklist_excel
from utils.prompt_loader import PromptLoader
from api.gemini import call_gemini
from typing import Optional


def generate_report_from_excel(
    input_path: str,
    output_path: str,
    prompt_path: str = "data/prompts/prompts.json",
    prompt_ids: Optional[list] = None,
    prompt_id: Optional[str] = None,  # 하위 호환성 유지
    sheet_name: Optional[str] = None
):
    """
    엑셀 체크시트 → LLM 코멘트 생성 → 엑셀 저장 (AI_코멘트 컬럼 추가)
    prompt_ids: 적용할 프롬프트 id 목록 (없으면 첫 번째 활성 프롬프트 사용)
    prompt_id: (이전 버전 호환용) 단일 프롬프트 id
    """
    # 1. 엑셀 데이터 추출
    items = parse_checklist_excel(input_path, sheet_name=sheet_name)
    df = pd.read_excel(input_path, sheet_name=sheet_name)

    # 2. 프롬프트 로드 (항목별 적용용)
    prompt_loader = PromptLoader(prompt_path)
    all_prompts = prompt_loader.load_prompts_by_usage(usage_type="report")
    
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
            raise ValueError("활성화된 report 타입 프롬프트가 없습니다.")    # 3. 각 행별로 LLM 호출 및 결과 저장
    ai_comments = []
    for item in items:
        combined_responses = []
        
        # 모든 선택된 프롬프트에 대해 처리
        for prompt_template in selected_prompts:
            prompt_text = prompt_template.format(
                clause=item["clause"],
                title=item["title"],
                remark=item["remark"],
                status=item["status"]
            )
            try:
                ai_comment = call_gemini(prompt_text)
                combined_responses.append(ai_comment)
            except Exception as e:
                combined_responses.append(f"[AI 오류] {e}")
        
        # 모든 응답 결합
        ai_comment = "\n\n====================\n\n".join(combined_responses)
        ai_comments.append(ai_comment)

    # 4. 결과 엑셀에 저장 (AI_코멘트 컬럼 추가)
    df["AI_코멘트"] = ai_comments
    df.to_excel(output_path, index=False)
    print(f"완료: {output_path}에 저장됨") 