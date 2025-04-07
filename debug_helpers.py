"""
디버깅 유틸리티 모듈
"""
import os
import sys
import json
import traceback

def print_environment_info():
    """환경 정보 출력"""
    print("\n=== 환경 정보 ===")
    print(f"Python 버전: {sys.version}")
    print(f"실행 경로: {os.path.abspath('.')}")
    print(f"PYTHONPATH: {os.pathsep.join(sys.path)}")
    
    # 필요한 디렉토리 확인
    dirs_to_check = ['prompts', 'output']
    for dir_name in dirs_to_check:
        if os.path.exists(dir_name):
            print(f"디렉토리 '{dir_name}' 존재함: {len(os.listdir(dir_name))}개 파일")
        else:
            print(f"디렉토리 '{dir_name}' 없음")
    print("==================\n")

def check_prompt_files():
    """프롬프트 파일 점검"""
    prompt_dir = 'prompts'
    if not os.path.exists(prompt_dir):
        print(f"프롬프트 디렉토리가 없습니다: {prompt_dir}")
        return
        
    print("\n=== 프롬프트 파일 ===")
    for file in os.listdir(prompt_dir):
        if file.endswith('.json'):
            try:
                with open(os.path.join(prompt_dir, file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    prompt_type = data.get('type', [])
                    priority = data.get('priority', 'N/A')
                    print(f"- {file}: 유형={prompt_type}, 우선순위={priority}")
            except Exception as e:
                print(f"- {file}: 오류 - {e}")
    print("====================\n")

def safe_function(func):
    """함수 실행 오류 포착 데코레이터"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"\n🔴 오류 발생: {func.__name__} - {e}")
            traceback.print_exc()
            return None
    return wrapper
