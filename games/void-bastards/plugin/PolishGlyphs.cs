// Polish letters for static TextMeshPro atlases, composed at runtime.
//
// The old TextMeshPro built into the game makes no glyphs on the fly, and the game's SDF atlases
// lack ąćęłńóśźż. For each font that lacks them we build a small fallback atlas: the base letter
// is copied from the same font's atlas (same face and weight) and the diacritic (acute, dot,
// ogonek, stroke) is drawn as a distance field. The fallback goes into the original's
// fallbackFontAssets. No font or atlas fragment ships in the package; everything is made from
// the player's game files.

using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;

namespace notgeese.VoidBastards
{
    internal static class PolishGlyphs
    {
        private enum Mark { Acute, Dot, Ogonek, Stroke, Low }

        private struct Recipe
        {
            public char Letter, Base;
            public Mark Mark;
            public Recipe(char letter, char baseChar, Mark mark) { Letter = letter; Base = baseChar; Mark = mark; }
        }

        private static readonly Recipe[] Recipes =
        {
            new Recipe('ą', 'a', Mark.Ogonek), new Recipe('ć', 'c', Mark.Acute), new Recipe('ę', 'e', Mark.Ogonek),
            new Recipe('ł', 'l', Mark.Stroke), new Recipe('ń', 'n', Mark.Acute), new Recipe('ó', 'o', Mark.Acute),
            new Recipe('ś', 's', Mark.Acute), new Recipe('ź', 'z', Mark.Acute), new Recipe('ż', 'z', Mark.Dot),
            new Recipe('Ą', 'A', Mark.Ogonek), new Recipe('Ć', 'C', Mark.Acute), new Recipe('Ę', 'E', Mark.Ogonek),
            new Recipe('Ł', 'L', Mark.Stroke), new Recipe('Ń', 'N', Mark.Acute), new Recipe('Ó', 'O', Mark.Acute),
            new Recipe('Ś', 'S', Mark.Acute), new Recipe('Ź', 'Z', Mark.Acute), new Recipe('Ż', 'Z', Mark.Dot),
            // Polish low quotes: the font's closing quote moved to the baseline.
            new Recipe('„', '”', Mark.Low), new Recipe('‚', '’', Mark.Low),
        };

        private static readonly HashSet<int> Done = new HashSet<int>();

        /// Complete all loaded TMP fonts. Safe to call repeatedly.
        internal static void PatchLoadedFonts()
        {
            foreach (var font in Resources.FindObjectsOfTypeAll<TMP_FontAsset>())
            {
                if (font == null || Done.Contains(font.GetInstanceID())) continue;
                Done.Add(font.GetInstanceID());
                try
                {
                    Patch(font);
                }
                catch (Exception error)
                {
                    Plugin.Log.LogWarning("Font \"" + font.name + "\": could not compose Polish letters: " + error.Message);
                }
            }
        }

