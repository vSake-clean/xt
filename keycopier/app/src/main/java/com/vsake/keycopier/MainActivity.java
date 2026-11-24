package com.vsake.keycopier;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Typeface;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.util.List;
import java.util.Locale;

public class MainActivity extends Activity {
    private LinearLayout list;

    @Override
    protected void onCreate(Bundle s) {
        super.onCreate(s);
        ScrollView sv = new ScrollView(this);
        sv.setBackgroundColor(0xFF121212);
        list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        int pad = Ui.dp(this, 16);
        list.setPadding(pad, pad, pad, pad);
        sv.addView(list);
        setContentView(sv);
    }

    @Override
    protected void onResume() {
        super.onResume();
        build();
    }

    private void build() {
        list.removeAllViews();
        TextView title = new TextView(this);
        title.setText("🔑 Key Copier");
        title.setTextSize(28);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(0xFFFF8C1A);
        list.addView(title);

        TextView info = text(Store.isCalibrated(this)
                ? String.format(Locale.US, "Ekran skalibrowany (%.2f px/mm)", Store.pxPerMm(this))
                : "⚠ Ekran nieskalibrowany – zrób kalibrację kartą, inaczej wymiary mogą się nie zgadzać.", 14);
        info.setTextColor(Store.isCalibrated(this) ? 0xFF9E9E9E : 0xFFFFC107);
        list.addView(info);
        list.addView(Ui.button(this, "⚙ Ustawienia (lupa, dotyk, wibracja…)", v -> Settings.show(this, null)), lp());
        list.addView(Ui.button(this, "📏 Kalibracja ekranu (karta)",
                v -> startActivity(new Intent(this, CalibrationActivity.class))), lp());

        header("1. Wybierz profil klucza");
        for (Profile p : Profile.builtIns()) addProfile(p, -1);
        List<Profile> custom = Store.customProfiles(this);
        for (int i = 0; i < custom.size(); i++) addProfile(custom.get(i), i);
        list.addView(Ui.button(this, "＋ Nowy własny profil", v -> editProfile(null, -1)), lp());
        list.addView(Ui.button(this, "📥 Importuj profil (wklej JSON)", v -> importProfile()), lp());
        TextView tip = text("Przytrzymaj profil: edycja kopii / udostępnienie. Profile „ogólne” mają przybliżone wymiary – dopasuj do swojego klucza.", 12);
        tip.setTextColor(0xFF777777);
        list.addView(tip);

        List<Store.SavedKey> keys = Store.keys(this);
        header("Zapisane klucze");
        if (keys.isEmpty()) list.addView(text("Brak – zapisz klucz przyciskiem 💾 na ekranie klucza.", 14));
        for (int i = 0; i < keys.size(); i++) {
            final int idx = i;
            final Store.SavedKey k = keys.get(i);
            Button b = Ui.button(this, k.name + "\n" + k.profile.shortName + "  ·  " + Store.codeString(k.profile, k.code),
                    v -> startActivity(KeyActivity.intent(this, k.profile, k.code, k.mirrorH, k.mirrorV, idx, k.name)));
            b.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
            b.setTextSize(16);
            b.setOnLongClickListener(v -> {
                new AlertDialog.Builder(this).setTitle(k.name)
                        .setItems(new String[]{"Usuń"}, (d, w) -> {
                            List<Store.SavedKey> l = Store.keys(this);
                            l.remove(idx);
                            Store.saveKeys(this, l);
                            build();
                        }).show();
                return true;
            });
            list.addView(b, lpWrap());
        }

        header("Jak używać");
        list.addView(text("1. Skalibruj ekran kartą płatniczą (raz).\n"
                + "2. Wybierz profil (np. Europrofil).\n"
                + "3. Połóż klucz na ekranie nacięciami do góry, ramieniem (ogranicznikiem) dokładnie przy czerwonej linii.\n"
                + "4. Dla każdego pinu ustaw głębokość (▲▼ lub przeciągnij palcem po ostrzu), aż obrys pokryje się z kluczem.\n"
                + "5. Odczytany kod zapisz 💾.\n"
                + "⇄ / ⇅ – odbicie, jeśli klucz leży w drugą stronę.\n"
                + "📷 – zdjęcie klucza pod obrysem: dopasuj palcami (✋), potem ✨ Auto odczyta nacięcia.\n"
                + "📤 – eksport: model 3D (STL), PDF 1:1 do druku, SVG, tekst.\n"
                + "Klucze dwustronne: ⇵ przełącza krawędź (kod: góra | dół).", 14));
    }

