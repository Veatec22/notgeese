// Polish letters for Broforce bitmap fonts, composed at runtime.
//
// Menus, cutscenes and big titles use bitmap fonts: atlas + character table.
// They lack ąćęńśźż; some have É, Ł and standalone accents ˛ ˙. Each missing
// letter is composed from the base letter and an accent of the same font (acute from É
// over E, dot from ˙, ogonek from ˛); when the font has no accent we draw one in the
// font's stroke width, with outline if the font has one. The letter goes into free
// atlas space and into the character table. No font or atlas ships in the package.
//
// Dynamic fonts (TTF) stay unchanged: Unity takes missing letters from a
// system font.

using System;
using System.Collections.Generic;
using UnityEngine;

namespace notgeese.Broforce
{
    internal static class PolishGlyphs
    {
        private enum Mark { Acute, Dot, Ogonek, Stroke }

        private struct Recipe
        {
            public char Letter, Base;
            public Mark Mark;
            public Recipe(char letter, char baseChar, Mark mark) { Letter = letter; Base = baseChar; Mark = mark; }
        }

        private static readonly Recipe[] Recipes =
        {
            new Recipe('Ą', 'A', Mark.Ogonek), new Recipe('Ć', 'C', Mark.Acute), new Recipe('Ę', 'E', Mark.Ogonek),
            new Recipe('Ł', 'L', Mark.Stroke), new Recipe('Ń', 'N', Mark.Acute), new Recipe('Ó', 'O', Mark.Acute),
            new Recipe('Ś', 'S', Mark.Acute), new Recipe('Ź', 'Z', Mark.Acute), new Recipe('Ż', 'Z', Mark.Dot),
            new Recipe('ą', 'a', Mark.Ogonek), new Recipe('ć', 'c', Mark.Acute), new Recipe('ę', 'e', Mark.Ogonek),
            new Recipe('ł', 'l', Mark.Stroke), new Recipe('ń', 'n', Mark.Acute), new Recipe('ó', 'o', Mark.Acute),
            new Recipe('ś', 's', Mark.Acute), new Recipe('ź', 'z', Mark.Acute), new Recipe('ż', 'z', Mark.Dot),
        };

        private static readonly HashSet<int> Done = new HashSet<int>();
        private static int lastFrame = -1;

        /// Complete every loaded bitmap font. Cheap to call repeatedly: once per frame.
        internal static void PatchLoadedFonts()
        {
            if (Time.frameCount == lastFrame) return;
            lastFrame = Time.frameCount;

            foreach (var font in Resources.FindObjectsOfTypeAll<Font>())
            {
                if (font == null || font.dynamic || !Done.Add(font.GetInstanceID())) continue;
                try
                {
                    Patch(font);
                }
                catch (Exception error)
                {
                    Plugin.Log.LogWarning("Font \"" + font.name + "\": could not compose Polish letters: " + error);
                }
            }
        }

        // ---------- glify ----------

        /// Glyph pixels in atlas texels, (0, 0) = font origin, y up.
        private sealed class Ink
        {
            public readonly Dictionary<long, Color32> Pixels = new Dictionary<long, Color32>();
            public int MinX = int.MaxValue, MaxX = int.MinValue, MinY = int.MaxValue, MaxY = int.MinValue;

            public bool Empty { get { return Pixels.Count == 0; } }

            public void Set(int x, int y, Color32 color)
            {
                Color32 old;
                var key = Key(x, y);
                if (Pixels.TryGetValue(key, out old) && old.a >= color.a) return;
                Pixels[key] = color;
                if (x < MinX) MinX = x;
                if (x > MaxX) MaxX = x;
                if (y < MinY) MinY = y;
                if (y > MaxY) MaxY = y;
            }

            /// Overwrites a pixel regardless of alpha (glyph interior over the outline).
            public void Put(int x, int y, Color32 color)
            {
                Pixels[Key(x, y)] = color;
                if (x < MinX) MinX = x;
                if (x > MaxX) MaxX = x;
                if (y < MinY) MinY = y;
                if (y > MaxY) MaxY = y;
            }

            public void Add(Ink other, int dx, int dy)
            {
                foreach (var pair in other.Pixels)
                {
                    int x, y;
                    Split(pair.Key, out x, out y);
                    Set(x + dx, y + dy, pair.Value);
                }
            }

