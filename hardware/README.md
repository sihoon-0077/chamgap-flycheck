# 참값 하드웨어 조립도면 v1

사용자가 제공한 `CHAMGAP_FlyCheck_FULL_SYSTEM_MASTER_v4.md`의 18-21장, 29장을 mm 단위 도면 8장으로 구성했습니다. **제작 검토용이며 미실측입니다.** 기구·전기 가공 승인 및 실제 통전 시험 완료를 뜻하지 않습니다.

- `../web/downloads/chamgap-assembly-v1.pdf`: 한국어 글꼴을 포함한 A3 가로형 벡터 PDF. 인쇄할 때는 표기 치수를 읽고, 그림을 자로 재어 가공하지 않습니다.
- `../web/assets/drawings/*.svg`: 페이지별 편집 가능한 벡터 원본. 텍스트는 Malgun Gothic 또는 Noto Sans KR 글꼴로 표시합니다.
- `../web/assets/drawings/manifest.json`: 웹 도면 목록.
- `build_drawings.py`: PDF와 SVG를 함께 재생성하는 단일 원본. Python 표준 라이브러리와 reportlab만 사용합니다.

## 도면 구성

1. 기존 책상 위 1구역 배치
2. 800×400×1200 3구역 프레임 정면·측면·평면
3. 로드셀 받침 분해 조립 원리
4. 센서 신호 배선과 하네스 ID
5. 펌프 전력 경로 및 독립 물길
6. 조립 순서·부품 묶음·공구·단계별 완료 기준
7. 미확정 치수와 검수 기록표
8. 2020 맞댐 가정의 절단안과 판 상세

## 정확도와 한계

원문 제안 치수를 표기하고, 로드셀 홀·나사·스페이서·체결 토크·판 재료·DC 차단·퓨즈 정격을 임의로 확정하지 않았습니다. 계량 받침 220×260 mm, 완성 높이 40 mm 이내는 목표입니다. 함체 글랜드/개폐 공간, 프레임 발/캡, 보강 구조는 실물과 제작실 검토가 필요합니다. 특히 로드셀 그림의 비율과 구멍은 설명용이며 실제 가공 좌표가 아닙니다.

1구역 파일럿의 센서·계량을 먼저 검수한 후 펌프 독립 컵 시험, 배지 시험, 3구역 확장 순으로 진행합니다. 센서-only 코드 업로드 동안 모터 전원은 물리적으로 차단합니다.

## 확인한 1차 출처 (2026-10-01)

- DFRobot DFR0457 핀아웃/사양/유도성 부하 보호: https://wiki.dfrobot.com/dfr0457/
- Espressif 클래식 ESP32 GPIO: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/gpio.html

PDF·SVG 생성: `python hardware/build_drawings.py` (Windows Malgun Gothic 글꼴 사용).
