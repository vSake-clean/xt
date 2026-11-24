package com.vsake.keycopier;

import java.util.ArrayList;
import java.util.List;

/**
 * Shared key geometry in millimetres. x = distance from the shoulder along the blade,
 * y = height above the bottom edge of the blade. Used by the screen view, PDF/SVG export and 3D model.
 */
public class Geometry {
    public static final double BOW_LEN = 26, BOW_EXTRA = 3.5, BOW_RADIUS = 6, HOLE_R = 3.5, HOLE_X = -19;

    public final Profile p;
    public final int[] code;

    public Geometry(Profile p, int[] code) { this.p = p; this.code = code; }

    private double slope() { return 1.0 / Math.tan(Math.toRadians(Math.max(20, Math.min(170, p.cutAngle)) / 2.0)); }

    public double tipY() { return p.doubleSided ? p.bladeHeight / 2 : p.bladeHeight * 0.3; }

    /** Height of the top edge at x. */
    public double top(double x) {
        double H = p.bladeHeight, s = slope(), h = H;
        for (int i = 0; i < p.pins; i++) {
            double d = Math.abs(x - p.cutCenter(i)) - p.flat / 2.0;
            h = Math.min(h, p.root(code[i]) + s * Math.max(0, d));
        }
        h = Math.min(h, tipY() + (p.tipX() - x));
        return Math.max(h, bottom(x));
    }

    /** Height of the bottom edge at x. */
    public double bottom(double x) {
        double tip = p.tipX();
        if (!p.doubleSided) {
            double start = tip - 1.5;
            return x > start ? Math.min(tipY(), (x - start) / 1.5 * tipY()) : 0;
        }
        double H = p.bladeHeight, s = slope(), b = 0;
        for (int i = 0; i < p.pins; i++) {
            double d = Math.abs(x - p.cutCenter(i)) - p.flat / 2.0;
            b = Math.max(b, (H - p.root(code[p.pins + i])) - s * Math.max(0, d));
        }
        b = Math.max(b, tipY() - (tip - x));
        return Math.min(b, H);
    }

    /** Blade outline polygon (counter-clockwise, y up), starting at the shoulder bottom. */
    public List<double[]> outline(double step) {
        List<double[]> pts = new ArrayList<>();
        double tip = p.tipX();
        int n = (int) Math.ceil(tip / step);
        for (int i = 0; i <= n; i++) { double x = tip * i / n; pts.add(new double[]{x, bottom(x)}); }
        for (int i = n; i >= 0; i--) { double x = tip * i / n; pts.add(new double[]{x, top(x)}); }
        return pts;
    }

    // ---- bow (head) ----
    public double bowBottom(double x) {
        double r = BOW_RADIUS, cx = -BOW_LEN + r, base = -BOW_EXTRA;
        if (x < cx) { double dx = cx - x; return base + r - Math.sqrt(Math.max(0, r * r - dx * dx)); }
        return base;
    }

    public double bowTop(double x) {
        double r = BOW_RADIUS, cx = -BOW_LEN + r, base = p.bladeHeight + BOW_EXTRA;
        if (x < cx) { double dx = cx - x; return base - r + Math.sqrt(Math.max(0, r * r - dx * dx)); }
        return base;
    }

    public double holeCy() { return p.bladeHeight / 2; }

    /** Half-height of the keyring hole at x (0 outside the hole). */
    public double holeHalf(double x) {
        double dx = x - HOLE_X;
        return Math.sqrt(Math.max(0, HOLE_R * HOLE_R - dx * dx));
    }

    /** Keyway cross-section as bands: {y0, y1, z0, z1}, bottom to top. */
    public List<double[]> bands() {
        double H = p.bladeHeight, T = Math.max(0.6, p.thickness);
        List<double[]> grooves = new ArrayList<>();
        List<Double> cuts = new ArrayList<>();
        cuts.add(0.0); cuts.add(H);
        if (p.grooves != null) {
            for (String g : p.grooves.split(";")) {
                String[] f = g.trim().split(":");
                if (f.length != 4) continue;
                try {
                    double side = f[0].trim().equalsIgnoreCase("B") ? 1 : 0;
                    double y = Double.parseDouble(f[1].trim().replace(',', '.'));
                    double w = Double.parseDouble(f[2].trim().replace(',', '.'));
                    double d = Double.parseDouble(f[3].trim().replace(',', '.'));
                    double y0 = Math.max(0, y - w / 2), y1 = Math.min(H, y + w / 2);
                    if (y1 - y0 < 0.05 || d <= 0) continue;
                    grooves.add(new double[]{side, y0, y1, Math.min(d, T * 0.45)});
                    cuts.add(y0); cuts.add(y1);
                } catch (NumberFormatException ignored) { }
            }
        }
        java.util.Collections.sort(cuts);
        List<double[]> bands = new ArrayList<>();
        for (int i = 0; i + 1 < cuts.size(); i++) {
            double y0 = cuts.get(i), y1 = cuts.get(i + 1);
            if (y1 - y0 < 1e-6) continue;
            double ym = (y0 + y1) / 2, z0 = 0, z1 = T;
            for (double[] g : grooves) {
                if (ym > g[1] && ym < g[2]) {
                    if (g[0] == 1) z0 = Math.max(z0, g[3]); else z1 = Math.min(z1, T - g[3]);
                }
            }
            if (z1 - z0 < 0.3) { double m = (z0 + z1) / 2; z0 = m - 0.15; z1 = m + 0.15; }
            bands.add(new double[]{y0, y1, z0, z1});
        }
        return bands;
    }
}
