package com.vsake.keycopier;

import android.content.Context;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.util.Arrays;
import java.util.Locale;

/** 3D preview of the generated key model with STL share / save. */
public class ModelActivity extends BaseActivity {
    private Profile profile;
    private int[] code;
    private Mesh mesh;

    public static Intent intent(Context c, Profile p, int[] code) {
        Intent i = new Intent(c, ModelActivity.class);
        try { i.putExtra("profile", p.toJson().toString()); } catch (JSONException e) { throw new RuntimeException(e); }
        i.putExtra("code", code);
        return i;
    }

    @Override
    protected void onCreate(Bundle s) {
        super.onCreate(s);
        try { profile = Profile.fromJson(new JSONObject(getIntent().getStringExtra("profile"))); }
        catch (Exception e) { finish(); return; }
        code = getIntent().getIntArrayExtra("code");
        mesh = Mesh.build(new Geometry(profile, code));

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(0xFF1B1B1B);
        root.addView(new ModelView(this, mesh), new FrameLayout.LayoutParams(-1, -1));

        TextView info = new TextView(this);
        info.setTextColor(0xFFFFFFFF);
        info.setTextSize(13);
        int pad = Ui.dp(this, 12);
        info.setPadding(pad, pad, pad, pad);
        info.setText(String.format(Locale.US, "%s  ·  %s\n%d trójkątów · grubość %.2f mm · skala 1:1 (mm)\n"
                        + "Rowki profilu są przybliżone – dopasuj w edycji profilu.",
                profile.name, Store.codeString(profile, code), mesh.triangles(), profile.thickness));
        root.addView(info, new FrameLayout.LayoutParams(-2, -2, Gravity.TOP | Gravity.START));

        LinearLayout bar = new LinearLayout(this);
        bar.setPadding(pad, pad, pad, pad);
        bar.addView(Ui.button(this, "Udostępnij STL", v -> export(true)), weighted());
        bar.addView(Ui.button(this, "Zapisz STL", v -> export(false)), weighted());
        root.addView(bar, new FrameLayout.LayoutParams(-1, Ui.dp(this, 72), Gravity.BOTTOM));
        setContentView(root);
    }

