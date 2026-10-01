import { infer, ACTIONS } from './flycheck.js';

const $ = selector => document.querySelector(selector);
const escape = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const actionNames = ['다시 측정', '비교 센서 확인', '시험 급수 검토', '사람에게 점검 요청'];
const actionDescriptions = ['같은 센서를 다시 읽어 변화와 반복성을 확인합니다.', '비교 센서의 새 관측으로 두 센서의 차이를 확인합니다.', '모델이 가상 시험 급수를 추천했습니다. 실제 장치 명령은 전송하지 않습니다.', '자동 판단을 보류하고 사람이 확인할 점검으로 넘깁니다.'];
const sheets = [
  ['01-pilot.svg','1구역 책상형 배치','PILOT LAYOUT','전자부품과 물길을 분리한 첫 조립 구성'],
  ['02-frame.svg','3구역 프레임 배치','FRONT / TOP / SIDE','800 × 400 × 1,200 mm 제안 배치 · 실물 확인 필요'],
  ['03-exploded.svg','계량 받침 분해도','LOADCELL ASSEMBLY','로드셀의 고정 베이스와 하중 상판을 구분한 조립 원리'],
  ['04-wiring.svg','센서 신호 배선','SIGNAL HARNESS','핀 이름과 H01–H13 연결표 · 실제 커넥터 배열 확인'],
  ['05-water-power.svg','전원과 물길','POWER / WATER','펌프 전력 경로와 구역별 독립 물길'],
  ['06-assembly.svg','부품과 조립 순서','ASSEMBLY SEQUENCE','부품 번호와 다음 단계 전 확인 조건'],
  ['07-verification.svg','실측 확인표','RELEASE CHECKLIST','확정되지 않은 치수·정격·실측 항목'],
  ['08-cutlist.svg','프레임 절단안','FRAME CUT PLAN','2020 맞댐 구조 가정 · 체결 방식 확정 후 발주']
];
let zoom = 100;
function selectSheet(index) {
  const [file,title,,description] = sheets[index];
  $('#sheet-index').textContent = `HW-${String(index+1).padStart(2,'0')}`;
  $('#drawing-title').textContent = title;
  $('#drawing-description').textContent = description;
  $('#drawing-image').src = `/assets/drawings/${file}`;
  $('#drawing-image').alt = `${title}. ${description}. 제작 검토용 미실측 도면.`;
  $('#drawing-open').href = $('#drawing-download').href = `/assets/drawings/${file}`;
  document.querySelectorAll('.sheet-button').forEach((button,i) => {
    button.classList.toggle('active',i===index);
    button.setAttribute('aria-pressed',String(i===index));
    button.querySelector('.sheet-indicator').hidden = i!==index;
  });
  setZoom(100);
}
$('#sheet-list').innerHTML = sheets.map((sheet,i) => `<button class="sheet-button${i===0?' active':''}" data-sheet="${i}" aria-pressed="${i===0}"><span class="number">${String(i+1).padStart(2,'0')}</span><span><strong>${sheet[1]}</strong><small>${sheet[2]}</small></span><span class="sheet-indicator" ${i===0?'':'hidden'}></span></button>`).join('');
$('#sheet-list').addEventListener('click', event => { const button = event.target.closest('[data-sheet]'); if(button) selectSheet(Number(button.dataset.sheet)); });
function setZoom(value) { zoom=Math.max(75,Math.min(250,value)); $('#drawing-image').style.width=`${zoom}%`; $('#drawing-image').style.minWidth=`${zoom}%`; $('#zoom-reset').textContent=`${zoom}%`; }
$('#zoom-in').addEventListener('click',()=>setZoom(zoom+25));
$('#zoom-out').addEventListener('click',()=>setZoom(zoom-25));
$('#zoom-reset').addEventListener('click',()=>setZoom(100));

