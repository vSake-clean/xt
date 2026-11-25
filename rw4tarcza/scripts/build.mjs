// Kompiluje build/face.json do pliku .bin tarczy dla Redmi Watch 4.
// Używa otwartego packera z projektu Watchface Designer
// (https://github.com/calinhoria/watchface-designer), czysty JS bez zależności.
//
//   node scripts/build.mjs <ścieżka do watchface-designer> [wyjście.bin]
import { createRequire } from 'node:module'
import fs from 'node:fs'
import path from 'node:path'

const designer = process.argv[2]
const out = process.argv[3] || 'Nocna.bin'
if (!designer) {
  console.error('Użycie: node scripts/build.mjs <watchface-designer> [wyjście.bin]')
  process.exit(1)
}
const require = createRequire(import.meta.url)
const { compileFaceProject } = require(path.resolve(designer, 'core/packer.js'))
const { unpack } = require(path.resolve(designer, 'core/unpacker.js'))

const face = JSON.parse(fs.readFileSync(new URL('../build/face.json', import.meta.url)))
const raw = (im) => ({ width: im.width, height: im.height, data: Buffer.from(im.rgba, 'base64') })
const images = {}
for (const [name, im] of Object.entries(face.images)) images[name] = raw(im)

const { bin, warnings } = compileFaceProject({
  deviceType: face.deviceType,
  title: face.title,
  faceId: face.faceId,
  slots: [{ widgets: face.widgets, images, preview: raw(face.preview), aod: false }]
})
for (const w of warnings || []) console.log('uwaga:', w)
fs.writeFileSync(out, bin)

// weryfikacja: rozpakuj i porównaj podstawowe dane
const re = unpack(bin)
// Numer tarczy w stylu oficjalnego kompilatora (1672100xx) sprawia, że
// unpacker rozpoznaje typ 7 (ekran 390x450, jak działające tarcze z Mi Create
// dla Redmi Watch 4), a numer zaczynający się od 365 daje typ 365.
const sameScreen = [face.deviceType, 7]
const ok = re.version === 2 && sameScreen.includes(re.watchType) && re.title === face.title &&
  re.slots.length === 1
console.log('zapisano', out, bin.length, 'B; wersja', re.version, '; zegarek', re.watchType,
  '; tytuł', JSON.stringify(re.title), '; widgety', re.slots[0].widgets.length)
if (!ok) { console.error('BŁĄD weryfikacji'); process.exit(1) }
