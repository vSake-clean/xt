package com.vsake.keycopier;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.DashPathEffect;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.view.HapticFeedbackConstants;
import android.view.MotionEvent;
import android.view.View;

/**
 * Draws the key blade at real (1:1) scale. The user lays the physical key on the screen with its
 * shoulder against the red line and adjusts every cut until the drawn outline matches the key.
 */
public class KeyView extends View {
    public interface Listener { void onChanged(); }

    private Profile p;
    private int[] code;
    private int selected = 0;
    private float pxmm;
    private boolean mirrorH, mirrorV;
    private Listener listener;

    private final Paint bg = new Paint();
    private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint thin = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint dashed = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint shoulder = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint sel = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint warn = new Paint(Paint.ANTI_ALIAS_FLAG);

    private float shoulderPx, baseY; // screen x of shoulder; screen y of blade bottom (or top when mirrorV)

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
        sel.setColor(0xFF000000); sel.setStyle(Paint.Style.FILL);
        warn.setColor(0xFFB00000); warn.setTypeface(Typeface.DEFAULT_BOLD);
    }

    public void setup(Profile p, int[] code, float pxmm) {
        this.p = p; this.code = code; this.pxmm = pxmm;
        if (selected >= p.pins) selected = 0;
        invalidate();
    }

    public void setListener(Listener l) { listener = l; }
    public void setMirror(boolean h, boolean v) { mirrorH = h; mirrorV = v; invalidate(); }
    public boolean isMirrorH() { return mirrorH; }
    public boolean isMirrorV() { return mirrorV; }
    public int[] getCode() { return code; }
    public int getSelected() { return selected; }

    public void select(int delta) {
        selected = Math.max(0, Math.min(p.pins - 1, selected + delta));
        changed();
    }

    /** dir > 0 = raise cut root (shallower), dir < 0 = lower (deeper). */
    public void shiftDepth(int dir) {
        int idx = code[selected] + (p.depthStep >= 0 ? -dir : dir);
        idx = Math.max(0, Math.min(p.depthCount - 1, idx));
        if (idx != code[selected]) { code[selected] = idx; changed(); }
    }

    public void resetCode() { for (int i = 0; i < code.length; i++) code[i] = 0; changed(); }

    private void changed() {
        performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY);
        invalidate();
        if (listener != null) listener.onChanged();
    }

    // ---- coordinate helpers: mm along blade (from shoulder) / mm height (from bottom edge) -> px ----
    private float sx(double mm) { return (float) (mirrorH ? shoulderPx - mm * pxmm : shoulderPx + mm * pxmm); }
    private float sy(double h) { return (float) (mirrorV ? baseY + h * pxmm : baseY - h * pxmm); }
    private double mmX(float x) { return mirrorH ? (shoulderPx - x) / pxmm : (x - shoulderPx) / pxmm; }
    private double mmY(float y) { return mirrorV ? (y - baseY) / pxmm : (baseY - y) / pxmm; }

    /** Height of the top (cut) edge at position x (mm from shoulder). */
    private double topEdge(double x) {
        double H = p.bladeHeight;
        double slope = 1.0 / Math.tan(Math.toRadians(p.cutAngle / 2.0));
        double h = H;
        for (int i = 0; i < p.pins; i++) {
            double d = Math.abs(x - p.cutCenter(i)) - p.flat / 2.0;
            double v = p.root(code[i]) + slope * Math.max(0, d);
            if (v < h) h = v;
        }
        double tip = p.tipX();
        double tipLimit = H * 0.3 + (tip - x);
        return Math.max(0, Math.min(h, tipLimit));
    }

    private void layout() {
        float w = getWidth(), h = getHeight();
        float margin = 30f * pxmm; // room for the key bow
        shoulderPx = mirrorH ? w - margin : margin;
        float half = (float) (p.bladeHeight * pxmm / 2f);
        baseY = mirrorV ? h / 2f - half : h / 2f + half;
    }

    @Override
    protected void onDraw(Canvas c) {
        if (p == null) return;
        layout();
        c.drawPaint(bg);
        double H = p.bladeHeight;
        double tip = p.tipX();

        // bow (head) of the key, left of the shoulder
        float bx1 = sx(-26), bx2 = sx(0), by1 = sy(-3.5), by2 = sy(H + 3.5);
        RectF bow = new RectF(Math.min(bx1, bx2), Math.min(by1, by2), Math.max(bx1, bx2), Math.max(by1, by2));
        c.drawRoundRect(bow, 6 * pxmm, 6 * pxmm, fill);
        c.drawRoundRect(bow, 6 * pxmm, 6 * pxmm, stroke);

        // blade outline
        Path path = new Path();
        path.moveTo(sx(0), sy(0));
        path.lineTo(sx(tip - 1.5), sy(0));
        path.lineTo(sx(tip), sy(topEdge(tip)));
        for (double x = tip; x >= 0; x -= 0.05) path.lineTo(sx(x), sy(topEdge(x)));
        path.lineTo(sx(0), sy(topEdge(0)));
        path.close();
        c.drawPath(path, fill);
        c.drawPath(path, stroke);

        // decorative keyway grooves
        c.drawLine(sx(1), sy(H * 0.33), sx(tip - 3), sy(H * 0.33), thin);
        c.drawLine(sx(1), sy(H * 0.55), sx(tip - 4), sy(H * 0.55), thin);

        // shoulder alignment line
        c.drawLine(sx(0), 0, sx(0), getHeight(), shoulder);

        // pin centre lines + depth ladder on the selected pin
        float textSize = Math.max(28f, 3.2f * pxmm);
        text.setTextSize(textSize);
        float labelY = mirrorV ? sy(H + 4) + textSize : sy(H + 4);
        float arrowY = mirrorV ? labelY + textSize * 0.6f : labelY - textSize * 1.3f;
        for (int i = 0; i < p.pins; i++) {
            float x = sx(p.cutCenter(i));
            c.drawLine(x, sy(-2), x, sy(H + 2), dashed);
            text.setFakeBoldText(i == selected);
            c.drawText(p.label(code[i]), x, labelY, text);
        }
        float selX = sx(p.cutCenter(selected));
        drawArrow(c, selX, arrowY, textSize * 0.5f);

        float tick = (float) Math.max(p.flat / 2 + 0.6, 1.2) * pxmm;
        Paint ladder = new Paint(thin);
        ladder.setStrokeWidth(1.5f);
        ladder.setColor(0xAA000000);
        for (int d = 0; d < p.depthCount; d++) {
            float y = sy(p.root(d));
            c.drawLine(selX - tick, y, selX + tick, y, ladder);
        }
        Paint cur = new Paint(shoulder);
        cur.setStrokeWidth(3f);
        float cy = sy(p.root(code[selected]));
        c.drawLine(selX - tick * 1.4f, cy, selX + tick * 1.4f, cy, cur);

        // header: profile + code + warnings
        Paint hdr = new Paint(text);
        hdr.setTextAlign(Paint.Align.LEFT);
        hdr.setTextSize(Math.max(26f, 2.6f * pxmm));
        float hx = mirrorH ? 24 : sx(-26) > 0 ? sx(-26) : 24;
        float hy = hdr.getTextSize() + 16;
        c.drawText(p.shortName + "   " + Store.codeString(p, code), hx, hy, hdr);
        if (p.macs > 0) {
            for (int i = 0; i + 1 < p.pins; i++) {
                if (Math.abs(code[i] - code[i + 1]) > p.macs) {
                    warn.setTextSize(hdr.getTextSize() * 0.8f);
                    c.drawText("Uwaga: przekroczony MACS (" + p.macs + ") między " + (i + 1) + " i " + (i + 2),
                            hx, hy * 2, warn);
                    break;
                }
            }
        }
        Paint hint = new Paint(hdr);
        hint.setTextSize(hdr.getTextSize() * 0.6f);
        hint.setColor(0xAA000000);
        c.drawText("Oprzyj ramię klucza o czerwoną linię", hx, getHeight() - 16, hint);
    }

    private void drawArrow(Canvas c, float x, float y, float s) {
        Path a = new Path();
        if (mirrorV) { a.moveTo(x, y); a.lineTo(x - s / 2, y + s); a.lineTo(x + s / 2, y + s); }
        else { a.moveTo(x, y + s); a.lineTo(x - s / 2, y); a.lineTo(x + s / 2, y); }
        a.close();
        c.drawPath(a, sel);
    }

    @Override
    public boolean onTouchEvent(MotionEvent e) {
        if (p == null) return false;
        int a = e.getActionMasked();
        if (a != MotionEvent.ACTION_DOWN && a != MotionEvent.ACTION_MOVE) return a == MotionEvent.ACTION_UP;
        double x = mmX(e.getX()), y = mmY(e.getY());
        if (x < p.firstCut - p.spacing || x > p.tipX() + 2) return true;
        int pin = (int) Math.round((x - p.firstCut) / p.spacing);
        pin = Math.max(0, Math.min(p.pins - 1, pin));
        boolean change = false;
        if (pin != selected) { selected = pin; change = true; }
        if (y > -2 && y < p.bladeHeight + 2.5) {
            int best = code[pin];
            double bd = Double.MAX_VALUE;
            for (int d = 0; d < p.depthCount; d++) {
                double dd = Math.abs(p.root(d) - y);
                if (dd < bd) { bd = dd; best = d; }
            }
            if (best != code[pin]) { code[pin] = best; change = true; }
        }
        if (change) changed();
        return true;
    }
}