const steps = [
  ['책상과 고정 받침 준비','물통·화분·전자부품 위치를 도면 HW-01과 맞추고, 물받이와 케이블 지지를 준비합니다.','낙수·넘어짐 경로와 전장 분리 확인'],
  ['센서를 한 종류씩 연결','펌프 전력선을 분리한 상태에서 SHT31, 토양수분, HX711을 순서대로 연결합니다.','전압·I2C 주소·원시값·결측 표시 확인'],
  ['대상·비교 센서 동시 수집','같은 조건에서 두 센서의 원시값을 기록합니다. ADC를 체적함수율로 임의 변환하지 않습니다.','센서별 편차와 반복성 기록'],
  ['계량 받침 조립·검수','로드셀 한쪽을 베이스에, 반대쪽을 하중 상판에 고정합니다. 알려진 질량과 호스 장력의 영향을 확인합니다.','영점·반복성·작은 질량 변화 식별'],
  ['펌프 독립 컵 시험','DC 차단·퓨즈·전선 정격을 확인한 뒤, 별도 용기와 독립 저울로 시간별 공급량을 측정합니다.','정지·타임아웃 검수와 공급량 보정'],
  ['배지 반응 기록','배지·삽입 깊이·다짐을 일정하게 유지하고 공급량과 센서 반응을 함께 기록합니다.','공급량과 반응 지연 기록'],
  ['3구역으로 복제','검수된 부품과 배선으로 두 구역을 추가합니다. 구역·센서 ID를 부착하고 상호 간섭을 확인합니다.','다른 구역 작동 시 계량 영향 확인']
];
$('#assembly-steps').innerHTML=steps.map((step,i)=>`<li><span class="step-number">${i+1}</span><div><h3>${step[0]}</h3><p>${step[1]}</p><span class="step-check">확인 · ${step[2]}</span></div></li>`).join('');

async function getJson(path) { const response=await fetch(path); if(!response.ok) throw new Error(`${path} (${response.status})`); return response.json(); }
let bom;
async function loadBom() {
  try { bom ??= await getJson('/data/bom.json'); renderBom(); }
  catch { $('#bom-body').innerHTML='<tr><td colspan="5">부품표를 불러오지 못했습니다. PDF의 부품표를 확인해주세요.</td></tr>'; }
}
function renderBom() {
  const category=$('#bom-filter').value;
  $('#bom-body').innerHTML=bom.items.filter(p=>category==='all'||p.id.startsWith(category)).map(p=>`<tr><td>${escape(p.id)}</td><td><strong>${escape(p.name)}</strong><span class="part-description">${escape(p.description)}</span></td><td>${p.qty}</td><td>${p.price.toLocaleString('ko-KR')}원</td><td><a href="${escape(p.url)}" target="_blank" rel="noopener">${escape(p.vendor)} ↗</a></td></tr>`).join('');
}
$('#bom-filter').addEventListener('change',()=>{if(bom)renderBom();});

