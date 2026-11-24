package com.vsake.keycopier;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.Toast;

import org.json.JSONException;
import org.json.JSONObject;

import java.util.List;

public class KeyActivity extends Activity {
    public static final String EX_PROFILE = "profile";
    public static final String EX_CODE = "code";
    public static final String EX_MH = "mh";
    public static final String EX_MV = "mv";
    public static final String EX_SAVED = "saved";
    public static final String EX_NAME = "name";

    private KeyView keyView;
    private LinearLayout panel;
    private Profile profile;
    private int savedIndex = -1;
    private String savedName;

    public static Intent intent(Context c, Profile p, int[] code, boolean mh, boolean mv, int savedIdx, String name) {
        Intent i = new Intent(c, KeyActivity.class);
        try { i.putExtra(EX_PROFILE, p.toJson().toString()); } catch (JSONException e) { throw new RuntimeException(e); }
        if (code != null) i.putExtra(EX_CODE, code);
        i.putExtra(EX_MH, mh); i.putExtra(EX_MV, mv);
        i.putExtra(EX_SAVED, savedIdx); i.putExtra(EX_NAME, name);
        return i;
    }

    @Override
    protected void onCreate(Bundle s) {
        super.onCreate(s);
        Intent in = getIntent();
        try { profile = Profile.fromJson(new JSONObject(in.getStringExtra(EX_PROFILE))); }
        catch (Exception e) { finish(); return; }
        int[] code = s != null ? s.getIntArray(EX_CODE) : in.getIntArrayExtra(EX_CODE);
        if (code == null || code.length != profile.pins) code = new int[profile.pins];
        savedIndex = in.getIntExtra(EX_SAVED, -1);
        savedName = in.getStringExtra(EX_NAME);
        boolean mh = s != null ? s.getBoolean(EX_MH) : in.getBooleanExtra(EX_MH, false);
        boolean mv = s != null ? s.getBoolean(EX_MV) : in.getBooleanExtra(EX_MV, false);

        FrameLayout root = new FrameLayout(this);
        keyView = new KeyView(this);
        keyView.setup(profile, code, Store.pxPerMm(this));
        keyView.setMirror(mh, mv);
        root.addView(keyView, new FrameLayout.LayoutParams(-1, -1));

        panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setGravity(Gravity.CENTER_HORIZONTAL);
        int pad = Ui.dp(this, 8);
        panel.setPadding(pad, pad, pad, pad);

        panel.addView(Ui.button(this, "▲", v -> keyView.shiftDepth(+1)), lp(-1));
        LinearLayout row = new LinearLayout(this);
        row.addView(Ui.button(this, "◀", v -> keyView.select(keyView.isMirrorH() ? 1 : -1)), weighted());
        row.addView(Ui.button(this, "▶", v -> keyView.select(keyView.isMirrorH() ? -1 : 1)), weighted());
        panel.addView(row, lp(-1));
        panel.addView(Ui.button(this, "▼", v -> keyView.shiftDepth(-1)), lp(-1));
        panel.addView(Ui.button(this, "💾 Zapisz", v -> save()), lp(-1));
        LinearLayout row2 = new LinearLayout(this);
        row2.addView(Ui.button(this, "⇄", v -> { keyView.setMirror(!keyView.isMirrorH(), keyView.isMirrorV()); placePanel(); }), weighted());
        row2.addView(Ui.button(this, "⇅", v -> keyView.setMirror(keyView.isMirrorH(), !keyView.isMirrorV())), weighted());
        panel.addView(row2, lp(-1));
        panel.addView(Ui.button(this, "Zeruj", v -> keyView.resetCode()), lp(-1));

        root.addView(panel);
        placePanel();
        setContentView(root);
        Ui.immersive(this);
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) Ui.immersive(this);
    }

    private void placePanel() {
        FrameLayout.LayoutParams p = new FrameLayout.LayoutParams(Ui.dp(this, 150), -2);
        p.gravity = Gravity.CENTER_VERTICAL | (keyView.isMirrorH() ? Gravity.START : Gravity.END);
        panel.setLayoutParams(p);
    }

    private LinearLayout.LayoutParams lp(int w) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(w, Ui.dp(this, 48));
        p.topMargin = Ui.dp(this, 4);
        return p;
    }

    private LinearLayout.LayoutParams weighted() {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, -1, 1f);
        p.leftMargin = Ui.dp(this, 2); p.rightMargin = Ui.dp(this, 2);
        return p;
    }

    private void save() {
        final EditText name = new EditText(this);
        name.setHint("np. Drzwi wejściowe");
        if (savedName != null) name.setText(savedName);
        new AlertDialog.Builder(this)
                .setTitle("Zapisz klucz  (" + Store.codeString(profile, keyView.getCode()) + ")")
                .setView(name)
                .setPositiveButton("Zapisz", (d, w) -> {
                    String n = name.getText().toString().trim();
                    if (n.isEmpty()) n = profile.shortName + " " + Store.codeString(profile, keyView.getCode());
                    List<Store.SavedKey> keys = Store.keys(this);
                    Store.SavedKey k = new Store.SavedKey();
                    k.name = n; k.profile = profile; k.code = keyView.getCode().clone();
                    k.mirrorH = keyView.isMirrorH(); k.mirrorV = keyView.isMirrorV();
                    if (savedIndex >= 0 && savedIndex < keys.size()) keys.set(savedIndex, k);
                    else { keys.add(k); savedIndex = keys.size() - 1; }
                    savedName = n;
                    Store.saveKeys(this, keys);
                    Toast.makeText(this, "Zapisano: " + n, Toast.LENGTH_SHORT).show();
                })
                .setNegativeButton("Anuluj", null)
                .show();
    }

    @Override
    protected void onSaveInstanceState(Bundle o) {
        super.onSaveInstanceState(o);
        o.putIntArray(EX_CODE, keyView.getCode());
        o.putBoolean(EX_MH, keyView.isMirrorH());
        o.putBoolean(EX_MV, keyView.isMirrorV());
    }
}