    private void addProfile(Profile p, int customIdx) {
        Button b = Ui.button(this, p.name + "   (" + p.pins + " pin)",
                v -> startActivity(KeyActivity.intent(this, p, null, false, false, -1, null)));
        b.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        b.setOnLongClickListener(v -> {
            if (customIdx < 0) {
                new AlertDialog.Builder(this).setTitle(p.name)
                        .setItems(new String[]{"Edytuj kopię", "Udostępnij profil (JSON)"}, (d, w) -> {
                            if (w == 0) editProfile(p.copy(), -1); else shareProfile(p);
                        }).show();
                return true;
            }
            new AlertDialog.Builder(this).setTitle(p.name)
                    .setItems(new String[]{"Edytuj", "Udostępnij profil (JSON)", "Usuń"}, (d, w) -> {
                        if (w == 0) editProfile(p, customIdx);
                        else if (w == 1) shareProfile(p);
                        else {
                            List<Profile> l = Store.customProfiles(this);
                            l.remove(customIdx);
                            Store.saveCustomProfiles(this, l);
                            build();
                        }
                    }).show();
            return true;
        });
        list.addView(b, lp());
    }

    private void editProfile(Profile src, int customIdx) {
        final Profile p = src != null ? src : Profile.builtIns().get(0).copy();
        if (customIdx < 0) {
            p.id = "custom" + System.currentTimeMillis();
            if (src != null) p.name = p.name + " (kopia)";
            else p.name = "Mój profil";
        }
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        int pad = Ui.dp(this, 16);
        form.setPadding(pad, pad / 2, pad, 0);
        EditText name = field(form, "Nazwa", p.name, false);
        EditText shortN = field(form, "Skrót (na ekranie)", p.shortName, false);
        EditText pins = field(form, "Liczba pinów", String.valueOf(p.pins), true);
        EditText h = field(form, "Wysokość ostrza [mm]", fmt(p.bladeHeight), true);
        EditText first = field(form, "Ramię → środek 1. nacięcia [mm]", fmt(p.firstCut), true);
        EditText sp = field(form, "Rozstaw nacięć [mm]", fmt(p.spacing), true);
        EditText r0 = field(form, "Wysokość dna dla głęb. 0 (od spodu) [mm]", fmt(p.root0), true);
        EditText step = field(form, "Krok głębokości [mm]", fmt(p.depthStep), true);
        EditText n = field(form, "Liczba głębokości", String.valueOf(p.depthCount), true);
        EditText ls = field(form, "Numer pierwszej głębokości", String.valueOf(p.labelStart), true);
        EditText ang = field(form, "Kąt nacięcia [°]", fmt(p.cutAngle), true);
        EditText flat = field(form, "Szerokość dna nacięcia [mm]", fmt(p.flat), true);
        EditText macs = field(form, "MACS (0 = brak)", String.valueOf(p.macs), true);
        EditText ds = field(form, "Dwustronny (0 = nie, 1 = tak)", p.doubleSided ? "1" : "0", true);
        EditText thick = field(form, "Grubość ostrza – model 3D [mm]", fmt(p.thickness), true);
        EditText gr = field(form, "Rowki – model 3D (F/B:wysokość:szer:głęb; …)", p.grooves, false);
        ScrollView sv = new ScrollView(this);
        sv.addView(form);
        new AlertDialog.Builder(this)
                .setTitle(customIdx >= 0 ? "Edytuj profil" : "Nowy profil")
                .setView(sv)
                .setPositiveButton("Zapisz", (d, w) -> {
                    try {
                        p.name = name.getText().toString().trim();
                        p.shortName = shortN.getText().toString().trim();
                        if (p.shortName.isEmpty()) p.shortName = p.name;
                        p.pins = clamp(Integer.parseInt(pins.getText().toString().trim()), 1, 12);
                        p.bladeHeight = num(h); p.firstCut = num(first); p.spacing = num(sp);
                        p.root0 = num(r0); p.depthStep = num(step);
                        p.depthCount = clamp(Integer.parseInt(n.getText().toString().trim()), 1, 20);
                        p.labelStart = Integer.parseInt(ls.getText().toString().trim());
                        p.cutAngle = num(ang); p.flat = num(flat);
                        p.macs = Integer.parseInt(macs.getText().toString().trim());
                        p.doubleSided = "1".equals(ds.getText().toString().trim());
                        p.thickness = num(thick);
                        p.grooves = gr.getText().toString().trim();
                        p.builtIn = false;
                        List<Profile> l = Store.customProfiles(this);
                        if (customIdx >= 0 && customIdx < l.size()) l.set(customIdx, p); else l.add(p);
                        Store.saveCustomProfiles(this, l);
                        build();
                    } catch (Exception e) {
                        Toast.makeText(this, "Błędne dane: " + e.getMessage(), Toast.LENGTH_LONG).show();
                    }
                })
                .setNegativeButton("Anuluj", null)
                .show();
    }

