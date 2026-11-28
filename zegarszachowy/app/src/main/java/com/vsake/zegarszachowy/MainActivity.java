package com.vsake.zegarszachowy;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.media.AudioManager;
import android.media.ToneGenerator;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.text.InputType;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.util.Locale;

public class MainActivity extends Activity {
    static final int REQ_SETTINGS = 1;
    static final int C_IDLE = 0xFF37474F, C_ACTIVE = 0xFF2E7D32, C_PAUSED = 0xFFF9A825,
            C_FLAG = 0xFFB71C1C, C_LOW = 0xFFE65100, C_BAR = 0xFF101418;

    private SharedPreferences prefs;
    private ChessClock clock;
    private final Panel[] panels = new Panel[2];   // 0 = góra (obrócona), 1 = dół
    private Button btnPause, btnSound, btnEdit;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private ToneGenerator tone;
    private Vibrator vibrator;
    private boolean sound, vibrate;

    private final Runnable ticker = new Runnable() {
        @Override public void run() {
            long now = SystemClock.elapsedRealtime();
            if (clock.tick(now)) onFlag();
            refresh();
            if (clock.running()) handler.postDelayed(this, 50);
        }
    };

    class Panel {
        final int player;
        final FrameLayout root;
        final TextView time, info, top;
        String lastText = "";

        Panel(Context ctx, int player) {
            this.player = player;
            root = new FrameLayout(ctx);
            LinearLayout col = new LinearLayout(ctx);
            col.setOrientation(LinearLayout.VERTICAL);
            col.setGravity(Gravity.CENTER);
            top = text(ctx, 18);
            time = new TextView(ctx);
            time.setGravity(Gravity.CENTER);
            time.setTextColor(Color.WHITE);
            time.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
            time.setIncludeFontPadding(false);
            if (Build.VERSION.SDK_INT >= 21) time.setFontFeatureSettings("tnum");
            info = text(ctx, 18);
            col.addView(top, wrap());
            col.addView(time, wrap());
            col.addView(info, wrap());
            root.addView(col, new FrameLayout.LayoutParams(-1, -1));
            root.setOnTouchListener(new View.OnTouchListener() {
                @Override public boolean onTouch(View v, MotionEvent e) {
                    if (e.getActionMasked() == MotionEvent.ACTION_DOWN) onPress(Panel.this.player);
                    return true;
                }
            });
            if (player == 0) root.setRotation(180f);
        }

        void setTime(String s, int color) {
            time.setTextColor(color);
            if (s.length() != lastText.length()) fit(s);
            if (!s.equals(lastText)) time.setText(s);
            lastText = s;
        }

        void fit(String s) {
            int w = root.getWidth(), h = root.getHeight();
            if (w == 0 || h == 0) { lastText = ""; return; }
            Paint p = new Paint();
            p.setTypeface(time.getTypeface());
            p.setTextSize(100);
            if (Build.VERSION.SDK_INT >= 21) p.setFontFeatureSettings("tnum");
            float byW = (w * 0.92f) / p.measureText(s) * 100f;
            float byH = h * 0.55f;
            time.setTextSize(TypedValue.COMPLEX_UNIT_PX, Math.min(byW, byH));
        }
    }

