package com.vsake.keycopier;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.os.Bundle;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.Toast;

/**
 * Screen calibration: the user places a standard ID / bank card (ISO/IEC 7810 ID-1, 85.60 x 53.98 mm)
 * on the screen and scales the rectangle until it matches the card exactly.
 */
public class CalibrationActivity extends Activity {
    private static final float CARD_W = 85.60f, CARD_H = 53.98f;
    private float pxmm;
    private CalView view;

    @Override
    protected void onCreate(Bundle s) {
        super.onCreate(s);
        pxmm = Store.pxPerMm(this);
        FrameLayout root = new FrameLayout(this);
        view = new CalView(this);
        root.addView(view, new FrameLayout.LayoutParams(-1, -1));

        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.VERTICAL);
        int pad = Ui.dp(this, 8);
        bar.setPadding(pad, pad, pad, pad);
        bar.addView(Ui.button(this, "+ +", v -> adjust(1.01f)), lp());
        bar.addView(Ui.button(this, "+", v -> adjust(1.001f)), lp());
        bar.addView(Ui.button(this, "−", v -> adjust(1 / 1.001f)), lp());
        bar.addView(Ui.button(this, "− −", v -> adjust(1 / 1.01f)), lp());
        bar.addView(Ui.button(this, "Zapisz", v -> {
            Store.setPxPerMm(this, pxmm);
            Toast.makeText(this, "Kalibracja zapisana", Toast.LENGTH_SHORT).show();
            finish();
        }), lp());
        bar.addView(Ui.button(this, "Reset", v -> { pxmm = Store.defaultPxPerMm(this); view.invalidate(); }), lp());
        FrameLayout.LayoutParams blp = new FrameLayout.LayoutParams(Ui.dp(this, 120), -2);
        blp.gravity = Gravity.END | Gravity.CENTER_VERTICAL;
        root.addView(bar, blp);
        setContentView(root);
        Ui.immersive(this);
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) Ui.immersive(this);
    }

    private LinearLayout.LayoutParams lp() {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, Ui.dp(this, 46));
        p.topMargin = Ui.dp(this, 4);
        return p;
    }

    private void adjust(float f) { pxmm *= f; view.invalidate(); }

    private class CalView extends View {
        private final Paint bg = new Paint(), card = new Paint(Paint.ANTI_ALIAS_FLAG),
                edge = new Paint(Paint.ANTI_ALIAS_FLAG), tick = new Paint(), txt = new Paint(Paint.ANTI_ALIAS_FLAG);
        private float lastX;

        CalView(Context c) {
            super(c);
            bg.setColor(0xFFFF8C1A);
            card.setColor(0x55FFFFFF);
            edge.setColor(0xFF000000); edge.setStyle(Paint.Style.STROKE); edge.setStrokeWidth(3);
            tick.setColor(0xFF000000); tick.setStrokeWidth(2);
            txt.setColor(0xFF000000);
        }

        @Override
        protected void onDraw(Canvas c) {
            c.drawPaint(bg);
            // card anchored to the top-left corner so it can be aligned against the screen edge
            float m = 3 * pxmm;
            RectF r = new RectF(m, m, m + CARD_W * pxmm, m + CARD_H * pxmm);
            c.drawRoundRect(r, 3.18f * pxmm, 3.18f * pxmm, card);
            c.drawRoundRect(r, 3.18f * pxmm, 3.18f * pxmm, edge);
            // mm ruler under the card
            float y0 = r.bottom + 4 * pxmm;
            txt.setTextSize(Math.max(24, 2.5f * pxmm));
            for (int i = 0; i <= 85; i++) {
                float x = m + i * pxmm;
                float len = (i % 10 == 0 ? 4 : i % 5 == 0 ? 2.5f : 1.5f) * pxmm;
                c.drawLine(x, y0, x, y0 + len, tick);
                if (i % 10 == 0) c.drawText(String.valueOf(i / 10), x + 3, y0 + len + txt.getTextSize(), txt);
            }
            txt.setTextSize(Math.max(26, 2.8f * pxmm));
            float tx = m + 4 * pxmm;
            c.drawText("Połóż kartę płatniczą / dowód", tx, m + 10 * pxmm, txt);
            c.drawText("w lewym górnym rogu i dopasuj", tx, m + 16 * pxmm, txt);
            c.drawText("prostokąt (+/− lub przeciągnij).", tx, m + 22 * pxmm, txt);
            c.drawText(String.format("%.2f px/mm", pxmm), tx, m + 34 * pxmm, txt);
        }

        @Override
        public boolean onTouchEvent(MotionEvent e) {
            if (e.getActionMasked() == MotionEvent.ACTION_DOWN) lastX = e.getX();
            else if (e.getActionMasked() == MotionEvent.ACTION_MOVE) {
                float dx = e.getX() - lastX;
                lastX = e.getX();
                pxmm = Math.max(2f, pxmm + dx / CARD_W * 0.25f);
                invalidate();
            }
            return true;
        }
    }
}