    private void shareProfile(Profile p) {
        try {
            Intent i = new Intent(Intent.ACTION_SEND);
            i.setType("text/plain");
            i.putExtra(Intent.EXTRA_TEXT, p.toJson().toString());
            startActivity(Intent.createChooser(i, "Udostępnij profil"));
        } catch (Exception e) {
            Toast.makeText(this, e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    private void importProfile() {
        EditText e = new EditText(this);
        e.setHint("{\"id\":…}");
        e.setMinLines(4);
        android.content.ClipboardManager cm = (android.content.ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
        if (cm != null && cm.hasPrimaryClip() && cm.getPrimaryClip().getItemCount() > 0) {
            CharSequence t = cm.getPrimaryClip().getItemAt(0).coerceToText(this);
            if (t != null && t.toString().trim().startsWith("{")) e.setText(t);
        }
        new AlertDialog.Builder(this).setTitle("Importuj profil").setView(e)
                .setPositiveButton("Importuj", (d, w) -> {
                    try {
                        Profile p = Profile.fromJson(new org.json.JSONObject(e.getText().toString().trim()));
                        p.id = "custom" + System.currentTimeMillis();
                        p.builtIn = false;
                        List<Profile> l = Store.customProfiles(this);
                        l.add(p);
                        Store.saveCustomProfiles(this, l);
                        build();
                        Toast.makeText(this, "Zaimportowano: " + p.name, Toast.LENGTH_SHORT).show();
                    } catch (Exception ex) {
                        Toast.makeText(this, "Niepoprawny JSON: " + ex.getMessage(), Toast.LENGTH_LONG).show();
                    }
                }).setNegativeButton("Anuluj", null).show();
    }

    private static int clamp(int v, int a, int b) { return Math.max(a, Math.min(b, v)); }

    private static double num(EditText e) { return Double.parseDouble(e.getText().toString().trim().replace(',', '.')); }

    private static String fmt(double v) { return String.format(Locale.US, "%.3f", v).replaceAll("\\.?0+$", ""); }

    private EditText field(LinearLayout form, String label, String value, boolean numeric) {
        TextView t = new TextView(this);
        t.setText(label);
        t.setTextSize(12);
        form.addView(t);
        EditText e = new EditText(this);
        e.setText(value);
        e.setSingleLine(true);
        if (numeric) e.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        form.addView(e);
        return e;
    }

    private void header(String s) {
        TextView t = text(s, 18);
        t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setTextColor(0xFFFFFFFF);
        t.setPadding(0, Ui.dp(this, 20), 0, Ui.dp(this, 4));
        list.addView(t);
    }

    private TextView text(String s, int size) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(size);
        t.setTextColor(0xFFCCCCCC);
        return t;
    }

    private LinearLayout.LayoutParams lp() {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, Ui.dp(this, 52));
        p.topMargin = Ui.dp(this, 6);
        return p;
    }

    private LinearLayout.LayoutParams lpWrap() {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, -2);
        p.topMargin = Ui.dp(this, 6);
        return p;
    }
}
