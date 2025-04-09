"""
규격/표준 자동 감지 모듈
"""
import os
import re
import pandas as pd

# 규격별 키워드 및 패턴 정의 - 한국어 키워드 추가
STANDARD_PATTERNS = {
    "IEC_60204-1": {
        "keywords": ["60204", "전기장비", "전기 장비", "기계 안전", "기계류 안전", "machine safety"],
        "patterns": [r"60204(-|\s)?1", r"electrical equipment", r"기계(의|류)?\s?전기\s?장비", r"전기.*?장비"]
    },
    "IEC_61010": {
        "keywords": ["61010", "측정기기", "측정 장비", "시험장비", "laboratory equipment"],
        "patterns": [r"61010", r"측정(용|을 위한)?\s?(장비|장치|기기)", r"laboratory", r"실험실.*?장비"]
    },
    "ISO_13849": {
        "keywords": ["13849", "안전 관련", "제어 시스템", "control systems", "안전 제어", "PL"],
        "patterns": [r"13849", r"safety-related", r"안전\s?관련\s?제어", r"PL\s?[a-e]"]
    },
    "IEC_62061": {
        "keywords": ["62061", "안전", "기능안전", "functional safety", "SIL"],
        "patterns": [r"62061", r"기능\s?안전", r"functional safety", r"SIL\s?[1-4]"]
    },
    "ISO_14119": {
        "keywords": ["14119", "인터록", "가드", "interlock", "guards", "연동장치"],
        "patterns": [r"14119", r"인터록\s?장치", r"interlocking devices", r"연동.*?장치"]
    },
    "IEC_60335": {
        "keywords": ["60335", "가전", "가정용", "household", "가정용 기기"],
        "patterns": [r"60335", r"가정용.*?기기", r"household appliance"]
    }
}

def detect_standard_from_file(file_path, sheet_name=None):
    """
    파일에서 규격 탐지
    
    Args:
        file_path: 엑셀 파일 경로
        sheet_name: 시트 이름 (선택적)
        
    Returns:
        str: 감지된 규격 식별자 또는 "UNKNOWN"
    """
    # 파일이 존재하는지 확인
    if not os.path.exists(file_path):
        print(f"파일이 존재하지 않습니다: {file_path}")
        return "UNKNOWN"
        
    filename = os.path.basename(file_path).lower()
    
    # 1. 파일명에서 탐지 시도
    std = detect_from_filename(filename)
    if std != "UNKNOWN":
        return std
    
    # 2. 파일 내용에서 탐지 시도
    try:
        # 시트 목록 확인
        if sheet_name is None:
            xls = pd.ExcelFile(file_path)
            sheets = xls.sheet_names
            if not sheets:
                return "UNKNOWN"
            sheet_name = sheets[0]  # 기본값은 첫 번째 시트
        
        # 선택된 시트 로드
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # 2.1 열 이름에서 탐지
        column_sample = " ".join([str(col) for col in df.columns])
        std = detect_from_text(column_sample)
        if std != "UNKNOWN":
            return std
        
        # 2.2 데이터 내용에서 탐지 (텍스트 열만)
        text_sample = ""
        for col in df.select_dtypes(include=['object']).columns:
            # 각 열에서 최대 20개 행 샘플링
            sample_size = min(20, len(df))
            for i in range(sample_size):
                if i < len(df) and pd.notna(df.iloc[i][col]):
                    text_sample += str(df.iloc[i][col]) + " "
                    
            if len(text_sample) > 200:  # 충분한 샘플 확보하면 검사
                std = detect_from_text(text_sample)
                if std != "UNKNOWN":
                    return std
                # 텍스트 샘플 초기화 (메모리 절약)
                text_sample = ""
    
    except Exception as e:
        print(f"파일 내용 검사 중 오류: {e}")
    
    return "UNKNOWN"

def detect_from_filename(filename):
    """파일 이름에서 규격 탐지"""
    for std_name, data in STANDARD_PATTERNS.items():
        # 키워드 검사
        for keyword in data["keywords"]:
            if keyword.lower() in filename:
                return std_name
                
        # 패턴 검사
        for pattern in data["patterns"]:
            if re.search(pattern, filename, re.IGNORECASE):
                return std_name
    
    return "UNKNOWN"

