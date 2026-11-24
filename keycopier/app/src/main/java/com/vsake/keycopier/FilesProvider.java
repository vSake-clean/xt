package com.vsake.keycopier;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;

import java.io.File;
import java.io.FileNotFoundException;

/**
 * Minimal file provider for files in cache/share: used to share exports and to receive camera photos.
 * URI: content://com.vsake.keycopier.files/<name>
 */
public class FilesProvider extends ContentProvider {
    public static final String AUTH = "com.vsake.keycopier.files";

    public static File dir(Context c) {
        File d = new File(c.getCacheDir(), "share");
        d.mkdirs();
        return d;
    }

    public static Uri uri(File f) { return Uri.parse("content://" + AUTH + "/" + Uri.encode(f.getName())); }

    private File file(Uri uri) throws FileNotFoundException {
        String name = uri.getLastPathSegment();
        if (name == null || name.contains("/") || name.contains("..")) throw new FileNotFoundException();
        return new File(dir(getContext()), name);
    }

    @Override public boolean onCreate() { return true; }

    @Override
    public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
        return ParcelFileDescriptor.open(file(uri), ParcelFileDescriptor.parseMode(mode));
    }

    @Override
    public Cursor query(Uri uri, String[] proj, String sel, String[] args, String sort) {
        try {
            File f = file(uri);
            MatrixCursor c = new MatrixCursor(new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE});
            c.addRow(new Object[]{f.getName(), f.length()});
            return c;
        } catch (FileNotFoundException e) {
            return null;
        }
    }

    @Override
    public String getType(Uri uri) {
        String n = uri.getLastPathSegment();
        if (n == null) return "application/octet-stream";
        if (n.endsWith(".pdf")) return "application/pdf";
        if (n.endsWith(".svg")) return "image/svg+xml";
        if (n.endsWith(".jpg")) return "image/jpeg";
        if (n.endsWith(".png")) return "image/png";
        if (n.endsWith(".json") || n.endsWith(".txt")) return "text/plain";
        return "application/octet-stream";
    }

    @Override public Uri insert(Uri uri, ContentValues v) { return null; }
    @Override public int delete(Uri uri, String s, String[] a) { return 0; }
    @Override public int update(Uri uri, ContentValues v, String s, String[] a) { return 0; }
}
