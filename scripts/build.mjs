import { cp, mkdir, access } from 'node:fs/promises';
const required = ['web/index.html', 'web/app.js', 'web/styles.css', 'web/flycheck.js', 'web/data/flycheck-model.json', 'web/data/demo-cases.json', 'web/data/evaluation.json', 'web/assets/drawings/01-pilot.svg', 'web/downloads/chamgap-assembly-v1.pdf'];
await Promise.all(required.map(p => access(p)));
await mkdir('dist', { recursive: true });
await cp('web', 'dist', { recursive: true });
console.log('Built static site: dist/ (no server credentials or research datasets included)');
