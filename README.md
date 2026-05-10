# Studio Orot Multi-Bot

Discord + Gemini + Make.com 기반 SNS 콘텐츠 자동화 봇입니다.

이 버전은 **명령어로 채널 라우팅 설정**이 가능합니다.

## 빠른 실행

```bash
cp .env.example .env
docker compose up -d --build
docker logs -f studio_orot
```

`.env` 최소 설정:

```env
SINGLE_BOT_MODE=true
USE_MOCK_GEMINI=true
ENABLE_MAKE_WEBHOOK=false
TOKEN_DIRECTOR=디스코드_봇_토큰
```

## 기본 명령어

```text
!상태
!gemini테스트
```

## 채널 라우팅 명령어

형식:

```text
!채널설정 [카테고리] [단계] [#채널]
```

카테고리:

```text
건기식 / 식품 / 주방
```

단계:

```text
input     소싱/분석 결과
text      타겟 전략, 본문, 해시태그
short     숏폼/틱톡/릴스 결과
publish   최종 검수 및 발행 버튼
log       시스템 로그용
dashboard 대시보드용
meeting   봇 회의실용
```

예시:

```text
!채널설정 건기식 input #건기식-소싱-input
!채널설정 건기식 text #건기식-텍스트-pvw
!채널설정 건기식 short #건기식-숏폼-pvw
!채널설정 건기식 publish #건기식-송출-pgm

!채널설정 식품 input #식품-소싱-input
!채널설정 식품 text #식품-텍스트-pvw
!채널설정 식품 short #식품-숏폼-pvw
!채널설정 식품 publish #식품-송출-pgm

!채널설정 주방 input #주방-소싱-input
!채널설정 주방 text #주방-텍스트-pvw
!채널설정 주방 short #주방-숏폼-pvw
!채널설정 주방 publish #주방-송출-pgm
```

확인:

```text
!채널목록
```

초기화:

```text
!채널초기화 건기식
```

## 기획 실행

이미지 없이 테스트:

```text
!테스트기획 리빙 인스타 수납 https://link.coupang.com/test 좁은 원룸에 어울리는 베이지 수납함
```

이미지 첨부 테스트:

```text
!기획시작 리빙 인스타 수납 https://link.coupang.com/test 좁은 원룸용 베이지 수납장
```

`리빙`은 내부적으로 `주방` 카테고리로 라우팅됩니다.

## 저장 위치

채널 설정은 아래 파일에 저장됩니다.

```text
./data/channel_routes.json
```

컨테이너를 재시작해도 유지됩니다.

## Make.com

기본값:

```env
ENABLE_MAKE_WEBHOOK=false
```

이 상태에서는 발행 버튼을 눌러도 실제 전송하지 않고 payload preview만 보여줍니다.

## Discord Developer Portal 필수 설정

Bot 메뉴에서:

```text
MESSAGE CONTENT INTENT = ON
```

OAuth2 권한 추천:

```text
View Channels
Send Messages
Embed Links
Attach Files
Read Message History
Add Reactions
Use External Emojis
Use Application Commands
```
