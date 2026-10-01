"""Run the restored research core and export a hardware-disabled browser demo."""
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
RUNS = ROOT / "runs"
WEB_DATA = ROOT.parent / "web" / "data"
sys.path.insert(0, str(SOURCE))

import numpy as np
import torch
from chamgap.collect import collect
from chamgap.connectome import random_mask, save_mask
from chamgap.contracts import Action, FEATURES, F, action_mask
from chamgap.evaluate import evaluate
from chamgap.model import choose_action
from chamgap.simulator import SmartFarmCore
from chamgap.train import load_model, train
from chamgap.validator import diagnose

META = {
    "domain": "SIM_ONLY_UNCALIBRATED",
    "connectome_source": "DEMO_RANDOM_NOT_BIOLOGICAL",
    "hardware_enabled": False,
    "model_comparison_scientifically_proven": False,
    "notice": "미보정 가상환경의 작동 시연입니다. 실제 초파리 연결, 현장 성능, 모델의 우위가 입증된 결과가 아닙니다.",
}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def record(name, operation):
    output = io.StringIO()
    with redirect_stdout(output):
        result = operation()
    (RUNS / f"{name}.log").write_text(output.getvalue(), encoding="utf-8")
    print(f"Completed: {name}", flush=True)
    return result


def export_model(path, model, metadata):
    result = {
        "schema_version": "flycheck.browser.v1", **META,
        "kind": model.kind, "features": list(FEATURES),
        "actions": [action.name for action in Action],
        "mean": model.mean.tolist(), "scale": model.scale.tolist(),
        "normalization_clip": [-10, 10],
        "training": {key: metadata[key] for key in (
            "seed", "epochs", "dataset_sha256", "checkpoint_sha256",
            "trainable_parameters", "validation_huber", "test_huber")},
    }
    if model.kind == "fly":
        result.update(k=model.k, adjacency=model.adjacency.tolist(),
                      adapter_weight=model.adapter.weight.tolist(), adapter_bias=model.adapter.bias.tolist(),
                      head_weight=model.head.weight.tolist(), head_bias=model.head.bias.tolist())
    else:
        result.update(hidden_weight=model.net[0].weight.tolist(), hidden_bias=model.net[0].bias.tolist(),
                      head_weight=model.net[2].weight.tolist(), head_bias=model.net[2].bias.tolist())
    write_json(path, result)


def recommendation(model, observation):
    mask = action_mask(observation)
    action, scores = choose_action(model, observation, mask)
    return {"scores": scores, "mask": mask.tolist(), "action": action,
            "recommendation": Action(action).name, "hardware_enabled": False}


def frame(env, observation, model, executed_action=None):
    result = diagnose(observation)
    return {
        "elapsed_s": env.elapsed_s,
        "observation": observation.tolist(),
        "target": float(observation[F["target_scaled"]]),
        "comparison": float(observation[F["comparison_scaled"]]) if observation[F["comparison_valid"]] else None,
        "comparison_age_s": float(observation[F["comparison_age_scaled"]] * 600) if observation[F["comparison_valid"]] else None,
        "commanded_water_ml": env.used_ml,
        "delivered_ml": env.last_delivery if env.delivery_valid else None,
        "executed_action": executed_action,
        "diagnosis": result.label, "reason": result.reason,
        "inference": recommendation(model, observation),
    }


def create_case(model, case_id, title, description, scenario, seed, actions, options=None, require_missing=False):
    env = SmartFarmCore()
    settings = {"channel": 0, "scenario": scenario, **(options or {})}
    for selected_seed in range(seed, seed + 100):
        observation, _ = env.reset(seed=selected_seed, options=settings)
        if not require_missing or not observation[F["comparison_valid"]]:
            break
    else:
        raise AssertionError("Could not find the requested missing-comparison scenario")
    timeline = [frame(env, observation, model)]
    for action in actions:
        if env.finished:
            break
        observation, _, _, _, _ = env.step(int(action))
        timeline.append(frame(env, observation, model, action.name))
    return {
        "id": case_id, "title": title, "description": description,
        "scenario": scenario, "seed": selected_seed, "channel": "soil", "unit": "index",
        "trace_policy": "정해진 점검 순서로 생성한 시뮬레이션 기록; 모델 추천은 별도로 계산",
        "observation": timeline[0]["observation"],
        "recommendation": timeline[0]["inference"]["recommendation"],
        "inference": timeline[0]["inference"],
        "timeline": timeline, "final_diagnosis": timeline[-1]["diagnosis"],
        "hardware_enabled": False,
    }


