import tkinter as tk
import os
import sys
import traceback
import argparse
import datetime

# 버전 정보
VERSION = "0.1.5"

def setup_environment():
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

def main():
    # 파이썬 버전 체크
    if sys.version_info < (3, 6):
        print("❌ 이 프로그램은 Python 3.6 이상이 필요합니다.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description=f"Gemini 보고서 자동 생성기 v{VERSION}")
    parser.add_argument("--mode", choices=["gui"], default="gui", help="실행 모드 선택")
    parser.add_argument("--debug", action="store_true", help="디버그 모드 활성화")
    args = parser.parse_args()

    # 로거 초기화
    from utils.logger import logger
    logger.info(f"Gemini 보고서 생성기 v{VERSION} 시작")

    # 디버그 모드가 활성화된 경우 디버깅 정보 출력
    if args.debug:
        from debug_helpers import print_environment_info, check_prompt_files
        print_environment_info()
        check_prompt_files()

    if args.mode == "gui":
        print(f"[INFO] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Gemini 보고서 생성기 v{VERSION} 시작 중...")
        
        # 먼저 환경 설정 (디렉토리 및 기본 프롬프트 생성)
        try:
            setup_environment()
        except Exception as e:
            print(f"❌ 환경 초기화 중 오류 발생: {e}")
            traceback.print_exc()
            sys.exit(1)
        
        # GUI 초기화
        try:
            # 먼저 UI 설정 모듈 임포트
            from ui.gui_main import create_main_window
            
            # GUI 생성 - 프로그램 실행에 가장 중요한 부분
            app = create_main_window()
            if app is None:
                raise RuntimeError("❌ GUI 초기화 실패")
            
            # 애플리케이션 실행
            print(f"[INFO] GUI 초기화 완료, 애플리케이션 실행 시작")
            app.mainloop()
            
        except ImportError as e:
            print(f"❌ GUI 모듈을 불러올 수 없습니다: {e}")
            traceback.print_exc()
            sys.exit(1)
        except Exception as e:
            print(f"❌ GUI 실행 중 오류 발생: {e}")
            traceback.print_exc()
            sys.exit(1)
    else:
        print("❌ 현재는 GUI 모드만 지원됩니다.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] 사용자에 의해 프로그램이 종료되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 예상치 못한 오류로 프로그램이 종료됩니다: {e}")
        traceback.print_exc()
        sys.exit(1)
