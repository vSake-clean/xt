package com.vsake.keycopier;

import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.MediaStore;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Toast;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.InputStream;
import java.util.List;

public class KeyActivity extends BaseActivity {
    public static final String EX_PROFILE = "profile";
    public static final String EX_CODE = "code";
    public static final String EX_MH = "mh";
    public static final String EX_MV = "mv";
    public static final String EX_SAVED = "saved";
    public static final String EX_NAME = "name";
    private static final int REQ_CAMERA = 1, REQ_GALLERY = 2;

    private KeyView keyView;
    private ScrollView panelScroll;
    private Button photoMoveBtn, autoBtn;
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
        int[] src = s != null ? s.getIntArray(EX_CODE) : in.getIntArrayExtra(EX_CODE);
        int[] code = new int[profile.codeLen()];
        if (src != null) System.arraycopy(src, 0, code, 0, Math.min(src.length, code.length));
        for (int i = 0; i < code.length; i++) code[i] = Math.max(0, Math.min(profile.depthCount - 1, code[i]));
        savedIndex = in.getIntExtra(EX_SAVED, -1);
        savedName = in.getStringExtra(EX_NAME);
        boolean mh = s != null ? s.getBoolean(EX_MH) : in.getBooleanExtra(EX_MH, false);
        boolean mv = s != null ? s.getBoolean(EX_MV) : in.getBooleanExtra(EX_MV, false);

        FrameLayout root = new FrameLayout(this);
        keyView = new KeyView(this);
        keyView.setup(profile, code, Store.pxPerMm(this));
        keyView.setMirror(mh, mv);
        root.addView(keyView, new FrameLayout.LayoutParams(-1, -1));

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        int pad = Ui.dp(this, 6);
        panel.setPadding(pad, pad, pad, pad);

        panel.addView(Ui.button(this, "▲", v -> keyView.shiftDepth(true)), lp());
        panel.addView(row(Ui.button(this, "◀", v -> keyView.select(keyView.isMirrorH() ? 1 : -1)),
                Ui.button(this, "▶", v -> keyView.select(keyView.isMirrorH() ? -1 : 1))), lp());
        panel.addView(Ui.button(this, "▼", v -> keyView.shiftDepth(false)), lp());
        if (profile.doubleSided) {
            panel.addView(row(Ui.button(this, "⇵ Krawędź", v -> keyView.switchEdge()),
                    Ui.button(this, "Góra→dół", v -> keyView.copyTopToBottom())), lp());
        }
        panel.addView(row(Ui.button(this, "💾", v -> save()), Ui.button(this, "📤", v -> exportMenu())), lp());
        panel.addView(row(Ui.button(this, "⇄", v -> { keyView.setMirror(!keyView.isMirrorH(), keyView.isMirrorV()); placePanel(); }),
                Ui.button(this, "⇅", v -> keyView.setMirror(keyView.isMirrorH(), !keyView.isMirrorV()))), lp());
        panel.addView(row(Ui.button(this, "📷", v -> photoMenu()), Ui.button(this, "Zeruj", v -> keyView.resetCode())), lp());
        photoMoveBtn = Ui.button(this, "✋", v -> { keyView.setPhotoMove(!keyView.isPhotoMove()); updatePhotoButtons(); });
        autoBtn = Ui.button(this, "✨ Auto", v -> {
            keyView.setPhotoMove(false);
            updatePhotoButtons();
            if (keyView.autoDetect()) Toast.makeText(this, "Odczytano – sprawdź i popraw ręcznie", Toast.LENGTH_SHORT).show();
        });
        panel.addView(row(photoMoveBtn, autoBtn), lp());
        panel.addView(Ui.button(this, "⚙ Ustawienia", v -> Settings.show(this, () -> {
            keyView.reloadSettings();
            Ui.immersive(this);
        })), lp());
        updatePhotoButtons();

