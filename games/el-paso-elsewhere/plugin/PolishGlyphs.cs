// Polish letters for static TextMeshPro atlases, composed at runtime.
//
// Ported from Laika (Mono, same TMP) to IL2CPP. The game's SDF atlases (Saira, OfficeCodePro,
// LiberationSans, Consolas) are static and lack Polish letters. A dynamic font draws them
// itself; a static one gets a dynamic fallback from the TTF of the same face if the game has it
// (LiberationSans); otherwise we build a small fallback atlas: the base letter is copied from
// the same font's atlas (same face and weight) and the diacritic (acute, dot, ogonek, stroke)
// is drawn as a distance field. The fallback goes first in fallbackFontAssetTable. Nothing
// ships; everything is made from the player's game files.

using System;
using System.Collections.Generic;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using TMPro;
using UnityEngine;
using UnityEngine.TextCore;
using UnityEngine.TextCore.LowLevel;
using Object = UnityEngine.Object;

namespace notgeese.ElPaso
{
    internal static class PolishGlyphs
    {
        private enum Mark { Acute, Dot, Ogonek, Stroke, Low, Copy }

        private struct Recipe
        {
            public char Letter;
            public string Bases; // first base letter the font has
            public Mark Mark;
            public Recipe(char letter, string bases, Mark mark) { Letter = letter; Bases = bases; Mark = mark; }
        }

        private static readonly Recipe[] Recipes =
        {
            new Recipe('ą', "a", Mark.Ogonek), new Recipe('ć', "c", Mark.Acute), new Recipe('ę', "e", Mark.Ogonek),
            new Recipe('ł', "l", Mark.Stroke), new Recipe('ń', "n", Mark.Acute), new Recipe('ó', "o", Mark.Acute),
            new Recipe('ś', "s", Mark.Acute), new Recipe('ź', "z", Mark.Acute), new Recipe('ż', "z", Mark.Dot),
            new Recipe('Ą', "A", Mark.Ogonek), new Recipe('Ć', "C", Mark.Acute), new Recipe('Ę', "E", Mark.Ogonek),
            new Recipe('Ł', "L", Mark.Stroke), new Recipe('Ń', "N", Mark.Acute), new Recipe('Ó', "O", Mark.Acute),
            new Recipe('Ś', "S", Mark.Acute), new Recipe('Ź', "Z", Mark.Acute), new Recipe('Ż', "Z", Mark.Dot),
            // Polish quotes: closing = the font's straight quote, opening = same shape on the baseline.
            new Recipe('”', "\"", Mark.Copy), new Recipe('„', "”\"", Mark.Low),
        };

        private static readonly HashSet<int> Done = new HashSet<int>();

        /// Complete every loaded TMP font. Returns the number of fonts completed.
        internal static int PatchLoadedFonts()
        {
            var patched = 0;
            foreach (var font in Resources.FindObjectsOfTypeAll<TMP_FontAsset>())
            {
                if (font == null || Done.Contains(font.GetInstanceID())) continue;
                try
                {
                    if (Patch(font, out var final)) patched++;
                    if (final) Done.Add(font.GetInstanceID());
                }
                catch (Exception error)
                {
                    Done.Add(font.GetInstanceID());
                    Plugin.Logger.LogWarning("TMP font \"" + font.name + "\": could not add Polish letters: " + error);
                }
            }
            return patched;
        }

