package com.vsake.keycopier;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.pdf.PdfDocument;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.List;
import java.util.Locale;

/** File exports: PDF 1:1 for printing, SVG for laser/plotter, STL 3D model, plain text. */
public class Exporter {

    public static String baseName(Profile p, int[] code) {
        StringBuilder sb = new StringBuilder("klucz_").append(p.shortName.replaceAll("[^A-Za-z0-9]+", ""));
        sb.append('_');
        for (int i = 0; i < code.length; i++) sb.append(p.label(code[i]));
        return sb.toString();
    }

    public static String text(Profile p, int[] code) {
        return "Klucz: " + p.name + "\nKod: " + Store.codeString(p, code)
                + (p.doubleSided ? "  (góra | dół)" : "")
                + String.format(Locale.US, "\nPiny: %d, rozstaw %.2f mm, 1. nacięcie %.2f mm od ramienia",
                p.pins, p.spacing, p.firstCut);
    }

    public static File pdf(Context c, Profile p, int[] code) throws IOException {
        Geometry g = new Geometry(p, code);
        final float k = 72f / 25.4f; // points per mm
        PdfDocument doc = new PdfDocument();
        PdfDocument.Page page = doc.startPage(new PdfDocument.PageInfo.Builder(595, 842, 1).create());
        Canvas cv = page.getCanvas();
        Paint line = new Paint(Paint.ANTI_ALIAS_FLAG);
        line.setStyle(Paint.Style.STROKE);
        line.setStrokeWidth(0.6f);
        Paint txt = new Paint(Paint.ANTI_ALIAS_FLAG);
        txt.setTextSize(11);

        cv.drawText("Key Copier – " + p.name, 40, 50, txt);
        cv.drawText("Kod: " + Store.codeString(p, code), 40, 66, txt);
        cv.drawText("Drukuj w skali 100% (bez dopasowania do strony). Sprawdź linijką 50 mm poniżej.", 40, 82, txt);

        float ox = 40 + (float) (Geometry.BOW_LEN * k), oy = 200;
        // bow
        RectF bow = new RectF(ox - (float) (Geometry.BOW_LEN * k), oy - (float) ((p.bladeHeight + Geometry.BOW_EXTRA) * k),
                ox, oy + (float) (Geometry.BOW_EXTRA * k));
        cv.drawRoundRect(bow, (float) (Geometry.BOW_RADIUS * k), (float) (Geometry.BOW_RADIUS * k), line);
        cv.drawCircle(ox + (float) (Geometry.HOLE_X * k), oy - (float) (g.holeCy() * k), (float) (Geometry.HOLE_R * k), line);
        // blade
        Path path = new Path();
        List<double[]> pts = g.outline(0.05);
        for (int i = 0; i < pts.size(); i++) {
            float x = ox + (float) (pts.get(i)[0] * k), y = oy - (float) (pts.get(i)[1] * k);
            if (i == 0) path.moveTo(x, y); else path.lineTo(x, y);
        }
        path.close();
        cv.drawPath(path, line);
        Paint thin = new Paint(line);
        thin.setStrokeWidth(0.25f);
        for (int i = 0; i < p.pins; i++) {
            float x = ox + (float) (p.cutCenter(i) * k);
            cv.drawLine(x, oy + 8, x, oy - (float) ((p.bladeHeight + 2) * k), thin);
        }
        // 50 mm ruler
        float ry = 320;
        cv.drawLine(40, ry, 40 + 50 * k, ry, line);
        for (int i = 0; i <= 50; i++) {
            float len = i % 10 == 0 ? 10 : i % 5 == 0 ? 6 : 3;
            cv.drawLine(40 + i * k, ry, 40 + i * k, ry - len, thin);
        }
        cv.drawText("50 mm", 40 + 50 * k + 6, ry, txt);
        doc.finishPage(page);
        File f = new File(FilesProvider.dir(c), baseName(p, code) + ".pdf");
        try (FileOutputStream os = new FileOutputStream(f)) { doc.writeTo(os); }
        doc.close();
        return f;
    }

    public static File svg(Context c, Profile p, int[] code) throws IOException {
        Geometry g = new Geometry(p, code);
        double ox = Geometry.BOW_LEN + 2, top = p.bladeHeight + Geometry.BOW_EXTRA + 2;
        double w = ox + p.tipX() + 2, h = top + Geometry.BOW_EXTRA + 2;
        StringBuilder d = new StringBuilder();
        List<double[]> pts = g.outline(0.05);
        for (int i = 0; i < pts.size(); i++) {
            d.append(i == 0 ? "M" : "L").append(String.format(Locale.US, "%.3f %.3f ", ox + pts.get(i)[0], top - pts.get(i)[1]));
        }
        d.append('Z');
        StringBuilder s = new StringBuilder();
        s.append(String.format(Locale.US, "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"%.3fmm\" height=\"%.3fmm\" viewBox=\"0 0 %.3f %.3f\">\n", w, h, w, h));
        s.append("<!-- ").append(p.name).append(" kod ").append(Store.codeString(p, code)).append(" -->\n");
        s.append("<g fill=\"none\" stroke=\"#000\" stroke-width=\"0.1\">\n");
        s.append(String.format(Locale.US, "<rect x=\"%.3f\" y=\"%.3f\" width=\"%.3f\" height=\"%.3f\" rx=\"%.3f\"/>\n",
                2.0, top - p.bladeHeight - Geometry.BOW_EXTRA, Geometry.BOW_LEN, p.bladeHeight + 2 * Geometry.BOW_EXTRA, Geometry.BOW_RADIUS));
        s.append(String.format(Locale.US, "<circle cx=\"%.3f\" cy=\"%.3f\" r=\"%.3f\"/>\n", ox + Geometry.HOLE_X, top - g.holeCy(), Geometry.HOLE_R));
        s.append("<path d=\"").append(d).append("\"/>\n</g>\n</svg>\n");
        File f = new File(FilesProvider.dir(c), baseName(p, code) + ".svg");
        try (Writer wr = new OutputStreamWriter(new FileOutputStream(f), "UTF-8")) { wr.write(s.toString()); }
        return f;
    }

    public static File stl(Context c, Profile p, int[] code) throws IOException {
        Mesh m = Mesh.build(new Geometry(p, code));
        File f = new File(FilesProvider.dir(c), baseName(p, code) + ".stl");
        m.writeStl(f, "KeyCopier " + p.shortName + " " + Store.codeString(p, code));
        return f;
    }
}
