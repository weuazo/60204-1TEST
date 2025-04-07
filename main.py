import argparse
import sys
import traceback
import datetime
import os

# 버전 상수
VERSION = "0.1.3"  # 버전 업데이트

def setup_environment():
    """환경 초기화"""
    # 필요한 디렉토리 생성
    os.makedirs("output", exist_ok=True)
    os.makedirs("prompts", exist_ok=True)
    
    # 기본 프롬프트 파일 생성
    create_default_prompts_if_needed()

def create_default_prompts_if_needed():
    """기본 프롬프트 파일 생성"""
    import json
    
    default_prompts = [
        {
            "prompt_name": "IEC_Report",
            "type": ["remark"],
            "template": "{clause} 항목에 대한 검토 의견을 IEC 60204-1 표준에 근거하여 작성해주세요. 항목 내용: {title}",
            "priority": 1,
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "prompt_name": "General_Review",
            "type": ["remark"],
            "template": "{clause} 항목의 '{title}'에 대한 검토 의견을 전문가 관점에서 작성해주세요.",
            "priority": 2,
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "prompt_name": "Technical_Assistant",
            "type": ["chat"], 
            "template": "당신은 기술 문서 검토를 돕는 전문 AI 어시스턴트입니다. 사용자의 질문에 명확하고 정확하게 답변해 주세요.",
            "priority": 3,
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    for prompt in default_prompts:
        filename = os.path.join("prompts", f"{prompt['prompt_name']}.json")
        if not os.path.exists(filename):
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(prompt, f, ensure_ascii=False, indent=2)

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
            from ui.gui_main import create_gui
            
            # GUI 생성
            app = create_gui()
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
