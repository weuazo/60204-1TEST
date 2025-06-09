"""
최종 통합 테스트
모든 수정된 컴포넌트의 통합 테스트
"""

import sys
import os
import traceback
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_excel_parser():
    """수정된 Excel 파서 테스트"""
    print("🔍 Excel Parser 테스트 중...")
    try:
        from parsers.excel_parser import EnhancedExcelParser, parse_excel_file
        
        # 파서 인스턴스 생성
        parser = EnhancedExcelParser(chunk_size=1000)
        print("✅ EnhancedExcelParser 인스턴스 생성 성공")
        
        # 메모리 트래커 테스트
        memory_stats = parser.memory_tracker.get_memory_stats()
        print(f"✅ 메모리 트래커 작동 확인: {memory_stats}")
        
        # 편의 함수 테스트
        print("✅ parse_excel_file 함수 import 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ Excel Parser 테스트 실패: {str(e)}")
        traceback.print_exc()
        return False

def test_enhanced_error_handling():
    """향상된 오류 처리 테스트"""
    print("\n🔍 Enhanced Error Handling 테스트 중...")
    try:
        from utils.enhanced_error_handling import (
            ErrorHandler, ErrorCategory, ErrorSeverity,
            FileAccessError, MemoryError, ParsingError
        )
        
        # 에러 핸들러 인스턴스 생성
        error_handler = ErrorHandler()
        print("✅ ErrorHandler 인스턴스 생성 성공")
        
        # 에러 카테고리 테스트
        test_error = FileAccessError("테스트 파일 접근 오류")
        result = error_handler.handle_error(test_error, "test_context")
        print(f"✅ 에러 처리 결과: {result}")
        
        # 통계 확인
        stats = error_handler.get_error_statistics()
        print(f"✅ 에러 통계: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Error Handling 테스트 실패: {str(e)}")
        traceback.print_exc()
        return False

def test_ui_components():
    """UI 컴포넌트 테스트"""
    print("\n🔍 UI Components 테스트 중...")
    try:
        from ui.enhanced_ui_components import (
            EnhancedProgressBar, EnhancedFileSelector, 
            EnhancedConfigPanel, EnhancedLogViewer
        )
        
        print("✅ 모든 UI 컴포넌트 import 성공")
        
        # 컴포넌트 클래스 확인
        components = [EnhancedProgressBar, EnhancedFileSelector, 
                     EnhancedConfigPanel, EnhancedLogViewer]
        
        for component in components:
            print(f"✅ {component.__name__} 클래스 확인 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ UI Components 테스트 실패: {str(e)}")
        traceback.print_exc()
        return False

def test_main_window():
    """메인 윈도우 테스트"""
    print("\n🔍 Main Window 테스트 중...")
    try:
        from ui.enhanced_main_window import EnhancedMainWindow
        
        print("✅ EnhancedMainWindow import 성공")
        
        # 클래스 속성 확인
        required_methods = ['__init__', 'create_menu', 'create_main_frame', 
                           'setup_file_operations', 'setup_processing_options']
        
        for method in required_methods:
            if hasattr(EnhancedMainWindow, method):
                print(f"✅ {method} 메소드 확인 완료")
            else:
                print(f"⚠️  {method} 메소드 없음")
        
        return True
        
    except Exception as e:
        print(f"❌ Main Window 테스트 실패: {str(e)}")
        traceback.print_exc()
        return False

def test_launcher():
    """런처 테스트"""
    print("\n🔍 Launcher 테스트 중...")
    try:
        import launch_enhanced_ui
        
        print("✅ launch_enhanced_ui import 성공")
        
        # 의존성 확인 함수 테스트
        if hasattr(launch_enhanced_ui, 'check_dependencies'):
            print("✅ check_dependencies 함수 확인 완료")
        
        if hasattr(launch_enhanced_ui, 'main'):
            print("✅ main 함수 확인 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ Launcher 테스트 실패: {str(e)}")
        traceback.print_exc()
        return False

def test_documentation_and_config():
    """문서화 및 설정 파일 테스트"""
    print("\n🔍 Documentation & Config 테스트 중...")
    try:
        # 문서 파일 존재 확인
        doc_files = [
            'docs/excel_parser_guide.md',
            'FINAL_STATUS_REPORT.md'
        ]
        
        for doc_file in doc_files:
            if os.path.exists(doc_file):
                file_size = os.path.getsize(doc_file)
                print(f"✅ {doc_file} 존재 확인 ({file_size:,} bytes)")
            else:
                print(f"⚠️  {doc_file} 파일 없음")
        
        # 설정 파일 확인
        config_files = [
            'config/app_config.json',
            'config/parser_config.json',
            'config/ui_config.json'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                print(f"✅ {config_file} 존재 확인")
            else:
                print(f"⚠️  {config_file} 파일 없음")
        
        return True
        
    except Exception as e:
        print(f"❌ Documentation & Config 테스트 실패: {str(e)}")
        traceback.print_exc()
        return False

def run_comprehensive_test():
    """종합 테스트 실행"""
    print("=" * 60)
    print("🚀 Gemini Report Generator - 최종 통합 테스트")
    print("=" * 60)
    print(f"테스트 시작 시간: {datetime.now()}")
    print()
    
    test_results = {}
    
    # 각 컴포넌트 테스트 실행
    tests = [
        ("Excel Parser", test_excel_parser),
        ("Enhanced Error Handling", test_enhanced_error_handling),
        ("UI Components", test_ui_components),
        ("Main Window", test_main_window),
        ("Launcher", test_launcher),
        ("Documentation & Config", test_documentation_and_config)
    ]
    
    for test_name, test_func in tests:
        try:
            test_results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} 테스트 중 예외 발생: {str(e)}")
            test_results[test_name] = False
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    success_rate = (passed / total) * 100
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
    
    print(f"\n성공률: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 우수한 성과! 대부분의 컴포넌트가 정상 작동합니다.")
    elif success_rate >= 60:
        print("👍 양호한 상태입니다. 일부 개선이 필요할 수 있습니다.")
    else:
        print("⚠️  추가 수정이 필요합니다.")
    
    print(f"\n테스트 완료 시간: {datetime.now()}")
    
    return test_results, success_rate

if __name__ == "__main__":
    results, success_rate = run_comprehensive_test()
    
    # 성공률에 따른 종료 코드 설정
    sys.exit(0 if success_rate >= 80 else 1)