        /// final = no point retrying (done, or the font has nothing to compose from).
        private static bool Patch(TMP_FontAsset font, out bool final)
        {
            final = true;
            if (font.name.StartsWith("notgeese", StringComparison.Ordinal)) return false;
            var atlases = font.atlasTextures;
            if (font.material == null || atlases == null || atlases.Length == 0 || atlases[0] == null)
            {
                final = false; // font still loading
                return false;
            }
            if (font.characterLookupTable == null) { final = false; return false; }
            var own = OwnCharacters(font);

            if (font.atlasPopulationMode == AtlasPopulationMode.Dynamic && font.sourceFontFile != null)
            {
                font.TryAddCharacters(Wanted(own), false);
                own = OwnCharacters(font);
                if (Wanted(own).Length == 0)
                {
                    Plugin.Logger.LogInfo("TMP font \"" + font.name + "\": draws Polish letters itself (dynamic).");
                    return false;
                }
                var bases = "IlLE";
                foreach (var recipe in Recipes)
                    if (!own.ContainsKey(recipe.Letter) && recipe.Mark != Mark.Copy && recipe.Mark != Mark.Low)
                        bases += recipe.Bases;
                font.TryAddCharacters(bases, false);
                own = OwnCharacters(font);
            }

            if (Wanted(own).Length == 0)
            {
                Plugin.Logger.LogInfo("TMP font \"" + font.name + "\": has Polish letters.");
                return false;
            }
            if (RealFallback(font, own)) return true;

            var wanted = new List<KeyValuePair<Recipe, Glyph>>();
            foreach (var recipe in Recipes)
            {
                if (own.ContainsKey(recipe.Letter)) continue;
                var glyph = BaseGlyph(recipe, own, wanted);
                if (glyph != null) wanted.Add(new KeyValuePair<Recipe, Glyph>(recipe, glyph));
            }
            if (wanted.Count == 0) return false;

            var padding = Mathf.Max(1, font.atlasPadding);
            var gradient = font.material.HasProperty("_GradientScale") ? font.material.GetFloat("_GradientScale") : padding + 1f;
            var alphas = new Dictionary<int, byte[]>();

            var stroke = MeasureStroke(font, own, alphas);
            var cells = new List<Cell>();
            foreach (var pair in wanted)
                cells.Add(Compose(pair.Key, pair.Value, Alpha(font, pair.Value.atlasIndex, alphas),
                    font.atlasTextures[pair.Value.atlasIndex], padding, gradient, stroke, font.faceInfo.ascentLine));

            var fallback = Build(font, cells, padding);
            if (font.fallbackFontAssetTable == null) font.fallbackFontAssetTable = new Il2CppSystem.Collections.Generic.List<TMP_FontAsset>();
            font.fallbackFontAssetTable.Insert(0, fallback);

            var letters = "";
            foreach (var pair in wanted) letters += pair.Key.Letter;
            Plugin.Logger.LogInfo(string.Format("TMP font \"{0}\": composed {1} ({2} px stroke, atlas {3}x{4}).",
                font.name, letters, stroke.ToString("0.0"), fallback.atlasTexture.width, fallback.atlasTexture.height));
            return true;
        }

        private static string Wanted(Dictionary<uint, TMP_Character> own)
        {
            var letters = "";
            foreach (var recipe in Recipes)
                if (!own.ContainsKey(recipe.Letter)) letters += recipe.Letter;
            return letters;
        }

        /// TTF of the same face, if the game already loaded it (Resources.LoadAll could load whole scenes).
        private static Font SourceFont(TMP_FontAsset font)
        {
            var wanted = new[] { Simple(font.faceInfo.familyName + font.faceInfo.styleName), Simple(font.faceInfo.familyName) };
            if (wanted[1].Length == 0) return null;
            var candidates = Resources.FindObjectsOfTypeAll<Font>();
            foreach (var name in wanted)
                foreach (var candidate in candidates)
                    if (candidate != null && Simple(candidate.name) == name) return candidate;
            return null;
        }

        private static string Simple(string name)
        {
            var simple = new System.Text.StringBuilder();
            foreach (var c in name ?? "")
                if (char.IsLetterOrDigit(c)) simple.Append(char.ToLowerInvariant(c));
            return simple.ToString();
        }

