from .matcher_base import DocumentMatcher
from .basic_matcher import BasicMatcher
from .ai_matcher import AIMatcher

def create_matcher(mode="basic"):  # 기본값이 "basic"으로 설정되어 있음 (필요하면 변경)
    """매칭 모드에 따른 매처 클래스 인스턴스 생성"""
    if mode == "basic":
        return BasicMatcher()
    elif mode == "ai":
        return AIMatcher()
    else:
        raise ValueError(f"지원되지 않는 매칭 모드: {mode}")
