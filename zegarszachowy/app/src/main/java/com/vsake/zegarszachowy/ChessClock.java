package com.vsake.zegarszachowy;

import android.content.SharedPreferences;

/** Logika zegara, liczona od SystemClock.elapsedRealtime() (niezależna od zmiany godziny w telefonie). */
public class ChessClock {
    public static final int NONE = -1;

    public TimeControl tc;
    public final long[] remain = new long[2];
    public final int[] moves = new int[2];
    public int active = NONE;      // czyj zegar chodzi
    public boolean paused;
    public int flagged = NONE;     // komu spadła flaga
    private long turnUsed;         // czas zużyty w bieżącym ruchu przed bieżącym odcinkiem
    private long segStart;         // początek bieżącego odcinka (elapsedRealtime)

    public ChessClock(TimeControl tc) {
        reset(tc);
    }

    public void reset(TimeControl tc) {
        this.tc = tc;
        remain[0] = remain[1] = tc.baseMs;
        moves[0] = moves[1] = 0;
        active = NONE;
        paused = false;
        flagged = NONE;
        turnUsed = 0;
    }

    public boolean started() { return active != NONE || flagged != NONE; }
    public boolean running() { return active != NONE && !paused && flagged == NONE; }

    private long turnElapsed(long now) {
        return turnUsed + (running() ? now - segStart : 0);
    }

    /** Czas do wyświetlenia dla gracza p. */
    public long display(int p, long now) {
        if (p != active || flagged != NONE) return remain[p];
        long used = turnElapsed(now);
        if (tc.mode == TimeControl.DELAY) used = Math.max(0, used - tc.incMs);
        return remain[p] - used;
    }

    /** Pozostałe opóźnienie w trybie DELAY (0 gdy brak). */
    public long delayLeft(int p, long now) {
        if (tc.mode != TimeControl.DELAY || p != active || flagged != NONE) return 0;
        return Math.max(0, tc.incMs - turnElapsed(now));
    }

    /** @return true, jeśli właśnie spadła flaga. */
    public boolean tick(long now) {
        if (!running()) return false;
        if (display(active, now) <= 0) {
            remain[active] = 0;
            turnUsed = 0;
            flagged = active;
            return true;
        }
        return false;
    }

    /** Gracz p nacisnął swoją połowę ekranu. @return true, jeśli zmieniono stan. */
    public boolean press(int p, long now) {
        if (flagged != NONE || paused) return false;
        if (active == NONE) {          // start: grający czarnymi uruchamia zegar białych
            active = 1 - p;
            turnUsed = 0;
            segStart = now;
            return true;
        }
        if (active != p) return false;
        if (tick(now)) return true;
        long used = turnElapsed(now);
        long r = display(p, now);
        if (tc.mode == TimeControl.FISCHER) r += tc.incMs;
        else if (tc.mode == TimeControl.BRONSTEIN) r += Math.min(used, tc.incMs);
        moves[p]++;
        if (tc.stageMoves > 0 && moves[p] == tc.stageMoves) r += tc.stageMs;
        remain[p] = r;
        active = 1 - p;
        turnUsed = 0;
        segStart = now;
        return true;
    }

    public void pause(long now) {
        if (!running()) return;
        turnUsed += now - segStart;
        paused = true;
    }

    public void resume(long now) {
        if (!paused) return;
        paused = false;
        segStart = now;
    }

    /** Korekta sędziowska (tylko w pauzie / przed startem). */
    public void setTime(int p, long ms, int mv) {
        remain[p] = ms;
        moves[p] = mv;
        if (p == active) turnUsed = 0;
        if (flagged == p && ms > 0) flagged = NONE;
    }

    public void save(SharedPreferences.Editor e, long now) {
        e.putLong("c_r0", remain[0]).putLong("c_r1", remain[1])
                .putInt("c_m0", moves[0]).putInt("c_m1", moves[1])
                .putInt("c_active", active).putBoolean("c_paused", paused)
                .putInt("c_flag", flagged).putLong("c_used", turnElapsed(now))
                .putLong("c_now", now).putBoolean("c_saved", true);
    }

    public void load(SharedPreferences p, long now) {
        if (!p.getBoolean("c_saved", false)) return;
        remain[0] = p.getLong("c_r0", remain[0]);
        remain[1] = p.getLong("c_r1", remain[1]);
        moves[0] = p.getInt("c_m0", 0);
        moves[1] = p.getInt("c_m1", 0);
        active = p.getInt("c_active", NONE);
        paused = p.getBoolean("c_paused", false);
        flagged = p.getInt("c_flag", NONE);
        turnUsed = p.getLong("c_used", 0);
        long savedNow = p.getLong("c_now", now);
        if (running()) {
            if (savedNow <= now) {
                segStart = savedNow;   // zegar chodził dalej, gdy aplikacja była zamknięta
            } else {                    // telefon zrestartowany – zatrzymaj
                paused = true;
            }
        }
    }
}
