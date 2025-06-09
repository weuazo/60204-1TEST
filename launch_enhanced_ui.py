"""
Enhanced UI Launcher
향상된 UI 실행을 위한 런처 스크립트
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """필수 의존성 확인"""
    missing_deps = []
    
    try:
        import pandas
        del pandas  # 사용 후 삭제하여 경고 방지
    except ImportError:
        missing_deps.append("pandas")
    
    try:
        import openpyxl
        del openpyxl  # 사용 후 삭제하여 경고 방지
    except ImportError:
        missing_deps.append("openpyxl")
    
    try:
        import psutil
        del psutil  # 사용 후 삭제하여 경고 방지
    except ImportError:
        missing_deps.append("psutil")
    
    return missing_deps

def main():
    """메인 실행 함수"""
    # 의존성 확인
    missing_deps = check_dependencies()
    if missing_deps:
        root = tk.Tk()
        root.withdraw()  # 메인 윈도우 숨기기
        
        deps_text = ", ".join(missing_deps)
        messagebox.showerror(
            "의존성 오류",
            f"다음 패키지들이 설치되지 않았습니다:\\n{deps_text}\\n\\n"
            f"다음 명령어로 설치해주세요:\\n"
            f"pip install {' '.join(missing_deps)}"
        )
        return
    
    try:
        # 향상된 메인 윈도우 임포트 및 실행
        from ui.enhanced_main_window import EnhancedMainWindow
        
        app = EnhancedMainWindow()
        app.run()
        
    except ImportError as e:
        # 향상된 UI를 사용할 수 없는 경우 기본 UI로 폴백
        print(f"향상된 UI 로드 실패: {e}")
        print("기본 UI로 실행합니다...")
        
        try:
            from ui.main_window import MainWindow
            app = MainWindow()
            app.run()
        except Exception as e:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("실행 오류", f"애플리케이션 실행 실패:\\n{str(e)}")
    
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("실행 오류", f"예상치 못한 오류 발생:\\n{str(e)}")

if __name__ == "__main__":
    main()
