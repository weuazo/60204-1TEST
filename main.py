"""
메인 애플리케이션 모듈
"""

import os
import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow
from utils.app_context import AppContext
from utils.logger import logger
from utils.report_pipeline import generate_report_from_excel
from utils.chatbot import chat_with_ai

def main():
    """메인 함수 (GUI)"""
    try:
        # 애플리케이션 컨텍스트 초기화
        app_context = AppContext.get_instance()
        
        # 애플리케이션 생성
        app = QApplication(sys.argv)

        # QSS 파일 로드 및 적용
        try:
            qss_file_path = os.path.join(os.path.dirname(__file__), "gui", "style.qss")
            if not os.path.exists(qss_file_path):
                 # PyInstaller 등으로 패키징되었을 때의 대체 경로 (sys._MEIPASS 사용)
                 # 이 경로는 실행 환경에 따라 조정 필요
                 if hasattr(sys, '_MEIPASS'):
                     qss_file_path = os.path.join(sys._MEIPASS, "gui", "style.qss")
            
            if os.path.exists(qss_file_path):
                with open(qss_file_path, "r", encoding="utf-8") as f:
                    qss = f.read()
                    app.setStyleSheet(qss)
            else:
                logger.warning("style.qss 파일을 찾을 수 없습니다. 기본 스타일로 실행됩니다.")
        except Exception as e:
            logger.error(f"스타일시트 적용 중 오류 발생: {e}")
        
        # 메인 윈도우 생성
        window = MainWindow()
        window.show()
        
        # 애플리케이션 실행
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"애플리케이션 실행 중 오류 발생: {e}")
        sys.exit(1)

def cli_main():
    print("1. 엑셀 자동 보고서 생성")
    print("2. 챗봇 질의응답")
    mode = input("모드 선택 (1/2): ").strip()

    if mode == "1":
        input_path = input("입력 엑셀 파일 경로: ").strip()
        output_path = input("출력 엑셀 파일 경로: ").strip()
        prompt_path = input("프롬프트 JSON 경로(엔터시 기본): ").strip() or "data/prompts/prompts.json"
        
        # 프롬프트 선택 로직 추가
        from utils.prompt_loader import PromptLoader
        loader = PromptLoader(prompt_path)
        prompts = loader.load_prompts_by_usage(usage_type="report")
        
        if not prompts:
            print("활성화된 report 타입 프롬프트가 없습니다.")
            return
        
        print("\n사용 가능한 프롬프트:")
        for i, p in enumerate(prompts):
            print(f"{i+1}. {p.get('name', '(이름없음)')}")
        
        prompt_ids = []
        prompt_input = input("\n사용할 프롬프트 번호(여러 개는 쉼표로 구분, 전체는 'all'): ").strip().lower()
        
        if prompt_input == 'all':
            prompt_ids = [p.get('name', '') for p in prompts]
        else:
            try:
                selected_indices = [int(idx.strip()) for idx in prompt_input.split(',') if idx.strip()]
                for idx in selected_indices:
                    if 1 <= idx <= len(prompts):
                        prompt_ids.append(prompts[idx-1].get('name', ''))
                    else:
                        print(f"경고: {idx}번은 유효한 프롬프트 번호가 아닙니다.")
            except ValueError:
                print("경고: 잘못된 번호 형식입니다. 첫 번째 프롬프트를 사용합니다.")
                prompt_ids = [prompts[0].get('name', '')]
        
        if not prompt_ids:
            prompt_ids = [prompts[0].get('name', '')]
            print("선택된 프롬프트가 없어 첫 번째 프롬프트를 사용합니다.")
        
        print(f"선택된 프롬프트: {', '.join(prompt_ids)}")
        generate_report_from_excel(input_path, output_path, prompt_path, prompt_ids=prompt_ids)
        
    elif mode == "2":
        prompt_path = input("프롬프트 JSON 경로(엔터시 기본): ").strip() or "data/prompts/prompts.json"
        
        # 프롬프트 선택 로직 추가
        from utils.prompt_loader import PromptLoader
        loader = PromptLoader(prompt_path)
        prompts = loader.load_prompts_by_usage(usage_type="chat")
        
        if not prompts:
            print("활성화된 chat 타입 프롬프트가 없습니다.")
            return
        
        print("\n사용 가능한 프롬프트:")
        for i, p in enumerate(prompts):
            print(f"{i+1}. {p.get('name', '(이름없음)')}")
        
        prompt_ids = []
        prompt_input = input("\n사용할 프롬프트 번호(여러 개는 쉼표로 구분, 전체는 'all'): ").strip().lower()
        
        if prompt_input == 'all':
            prompt_ids = [p.get('name', '') for p in prompts]
        else:
            try:
                selected_indices = [int(idx.strip()) for idx in prompt_input.split(',') if idx.strip()]
                for idx in selected_indices:
                    if 1 <= idx <= len(prompts):
                        prompt_ids.append(prompts[idx-1].get('name', ''))
                    else:
                        print(f"경고: {idx}번은 유효한 프롬프트 번호가 아닙니다.")
            except ValueError:
                print("경고: 잘못된 번호 형식입니다. 첫 번째 프롬프트를 사용합니다.")
                prompt_ids = [prompts[0].get('name', '')]
        
        if not prompt_ids:
            prompt_ids = [prompts[0].get('name', '')]
            print("선택된 프롬프트가 없어 첫 번째 프롬프트를 사용합니다.")
            
        print(f"선택된 프롬프트: {', '.join(prompt_ids)}")
            
        print("\n엑셀 항목 정보(없으면 엔터):")
        clause = input("  - 항목/번호: ").strip()
        title = input("  - 내용/제목: ").strip()
        remark = input("  - 코멘트: ").strip()
        status = input("  - 상태: ").strip()
        context = {}
        if clause: context["clause"] = clause
        if title: context["title"] = title
        if remark: context["remark"] = remark
        if status: context["status"] = status
        question = input("질문: ").strip()
        answer = chat_with_ai(question, context, prompt_path, prompt_ids=prompt_ids)
        print("\n[AI 답변]\n", answer)
    else:
        print("잘못된 입력입니다.")

if __name__ == '__main__':
    if '--cli' in sys.argv:
        cli_main()
    else:
        main()