# Gemini 보고서 생성기

Gemini AI를 활용한 차세대 자동 보고서 생성 도구입니다.

## 🎯 새로운 Enhanced UI

**최신 업데이트**: 혁신적인 Enhanced UI가 도입되었습니다! 실시간 모니터링, 고급 오류 처리, 파일 분석 등 강력한 기능을 제공합니다.

### 🚀 Enhanced UI로 시작하기
```bash
python launch_enhanced_ui_as_default.py
```

> Enhanced UI에 대한 자세한 내용은 [README_ENHANCED.md](README_ENHANCED.md)를 참고하세요.

## 주요 기능

1. **Enhanced UI (신규 권장)**
   - 실시간 성능 모니터링 (메모리, 진행률, ETA)
   - 고급 오류 처리 및 자동 재시도
   - Excel 파일 사전 분석 및 최적화 권장
   - 색상 코딩된 로깅 시스템
   - 사용자 설정 지속성

2. 엑셀 템플릿 기반 보고서 생성
   - 설정 시트: 규격명, 버전, 검토자 등 기본 정보
   - 검토항목 시트: 검토할 항목과 내용
   - 프롬프트설정 시트: 사용할 프롬프트 설정

3. 프롬프트 관리
   - JSON 파일 기반 프롬프트 관리
   - 프롬프트 활성화/비활성화
   - 우선순위 설정
   - 프롬프트 세트 관리

4. API 연동
   - Gemini API 호출
   - 환경 변수 기반 API 키 관리
   - 에러 처리 및 재시도

## 설치 방법

1. Python 3.8 이상 설치

2. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

3. API 키 설정
   - 환경 변수 설정:
     ```bash
     # Windows
     set GEMINI_API_KEY=your_api_key
     
     # Linux/Mac
     export GEMINI_API_KEY=your_api_key
     ```
   - 또는 `.env` 파일 생성:
     ```
     GEMINI_API_KEY=your_api_key
     ```

## 사용 방법

### Enhanced UI 사용 (권장)
```bash
python launch_enhanced_ui_as_default.py
```

1. **파일 선택**: Excel 파일과 출력 경로 선택
2. **설정 조정**: 파일 크기에 맞는 최적 설정 선택
3. **실시간 모니터링**: 진행률과 메모리 사용량 확인
4. **로그 모니터링**: 상세한 작업 로그 실시간 확인
5. **결과 확인**: 처리 완료 후 결과 검토

### 기존 GUI 사용
```bash
python main.py
```

1. 템플릿 파일 준비
   - `data/templates/report_template.xlsx` 파일을 복사하여 사용
   - 필요한 항목과 내용 입력

2. 보고서 생성
   - 템플릿 파일 선택
   - 출력 경로 선택
   - 프롬프트 세트 선택
   - '보고서 생성' 버튼 클릭

## 프롬프트 커스터마이징

1. 프롬프트 파일 위치
   - `data/prompts/` 디렉토리에 JSON 파일로 저장

2. 프롬프트 파일 형식
```json
{
    "id": "prompt_id",
    "name": "프롬프트 이름",
    "description": "프롬프트 설명",
    "template": "프롬프트 템플릿\n{content} 등의 변수 사용 가능"
}
```

3. 프롬프트 세트 관리
   - 템플릿의 '프롬프트설정' 시트에서 관리
   - 활성화/비활성화 및 우선순위 설정

## 주의사항

1. API 키 보안
   - API 키는 절대 공개하지 마세요
   - 환경 변수나 `.env` 파일로 관리하세요

2. 템플릿 파일
   - 시트 이름과 열 구조를 유지하세요
   - 필수 항목을 반드시 입력하세요

3. 프롬프트 설정
   - 프롬프트 ID는 고유해야 합니다
   - 템플릿의 변수와 일치해야 합니다

## 문제 해결

1. API 오류
   - API 키가 올바르게 설정되었는지 확인
   - 인터넷 연결 상태 확인
   - API 할당량 확인

2. 파일 오류
   - 파일 경로가 올바른지 확인
   - 파일 권한 확인
   - 파일이 다른 프로그램에서 열려있지 않은지 확인

3. 프롬프트 오류
   - 프롬프트 파일 형식 확인
   - 프롬프트 ID 중복 확인
   - 템플릿 변수 확인

## 라이선스

MIT License