def detect_from_text(text):
    """텍스트 내용에서 규격 탐지"""
    text = text.lower()
    
    for std_name, data in STANDARD_PATTERNS.items():
        # 키워드 검사
        for keyword in data["keywords"]:
            if keyword.lower() in text:
                return std_name
                
        # 패턴 검사
        for pattern in data["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                return std_name
    
    return "UNKNOWN"

def get_standard_info(standard_id):
    """
    규격 ID에 대한 추가 정보 반환
    
    Args:
        standard_id: 규격 식별자 (예: "IEC_60204-1")
    
    Returns:
        dict: 규격 관련 정보
    """
    standard_info = {
        "IEC_60204-1": {
            "title": "IEC 60204-1 기계류의 전기장비",
            "description": "기계류의 전기장비에 대한 안전 요구사항",
            "scope": "산업용 기계의 전기 장비 및 시스템",
            "key_sections": ["위험 평가", "보호 접지", "비상 정지", "제어 회로", "문서화"],
            "version": "IEC 60204-1:2016"
        },
        "IEC_61010": {
            "title": "IEC 61010 측정, 제어 및 실험실용 전기장비",
            "description": "측정, 제어 및 실험실용 전기장비의 안전 요구사항",
            "scope": "측정, 실험 및 테스트 장비",
            "key_sections": ["감전 보호", "기계적 위험", "확산된 에너지", "문서화"],
            "version": "IEC 61010-1:2010+AMD1:2016"
        },
        "ISO_13849": {
            "title": "ISO 13849 안전 관련 제어 시스템",
            "description": "기계류의 안전 관련 제어 시스템 설계 원칙",
            "scope": "안전 관련 제어 시스템",
            "key_sections": ["위험 평가", "성능 수준(PL)", "카테고리", "검증 및 유효성 확인"],
            "version": "ISO 13849-1:2015"
        },
        "IEC_62061": {
            "title": "IEC 62061 기계류의 안전성",
            "description": "기계류의 안전 관련 전기, 전자 및 프로그래머블 제어 시스템",
            "scope": "안전 관련 전기제어 시스템",
            "key_sections": ["안전 무결성 수준(SIL)", "하드웨어 고장 확률", "진단 범위", "소프트웨어 요구사항"],
            "version": "IEC 62061:2021"
        },
        "ISO_14119": {
            "title": "ISO 14119 인터록 장치",
            "description": "가드 관련 인터록 장치의 설계 및 선택 원칙",
            "scope": "가드와 관련된 인터록 장치",
            "key_sections": ["락킹 장치", "이스케이핑", "마스킹", "오류 배제 원칙"],
            "version": "ISO 14119:2013"
        },
        "IEC_60335": {
            "title": "IEC 60335 가정용 및 유사한 전기기기",
            "description": "가정용 및 유사한 전기기기의 안전성",
            "scope": "가정용 전기기기",
            "key_sections": ["일반 요구사항", "시험 요구사항", "마킹", "보호 조치"],
            "version": "IEC 60335-1:2020"
        },
        "UNKNOWN": {
            "title": "미확인 규격",
            "description": "자동으로 감지된 규격이 없습니다",
            "scope": "알 수 없음",
            "key_sections": [],
            "version": "N/A"
        }
    }
    
    return standard_info.get(standard_id, standard_info["UNKNOWN"])

def enhance_detection_with_ai(file_path, text_content):
    """AI 기반 규격 감지 향상"""
    from api.gemini import call_gemini
    
    # 복합적 프롬프트 작성
    prompt = f"""
분석 작업: 다음 텍스트가 어떤 기술 규격 또는 표준과 관련되어 있는지 식별해주세요.

텍스트 샘플:
{text_content[:3000]}

파일명: {os.path.basename(file_path)}

당신의 임무는 다음 규격 중 하나와 관련된 것인지 판별하는 것입니다:
1. IEC 60204-1: 기계류의 전기장비
2. IEC 61010: 측정, 제어 및 실험실용 전기장비
3. ISO 13849: 안전 관련 제어 시스템
4. IEC 62061: 기계류의 안전성
5. ISO 14119: 인터록 장치
6. IEC 60335: 가정용 및 유사한 전기기기

다음 형식으로만 응답해주세요:
{{
  "standard_id": "규격ID (예: IEC_60204-1)",
  "confidence": 0-1 사이 숫자 (확신도),
  "reason": "감지 이유를 간략하게 설명"
}}

위 규격 중 어느 것에도 해당하지 않는다면 standard_id를 "UNKNOWN"으로 설정하세요.
"""
    
    try:
        response = call_gemini(prompt)
        
        # JSON 응답 추출
        import re
        import json
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            return result.get("standard_id", "UNKNOWN"), result.get("confidence", 0)
            
    except Exception as e:
        print(f"AI 규격 감지 중 오류: {e}")
        
    return "UNKNOWN", 0

def get_all_standards():
    """
    모든 규격 정보 반환
    
    Returns:
        dict: 모든 규격 정보
    """
    standards = {}
    
    # 기본 규격 정보 가져오기
    for std_id in ["IEC_60204-1", "IEC_61010", "ISO_13849", "IEC_62061", "ISO_14119", "IEC_60335"]:
        standards[std_id] = get_standard_info(std_id)
    
    # 사용자 추가 규격 정보 로드 (향후 기능)
    # TODO: 사용자 정의 규격 로드 기능 추가
    
    return standards

def update_standard_info(standard_id, new_info):
    """
    규격 정보 업데이트 (향후 확장용)
    
    Args:
        standard_id: 규격 ID
        new_info: 업데이트할 정보 딕셔너리
    
    Returns:
        bool: 성공 여부
    """
    try:
        # 현재는 메모리에만 저장됨
        # TODO: 향후 지속적으로 저장하는 기능 추가
        return True
    except Exception as e:
        print(f"규격 정보 업데이트 중 오류: {e}")
        return False