            public Ink Above(int level)
            {
                var result = new Ink();
                foreach (var pair in Pixels)
                {
                    int x, y;
                    Split(pair.Key, out x, out y);
                    if (y > level) result.Set(x, y, pair.Value);
                }
                return result;
            }

            public bool TryGet(int x, int y, out Color32 color) { return Pixels.TryGetValue(Key(x, y), out color); }

            private static long Key(int x, int y) { return ((long)(x + 100000) << 32) | (uint)(y + 100000); }

            internal static void Split(long key, out int x, out int y)
            {
                x = (int)(key >> 32) - 100000;
                y = (int)(key & 0xffffffff) - 100000;
            }
        }

        private sealed class Atlas
        {
            public int Width, Height;
            public Color32[] Pixels;
        }

        private sealed class FontData
        {
            public Font Font;
            public Atlas Atlas;
            public Dictionary<int, CharacterInfo> Chars;
            public float ScaleX, ScaleY;   // atlas texels per font unit
            public float OffsetX, OffsetY; // texel grid origin in font units
            public float HeightScale = 1f; // how many times the atlas height grew (old uv.y is multiplied by this)
        }

        /// Font stroke look measured on "I": width, outline and colors.
        private struct Pen
        {
            public int Width;   // full stroke width including outline, in texels
            public int Border;  // outline width (0 = font without outline)
            public Color32 Fill, Edge;
        }

#pragma warning disable 618 // uv, vert and flipped are the only exact description of bitmap font characters
        private static Ink Extract(FontData f, char c)
        {
            CharacterInfo info;
            if (!f.Chars.TryGetValue(c, out info)) return null;
            var v = info.vert;
            var uv = info.uv;
            float x0 = v.x, x1 = v.x + v.width, yb = v.y + v.height, yt = v.y;
            if (Mathf.Abs(x1 - x0) < 0.5f || Mathf.Abs(yt - yb) < 0.5f) return null;

            float left = Mathf.Min(x0, x1), right = Mathf.Max(x0, x1), bottom = Mathf.Min(yb, yt), top = Mathf.Max(yb, yt);
            var ink = new Ink();
            var atlas = f.Atlas;
            var iy0 = Mathf.FloorToInt((bottom - f.OffsetY) * f.ScaleY) - 1;
            var iy1 = Mathf.CeilToInt((top - f.OffsetY) * f.ScaleY) + 1;
            var ix0 = Mathf.FloorToInt((left - f.OffsetX) * f.ScaleX) - 1;
            var ix1 = Mathf.CeilToInt((right - f.OffsetX) * f.ScaleX) + 1;
            for (var iy = iy0; iy <= iy1; iy++)
            {
                for (var ix = ix0; ix <= ix1; ix++)
                {
                    var cx = f.OffsetX + (ix + 0.5f) / f.ScaleX;
                    var cy = f.OffsetY + (iy + 0.5f) / f.ScaleY;
                    if (cx < left || cx >= right || cy < bottom || cy >= top) continue;
                    // Glyph bottom-left = (uv.x, uv.y), top-right = (uv.xMax, uv.yMax);
                    // a flipped character lies transposed in the atlas.
                    var s = (cx - x0) / (x1 - x0);
                    var t = (cy - yb) / (yt - yb);
                    float u, w;
                    if (info.flipped)
                    {
                        u = uv.x + t * uv.width;
                        w = uv.y + s * uv.height;
                    }
                    else
                    {
                        u = uv.x + s * uv.width;
                        w = uv.y + t * uv.height;
                    }
                    var px = Mathf.Clamp((int)(u * atlas.Width), 0, atlas.Width - 1);
                    var py = Mathf.Clamp((int)(w * atlas.Height), 0, atlas.Height - 1);
                    var color = atlas.Pixels[py * atlas.Width + px];
                    if (color.a > 0) ink.Set(ix, iy, color);
                }
            }
            return ink.Empty ? null : ink;
        }

        // ---------- composing ----------

