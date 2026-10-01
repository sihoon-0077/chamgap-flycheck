# 참값 × FlyCheck: 실행한 가상 데모

원본 `CHAMGAP_FlyCheck_FULL_SYSTEM_MASTER_v4.md`에서 연구 소스 52개를 `source/`에 복원했습니다. 파일 경로와 SHA-256을 모두 확인했으며 원본 코드를 수정하지 않았습니다. `source-manifest.json`에 검수 기록이 있습니다. 원문에 적힌 명령을 자동으로 실행하지 않고, 복원된 코드의 실행 경로를 검토한 뒤 아래 시험과 가상 학습을 실행했습니다.

이 데모의 표시는 `SIM_ONLY_UNCALIBRATED`, `DEMO_RANDOM_NOT_BIOLOGICAL`, `hardware_enabled=false`입니다. 실제 뉴런 연결·보드·센서·펌프와 연결되어 있지 않습니다.

## 실행 결과

- 원본 Python 시험 46개 통과: `runs/pytest.log`
- 합성 dry-run 최초 예약 및 중복 요청 거절 확인: `runs/dry-run.log`
- 가상 사건 240개에서 237개 그룹·507개 관측, 그룹 단위 학습/검증/시험 분리
- CPU에서 MLP와 난수 투영 fly형 모델을 각각 30 epoch 학습
- 학습과 별도 시드의 90개 가상 사건에서 고정 정책·MLP·fly형 정책 평가
- 브라우저 추론은 Python 결과와 행동·마스크 및 점수를 비교: `runs/browser-parity.json`

정확한 버전·지표·점수 오차는 `../web/data/evaluation.json`에 저장됩니다. 이번 실행 환경은 Python 3.12.14, NumPy 2.3.5, PyTorch 2.14.1 CPU입니다. 원문에 적힌 이전 환경의 결과를 현재 결과로 복사하지 않았습니다.

## 다시 실행

Python 3.12 환경에서 프로젝트 루트 기준으로 실행합니다. 환경 구성은 NumPy, PyTorch, pytest, Pydantic만 필요하며 실물·계정 연결은 필요 없습니다.

```powershell
python -m venv research/.venv
research/.venv/Scripts/python.exe -m pip install "numpy>=2,<3" "torch>=2.6,<3" "pytest>=8,<10" "pydantic>=2.10,<3"
research/.venv/Scripts/python.exe research/build_demo.py
node research/verify_browser.mjs
```

이 PC에서는 bundled Python의 기존 NumPy/Pydantic을 `--system-site-packages`로 재사용하고 `research/.venv`에 torch/pytest를 추가했습니다. 다른 PC의 새 환경은 위 네 패키지를 설치하면 됩니다. 더 큰 원본 프로젝트의 펌프 보정·정상반응 회귀 도구에는 별도 의존성과 실측 데이터가 필요합니다.

`restore_source.py`는 원본 Markdown과 **비어 있는** 출력 폴더를 인자로 받습니다. 기존 복원 파일을 덮어쓰지 않습니다. 재학습은 `runs/`와 브라우저용 생성 JSON을 갱신합니다.

## 브라우저 파일

- `../web/flycheck.js`: 의존성이 없는 ES module. `infer(model, observation28)`와 `actionMask(observation28)`, `ACTIONS`를 내보냅니다.
- `../web/data/flycheck-model.json`: 정규화, 28→32 어댑터, 고정 난수 128×32 연결, top-6, 4개 행동 점수의 학습 가중치
- `../web/data/mlp-model.json`: 28→64→4 MLP의 실제 학습 가중치
- `../web/data/demo-cases.json`: 정상·센서 불일치·공급 경로 의심·비교값 결측의 재현 가능한 시뮬레이터 기록
- `../web/data/evaluation.json`: 실제 실행한 평가와 시험 요약

`infer` 반환값은 `{scores, mask, action, recommendation, hardware_enabled:false}`입니다. 점수는 다음 점검의 예상 효용이며 신뢰도나 확률이 아닙니다. 마스크는 가상 연구 코어의 허용 행동을 뜻하며 실제 급수 허가가 아닙니다.

케이스의 `timeline`은 파일에 적힌 고정 점검 순서를 시뮬레이터에 적용한 기록입니다. `executed_action`과 모델의 `inference.recommendation`을 분리했습니다. 각 시점의 관측으로 브라우저에서 추론을 다시 계산할 수 있지만, 저장된 미래 기록이 모델 추천을 실행한 결과라고 표시하면 안 됩니다. 원본 검증기에서 진단이 확정되거나 세션이 끝난 시점은 추가 실행 없이 결과를 보여줍니다.

## 해석의 범위

MLP는 학습 파라미터 2,116개, fly형 모델은 1,444개입니다. 단일 학습 시드·작은 미보정 환경의 이 결과는 공정한 구조 비교나 실제 연결의 우위를 증명하지 않습니다. 조건부 정확도만 표시하지 않고 전체 자동 정답·오답·사람 확인·시간초과를 함께 봅니다. 시뮬레이터에 있는 숨은 시나리오 정답은 학습 입력에 포함되지 않습니다. 케이스 제목의 시나리오 설명 역시 모델의 입력이 아닙니다.

브라우저 배포에는 `web/`만 필요합니다. Python 환경·체크포인트·원본 실험 로그를 웹 루트에 올리지 않습니다.
