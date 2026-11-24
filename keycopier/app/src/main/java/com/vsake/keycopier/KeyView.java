package com.vsake.keycopier;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.DashPathEffect;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.view.HapticFeedbackConstants;
import android.view.MotionEvent;
import android.view.View;

import java.util.List;

/**
 * Draws the key at real (1:1) scale. The user lays the physical key on the screen with its shoulder
 * against the red line and adjusts every cut until the outline matches. Optionally a photo of the key
 * can be shown underneath, moved/scaled/rotated with fingers, and the cuts detected automatically.
 */
public class KeyView extends View {
    public interface Listener { void onChanged(); }

    private Profile p;
    private int[] code;
    private Geometry geo;
    private int selected = 0;
    private float pxmm;
    private boolean mirrorH, mirrorV;
    private Listener listener;

    private Bitmap photo;
    private final Matrix photoM = new Matrix();
    /** Touch modes: edit the key, move the photo, or pan/zoom the whole view. */
    public static final int MODE_KEY = 0, MODE_PHOTO = 1, MODE_VIEW = 2;
    private int mode = MODE_KEY;
    private final Matrix viewM = new Matrix();
    private final Matrix viewInv = new Matrix();
    private final Paint photoPaint = new Paint(Paint.FILTER_BITMAP_FLAG);

    private boolean touching;
    private float touchX, touchY;
    private float lastX0, lastY0, lastX1, lastY1;
    private int lastCount;

    private final Paint bg = new Paint();
    private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint thin = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint dashed = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint shoulder = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint sel = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint warn = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint loupeRing = new Paint(Paint.ANTI_ALIAS_FLAG);

    private float shoulderPx, baseY;
    private boolean optLoupe, optTouchDepth, optTouchPin, optVibrate, optHints, optLadder;

    /** Re-reads quick settings (⚙). */
    public void reloadSettings() {
        Context c = getContext();
        optLoupe = Settings.get(c, Settings.LOUPE);
        optTouchDepth = Settings.get(c, Settings.TOUCH_DEPTH);
        optTouchPin = Settings.get(c, Settings.TOUCH_PIN);
        optVibrate = Settings.get(c, Settings.VIBRATE);
        optHints = Settings.get(c, Settings.HINTS);
        optLadder = Settings.get(c, Settings.LADDER);
        invalidate();
    }

    public KeyView(Context c) {
        super(c);
        bg.setColor(0xFFFF8C1A);
        fill.setColor(0x66FFFFFF);
        stroke.setColor(0xFF000000); stroke.setStyle(Paint.Style.STROKE); stroke.setStrokeWidth(3f);
        stroke.setStrokeJoin(Paint.Join.ROUND);
        thin.setColor(0xFF3A1A00); thin.setStrokeWidth(2f);
        dashed.setColor(0x88000000); dashed.setStrokeWidth(1.5f);
        dashed.setPathEffect(new DashPathEffect(new float[]{8, 8}, 0));
        shoulder.setColor(0xFFD00000); shoulder.setStrokeWidth(4f);
        text.setColor(0xFF000000); text.setTypeface(Typeface.MONOSPACE); text.setTextAlign(Paint.Align.CENTER);
        sel.setColor(0xFF000000);
        warn.setColor(0xFFB00000); warn.setTypeface(Typeface.DEFAULT_BOLD);
        loupeRing.setStyle(Paint.Style.STROKE); loupeRing.setStrokeWidth(5f); loupeRing.setColor(0xFF000000);
        photoPaint.setAlpha(170);
        reloadSettings();
    }

    public void setup(Profile p, int[] code, float pxmm) {
        this.p = p; this.code = code; this.pxmm = pxmm;
        geo = new Geometry(p, code);
        if (selected >= p.codeLen()) selected = 0;
        invalidate();
    }

