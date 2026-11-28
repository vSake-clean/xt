package com.vsake.zegarszachowy;

import android.app.Activity;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.text.InputType;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

public class SettingsActivity extends Activity {
    private SharedPreferences prefs;
    private LinearLayout col;

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        prefs = getSharedPreferences("clock", MODE_PRIVATE);
        ScrollView sv = new ScrollView(this);
        sv.setBackgroundColor(0xFF101418);
        col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(16);
        col.setPadding(pad, pad, pad, pad);
        sv.addView(col);
        setContentView(sv);

        TimeControl cur = TimeControl.load(prefs);
        header("Tempo gry");
        label("Obecnie: " + cur.name + " (" + cur.describe() + ")");

        LinearLayout row = null;
        for (int i = 0; i < TimeControl.PRESETS.length; i++) {
            if (i % 2 == 0) {
                row = new LinearLayout(this);
                col.addView(row);
            }
            final TimeControl tc = TimeControl.PRESETS[i];
            Button btn = new Button(this);
            btn.setText(tc.name);
            btn.setAllCaps(false);
            btn.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
            btn.setOnClickListener(new View.OnClickListener() {
                @Override public void onClick(View v) { choose(tc); }
            });
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, dp(56), 1f);
            lp.setMargins(dp(2), dp(2), dp(2), dp(2));
            row.addView(btn, lp);
        }
        if (TimeControl.PRESETS.length % 2 == 1) row.addView(new View(this), new LinearLayout.LayoutParams(0, 1, 1f));

        header("Własne tempo");
        final EditText min = field("Minuty na partię", cur.baseMs / 60000);
        final EditText sec = field("+ sekundy", cur.baseMs / 1000 % 60);
        final EditText inc = field("Dodatek / opóźnienie (s na ruch)", cur.incMs / 1000);
        final RadioGroup mode = new RadioGroup(this);
        String[] modes = {"Fischer – dodatek po każdym ruchu (FIDE)", "Bronstein – zwrot zużytego czasu",
                "Opóźnienie (delay) – czas startuje po N s"};
        for (int i = 0; i < modes.length; i++) {
            RadioButton rb = new RadioButton(this);
            rb.setText(modes[i]);
            rb.setTextColor(Color.WHITE);
            rb.setId(100 + i);
            mode.addView(rb);
        }
        mode.check(100 + cur.mode);
        col.addView(mode);
        final CheckBox stage = new CheckBox(this);
        stage.setText("Drugi okres (kontrola po X ruchach)");
        stage.setTextColor(Color.WHITE);
        stage.setChecked(cur.stageMoves > 0);
        col.addView(stage);
        final EditText sMoves = field("Po ilu ruchach", cur.stageMoves > 0 ? cur.stageMoves : 40);
        final EditText sMin = field("Ile minut dodać", cur.stageMoves > 0 ? cur.stageMs / 60000 : 30);

        Button start = new Button(this);
        start.setText("Ustaw własne tempo");
        start.setAllCaps(false);
        start.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                int m = num(min), s = num(sec), in = num(inc);
                if (m * 60 + s <= 0) {
                    Toast.makeText(SettingsActivity.this, "Podaj czas większy od zera", Toast.LENGTH_SHORT).show();
                    return;
                }
                boolean st = stage.isChecked() && num(sMoves) > 0;
                TimeControl tc = new TimeControl("Własne", m, in, mode.getCheckedRadioButtonId() - 100,
                        st ? num(sMoves) : 0, st ? num(sMin) : 0);
                tc.baseMs += s * 1000L;
                choose(tc);
            }
        });
        col.addView(start, new LinearLayout.LayoutParams(-1, dp(56)));

        header("Inne");
        final CheckBox vib = new CheckBox(this);
        vib.setText("Wibracja przy naciśnięciu");
        vib.setTextColor(Color.WHITE);
        vib.setChecked(prefs.getBoolean("vibrate", true));
        vib.setOnCheckedChangeListener((bt, c) -> prefs.edit().putBoolean("vibrate", c).apply());
        col.addView(vib);
        final CheckBox snd = new CheckBox(this);
        snd.setText("Dźwięk przy naciśnięciu");
        snd.setTextColor(Color.WHITE);
        snd.setChecked(prefs.getBoolean("sound", true));
        snd.setOnCheckedChangeListener((bt, c) -> prefs.edit().putBoolean("sound", c).apply());
        col.addView(snd);
        label("Połóż telefon między graczami. Każdy dotyka swojej połowy ekranu po wykonaniu ruchu. "
                + "Na początku gracz z czarnymi dotyka swojej strony, co uruchamia zegar białych. "
                + "⏸ pauza (np. wezwanie sędziego), ± korekta czasu i liczby ruchów, ↺ nowa partia. "
                + "Ekran nie gaśnie, a czas liczony jest dalej nawet po zamknięciu aplikacji.");
    }

    private void choose(TimeControl tc) {
        SharedPreferences.Editor e = prefs.edit();
        tc.save(e);
        e.apply();
        setResult(RESULT_OK);
        finish();
    }

    private void header(String s) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextColor(0xFF81C784);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, 20);
        t.setPadding(0, dp(18), 0, dp(6));
        col.addView(t);
    }

    private void label(String s) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextColor(0xFFB0BEC5);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        t.setPadding(0, dp(4), 0, dp(4));
        col.addView(t);
    }

    private EditText field(String hint, long value) {
        LinearLayout row = new LinearLayout(this);
        row.setGravity(Gravity.CENTER_VERTICAL);
        TextView l = new TextView(this);
        l.setText(hint);
        l.setTextColor(Color.WHITE);
        EditText e = new EditText(this);
        e.setInputType(InputType.TYPE_CLASS_NUMBER);
        e.setText(String.valueOf(value));
        e.setTextColor(Color.WHITE);
        e.setGravity(Gravity.CENTER);
        row.addView(l, new LinearLayout.LayoutParams(0, -2, 2f));
        row.addView(e, new LinearLayout.LayoutParams(0, -2, 1f));
        col.addView(row);
        return e;
    }

    private static int num(EditText e) {
        try { return Math.max(0, Integer.parseInt(e.getText().toString().trim())); }
        catch (NumberFormatException ex) { return 0; }
    }

    private int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density + 0.5f);
    }
}
