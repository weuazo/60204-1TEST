import os
import sys
import traceback
import argparse
import datetime
from utils.plugin_loader import PluginLoader

# 버전 정보
VERSION = "0.1.5"

def setup_environment() -> None:
    """전역 변수환경 초기화"""
    # 필수 디렉토리 생성
    os.makedirs("output", exist_ok=True)
    os.makedirs("prompts", exist_ok=True)
    os.makedirs("data", exist_ok=True)  # AI 엑셀 분석기의 학습 데이터 저장 디렉토리
    
    # 기본 프롬프트 파일 생성
    default_prompt_file = os.path.join("prompts", "General_Review.json")
    if not os.path.exists(default_prompt_file):
        try:
            with open(default_prompt_file, "w", encoding="utf-8") as f:
                f.write('''{
  "prompt_name": "General_Review",
  "type": ["remark"],
  "template": "항목 {clause}에 대한 검토 의견을 작성해주세요. 해당 항목은 \\\"{title}\\\"에 관한 것입니다.",
  "priority": 1,
  "metadata": {
    "name": "일반 검토",
    "description": "기본적인 검토 의견 생성 프롬프트입니다.",
    "author": "system",
    "created": "2023-12-01"
  }
}''')
            print(f"기본 프롬프트 파일 생성: {default_prompt_file}")
        except Exception as e:
            print(f"기본 프롬프트 파일 생성 실패: {e}")
    else:
        print(f"기본 프롬프트 파일이 이미 존재합니다: {default_prompt_file}")
    
    # 로그 디렉토리 생성 
    os.makedirs("logs", exist_ok=True)

def log_with_timestamp(message: str, level: str = "INFO") -> None:
    """타임스탬프와 함께 로그 메시지 출력"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{level}] {timestamp} - {message}")

def main() -> int:
    """메인 함수
    
    Returns:
        int: 종료 코드 (0: 성공, 1: 오류)
    """
    print("Starting Gemini Report Generator...")

    # 파이썬 버전 체크
    if sys.version_info < (3, 6):
        print("❌ 이 프로그램은 Python 3.6 이상이 필요합니다.")
        return 1

    parser = argparse.ArgumentParser(description=f"Gemini 보고서 자동 생성기 v{VERSION}")
    parser.add_argument("--mode", choices=["gui"], default="gui", help="실행 모드 선택")
    parser.add_argument("--debug", action="store_true", help="디버그 모드 활성화")
    args = parser.parse_args()

    try:
        # 로거 초기화
        from utils.logger import logger
        logger.info(f"Gemini 보고서 생성기 v{VERSION} 시작")

        # 디버그 모드가 활성화된 경우 디버깅 정보 출력
        if args.debug:
            from debug_helpers import print_environment_info, check_prompt_files
            print_environment_info()
            check_prompt_files()

        if args.mode == "gui":
            log_with_timestamp(f"Gemini 보고서 생성기 v{VERSION} 시작 중...")

            # 먼저 환경 설정 (디렉토리 및 기본 프롬프트 생성)
            setup_environment()

            # 애플리케이션 컨텍스트 초기화
            from utils.app_context import AppContext
            app_context = AppContext.get_instance()

            # 설정 로드
            app_context.load_config()

            # GUI 모듈 임포트 및 초기화
            try:
                from ui import gui_main
                logger.debug("Initializing GUI...")
                root = gui_main.create_main_window(app_context)

                if not root:
                    logger.error("GUI 초기화 실패")
                    log_with_timestamp("GUI 초기화 실패", "ERROR")
                    return 1

                logger.debug("Starting Tkinter main loop...")
                root.mainloop()
            except ImportError as e:
                logger.error(f"GUI 모듈 로딩 실패: {e}")
                log_with_timestamp(f"GUI 모듈 로딩 실패: {e}", "ERROR")
                return 1
            except KeyboardInterrupt:
                log_with_timestamp("사용자에 의해 프로그램 종료", "INFO")
            except Exception as e:
                logger.error(f"실행 중 오류 발생: {e}")
                log_with_timestamp(f"실행 중 오류 발생: {e}", "ERROR")
                traceback.print_exc()
                return 1

        # Load plugins
        loader = PluginLoader()
        loader.load_plugins()

        # Execute a sample plugin if available
        sample_plugin = loader.get_plugin("sample_plugin")
        if sample_plugin and hasattr(sample_plugin, "run"):
            sample_plugin.run()
        else:
            print("Sample plugin not found or missing 'run' method.")

        # 프로그램 종료
        logger.info("프로그램 정상 종료")
        log_with_timestamp("프로그램 종료되었습니다.")
        return 0
    except Exception as e:
        print(f"❌ 예기치 않은 오류 발생: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