let lab, selectedCase=0, selectedStep=-1, history=[];
async function loadLab() {
  if(lab) return;
  try {
    const [model,data]=await Promise.all([getJson('/data/flycheck-model.json'),getJson('/data/demo-cases.json')]);
    if(!data.cases?.length || model.hardware_enabled!==false) throw new Error('Invalid demo');
    lab={model,cases:data.cases};
    $('#case-list').innerHTML=data.cases.map((item,i)=>`<button class="case-button${i===0?' active':''}" data-case="${i}" aria-pressed="${i===0}">${escape(item.title)}</button>`).join('');
    $('#lab-loading').hidden=true; $('#lab-content').hidden=false;
    selectCase(0);
  } catch(error) { $('#lab-loading').textContent='학습 파일을 불러오지 못했습니다. 페이지를 새로고침해 다시 시도해주세요.'; $('#lab-loading').classList.add('error-state'); console.error(error); }
}
function currentObservation() { const item=lab.cases[selectedCase];return selectedStep<0?item.observation:item.timeline[selectedStep].observation; }
function currentPoint() {return lab.cases[selectedCase].timeline[selectedStep<0?0:selectedStep];}
function isTerminal(){const point=currentPoint();return point.diagnosis!=='UNKNOWN'||point.executed_action==='REQUEST_INSPECTION';}
function showObservation() {
  const observation=currentObservation();
  const names=lab.model.feature_names||lab.model.features||[];
  $('#observation-list').innerHTML=observation.map((value,i)=>`<div><span>${escape(names[i]||`feature_${String(i).padStart(2,'0')}`)}</span><span>${Number(value).toFixed(4)}</span></div>`).join('');
}
function resetRecommendation() {
  $('#run-inference').disabled=isTerminal();
  if(isTerminal()){
    const point=currentPoint(),names={NORMAL:'정상으로 판정된 가상 기록',SENSOR:'센서 이상으로 판정된 가상 기록',SUPPLY:'공급 경로 이상으로 판정된 가상 기록',UNKNOWN:'사람 확인으로 넘긴 기록'};
    const reasons={fresh_comparison_agrees:'새 비교 측정이 대상 센서와 일치했습니다.',persistent_measurement_disagreement:'대상·비교 센서의 불일치가 반복됐습니다.',command_without_expected_mass_increase:'급수 명령에 비해 관측된 질량 증가가 부족했습니다.'};
    $('#recommendation').innerHTML=`<span class="result-symbol">✓</span><div><span class="eyebrow">RECORDED RESULT</span><h3>${names[point.diagnosis]||escape(point.diagnosis)}</h3><p>${reasons[point.reason]||'이 가상 기록은 종료됐습니다. 이전 관측 시점을 선택해 추천을 확인하세요.'}</p></div>`;
    $('#score-list').innerHTML='<p class="small-note">저장된 가상 실험의 종료 상태입니다. 추가 점검을 추천하지 않습니다.</p>';return;
  }
  $('#recommendation').innerHTML='<span class="result-symbol">◎</span><div><span class="eyebrow">READY</span><h3>점검 추천을 계산해보세요.</h3><p>입력은 현재 선택한 가상 관측입니다.</p></div>';
  $('#score-list').innerHTML='';
}
function selectCase(index) {
  selectedCase=index;selectedStep=-1;
  const item=lab.cases[index];
  $('#case-title').textContent=item.title;
  $('#case-description').textContent=item.description;
  document.querySelectorAll('[data-case]').forEach((button,i)=>{button.classList.toggle('active',i===index);button.setAttribute('aria-pressed',String(i===index));});
  let select=$('#timeline-step');
  if(!select){const label=document.createElement('label');label.className='timeline-label';label.textContent='가상 실험의 관측 시점';select=document.createElement('select');select.id='timeline-step';label.append(select);$('.case-detail').append(label);select.addEventListener('change',()=>{selectedStep=Number(select.value);showObservation();resetRecommendation();});}
  select.innerHTML='<option value="-1">시작 관측</option>'+item.timeline.map((point,i)=>`<option value="${i}">${point.elapsed_s}초 · ${escape(point.executed_action||'관측')}</option>`).join('');
  if(!$('#trace-note')){const note=document.createElement('p');note.id='trace-note';note.className='small-note';note.textContent='관측 시점은 고정 순서로 수행한 가상 실험 기록입니다. 지금 계산한 모델 추천을 실행한 결과는 아닙니다.';$('.case-detail').append(note);}
  showObservation();resetRecommendation();
}
$('#case-list').addEventListener('click',event=>{const button=event.target.closest('[data-case]');if(button)selectCase(Number(button.dataset.case));});
$('#run-inference').addEventListener('click',()=>{
  if(!lab||isTerminal())return;
  try {
    const observation=currentObservation(); const result=infer(lab.model,observation);
    $('#recommendation').innerHTML=`<span class="result-symbol">◎</span><div><span class="eyebrow">${ACTIONS[result.action]}</span><h3>${actionNames[result.action]}</h3><p>${actionDescriptions[result.action]}</p></div>`;
    const min=Math.min(...result.scores),max=Math.max(...result.scores),range=Math.max(max-min,.001);
    $('#score-list').innerHTML=result.scores.map((score,i)=>`<div class="score-row${i===result.action?' selected':''}${result.mask[i]?'':' masked'}"><span>${actionNames[i]}${result.mask[i]?'':' · 불허'}</span><div class="score-bar"><div class="score-fill"></div></div><span class="score-value">${score.toFixed(3)}</span></div>`).join('')+'<p class="small-note">점수는 예측 효용이며 확률이 아닙니다. 막대는 이번 계산의 최소·최대에 맞춘 상대 크기입니다. 가상 허용 조건을 만족한 행동 중 선택합니다.</p>';
    document.querySelectorAll('.score-fill').forEach((bar,i)=>bar.style.width=`${Math.max(3,(result.scores[i]-min)/range*100)}%`);
    history.unshift({timestamp:new Date().toISOString(),case_id:lab.cases[selectedCase].id,title:lab.cases[selectedCase].title,step:selectedStep,observation,result,domain:'SIM_ONLY_UNCALIBRATED',connectome_source:'DEMO_RANDOM_NOT_BIOLOGICAL',hardware_enabled:false});
    $('#history').innerHTML=history.slice(0,10).map(row=>`<div class="history-row"><time>${new Date(row.timestamp).toLocaleTimeString('ko-KR',{hour12:false})}</time><span>${escape(row.title)}</span><strong>${actionNames[row.result.action]}</strong></div>`).join('');
    $('#export-history').disabled=false;
  }catch(error){$('#recommendation').textContent='입력이나 모델이 유효하지 않아 계산을 중단했습니다.';console.error(error);}
});
$('#export-history').addEventListener('click',()=>{
  const url=URL.createObjectURL(new Blob([JSON.stringify({schema:'flycheck.browser-session.v1',hardware_enabled:false,records:history},null,2)],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download='flycheck-simulation-session.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});

let evaluation;
async function loadVerification(){
  if(evaluation)return;
  try {
    evaluation=await getJson('/data/evaluation.json');
    const check=evaluation.verification, parity=check.browser_parity;
    const percent=value=>`${(value*100).toFixed(1)}%`;
    const labels={fixed:'고정 점검 규칙',mlp:'일반 MLP',fly:'FlyCheck 난수 연결'};
    $('#verification-results').innerHTML=`<div class="result-stats"><article class="stat-card"><span>Python 코어·통합 시험</span><strong>${check.python_tests_passed} <small>PASS</small></strong><small>현재 환경에서 재실행</small></article><article class="stat-card"><span>웹 / Python 추론 비교</span><strong>${parity.model_checks.toLocaleString()} <small>회 일치</small></strong><small>행동·허용 마스크 일치</small></article><article class="stat-card"><span>학습 데이터</span><strong>${evaluation.dataset.rows} <small>행</small></strong><small>${evaluation.dataset.groups_saved}개 가상 사건 그룹</small></article></div><div class="card"><div class="card-heading"><div><h2>같은 가상 사건 90개에서 비교</h2><p>단일 학습 시드 · 미보정 가상환경 · 실물 정확도가 아닙니다.</p></div><span class="pill">실행 완료</span></div><div class="table-wrap"><table><thead><tr><th>정책</th><th>자동 정답 / 전체</th><th>자동 오답 / 전체</th><th>사람 요청 / 전체</th><th>시간 초과 / 전체</th><th>학습 파라미터</th></tr></thead><tbody>${Object.entries(evaluation.policies).map(([key,p])=>`<tr><td>${labels[key]||escape(key)}</td><td>${percent(p.summary.auto_correct)}</td><td>${percent(p.summary.auto_wrong)}</td><td>${percent(p.summary.human)}</td><td>${percent(p.summary.timeout)}</td><td>${p.trainable_parameters.toLocaleString()}</td></tr>`).join('')}</tbody></table></div><p class="table-footnote">모든 비율의 분모는 전체 90개 사건입니다. 모델별 파라미터 수가 다르므로 구조의 우위를 판정하는 공정 비교가 아닙니다. 이번 실행에서 FlyCheck의 우위는 확인되지 않았습니다.</p><details class="observation-details"><summary>실행 환경과 검증 상세</summary><pre>${escape(JSON.stringify({runtime:evaluation.runtime,verification:check,limitations:evaluation.limitations},null,2))}</pre></details></div>`;
  }catch(error){$('#verification-results').innerHTML='<p class="error-state">검증 기록을 불러오지 못했습니다. 결과 JSON을 확인해주세요.</p>';console.error(error);}
}
function route(){
  const requested=location.hash.slice(1);if(requested==='main'){$('#main').focus();return;}
  const name=['drawings','assembly','flycheck','verification'].includes(requested)?requested:'drawings';
  document.querySelectorAll('.view').forEach(view=>view.hidden=view.id!==`view-${name}`);
  document.querySelectorAll('[data-nav]').forEach(link=>{const current=link.dataset.nav===name;link.classList.toggle('active',current);if(current)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');});
  $('#breadcrumb-current').textContent={drawings:'조립 도면',assembly:'부품과 조립',flycheck:'FlyCheck Lab',verification:'검증 기록'}[name];
  if(name==='assembly')loadBom();if(name==='flycheck')loadLab();if(name==='verification')loadVerification();
  window.scrollTo(0,0);
}
window.addEventListener('hashchange',route);route();
