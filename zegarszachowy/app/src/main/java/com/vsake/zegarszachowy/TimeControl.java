package com.vsake.zegarszachowy;

import android.content.SharedPreferences;

/** Tempo gry: czas bazowy, dodatek/opóźnienie i opcjonalny drugi okres (np. 90'/40 ruchów + 30'). */
public class TimeControl {
    public static final int FISCHER = 0;   // dodatek po każdym ruchu
    public static final int BRONSTEIN = 1; // zwrot zużytego czasu, maks. N s
    public static final int DELAY = 2;     // opóźnienie: przez N s czas nie płynie

    public String name;
    public long baseMs;
    public long incMs;
    public int mode = FISCHER;
    public int stageMoves;   // 0 = brak drugiego okresu
    public long stageMs;

    public TimeControl(String name, int minutes, int incSec, int mode, int stageMoves, int stageMinutes) {
        this.name = name;
        this.baseMs = minutes * 60000L;
        this.incMs = incSec * 1000L;
        this.mode = mode;
        this.stageMoves = stageMoves;
        this.stageMs = stageMinutes * 60000L;
    }

    public TimeControl(String name, int minutes, int incSec) {
        this(name, minutes, incSec, FISCHER, 0, 0);
    }

    public static final TimeControl[] PRESETS = {
            new TimeControl("Bullet 1+0", 1, 0),
            new TimeControl("Bullet 2+1", 2, 1),
            new TimeControl("Blitz 3+0", 3, 0),
            new TimeControl("Blitz 3+2", 3, 2),
            new TimeControl("Blitz 5+0", 5, 0),
            new TimeControl("Blitz 5+3", 5, 3),
            new TimeControl("Rapid 10+0", 10, 0),
            new TimeControl("Rapid 10+5", 10, 5),
            new TimeControl("Rapid 15+10", 15, 10),
            new TimeControl("Rapid 25+10", 25, 10),
            new TimeControl("Rapid 30+0", 30, 0),
            new TimeControl("Klasyczne 60+30", 60, 30),
            new TimeControl("Klasyczne 90+30", 90, 30),
            new TimeControl("FIDE 90'/40 + 30' +30\"", 90, 30, FISCHER, 40, 30),
            new TimeControl("Klasyczne 120+0", 120, 0),
            new TimeControl("Opóźnienie G/5 d5", 5, 5, DELAY, 0, 0),
    };

    public String describe() {
        StringBuilder sb = new StringBuilder();
        sb.append(fmtMin(baseMs));
        if (stageMoves > 0) sb.append("/").append(stageMoves).append(" ruchów + ").append(fmtMin(stageMs));
        if (incMs > 0) {
            long s = incMs / 1000;
            if (mode == FISCHER) sb.append(" +").append(s).append("s/ruch");
            else if (mode == BRONSTEIN) sb.append(" Bronstein ").append(s).append("s");
            else sb.append(" opóźn. ").append(s).append("s");
        }
        return sb.toString();
    }

    private static String fmtMin(long ms) {
        long sec = ms / 1000;
        if (sec % 60 == 0) return (sec / 60) + "'";
        return (sec / 60) + "'" + (sec % 60) + "\"";
    }

    public void save(SharedPreferences.Editor e) {
        e.putString("tc_name", name);
        e.putLong("tc_base", baseMs);
        e.putLong("tc_inc", incMs);
        e.putInt("tc_mode", mode);
        e.putInt("tc_stage_moves", stageMoves);
        e.putLong("tc_stage_ms", stageMs);
    }

    public static TimeControl load(SharedPreferences p) {
        if (!p.contains("tc_base")) return PRESETS[5];
        TimeControl t = new TimeControl(p.getString("tc_name", "Własne"), 0, 0);
        t.baseMs = p.getLong("tc_base", 300000);
        t.incMs = p.getLong("tc_inc", 0);
        t.mode = p.getInt("tc_mode", FISCHER);
        t.stageMoves = p.getInt("tc_stage_moves", 0);
        t.stageMs = p.getLong("tc_stage_ms", 0);
        return t;
    }
}
