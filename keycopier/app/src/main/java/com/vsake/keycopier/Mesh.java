package com.vsake.keycopier;

import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.List;

/**
 * Builds a printable 3D model of the key (bow + cut blade + keyway grooves) as a triangle mesh.
 * The blade is split into thin columns along x and into cross-section bands along y; each cell is a
 * convex prism. Only faces on the outside of the solid are emitted, so the mesh is closed.
 */
public class Mesh {
    private static final double EPS = 1e-7;
    private float[] data = new float[9 * 4096];
    private int n; // triangles

    public int triangles() { return n; }

    public float[] data() { return data; }

    private void tri(double[] a, double[] b, double[] c) {
        if (9 * (n + 1) > data.length) {
            float[] d = new float[data.length * 2];
            System.arraycopy(data, 0, d, 0, data.length);
            data = d;
        }
        int o = 9 * n++;
        data[o] = (float) a[0]; data[o + 1] = (float) a[1]; data[o + 2] = (float) a[2];
        data[o + 3] = (float) b[0]; data[o + 4] = (float) b[1]; data[o + 5] = (float) b[2];
        data[o + 6] = (float) c[0]; data[o + 7] = (float) c[1]; data[o + 8] = (float) c[2];
    }

    /** Side wall along polygon edge a->b (polygon CCW in xy) between za and zb. */
    private void wall(double[] a, double[] b, double za, double zb) {
        if (zb - za < EPS) return;
        double[] a0 = {a[0], a[1], za}, b0 = {b[0], b[1], za}, b1 = {b[0], b[1], zb}, a1 = {a[0], a[1], zb};
        tri(a0, b0, b1);
        tri(a0, b1, a1);
    }

    /** Wall for the part of [z0,z1] not covered by the neighbour's [n0,n1]. */
    private void wallMinus(double[] a, double[] b, double z0, double z1, double n0, double n1) {
        if (n0 > z0) wall(a, b, z0, Math.min(z1, n0));
        if (n1 < z1) wall(a, b, Math.max(z0, n1), z1);
    }

    private void caps(List<double[]> poly, double z0, double z1) {
        double[] p0 = poly.get(0);
        for (int k = 1; k + 1 < poly.size(); k++) {
            double[] pa = poly.get(k), pb = poly.get(k + 1);
            tri(new double[]{p0[0], p0[1], z1}, new double[]{pa[0], pa[1], z1}, new double[]{pb[0], pb[1], z1});
            tri(new double[]{p0[0], p0[1], z0}, new double[]{pb[0], pb[1], z0}, new double[]{pa[0], pa[1], z0});
        }
    }

    /** Clip polygon by half-plane a*x + b*y + c >= 0 (Sutherland–Hodgman). */
    private static List<double[]> clip(List<double[]> in, double a, double b, double c) {
        List<double[]> out = new ArrayList<>();
        int m = in.size();
        for (int i = 0; i < m; i++) {
            double[] P = in.get(i), Q = in.get((i + 1) % m);
            double fp = a * P[0] + b * P[1] + c, fq = a * Q[0] + b * Q[1] + c;
            if (fp >= 0) out.add(P);
            if ((fp >= 0) != (fq >= 0)) {
                double t = fp / (fp - fq);
                out.add(new double[]{P[0] + (Q[0] - P[0]) * t, P[1] + (Q[1] - P[1]) * t});
            }
        }
        return out;
    }

    private static List<double[]> clean(List<double[]> in) {
        List<double[]> out = new ArrayList<>();
        for (double[] q : in) {
            if (!out.isEmpty()) {
                double[] l = out.get(out.size() - 1);
                if (Math.abs(l[0] - q[0]) < EPS && Math.abs(l[1] - q[1]) < EPS) continue;
            }
            out.add(q);
        }
        while (out.size() > 1) {
            double[] f = out.get(0), l = out.get(out.size() - 1);
            if (Math.abs(l[0] - f[0]) < EPS && Math.abs(l[1] - f[1]) < EPS) out.remove(out.size() - 1); else break;
        }
        if (out.size() < 3) return null;
        double area = 0;
        for (int i = 0; i < out.size(); i++) {
            double[] P = out.get(i), Q = out.get((i + 1) % out.size());
            area += P[0] * Q[1] - Q[0] * P[1];
        }
        return area > 1e-9 ? out : null;
    }