        private static void Patch(Font font)
        {
            var infos = font.characterInfo;
            if (infos == null || infos.Length == 0) return;

            var chars = new Dictionary<int, CharacterInfo>();
            foreach (var info in infos) chars[info.index] = info;
            if (!chars.ContainsKey('A') || !chars.ContainsKey('E')) return;

            // Some game fonts have non-ASCII entries copied from another atlas (HudsonOutline):
            // they point to random places and draw garbage. Recognizable by orientation reversed
            // vs letters A–Z; treated as absent.
            var stale = StaleEntries(chars);
            foreach (var index in stale) chars.Remove(index);

            var wanted = new List<Recipe>();
            foreach (var recipe in Recipes)
                if (!chars.ContainsKey(recipe.Letter) && chars.ContainsKey(recipe.Base)) wanted.Add(recipe);
            if (wanted.Count == 0) return;

            var texture = font.material != null ? font.material.mainTexture as Texture2D : null;
            if (texture == null) return;

            var probe = chars['E'];
            var f = new FontData
            {
                Font = font,
                Atlas = Read(texture),
                Chars = chars,
                ScaleX = Mathf.Abs((probe.flipped ? probe.uv.height * texture.height : probe.uv.width * texture.width) / probe.vert.width),
                ScaleY = Mathf.Abs((probe.flipped ? probe.uv.width * texture.width : probe.uv.height * texture.height) / probe.vert.height),
                OffsetX = probe.vert.x - Mathf.Floor(probe.vert.x),
                OffsetY = (probe.vert.y + probe.vert.height) - Mathf.Floor(probe.vert.y + probe.vert.height),
            };
            if (f.ScaleX < 0.25f || f.ScaleY < 0.25f || f.ScaleX > 8f || f.ScaleY > 8f) return;
            var pen = MeasurePen(f);

            var composed = new List<KeyValuePair<Recipe, Ink>>();
            foreach (var recipe in wanted)
            {
                var ink = Compose(f, recipe, pen);
                if (ink != null) composed.Add(new KeyValuePair<Recipe, Ink>(recipe, ink));
            }
            if (composed.Count == 0) return;

            var added = Place(f, texture, composed);
            if (added.Count == 0) return;

            var replaced = new HashSet<int>();
            foreach (var info in added) replaced.Add(info.index);
            var list = new List<CharacterInfo>();
            foreach (var info in infos)
            {
                if (replaced.Contains(info.index)) continue;
                var copy = info;
                if (f.HeightScale != 1f)
                {
#pragma warning disable 618
                    var uv = copy.uv;
                    copy.uv = new Rect(uv.x, uv.y * f.HeightScale, uv.width, uv.height * f.HeightScale);
#pragma warning restore 618
                }
                list.Add(copy);
            }
            list.AddRange(added);
            font.characterInfo = list.ToArray();
            Refresh(font);

            var letters = "";
            foreach (var info in added) letters += (char)info.index;
            Plugin.Log.LogInfo(string.Format(
                "Font \"{0}\": composed {1} (atlas {2}×{3}, scale {4:0.00}×{5:0.00}, stroke {6}, outline {7}, broken entries skipped: {8}).",
                font.name, letters, texture.width, texture.height, f.ScaleX, f.ScaleY, pen.Width, pen.Border, stale.Count));
        }

        private static List<int> StaleEntries(Dictionary<int, CharacterInfo> chars)
        {
            int up = 0, down = 0;
            for (var c = 'A'; c <= 'Z'; c++)
            {
                CharacterInfo info;
                if (!chars.TryGetValue(c, out info) || info.flipped) continue;
                if (info.uv.height > 0) up++;
                else if (info.uv.height < 0) down++;
            }
            var stale = new List<int>();
            if (up == 0 || down == 0)
            {
                var sign = up > 0 ? 1 : -1;
                foreach (var pair in chars)
                {
                    if (pair.Key < 0x80 || pair.Value.flipped || pair.Value.uv.height == 0) continue;
                    if (System.Math.Sign(pair.Value.uv.height) != sign) stale.Add(pair.Key);
                }
            }
            return stale;
        }

