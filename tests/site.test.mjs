import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, access } from 'node:fs/promises';
import { infer } from '../web/flycheck.js';
const json=async name=>JSON.parse(await readFile(new URL(`../web/data/${name}`,import.meta.url),'utf8'));
test('published links and all eight drawing sheets resolve locally',async()=>{
  const html=await readFile('web/index.html','utf8');
  for(const [,path] of html.matchAll(/(?:href|src)="(\/[^"#]+)"/g))await access(`web${path}`);
  for(const name of ['01-pilot','02-frame','03-exploded','04-wiring','05-water-power','06-assembly','07-verification','08-cutlist'])await access(`web/assets/drawings/${name}.svg`);
  const pdf=await readFile('web/downloads/chamgap-assembly-v1.pdf');assert.equal(pdf.subarray(0,5).toString(),'%PDF-');
});
test('all scenario recommendations reproduce exported Python results without hardware',async()=>{
  const [model,data]=await Promise.all([json('flycheck-model.json'),json('demo-cases.json')]);
  assert.equal(model.connectome_source,'DEMO_RANDOM_NOT_BIOLOGICAL');
  for(const scenario of data.cases)for(const point of scenario.timeline){
    const result=infer(model,point.observation);
    assert.equal(result.action,point.inference.action);assert.deepEqual(result.mask,point.inference.mask);assert.equal(result.hardware_enabled,false);
    result.scores.forEach((score,i)=>assert.ok(Math.abs(score-point.inference.scores[i])<.00005));
  }
  assert.throws(()=>infer(model,Array(28).fill(NaN)));
});
test('BOM preserves the source snapshot and no prices pretend to be current',async()=>{
  const bom=await json('bom.json');assert.equal(bom.items.length,25);assert.equal(bom.current_price_verified,false);assert.equal(bom.items.reduce((s,p)=>s+p.total,0),504891);
  for(const p of bom.items){assert.ok(p.name);assert.equal(new URL(p.url).protocol,'https:');}
});
