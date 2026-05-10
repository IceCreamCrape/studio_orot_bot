# 공통 채널 라우팅 패치

이 패치는 아래 구조를 지원합니다.

```text
봇 회의 메시지 → #봇회의실
오류/시스템 로그 → #시스템-로그
대시보드 → #일일-대시보드
카테고리별 결과 → 각 카테고리 채널
```

## 적용 파일

아래 파일을 프로젝트에 덮어쓰기 하세요.

```text
app/services/channel_route_service.py
app/bots/multi_workflow.py
```

그리고 기존 `app/bots/bot_factory.py`의 `/admin 자동세팅` mapping에 아래 공통 항목을 추가하세요.

```python
"공통": {
    "dashboard": "일일-대시보드",
    "log": "시스템-로그",
    "meeting": "봇회의실",
},
```

## 사용 순서

```text
/admin 자동세팅
/admin 채널목록
/multi 테스트기획
```

`/admin 채널목록`에 아래가 보여야 합니다.

```text
[공통]
dashboard → #일일-대시보드
log → #시스템-로그
meeting → #봇회의실
```
