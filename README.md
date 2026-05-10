# Studio Orot Multi-Bot

Discord + Gemini + Make.com 기반 SNS 콘텐츠 자동화 봇입니다.

기본값은 **로컬 테스트 모드**입니다.

- Make.com 전송은 기본 비활성화
- Gemini API Key가 없으면 mock 응답으로 테스트 가능
- 11개 토큰이 없어도 `SINGLE_BOT_MODE=true` 상태에서 1개 봇으로 전체 흐름 테스트 가능

---

## 1. 폴더 구조

```text
studio_orot_bot/
├── app/
│   ├── main.py
│   ├── agents/
│   │   └── persona_models.py
│   ├── bots/
│   │   ├── approval_view.py
│   │   ├── bot_factory.py
│   │   ├── registry.py
│   │   └── workflow.py
│   ├── config/
│   │   └── settings.py
│   ├── services/
│   │   ├── gemini_service.py
│   │   └── webhook_service.py
│   └── utils/
│       ├── discord_format.py
│       └── image_utils.py
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 2. 빠른 실행

```bash
cp .env.example .env
```

`.env`에 최소한 이것만 입력하세요.

```env
TOKEN_DIRECTOR=디스코드_봇_토큰
SINGLE_BOT_MODE=true
ENABLE_MAKE_WEBHOOK=false
USE_MOCK_GEMINI=true
```

실행:

```bash
docker compose up -d --build
```

로그 확인:

```bash
docker logs -f studio_orot
```

---

## 3. 디스코드 테스트 명령어

이미지 없이도 테스트 가능:

```text
!테스트기획 리빙 인스타 수납 https://link.coupang.com/test 좁은 원룸에 어울리는 베이지 수납함
```

이미지를 첨부해서 실제 흐름 테스트:

```text
!기획시작 리빙 인스타 수납 https://link.coupang.com/test 좁은 원룸에 어울리는 베이지 수납함
```

카테고리:

```text
건기식 / 식품 / 리빙
```

플랫폼:

```text
인스타 / 쓰레드 / 블로그 / 틱톡
```

---

## 4. Make.com 전송

기본값은 꺼져 있습니다.

```env
ENABLE_MAKE_WEBHOOK=false
```

이 상태에서는 버튼을 눌러도 실제 전송하지 않고, 디스코드에 payload preview만 보여줍니다.

실제 전송을 켜려면:

```env
ENABLE_MAKE_WEBHOOK=true
MAKE_WEBHOOK_URL=https://hook.make.com/your-webhook
```

---

## 5. Discord Developer Portal 설정

봇에서 반드시 켜야 합니다.

- Message Content Intent
- Server Members Intent는 필수 아님
- Presence Intent도 필수 아님

초대 URL 권한:

- Send Messages
- Read Message History
- Attach Files
- Use Slash Commands는 현재 필수 아님
- Embed Links

---

## 6. 모드 설명

### SINGLE_BOT_MODE=true

1개 봇으로 전체 직원 역할을 시뮬레이션합니다.  
로컬 테스트 추천 모드입니다.

### SINGLE_BOT_MODE=false

11개 봇 토큰으로 실제 멀티 봇을 동시에 실행합니다.
