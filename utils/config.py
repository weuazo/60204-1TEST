import json
import os

# 기본 설정
DEFAULT_CONFIG = {
    "api": {
        "timeout": 30,
        "max_retries": 3,
        "parallel_requests": 5
    },
    "ui": {
        "theme": "light",
        "font_size": 10
    },
    "files": {
        "output_dir": "output",
        "prompt_dir": "prompts",
        "data_dir": "data"
    },
    "standards": {
        "auto_detect": True,
        "use_ai_detection": True
    }
}

# 설정 파일 경로
CONFIG_FILE = os.path.join("config", "settings.json")

def load_config():
    """설정 로드"""
    if not os.path.exists(CONFIG_FILE):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
        
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # 누락된 설정 기본값으로 보완
            return _merge_configs(DEFAULT_CONFIG, config)
    except Exception as e:
        print(f"설정 로드 실패: {e}, 기본 설정 사용")
        return DEFAULT_CONFIG

def save_config(config):
    """설정 저장"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"설정 저장 실패: {e}")
        return False

def _merge_configs(default, user):
    """두 설정 병합 (기본값 + 사용자 설정)"""
    result = default.copy()
    
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
            
    return result

# 설정 인스턴스
config = load_config()