    public void setListener(Listener l) { listener = l; }
    public void setMirror(boolean h, boolean v) { mirrorH = h; mirrorV = v; invalidate(); }
    public boolean isMirrorH() { return mirrorH; }
    public boolean isMirrorV() { return mirrorV; }
    public int[] getCode() { return code; }
    public boolean onBottomEdge() { return selected >= p.pins; }

    // ---------------- photo ----------------
    public void setPhoto(Bitmap b) {
        photo = b;
        photoM.reset();
        if (b != null && getWidth() > 0) {
            float s = Math.max(getWidth() / (float) b.getWidth(), getHeight() / (float) b.getHeight());
            photoM.postScale(s, s);
            photoM.postTranslate((getWidth() - b.getWidth() * s) / 2f, (getHeight() - b.getHeight() * s) / 2f);
        }
        mode = b != null ? MODE_PHOTO : (mode == MODE_PHOTO ? MODE_KEY : mode);
        lastCount = 0;
        invalidate();
    }

    public boolean hasPhoto() { return photo != null; }
    public int getMode() { return mode; }

    public void setMode(int m) {
        if (m == MODE_PHOTO && photo == null) m = MODE_KEY;
        mode = m;
        lastCount = 0;
        invalidate();
    }

    /** Key -> (Photo) -> View -> Key. */
    public void cycleMode() {
        if (mode == MODE_KEY) setMode(photo != null ? MODE_PHOTO : MODE_VIEW);
        else if (mode == MODE_PHOTO) setMode(MODE_VIEW);
        else setMode(MODE_KEY);
    }

    public boolean isZoomed() { return !viewM.isIdentity(); }

    public void resetView() { viewM.reset(); invalidate(); }

    private float viewScale() {
        float[] v = new float[9];
        viewM.getValues(v);
        return (float) Math.hypot(v[Matrix.MSCALE_X], v[Matrix.MSKEW_Y]);
    }

    // ---------------- editing ----------------
    public void select(int delta) {
        int edge = selected / p.pins, pin = selected % p.pins;
        pin = Math.max(0, Math.min(p.pins - 1, pin + delta));
        selected = edge * p.pins + pin;
        changed();
    }

    public void switchEdge() {
        if (!p.doubleSided) return;
        selected = (selected + p.pins) % (2 * p.pins);
        changed();
    }

    public void copyTopToBottom() {
        if (!p.doubleSided) return;
        System.arraycopy(code, 0, code, p.pins, p.pins);
        changed();
    }

    /** Move the selected cut root up or down on the screen. */
    public void shiftDepth(boolean screenUp) {
        boolean heightUp = screenUp ^ mirrorV;
        boolean bottom = onBottomEdge();
        int d = (heightUp ^ bottom) ? -1 : 1;
        if (p.depthStep < 0) d = -d;
        int idx = Math.max(0, Math.min(p.depthCount - 1, code[selected] + d));
        if (idx != code[selected]) { code[selected] = idx; changed(); }
    }

    public void resetCode() { for (int i = 0; i < code.length; i++) code[i] = 0; changed(); }

