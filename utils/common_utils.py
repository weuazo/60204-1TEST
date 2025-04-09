"""
공통 유틸리티 함수 모듈
프로젝트 전체에서 사용되는 공통 기능들을 모아둔 모듈입니다.
"""
import os
import traceback
from datetime import datetime
from functools import wraps, lru_cache
import threading
from concurrent.futures import ThreadPoolExecutor

# 로깅 시스템 통합
def get_logger():
    """중앙 집중식 로거 객체 반환"""
    try:
        from utils.logger import logger
        return logger
    except ImportError:
        import logging
        # 로거 모듈을 임포트 할 수 없는 경우 기본 로거 생성
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('gemini_report')

# 전역 로거 인스턴스
logger = get_logger()

def handle_exception(e, title="오류", message_prefix="작업 중 오류가 발생했습니다", log_error=True):
    """예외를 일관되게 처리하는 통합 함수"""
    error_message = str(e)
    
    if log_error:
        logger.error(f"{message_prefix}: {error_message}")
    
    try:
        from tkinter import messagebox
        messagebox.showerror(title, f"{message_prefix}:\n{error_message}")
    except Exception:
        # TK가 초기화되지 않았거나 GUI 환경이 아닌 경우
        print(f"❌ {title}: {message_prefix}: {error_message}")
    
    return error_message

def safe_function(func):
    """오류 포착 및 로깅 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"함수 {func.__name__} 실행 중 오류: {e}")
            traceback.print_exc()
            return None
    return wrapper

def save_result_file(df, original_path=None):
    """결과 파일 저장 - generator와 extended_generator에서 중복 사용되던 함수 통합"""
    try:
        os.makedirs("output", exist_ok=True)
        
        # 원본 경로가 없는 경우 기본 파일명 사용
        if not original_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join("output", f"result_{timestamp}.xlsx")
            df.to_excel(output_path, index=False)
            return output_path
        
        # 파일명과 확장자 추출
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
        
        logger.info(f"결과 파일 저장 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"결과 파일 저장 중 오류: {str(e)}")
        # 실패 시 임시 파일로 저장 시도
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            emergency_path = os.path.join("output", f"emergency_save_{timestamp}.xlsx")
            df.to_excel(emergency_path, index=False)
            logger.warning(f"임시 파일로 저장됨: {emergency_path}")
            return emergency_path
        except Exception as e2:
            logger.critical(f"임시 저장도 실패: {str(e2)}")
            return None

def run_in_background(func, callback=None, error_handler=None, *args, **kwargs):
    """
    백그라운드 스레드에서 함수 실행 - 개선된 버전
    
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
                    # GUI 모듈을 메인 스레드에서만 가져오도록 지연 임포트
                    def get_root_safely():
                        try:
                            from ui.gui_main import get_root
                            return get_root()
                        except (ImportError, AttributeError):
                            return None
                    
                    root = get_root_safely()
                    if root and root.winfo_exists():
                        root.after(0, lambda: callback(result))
                    else:
                        callback(result)
                except Exception:
                    # GUI 없는 환경에서는 직접 콜백 실행
                    callback(result)
        except Exception as e:
            logger.error(f"백그라운드 작업 오류: {e}")
            traceback.print_exc()
            if error_handler:
                try:
                    # 오류 처리기도 메인 스레드에서 실행 시도
                    root = get_root_safely()
                    if root and root.winfo_exists():
                        root.after(0, lambda: error_handler(e))
                    else:
                        error_handler(e)
                except Exception:
                    error_handler(e)
    
    thread = threading.Thread(target=thread_func)
    thread.daemon = True  # 메인 프로그램 종료 시 스레드도 종료
    thread.start()
    return thread

def parallel_process(items, process_func, max_workers=None, cancel_var=None):
    """
    항목들을 병렬로 처리하는 일반화된 함수
    
    Args:
        items: 처리할 항목들의 리스트
        process_func: 각 항목을 처리할 함수 (항목을 인자로 받고 결과를 반환)
        max_workers: 최대 작업자 수 (기본값: min(10, 항목 수))
        cancel_var: 취소 여부를 저장할 변수 (dictionary with 'cancelled' key)
        
    Returns:
        처리 결과 리스트
    """
    if not items:
        return []
    
    # 작업자 수 설정
    if max_workers is None:
        max_workers = min(10, len(items))
    
    results = []
    processed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        
        # 작업 제출
        for i, item in enumerate(items):
            if cancel_var and cancel_var.get('cancelled', False):
                logger.info("사용자에 의해 작업 취소됨")
                break
                
            future = executor.submit(process_func, item)
            futures[future] = i
        
        # 완료된 작업 결과 처리
        for future in futures:
            try:
                # 주기적으로 취소 여부 확인
                if cancel_var and cancel_var.get('cancelled', False) and processed % 5 == 0:
                    logger.info("사용자에 의해 작업 취소됨 - 남은 작업 건너뜀")
                    break
                    
                result = future.result()
                results.append(result)
                
                processed += 1
                # 진행 상황 로깅
                if processed % 5 == 0 or processed == len(futures):
                    percent_done = int(processed/len(futures)*100)
                    logger.info(f"처리 중: {processed}/{len(futures)} ({percent_done}%)")
                
            except Exception as e:
                logger.error(f"항목 처리 중 오류: {e}")
                results.append(None)  # 실패한 항목은 None으로 표시
    
    return results

# 캐시 데코레이터 - 메모리 효율성을 위해 LRU 캐시 사용
def cached(max_size=128):
    """LRU 캐싱 데코레이터"""
    def decorator(func):
        @lru_cache(maxsize=max_size)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        # 캐시 무효화 메서드 추가
        wrapper.clear_cache = wrapper.__wrapped__.cache_clear
        return wrapper
    return decorator