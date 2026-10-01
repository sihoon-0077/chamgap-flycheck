// Pure browser inference for the exported, synthetic research models. No device API.
export const ACTIONS = Object.freeze(['RESAMPLE', 'COMPARE', 'PULSE_TEST', 'REQUEST_INSPECTION']);

function checkedObservation(observation) {
  if (!Array.isArray(observation) || observation.length !== 28 || !observation.every(Number.isFinite)) {
    throw new TypeError('현재 관측은 유한한 숫자 28개여야 합니다.');
  }
  return observation.map(Math.fround);
}

export function actionMask(observation) {
  const x = checkedObservation(observation);
  const freshWet = x[8] > .5 && x[9] <= Math.fround(.05) && x[7] >= Math.fround(.82);
  const pulse = x[0] > .5 && x[23] > .5 && x[24] > .5 && x[25] < .5 && x[26] < .5
    && x[27] > .5 && !freshWet && x[22] >= .5 && x[21] < 2;
  return [x[19] < 2, x[20] < 2, pulse, true];
}

function linear(weights, bias, values) {
  return weights.map((row, index) => row.reduce((sum, weight, j) => sum + weight * values[j], bias[index]));
}

export function infer(model, observation) {
  const input = checkedObservation(observation);
  if (model?.schema_version !== 'flycheck.browser.v1' || model.hardware_enabled !== false
      || model.mean?.length !== 28 || model.scale?.length !== 28
      || !model.scale.every(value => Number.isFinite(value) && value > 0)) {
    throw new TypeError('검증된 FlyCheck 가상 모델 파일이 필요합니다.');
  }
  const normalized = input.map((value, i) => Math.max(-10, Math.min(10, (value - model.mean[i]) / model.scale[i])));
  let hidden;
  if (model.kind === 'fly') {
    const pn = linear(model.adapter_weight, model.adapter_bias, normalized).map(value => 1 / (1 + Math.exp(-value)));
    const kc = linear(model.adjacency, model.adjacency.map(() => 0), pn);
    const selected = new Set(kc.map((value, index) => ({value, index}))
      .sort((a, b) => b.value - a.value || a.index - b.index).slice(0, model.k).map(item => item.index));
    hidden = kc.map((value, index) => selected.has(index) ? value : 0);
  } else if (model.kind === 'mlp') {
    hidden = linear(model.hidden_weight, model.hidden_bias, normalized).map(value => Math.max(0, value));
  } else {
    throw new TypeError('지원하지 않는 모델 종류입니다.');
  }
  const scores = linear(model.head_weight, model.head_bias, hidden);
  const mask = actionMask(input);
  if (scores.length !== 4 || !scores.every(Number.isFinite)) throw new TypeError('모델 점수가 유효하지 않습니다.');
  let action = 3;
  for (let i = 0; i < scores.length; i++) {
    if (mask[i] && (!mask[action] || scores[i] > scores[action] || (scores[i] === scores[action] && i < action))) action = i;
  }
  return {scores, mask, action, recommendation: ACTIONS[action], hardware_enabled: false};
}