        private static Pen MeasurePen(FontData f)
        {
            foreach (var probe in new[] { 'I', 'l', 'L', 'E' })
            {
                var ink = Extract(f, probe);
                if (ink == null) continue;
                var row = (ink.MinY + ink.MaxY) / 2;
                // Longest run at half height = the letter's stem.
                int best = 0, bestStart = 0, run = 0;
                for (var x = ink.MinX; x <= ink.MaxX + 1; x++)
                {
                    Color32 dummy;
                    if (x <= ink.MaxX && ink.TryGet(x, row, out dummy)) run++;
                    else
                    {
                        if (run > best) { best = run; bestStart = x - run; }
                        run = 0;
                    }
                }
                if (best == 0) continue;

                Color32 edge, fill;
                ink.TryGet(bestStart, row, out edge);
                ink.TryGet(bestStart + best / 2, row, out fill);
                var border = 0;
                if (!Similar(edge, fill))
                {
                    Color32 c;
                    while (border < best / 2 && ink.TryGet(bestStart + border, row, out c) && Similar(c, edge)) border++;
                }
                edge.a = 255;
                fill.a = 255;
                return new Pen { Width = System.Math.Max(1, best), Border = border, Fill = fill, Edge = edge };
            }
            var white = new Color32(255, 255, 255, 255);
            return new Pen { Width = 2, Border = 0, Fill = white, Edge = white };
        }

        private static bool Similar(Color32 a, Color32 b)
        {
            return System.Math.Abs(a.r - b.r) + System.Math.Abs(a.g - b.g) + System.Math.Abs(a.b - b.b) < 90;
        }

        /// Accent = pixels of the accented char above the base letter's top edge (É − E).
        private static bool AccentFrom(FontData f, char accented, char plain, out Ink accent, out Ink reference)
        {
            accent = null;
            reference = Extract(f, plain);
            var full = Extract(f, accented);
            if (reference == null || full == null) return false;
            accent = full.Above(reference.MaxY);
            return accent.Pixels.Count >= 3;
        }

        private static Ink Compose(FontData f, Recipe recipe, Pen pen)
        {
            var baseInk = Extract(f, recipe.Base);
            if (baseInk == null) return null;
            var upper = char.IsUpper(recipe.Letter);
            var result = new Ink();
            result.Add(baseInk, 0, 0);
            var t = pen.Width;
            var gap = System.Math.Max(1, Mathf.RoundToInt(t * 0.2f));
            var center2 = baseInk.MinX + baseInk.MaxX; // doubled center, no rounding

            switch (recipe.Mark)
            {
                case Mark.Acute:
                case Mark.Dot:
                {
                    Ink accent, reference;
                    var found = upper
                        ? AccentFrom(f, 'É', 'E', out accent, out reference) || AccentFrom(f, 'Á', 'A', out accent, out reference) || AccentFrom(f, 'Ó', 'O', out accent, out reference)
                        : AccentFrom(f, 'é', 'e', out accent, out reference) || AccentFrom(f, 'á', 'a', out accent, out reference) || AccentFrom(f, 'ó', 'o', out accent, out reference);

                    // Accent position: horizontally as over the reference letter, vertically vs the base top.
                    var dx = found ? (center2 - (reference.MinX + reference.MaxX)) / 2 : 0;
                    var dy = found ? baseInk.MaxY - reference.MaxY : 0;
                    float bottom, middle;
                    if (found)
                    {
                        bottom = accent.MinY + dy;
                        middle = (accent.MinX + accent.MaxX) / 2f + dx;
                    }
                    else
                    {
                        bottom = baseInk.MaxY + 1 + gap;
                        middle = center2 / 2f + 0.5f;
                    }

                    if (recipe.Mark == Mark.Acute)
                    {
                        if (found) result.Add(accent, dx, dy);
                        else
                        {
                            var r = Radius(pen, 0.9f);
                            Draw(result, pen, r, false,
                                new Vector2(middle - t * 0.22f, bottom + r),
                                new Vector2(middle + t * 0.22f, bottom + r + t * 0.32f));
                        }
                    }
                    else
                    {
                        var dot = Extract(f, '˙');
                        if (dot != null)
                            result.Add(dot, Mathf.RoundToInt(middle - (dot.MinX + dot.MaxX) / 2f), Mathf.RoundToInt(bottom) - dot.MinY);
                        else
                        {
                            var r = Radius(pen, 1.3f);
                            var c = new Vector2(middle, bottom + r);
                            Draw(result, pen, r, true, c, c);
                        }
                    }
                    break;
                }
                case Mark.Ogonek:
                {
                    var ogonek = Extract(f, '˛');
                    if (ogonek != null)
                        // Ogonek's right edge under the letter's right edge, top row overlaps the letter.
                        result.Add(ogonek, baseInk.MaxX - ogonek.MaxX, baseInk.MinY - ogonek.MaxY + 1);
                    else
                    {
                        var r = Radius(pen, 1f);
                        var x = baseInk.MaxX + 1 - r;
                        var y = baseInk.MinY;
                        var a = new Vector2(x, y + r * 0.5f);
                        var b = new Vector2(x - t * 0.3f, y - t * 0.5f);
                        var c = new Vector2(x + t * 0.1f, y - t * 0.8f);
                        Draw(result, pen, r, false, a, b, c);
                    }
                    break;
                }
                case Mark.Stroke:
                {
                    // Slanted bar across the stem: "L" has the stem on the left, "l" in the middle.
                    var stem = upper ? baseInk.MinX + t * 0.5f : center2 / 2f + 0.5f;
                    var h = baseInk.MaxY - baseInk.MinY + 1;
                    var r = Radius(pen, 0.75f);
                    Draw(result, pen, r, false,
                        new Vector2(stem - t * 0.7f, baseInk.MinY + h * 0.38f),
                        new Vector2(stem + t * 0.9f, baseInk.MinY + h * 0.6f));
                    break;
                }
            }
            return result;
        }

