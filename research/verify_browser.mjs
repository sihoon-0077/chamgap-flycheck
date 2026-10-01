import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {infer, actionMask} from '../web/flycheck.js';

const root = path.dirname(fileURLToPath(import.meta.url));
const load = relative => JSON.parse(fs.readFileSync(path.join(root, relative), 'utf8'));
const cases = load('runs/parity-input.json');
const models = {fly: load('../web/data/flycheck-model.json'), mlp: load('../web/data/mlp-model.json')};
let maximumError = 0;
for (const row of cases) {
  for (const [kind, model] of Object.entries(models)) {
    const actual = infer(model, row.observation);
    assert.deepEqual(actual.mask, row[kind].mask);
    assert.equal(actual.action, row[kind].action);
    actual.scores.forEach((score, index) => {
      const error = Math.abs(score - row[kind].scores[index]);
      maximumError = Math.max(maximumError, error);
      assert.ok(error < 0.00005, `${kind}: score discrepancy ${error}`);
    });
  }
}
assert.throws(() => infer(models.fly, [0]));
assert.throws(() => infer(models.fly, Array(28).fill(NaN)));
const noPermit = [...cases[0].observation]; noPermit[23] = 0;
assert.equal(actionMask(noPermit)[2], false);
const estop = [...cases[0].observation]; estop[25] = 1;
assert.equal(actionMask(estop)[2], false);
const result = {status: 'passed', observations: cases.length, model_checks: cases.length * 2,
  max_absolute_score_error: maximumError, tolerance: 0.00005, actions_and_masks_match: true};
fs.writeFileSync(path.join(root, 'runs/browser-parity.json'), JSON.stringify(result, null, 2) + '\n');
const evaluation = load('../web/data/evaluation.json');
evaluation.verification.browser_parity = result;
fs.writeFileSync(path.join(root, '../web/data/evaluation.json'), JSON.stringify(evaluation, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