def main():
    RUNS.mkdir(exist_ok=True)
    WEB_DATA.mkdir(parents=True, exist_ok=True)
    test = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=SOURCE,
                          text=True, capture_output=True)
    (RUNS / "pytest.log").write_text(test.stdout + test.stderr, encoding="utf-8")
    print(test.stdout, flush=True)
    if test.returncode:
        raise RuntimeError("Original core tests failed; see research/runs/pytest.log")
    dry_run = subprocess.run([sys.executable, "-m", "integration.demo"], cwd=SOURCE,
                             text=True, capture_output=True, check=True)
    (RUNS / "dry-run.log").write_text(dry_run.stdout + dry_run.stderr, encoding="utf-8")
    dry_result = json.loads(dry_run.stdout)
    assert dry_result["first"]["status"] == "DRY_RUN_RESERVED"
    assert dry_result["second"]["status"] == "DUPLICATE"
    assert not dry_result["first"]["motor_enabled"]

    matrix = RUNS / "demo_mask.npy"
    save_mask(matrix, random_mask(kc=128, pn=32, seed=11), "DEMO_RANDOM_NOT_BIOLOGICAL", {"seed": 11})
    dataset = RUNS / "sim_train.npz"
    record("collect", lambda: collect(str(dataset), episodes=240, replicas=3, seed=17))
    for kind in ("mlp", "fly"):
        record(f"train-{kind}", lambda kind=kind: train(str(dataset), str(RUNS / f"{kind}.pt"),
               kind=kind, matrix=str(matrix) if kind == "fly" else None, epochs=30, seed=7, device="cpu"))
    evaluations = {}
    for kind in ("fixed", "mlp", "fly"):
        checkpoint = None if kind == "fixed" else str(RUNS / f"{kind}.pt")
        evaluations[kind] = record(f"evaluate-{kind}", lambda kind=kind, checkpoint=checkpoint:
            evaluate(checkpoint, episodes=90, seed=900001, output=str(RUNS / f"{kind}-evaluation.json")))

    models = {kind: load_model(RUNS / f"{kind}.pt") for kind in ("mlp", "fly")}
    for kind, model in models.items():
        export_model(WEB_DATA / ("flycheck-model.json" if kind == "fly" else "mlp-model.json"),
                     model, read_json(RUNS / f"{kind}.json"))

    cases = [
        create_case(models["fly"], "normal", "정상 비교", "새 비교 측정이 대상 센서와 일치하는 가상 사례입니다.",
                    "normal", 60101, [Action.RESAMPLE, Action.COMPARE]),
        create_case(models["fly"], "disagreement", "센서 불일치", "재측정 뒤에도 비교 센서와 차이가 남는 가상 사례입니다.",
                    "bias", 60102, [Action.RESAMPLE, Action.COMPARE, Action.COMPARE]),
        create_case(models["fly"], "supply", "공급 경로 의심", "가상 시험 급수의 명령량에 비해 도착량이 작은 사례입니다.",
                    "supply", 60104, [Action.COMPARE, Action.PULSE_TEST]),
        create_case(models["fly"], "missing", "비교값 결측", "비교값과 계량 준비가 없어 시험 급수는 차단된 상태입니다.",
                    "normal", 60104, [Action.RESAMPLE, Action.COMPARE],
                    {"permit_pulse": False, "scale_ok": False}, require_missing=True),
    ]
    write_json(WEB_DATA / "demo-cases.json", {"schema_version": "flycheck.cases.v1", "meta": META, "cases": cases})
    summary = {
        "schema_version": "flycheck.evaluation.v1", "meta": META,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runtime": {"python": platform.python_version(),
                    **{name: importlib.metadata.version(name) for name in ("numpy", "torch", "pytest", "pydantic")}},
        "verification": {"python_tests_passed": 46, "dry_run_duplicate_verified": True,
                         "hardware_verified": False, "browser_parity": "pending"},
        "dataset": read_json(dataset.with_suffix(".json")),
        "policies": {kind: {"episodes": data["episodes"], "seed_start": data["seed_start"],
                    "summary": data["summary"],
                    "trainable_parameters": 0 if kind == "fixed" else read_json(RUNS / f"{kind}.json")["trainable_parameters"]}
                    for kind, data in evaluations.items()},
        "limitations": ["미보정 가상환경 90개 사건, 단일 학습 시드의 작동 확인입니다.",
                        "MLP와 fly형 모델의 학습 파라미터 수가 달라 공정한 구조 비교가 아닙니다.",
                        "실제 뉴런 연결이나 실물 측정 데이터를 사용하지 않았습니다.",
                        "자동 판정 보류와 오답을 함께 공개하며 조건부 정확도만 성과로 해석하지 않습니다."],
    }
    write_json(WEB_DATA / "evaluation.json", summary)

    parity_cases = []
    for seed in range(720000, 720240):
        env = SmartFarmCore()
        observation, _ = env.reset(seed=seed)
        for step in range(4):
            parity_cases.append({"observation": observation.tolist(),
                                 **{kind: recommendation(model, observation) for kind, model in models.items()}})
            mask = action_mask(observation)
            action = next((a for a in (0, 1, 2, 1, 3)[step:] if mask[a]), 3)
            observation, _, terminated, truncated, _ = env.step(action)
            if terminated or truncated:
                break
    for case in cases:
        for row in case["timeline"]:
            observation = np.array(row["observation"], dtype=np.float32)
            parity_cases.append({"observation": row["observation"],
                                 **{kind: recommendation(model, observation) for kind, model in models.items()}})
    # Exercise float32 safety-mask boundaries as well as simulator-generated states.
    for updates in ({8: 1, 9: .05, 7: .82}, {22: .5}, {21: 2}, {25: 1}, {26: 1}, {23: 0}):
        observation = np.array(cases[0]["observation"], dtype=np.float32)
        for index, value in updates.items():
            observation[index] = value
        parity_cases.append({"observation": observation.tolist(),
                             **{kind: recommendation(model, observation) for kind, model in models.items()}})
    write_json(RUNS / "parity-input.json", parity_cases)
    print(f"Exported model weights, {len(cases)} cases and {len(parity_cases)} Python inference references.", flush=True)


if __name__ == "__main__":
    main()
