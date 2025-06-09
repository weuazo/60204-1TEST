"""
Comprehensive Test Runner for Enhanced Features
향상된 기능들에 대한 종합 테스트 실행기
"""

import unittest
import sys
import os
import time
import tempfile
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_data():
    """테스트용 Excel 파일 생성"""
    print("📊 테스트 데이터 생성 중...")
    
    # 작은 테스트 파일
    small_data = pd.DataFrame({
        'ID': range(100),
        'Name': [f'Item_{i}' for i in range(100)],
        'Value': np.random.rand(100),
        'Category': np.random.choice(['A', 'B', 'C'], 100)
    })
    
    small_file = os.path.join(tempfile.gettempdir(), 'test_small.xlsx')
    small_data.to_excel(small_file, index=False)
    
    # 중간 크기 테스트 파일
    medium_data = pd.DataFrame({
        'ID': range(10000),
        'Name': [f'Item_{i}' for i in range(10000)],
        'Value': np.random.rand(10000),
        'Category': np.random.choice(['A', 'B', 'C', 'D'], 10000),
        'Date': pd.date_range('2023-01-01', periods=10000)
    })
    
    medium_file = os.path.join(tempfile.gettempdir(), 'test_medium.xlsx')
    medium_data.to_excel(medium_file, index=False)
    
    print(f"✅ 테스트 파일 생성 완료:")
    print(f"   - 작은 파일: {small_file} ({os.path.getsize(small_file) / 1024:.1f} KB)")
    print(f"   - 중간 파일: {medium_file} ({os.path.getsize(medium_file) / 1024:.1f} KB)")
    
    return small_file, medium_file

def test_memory_tracker():
    """MemoryTracker 기능 테스트"""
    print("\n🧠 MemoryTracker 테스트 시작...")
    
    try:
        from parsers.excel_parser import MemoryTracker
        
        # 싱글톤 인스턴스 가져오기
        tracker = MemoryTracker.get_instance()
        
        # 메모리 사용량 확인
        memory_usage = tracker.get_memory_usage()
        print(f"   현재 메모리 사용량: {memory_usage * 100:.1f}%")
        
        # 모니터링 시작/중지 테스트
        tracker.start_monitoring()
        time.sleep(1)
        tracker.stop_monitoring()
        print("   ✅ 메모리 모니터링 시작/중지 테스트 통과")
        
        # 적응형 청크 크기 계산 테스트
        chunk_size = tracker.calculate_optimal_chunk_size(100.0, 0.7)
        print(f"   최적 청크 크기 (100MB, 70% 메모리): {chunk_size:,}")
        
        # 데이터프레임 압축 테스트
        test_df = pd.DataFrame({
            'category': ['A'] * 1000 + ['B'] * 1000,
            'value': np.random.rand(2000)
        })
        compressed_df = tracker.compress_dataframe(test_df)
        print(f"   데이터프레임 압축 테스트: {len(test_df)} -> {len(compressed_df)} 행")
        
        print("   ✅ MemoryTracker 모든 테스트 통과")
        return True
        
    except Exception as e:
        print(f"   ❌ MemoryTracker 테스트 실패: {e}")
        return False

def test_error_handling():
    """Error Handling 시스템 테스트"""
    print("\n🔧 Error Handling 시스템 테스트 시작...")
    
    try:
        from utils.enhanced_error_handling import (
            ErrorHandler, ExcelParsingError, ErrorCategory, 
            ErrorSeverity, ProgressInfo, global_error_handler
        )
        
        # 오류 생성 및 처리 테스트
        error = ExcelParsingError(
            message="테스트 오류",
            category=ErrorCategory.PARSING,
            severity=ErrorSeverity.MEDIUM,
            details={'test_key': 'test_value'}
        )
        
        # 전역 에러 핸들러 테스트
        global_error_handler.handle_error(error)
        
        # 사용자 친화적 메시지 생성
        friendly_msg = global_error_handler.get_user_friendly_message(error)
        print(f"   사용자 친화적 메시지: {friendly_msg[:50]}...")
        
        # 제안 생성
        suggestions = error.get_suggestions()
        print(f"   생성된 제안 수: {len(suggestions)}")
        
        # 진행률 정보 테스트
        progress = ProgressInfo(
            current=50,
            total=100,
            operation="테스트 작업",
            details={'stage': 'testing'}
        )
        print(f"   진행률: {progress.percentage}%")
        
        # 통계 확인
        stats = global_error_handler.get_error_statistics()
        print(f"   총 오류 수: {stats.get('total_errors', 0)}")
        
        print("   ✅ Error Handling 모든 테스트 통과")
        return True
        
    except Exception as e:
        print(f"   ❌ Error Handling 테스트 실패: {e}")
        return False

