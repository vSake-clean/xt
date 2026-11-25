// Lista dźwięków, memów i wibracji. Pliki dźwięków robi scripts/gen_sounds.py
// (src/common/snd/<id>_<wersja>.mp3 i <id>.wav).

export const SOUNDS = [
  { id: 'ping' },
  { id: 'kropla' },
  { id: 'dzwonek' },
  { id: 'ptaszek' },
  { id: 'gong' },
  { id: 'klik' },
  { id: 'alarm' },
  { id: 'fanfara' },
  { id: 'wlasny', custom: true }
]

// Memowe dźwięki: prawdziwe nagrania CC0 z Freesound (autorzy w
// zrodla/ZRODLA.md). Tylko piknięcia bomby są syntezowane.
export const MEMES = [
  { id: 'bomba_plant' },
  { id: 'bomba_tik' },
  { id: 'wybuch' },
  { id: 'kliker' },
  { id: 'boom' },
  { id: 'smutna' },
  { id: 'badumtss' },
  { id: 'trabka' },
  { id: 'rura' },
  { id: 'swierszcze' },
  { id: 'boing' },
  { id: 'blad' },
  { id: 'pierd' },
  { id: 'bruh' },
  { id: 'zgrzyt' },
  { id: 'smiech' }
]

// Wzory wibracji: 'b' krótkie uderzenie, 'B' długie, liczba = pauza w ms.
export const VIBES = [
  { id: 'tik', pattern: ['b'] },
  { id: 'podwojny', pattern: ['b', 220, 'b'] },
  { id: 'serce', pattern: ['b', 140, 'b', 650, 'b', 140, 'b'] },
  { id: 'fala', pattern: ['b', 300, 'b', 300, 'B'] },
  { id: 'sos', pattern: ['b', 160, 'b', 160, 'b', 400, 'B', 200, 'B', 200, 'B', 400, 'b', 160, 'b', 160, 'b'] },
  { id: 'alarm', pattern: ['b', 120, 'b', 120, 'b', 120, 'b', 120, 'b', 120, 'b'] },
  { id: 'zegar', pattern: ['b', 900, 'b', 900, 'b', 900, 'b'] },
  { id: 'wlasna', custom: true }
]

// Domyślny własny dźwięk (c e g c') i własna wibracja (tik, tik, BZZ).
export const DEFAULT_NOTES = [1, 3, 5, 8, 0, 0, 0, 0]
export const DEFAULT_VIBE = [1, 0, 1, 0, 2, 0, 0, 0]

export const PER_PAGE = 5

// Rodzaje: 's' dźwięki, 'm' memy, 'v' wibracje.
export function itemsOf(kind) {
  if (kind === 's') return SOUNDS
  if (kind === 'm') return MEMES
  return VIBES
}

export function pagesOf(kind) {
  return Math.ceil(itemsOf(kind).length / PER_PAGE)
}

export function levelKey(kind, id) {
  return kind + ':' + id
}
