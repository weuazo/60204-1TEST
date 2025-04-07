import re
import pandas as pd

def infer_columns_from_text(text):
    """텍스트에서 열 구조 추론하기"""
    # 항목 번호 패턴
    clause_pattern = r'(\d+\.\d+(?:\.\d+)?)\s+(.*?)(?=\d+\.\d+|\Z)'
    matches = re.findall(clause_pattern, text, re.DOTALL)
    
    if matches:
        items = []
        for clause, content in matches:
            # 제목과 내용 분리 시도
            title_match = re.match(r'([^\n]+)', content.strip())
            title = title_match.group(1) if title_match else ""
            
            # 내용은 제목을 제외한 나머지
            if title and len(content) > len(title):
                description = content[len(title):].strip()
            else:
                description = ""
                
            items.append({
                "항목번호": clause.strip(),
                "제목": title.strip(),
                "내용": description.strip()
            })
        
        # 데이터프레임 생성
        if items:
            return pd.DataFrame(items)
    
    return None