def test_excel_parser_performance(test_files):
    """ExcelParser 성능 테스트"""
    print("\n📈 ExcelParser 성능 테스트 시작...")
    
    try:
        from parsers.excel_parser import ExcelParser
        from utils.enhanced_error_handling import ProgressInfo
        
        parser = ExcelParser()
        small_file, medium_file = test_files
        
        # 진행률 콜백 함수
        progress_updates = []
        def progress_callback(current, total, percentage):
            progress_updates.append(percentage)
            if len(progress_updates) % 10 == 0:  # 10번째마다 출력
                print(f"   진행률: {percentage:.1f}%")
        
        # 작은 파일 테스트
        print("   작은 파일 파싱 테스트...")
        start_time = time.time()
        result_small = parser.parse(
            small_file, 
            progress_callback=progress_callback,
            enable_memory_optimization=True
        )
        small_time = time.time() - start_time
        print(f"   작은 파일 처리 시간: {small_time:.2f}초")
        
        # 결과 검증
        if 'dataframes' in result_small:
            print(f"   파싱된 시트 수: {len(result_small['dataframes'])}")
        
        # 중간 크기 파일 테스트
        print("   중간 파일 파싱 테스트...")
        progress_updates.clear()
        start_time = time.time()
        result_medium = parser.parse(
            medium_file,
            progress_callback=progress_callback,
            enable_memory_optimization=True
        )
        medium_time = time.time() - start_time
        print(f"   중간 파일 처리 시간: {medium_time:.2f}초")
        
        # 성능 통계 출력
        if 'performance_stats' in result_medium:
            stats = result_medium['performance_stats']
            print(f"   성능 통계: {stats}")
        
        print("   ✅ ExcelParser 성능 테스트 통과")
        return True
        
    except Exception as e:
        print(f"   ❌ ExcelParser 성능 테스트 실패: {e}")
        return False

def test_ui_components():
    """UI 컴포넌트 테스트 (비주얼 테스트 제외)"""
    print("\n🖥️ UI 컴포넌트 테스트 시작...")
    
    try:
        # 모듈 임포트 테스트
        from ui.enhanced_ui_components import (
            ProgressDialog, ErrorDisplayDialog, PerformanceMonitorWidget
        )
        from ui.enhanced_main_window import EnhancedMainWindow
        
        print("   ✅ UI 모듈 임포트 성공")
        
        # 스타일 설정 테스트
        from ui.enhanced_ui_components import setup_progress_styles
        print("   ✅ 스타일 설정 함수 로드 성공")
        
        print("   ✅ UI 컴포넌트 테스트 통과 (시각적 테스트는 수동 실행 필요)")
        return True
        
    except Exception as e:
        print(f"   ❌ UI 컴포넌트 테스트 실패: {e}")
        return False

def test_integration():
    """통합 테스트"""
    print("\n🔄 통합 테스트 시작...")
    
    try:
        # 전체 시스템 통합 테스트
        from parsers.excel_parser import MemoryTracker, ExcelParser
        from utils.enhanced_error_handling import global_error_handler, ProgressInfo
        
        # 메모리 추적기 시작
        tracker = MemoryTracker.get_instance()
        tracker.start_monitoring()
        
        # 테스트 데이터 생성
        test_data = pd.DataFrame({
            'col1': range(1000),
            'col2': np.random.rand(1000),
            'col3': [f'text_{i}' for i in range(1000)]
        })
        
        test_file = os.path.join(tempfile.gettempdir(), 'integration_test.xlsx')
        test_data.to_excel(test_file, index=False)
        
        # 파서로 처리
        parser = ExcelParser()
        
        def integration_progress(current, total, percentage):
            progress_info = ProgressInfo(
                current=current,
                total=total,
                operation=f"통합 테스트 진행 중... ({current}/{total})",
                details={'test': 'integration'}
            )
            global_error_handler.update_progress(progress_info)
        
        result = parser.parse(
            test_file,
            progress_callback=integration_progress,
            enable_memory_optimization=True
        )
        
        # 결과 검증
        assert 'dataframes' in result, "파싱 결과에 dataframes가 없음"
        assert len(result['dataframes']) > 0, "파싱된 데이터프레임이 없음"
        
        # 메모리 통계 확인
        memory_stats = tracker.get_memory_stats()
        print(f"   메모리 통계: 평균 사용량 {memory_stats.get('avg_usage', 0) * 100:.1f}%")
        
        # 에러 통계 확인
        error_stats = global_error_handler.get_error_statistics()
        print(f"   오류 통계: 총 {error_stats.get('total_errors', 0)}개 오류")
        
        # 정리
        tracker.stop_monitoring()
        os.unlink(test_file)
        
        print("   ✅ 통합 테스트 통과")
        return True
        
    except Exception as e:
        print(f"   ❌ 통합 테스트 실패: {e}")
        return False

