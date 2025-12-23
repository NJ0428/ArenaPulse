# ArenaPulse

![Panda3D](https://img.shields.io/badge/Panda3D-1.10+-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)

DOOM 스타일의 고속 액션 1인칭 슈팅 게임입니다. Panda3D 게임 엔진으로 제작되었습니다.

## 기능

- **1인칭 슈팅 (FPS)** - 몰입감 있는 1인칭 시점
- **고속 액션** - 빠른 이동과 전투
- **원거리 공격** - 투사체 발사
- **근접 공격** - 근접 전투 시스템
- **점프 및 중력** - 자연스러운 물리 엔진
- **데이터베이스** - 게임 데이터 저장

## 요구사항

- Python 3.8+
- Panda3D 1.10+

## 설치

```bash
# 가상환경 생성 (선택사항)
python -m venv venv

# 가상환경 활성화
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

## 실행

```bash
# Windows
.\venv\Scripts\python.exe game\main.py

# Linux/Mac
python game/main.py
```

## 조작법

| 키 | 동작 |
|---|---|
| **W** | 앞으로 이동 |
| **S** | 뒤로 이동 |
| **A** | 왼쪽 이동 |
| **D** | 오른쪽 이동 |
| **마우스** | 시점 조정 |
| **좌클릭** | 원거리 공격 (투사체) |
| **우클릭 / Space** | 근접 공격 / 점프 |
| **ESC** | 일시정지 |

## 프로젝트 구조

```
ArenaPulse/
├── game/
│   ├── main.py       # 게임 메인 실행 파일
│   ├── config.py     # 게임 설정
│   ├── player.py     # 플레이어 클래스
│   ├── controls.py   # 입력 컨트롤
│   ├── database.py   # 데이터베이스 관리
│   └── __init__.py
├── data/             # 게임 데이터
├── assets/           # 게임 리소스
├── requirements.txt  # Python 의존성
└── README.md
```

## 설정

`game/config.py`에서 게임 설정을 수정할 수 있습니다:

- `SCREEN_WIDTH` / `SCREEN_HEIGHT` - 화면 해상도 (기본값: 1920x1080)
- `WINDOW_TITLE` - 창 제목
- `FPS` - 목표 프레임률

## 라이선스

MIT License