        private static void Patch(TMP_FontAsset font)
        {
            if (font.name.StartsWith("notgeese", StringComparison.Ordinal) || font.atlas == null || font.fontInfo == null) return;

            var wanted = new List<Recipe>();
            foreach (var recipe in Recipes)
                if (!font.HasCharacter(recipe.Letter) && font.characterDictionary.ContainsKey(recipe.Base))
                    wanted.Add(recipe);
            if (wanted.Count == 0) return;

            var info = font.fontInfo;
            var padding = Mathf.Max(1, Mathf.RoundToInt(info.Padding));
            var gradient = font.material != null && font.material.HasProperty("_GradientScale")
                ? font.material.GetFloat("_GradientScale") : padding + 1f;
            var source = ReadAlpha(font.atlas);
            var atlasWidth = font.atlas.width;
            var atlasHeight = font.atlas.height;

            // Font stroke width: the longest horizontal "inside" run at half the height of "I" or "l".
            var stroke = MeasureStroke(font, source, atlasWidth, atlasHeight);

            var cells = new List<Cell>();
            foreach (var recipe in wanted)
                cells.Add(Compose(recipe, font.characterDictionary[recipe.Base], source, atlasWidth, atlasHeight, padding, gradient, stroke));

            var glyphs = Pack(cells, padding, out var atlas);
            var fallback = ScriptableObject.CreateInstance<TMP_FontAsset>();
            fallback.name = "notgeese PL " + font.name;
            fallback.hashCode = SimpleHash(fallback.name);
            fallback.fontAssetType = TMP_FontAsset.FontAssetTypes.SDF;
            var face = CopyFace(info);
            face.AtlasWidth = atlas.width;
            face.AtlasHeight = atlas.height;
            fallback.AddFaceInfo(face);
            fallback.atlas = atlas;
            fallback.AddGlyphInfo(glyphs.ToArray());
            fallback.AddKerningInfo(new KerningTable());
            var material = new Material(font.material);
            material.name = fallback.name + " Material";
            material.SetTexture("_MainTex", atlas);
            material.SetFloat("_TextureWidth", atlas.width);
            material.SetFloat("_TextureHeight", atlas.height);
            fallback.material = material;
            fallback.materialHashCode = SimpleHash(material.name);
            fallback.ReadFontDefinition();
            UnityEngine.Object.DontDestroyOnLoad(atlas);
            UnityEngine.Object.DontDestroyOnLoad(material);
            UnityEngine.Object.DontDestroyOnLoad(fallback);

            if (font.fallbackFontAssets == null) font.fallbackFontAssets = new List<TMP_FontAsset>();
            font.fallbackFontAssets.Insert(0, fallback);

            var letters = "";
            foreach (var recipe in wanted) letters += recipe.Letter;
            Plugin.Log.LogInfo(string.Format("TMP font \"{0}\": composed {1} ({2} px stroke, atlas {3}×{4}).",
                font.name, letters, stroke.ToString("0.0"), atlas.width, atlas.height));
        }

        // ---------- atlas ----------