    /** Convex region inside column [xa,xb], strip [y0,y1], above line lo and below line hi. */
    private static List<double[]> cell(double xa, double xb, double y0, double y1,
                                       double loA, double loB, double hiA, double hiB) {
        List<double[]> poly = new ArrayList<>();
        poly.add(new double[]{xa, y0}); poly.add(new double[]{xb, y0});
        poly.add(new double[]{xb, y1}); poly.add(new double[]{xa, y1});
        double k = (xb - xa);
        // y >= lo(x):  -(loB-loA)/k * x + y - (loA - (loB-loA)/k*xa) >= 0
        double sl = (loB - loA) / k;
        poly = clip(poly, -sl, 1, -(loA - sl * xa));
        if (poly.size() < 3) return null;
        double sh = (hiB - hiA) / k;
        poly = clip(poly, sh, -1, hiA - sh * xa);
        if (poly.size() < 3) return null;
        return clean(poly);
    }

    private static boolean on(double v, double w) { return Math.abs(v - w) < 1e-6; }

    public static Mesh build(Geometry g) {
        Mesh m = new Mesh();
        Profile p = g.p;
        double T = Math.max(0.6, p.thickness);
        List<double[]> bands = g.bands();
        double tip = p.tipX();

        // ---------- blade ----------
        int cols = Math.max(20, (int) Math.ceil(tip / 0.1));
        double[] xs = new double[cols + 1], tops = new double[cols + 1], bots = new double[cols + 1];
        for (int i = 0; i <= cols; i++) { xs[i] = tip * i / cols; tops[i] = g.top(xs[i]); bots[i] = g.bottom(xs[i]); }
        for (int j = 0; j < bands.size(); j++) {
            double[] bd = bands.get(j);
            for (int i = 0; i < cols; i++) {
                double xa = xs[i], xb = xs[i + 1];
                List<double[]> poly = cell(xa, xb, bd[0], bd[1], bots[i], bots[i + 1], tops[i], tops[i + 1]);
                if (poly == null) continue;
                m.caps(poly, bd[2], bd[3]);
                for (int k = 0; k < poly.size(); k++) {
                    double[] a = poly.get(k), b = poly.get((k + 1) % poly.size());
                    double xm = (a[0] + b[0]) / 2;
                    if (on(a[0], xa) && on(b[0], xa)) continue;            // shared with left column / bow
                    if (on(a[0], xb) && on(b[0], xb)) {
                        if (i < cols - 1) continue;                         // shared with right column
                        m.wall(a, b, bd[2], bd[3]);
                        continue;
                    }
                    double tm = tops[i] + (tops[i + 1] - tops[i]) * (xm - xa) / (xb - xa);
                    double bm = bots[i] + (bots[i + 1] - bots[i]) * (xm - xa) / (xb - xa);
                    if (on(a[1], bd[0]) && on(b[1], bd[0]) && j > 0 && bm < bd[0] - 1e-6) {
                        double[] nb = bands.get(j - 1);
                        m.wallMinus(a, b, bd[2], bd[3], nb[2], nb[3]);
                    } else if (on(a[1], bd[1]) && on(b[1], bd[1]) && j < bands.size() - 1 && tm > bd[1] + 1e-6) {
                        double[] nb = bands.get(j + 1);
                        m.wallMinus(a, b, bd[2], bd[3], nb[2], nb[3]);
                    } else {
                        m.wall(a, b, bd[2], bd[3]);
                    }
                }
            }
        }

        // ---------- bow ----------
        double L = Geometry.BOW_LEN;
        int bc = 80;
        double[] bx = new double[bc + 1];
        for (int i = 0; i <= bc; i++) bx[i] = -L + L * i / bc;
        double cy = g.holeCy();
        for (int i = 0; i < bc; i++) {
            double xa = bx[i], xb = bx[i + 1];
            List<double[][]> ivA = bowIntervals(g, xa, xa, xb), ivB = bowIntervals(g, xb, xa, xb);
            for (int q = 0; q < ivA.size(); q++) {
                double[] A = ivA.get(q)[0], B = ivB.get(q)[0];
                List<double[]> poly = cell(xa, xb, -1e3, 1e3, A[0], B[0], A[1], B[1]);
                if (poly == null) continue;
                m.caps(poly, 0, T);
                for (int k = 0; k < poly.size(); k++) {
                    double[] a = poly.get(k), b = poly.get((k + 1) % poly.size());
                    if ((on(a[0], xa) && on(b[0], xa)) || (on(a[0], xb) && on(b[0], xb))) continue;
                    m.wall(a, b, 0, T);
                }
            }
            // vertical faces at column boundaries: own segments minus neighbour's segments
            List<double[]> own = segs(bowIntervals(g, xa, xa, xb));
            List<double[]> left = i > 0 ? segs(bowIntervals(g, xa, bx[i - 1], xa)) : new ArrayList<double[]>();
            for (double[] s : subtract(own, left)) m.wall(new double[]{xa, s[1]}, new double[]{xa, s[0]}, 0, T);
            List<double[]> ownR = segs(bowIntervals(g, xb, xa, xb));
            if (i < bc - 1) {
                List<double[]> right = segs(bowIntervals(g, xb, xb, bx[i + 2]));
                for (double[] s : subtract(ownR, right)) m.wall(new double[]{xb, s[0]}, new double[]{xb, s[1]}, 0, T);
            } else {
                // shoulder face at x = 0: bow minus blade cross-section
                double t0 = g.top(0), b0 = g.bottom(0);
                for (double[] s : ownR) {
                    List<double[]> blade = new ArrayList<>();
                    blade.add(new double[]{b0, t0});
                    for (double[] r : subtract(java.util.Collections.singletonList(s), blade))
                        m.wall(new double[]{0, r[0]}, new double[]{0, r[1]}, 0, T);
                    for (double[] bd : bands) {
                        double u = Math.max(Math.max(bd[0], b0), s[0]), v = Math.min(Math.min(bd[1], t0), s[1]);
                        if (v - u < EPS) continue;
                        m.wallMinus(new double[]{0, u}, new double[]{0, v}, 0, T, bd[2], bd[3]);
                    }
                }
            }
        }
        return m;
    }