        /// Radius of a drawn mark: font outline + a fraction of the stroke fill width.
        private static float Radius(Pen pen, float k)
        {
            return pen.Border + Mathf.Max(0.75f, (pen.Width - 2 * pen.Border) * 0.5f * k);
        }

        /// Draws a polyline of radius-r segments (or a square when square) in the font color,
        /// with a pen outline if the font has one.
        private static void Draw(Ink ink, Pen pen, float r, bool square, params Vector2[] points)
        {
            float minX = float.MaxValue, maxX = float.MinValue, minY = float.MaxValue, maxY = float.MinValue;
            foreach (var p in points)
            {
                minX = Mathf.Min(minX, p.x); maxX = Mathf.Max(maxX, p.x);
                minY = Mathf.Min(minY, p.y); maxY = Mathf.Max(maxY, p.y);
            }
            var inner = r - pen.Border;
            for (var y = Mathf.FloorToInt(minY - r) - 1; y <= Mathf.CeilToInt(maxY + r) + 1; y++)
            {
                for (var x = Mathf.FloorToInt(minX - r) - 1; x <= Mathf.CeilToInt(maxX + r) + 1; x++)
                {
                    var point = new Vector2(x + 0.5f, y + 0.5f);
                    var d = float.MaxValue;
                    if (square)
                        d = Mathf.Max(Mathf.Abs(point.x - points[0].x), Mathf.Abs(point.y - points[0].y));
                    else
                        for (var i = 0; i + 1 < points.Length; i++) d = Mathf.Min(d, Segment(point, points[i], points[i + 1]));
                    if (d > r) continue;
                    if (pen.Border > 0 && d > inner)
                    {
                        Color32 old;
                        // The outline never paints over the base letter's interior.
                        if (!ink.TryGet(x, y, out old)) ink.Put(x, y, pen.Edge);
                    }
                    else ink.Put(x, y, pen.Fill);
                }
            }
        }

        private static float Segment(Vector2 p, Vector2 a, Vector2 b)
        {
            var ab = b - a;
            var along = ab.sqrMagnitude < 1e-6f ? 0f : Mathf.Clamp01(Vector2.Dot(p - a, ab) / ab.sqrMagnitude);
            return (p - (a + ab * along)).magnitude;
        }

        // ---------- atlas ----------

        private static Atlas Read(Texture2D texture)
        {
            var target = RenderTexture.GetTemporary(texture.width, texture.height, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Linear);
            var previous = RenderTexture.active;
            try
            {
                Graphics.Blit(texture, target);
                RenderTexture.active = target;
                var copy = new Texture2D(texture.width, texture.height, TextureFormat.RGBA32, false, true);
                copy.ReadPixels(new Rect(0, 0, texture.width, texture.height), 0, 0);
                copy.Apply();
                var atlas = new Atlas { Width = texture.width, Height = texture.height, Pixels = copy.GetPixels32() };
                UnityEngine.Object.Destroy(copy);
                return atlas;
            }
            finally
            {
                RenderTexture.active = previous;
                RenderTexture.ReleaseTemporary(target);
            }
        }

        private struct Slot
        {
            public int X, Y, W, H;
        }

