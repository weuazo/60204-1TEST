# utils/prompt_loader.py
import os
import json
import threading
import time
from tkinter import ttk

# 캐시 관련 전역 변수
_prompt_cache = {}
_prompt_cache_timestamp = {}
_cache_lock = threading.Lock()

def load_prompts_by_type(prompt_type, as_dict=False, include_metadata=False):
    """
    지정된 유형의 프롬프트를 로드합니다.
    
    Args:
        prompt_type: 프롬프트 유형 ("remark" 또는 "chat")
        as_dict: 딕셔너리 형태로 반환할지 여부
        include_metadata: 우선순위 등 메타데이터 포함 여부
    
    Returns:
        프롬프트 목록 또는 딕셔너리
    """
    prompt_dir = "prompts"
    if not os.path.exists(prompt_dir):
        os.makedirs(prompt_dir, exist_ok=True)
        return {} if as_dict else []

    result = {} if as_dict else []
    all_prompts = []
    
    try:
        # 모든 프롬프트 파일 로드
        for file in os.listdir(prompt_dir):
            if not file.endswith(".json"):
                continue
                
            try:
                with open(os.path.join(prompt_dir, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # 파일 이름에서 .json 제거
                    prompt_name = data.get("prompt_name", file[:-5])
                    
                    # 유형 확인 (문자열로 된 경우 리스트로 변환)
                    prompt_types = data.get("type", [])
                    if isinstance(prompt_types, str):
                        prompt_types = [prompt_types]
                    elif not isinstance(prompt_types, list):
                        prompt_types = []
                        
                    # 지정된 유형이 있는지 확인
                    if prompt_type in prompt_types:
                        priority = data.get("priority", 999)
                        template = data.get("template", "")
                        
                        if include_metadata:
                            all_prompts.append({
                                "prompt_name": prompt_name,
                                "priority": priority,
                                "template": template,
                                "type": prompt_types,
                                "data": data
                            })
                        else:
                            all_prompts.append({
                                "prompt_name": prompt_name,
                                "priority": priority,
                                "template": template
                            })
            except Exception as e:
                print(f"프롬프트 파일 로드 실패: {file} - {str(e)}")
                
        # 우선순위 기준으로 정렬
        all_prompts.sort(key=lambda x: x["priority"])
        
        # 반환 형태에 맞게 처리
        if as_dict:
            for prompt in all_prompts:
                prompt_name = prompt["prompt_name"]
                if include_metadata:
                    result[prompt_name] = prompt["data"]
                else:
                    result[prompt_name] = prompt["template"]
        else:
            result = [prompt["template"] for prompt in all_prompts]
    except Exception as e:
        print(f"프롬프트 로드 중 예기치 않은 오류: {str(e)}")
    
    return result

def load_prompts_by_type_cached(prompt_type, as_dict=False, include_metadata=False):
    """캐싱된 프롬프트 로더"""
    global _prompt_cache, _prompt_cache_timestamp, _cache_lock
    
    cache_key = f"{prompt_type}_{as_dict}_{include_metadata}"
    
    with _cache_lock:
        # 캐시 유효성 검사
        if cache_key in _prompt_cache:
            # 디렉토리의 최신 수정 시간 확인
            dir_mtime = os.path.getmtime("prompts") if os.path.exists("prompts") else 0
            if dir_mtime <= _prompt_cache_timestamp.get(cache_key, 0):
                return _prompt_cache[cache_key]
        
        # 캐시 없거나 만료됨 - 다시 로드
        result = load_prompts_by_type(prompt_type, as_dict, include_metadata)
        _prompt_cache[cache_key] = result
        _prompt_cache_timestamp[cache_key] = time.time()
        
        return result

# 스레드 기반 처리 함수
def run_in_background(func, callback=None, error_handler=None, *args, **kwargs):
    """
    백그라운드 스레드에서 함수 실행
    
    Args:
        func: 실행할 함수
        callback: 성공 시 호출할 콜백 함수 (결과를 인자로 받음)
        error_handler: 오류 시 호출할 함수 (예외를 인자로 받음)
        *args, **kwargs: func에 전달할 인자들
    """
    def thread_func():
        try:
            result = func(*args, **kwargs)
            if callback:
                # tkinter UI와의 안전한 상호작용을 위해
                # UI 스레드에서 콜백 실행 시도
                try:
                    import tkinter as tk
                    # 현재 tkinter 루트 윈도우 찾기 시도
                    from ui.gui_main import get_root
                    root = get_root()
                    if root and not root.winfo_ismapped():
                        # UI가 이미 종료된 경우
                        root = None
                except (ImportError, AttributeError):
                    root = None
                
                if root:
                    # tkinter 이벤트 루프에서 콜백 실행
                    root.after(0, lambda: callback(result))
                else:
                    # UI가 없는 경우 직접 실행
                    callback(result)
        except Exception as e:
            if error_handler:
                # 오류 처리기 호출
                try:
                    # UI 스레드에서 오류 처리
                    from ui.gui_main import get_root
                    root = get_root()
                    if root and not root.winfo_ismapped():
                        root = None
                except (ImportError, AttributeError):
                    root = None
                
                if root:
                    root.after(0, lambda: error_handler(e))
                else:
                    error_handler(e)
            else:
                # 오류 처리기가 없으면 출력만
                print(f"백그라운드 작업 오류: {e}")
    
    thread = threading.Thread(target=thread_func)
    thread.daemon = True  # 메인 프로그램 종료 시 스레드도 종료
    thread.start()
    return thread
