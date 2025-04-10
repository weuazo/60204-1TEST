"""
애플리케이션 컨텍스트 모듈
앱 전체에서 사용되는 상태와 서비스를 중앙 관리하는 싱글톤 클래스
"""

import os
import json
import tkinter as tk
from typing import Dict, Any, Optional, Callable, List, Union, TypeVar, Type, cast

# 타입 별칭 정의
ConfigDict = Dict[str, Any]
ServiceDict = Dict[str, Any]
EventListenerDict = Dict[str, List[Callable[..., None]]]


class AppContext:
    """
    애플리케이션 상태를 중앙에서 관리하는 싱글톤 클래스
    의존성 주입 패턴을 구현하여 서비스와 컴포넌트 간 결합도 감소
    """
    _instance: Optional['AppContext'] = None
    
    @classmethod
    def get_instance(cls: Type['AppContext']) -> 'AppContext':
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = AppContext()
        return cls._instance
    
    def __init__(self) -> None:
        """생성자: 초기 상태 설정"""
        if AppContext._instance is not None:
            raise Exception("싱글톤 클래스는 직접 인스턴스화할 수 없습니다. get_instance()를 사용하세요.")
        
        # UI 상태
        self.ui_root: Optional[tk.Tk] = None
        self.status_message: str = "준비됨"
        
        # 설정 정보
        self.config: ConfigDict = {
            "api_key": os.environ.get("GEMINI_API_KEY", ""),
            "default_output_path": os.path.join("output"),
            "last_used_paths": {
                "source_doc": "",
                "target_doc": "",
                "output_dir": os.path.join("output")
            },
            "column_mapping": {},
            "ai_settings": {
                "temperature": 0.3,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 2048
            },
            "ui_preferences": {
                "theme": "light",
                "font_size": 10,
                "show_log": True
            }
        }
        
        # 서비스 컨테이너
        self.services: ServiceDict = {}
        
        # 이벤트 리스너
        self.event_listeners: EventListenerDict = {}
    
    # UI 관련 메서드
    def set_ui_root(self, root: tk.Tk) -> None:
        """UI 루트 윈도우 설정"""
        self.ui_root = root
    
    def get_ui_root(self) -> Optional[tk.Tk]:
        """UI 루트 윈도우 반환"""
        return self.ui_root
    
    def set_status(self, message: str) -> None:
        """상태 메시지 설정"""
        self.status_message = message
        # UI 상태바 업데이트 이벤트 발생
        self.trigger_event("status_changed", message)
    
    # 설정 관련 메서드
    def load_config(self) -> bool:
        """설정 파일에서 설정 로드"""
        config_path = os.path.join("data", "config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    # 설정 병합 (기존 구조 유지하면서 값만 업데이트)
                    self._merge_config(self.config, loaded_config)
                
                # 환경 변수의 API 키가 있으면 우선 사용
                env_api_key = os.environ.get("GEMINI_API_KEY")
                if env_api_key:
                    self.config["api_key"] = env_api_key
                
                return True
        except Exception as e:
            print(f"설정 로드 중 오류: {e}")
        return False
    
    def save_config(self) -> bool:
        """설정을 파일에 저장"""
        config_path = os.path.join("data", "config.json")
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # API 키는 설정 파일에 저장하지 않음
            config_to_save = self.config.copy()
            if "api_key" in config_to_save:
                config_to_save.pop("api_key")
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"설정 저장 중 오류: {e}")
        return False
    
    def _merge_config(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """설정 구조를 유지하면서 값만 병합"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # 둘 다 딕셔너리인 경우 재귀적으로 병합
                self._merge_config(target[key], value)
            else:
                # 그 외의 경우 값 덮어쓰기
                target[key] = value
    
    def get_config(self, key: Optional[str] = None, default: Any = None) -> Any:
        """설정값 반환"""
        if key is None:
            return self.config
        
        # 중첩 키를 지원하기 위한 로직 (예: "ai_settings.temperature")
        if "." in key:
            parts = key.split(".")
            value = self.config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """설정값 설정"""
        # 중첩 키를 지원하기 위한 로직
        if "." in key:
            parts = key.split(".")
            config = self.config
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                config = config[part]
            config[parts[-1]] = value
        else:
            self.config[key] = value
        
        # 설정 변경 이벤트 발생
        self.trigger_event("config_changed", key, value)
    
    def update_last_path(self, path_type: str, path: str) -> None:
        """최근 사용 경로 업데이트"""
        if path and path_type in ["source_doc", "target_doc", "output_dir"]:
            self.config["last_used_paths"][path_type] = path
            self.save_config()
    
    # API 키 관련 메서드
    def get_api_key(self) -> str:
        """API 키 반환"""
        return cast(str, self.config.get("api_key", ""))
    
    def set_api_key(self, api_key: str) -> None:
        """API 키 설정 및 환경 변수에도 적용"""
        self.config["api_key"] = api_key
        os.environ["GEMINI_API_KEY"] = api_key
        # API 키 변경 이벤트 발생
        self.trigger_event("api_key_changed", api_key)
    
    # 서비스 컨테이너 관련 메서드
    def register_service(self, name: str, service: Any) -> None:
        """서비스 등록"""
        self.services[name] = service
    
    def get_service(self, name: str) -> Any:
        """서비스 반환"""
        return self.services.get(name)
    
    # 이벤트 시스템 관련 메서드
    def add_event_listener(self, event_name: str, listener: Callable[..., None]) -> None:
        """이벤트 리스너 등록"""
        if event_name not in self.event_listeners:
            self.event_listeners[event_name] = []
        self.event_listeners[event_name].append(listener)
    
    def remove_event_listener(self, event_name: str, listener: Callable[..., None]) -> None:
        """이벤트 리스너 제거"""
        if event_name in self.event_listeners and listener in self.event_listeners[event_name]:
            self.event_listeners[event_name].remove(listener)
    
    def trigger_event(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """이벤트 발생"""
        if event_name in self.event_listeners:
            for listener in self.event_listeners[event_name]:
                try:
                    listener(*args, **kwargs)
                except Exception as e:
                    print(f"이벤트 리스너 실행 중 오류 ({event_name}): {e}")
                    
    # 편의 메서드
    def is_api_key_set(self) -> bool:
        """API 키가 설정되어 있는지 확인"""
        api_key = self.get_api_key()
        return bool(api_key and api_key.strip())