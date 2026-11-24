package com.vsake.keycopier;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;

/** Quick settings shared by all screens. */
public class Settings {
    public static final String LOUPE = "s_loupe", TOUCH_DEPTH = "s_touch_depth", TOUCH_PIN = "s_touch_pin",
            VIBRATE = "s_vibrate", BRIGHT = "s_bright", HINTS = "s_hints", LADDER = "s_ladder";

    private static final String[] KEYS = {LOUPE, TOUCH_DEPTH, TOUCH_PIN, VIBRATE, BRIGHT, HINTS, LADDER};
    private static final String[] LABELS = {
            "Lupa przy dotyku",
            "Dotyk na kluczu zmienia głębokość",
            "Dotyk na kluczu wybiera pin",
            "Wibracja",
            "Pełna jasność ekranu",
            "Podpowiedzi na ekranie",
            "Podziałka głębokości",
    };

    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences("keycopier", Context.MODE_PRIVATE);
    }

    public static boolean get(Context c, String key) { return prefs(c).getBoolean(key, true); }

    /** Shows the quick-settings dialog; onDone runs after the user closes it. */
    public static void show(Activity a, Runnable onDone) {
        final boolean[] v = new boolean[KEYS.length];
        for (int i = 0; i < KEYS.length; i++) v[i] = get(a, KEYS[i]);
        new AlertDialog.Builder(a)
                .setTitle("⚙ Ustawienia")
                .setMultiChoiceItems(LABELS, v, (d, which, checked) -> v[which] = checked)
                .setPositiveButton("OK", (d, w) -> {
                    SharedPreferences.Editor e = prefs(a).edit();
                    for (int i = 0; i < KEYS.length; i++) e.putBoolean(KEYS[i], v[i]);
                    e.apply();
                    if (onDone != null) onDone.run();
                })
                .setNeutralButton("Domyślne", (d, w) -> {
                    SharedPreferences.Editor e = prefs(a).edit();
                    for (String k : KEYS) e.remove(k);
                    e.apply();
                    if (onDone != null) onDone.run();
                })
                .setNegativeButton("Anuluj", null)
                .show();
    }
}
