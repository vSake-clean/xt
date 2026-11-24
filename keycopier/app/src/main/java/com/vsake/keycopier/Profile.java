package com.vsake.keycopier;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/** Key blank profile. All dimensions in millimetres. */
public class Profile {
    public String id;
    public String name;
    public String shortName;
    public int pins;
    public double bladeHeight;   // height of the blade (bottom edge -> top edge)
    public double firstCut;      // shoulder -> centre of first cut
    public double spacing;       // centre-to-centre spacing of cuts
    public double root0;         // root height (from bottom edge) of depth index 0
    public double depthStep;     // root height decrease per depth index
    public int depthCount;       // number of depths
    public int labelStart;       // label of depth index 0 (e.g. Kwikset starts at 1)
    public double cutAngle;      // included angle of the V cut, degrees
    public double flat;          // width of the flat at the cut root
    public double tipLength;     // last cut centre -> tip
    public int macs;             // max adjacent cut spec, 0 = none
    public boolean builtIn;

    private static final double IN = 25.4;

    public double root(int idx) { return root0 - depthStep * idx; }

    public double cutCenter(int pin) { return firstCut + spacing * pin; }

    public double tipX() { return cutCenter(pins - 1) + tipLength; }

    public String label(int idx) { return String.valueOf(labelStart + idx); }

    public Profile copy() {
        try { return fromJson(toJson()); } catch (JSONException e) { throw new RuntimeException(e); }
    }

    public JSONObject toJson() throws JSONException {
        JSONObject o = new JSONObject();
        o.put("id", id); o.put("name", name); o.put("short", shortName);
        o.put("pins", pins); o.put("h", bladeHeight); o.put("first", firstCut);
        o.put("sp", spacing); o.put("root0", root0); o.put("step", depthStep);
        o.put("n", depthCount); o.put("ls", labelStart); o.put("ang", cutAngle);
        o.put("flat", flat); o.put("tip", tipLength); o.put("macs", macs);
        return o;
    }

    public static Profile fromJson(JSONObject o) throws JSONException {
        Profile p = new Profile();
        p.id = o.getString("id"); p.name = o.getString("name"); p.shortName = o.optString("short", p.name);
        p.pins = o.getInt("pins"); p.bladeHeight = o.getDouble("h"); p.firstCut = o.getDouble("first");
        p.spacing = o.getDouble("sp"); p.root0 = o.getDouble("root0"); p.depthStep = o.getDouble("step");
        p.depthCount = o.getInt("n"); p.labelStart = o.optInt("ls", 0); p.cutAngle = o.optDouble("ang", 90);
        p.flat = o.optDouble("flat", 0.8); p.tipLength = o.optDouble("tip", 5); p.macs = o.optInt("macs", 0);
        return p;
    }

    private static Profile inch(String id, String name, String sn, int pins, double h, double first, double sp,
                                double root0, double inc, int n, int ls, double ang, double flat, int macs) {
        Profile p = new Profile();
        p.id = id; p.name = name; p.shortName = sn; p.pins = pins;
        p.bladeHeight = h * IN; p.firstCut = first * IN; p.spacing = sp * IN;
        p.root0 = root0 * IN; p.depthStep = inc * IN; p.depthCount = n; p.labelStart = ls;
        p.cutAngle = ang; p.flat = flat * IN; p.tipLength = 0.22 * IN; p.macs = macs; p.builtIn = true;
        return p;
    }

    private static Profile mm(String id, String name, String sn, int pins, double h, double first, double sp,
                              double root0, double step, int n, int ls, double ang, double flat, double tip, int macs) {
        Profile p = new Profile();
        p.id = id; p.name = name; p.shortName = sn; p.pins = pins;
        p.bladeHeight = h; p.firstCut = first; p.spacing = sp; p.root0 = root0; p.depthStep = step;
        p.depthCount = n; p.labelStart = ls; p.cutAngle = ang; p.flat = flat; p.tipLength = tip;
        p.macs = macs; p.builtIn = true;
        return p;
    }

    public static List<Profile> builtIns() {
        List<Profile> l = new ArrayList<>();
        // European profile cylinder keys – generic values, adjust with "Edytuj kopię" if your key differs.
        l.add(mm("euro5", "Europrofil 5 pin (ogólny)", "EURO5", 5, 8.6, 4.0, 4.0, 8.0, 0.5, 8, 0, 90, 0.8, 5.0, 0));
        l.add(mm("euro6", "Europrofil 6 pin (ogólny)", "EURO6", 6, 8.6, 4.0, 4.0, 8.0, 0.5, 8, 0, 90, 0.8, 5.0, 0));
        l.add(inch("kw1", "Kwikset KW1 (5 pin)", "KW1", 5, .335, .247, .150, .329, .023, 7, 1, 90, .084, 4));
        l.add(inch("kw10", "Kwikset KW10 (6 pin)", "KW10", 6, .335, .247, .150, .329, .023, 7, 1, 90, .084, 4));
        l.add(inch("sc1", "Schlage SC1 (5 pin)", "SC1", 5, .343, .231, .156, .335, .015, 10, 0, 100, .031, 7));
        l.add(inch("sc4", "Schlage SC4 (6 pin)", "SC4", 6, .343, .231, .156, .335, .015, 10, 0, 100, .031, 7));
        l.add(inch("y1", "Yale Y1 (5 pin)", "Y1", 5, .335, .200, .165, .320, .019, 10, 0, 90, .054, 7));
        l.add(inch("m1", "Master Lock M1 (4 pin)", "M1", 4, .284, .185, .125, .276, .015, 8, 0, 90, .031, 7));
        return l;
    }
}
