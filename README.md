# QuantumBE

> 이 프로젝트는 백엔드 서버 및 LLM 서빙에 대한 기초 학습을 위해 진행되었음
> <br>
> 클라우드 서비스에 임베딩 기반 검색 솔루션을 삽입한 형태
> <br>
> 호스팅 서버는 MSA 형태로 분리하여 HTTP 통신으로 데이터 공유
> <br>
> 로컬 서버에서 구동하는 걸 전제로 설계
> <br>
> 시스템 구성
> - CPU: AMD Ryzen 5 5600G with Radeon Graphics
> - MEM: 32GB
> - GPU: NVIDIA GeForce GTX 1650 4GB

---

## Tech Stack

| 분류 | 기술 |
|------|------|
| **Framework** | FastAPI |
| **Auth** | fastapi-login (JWT / Cookie 기반) |
| **ORM** | SQLAlchemy |
| **DB** | MySQL, SQLite (캐시), MongoDB (로그) |
| **Vector DB** | ChromaDB |
| **AI Model** | BLIP (Salesforce/blip-image-captioning-base) via HuggingFace Transformers |
| **Scheduler** | APScheduler |
| **HTTP Client** | httpx |
| **Video Processing** | MoviePy, OpenCV |
| **Server** | Uvicorn (HTTPS) |

---

## File Architecture

```
QuantumBE/
├── server.py                   # 앱 진입점, 미들웨어 및 라우터 등록, 스케줄러 설정
│
├── routers/                    # API 엔드포인트
│   ├── authenticator.py        # 회원가입 / 로그인 / 로그아웃
│   ├── profile.py              # 사용자 프로필
│   ├── file.py                 # 파일 업로드, 다운로드, 조회, 삭제
│   ├── trashbin.py             # 휴지통 관리
│   ├── share.py                # 파일 공유
│   └── dependencies.py         # 공용 의존성 (LoginManager, 환경 변수 등)
│
├── modules/
│   ├── common/                 # 공통 유틸리티
│   │   ├── connect.py          # MongoDB 비동기 연결 데코레이터
│   │   ├── dbUtils.py          # DB 공통 유틸
│   │   ├── fileUtils.py        # 파일 처리 유틸
│   │   └── tree.py             # 디렉토리 트리 유틸
│   ├── mysql/                  # MySQL (메인 DB)
│   │   ├── database.py         # 세션 및 엔진 설정
│   │   ├── model.py            # ORM 모델 (User, Data 등)
│   │   ├── schema.py           # Pydantic 스키마
│   │   └── crud.py             # CRUD 쿼리
│   ├── sqlite/                 # SQLite (캐시 DB)
│   │   ├── database.py
│   │   ├── model.py
│   │   ├── schema.py
│   │   └── crud.py
│   └── mongo/
│       └── logger.py           # MongoDB 요청 로거
│
├── analyzer/
│   └── videoVision.py          # BLIP 모델 기반 이미지/영상 캡셔닝 + ChromaDB 벡터 저장소
│
├── periodicTasks/
│   └── sqliteJobs.py           # 만료된 캐시 정리 (1분 주기)
│
├── config/
│   ├── .env                    # 환경 변수 (HF_TOKEN 등)
│   ├── mongodb.py              # MongoDB 연결 설정
│   └── mysql.py                # MySQL 연결 설정
│
├── cache/                      # BLIP 모델 로컬 캐시
├── chroma/                     # ChromaDB 영구 저장소
├── thumbnails/                 # 파일 썸네일 이미지
├── crt/                        # SSL 인증서
└── requirements.txt
```

---

## Getting Started

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`config/.env` 파일에 필요한 값을 설정합니다.

```env
HF_TOKEN=<HuggingFace API Token>
```

`routers/dependencies.py`에서 DB 연결 정보 및 외부 서비스 호스트를 확인하고 수정합니다.

### 3. 서버 실행

**개발 (HTTP)**
```bash
uvicorn server:app --host 0.0.0.0 --port 5300 --reload
```

**프로덕션 (HTTPS)**
```bash
python server.py
```

> SSL 인증서 파일(`crt/private.key`, `crt/certificate.crt`, `crt/ca_bundle.crt`)이 존재해야 합니다.

### 4. API 문서

서버 실행 후 아래 주소에서 자동 생성된 API 문서를 확인할 수 있습니다.

- Swagger UI: `https://localhost:5300/docs`
- ReDoc: `https://localhost:5300/redoc`
