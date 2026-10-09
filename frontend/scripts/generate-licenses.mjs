import { readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const lock = JSON.parse(await readFile(path.join(root, 'package-lock.json'), 'utf8'));
const notices = ['Euclid — third-party runtime licenses\n'];

for (const [location, metadata] of Object.entries(lock.packages)) {
  if (!location || metadata.dev) continue;
  const directory = path.join(root, location);
  const manifest = JSON.parse(await readFile(path.join(directory, 'package.json'), 'utf8'));
  const files = (await readdir(directory, { withFileTypes: true }))
    .filter((entry) => entry.isFile() && /^(?:license|copying|notice|copyright)/i.test(entry.name))
    .map((entry) => entry.name).sort();
  if (!files.length) throw new Error(`Missing license text for ${manifest.name}`);
  notices.push(`\n${'='.repeat(72)}\n${manifest.name}@${manifest.version} (${metadata.license ?? 'see terms below'})\n`);
  for (const file of files) notices.push((await readFile(path.join(directory, file), 'utf8')).replace(/\r\n/g, '\n'));
}

await writeFile(path.join(root, 'public/THIRD_PARTY_LICENSES.txt'), notices.join('\n'));