        /// Places composed letters in free atlas space and returns their character info.
        private static List<CharacterInfo> Place(FontData f, Texture2D texture, List<KeyValuePair<Recipe, Ink>> composed)
        {
            var atlas = f.Atlas;
            int w = atlas.Width, h = atlas.Height;

            // Taken: every drawn pixel with a margin and ASCII character rects (space also
            // points at a piece of the atlas). Empty non-ASCII cells are free to use.
            var used = new bool[w * h];
            for (var y = 0; y < h; y++)
                for (var x = 0; x < w; x++)
                    if (atlas.Pixels[y * w + x].a > 0) MarkUsed(used, w, h, x - 1, y - 1, x + 2, y + 2);
            foreach (var info in f.Chars.Values)
            {
                if (info.index >= 0x80) continue;
                var uv = info.uv;
                MarkUsed(used, w, h,
                    Mathf.FloorToInt(Mathf.Min(uv.xMin, uv.xMax) * w) - 1, Mathf.FloorToInt(Mathf.Min(uv.yMin, uv.yMax) * h) - 1,
                    Mathf.CeilToInt(Mathf.Max(uv.xMin, uv.xMax) * w) + 1, Mathf.CeilToInt(Mathf.Max(uv.yMin, uv.yMax) * h) + 1);
            }

            var added = new List<CharacterInfo>();
            var slots = new List<Slot>();
            foreach (var pair in composed)
            {
                var ink = pair.Value;
                var gw = ink.MaxX - ink.MinX + 1;
                var gh = ink.MaxY - ink.MinY + 1;
                int sx, sy;
                if (!FindFree(used, w, h, gw + 2, gh + 2, out sx, out sy) && f.HeightScale == 1f && !CanCopyInPlace(texture))
                {
                    // The texture will be new anyway: double the atlas height, the empty band goes on top.
                    var grown = new Color32[w * h * 2];
                    Array.Copy(atlas.Pixels, grown, atlas.Pixels.Length);
                    var grownUsed = new bool[w * h * 2];
                    Array.Copy(used, grownUsed, used.Length);
                    atlas.Pixels = grown;
                    used = grownUsed;
                    h *= 2;
                    atlas.Height = h;
                    f.HeightScale = 0.5f;
                    for (var i = 0; i < added.Count; i++)
                    {
                        var info0 = added[i];
                        var r0 = info0.uv;
                        info0.uv = new Rect(r0.x, r0.y * 0.5f, r0.width, r0.height * 0.5f);
                        added[i] = info0;
                    }
                }
                if (!FindFree(used, w, h, gw + 2, gh + 2, out sx, out sy))
                {
                    Plugin.Log.LogWarning("Font \"" + f.Font.name + "\": no atlas space for " + pair.Key.Letter + ".");
                    break;
                }
                MarkUsed(used, w, h, sx, sy, sx + gw + 2, sy + gh + 2);
                var ax = sx + 1;
                var ay = sy + 1;
                for (var y = 0; y < gh; y++)
                    for (var x = 0; x < gw; x++)
                        atlas.Pixels[(ay + y) * w + ax + x] = new Color32(0, 0, 0, 0);
                foreach (var p in ink.Pixels)
                {
                    int x, y;
                    Ink.Split(p.Key, out x, out y);
                    atlas.Pixels[(ay + y - ink.MinY) * w + ax + x - ink.MinX] = p.Value;
                }
                slots.Add(new Slot { X = ax, Y = ay, W = gw, H = gh });

                var info = f.Chars[pair.Key.Base];
                info.index = pair.Key.Letter;
                info.flipped = false;
                info.uv = new Rect(ax / (float)w, ay / (float)h, gw / (float)w, gh / (float)h);
                var left = f.OffsetX + ink.MinX / f.ScaleX;
                var bottom = f.OffsetY + ink.MinY / f.ScaleY;
                info.vert = new Rect(left, bottom + gh / f.ScaleY, gw / f.ScaleX, -gh / f.ScaleY);
                added.Add(info);
            }
            if (added.Count > 0)
            {
                var replacement = Upload(f.Font, texture, atlas, slots);
                if (replacement != null) Retarget(texture, replacement);
            }
            return added;
        }
#pragma warning restore 618

