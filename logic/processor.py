# logic/processor.py

import pandas as pd
import os
import json
from datetime import datetime
from api.gemini import call_gemini
from utils.prompt_loader import load_prompts_by_type

def load_prompt_by_name(name):
    """이름으로 프롬프트 템플릿 불러오기"""
    prompts = load_prompts_by_type("remark", as_dict=True, include_metadata=True)
    if name in prompts:
        return prompts[name].get('template', '')
    return None

def generate_remarks_from_excel(base_path, review_path, clause_col, title_col, remark_col, prompt_names):
    """Excel 파일에서 리마크 생성"""
    # 단일 프롬프트 지원
    if isinstance(prompt_names, str):
        prompt_names = [prompt_names]
        
    # 프롬프트 로드
    prompts_data = load_prompts_by_type("remark", as_dict=True, include_metadata=True)
    
    # 선택된 프롬프트 필터링
    selected_prompts = {name: data for name, data in prompts_data.items() 
                      if name in prompt_names}
    
    if not selected_prompts:
        raise ValueError("선택한 프롬프트를 찾을 수 없습니다.")
    
    # 우선순위로 정렬
    sorted_prompts = sorted(selected_prompts.items(), 
                           key=lambda x: x[1].get('priority', 999))
    
    # 모든 프롬프트 지침 결합
    system_instructions = []
    for name, data in sorted_prompts:
        template = data.get('template', '')
        system_instructions.append(f"# {name} 지침\n{template}")

    # 결합된 프롬프트
    combined_template = "\n\n".join(system_instructions)
    
    # 데이터 로드
    df = pd.read_excel(review_path)
    results = []
    
    # 각 행 처리
    for idx, row in df.iterrows():
        clause = str(row.get(clause_col, "")).strip()
        title = str(row.get(title_col, "")).strip()
        
        if not clause:
            continue
            
        # 프롬프트 적용
        prompt = combined_template.replace("{clause}", clause).replace("{title}", title)
        prompt += f"\n\n# 작업 요청\n위 지침에 따라 항목 '{clause}' ({title})에 대한 검토 의견을 작성해주세요."

        try:
            response = call_gemini(prompt)
            df.at[idx, remark_col] = response.strip()
        except Exception as e:
            df.at[idx, remark_col] = f"[ERROR] {str(e)}"

        results.append((clause, title))

    # 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("output", exist_ok=True)
    save_path = os.path.join("output", f"report_{timestamp}.xlsx")
    df.to_excel(save_path, index=False)
    
    return save_path
