package com.vsake.keycopier;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.DisplayMetrics;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/** Persistence: calibration, custom profiles and saved keys. */
public class Store {
    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences("keycopier", Context.MODE_PRIVATE);
    }

    public static float defaultPxPerMm(Context c) {
        DisplayMetrics dm = c.getResources().getDisplayMetrics();
        float dpi = (dm.xdpi + dm.ydpi) / 2f;
        if (dpi < 50) dpi = dm.densityDpi;
        return dpi / 25.4f;
    }

    public static float pxPerMm(Context c) {
        return prefs(c).getFloat("pxmm", defaultPxPerMm(c));
    }

    public static boolean isCalibrated(Context c) { return prefs(c).contains("pxmm"); }

    public static void setPxPerMm(Context c, float v) { prefs(c).edit().putFloat("pxmm", v).apply(); }

    public static void resetCalibration(Context c) { prefs(c).edit().remove("pxmm").apply(); }

    // ---- custom profiles ----
    public static List<Profile> customProfiles(Context c) {
        List<Profile> l = new ArrayList<>();
        try {
            JSONArray a = new JSONArray(prefs(c).getString("profiles", "[]"));
            for (int i = 0; i < a.length(); i++) l.add(Profile.fromJson(a.getJSONObject(i)));
        } catch (JSONException ignored) { }
        return l;
    }

    public static void saveCustomProfiles(Context c, List<Profile> l) {
        JSONArray a = new JSONArray();
        try { for (Profile p : l) a.put(p.toJson()); } catch (JSONException ignored) { }
        prefs(c).edit().putString("profiles", a.toString()).apply();
    }

    // ---- saved keys ----
    public static class SavedKey {
        public String name;
        public Profile profile;
        public int[] code;
        public boolean mirrorH, mirrorV;
    }

    public static List<SavedKey> keys(Context c) {
        List<SavedKey> l = new ArrayList<>();
        try {
            JSONArray a = new JSONArray(prefs(c).getString("keys", "[]"));
            for (int i = 0; i < a.length(); i++) {
                JSONObject o = a.getJSONObject(i);
                SavedKey k = new SavedKey();
                k.name = o.getString("name");
                k.profile = Profile.fromJson(o.getJSONObject("profile"));
                JSONArray ca = o.getJSONArray("code");
                k.code = new int[ca.length()];
                for (int j = 0; j < ca.length(); j++) k.code[j] = ca.getInt(j);
                k.mirrorH = o.optBoolean("mh"); k.mirrorV = o.optBoolean("mv");
                l.add(k);
            }
        } catch (JSONException ignored) { }
        return l;
    }

    public static void saveKeys(Context c, List<SavedKey> l) {
        JSONArray a = new JSONArray();
        try {
            for (SavedKey k : l) {
                JSONObject o = new JSONObject();
                o.put("name", k.name);
                o.put("profile", k.profile.toJson());
                JSONArray ca = new JSONArray();
                for (int v : k.code) ca.put(v);
                o.put("code", ca);
                o.put("mh", k.mirrorH); o.put("mv", k.mirrorV);
                a.put(o);
            }
        } catch (JSONException ignored) { }
        prefs(c).edit().putString("keys", a.toString()).apply();
    }

    public static String codeString(Profile p, int[] code) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < code.length; i++) {
            if (i > 0) sb.append(i == p.pins ? "  |  " : " ");
            sb.append(p.label(code[i]));
        }
        return sb.toString();
    }
}
