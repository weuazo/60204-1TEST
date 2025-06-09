#!/usr/bin/env python3
"""
Launch Enhanced UI as Default
Enhanced UI를 기본 UI로 실행하는 스크립트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Enhanced UI를 메인 UI로 실행"""
    try:
        # Enhanced UI 실행
        from ui.enhanced_main_window import EnhancedMainWindow
        
        print("🚀 Gemini Report Generator (Enhanced UI) 시작...")
        app = EnhancedMainWindow()
        app.run()
        
    except ImportError as e:
        print(f"❌ Enhanced UI 모듈 로드 실패: {e}")
        print("📋 Fallback: 기존 GUI로 실행...")
        
        try:
            # Fallback to original GUI
            from main import main as original_main
            original_main()
        except Exception as fallback_error:
            print(f"❌ Fallback도 실패: {fallback_error}")
            
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
        print("💡 launch_enhanced_ui.py를 대신 사용해보세요.")

if __name__ == "__main__":
    main()