    /** Bow y-intervals at x for the column [xa,xb] (the hole is used when the column centre is inside it). */
    private static List<double[][]> bowIntervals(Geometry g, double x, double xa, double xb) {
        List<double[][]> l = new ArrayList<>();
        double lo = g.bowBottom(x), hi = g.bowTop(x), mid = (xa + xb) / 2, cy = g.holeCy();
        if (g.holeHalf(mid) > 0) {
            double h = g.holeHalf(x);
            l.add(new double[][]{{lo, cy - h}});
            l.add(new double[][]{{cy + h, hi}});
        } else {
            l.add(new double[][]{{lo, hi}});
        }
        return l;
    }

    private static List<double[]> segs(List<double[][]> iv) {
        List<double[]> s = new ArrayList<>();
        for (double[][] v : iv) if (v[0][1] - v[0][0] > EPS) s.add(new double[]{v[0][0], v[0][1]});
        return s;
    }

    /** 1D interval subtraction A \ B. */
    private static List<double[]> subtract(List<double[]> a, List<double[]> b) {
        List<double[]> cur = new ArrayList<>(a);
        for (double[] r : b) {
            List<double[]> next = new ArrayList<>();
            for (double[] s : cur) {
                if (r[1] <= s[0] || r[0] >= s[1]) { next.add(s); continue; }
                if (r[0] > s[0] + EPS) next.add(new double[]{s[0], r[0]});
                if (r[1] < s[1] - EPS) next.add(new double[]{r[1], s[1]});
            }
            cur = next;
        }
        return cur;
    }

    public void writeStl(File f, String header) throws IOException {
        try (OutputStream os = new BufferedOutputStream(new FileOutputStream(f))) {
            ByteBuffer h = ByteBuffer.allocate(84).order(ByteOrder.LITTLE_ENDIAN);
            byte[] hb = header.getBytes("US-ASCII");
            h.put(hb, 0, Math.min(80, hb.length));
            h.position(80);
            h.putInt(n);
            os.write(h.array());
            ByteBuffer t = ByteBuffer.allocate(50).order(ByteOrder.LITTLE_ENDIAN);
            for (int i = 0; i < n; i++) {
                int o = 9 * i;
                float ux = data[o + 3] - data[o], uy = data[o + 4] - data[o + 1], uz = data[o + 5] - data[o + 2];
                float vx = data[o + 6] - data[o], vy = data[o + 7] - data[o + 1], vz = data[o + 8] - data[o + 2];
                float nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
                float len = (float) Math.sqrt(nx * nx + ny * ny + nz * nz);
                if (len > 0) { nx /= len; ny /= len; nz /= len; }
                t.clear();
                t.putFloat(nx); t.putFloat(ny); t.putFloat(nz);
                for (int k = 0; k < 9; k++) t.putFloat(data[o + k]);
                t.putShort((short) 0);
                os.write(t.array());
            }
        }
    }
}