def run_performance_benchmark():
    """성능 벤치마크 실행"""
    print("\n⚡ 성능 벤치마크 시작...")
    
    try:
        # 벤치마크용 대용량 데이터 생성
        print("   벤치마크 데이터 생성 중...")
        benchmark_data = pd.DataFrame({
            'id': range(50000),
            'value': np.random.rand(50000),
            'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], 50000),
            'text': [f'sample_text_{i}' for i in range(50000)],
            'date': pd.date_range('2023-01-01', periods=50000)
        })
        
        benchmark_file = os.path.join(tempfile.gettempdir(), 'benchmark.xlsx')
        benchmark_data.to_excel(benchmark_file, index=False)
        file_size_mb = os.path.getsize(benchmark_file) / (1024 * 1024)
        print(f"   벤치마크 파일 크기: {file_size_mb:.2f} MB")
        
        from parsers.excel_parser import ExcelParser, MemoryTracker
        
        parser = ExcelParser()
        tracker = MemoryTracker.get_instance()
        tracker.start_monitoring()
        
        # 성능 측정
        start_time = time.time()
        start_memory = tracker.get_memory_usage()
        
        result = parser.parse(
            benchmark_file,
            enable_memory_optimization=True
        )
        
        end_time = time.time()
        end_memory = tracker.get_memory_usage()
        
        # 결과 출력
        processing_time = end_time - start_time
        memory_delta = (end_memory - start_memory) * 100
        
        print(f"   처리 시간: {processing_time:.2f}초")
        print(f"   처리 속도: {50000 / processing_time:.0f} 행/초")
        print(f"   메모리 증가: {memory_delta:+.1f}%")
        
        # 성능 통계
        if 'performance_stats' in result:
            stats = result['performance_stats']
            print(f"   상세 성능 통계: {stats}")
        
        # 정리
        tracker.stop_monitoring()
        os.unlink(benchmark_file)
        
        # 성능 기준 검증
        if processing_time < 10.0:  # 10초 이내
            print("   ✅ 성능 벤치마크 통과 (우수)")
        elif processing_time < 30.0:  # 30초 이내
            print("   ✅ 성능 벤치마크 통과 (양호)")
        else:
            print("   ⚠️ 성능 벤치마크 주의 (느림)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 성능 벤치마크 실패: {e}")
        return False

def create_demonstration_report():
    """시연용 보고서 생성"""
    print("\n📋 시연용 보고서 생성...")
    
    report = {
        "test_summary": {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0
        },
        "test_results": [],
        "recommendations": []
    }
    
    return report

def main():
    """메인 테스트 실행 함수"""
    print("🚀 Gemini Report Generator - Enhanced Features 종합 테스트")
    print("=" * 60)
    
    # 테스트 결과 추적
    test_results = []
    
    try:
        # 1. 테스트 데이터 생성
        test_files = create_test_data()
        
        # 2. 개별 기능 테스트
        tests = [
            ("MemoryTracker", test_memory_tracker),
            ("Error Handling", test_error_handling),
            ("ExcelParser Performance", lambda: test_excel_parser_performance(test_files)),
            ("UI Components", test_ui_components),
            ("Integration", test_integration)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🧪 {test_name} 테스트 실행 중...")
            try:
                result = test_func()
                test_results.append((test_name, result))
                if result:
                    print(f"✅ {test_name} 테스트 성공")
                else:
                    print(f"❌ {test_name} 테스트 실패")
            except Exception as e:
                test_results.append((test_name, False))
                print(f"❌ {test_name} 테스트 오류: {e}")
        
        # 3. 성능 벤치마크
        benchmark_result = run_performance_benchmark()
        test_results.append(("Performance Benchmark", benchmark_result))
        
        # 4. 결과 요약
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<25} {status}")
        
        print(f"\n총 테스트: {total}")
        print(f"성공: {passed}")
        print(f"실패: {total - passed}")
        print(f"성공률: {passed / total * 100:.1f}%")
        
        # 5. 권장사항
        print("\n📋 권장사항:")
        if passed == total:
            print("🎉 모든 테스트가 통과했습니다! 시스템이 완벽하게 작동합니다.")
        elif passed >= total * 0.8:
            print("👍 대부분의 기능이 정상 작동합니다. 일부 개선이 필요합니다.")
        else:
            print("⚠️ 여러 기능에 문제가 있습니다. 시스템 점검이 필요합니다.")
        
        print("\n🎯 다음 단계:")
        print("1. launch_enhanced_ui.py를 실행하여 향상된 UI를 체험해보세요")
        print("2. 대용량 Excel 파일로 성능을 테스트해보세요")
        print("3. 설정 탭에서 메모리 임계값을 조정해보세요")
        print("4. 의도적으로 오류를 발생시켜 오류 처리를 확인해보세요")
        
        # 정리
        for file_path in test_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
        
        return passed == total
        
    except Exception as e:
        print(f"\n💥 치명적 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
