// Poziomy głośności 1..1000 i plany odtwarzania (czysty JS, testowalny).
//
// Dźwięk: poziom zamienia się na wzmocnienie od 0.001 (poziom 1, -60 dB,
// prawie szept) do 1.0 (poziom 1000). Skala jest logarytmiczna, więc każdy
// krok w górę jest tak samo słyszalny na dole i na górze skali. Każdy dźwięk
// jest zapisany w trzech wersjach (pełna, -20 dB, -40 dB). Aplikacja bierze
// najcichszą wersję, która jeszcze wystarcza, a resztę ustawia przez
// audio.volume. Dzięki temu poziom 1 jest bardzo cichy nawet wtedy, gdy
// zegarek zaokrągla głośność odtwarzacza do kilku stopni.
//
// Wibracja: Redmi Watch 4 ma tylko vibrator.vibrate({mode:'short'|'long'}),
// siły silnika nie da się zmienić. Poziom wydłuża więc "uderzenie": poziom 1
// to jeden najkrótszy impuls (najsłabsza wibracja, jaką zegarek umie),
// wyższe poziomy dokładają kolejne impulsy, aż do ok. 0,4 s ciągłego brzęczenia.

export const MIN = 1
export const MAX = 1000
export const DEFAULT = 1

// Wersje plików dźwięku: _0 pełna, _1 -20 dB, _2 -40 dB.
export const TIERS = [1, 0.1, 0.01]

// Odstęp między krótkimi impulsami wibracji (ms) i najdłuższe uderzenie.
export const PULSE_MS = 40
export const MAX_PULSES = 10
export const LONG_FACTOR = 2.5

export function clamp(v) {
  v = Math.round(Number(v))
  if (!(v >= MIN)) return MIN
  if (v > MAX) return MAX
  return v
}

// Wzmocnienie 0.001..1 dla poziomu 1..1000.
export function gain(level) {
  const s = (clamp(level) - MIN) / (MAX - MIN)
  return Math.pow(10, 3 * s - 3)
}

// Który plik mp3 (0/1/2) i jaka głośność odtwarzacza (0.1..1].
// gain to całkowita głośność, używana dla zapasowego pliku .wav
// (jest tylko w jednej, pełnej wersji).
export function soundPlan(level) {
  const g = gain(level)
  let tier = 0
  for (let t = TIERS.length - 1; t >= 0; t--) {
    if (TIERS[t] >= g - 1e-9) {
      tier = t
      break
    }
  }
  let volume = g / TIERS[tier]
  if (volume > 1) volume = 1
  volume = Math.round(volume * 10000) / 10000
  return { tier: tier, volume: volume, gain: Math.round(g * 1000000) / 1000000 }
}

// Ile krótkich impulsów składa się na jedno uderzenie wibracji.
export function pulses(level) {
  const s = (clamp(level) - MIN) / (MAX - MIN)
  return 1 + Math.floor(s * (MAX_PULSES - 1) + 1e-9)
}

export function longPulses(level) {
  return Math.max(3, Math.round(pulses(level) * LONG_FACTOR))
}

// Wzór wibracji: 'b' krótkie uderzenie, 'B' długie, liczba = pauza w ms.
// Wynik: chwile (ms od startu), w których trzeba wywołać vibrate('short').
export function vibeTimes(pattern, level) {
  const n = pulses(level)
  const nl = longPulses(level)
  const out = []
  let t = 0
  for (let i = 0; i < pattern.length; i++) {
    const p = pattern[i]
    if (p === 'b' || p === 'B') {
      const k = p === 'b' ? n : nl
      for (let j = 0; j < k; j++) out.push(t + j * PULSE_MS)
      t += k * PULSE_MS
    } else {
      t += Math.max(0, Number(p) || 0)
    }
  }
  return out
}

// Własna wibracja: 8 kroków, 0 = pauza, 1 = tik, 2 = BZZ.
export const VIBE_STEPS = 8
export const VIBE_OPTIONS = 3
export function customVibePattern(steps) {
  const out = []
  for (let i = 0; i < steps.length; i++) {
    const v = steps[i]
    if (v === 1) out.push('b', 160)
    else if (v === 2) out.push('B', 160)
    else out.push(320)
  }
  while (out.length && typeof out[out.length - 1] === 'number') out.pop()
  return out
}

// Własny dźwięk: 8 kroków, 0 = pauza, 1..8 = nuty c d e f g a h c'.
export const NOTE_STEPS = 8
export const NOTE_OPTIONS = 9
export const NOTE_MS = 260

export function normalizeSteps(raw, len, options, fallback) {
  const out = []
  for (let i = 0; i < len; i++) {
    const v = raw && raw.length > i ? Math.round(Number(raw[i])) : fallback[i]
    out.push(v >= 0 && v < options ? v : 0)
  }
  return out
}

// Poziomy są zapisywane osobno dla każdego dźwięku i każdej wibracji.
// Brak wpisu = poziom 1, czyli wszystko startuje super cicho.
export function getLevel(map, key) {
  if (!map || typeof map !== 'object' || map[key] === undefined) return DEFAULT
  return clamp(map[key])
}

export function setLevel(map, key, level) {
  const m = map && typeof map === 'object' ? map : {}
  m[key] = clamp(level)
  return m
}

export function parseLevels(text) {
  try {
    const raw = JSON.parse(text)
    const out = {}
    if (raw && typeof raw === 'object') {
      for (const k in raw) out[k] = clamp(raw[k])
    }
    return out
  } catch (e) {
    return {}
  }
}

export function digits(level) {
  return String(clamp(level)).split('')
}