    private static TextView text(Context ctx, int sp) {
        TextView t = new TextView(ctx);
        t.setGravity(Gravity.CENTER);
        t.setTextColor(0xDDFFFFFF);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp);
        return t;
    }

    private static LinearLayout.LayoutParams wrap() {
        return new LinearLayout.LayoutParams(-1, -2);
    }

    @Override protected void onCreate(Bundle b) {
        super.onCreate(b);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        prefs = getSharedPreferences("clock", MODE_PRIVATE);
        sound = prefs.getBoolean("sound", true);
        vibrate = prefs.getBoolean("vibrate", true);
        clock = new ChessClock(TimeControl.load(prefs));
        clock.load(prefs, SystemClock.elapsedRealtime());
        vibrator = (Vibrator) getSystemService(VIBRATOR_SERVICE);
        try { tone = new ToneGenerator(AudioManager.STREAM_MUSIC, 70); } catch (RuntimeException ignored) { }

        LinearLayout main = new LinearLayout(this);
        main.setOrientation(LinearLayout.VERTICAL);
        main.setBackgroundColor(C_BAR);
        panels[0] = new Panel(this, 0);
        panels[1] = new Panel(this, 1);

        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setBackgroundColor(C_BAR);
        btnPause = barButton(bar, "⏸");
        Button btnReset = barButton(bar, "↺");
        btnEdit = barButton(bar, "±");
        Button btnSet = barButton(bar, "⚙");
        btnSound = barButton(bar, "");

        btnPause.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { togglePause(); }
        });
        btnReset.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { askReset(); }
        });
        btnEdit.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { editTimes(); }
        });
        btnSet.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { openSettings(); }
        });
        btnSound.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                sound = !sound;
                prefs.edit().putBoolean("sound", sound).apply();
                refresh();
            }
        });

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, 0, 1f);
        int m = dp(3);
        lp.setMargins(m, m, m, m);
        main.addView(panels[0].root, lp);
        main.addView(bar, new LinearLayout.LayoutParams(-1, dp(64)));
        LinearLayout.LayoutParams lp2 = new LinearLayout.LayoutParams(-1, 0, 1f);
        lp2.setMargins(m, m, m, m);
        main.addView(panels[1].root, lp2);
        setContentView(main);

        panels[1].root.addOnLayoutChangeListener(new View.OnLayoutChangeListener() {
            @Override public void onLayoutChange(View v, int l, int t, int r, int bo, int ol, int ot, int or, int ob) {
                panels[0].lastText = "";
                panels[1].lastText = "";
                refresh();
            }
        });
        refresh();
        if (clock.running()) handler.post(ticker);
    }

    private Button barButton(LinearLayout bar, String label) {
        Button b = new Button(this);
        b.setText(label);
        b.setTextSize(TypedValue.COMPLEX_UNIT_SP, 26);
        b.setTextColor(Color.WHITE);
        b.setBackgroundColor(Color.TRANSPARENT);
        b.setAllCaps(false);
        b.setPadding(0, 0, 0, 0);
        bar.addView(b, new LinearLayout.LayoutParams(0, -1, 1f));
        return b;
    }

    private int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density + 0.5f);
    }

    private void onPress(int p) {
        long now = SystemClock.elapsedRealtime();
        boolean wasStarted = clock.started();
        if (clock.paused) {
            Toast.makeText(this, "Pauza – wznów przyciskiem ▶", Toast.LENGTH_SHORT).show();
            return;
        }
        if (!clock.press(p, now)) return;
        if (clock.flagged != ChessClock.NONE) { onFlag(); refresh(); return; }
        feedback();
        handler.removeCallbacks(ticker);
        handler.post(ticker);
        if (!wasStarted) refresh();
    }

    private void feedback() {
        if (sound && tone != null) tone.startTone(ToneGenerator.TONE_PROP_BEEP, 40);
        if (vibrate) vib(25);
    }

    private void vib(long ms) {
        if (vibrator == null || !vibrator.hasVibrator()) return;
        if (Build.VERSION.SDK_INT >= 26) vibrator.vibrate(VibrationEffect.createOneShot(ms, VibrationEffect.DEFAULT_AMPLITUDE));
        else vibrator.vibrate(ms);
    }

    private void onFlag() {
        if (sound && tone != null) tone.startTone(ToneGenerator.TONE_CDMA_ALERT_CALL_GUARD, 1200);
        if (vibrate) vib(700);
        saveState();
    }

    private void togglePause() {
        long now = SystemClock.elapsedRealtime();
        if (clock.running()) {
            clock.pause(now);
            handler.removeCallbacks(ticker);
        } else if (clock.paused) {
            clock.resume(now);
            handler.post(ticker);
        } else {
            return;
        }
        saveState();
        refresh();
    }

    private void askReset() {
        if (!clock.started()) { resetClock(); return; }
        pauseIfRunning();
        new AlertDialog.Builder(this)
                .setTitle("Nowa partia?")
                .setMessage("Zegar zostanie wyzerowany do tempa: " + clock.tc.describe())
                .setPositiveButton("Tak", (d, w) -> resetClock())
                .setNegativeButton("Nie", null)
                .show();
    }

    private void pauseIfRunning() {
        if (clock.running()) {
            clock.pause(SystemClock.elapsedRealtime());
            handler.removeCallbacks(ticker);
            refresh();
        }
    }

    private void resetClock() {
        handler.removeCallbacks(ticker);
        clock.reset(TimeControl.load(prefs));
        saveState();
        refresh();
    }

    private void openSettings() {
        if (clock.running()) {
            Toast.makeText(this, "Najpierw zatrzymaj zegar (⏸)", Toast.LENGTH_SHORT).show();
            return;
        }
        startActivityForResult(new Intent(this, SettingsActivity.class), REQ_SETTINGS);
    }

    @Override protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        vibrate = prefs.getBoolean("vibrate", true);
        sound = prefs.getBoolean("sound", true);
        if (req == REQ_SETTINGS && res == RESULT_OK) resetClock();
        refresh();
    }

    /** Korekta sędziowska czasu i liczby ruchów. */
    private void editTimes() {
        pauseIfRunning();
        long now = SystemClock.elapsedRealtime();
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(20), dp(8), dp(20), 0);
        final EditText[] t = new EditText[2], mv = new EditText[2];
        String[] names = {"Gracz u góry", "Gracz na dole"};
        for (int p = 0; p < 2; p++) {
            TextView l = new TextView(this);
            l.setText(names[p] + " – czas (g:mm:ss lub mm:ss) i ruchy");
            box.addView(l);
            LinearLayout row = new LinearLayout(this);
            t[p] = new EditText(this);
            t[p].setInputType(InputType.TYPE_CLASS_DATETIME | InputType.TYPE_DATETIME_VARIATION_TIME);
            t[p].setText(fmtEdit(Math.max(0, clock.display(p, now))));
            mv[p] = new EditText(this);
            mv[p].setInputType(InputType.TYPE_CLASS_NUMBER);
            mv[p].setText(String.valueOf(clock.moves[p]));
            row.addView(t[p], new LinearLayout.LayoutParams(0, -2, 2f));
            row.addView(mv[p], new LinearLayout.LayoutParams(0, -2, 1f));
            box.addView(row);
        }
        new AlertDialog.Builder(this)
                .setTitle("Korekta zegara")
                .setView(box)
                .setPositiveButton("Zapisz", (d, w) -> {
                    for (int p = 0; p < 2; p++) {
                        long ms = parseTime(t[p].getText().toString());
                        int moves;
                        try { moves = Integer.parseInt(mv[p].getText().toString().trim()); }
                        catch (NumberFormatException e) { moves = clock.moves[p]; }
                        if (ms >= 0) clock.setTime(p, ms, moves);
                    }
                    saveState();
                    refresh();
                })
                .setNegativeButton("Anuluj", null)
                .show();
    }

    static long parseTime(String s) {
        try {
            String[] parts = s.trim().replace('.', ':').replace(',', ':').split(":");
            long sec = 0;
            for (String part : parts) sec = sec * 60 + Long.parseLong(part.trim());
            return sec * 1000;
        } catch (NumberFormatException e) {
            return -1;
        }
    }

    static String fmtEdit(long ms) {
        long s = (ms + 999) / 1000;
        if (s >= 3600) return String.format(Locale.US, "%d:%02d:%02d", s / 3600, s / 60 % 60, s % 60);
        return String.format(Locale.US, "%d:%02d", s / 60, s % 60);
    }

    static String fmt(long ms) {
        if (ms <= 0) return "0:00.0";
        if (ms < 20000) return String.format(Locale.US, "0:%02d.%d", ms / 1000, (ms / 100) % 10);
        long s = (ms + 999) / 1000;
        if (s >= 3600) return String.format(Locale.US, "%d:%02d:%02d", s / 3600, s / 60 % 60, s % 60);
        return String.format(Locale.US, "%d:%02d", s / 60, s % 60);
    }

    private void refresh() {
        long now = SystemClock.elapsedRealtime();
        for (int p = 0; p < 2; p++) {
            Panel pn = panels[p];
            long ms = clock.display(p, now);
            int bg, fg = Color.WHITE;
            boolean isActive = clock.active == p;
            if (clock.flagged == p) bg = C_FLAG;
            else if (isActive && clock.paused) { bg = C_PAUSED; fg = 0xFF1B1B1B; }
            else if (isActive) bg = ms < 10000 ? C_LOW : C_ACTIVE;
            else { bg = C_IDLE; fg = 0xFFB0BEC5; }
            pn.root.setBackgroundColor(bg);
            pn.setTime(fmt(ms), fg);
            pn.info.setTextColor(fg);
            pn.top.setTextColor(fg);

            String top;
            if (clock.flagged == p) top = "CZAS MINĄŁ";
            else if (clock.flagged != ChessClock.NONE) top = "Wygrana na czas";
            else if (!clock.started()) top = clock.tc.describe();
            else if (isActive && clock.paused) top = "PAUZA";
            else top = "";
            pn.top.setText(top);

            StringBuilder info = new StringBuilder();
            if (!clock.started()) {
                info.append("Czarne: dotknij swojej strony,\naby uruchomić zegar białych");
            } else {
                info.append("Ruchy: ").append(clock.moves[p]);
                long dl = clock.delayLeft(p, now);
                if (dl > 0) info.append("   opóźn. ").append((dl + 999) / 1000).append("s");
                TimeControl tc = clock.tc;
                if (tc.stageMoves > 0 && clock.moves[p] < tc.stageMoves)
                    info.append("   do kontroli: ").append(tc.stageMoves - clock.moves[p]);
            }
            pn.info.setText(info);
        }
        btnPause.setText(clock.paused ? "▶" : "⏸");
        btnPause.setEnabled(clock.running() || clock.paused);
        btnPause.setAlpha(btnPause.isEnabled() ? 1f : 0.35f);
        btnSound.setText(sound ? "🔊" : "🔇");
    }

    private void saveState() {
        SharedPreferences.Editor e = prefs.edit();
        clock.save(e, SystemClock.elapsedRealtime());
        e.apply();
    }

    @Override protected void onPause() {
        super.onPause();
        saveState();
    }

    @Override protected void onResume() {
        super.onResume();
        hideBars();
        handler.removeCallbacks(ticker);
        handler.post(ticker);
    }

    @Override protected void onDestroy() {
        super.onDestroy();
        handler.removeCallbacks(ticker);
        if (tone != null) tone.release();
    }

    @Override public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideBars();
    }

    @SuppressWarnings("deprecation")
    private void hideBars() {
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN);
    }

    @SuppressWarnings("deprecation")
    @Override public void onBackPressed() {
        if (clock.running()) {
            Toast.makeText(this, "Zegar chodzi – zatrzymaj go (⏸), aby wyjść", Toast.LENGTH_SHORT).show();
            return;
        }
        super.onBackPressed();
    }
}
