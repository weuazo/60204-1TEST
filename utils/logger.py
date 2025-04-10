import logging
import sys

# 로깅 시스템 구성
def setup_logger(log_level=logging.INFO):
    logger = logging.getLogger('gemini_report')
    logger.setLevel(log_level)

    # 기존 핸들러 제거 (중복 방지)
    if logger.hasHandlers():
        logger.handlers.clear()

    # 콘솔 핸들러
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)

    # 파일 핸들러 (로그 파일 저장)
    file_handler = logging.FileHandler('gemini_report.log')
    file_handler.setLevel(logging.DEBUG)

    # 포맷 설정
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 핸들러 추가
    logger.addHandler(console)
    logger.addHandler(file_handler)

    return logger

# 로그 필터링 클래스
def set_log_level(level):
    """동적으로 로그 레벨을 설정합니다."""
    logger = logging.getLogger('gemini_report')
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

# 로거 인스턴스 생성
logger = setup_logger()

# 예제 사용법
if __name__ == "__main__":
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