        /// Dynamic fallback from the face file: real letters instead of composed ones.
        private static bool RealFallback(TMP_FontAsset font, Dictionary<uint, TMP_Character> own)
        {
            var source = SourceFont(font);
            if (source == null) return false;
            var needed = Wanted(own);
            var fallback = TMP_FontAsset.CreateFontAsset(source, Mathf.Max(8, Mathf.RoundToInt(font.faceInfo.pointSize)),
                Mathf.Max(1, font.atlasPadding), font.atlasRenderMode, 512, 512, AtlasPopulationMode.Dynamic, true);
            if (fallback == null) return false;
            fallback.TryAddCharacters(needed, false);
            var added = OwnCharacters(fallback);
            var absent = "";
            foreach (var c in needed) if (!added.ContainsKey(c)) absent += c;
            if (absent.Length >= needed.Length)
            {
                Object.Destroy(fallback);
                return false;
            }
            fallback.name = "notgeese PL " + font.name + " (" + source.name + ")";
            Object.DontDestroyOnLoad(fallback);
            if (font.fallbackFontAssetTable == null) font.fallbackFontAssetTable = new Il2CppSystem.Collections.Generic.List<TMP_FontAsset>();
            font.fallbackFontAssetTable.Insert(0, fallback);
            Plugin.Logger.LogInfo(string.Format("TMP font \"{0}\": letters {1} from face file \"{2}\"{3}.", font.name, needed, source.name,
                absent.Length == 0 ? "" : ", missing " + absent));
            return true;
        }

        /// Only the font's own characters: the lookup also holds characters found in fallbacks.
        private static Dictionary<uint, TMP_Character> OwnCharacters(TMP_FontAsset font)
        {
            var own = new Dictionary<uint, TMP_Character>();
            var table = font.characterTable;
            for (var i = 0; table != null && i < table.Count; i++)
            {
                var character = table[i];
                if (character != null && character.glyph != null && !own.ContainsKey(character.unicode))
                    own[character.unicode] = character;
            }
            return own;
        }

        private static Glyph BaseGlyph(Recipe recipe, Dictionary<uint, TMP_Character> own, List<KeyValuePair<Recipe, Glyph>> wanted)
        {
            foreach (var b in recipe.Bases)
            {
                if (own.TryGetValue(b, out var character) && character.glyph.glyphRect.width > 0) return character.glyph;
                foreach (var pair in wanted)
                    if (pair.Key.Letter == b && pair.Key.Mark == Mark.Copy) return pair.Value;
            }
            return null;
        }

        // ---------- atlas ----------

        private static byte[] Alpha(TMP_FontAsset font, int index, Dictionary<int, byte[]> cache)
        {
            if (!cache.TryGetValue(index, out var alpha))
            {
                alpha = ReadAlpha(font.atlasTextures[index]);
                cache[index] = alpha;
            }
            return alpha;
        }