        private static void MarkUsed(bool[] used, int w, int h, int x0, int y0, int x1, int y1)
        {
            x0 = Mathf.Clamp(x0, 0, w); x1 = Mathf.Clamp(x1, 0, w);
            y0 = Mathf.Clamp(y0, 0, h); y1 = Mathf.Clamp(y1, 0, h);
            for (var y = y0; y < y1; y++)
                for (var x = x0; x < x1; x++) used[y * w + x] = true;
        }

        private static bool FindFree(bool[] used, int w, int h, int rw, int rh, out int fx, out int fy)
        {
            // Prefix-sum table: whether a rectangle is free is checked in constant time.
            var sum = new int[(w + 1) * (h + 1)];
            for (var y = 0; y < h; y++)
            {
                var row = 0;
                for (var x = 0; x < w; x++)
                {
                    row += used[y * w + x] ? 1 : 0;
                    sum[(y + 1) * (w + 1) + x + 1] = sum[y * (w + 1) + x + 1] + row;
                }
            }
            for (var y = 0; y + rh <= h; y++)
            {
                for (var x = 0; x + rw <= w; x++)
                {
                    var total = sum[(y + rh) * (w + 1) + x + rw] - sum[y * (w + 1) + x + rw] - sum[(y + rh) * (w + 1) + x] + sum[y * (w + 1) + x];
                    if (total == 0)
                    {
                        fx = x;
                        fy = y;
                        return true;
                    }
                }
            }
            fx = fy = 0;
            return false;
        }

        private static bool CanCopyInPlace(Texture2D texture)
        {
            var format = texture.format;
            var sameFormat = format == TextureFormat.RGBA32 || format == TextureFormat.ARGB32 || format == TextureFormat.Alpha8;
            return sameFormat && texture.mipmapCount == 1 && SystemInfo.copyTextureSupport != UnityEngine.Rendering.CopyTextureSupport.None;
        }

        /// Writes new letters into the font texture. Where possible into the same texture (CopyTexture)
        /// so material copies see them too; otherwise the font material gets a new texture.
        private static Texture2D Upload(Font font, Texture2D texture, Atlas atlas, List<Slot> slots)
        {
            var format = texture.format;
            if (CanCopyInPlace(texture) && atlas.Width == texture.width && atlas.Height == texture.height)
            {
                try
                {
                    var source = new Texture2D(atlas.Width, atlas.Height, format, false, true);
                    source.SetPixels32(atlas.Pixels);
                    source.Apply(false, false);
                    foreach (var s in slots)
                        Graphics.CopyTexture(source, 0, 0, s.X, s.Y, s.W, s.H, texture, 0, 0, s.X, s.Y);
                    UnityEngine.Object.Destroy(source);
                    return null;
                }
                catch (Exception error)
                {
                    Plugin.Log.LogInfo("Font \"" + font.name + "\": CopyTexture failed (" + error.Message + "), replacing the texture.");
                }
            }

            var copy = new Texture2D(atlas.Width, atlas.Height, TextureFormat.RGBA32, false, true)
            {
                name = texture.name + " (PL)",
                filterMode = texture.filterMode,
                wrapMode = texture.wrapMode,
                anisoLevel = texture.anisoLevel,
            };
            copy.SetPixels32(atlas.Pixels);
            copy.Apply(false, true);
            UnityEngine.Object.DontDestroyOnLoad(copy);
            font.material.mainTexture = copy;
            return copy;
        }

        /// Texts with their own copy of the font material need the new texture too.
        private static void Retarget(Texture2D old, Texture2D replacement)
        {
            foreach (var renderer in Resources.FindObjectsOfTypeAll<MeshRenderer>())
            {
                if (renderer == null) continue;
                foreach (var material in renderer.sharedMaterials)
                    if (material != null && material.mainTexture == old) material.mainTexture = replacement;
            }
        }

        /// Texts built before the letters were added must be redrawn.
        private static void Refresh(Font font)
        {
            foreach (var mesh in Resources.FindObjectsOfTypeAll<TextMesh>())
            {
                if (mesh == null || mesh.font != font) continue;
                var text = mesh.text;
                mesh.text = "";
                mesh.text = text;
            }
            foreach (var text in Resources.FindObjectsOfTypeAll<UnityEngine.UI.Text>())
                if (text != null && text.font == font) text.SetAllDirty();
        }
    }
}