        private static byte[] ReadAlpha(Texture2D texture)
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
                var pixels = copy.GetPixels32();
                UnityEngine.Object.Destroy(copy);
                var alpha = new byte[pixels.Length];
                for (var i = 0; i < pixels.Length; i++) alpha[i] = pixels[i].a;
                return alpha;
            }
            finally
            {
                RenderTexture.active = previous;
                RenderTexture.ReleaseTemporary(target);
            }
        }

        private static float MeasureStroke(TMP_FontAsset font, byte[] alpha, int width, int height)
        {
            foreach (var probe in new[] { 'I', 'l', 'i', 'L', 'E' })
            {
                TMP_Glyph glyph;
                if (!font.characterDictionary.TryGetValue(probe, out glyph)) continue;
                var x0 = Mathf.RoundToInt(glyph.x);
                var w = Mathf.RoundToInt(glyph.width);
                var row = height - Mathf.RoundToInt(glyph.y) - Mathf.RoundToInt(glyph.height * 0.5f);
                if (row < 0 || row >= height) continue;
                var best = 0;
                var run = 0;
                for (var x = x0; x < x0 + w && x < width; x++)
                {
                    run = alpha[row * width + x] >= 128 ? run + 1 : 0;
                    best = Math.Max(best, run);
                }
                if (best > 0) return Mathf.Clamp(best, glyph.height * 0.08f, glyph.height * 0.3f);
            }
            TMP_Glyph any;
            return font.characterDictionary.TryGetValue('E', out any) ? any.height * 0.15f : 4f;
        }

        // ---------- composing a letter ----------

        private sealed class Cell
        {
            public int Id, Width, Height;
            public byte[] Alpha;
            public float MinX, MinY, BoxWidth, BoxHeight, XOffset, YOffset, XAdvance, Scale;
        }

        private struct Capsule
        {
            public Vector2 A, B;
            public float Radius;
            public bool Square;
            public Capsule(Vector2 a, Vector2 b, float radius, bool square = false) { A = a; B = b; Radius = radius; Square = square; }
        }

        private static Cell Compose(Recipe recipe, TMP_Glyph glyph, byte[] source, int atlasWidth, int atlasHeight,
            int padding, float gradient, float t)
        {
            var w = glyph.width;
            var h = glyph.height;
            var shapes = new List<Capsule>();
            var gap = t * 0.6f;
            switch (recipe.Mark)
            {
                case Mark.Acute:
                    {
                        var cx = w * 0.5f;
                        shapes.Add(new Capsule(new Vector2(cx - t * 0.35f, h + gap + t * 0.35f),
                            new Vector2(cx + t * 0.75f, h + gap + t * 1.35f), t * 0.42f));
                        break;
                    }
                case Mark.Dot:
                    {
                        var c = new Vector2(w * 0.5f, h + gap + t * 0.5f);
                        shapes.Add(new Capsule(c, c, t * 0.5f, true));
                        break;
                    }
                case Mark.Ogonek:
                    {
                        var x = w - t * 0.55f;
                        shapes.Add(new Capsule(new Vector2(x, t * 0.3f), new Vector2(x - t * 0.45f, -t * 0.85f), t * 0.38f));
                        shapes.Add(new Capsule(new Vector2(x - t * 0.45f, -t * 0.85f), new Vector2(x + t * 0.35f, -t * 1.35f), t * 0.34f));
                        break;
                    }
                case Mark.Stroke:
                    {
                        // "L" has the stem on the left, "l" in the middle.
                        var stem = char.IsUpper(recipe.Letter) ? t * 0.5f : w * 0.5f;
                        shapes.Add(new Capsule(new Vector2(stem - t * 0.95f, h * 0.36f), new Vector2(stem + t * 1.25f, h * 0.62f), t * 0.4f));
                        break;
                    }
                case Mark.Low:
                    break;
            }

            float minX = 0, minY = 0, maxX = w, maxY = h;
            foreach (var s in shapes)
            {
                minX = Mathf.Min(minX, Mathf.Min(s.A.x, s.B.x) - s.Radius);
                minY = Mathf.Min(minY, Mathf.Min(s.A.y, s.B.y) - s.Radius);
                maxX = Mathf.Max(maxX, Mathf.Max(s.A.x, s.B.x) + s.Radius);
                maxY = Mathf.Max(maxY, Mathf.Max(s.A.y, s.B.y) + s.Radius);
            }
            minX = Mathf.Floor(minX);
            minY = Mathf.Floor(minY);
            maxX = Mathf.Ceil(maxX);
            maxY = Mathf.Ceil(maxY);

            var cell = new Cell
            {
                Id = recipe.Letter,
                BoxWidth = maxX - minX,
                BoxHeight = maxY - minY,
                MinX = minX,
                MinY = minY,
                XOffset = glyph.xOffset + minX,
                YOffset = glyph.yOffset + (maxY - h),
                XAdvance = Mathf.Max(glyph.xAdvance, glyph.xOffset + maxX),
                Scale = glyph.scale,
            };
            // Low quote: same shape, bottom just below the baseline.
            if (recipe.Mark == Mark.Low) cell.YOffset = h * 0.85f;
            cell.Width = (int)cell.BoxWidth + padding * 2;
            cell.Height = (int)cell.BoxHeight + padding * 2;
            cell.Alpha = new byte[cell.Width * cell.Height];

            var gx = Mathf.RoundToInt(glyph.x);
            var gyBottom = atlasHeight - Mathf.RoundToInt(glyph.y) - Mathf.RoundToInt(h);
            for (var cy = 0; cy < cell.Height; cy++)
            {
                for (var cx = 0; cx < cell.Width; cx++)
                {
                    // Coordinates in the base letter's frame (0,0 = bottom-left of its rect).
                    var bu = cx - padding + (int)minX;
                    var bv = cy - padding + (int)minY;
                    var baseAlpha = 0;
                    var sx = gx + bu;
                    var sy = gyBottom + bv;
                    if (bu >= -padding && bu < w + padding && bv >= -padding && bv < h + padding
                        && sx >= 0 && sx < atlasWidth && sy >= 0 && sy < atlasHeight)
                        baseAlpha = source[sy * atlasWidth + sx];

                    var point = new Vector2(bu + 0.5f, bv + 0.5f);
                    var distance = float.MaxValue;
                    foreach (var s in shapes) distance = Mathf.Min(distance, Distance(point, s));
                    var markAlpha = Mathf.Clamp01(0.5f - distance / (2f * gradient));
                    cell.Alpha[cy * cell.Width + cx] = (byte)Mathf.Max(baseAlpha, Mathf.RoundToInt(markAlpha * 255f));
                }
            }
            return cell;
        }

        private static float Distance(Vector2 p, Capsule s)
        {
            if (s.Square)
            {
                var d = new Vector2(Mathf.Abs(p.x - s.A.x) - s.Radius, Mathf.Abs(p.y - s.A.y) - s.Radius);
                var outside = new Vector2(Mathf.Max(d.x, 0), Mathf.Max(d.y, 0)).magnitude;
                return outside + Mathf.Min(Mathf.Max(d.x, d.y), 0);
            }
            var ab = s.B - s.A;
            var along = ab.sqrMagnitude < 1e-6f ? 0f : Mathf.Clamp01(Vector2.Dot(p - s.A, ab) / ab.sqrMagnitude);
            return (p - (s.A + ab * along)).magnitude - s.Radius;
        }

        // ---------- pakowanie ----------

        private static List<TMP_Glyph> Pack(List<Cell> cells, int padding, out Texture2D atlas)
        {
            var size = 64;
            List<Vector2> places;
            while (!TryPack(cells, size, out places)) size *= 2;

            var alpha = new byte[size * size];
            var glyphs = new List<TMP_Glyph>();
            for (var i = 0; i < cells.Count; i++)
            {
                var cell = cells[i];
                var px = (int)places[i].x;
                var py = (int)places[i].y; // bottom row of the cell, counted from the bottom
                for (var y = 0; y < cell.Height; y++)
                    Array.Copy(cell.Alpha, y * cell.Width, alpha, (py + y) * size + px, cell.Width);
                glyphs.Add(new TMP_Glyph
                {
                    id = cell.Id,
                    x = px + padding,
                    y = size - (py + padding + cell.BoxHeight), // TMP counts y from the atlas top
                    width = cell.BoxWidth,
                    height = cell.BoxHeight,
                    xOffset = cell.XOffset,
                    yOffset = cell.YOffset,
                    xAdvance = cell.XAdvance,
                    scale = cell.Scale,
                });
            }

            atlas = new Texture2D(size, size, TextureFormat.Alpha8, false, true);
            atlas.name = "notgeese PL atlas";
            atlas.filterMode = FilterMode.Bilinear;
            atlas.wrapMode = TextureWrapMode.Clamp;
            var pixels = new Color32[alpha.Length];
            for (var i = 0; i < alpha.Length; i++) pixels[i] = new Color32(255, 255, 255, alpha[i]);
            atlas.SetPixels32(pixels);
            atlas.Apply(false, false);
            return glyphs;
        }

        private static bool TryPack(List<Cell> cells, int size, out List<Vector2> places)
        {
            places = new List<Vector2>();
            int x = 0, y = 0, shelf = 0;
            foreach (var cell in cells)
            {
                if (cell.Width > size || cell.Height > size) return false;
                if (x + cell.Width > size)
                {
                    x = 0;
                    y += shelf;
                    shelf = 0;
                }
                if (y + cell.Height > size) return false;
                places.Add(new Vector2(x, y));
                x += cell.Width + 1;
                shelf = Math.Max(shelf, cell.Height + 1);
            }
            return true;
        }

        private static FaceInfo CopyFace(FaceInfo f)
        {
            return new FaceInfo
            {
                Name = f.Name, PointSize = f.PointSize, Scale = f.Scale, CharacterCount = f.CharacterCount,
                LineHeight = f.LineHeight, Baseline = f.Baseline, Ascender = f.Ascender, CapHeight = f.CapHeight,
                Descender = f.Descender, CenterLine = f.CenterLine, SuperscriptOffset = f.SuperscriptOffset,
                SubscriptOffset = f.SubscriptOffset, SubSize = f.SubSize, Underline = f.Underline,
                UnderlineThickness = f.UnderlineThickness, TabWidth = f.TabWidth, Padding = f.Padding,
                AtlasWidth = f.AtlasWidth, AtlasHeight = f.AtlasHeight,
            };
        }

        private static int SimpleHash(string text)
        {
            var hash = 0;
            foreach (var c in text) hash = ((hash << 5) + hash) ^ c;
            return hash;
        }
    }
}