    private LinearLayout.LayoutParams weighted() {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, -1, 1f);
        p.leftMargin = Ui.dp(this, 4); p.rightMargin = Ui.dp(this, 4);
        return p;
    }

    private void export(boolean share) {
        try {
            File f = new File(FilesProvider.dir(this), Exporter.baseName(profile, code) + ".stl");
            mesh.writeStl(f, "KeyCopier " + profile.shortName);
            if (share) share(f, "application/octet-stream"); else saveAs(f, "application/octet-stream");
        } catch (Exception e) {
            Toast.makeText(this, "Błąd: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    /** Simple software renderer: flat shading, painter's algorithm, drag to rotate, pinch to zoom. */
    static class ModelView extends View {
        private final float[] tri;
        private final int n;
        private final float cx, cy, cz;
        private float yaw = -0.5f, pitch = 0.6f, zoom = 1f;
        private float lx, ly, lastDist;
        private float[] verts;
        private int[] colors;
        private long[] order;
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);

        ModelView(Context c, Mesh m) {
            super(c);
            setLayerType(LAYER_TYPE_SOFTWARE, null); // drawVertices with colors needs software rendering on old APIs
            n = m.triangles();
            tri = Arrays.copyOf(m.data(), 9 * n);
            float minX = Float.MAX_VALUE, minY = Float.MAX_VALUE, minZ = Float.MAX_VALUE;
            float maxX = -Float.MAX_VALUE, maxY = -Float.MAX_VALUE, maxZ = -Float.MAX_VALUE;
            for (int i = 0; i < tri.length; i += 3) {
                minX = Math.min(minX, tri[i]); maxX = Math.max(maxX, tri[i]);
                minY = Math.min(minY, tri[i + 1]); maxY = Math.max(maxY, tri[i + 1]);
                minZ = Math.min(minZ, tri[i + 2]); maxZ = Math.max(maxZ, tri[i + 2]);
            }
            cx = (minX + maxX) / 2; cy = (minY + maxY) / 2; cz = (minZ + maxZ) / 2;
            verts = new float[6 * n];
            colors = new int[3 * n];
            order = new long[n];
        }

        @Override
        protected void onDraw(Canvas c) {
            float scale = Math.min(getWidth(), getHeight()) / 60f * zoom;
            float ox = getWidth() / 2f, oy = getHeight() / 2f;
            float cyw = (float) Math.cos(yaw), syw = (float) Math.sin(yaw);
            float cp = (float) Math.cos(pitch), sp = (float) Math.sin(pitch);
            float[] tx = new float[9];
            int vis = 0;
            for (int t = 0; t < n; t++) {
                int o = 9 * t;
                for (int k = 0; k < 3; k++) {
                    float x = tri[o + 3 * k] - cx, y = tri[o + 3 * k + 1] - cy, z = tri[o + 3 * k + 2] - cz;
                    float x1 = x * cyw + z * syw, z1 = -x * syw + z * cyw;
                    float y2 = y * cp - z1 * sp, z2 = y * sp + z1 * cp;
                    tx[3 * k] = x1; tx[3 * k + 1] = y2; tx[3 * k + 2] = z2;
                }
                float ux = tx[3] - tx[0], uy = tx[4] - tx[1], uz = tx[5] - tx[2];
                float vx = tx[6] - tx[0], vy = tx[7] - tx[1], vz = tx[8] - tx[2];
                float nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
                float len = (float) Math.sqrt(nx * nx + ny * ny + nz * nz);
                if (len == 0 || nz / len < -0.02f) continue; // back-face culling (camera looks from +z)
                float light = Math.max(0, (nx * 0.3f + ny * 0.5f + nz * 0.8f) / len / 0.99f);
                int shade = (int) (60 + 180 * Math.min(1, light));
                int col = Color.rgb(shade, (int) (shade * 0.8f), (int) (shade * 0.45f));
                for (int k = 0; k < 3; k++) {
                    verts[6 * vis + 2 * k] = ox + tx[3 * k] * scale;
                    verts[6 * vis + 2 * k + 1] = oy - tx[3 * k + 1] * scale;
                    colors[3 * vis + k] = col;
                }
                float depth = (tx[2] + tx[5] + tx[8]) / 3f;
                order[vis] = ((long) Float.floatToIntBits(depth + 1000f) << 32) | vis;
                vis++;
            }
            Arrays.sort(order, 0, vis);
            float[] sv = new float[6 * vis];
            int[] sc = new int[3 * vis];
            for (int i = 0; i < vis; i++) {
                int idx = (int) (order[i] & 0xFFFFFFFFL);
                System.arraycopy(verts, 6 * idx, sv, 6 * i, 6);
                System.arraycopy(colors, 3 * idx, sc, 3 * i, 3);
            }
            c.drawVertices(Canvas.VertexMode.TRIANGLES, sv.length, sv, 0, null, 0, sc, 0, null, 0, 0, paint);
        }

        @Override
        public boolean onTouchEvent(MotionEvent e) {
            if (e.getPointerCount() == 2) {
                float d = (float) Math.hypot(e.getX(1) - e.getX(0), e.getY(1) - e.getY(0));
                if (e.getActionMasked() == MotionEvent.ACTION_MOVE && lastDist > 0) {
                    zoom = Math.max(0.3f, Math.min(8f, zoom * d / lastDist));
                }
                lastDist = d;
                invalidate();
                return true;
            }
            lastDist = 0;
            if (e.getActionMasked() == MotionEvent.ACTION_MOVE) {
                yaw += (e.getX() - lx) * 0.01f;
                pitch += (e.getY() - ly) * 0.01f;
                invalidate();
            }
            lx = e.getX(); ly = e.getY();
            return true;
        }
    }
}