        /// Atlases aren't readable from the CPU; go through the GPU.
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
                var pixels = copy.GetPixels32(); // rows from the bottom, like GlyphRect
                Object.Destroy(copy);
                var alpha = new byte[pixels.Length];
                for (var i = 0; i < alpha.Length; i++) alpha[i] = pixels[i].a;
                return alpha;
            }
            finally
            {
                RenderTexture.active = previous;
                RenderTexture.ReleaseTemporary(target);
            }
        }

        /// Stroke width: longest horizontal run at half height of "I" or "l".
        private static float MeasureStroke(TMP_FontAsset font, Dictionary<uint, TMP_Character> own, Dictionary<int, byte[]> alphas)
        {
            foreach (var probe in new[] { 'I', 'l', 'i', 'L', 'E' })
            {
                if (!own.TryGetValue(probe, out var character)) continue;
                var rect = character.glyph.glyphRect;
                var texture = font.atlasTextures[character.glyph.atlasIndex];
                var alpha = Alpha(font, character.glyph.atlasIndex, alphas);
                var row = rect.y + rect.height / 2;
                if (row < 0 || row >= texture.height) continue;
                int best = 0, run = 0;
                for (var x = rect.x; x < rect.x + rect.width && x < texture.width; x++)
                {
                    run = alpha[row * texture.width + x] >= 128 ? run + 1 : 0;
                    best = Math.Max(best, run);
                }
                if (best > 0) return Mathf.Clamp(best, rect.height * 0.08f, rect.height * 0.3f);
            }
            return own.TryGetValue('E', out var e) ? e.glyph.glyphRect.height * 0.15f : 4f;
        }

        // ---------- composing a letter ----------

        private sealed class Cell
        {
            public uint Id;
            public int Width, Height;
            public byte[] Alpha;
            public float BoxWidth, BoxHeight;
            public GlyphMetrics Metrics;
            public float Scale;
        }

        private struct Capsule
        {
            public Vector2 A, B;
            public float Radius;
            public bool Square;
            public Capsule(Vector2 a, Vector2 b, float radius, bool square = false) { A = a; B = b; Radius = radius; Square = square; }
        }

        private static Cell Compose(Recipe recipe, Glyph glyph, byte[] source, Texture2D atlas, int padding, float gradient,
            float stroke, float ascent)
        {
            var rect = glyph.glyphRect;
            float w = rect.width, h = rect.height;
            var m = glyph.metrics;
            var kx = w > 0 ? m.width / w : 1f;
            var ky = h > 0 ? m.height / h : 1f;
            int atlasWidth = atlas.width, atlasHeight = atlas.height;

            // Mark no thicker than a fifth of the letter; room above up to the ascent line,
            // compressed when short but never thinner than 1.3 strokes.
            var t = Mathf.Min(stroke, h * 0.2f);
            var room = Mathf.Max((ascent - m.horizontalBearingY) / ky, t * 1.3f);
            var gap = Mathf.Min(t * 0.6f, room * 0.2f);
            var shapes = new List<Capsule>();
            switch (recipe.Mark)
            {
                case Mark.Acute:
                    {
                        var cx = w * 0.5f;
                        var r = Mathf.Min(t * 0.42f, (room - gap) * 0.3f);
                        var rise = Mathf.Clamp(room - gap - 2f * r, t * 0.2f, t);
                        shapes.Add(new Capsule(new Vector2(cx - t * 0.35f, h + gap + r),
                            new Vector2(cx + t * 0.75f, h + gap + r + rise), r));
                        break;
                    }
                case Mark.Dot:
                    {
                        var r = Mathf.Min(t * 0.5f, (room - gap) * 0.5f);
                        var c = new Vector2(w * 0.5f, h + gap + r);
                        shapes.Add(new Capsule(c, c, r, true));
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

            var bearingY = m.horizontalBearingY + (maxY - h) * ky;
            if (recipe.Mark == Mark.Low) bearingY = m.height * 0.15f;

            var cell = new Cell { Id = recipe.Letter, BoxWidth = maxX - minX, BoxHeight = maxY - minY, Scale = glyph.scale };
            cell.Metrics = new GlyphMetrics(cell.BoxWidth * kx, cell.BoxHeight * ky,
                m.horizontalBearingX + minX * kx, bearingY,
                Mathf.Max(m.horizontalAdvance, m.horizontalBearingX + maxX * kx));
            cell.Width = (int)cell.BoxWidth + padding * 2;
            cell.Height = (int)cell.BoxHeight + padding * 2;
            cell.Alpha = new byte[cell.Width * cell.Height];

            for (var cy = 0; cy < cell.Height; cy++)
            {
                for (var cx = 0; cx < cell.Width; cx++)
                {
                    var bu = cx - padding + (int)minX;
                    var bv = cy - padding + (int)minY;
                    var baseAlpha = 0;
                    var sx = rect.x + bu;
                    var sy = rect.y + bv;
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
                var dx = Mathf.Abs(p.x - s.A.x) - s.Radius;
                var dy = Mathf.Abs(p.y - s.A.y) - s.Radius;
                var outside = Mathf.Sqrt(Mathf.Max(dx, 0) * Mathf.Max(dx, 0) + Mathf.Max(dy, 0) * Mathf.Max(dy, 0));
                return outside + Mathf.Min(Mathf.Max(dx, dy), 0);
            }
            float abx = s.B.x - s.A.x, aby = s.B.y - s.A.y;
            var len = abx * abx + aby * aby;
            var along = len < 1e-6f ? 0f : Mathf.Clamp01(((p.x - s.A.x) * abx + (p.y - s.A.y) * aby) / len);
            float qx = p.x - (s.A.x + abx * along), qy = p.y - (s.A.y + aby * along);
            return Mathf.Sqrt(qx * qx + qy * qy) - s.Radius;
        }

        // ---------- fallback font ----------

        private static TMP_FontAsset Build(TMP_FontAsset font, List<Cell> cells, int padding)
        {
            var size = 64;
            List<Vector2Int> places;
            while (!TryPack(cells, size, out places)) size *= 2;

            var alpha = new byte[size * size];
            var fallback = ScriptableObject.CreateInstance<TMP_FontAsset>();
            fallback.name = "notgeese PL " + font.name;
            var glyphs = new Il2CppSystem.Collections.Generic.List<Glyph>();
            var characters = new Il2CppSystem.Collections.Generic.List<TMP_Character>();
            for (var i = 0; i < cells.Count; i++)
            {
                var cell = cells[i];
                var place = places[i]; // cell bottom-left, from the atlas bottom
                for (var y = 0; y < cell.Height; y++)
                    Array.Copy(cell.Alpha, y * cell.Width, alpha, (place.y + y) * size + place.x, cell.Width);
                var rect = new GlyphRect(place.x + padding, place.y + padding, (int)cell.BoxWidth, (int)cell.BoxHeight);
                var glyph = new Glyph(cell.Id, cell.Metrics, rect, cell.Scale, 0);
                glyphs.Add(glyph);
                characters.Add(new TMP_Character(cell.Id, glyph));
            }

            var atlas = new Texture2D(size, size, TextureFormat.Alpha8, false, true);
            atlas.name = "notgeese PL atlas";
            atlas.filterMode = FilterMode.Bilinear;
            atlas.wrapMode = TextureWrapMode.Clamp;
            atlas.LoadRawTextureData(new Il2CppStructArray<byte>(alpha));
            atlas.Apply(false, false);

            var material = new Material(font.material);
            material.name = fallback.name + " Material";
            material.SetTexture("_MainTex", atlas);
            material.SetFloat("_TextureWidth", size);
            material.SetFloat("_TextureHeight", size);

            // Serialized fields with internal setters; exposed as properties by the interop.
            fallback.m_Version = "1.1.0";
            fallback.m_AtlasWidth = size;
            fallback.m_AtlasHeight = size;
            fallback.m_AtlasPadding = padding;
            fallback.m_AtlasRenderMode = font.atlasRenderMode;
            fallback.faceInfo = font.faceInfo;
            fallback.atlasPopulationMode = AtlasPopulationMode.Static;
            fallback.m_GlyphTable = glyphs;
            fallback.m_CharacterTable = characters;
            fallback.atlasTextures = new Il2CppReferenceArray<Texture2D>(new[] { atlas });
            fallback.material = material;
            fallback.ReadFontAssetDefinition();

            Object.DontDestroyOnLoad(atlas);
            Object.DontDestroyOnLoad(material);
            Object.DontDestroyOnLoad(fallback);
            return fallback;
        }

        private static bool TryPack(List<Cell> cells, int size, out List<Vector2Int> places)
        {
            places = new List<Vector2Int>();
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
                places.Add(new Vector2Int(x, y));
                x += cell.Width + 1;
                shelf = Math.Max(shelf, cell.Height + 1);
            }
            return true;
        }
    }
}
