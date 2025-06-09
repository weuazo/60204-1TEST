"""
고급 오류 처리 및 사용자 피드백 시스템
"""
import traceback
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, Callable
from utils.logger import get_logger

logger = get_logger("error_handler")

class ErrorSeverity(Enum):
    """오류 심각도 레벨"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """오류 카테고리"""
    FILE_ACCESS = "file_access"
    MEMORY = "memory"
    PARSING = "parsing"
    NETWORK = "network"
    VALIDATION = "validation"
    PERMISSION = "permission"
    SYSTEM = "system"
    USER_INPUT = "user_input"

class ProgressInfo:
    """진행 상황 정보"""
    def __init__(self, current: int = 0, total: int = 0, message: str = "", 
                 stage: str = "", percentage: float = 0.0):
        self.current = current
        self.total = total
        self.message = message
        self.stage = stage
        self.percentage = percentage
        self.timestamp = datetime.now()
    
    def to_dict(self):
        return {
            'current': self.current,
            'total': self.total,
            'message': self.message,
            'stage': self.stage,
            'percentage': self.percentage,
            'timestamp': self.timestamp.isoformat()
        }

class ExcelParsingError(Exception):
    """엑셀 파싱 관련 오류"""
    def __init__(self, message: str, error_code: str = None, 
                 category: ErrorCategory = ErrorCategory.PARSING,
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 recoverable: bool = True,
                 suggestions: list = None):
        super().__init__(message)
        self.error_code = error_code
        self.category = category
        self.severity = severity
        self.recoverable = recoverable
        self.suggestions = suggestions or []
        self.timestamp = datetime.now()
        
    def to_dict(self):
        return {
            'message': str(self),
            'error_code': self.error_code,
            'category': self.category.value,
            'severity': self.severity.value,
            'recoverable': self.recoverable,
            'suggestions': self.suggestions,
            'timestamp': self.timestamp.isoformat()
        }

class FileAccessError(Exception):
    """파일 접근 관련 오류"""
    def __init__(self, message: str, file_path: str = None, 
                 category: ErrorCategory = ErrorCategory.FILE_ACCESS,
                 severity: ErrorSeverity = ErrorSeverity.ERROR):
        super().__init__(message)
        self.file_path = file_path
        self.category = category
        self.severity = severity
        self.timestamp = datetime.now()
        
    def get_user_friendly_message(self):
        """사용자 친화적 오류 메시지 반환"""
        if self.file_path:
            return f"파일 접근 오류: {self.file_path} - {str(self)}"
        return f"파일 접근 오류: {str(self)}"

class MemoryError(Exception):
    """메모리 관련 오류"""
    def __init__(self, message: str, memory_usage: float = None,
                 category: ErrorCategory = ErrorCategory.MEMORY,
                 severity: ErrorSeverity = ErrorSeverity.ERROR):
        super().__init__(message)
        self.memory_usage = memory_usage
        self.category = category
        self.severity = severity
        self.timestamp = datetime.now()
        
    def get_user_friendly_message(self):
        """사용자 친화적 오류 메시지 반환"""
        if self.memory_usage:
            return f"메모리 오류: 사용량 {self.memory_usage:.1f}MB - {str(self)}"
        return f"메모리 오류: {str(self)}"

class ParsingError(Exception):
    """파싱 관련 오류"""
    def __init__(self, message: str, file_path: str = None, line_number: int = None,
                 category: ErrorCategory = ErrorCategory.PARSING,
                 severity: ErrorSeverity = ErrorSeverity.ERROR):
        super().__init__(message)
        self.file_path = file_path
        self.line_number = line_number
        self.category = category
        self.severity = severity
        self.timestamp = datetime.now()
        
    def get_user_friendly_message(self):
        """사용자 친화적 오류 메시지 반환"""
        location = ""
        if self.file_path:
            location += f"파일: {self.file_path}"
        if self.line_number:
            location += f", 라인: {self.line_number}"
        if location:
            return f"파싱 오류 ({location}) - {str(self)}"
        return f"파싱 오류: {str(self)}"

class ErrorHandler:
    """통합 오류 처리 시스템"""
    
    def __init__(self):
        self.error_history = []
        self.progress_callbacks = []
        self.error_callbacks = []
        self.max_history = 100
        
    def handle_error(self, error: Exception, context: str = "", 
                    user_message: str = None, suggestions: list = None) -> Dict[str, Any]:
        """오류 처리 및 사용자 피드백 생성"""
        
        # 오류 분석
        error_info = self._analyze_error(error, context)
        
        # 사용자 친화적 메시지 생성
        if user_message is None:
            user_message = self._generate_user_message(error_info)
        
        # 해결 방안 제안
        if suggestions is None:
            suggestions = self._generate_suggestions(error_info)
        
        # 오류 기록
        error_record = {
            'timestamp': datetime.now(),
            'error_type': type(error).__name__,
            'message': str(error),
            'context': context,
            'user_message': user_message,
            'suggestions': suggestions,
            'error_info': error_info,
            'traceback': traceback.format_exc()
        }
        
        self.error_history.append(error_record)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        # 로깅
        self._log_error(error_record)
        
        # 콜백 호출
        self._notify_error_callbacks(error_record)
        
        return error_record
    
    def _analyze_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """오류 분석"""
        error_info = {
            'category': ErrorCategory.SYSTEM,
            'severity': ErrorSeverity.ERROR,
            'recoverable': True,
            'error_code': None
        }
        
        error_msg = str(error).lower()
        
        # 파일 접근 오류
        if any(keyword in error_msg for keyword in ['no such file', 'permission denied', 'access denied']):
            error_info.update({
                'category': ErrorCategory.FILE_ACCESS,
                'error_code': 'FILE_ACCESS_ERROR'
            })
        
        # 메모리 오류
        elif any(keyword in error_msg for keyword in ['memory', 'out of memory', 'memoryerror']):
            error_info.update({
                'category': ErrorCategory.MEMORY,
                'severity': ErrorSeverity.CRITICAL,
                'error_code': 'MEMORY_ERROR'
            })
        
        # 파싱 오류
        elif any(keyword in error_msg for keyword in ['parse', 'format', 'corrupt', 'invalid']):
            error_info.update({
                'category': ErrorCategory.PARSING,
                'error_code': 'PARSING_ERROR'
            })
        
        # 네트워크 오류
        elif any(keyword in error_msg for keyword in ['network', 'connection', 'timeout']):
            error_info.update({
                'category': ErrorCategory.NETWORK,
                'error_code': 'NETWORK_ERROR'
            })
        
        # 권한 오류
        elif any(keyword in error_msg for keyword in ['permission', 'unauthorized', 'forbidden']):
            error_info.update({
                'category': ErrorCategory.PERMISSION,
                'error_code': 'PERMISSION_ERROR'
            })
        
        return error_info
    
    def _generate_user_message(self, error_info: Dict[str, Any]) -> str:
        """사용자 친화적 오류 메시지 생성"""
        category = error_info['category']
        
        messages = {
            ErrorCategory.FILE_ACCESS: "파일에 접근할 수 없습니다. 파일 경로와 권한을 확인해주세요.",
            ErrorCategory.MEMORY: "메모리가 부족합니다. 다른 프로그램을 종료하거나 더 작은 파일로 시도해주세요.",
            ErrorCategory.PARSING: "파일 형식에 문제가 있습니다. 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다.",
            ErrorCategory.NETWORK: "네트워크 연결에 문제가 있습니다. 인터넷 연결을 확인해주세요.",
            ErrorCategory.PERMISSION: "권한이 부족합니다. 관리자 권한으로 실행하거나 파일 권한을 확인해주세요.",
            ErrorCategory.VALIDATION: "입력 데이터에 문제가 있습니다. 데이터 형식을 확인해주세요.",
            ErrorCategory.USER_INPUT: "입력 값이 올바르지 않습니다. 입력 내용을 다시 확인해주세요."
        }
        
        return messages.get(category, "예상치 못한 오류가 발생했습니다.")
    
    def _generate_suggestions(self, error_info: Dict[str, Any]) -> list:
        """해결 방안 제안 생성"""
        category = error_info['category']
        
        suggestions_map = {
            ErrorCategory.FILE_ACCESS: [
                "파일 경로가 올바른지 확인하세요",
                "파일이 다른 프로그램에서 사용 중이지 않은지 확인하세요",
                "파일 읽기 권한이 있는지 확인하세요"
            ],
            ErrorCategory.MEMORY: [
                "더 작은 파일로 나누어 처리해보세요",
                "다른 프로그램을 종료하여 메모리를 확보하세요",
                "청크 단위 처리 옵션을 사용해보세요"
            ],
            ErrorCategory.PARSING: [
                "파일이 손상되지 않았는지 확인하세요",
                "지원되는 파일 형식(.xlsx, .xls)인지 확인하세요",
                "다른 엑셀 프로그램에서 파일을 열어 확인해보세요"
            ],
            ErrorCategory.NETWORK: [
                "인터넷 연결을 확인하세요",
                "방화벽 설정을 확인하세요",
                "잠시 후 다시 시도해보세요"
            ],
            ErrorCategory.PERMISSION: [
                "관리자 권한으로 프로그램을 실행하세요",
                "파일 및 폴더 권한을 확인하세요",
                "파일이 읽기 전용이 아닌지 확인하세요"
            ]
        }
        
        return suggestions_map.get(category, ["프로그램을 재시작해보세요", "기술 지원팀에 문의하세요"])
    
    def _log_error(self, error_record: Dict[str, Any]):
        """오류 로깅"""
        severity = error_record['error_info'].get('severity', ErrorSeverity.ERROR)
        
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical Error: {error_record['message']}")
        elif severity == ErrorSeverity.ERROR:
            logger.error(f"Error: {error_record['message']}")
        elif severity == ErrorSeverity.WARNING:
            logger.warning(f"Warning: {error_record['message']}")
        else:
            logger.info(f"Info: {error_record['message']}")
    
    def _notify_error_callbacks(self, error_record: Dict[str, Any]):
        """오류 콜백 알림"""
        for callback in self.error_callbacks:
            try:
                callback(error_record)
            except Exception as e:
                logger.error(f"오류 콜백 실행 중 오류: {e}")
    
    def register_progress_callback(self, callback: Callable[[ProgressInfo], None]):
        """진행 상황 콜백 등록"""
        self.progress_callbacks.append(callback)
    
    def register_error_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """오류 콜백 등록"""
        self.error_callbacks.append(callback)
    
    def update_progress(self, current: int, total: int, message: str = "", stage: str = ""):
        """진행 상황 업데이트"""
        percentage = (current / total * 100) if total > 0 else 0
        progress_info = ProgressInfo(current, total, message, stage, percentage)
        
        logger.debug(f"Progress: {stage} - {message} ({current}/{total}, {percentage:.1f}%)")
        
        for callback in self.progress_callbacks:
            try:
                callback(progress_info)
            except Exception as e:
                logger.error(f"진행 상황 콜백 실행 중 오류: {e}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """오류 통계 반환"""
        if not self.error_history:
            return {'total_errors': 0}
        
        categories = {}
        severities = {}
        
        for error in self.error_history:
            category = error['error_info'].get('category', 'unknown')
            severity = error['error_info'].get('severity', 'unknown')
            
            categories[category] = categories.get(category, 0) + 1
            severities[severity] = severities.get(severity, 0) + 1
        
        return {
            'total_errors': len(self.error_history),
            'categories': categories,
            'severities': severities,
            'recent_errors': self.error_history[-5:] if len(self.error_history) >= 5 else self.error_history
        }
    
    def clear_history(self):
        """오류 히스토리 정리"""
        self.error_history.clear()
        logger.info("오류 히스토리 정리 완료")

# 전역 오류 처리기 인스턴스
global_error_handler = ErrorHandler()
