// Lista dźwięków i wibracji. Dźwięki są oryginalne, syntezowane przez
// scripts/gen_sounds.py (pliki src/common/snd/<id>_<wersja>.mp3/.wav).

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

export function itemsOf(kind) {
  return kind === 's' ? SOUNDS : VIBES
}

export function levelKey(kind, id) {
  return kind + ':' + id
}