        panelScroll = new ScrollView(this);
        panelScroll.addView(panel);
        root.addView(panelScroll);
        placePanel();
        setContentView(root);
        Ui.immersive(this);
    }

    private void updatePhotoButtons() {
        int vis = keyView.hasPhoto() ? View.VISIBLE : View.GONE;
        ((View) photoMoveBtn.getParent()).setVisibility(vis);
        photoMoveBtn.setText(keyView.isPhotoMove() ? "✋ Zdjęcie" : "✋ Klucz");
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) Ui.immersive(this);
    }

    private void placePanel() {
        FrameLayout.LayoutParams p = new FrameLayout.LayoutParams(Ui.dp(this, 150), -2);
        p.gravity = Gravity.CENTER_VERTICAL | (keyView.isMirrorH() ? Gravity.START : Gravity.END);
        panelScroll.setLayoutParams(p);
    }

    private LinearLayout row(View a, View b) {
        LinearLayout r = new LinearLayout(this);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, -1, 1f);
        p.leftMargin = Ui.dp(this, 2); p.rightMargin = Ui.dp(this, 2);
        r.addView(a, p);
        LinearLayout.LayoutParams p2 = new LinearLayout.LayoutParams(0, -1, 1f);
        p2.leftMargin = Ui.dp(this, 2); p2.rightMargin = Ui.dp(this, 2);
        r.addView(b, p2);
        return r;
    }

    private LinearLayout.LayoutParams lp() {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, Ui.dp(this, 44));
        p.topMargin = Ui.dp(this, 4);
        return p;
    }

    // ---------------- photo ----------------
    private File photoFile() { return new File(FilesProvider.dir(this), "photo.jpg"); }

    private void photoMenu() {
        String[] items = keyView.hasPhoto()
                ? new String[]{"Zrób zdjęcie", "Wybierz z galerii", "Usuń zdjęcie"}
                : new String[]{"Zrób zdjęcie", "Wybierz z galerii"};
        new AlertDialog.Builder(this)
                .setTitle("Zdjęcie klucza")
                .setMessage(null)
                .setItems(items, (d, w) -> {
                    if (w == 0) {
                        Intent i = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
                        photoFile().delete();
                        Uri u = FilesProvider.uri(photoFile());
                        i.putExtra(MediaStore.EXTRA_OUTPUT, u);
                        i.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION);
                        try {
                            photoFile().createNewFile();
                            startActivityForResult(i, REQ_CAMERA);
                        } catch (Exception e) {
                            Toast.makeText(this, "Brak aplikacji aparatu", Toast.LENGTH_SHORT).show();
                        }
                    } else if (w == 1) {
                        Intent i = new Intent(Intent.ACTION_GET_CONTENT);
                        i.setType("image/*");
                        startActivityForResult(Intent.createChooser(i, "Zdjęcie klucza"), REQ_GALLERY);
                    } else {
                        keyView.setPhoto(null);
                        updatePhotoButtons();
                    }
                }).show();
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (res != RESULT_OK) return;
        Uri u = null;
        if (req == REQ_CAMERA) u = FilesProvider.uri(photoFile());
        else if (req == REQ_GALLERY && data != null) u = data.getData();
        if (u == null) return;
        Bitmap b = loadBitmap(u);
        if (b == null) { Toast.makeText(this, "Nie udało się wczytać zdjęcia", Toast.LENGTH_SHORT).show(); return; }
        keyView.setPhoto(b);
        updatePhotoButtons();
        Toast.makeText(this, "Dopasuj zdjęcie do obrysu (ramię do czerwonej linii), potem ✨ Auto", Toast.LENGTH_LONG).show();
    }

    private Bitmap loadBitmap(Uri u) {
        try {
            BitmapFactory.Options o = new BitmapFactory.Options();
            o.inJustDecodeBounds = true;
            try (InputStream in = getContentResolver().openInputStream(u)) { BitmapFactory.decodeStream(in, null, o); }
            int sample = 1;
            while (Math.max(o.outWidth, o.outHeight) / sample > 2400) sample *= 2;
            BitmapFactory.Options o2 = new BitmapFactory.Options();
            o2.inSampleSize = sample;
            Bitmap b;
            try (InputStream in = getContentResolver().openInputStream(u)) { b = BitmapFactory.decodeStream(in, null, o2); }
            if (b == null) return null;
            int rot = 0;
            if (Build.VERSION.SDK_INT >= 24) {
                try (InputStream in = getContentResolver().openInputStream(u)) {
                    android.media.ExifInterface ex = new android.media.ExifInterface(in);
                    int or = ex.getAttributeInt(android.media.ExifInterface.TAG_ORIENTATION, 1);
                    rot = or == 6 ? 90 : or == 3 ? 180 : or == 8 ? 270 : 0;
                }
            }
            if (rot != 0) {
                Matrix m = new Matrix();
                m.postRotate(rot);
                b = Bitmap.createBitmap(b, 0, 0, b.getWidth(), b.getHeight(), m, true);
            }
            return b;
        } catch (Exception e) {
            return null;
        }
    }

    // ---------------- export ----------------
    private void exportMenu() {
        new AlertDialog.Builder(this)
                .setTitle("Eksport  " + Store.codeString(profile, keyView.getCode()))
                .setItems(new String[]{"Model 3D (STL) – podgląd", "PDF 1:1 do druku", "SVG (laser / ploter)", "Udostępnij kod (tekst)"},
                        (d, w) -> {
                            int[] code = keyView.getCode().clone();
                            try {
                                if (w == 0) startActivity(ModelActivity.intent(this, profile, code));
                                else if (w == 1) offerFile(Exporter.pdf(this, profile, code), "application/pdf");
                                else if (w == 2) offerFile(Exporter.svg(this, profile, code), "image/svg+xml");
                                else shareText(Exporter.text(profile, code));
                            } catch (Exception e) {
                                Toast.makeText(this, "Błąd eksportu: " + e.getMessage(), Toast.LENGTH_LONG).show();
                            }
                        }).show();
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
