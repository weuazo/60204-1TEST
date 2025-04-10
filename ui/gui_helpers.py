"""
GUI 초기화 및 문제 해결을 위한 헬퍼 모듈
"""
import tkinter as tk
from tkinter import ttk
import traceback
import time
from utils.logger import logger

def ensure_tab_visibility(root, notebook):
    """탭이 올바르게 표시되는지 확인하고 문제 해결"""
    try:
        logger.info("탭 가시성 확인...")
        
        # 노트북이 표시되지 않은 경우 처리
        if not notebook.winfo_ismapped():
            logger.warning("노트북이 매핑되지 않음: 강제 표시 시도")
            notebook.pack(fill=tk.BOTH, expand=True)
            root.update_idletasks()  # 즉시 업데이트 적용
        
        # 모든 탭 프레임이 있는지 확인하고 첫 번째 탭 선택
        tabs = notebook.tabs()
        if tabs:
            # 모든 탭을 순회하며 표시 상태 확인
            for i, tab_id in enumerate(tabs):
                tab_frame = notebook.nametowidget(tab_id)
                logger.info(f"탭 {i}: {tab_frame}, 표시={tab_frame.winfo_ismapped()}")
                
                # 탭 프레임이 매핑되지 않았다면 강제 표시
                if not tab_frame.winfo_ismapped():
                    logger.warning(f"탭 {i}가 매핑되지 않음: 강제 팩 시도")
                    tab_frame.pack(fill=tk.BOTH, expand=True)
                
                # 비어있는 탭이면 자식 위젯 확인
                if len(tab_frame.winfo_children()) == 0 and i == 0:  # 첫 번째 탭(보고서 탭)이 비어 있음
                    logger.warning(f"탭 {i}가 비어 있음: 보고서 탭 내용 강제 재생성")
                    # 강제로 내용 재생성
                    try:
                        from ui.report_tab import create_report_tab
                        create_report_tab(tab_frame)
                        root.update_idletasks()  # 즉시 업데이트 적용
                    except Exception as e:
                        logger.error(f"탭 내용 재생성 실패: {e}")
            
            # 첫 번째 탭(보고서 탭) 강제 선택 및 업데이트
            logger.info("보고서 탭 강제 선택 및 업데이트")
            notebook.select(0)  # 첫 번째 탭 선택
            root.update_idletasks()  # 선택 업데이트 적용
            
            # 보고서 탭 레이아웃 강제 업데이트
            tab_frame = notebook.nametowidget(notebook.tabs()[0])
            for child in tab_frame.winfo_children():
                child.update_idletasks()  # 각 자식 위젯도 강제 업데이트
                
            logger.info("보고서 탭 선택 완료")
            return True
        else:
            logger.error("노트북에 탭이 없음: 초기화 문제 가능성")
            
            # 진단 정보 수집 
            from utils.tab_diagnostics import diagnose_tab_issues
            diagnose_tab_issues(notebook)
            
            # 문제 해결 시도
            try:
                # 탭 강제 재생성 시도
                from utils.tab_diagnostics import force_refresh_report_tab
                if force_refresh_report_tab(notebook):
                    logger.info("보고서 탭 강제 재생성 성공")
                    # 재생성 후 UI 업데이트를 위한 약간의 지연
                    root.after(100, lambda: notebook.select(0))
                    root.update_idletasks()
                else:
                    logger.error("보고서 탭 강제 재생성 실패")
                    # 더 강력한 해결책 시도
                    try:
                        # 모든 탭 프레임 재생성
                        report_tab = ttk.Frame(notebook)
                        from ui.report_tab import create_report_tab
                        create_report_tab(report_tab)
                        notebook.add(report_tab, text=" 📊 보고서 생성 ")
                        notebook.select(0)
                        root.update_idletasks()
                    except Exception as recreate_error:
                        logger.error(f"탭 완전 재생성 실패: {recreate_error}")
            except Exception as tab_error:
                logger.error(f"탭 생성 시도 중 오류: {tab_error}")
                traceback.print_exc()
        
        # UI 업데이트 강제
        root.update_idletasks()
        # 약간의 지연 후 다시 한번 확인
        root.after(200, lambda: check_tab_after_delay(root, notebook))
        return True
    except Exception as e:
        logger.error(f"탭 가시성 확인 중 오류: {e}")
        traceback.print_exc()
        return False

def check_tab_after_delay(root, notebook):
    """지연 후 탭 상태 재확인"""
    try:
        tabs = notebook.tabs()
        if tabs:
            notebook.select(0)  # 첫 번째 탭 선택
            tab_frame = notebook.nametowidget(notebook.tabs()[0])
            
            # 자식 위젯이 여전히 없으면 report_tab 강제 재생성
            if len(tab_frame.winfo_children()) == 0:
                logger.warning("지연 후에도 보고서 탭이 비어 있음: 최종 재생성 시도")
                try:
                    from ui.report_tab import create_report_tab
                    create_report_tab(tab_frame)
                    root.update_idletasks()
                except Exception as e:
                    logger.error(f"최종 탭 내용 재생성 실패: {e}")
        
        logger.info("지연 후 탭 확인 완료")
    except Exception as e:
        logger.error(f"지연 후 탭 확인 중 오류: {e}")

def create_api_tab(parent):
    """Create the API management tab UI."""
    frame = ttk.Frame(parent)
    frame.pack(fill=tk.BOTH, expand=True)

    # Title
    ttk.Label(frame, text="API Management", font=("Arial", 14)).pack(pady=10)

    # API Key Input
    ttk.Label(frame, text="API Key:").pack(anchor="w", padx=10, pady=5)
    api_key_entry = ttk.Entry(frame, show="*", width=40)
    api_key_entry.pack(padx=10, pady=5)

    # Save Button
    def save_api_key():
        api_key = api_key_entry.get()
        if api_key:
            # Save the API key (placeholder logic)
            print(f"API Key saved: {api_key}")
            ttk.Label(frame, text="API Key saved successfully!", foreground="green").pack(pady=5)
        else:
            ttk.Label(frame, text="Please enter a valid API Key.", foreground="red").pack(pady=5)

    ttk.Button(frame, text="Save API Key", command=save_api_key).pack(pady=10)

    return frame
