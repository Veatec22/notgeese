// Polish letters in Wild Bastards' TextMeshPro fonts.
//
// The game's SDF atlases are static and lack ąćęłńśźż, but Resources holds TTF files of the
// same faces (Southbank Spurs, Grindstone Display, Josefin Sans). For each atlas without
// Polish letters we create a dynamic TMP_FontAsset from the same family's TTF and put it first
// as fallback; missing glyphs are drawn on the fly in the same face. No font ships.

using System;
using System.Collections.Generic;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.TextCore.LowLevel;

namespace notgeese.WildBastards
{
    internal static class PolishFonts
    {
        private static readonly HashSet<int> Done = new HashSet<int>();
        private static Dictionary<string, Font> fonts;

        internal static void PatchLoadedFonts()
        {
            LoadFonts();
            foreach (var asset in Resources.FindObjectsOfTypeAll<TMP_FontAsset>())
            {
                if (asset == null || Done.Contains(asset.GetInstanceID())) continue;
                Done.Add(asset.GetInstanceID());
                try
                {
                    Patch(asset);
                }
                catch (Exception error)
                {
                    Plugin.Log.LogWarning("Font „" + asset.name + "”: " + error.Message);
                }
            }
        }

        private static void LoadFonts()
        {
            if (fonts != null) return;
            fonts = new Dictionary<string, Font>();
            // File names first, then family names, only for free keys: SouthbankSpurs-Italic
            // also declares the family "Southbank Spurs" and used to overwrite the upright one.
            var all = new List<Font>(Resources.LoadAll<Font>("Fonts"));
            all.AddRange(Resources.FindObjectsOfTypeAll<Font>());
            foreach (var font in all)
                if (font != null && !fonts.ContainsKey(Key(font.name))) fonts[Key(font.name)] = font;
            foreach (var font in all) Remember(font);
            Plugin.Log.LogInfo("Game TTF files available for Polish letters: " + string.Join(", ", new List<string>(fonts.Keys).ToArray()));
        }

        private static void Remember(Font font)
        {
            if (font == null || font.fontNames == null) return;
            if (font.name.IndexOf("italic", StringComparison.OrdinalIgnoreCase) >= 0) return;
            foreach (var name in font.fontNames)
                if (!fonts.ContainsKey(Key(name))) fonts[Key(name)] = font;
        }

        private static string Key(string name)
        {
            var key = new StringBuilder();
            foreach (var c in name ?? "")
                if (char.IsLetterOrDigit(c)) key.Append(char.ToLowerInvariant(c));
            var text = key.ToString();
            return text.EndsWith("regular", StringComparison.Ordinal) ? text.Substring(0, text.Length - 7) : text;
        }

        private static Font FindFont(string family)
        {
            var key = Key(family);
            Font font;
            if (fonts.TryGetValue(key, out font)) return font;
            foreach (var pair in fonts)
                if (pair.Key.StartsWith(key, StringComparison.Ordinal) && !pair.Key.Contains("italic")) return pair.Value;
            return null;
        }

        private static void Patch(TMP_FontAsset asset)
        {
            if (asset.name.StartsWith("notgeese", StringComparison.Ordinal)) return;
            var family = asset.faceInfo.familyName ?? "";
            if (family.IndexOf("Noto Sans JP", StringComparison.OrdinalIgnoreCase) >= 0) return;

            var missing = Missing(asset);
            if (missing.Length == 0) return;

            if (asset.atlasPopulationMode == AtlasPopulationMode.Dynamic)
            {
                string left;
                asset.TryAddCharacters(missing, out left);
                Plugin.Log.LogInfo(string.Format("TMP font \"{0}\" (dynamic): Polish letters added, missing: {1}.",
                    asset.name, string.IsNullOrEmpty(left) ? "-" : left));
                return;
            }

            var source = FindFont(family);
            if (source == null)
            {
                Plugin.Log.LogInfo(string.Format("TMP font \"{0}\" ({1}): missing {2}, no TTF of this family; the game's fallback font stays.",
                    asset.name, family, missing));
                return;
            }

            var fallback = TMP_FontAsset.CreateFontAsset(source, Mathf.Max(24, asset.faceInfo.pointSize),
                Mathf.Max(5, asset.atlasPadding), GlyphRenderMode.SDFAA, 512, 512, AtlasPopulationMode.Dynamic, true);
            if (fallback == null)
            {
                Plugin.Log.LogWarning("Could not create a font from " + source.name + ".");
                return;
            }
            fallback.name = "notgeese PL " + asset.name;
            string notAdded;
            fallback.TryAddCharacters(missing, out notAdded);
            UnityEngine.Object.DontDestroyOnLoad(fallback);

            if (asset.fallbackFontAssetTable == null) asset.fallbackFontAssetTable = new List<TMP_FontAsset>();
            asset.fallbackFontAssetTable.Insert(0, fallback);
            Plugin.Log.LogInfo(string.Format("TMP font \"{0}\" ({1}): missing {2} → fallback from {3}{4}.",
                asset.name, family, missing, source.name,
                string.IsNullOrEmpty(notAdded) ? "" : " (TTF also lacks: " + notAdded + ")"));
        }

        private static string Missing(TMP_FontAsset asset)
        {
            var missing = new StringBuilder();
            foreach (var c in Plugin.PolishLetters)
                if (!asset.HasCharacter(c, false, false)) missing.Append(c);
            return missing.ToString();
        }
    }
}