    private void changed() {
        if (optVibrate) performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY);
        invalidate();
        if (listener != null) listener.onChanged();
    }

    // ---- coordinate helpers ----
    private float sx(double mm) { return (float) (mirrorH ? shoulderPx - mm * pxmm : shoulderPx + mm * pxmm); }
    private float sy(double h) { return (float) (mirrorV ? baseY + h * pxmm : baseY - h * pxmm); }
    private double mmX(float x) { return mirrorH ? (shoulderPx - x) / pxmm : (x - shoulderPx) / pxmm; }
    private double mmY(float y) { return mirrorV ? (y - baseY) / pxmm : (baseY - y) / pxmm; }

    private void layoutKey() {
        float w = getWidth(), h = getHeight();
        float margin = 30f * pxmm;
        shoulderPx = mirrorH ? w - margin : margin;
        float half = (float) (p.bladeHeight * pxmm / 2f);
        baseY = mirrorV ? h / 2f - half : h / 2f + half;
    }

    @Override
    protected void onDraw(Canvas c) {
        if (p == null) return;
        layoutKey();
        drawScene(c, true);
        if (touching && optLoupe) drawLoupe(c);
    }

    private void drawScene(Canvas c, boolean hud) {
        c.drawPaint(bg);
        c.save();
        c.concat(viewM);
        if (photo != null) c.drawBitmap(photo, photoM, photoPaint);
        double H = p.bladeHeight;

        // bow
        float bx1 = sx(-Geometry.BOW_LEN), bx2 = sx(0), by1 = sy(-Geometry.BOW_EXTRA), by2 = sy(H + Geometry.BOW_EXTRA);
        RectF bow = new RectF(Math.min(bx1, bx2), Math.min(by1, by2), Math.max(bx1, bx2), Math.max(by1, by2));
        float r = (float) (Geometry.BOW_RADIUS * pxmm);
        if (photo == null) c.drawRoundRect(bow, r, r, fill);
        c.drawRoundRect(bow, r, r, stroke);

        // blade
        Path path = new Path();
        List<double[]> pts = geo.outline(0.05);
        for (int i = 0; i < pts.size(); i++) {
            float x = sx(pts.get(i)[0]), y = sy(pts.get(i)[1]);
            if (i == 0) path.moveTo(x, y); else path.lineTo(x, y);
        }
        path.close();
        if (photo == null) c.drawPath(path, fill);
        c.drawPath(path, stroke);

        if (photo == null) {
            double tip = p.tipX();
            c.drawLine(sx(1), sy(H * 0.33), sx(tip - 3), sy(H * 0.33), thin);
            c.drawLine(sx(1), sy(H * 0.55), sx(tip - 4), sy(H * 0.55), thin);
        }
        c.drawLine(sx(0), -10 * getHeight(), sx(0), 11 * getHeight(), shoulder);

        // pin lines, labels and depth ladder
        float textSize = Math.max(28f, 3.2f * pxmm);
        text.setTextSize(textSize);
        for (int e = 0; e < (p.doubleSided ? 2 : 1); e++) {
            boolean bottomEdge = e == 1;
            boolean labelBelow = bottomEdge ^ mirrorV;
            float labelY = labelBelow ? sy(bottomEdge ? -4 : H + 4) + textSize : sy(bottomEdge ? -4 : H + 4);
            for (int i = 0; i < p.pins; i++) {
                float x = sx(p.cutCenter(i));
                if (e == 0) c.drawLine(x, sy(-2), x, sy(H + 2), dashed);
                int idx = e * p.pins + i;
                text.setFakeBoldText(idx == selected);
                c.drawText(p.label(code[idx]), x, labelY, text);
                if (idx == selected) {
                    boolean arrowDown = !labelBelow; // arrow points toward the blade
                    float ay = arrowDown ? labelY - textSize * 1.3f : labelY + textSize * 0.4f;
                    drawArrow(c, x, ay, textSize * 0.5f, arrowDown);
                }
            }
        }

        boolean bottomSel = onBottomEdge();
        float selX = sx(p.cutCenter(selected % p.pins));
        float tick = (float) Math.max(p.flat / 2 + 0.6, 1.2) * pxmm;
        Paint ladder = new Paint(thin);
        ladder.setStrokeWidth(1.5f);
        ladder.setColor(0xAA000000);
        for (int d = 0; optLadder && d < p.depthCount; d++) {
            float y = sy(bottomSel ? H - p.root(d) : p.root(d));
            c.drawLine(selX - tick, y, selX + tick, y, ladder);
        }
        Paint cur = new Paint(shoulder);
        cur.setStrokeWidth(3f);
        float cy = sy(bottomSel ? H - p.root(code[selected]) : p.root(code[selected]));
        c.drawLine(selX - tick * 1.4f, cy, selX + tick * 1.4f, cy, cur);
        c.restore();

        if (!hud) return;
        Paint hdr = new Paint(text);
        hdr.setTextAlign(Paint.Align.LEFT);
        hdr.setFakeBoldText(false);
        hdr.setTextSize(Math.max(26f, 2.6f * pxmm));
        float hx = mirrorH ? getWidth() * 0.45f : Math.max(24, isZoomed() ? 24 : sx(-26));
        float hy = hdr.getTextSize() + 16;
        String codeTxt = Store.codeString(p, code);
        c.drawText(p.shortName + "   " + codeTxt, hx, hy, hdr);
        String w = macsWarning();
        if (w != null) {
            warn.setTextSize(hdr.getTextSize() * 0.8f);
            c.drawText(w, hx, hy * 2, warn);
        }
        Paint hint = new Paint(hdr);
        hint.setTextSize(hdr.getTextSize() * 0.6f);
        hint.setColor(0xAA000000);
        if (isZoomed()) {
            warn.setTextSize(hdr.getTextSize() * 0.8f);
            c.drawText(String.format(java.util.Locale.US, "🔍 x%.1f – widok powiększony (to nie jest skala 1:1)", viewScale()),
                    hx, hy * (w != null ? 3 : 2), warn);
        }
        String h = mode == MODE_PHOTO ? "Tryb zdjęcia: przesuń / powiększ / obróć dwoma palcami, dopasuj do obrysu"
                : mode == MODE_VIEW ? "Tryb widoku: przesuwaj i przybliżaj cały obszar dwoma palcami"
                : "Oprzyj ramię klucza o czerwoną linię" + (p.doubleSided ? "  ·  ⇵ zmienia krawędź" : "");
        if (optHints) c.drawText(h, hx, getHeight() - 16, hint);
    }

    private String macsWarning() {
        if (p.macs <= 0) return null;
        for (int e = 0; e < (p.doubleSided ? 2 : 1); e++)
            for (int i = 0; i + 1 < p.pins; i++)
                if (Math.abs(code[e * p.pins + i] - code[e * p.pins + i + 1]) > p.macs)
                    return "Uwaga: przekroczony MACS (" + p.macs + ") między " + (i + 1) + " i " + (i + 2);
        return null;
    }

    private void drawArrow(Canvas c, float x, float y, float s, boolean down) {
        Path a = new Path();
        if (down) { a.moveTo(x, y + s); a.lineTo(x - s / 2, y); a.lineTo(x + s / 2, y); }
        else { a.moveTo(x, y); a.lineTo(x - s / 2, y + s); a.lineTo(x + s / 2, y + s); }
        a.close();
        c.drawPath(a, sel);
    }

    private void drawLoupe(Canvas c) {
        float R = Math.min(16 * pxmm, Math.min(getWidth(), getHeight()) / 4f);
        float zoom = 2.5f;
        float lx = touchX, ly = touchY - R - 30;
        if (ly - R < 0) ly = touchY + R + 30;
        Path clip = new Path();
        clip.addCircle(lx, ly, R, Path.Direction.CW);
        c.save();
        c.clipPath(clip);
        c.translate(lx, ly);
        c.scale(zoom, zoom);
        c.translate(-touchX, -touchY);
        drawScene(c, false);
        c.restore();
        c.drawCircle(lx, ly, R, loupeRing);
        Paint cross = new Paint(shoulder);
        cross.setStrokeWidth(1.5f);
        c.drawLine(lx - 12, ly, lx + 12, ly, cross);
        c.drawLine(lx, ly - 12, lx, ly + 12, cross);
    }

    // ---------------- auto detection from photo ----------------
    /** Detects the cut depths from the photo along every pin line. Returns false without a photo. */
    public boolean autoDetect() {
        if (photo == null) return false;
        layoutKey();
        Matrix inv = new Matrix();
        if (!photoM.invert(inv)) return false;
        double H = p.bladeHeight;
        double rMin = Math.min(p.root(0), p.root(p.depthCount - 1));
        for (int e = 0; e < (p.doubleSided ? 2 : 1); e++) {
            for (int i = 0; i < p.pins; i++) {
                double xc = p.cutCenter(i);
                double lo, hi;
                if (e == 0) { lo = rMin - 0.6; hi = H + 1.5; }
                else { lo = -1.5; hi = H - rMin + 0.6; }
                // Sample average colour across the cut at each height, scanning from outside the blade inward.
                int steps = (int) ((hi - lo) / 0.05);
                double[][] col = new double[steps + 1][];
                for (int k = 0; k <= steps; k++) {
                    double y = e == 0 ? hi - k * 0.05 : lo + k * 0.05;
                    col[k] = sample(inv, xc, y);
                }
                // background reference = first 0.4 mm (outside the key)
                double[] ref = new double[3];
                int rc = 0;
                for (int k = 0; k < 8 && k <= steps; k++) {
                    if (col[k] == null) continue;
                    for (int q = 0; q < 3; q++) ref[q] += col[k][q];
                    rc++;
                }
                if (rc == 0) continue;
                for (int q = 0; q < 3; q++) ref[q] /= rc;
                double[] dist = new double[steps + 1];
                double maxD = 0;
                for (int k = 0; k <= steps; k++) {
                    if (col[k] == null) { dist[k] = 0; continue; }
                    dist[k] = Math.sqrt(sq(col[k][0] - ref[0]) + sq(col[k][1] - ref[1]) + sq(col[k][2] - ref[2]));
                    maxD = Math.max(maxD, dist[k]);
                }
                if (maxD < 30) continue; // no contrast – leave as is
                double thr = Math.max(25, maxD * 0.45);
                double bestY = Double.NaN;
                for (int k = 8; k + 2 <= steps; k++) {
                    if (dist[k] > thr && dist[k + 1] > thr && dist[k + 2] > thr) {
                        bestY = e == 0 ? hi - k * 0.05 : lo + k * 0.05;
                        break;
                    }
                }
                if (Double.isNaN(bestY)) continue;
                int bestIdx = 0;
                double bd = Double.MAX_VALUE;
                for (int d = 0; d < p.depthCount; d++) {
                    double ry = e == 0 ? p.root(d) : H - p.root(d);
                    if (Math.abs(ry - bestY) < bd) { bd = Math.abs(ry - bestY); bestIdx = d; }
                }
                code[e * p.pins + i] = bestIdx;
            }
        }
        changed();
        return true;
    }

    private static double sq(double v) { return v * v; }

    /** Average RGB of a small patch around (x mm, y mm) in the photo, or null if outside. */
    private double[] sample(Matrix inv, double xc, double y) {
        double[] sum = new double[3];
        int cnt = 0;
        double w = Math.max(0.15, p.flat * 0.25);
        for (int dx = -2; dx <= 2; dx++) {
            for (int dy = -1; dy <= 1; dy++) {
                float[] pt = {sx(xc + dx * w / 2), sy(y + dy * 0.03)};
                inv.mapPoints(pt);
                int px = (int) pt[0], py = (int) pt[1];
                if (px < 0 || py < 0 || px >= photo.getWidth() || py >= photo.getHeight()) continue;
                int c = photo.getPixel(px, py);
                sum[0] += Color.red(c); sum[1] += Color.green(c); sum[2] += Color.blue(c);
                cnt++;
            }
        }
        if (cnt == 0) return null;
        for (int q = 0; q < 3; q++) sum[q] /= cnt;
        return sum;
    }

    // ---------------- touch ----------------
    @Override
    public boolean onTouchEvent(MotionEvent e) {
        if (p == null) return false;
        int a = e.getActionMasked();
        touchX = e.getX(); touchY = e.getY();
        if (a == MotionEvent.ACTION_UP || a == MotionEvent.ACTION_CANCEL) {
            touching = false; lastCount = 0; invalidate(); return true;
        }
        touching = true;
        if (mode == MODE_PHOTO) { handleGesture(e, photoM, true, true); invalidate(); return true; }
        if (mode == MODE_VIEW) { handleGesture(e, viewM, false, false); invalidate(); return true; }
        if (a != MotionEvent.ACTION_DOWN && a != MotionEvent.ACTION_MOVE) return true;
        if (!optTouchDepth && !optTouchPin) { invalidate(); return true; } // touch editing disabled
        layoutKey();
        float[] sp = {e.getX(), e.getY()};
        viewM.invert(viewInv);
        viewInv.mapPoints(sp); // screen -> scene (undo view zoom)
        double x = mmX(sp[0]), y = mmY(sp[1]);
        invalidate();
        if (x < p.firstCut - p.spacing || x > p.tipX() + 2) return true;
        int pin = (int) Math.round((x - p.firstCut) / p.spacing);
        pin = Math.max(0, Math.min(p.pins - 1, pin));
        boolean bottom = p.doubleSided && y < p.bladeHeight / 2;
        int idx = (bottom ? p.pins : 0) + pin;
        boolean change = false;
        if (optTouchPin) {
            if (idx != selected) { selected = idx; change = true; }
        } else {
            idx = selected; // depth only on the pin chosen with the buttons
            bottom = onBottomEdge();
        }
        if (optTouchDepth && y > -2.5 && y < p.bladeHeight + 2.5) {
            int best = code[idx];
            double bd = Double.MAX_VALUE;
            for (int d = 0; d < p.depthCount; d++) {
                double ry = bottom ? p.bladeHeight - p.root(d) : p.root(d);
                double dd = Math.abs(ry - y);
                if (dd < bd) { bd = dd; best = d; }
            }
            if (best != code[idx]) { code[idx] = best; change = true; }
        }
        if (change) changed();
        return true;
    }

    /**
     * One finger moves, two fingers zoom (and rotate if allowed) the target matrix.
     * sceneSpace: the target lives under the view transform (the photo), so touch points are un-zoomed first.
     */
    private void handleGesture(MotionEvent e, Matrix target, boolean sceneSpace, boolean allowRotate) {
        int cnt = Math.min(2, e.getPointerCount());
        float[] pt = {e.getX(0), e.getY(0), cnt > 1 ? e.getX(1) : 0, cnt > 1 ? e.getY(1) : 0};
        if (sceneSpace) { viewM.invert(viewInv); viewInv.mapPoints(pt); }
        float x0 = pt[0], y0 = pt[1], x1 = pt[2], y1 = pt[3];
        int a = e.getActionMasked();
        if (cnt == lastCount && a == MotionEvent.ACTION_MOVE) {
            if (cnt == 1) {
                target.postTranslate(x0 - lastX0, y0 - lastY0);
            } else {
                float omx = (lastX0 + lastX1) / 2, omy = (lastY0 + lastY1) / 2;
                float nmx = (x0 + x1) / 2, nmy = (y0 + y1) / 2;
                double od = Math.hypot(lastX1 - lastX0, lastY1 - lastY0), nd = Math.hypot(x1 - x0, y1 - y0);
                if (od > 10) {
                    float s = (float) (nd / od);
                    float rot = allowRotate ? (float) Math.toDegrees(Math.atan2(y1 - y0, x1 - x0)
                            - Math.atan2(lastY1 - lastY0, lastX1 - lastX0)) : 0;
                    if (!sceneSpace) { // keep view zoom between 1x and 12x
                        float cur = viewScale();
                        s = Math.max(1f / cur, Math.min(12f / cur, s));
                    }
                    target.postTranslate(-omx, -omy);
                    target.postScale(s, s);
                    if (rot != 0) target.postRotate(rot);
                    target.postTranslate(nmx, nmy);
                }
            }
        }
        lastCount = (a == MotionEvent.ACTION_POINTER_UP) ? 0 : cnt;
        lastX0 = x0; lastY0 = y0; lastX1 = x1; lastY1 = y1;
        if (cnt > 1) touching = false; // no loupe while pinching
    }
}
