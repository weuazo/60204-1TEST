"""
탭 초기화 및 표시 문제 진단을 위한 유틸리티 모듈
"""
import tkinter as tk
import traceback
import sys
from utils.logger import logger
import importlib

def diagnose_tab_issues(notebook):
    """탭 초기화 및 표시 문제 진단"""
    try:
        logger.info("탭 진단 시작...")
        
        # 노트북에 있는 모든 탭 정보 수집
        tabs = notebook.tabs()
        logger.info(f"노트북 탭 수: {len(tabs)}")
        
        for i, tab_id in enumerate(tabs):
            tab_text = notebook.tab(tab_id, "text")
            logger.info(f"탭 {i}: ID={tab_id}, 텍스트={tab_text}")
            
            # 탭의 자식 위젯 확인
            tab_frame = notebook.nametowidget(tab_id)
            children = tab_frame.winfo_children()
            logger.info(f"  - 자식 위젯 수: {len(children)}")
            
            for j, child in enumerate(children):
                logger.info(f"    - 자식 {j}: 클래스={child.__class__.__name__}, 표시={child.winfo_ismapped()}")
                
        # 노트북 상태 확인
        logger.info(f"현재 선택된 탭: {notebook.select()}")
        logger.info(f"노트북 표시 상태: {notebook.winfo_ismapped()}")
        
        return True
    except Exception as e:
        logger.error(f"탭 진단 중 오류: {e}")
        traceback.print_exc()
        return False

def check_report_tab_widgets(tab_frame):
    """보고서 탭의 주요 위젯 확인"""
    try:
        # 주요 위젯 확인 (예: LabelFrame, Button 등)
        found_widgets = {
            'label_frames': 0,
            'buttons': 0,
            'entries': 0,
            'treeviews': 0
        }
        
        def count_widgets(widget):
            """위젯과 그 자식들의 유형별 개수 계산"""
            if isinstance(widget, tk.ttk.LabelFrame):
                found_widgets['label_frames'] += 1
            elif isinstance(widget, tk.ttk.Button):
                found_widgets['buttons'] += 1
            elif isinstance(widget, tk.ttk.Entry):
                found_widgets['entries'] += 1
            elif isinstance(widget, tk.ttk.Treeview):
                found_widgets['treeviews'] += 1
                
            # 자식 위젯들도 확인
            for child in widget.winfo_children():
                count_widgets(child)
        
        # 모든 자식 위젯 확인
        for child in tab_frame.winfo_children():
            count_widgets(child)
            
        # 결과 기록
        logger.info(f"보고서 탭 위젯 구성: {found_widgets}")
        
        # 최소 필요한 위젯이 있는지 확인
        if (found_widgets['label_frames'] >= 4 and  # 파일 선택, AI 분석, 수동 조정, 미리보기 등
            found_widgets['buttons'] >= 3 and       # 찾아보기, 분석, 생성 버튼 등
            found_widgets['treeviews'] >= 1):       # 미리보기 트리뷰
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"위젯 확인 중 오류: {e}")
        return False

def force_refresh_report_tab(notebook):
    """보고서 탭 강제 새로고침"""
    try:
        logger.info("보고서 탭 강제 새로고침 시도...")
        
        # 첫 번째 탭이 보고서 탭인지 확인
        if len(notebook.tabs()) > 0:
            tab_id = notebook.tabs()[0]
            tab_frame = notebook.nametowidget(tab_id)
            
            # 현재 상태 저장
            notebook_master = notebook.master
            root = notebook.winfo_toplevel()
            
            # 기존 위젯 제거 전 다른 탭 선택
            if len(notebook.tabs()) > 1:
                notebook.select(1)  # 임시로 다른 탭 선택
            
            # 기존 위젯 제거
            for widget in tab_frame.winfo_children():
                widget.destroy()
            
            # 탭 완전히 제거
            if len(notebook.tabs()) > 1:
                try:
                    notebook.forget(0)  # 첫 번째 탭 제거
                    
                    # 새 프레임 생성
                    new_frame = tk.ttk.Frame(notebook)
                    
                    # 새 탭 삽입
                    notebook.insert(0, new_frame, text=" 📊 보고서 생성 ")
                    tab_frame = new_frame
                    
                    logger.info("보고서 탭 재생성 성공 (탭 교체)")
                except Exception as e:
                    logger.error(f"탭 교체 실패: {e}")
            
            # 보고서 탭 다시 생성
            try:
                from ui.report_tab import create_report_tab
                # 한 번 더 확인하여 자식 위젯이 없으면 생성
                if len(tab_frame.winfo_children()) == 0:
                    create_report_tab(tab_frame)
                
                # 강제로 업데이트 적용
                tab_frame.update_idletasks()
                root.update_idletasks()
                
                # 보고서 탭 선택
                notebook.select(0)
                
                logger.info("보고서 탭 새로고침 성공")
                return True
            except Exception as tab_error:
                logger.error(f"보고서 탭 재생성 중 오류: {tab_error}")
                traceback.print_exc()
                return False
        else:
            logger.error("노트북에 탭이 없습니다.")
            return False
    except Exception as e:
        logger.error(f"보고서 탭 새로고침 중 오류: {e}")
        traceback.print_exc()
        return False
