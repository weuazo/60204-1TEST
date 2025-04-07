import logging
import sys

# 로깅 시스템 구성
def setup_logger():
    logger = logging.getLogger('gemini_report')
    logger.setLevel(logging.INFO)
    
    # 콘솔 핸들러
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    
    # 파일 핸들러 (로그 파일 저장)
    file_handler = logging.FileHandler('gemini_report.log')
    file_handler.setLevel(logging.DEBUG)
    
    # 포맷 설정
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(console)
    logger.addHandler(file_handler)
    
    return logger

# 로거 인스턴스 생성
logger = setup_logger()
