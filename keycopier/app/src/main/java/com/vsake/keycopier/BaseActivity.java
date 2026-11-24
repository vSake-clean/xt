package com.vsake.keycopier;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.widget.Toast;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.OutputStream;

/** Share / "save as" helpers for exported files. */
public class BaseActivity extends Activity {
    private static final int REQ_SAVE = 9001;
    private File pendingSave;

    protected void offerFile(File f, String mime) {
        new AlertDialog.Builder(this)
                .setTitle(f.getName())
                .setItems(new String[]{"Udostępnij…", "Zapisz jako…"}, (d, w) -> {
                    if (w == 0) share(f, mime); else saveAs(f, mime);
                }).show();
    }

    protected void share(File f, String mime) {
        Intent i = new Intent(Intent.ACTION_SEND);
        i.setType(mime);
        i.putExtra(Intent.EXTRA_STREAM, FilesProvider.uri(f));
        i.putExtra(Intent.EXTRA_SUBJECT, f.getName());
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        startActivity(Intent.createChooser(i, "Udostępnij"));
    }

    protected void shareText(String t) {
        Intent i = new Intent(Intent.ACTION_SEND);
        i.setType("text/plain");
        i.putExtra(Intent.EXTRA_TEXT, t);
        startActivity(Intent.createChooser(i, "Udostępnij"));
    }

    protected void saveAs(File f, String mime) {
        pendingSave = f;
        Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType(mime);
        i.putExtra(Intent.EXTRA_TITLE, f.getName());
        startActivityForResult(i, REQ_SAVE);
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req == REQ_SAVE && res == RESULT_OK && data != null && pendingSave != null) {
            Uri u = data.getData();
            try (InputStream in = new FileInputStream(pendingSave); OutputStream out = getContentResolver().openOutputStream(u)) {
                byte[] b = new byte[16384];
                int n;
                while ((n = in.read(b)) > 0) out.write(b, 0, n);
                Toast.makeText(this, "Zapisano", Toast.LENGTH_SHORT).show();
            } catch (Exception e) {
                Toast.makeText(this, "Błąd zapisu: " + e.getMessage(), Toast.LENGTH_LONG).show();
            }
        }
    }
}
