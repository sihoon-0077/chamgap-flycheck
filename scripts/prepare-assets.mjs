import { readFile, writeFile, mkdir, copyFile } from 'node:fs/promises';
const csv=await readFile('research/source/docs/procurement_snapshot_20260929.csv','utf8');
// This source is a quoted CSV snapshot; quoted commas and escaped quotes must survive.
const rows=[];let row=[],field='',quoted=false;
for(let i=0;i<csv.length;i++){
  const c=csv[i];
  if(c==='"'){if(quoted&&csv[i+1]==='"'){field+='"';i++;}else quoted=!quoted;}
  else if(c===','&&!quoted){row.push(field);field='';}
  else if(c==='\n'&&!quoted){row.push(field.replace(/\r$/,''));rows.push(row);row=[];field='';}
  else field+=c;
}
if(field||row.length){row.push(field);rows.push(row);}
if(quoted)throw new Error('Unclosed CSV quote');
const header=rows.shift();
const names={E01:'ESP32 DevKitC-32',E02:'SHT31-D 온습도 센서',E03:'SEN0193 토양수분 센서',E04:'12V 도우징 펌프',E05:'DFR0457 MOSFET 모듈',E06:'PP-A410 10kg 로드셀',E07:'HX711 증폭 모듈',P01:'12V 5A 완제품 어댑터',P02:'5V 2A USB 어댑터',P03:'USB-A → USB-C 데이터 케이블',P04:'5.5 × 2.1mm DC 잭',P05:'1N4007 다이오드 후보',P06:'비상정지 스위치 후보',P07:'인라인 퓨즈 홀더 후보',C01:'FF 점퍼선',C02:'FM 점퍼선',C03:'MM 점퍼선',C04:'열수축 튜브',C05:'830점 브레드보드',C06:'만능기판',C07:'BOXCO 전장함',W01:'실리콘 연장 튜브',W02:'5L PE 물통',W03:'18cm 사각 화분',W04:'배양토 10L'};
const items=rows.filter(r=>r.length>1).map(r=>{if(r.length!==header.length)throw new Error('CSV field count');const p=Object.fromEntries(header.map((h,i)=>[h,r[i]]));return {...p,name:names[p.id],description:p.description.replace(/ [ABC] ·.*$/,''),qty:Number(p.qty),price:Number(p.price),total:Number(p.total)};});
if(items.length!==25||items.reduce((sum,p)=>sum+p.total,0)!==504891)throw new Error('Procurement snapshot mismatch');
await mkdir('web/data',{recursive:true});await mkdir('web/downloads',{recursive:true});
await writeFile('web/data/bom.json',JSON.stringify({source:'MASTER_v4_20260929_snapshot',price_date:'2026-09-29',current_price_verified:false,items},null,2)+'\n');
await copyFile('research/source/firmware_reference/src/sensor_bringup.ino','web/downloads/sensor-bringup.ino');
console.log('Prepared 25 BOM entries and sensor-only sketch.');
