# 참값 × FlyCheck

하드웨어 조립 도면과 가상 점검 추천을 함께 보는 제작 워크스페이스입니다.

- A3 가로 조립 도면 8장: 1구역 배치, 3구역 3면도, 계량 받침, 신호 배선, 전력·물길, 조립 순서, 실측 확인표, 절단안
- 부품표 25개 및 센서-only ESP32 참고 스케치
- 실제 학습 가중치로 브라우저에서 계산하는 FlyCheck 가상 데모 4개
- Python 시험 46개 및 Python/JavaScript 추론 일치 검증 기록

## 실행

Node.js 22 이상에서 추가 패키지 설치 없이 실행합니다.

```sh
npm run dev
# http://127.0.0.1:4173
npm test
npm run build
```

Vercel에서는 Framework `Other`, Build Command `npm run build`, Output Directory `dist`를 사용합니다. `vercel.json`에 포함되어 있습니다. 배포 범위는 `web/`에서 복사한 정적 파일뿐이며 별도 API 키나 데이터베이스가 필요 없습니다.

## 폴더

| 경로 | 내용 |
|---|---|
| `web/` | 정적 웹, 학습 가중치, 가상 관측, 평가 요약 |
| `web/downloads/` | 조립 PDF와 센서 스케치 |
| `web/assets/drawings/` | 수정 가능한 SVG 8장 |
| `hardware/` | 도면 생성기, 출처와 출력 검수 기록 |
| `research/` | 복원한 연구코어 52개, 재현 스크립트 및 설명 |
| `scripts/` | 정적 빌드·로컬 서버·부품표 변환 |

원문 구매 CSV 또는 센서 스케치를 변경한 경우 `node scripts/prepare-assets.mjs`로 웹용 파일을 갱신합니다. 모델 재학습과 도면 재생성은 각 폴더 README를 따릅니다. 실제 실행에 사용한 라이브러리 버전은 `web/data/evaluation.json`에 있습니다.

## 결과 해석

모델은 `SIM_ONLY_UNCALIBRATED` 환경의 `DEMO_RANDOM_NOT_BIOLOGICAL` 연결입니다. 실제 초파리 연결·센서·펌프에 연결되어 있지 않으며 `hardware_enabled=false`입니다. 타임라인은 고정 점검 순서의 가상 기록이며 새 추천을 실행한 미래 결과가 아닙니다. 진단이 확정된 관측에서는 추가 추천을 중지합니다.

90개 가상 사건에 대한 전체 자동 정답 비율은 고정 규칙 77.8%, MLP 76.7%, fly형 70.0%였습니다. 오답·사람 요청·시간초과를 함께 공개하며 실제 현장 성능 또는 fly형의 우위로 해석하지 않습니다. 모델 크기도 다르므로 공정한 구조 비교가 아닙니다.

도면은 제공된 마스터 v4의 제안 치수를 반영한 **제작 검토용 v1 / 미실측**입니다. 홀·나사·하중·퓨즈·DC 차단 정격을 확정한 가공 승인 도면이 아닙니다. 실물 부품을 확인한 뒤 표시된 미정 항목을 채워야 합니다.

기준 자료: 사용자가 제공한 `CHAMGAP_FlyCheck_FULL_SYSTEM_MASTER_v4.md`. 원문 전체 및 인증정보는 웹 배포에 포함하지 않습니다.
