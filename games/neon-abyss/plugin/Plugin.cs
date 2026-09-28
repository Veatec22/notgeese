// Not Geese: Polish for Neon Abyss, added at runtime.
//
// The plugin appends an eleventh language to the I2 Localization source right after it loads
// and fills it from pl.tsv next to this DLL. Also:
// - adds POLSKI to the options language switcher, which the game hardcodes;
// - gives Polish letters fonts from the game itself: English atlases are static and lack
//   ą, ę, ł, so they get fallback atlases with Polish letters rendered at startup by the
//   font engine from the game's TTF files (on-the-fly fill fails in this TMP version).
// No game file is changed. When something doesn't match, the plugin logs and drops out
// and the game stays English.

using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using I2.Loc;
using TMPro;
using UnityEngine;

namespace notgeese.NeonAbyss
{
    // The release before the project rename had a different GUID. If its folder is still in
    // plugins, BepInEx skips this plugin instead of loading two translations at once.
    [BepInIncompatibility("cc.notgoose.neonabyss")]
    [BepInPlugin(Id, "Neon Abyss PL", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string Id = "cc.notgeese.neonabyss";
        public const string Version = "0.1";

        internal const string LanguageName = "Polish";
        internal const string LanguageCode = "pl";
        internal const string MenuLabel = "POLSKI";
        internal const string TermsFile = "pl.tsv";

        internal static ManualLogSource Log;
        internal static Dictionary<string, string> Terms;

        private void Awake()
        {
            Log = Logger;

            Terms = ReadTerms();
            if (Terms.Count == 0)
            {
                Logger.LogError("No texts found in " + TermsFile + "; Polish will not be added.");
                return;
            }

            Logger.LogInfo(string.Format(
                "Game {0}, Unity {1}, loaded {2} entries.",
                Application.version, Application.unityVersion, Terms.Count));

            var harmony = new Harmony(Id);
            Patch(harmony, typeof(LocalizationManager), "AddSource", null, "AfterAddSource");
            Patch(harmony, typeof(LocalizationManager), "InitializeIfNeeded", null, "AfterInitialize");

            var valueSource = AccessTools.TypeByName("NEON.UI.Base.UIMenuSwitcherLanguageValueSource");
            var gamePlay = AccessTools.TypeByName("NEON.UI.MainScreen.Options.GamePlay.GamePlaySettingsHandler");
            var settings = AccessTools.TypeByName("NEON.UI.MainScreen.Options.Base.SettingsHandlerBase");
            Patch(harmony, valueSource, "Awake", null, "AfterValuesAwake");
            Patch(harmony, gamePlay, "LanguageReverseMapping", "MapLabel", null);
            Patch(harmony, gamePlay, "LanguageMapping", "MapLabel", null);
            Patch(harmony, settings, "InitWithLanguge", "InitSwitcher", null);
            Patch(harmony, typeof(TMP_Text), "set_font", "BeforeSetFont", null);
            Patch(harmony, typeof(TextMeshProUGUI), "LoadFontAsset", null, "AfterLoadFontAsset");
            Patch(harmony, typeof(TextMeshPro), "LoadFontAsset", null, "AfterLoadFontAsset");
        }

        private void Patch(Harmony harmony, Type type, string method, string prefix, string postfix)
        {
            try
            {
                var original = type == null ? null : AccessTools.Method(type, method);
                if (original == null)
                {
                    Logger.LogWarning(method + " not found; this game version differs from the expected one.");
                    return;
                }
                harmony.Patch(original,
                    prefix == null ? null : new HarmonyMethod(typeof(Patches), prefix),
                    postfix == null ? null : new HarmonyMethod(typeof(Patches), postfix));
            }
            catch (Exception error)
            {
                Logger.LogError("Could not hook " + method + ": " + error.Message);
            }
        }

        /// File next to the DLL: key, tab, text. Newlines stored as \n.
        private Dictionary<string, string> ReadTerms()
        {
            var terms = new Dictionary<string, string>(StringComparer.Ordinal);
            var folder = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            var path = Path.Combine(folder, TermsFile);

            if (!File.Exists(path))
            {
                Logger.LogError("Missing file " + path);
                return terms;
            }

            foreach (var line in File.ReadAllLines(path, Encoding.UTF8))
            {
                if (line.Length == 0) continue;
                var tab = line.IndexOf('\t');
                if (tab <= 0) continue;
                terms[line.Substring(0, tab)] = line.Substring(tab + 1).Replace("\\n", "\n");
            }

            return terms;
        }
    }

    internal static class Patches
    {
        // --- I2 source --------------------------------------------------------------

        // The global source comes from Resources, and every source goes through
        // LocalizationManager.AddSource before the game sets the saved language.
        private static void AfterAddSource(object[] __args)
        {
            Apply(__args.Length > 0 ? __args[0] as LanguageSourceData : null);
        }

        private static void AfterInitialize()
        {
            if (LocalizationManager.Sources == null) return;
            foreach (var source in LocalizationManager.Sources) Apply(source);
        }

        private static void Apply(LanguageSourceData source)
        {
            try
            {
                if (Install(source)) Fonts.Install();
            }
            catch (Exception error)
            {
                Plugin.Log.LogError("Could not add Polish: " + error);
            }
        }

        private static bool Install(LanguageSourceData source)
        {
            if (source == null || source.mTerms == null || source.mTerms.Count == 0) return false;

            var known = 0;
            foreach (var term in source.mTerms)
            {
                if (Plugin.Terms.ContainsKey(term.Term) && ++known > 4) break;
            }
            if (known == 0) return false;

            // Idempotent: the same source may pass here more than once.
            foreach (var language in source.mLanguages)
            {
                if (string.Equals(language.Code, Plugin.LanguageCode, StringComparison.OrdinalIgnoreCase)) return false;
            }

            var english = source.GetLanguageIndexFromCode("en-US", true, false);
            if (english < 0)
            {
                Plugin.Log.LogError("Source has no English; nothing to take missing texts from.");
                return false;
            }

            source.AddLanguage(Plugin.LanguageName, Plugin.LanguageCode);
            var index = source.GetLanguageIndexFromCode(Plugin.LanguageCode, true, false);

            int translated = 0, fallback = 0, other = 0;
            foreach (var term in source.mTerms)
            {
                if (term.Languages == null || index >= term.Languages.Length) continue;
                string value;
                if (Fonts.TermValues.TryGetValue(term.Term, out value))
                {
                    other++;
                }
                else if (term.TermType != eTermType.Text)
                {
                    // Sprites, materials, pad buttons: as in English.
                    value = term.Languages[english];
                    other++;
                }
                else if (Plugin.Terms.TryGetValue(term.Term, out value))
                {
                    translated++;
                }
                else
                {
                    // New texts after a game update stay English.
                    value = term.Languages[english];
                    fallback++;
                }
                term.Languages[index] = value;
            }

            source.UpdateDictionary(true);
            LocalizationManager.LocalizeAll(true);
            Plugin.Log.LogInfo(string.Format(
                "Polish added as language {0}: {1} texts in Polish, {2} other entries (fonts, sprites).",
                index + 1, translated, other));
            if (fallback > 0)
            {
                Plugin.Log.LogWarning(fallback + " texts of this game version are not in the translation; they stay English.");
            }
            return true;
        }

        // The game's broken atlas is swapped for a fresh one before it reaches a text.
        private static void BeforeSetFont(ref TMP_FontAsset value)
        {
            value = Fonts.Substitute(value);
            Fonts.Ensure(value);
        }

        // A text with the font saved in its prefab skips the setter; caught here.
        private static void AfterLoadFontAsset(TMP_Text __instance)
        {
            if (__instance != null) Fonts.Ensure(__instance.font);
        }

        // --- Options language switcher ----------------------------------------------
        //
        // Settings store the I2 language name; the menu shows labels ("ENGLISH", "РУССКИЙ")
        // from a list hardcoded in UIMenuSwitcherLanguageValueSource. The mapping both ways
        // is hardcoded too, so we add the pair POLSKI ↔ Polish.

        private static void AfterValuesAwake(object __instance)
        {
            try
            {
                var values = FindMember(__instance, "Values") as IList;
                if (values == null)
                {
                    Plugin.Log.LogWarning("Options language list has an unknown shape; POLSKI won't reach the menu.");
                    return;
                }
                if (!values.Contains(Plugin.MenuLabel)) values.Add(Plugin.MenuLabel);
            }
            catch (Exception error)
            {
                Plugin.Log.LogError("Could not add POLSKI to the menu: " + error.Message);
            }
        }

        // LanguageMapping and LanguageReverseMapping: label → I2 language name.
        private static bool MapLabel(object[] __args, ref string __result)
        {
            var label = __args.Length > 0 ? __args[0] as string : null;
            if (label != Plugin.MenuLabel && label != Plugin.LanguageName) return true;
            __result = Plugin.LanguageName;
            return false;
        }

        // InitWithLanguge(switcher, language name): sets the switcher to the saved language.
        private static bool InitSwitcher(object[] __args)
        {
            if (__args.Length < 2 || __args[0] == null || (__args[1] as string) != Plugin.LanguageName) return true;
            try
            {
                var switcher = __args[0];
                var source = Traverse.Create(switcher).Field("DataSource").GetValue();
                var options = Traverse.Create(source).Method("GetOptions").GetValue() as IEnumerable;
                var index = 0;
                foreach (var option in options)
                {
                    if ((option as string) == Plugin.MenuLabel)
                    {
                        Traverse.Create(switcher).Method("SwitchTo", new[] { typeof(int) }).GetValue(index);
                        return false;
                    }
                    index++;
                }
                Plugin.Log.LogWarning("Language switcher has no POLSKI item.");
            }
            catch (Exception error)
            {
                Plugin.Log.LogError("Could not set the switcher to POLSKI: " + error.Message);
            }
            return true;
        }

        private static object FindMember(object instance, string name)
        {
            const BindingFlags all = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
            for (var type = instance.GetType(); type != null; type = type.BaseType)
            {
                var field = type.GetField(name, all);
                if (field != null) return field.GetValue(instance);
                var property = type.GetProperty(name, all);
                if (property != null) return property.GetValue(instance, null);
            }
            return null;
        }
    }

    // Fonts. The game switches fonts per language with I2 terms UI/smallFont and UI/BigFont.
    // English atlases (PixAntiqua, ModernBrush) are static and lack Polish letters.
    // Small text gets the pixel Zpix, which the game has as a dynamic atlas for Traditional
    // Chinese; big headers stay ModernBrush with a fallback made from its own TTF. Texts with
    // a hardcoded font get a global Zpix fallback.
    internal static class Fonts
    {
        private const string Folder = "Fonts & Materials/";

        internal static readonly Dictionary<string, string> TermValues = new Dictionary<string, string>
        {
            { "UI/smallFont", Folder + "CHT_12px_Zpix" },
            { "UI/BigFont", Folder + "EN_70px_ModernBrush" },
        };

        private static bool installed;

        internal static void Install()
        {
            if (installed) return;
            installed = true;

            // Game atlases are raster (Bitmap shader), so fallbacks must match: the default
            // CreateFontAsset gives SDF, which Bitmap draws as an empty outline.
            AddFallback(Folder + "EN_70px_ModernBrush", Folder + "_TTF/ModernBrush-Regular", 70, 2);
            AddFallback(Folder + "EN_12px_PixAntiqua", Folder + "_TTF/Zpix", 12, 2);

            var global = Create(Folder + "_TTF/Zpix", 12, 2, Resources.Load<TMP_FontAsset>(Folder + "EN_12px_PixAntiqua"));
            if (global != null && TMP_Settings.instance != null && TMP_Settings.fallbackFontAssets != null)
            {
                Keep(global);
                TMP_Settings.fallbackFontAssets.Add(global);
                Plugin.Log.LogInfo("Global fallback font: Zpix.");
            }
        }

        // The game's dynamic CHT_12px_Zpix atlas ships with a free-rect list that overlaps
        // 159 already drawn glyphs ("i" among them), so every added Polish letter lands on
        // another glyph. Clearing the atlas (ClearFontAssetData) didn't fix it in this TMP
        // version, so for Polish texts get a fresh atlas from the same Zpix file with the same
        // settings: 12 px, hinted raster, padding 5, Bitmap shader. Chinese keeps the original.
        internal const string BrokenAtlas = "CHT_12px_Zpix";
        private static TMP_FontAsset fresh;
        private static bool freshFailed;

        internal static TMP_FontAsset Substitute(TMP_FontAsset asset)
        {
            if (asset == null || asset.name != BrokenAtlas || freshFailed) return asset;
            if (LocalizationManager.CurrentLanguageCode != Plugin.LanguageCode) return asset;
            if (fresh == null) fresh = CreateFresh(asset);
            return fresh ?? asset;
        }

        private static TMP_FontAsset CreateFresh(TMP_FontAsset original)
        {
            try
            {
                var font = Resources.Load<Font>(Folder + "_TTF/Zpix");
                if (font == null) throw new Exception("missing Fonts & Materials/_TTF/Zpix");
                var asset = TMP_FontAsset.CreateFontAsset(font, 12, 5,
                    UnityEngine.TextCore.LowLevel.GlyphRenderMode.RASTER_HINTED, 1024, 1024,
                    AtlasPopulationMode.Dynamic);
                if (asset == null) throw new Exception("CreateFontAsset returned null");
                asset.name = BrokenAtlas + " (Not Geese)";
                Initialize(asset);
                if (original.material != null && asset.material != null)
                {
                    var texture = asset.material.GetTexture(ShaderUtilities.ID_MainTex);
                    asset.material.shader = original.material.shader;
                    asset.material.SetTexture(ShaderUtilities.ID_MainTex, texture);
                }
                if (original.atlasTexture != null && asset.atlasTexture != null)
                    asset.atlasTexture.filterMode = original.atlasTexture.filterMode;
                asset.fallbackFontAssetTable = original.fallbackFontAssetTable;
                Keep(asset);
                Plugin.Log.LogInfo("Polish small text gets a fresh Zpix atlas instead of " + BrokenAtlas + ".");
                return asset;
            }
            catch (Exception error)
            {
                freshFailed = true;
                Plugin.Log.LogError("Could not build a fresh Zpix atlas, keeping " + BrokenAtlas + ": " + error.Message);
                return null;
            }
        }

        // Fallback atlases with Polish letters, by the name of the game atlas they attach to.
        // Between scenes the game frees unused assets (UnloadUnusedAssets), and an atlas reloaded
        // from Resources no longer has our fallback. So the fallback is built once, protected
        // from unloading and attached to every instance that reaches a text (Ensure in
        // TMP_Text.font and LoadFontAsset).
        private static readonly Dictionary<string, TMP_FontAsset> polish = new Dictionary<string, TMP_FontAsset>();
        private static readonly HashSet<int> ensured = new HashSet<int>();

        private static void AddFallback(string assetPath, string fontPath, int pointSize, int padding)
        {
            try
            {
                var asset = Resources.Load<TMP_FontAsset>(assetPath);
                var fallback = asset == null ? null : BuildStatic(fontPath, pointSize, padding, asset);
                if (asset == null || fallback == null)
                {
                    Plugin.Log.LogWarning("Missing " + (asset == null ? assetPath : fontPath) + "; Polish letters may not show.");
                    return;
                }
                Keep(fallback);
                polish[asset.name] = fallback;
                Ensure(asset);
            }
            catch (Exception error)
            {
                Plugin.Log.LogError("Could not add a font to " + assetPath + ": " + error.Message);
            }
        }

        internal static void Ensure(TMP_FontAsset asset)
        {
            TMP_FontAsset fallback;
            if (asset == null || !polish.TryGetValue(asset.name, out fallback)) return;
            if (asset.fallbackFontAssetTable == null) asset.fallbackFontAssetTable = new List<TMP_FontAsset>();
            if (asset.fallbackFontAssetTable.Count > 0 && asset.fallbackFontAssetTable[0] == fallback) return;
            asset.fallbackFontAssetTable.Remove(fallback);
            asset.fallbackFontAssetTable.Insert(0, fallback);
            if (ensured.Add(asset.GetInstanceID()))
                Plugin.Log.LogInfo("Font " + asset.name + " (instance " + asset.GetInstanceID() + ") got Polish letters from " + fallback.name + ".");
        }

        private static void Keep(TMP_FontAsset asset)
        {
            asset.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            if (asset.material != null) asset.material.hideFlags |= HideFlags.DontUnloadUnusedAsset;
            if (asset.atlasTexture != null) asset.atlasTexture.hideFlags |= HideFlags.DontUnloadUnusedAsset;
        }

        // In this TMP version an atlas from CreateFontAsset has null free/used rect lists, glyphs
        // to add etc.; in the editor serialization fills them. Without them
        // FontEngine.TryAddGlyphsToTexture throws NullReferenceException, the letter never
        // reaches the atlas and TMP silently takes it from the next fallback. We fill them as TMP
        // does when clearing an atlas: empty collections and one free rect for the whole atlas.
        private static void Initialize(TMP_FontAsset asset)
        {
            const BindingFlags instance = BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public;
            foreach (var field in typeof(TMP_FontAsset).GetFields(instance))
            {
                if (field.GetValue(asset) != null) continue;
                var type = field.FieldType;
                if (type.IsGenericType && type.GetConstructor(Type.EmptyTypes) != null)
                    field.SetValue(asset, Activator.CreateInstance(type));
                else if (type == typeof(TMP_FontFeatureTable))
                    field.SetValue(asset, new TMP_FontFeatureTable());
            }
            var free = AccessTools.Field(typeof(TMP_FontAsset), "m_FreeGlyphRects").GetValue(asset)
                as List<UnityEngine.TextCore.GlyphRect>;
            if (free != null && free.Count == 0)
                free.Add(new UnityEngine.TextCore.GlyphRect(0, 0, asset.atlasWidth, asset.atlasHeight));
            asset.ReadFontAssetDefinition();
        }

        // On-the-fly fill (dynamic atlases) doesn't work in this TMP version for atlases made
        // by CreateFontAsset: TryAddCharacters throws and the letter falls to the next
        // fallback in another face. So we build the Polish fallback ourselves with the font
        // engine: each letter rendered once from the game's TTF into our texture, atlas static.
        internal const string StaticLetters = "ĄĆĘŁŃÓŚŹŻąćęłńóśźż„”–—…";

        private static TMP_FontAsset BuildStatic(string fontPath, int pointSize, int padding, TMP_FontAsset like)
        {
            var font = Resources.Load<Font>(fontPath);
            if (font == null) return null;
            const UnityEngine.TextCore.LowLevel.GlyphRenderMode mode = UnityEngine.TextCore.LowLevel.GlyphRenderMode.RASTER_HINTED;
            var size = pointSize > 32 ? 512 : 128;

            var asset = TMP_FontAsset.CreateFontAsset(font, pointSize, padding, mode, size, size, AtlasPopulationMode.Static);
            if (asset == null) return null;
            asset.name = font.name + " " + pointSize + " PL (Not Geese)";
            Initialize(asset);

            var engine = typeof(UnityEngine.TextCore.LowLevel.FontEngine);
            var reset = AccessTools.Method(engine, "ResetAtlasTexture");
            var add = AccessTools.Method(engine, "TryAddGlyphToTexture");
            if (add == null || reset == null) throw new Exception("missing FontEngine.TryAddGlyphToTexture");
            var load = UnityEngine.TextCore.LowLevel.FontEngine.LoadFontFace(font, pointSize);
            if (load != UnityEngine.TextCore.LowLevel.FontEngineError.Success) throw new Exception("LoadFontFace: " + load);

            var texture = new Texture2D(size, size, TextureFormat.Alpha8, false);
            reset.Invoke(null, new object[] { texture });
            var free = new List<UnityEngine.TextCore.GlyphRect> { new UnityEngine.TextCore.GlyphRect(0, 0, size, size) };
            var used = new List<UnityEngine.TextCore.GlyphRect>();

            var added = new StringBuilder();
            var failed = new StringBuilder();
            foreach (var c in StaticLetters)
            {
                uint index;
                if (!UnityEngine.TextCore.LowLevel.FontEngine.TryGetGlyphIndex(c, out index) || index == 0)
                {
                    failed.Append(c);
                    continue;
                }
                var args = new object[] { index, padding, UnityEngine.TextCore.LowLevel.GlyphPackingMode.BestShortSideFit,
                    free, used, mode, texture, null };
                var ok = (bool)add.Invoke(null, args);
                var glyph = args[7] as UnityEngine.TextCore.Glyph;
                if (!ok || glyph == null)
                {
                    failed.Append(c);
                    continue;
                }
                asset.glyphTable.Add(glyph);
                asset.characterTable.Add(new TMP_Character(c, glyph));
                added.Append(c);
            }
            texture.Apply(false, false);
            if (like.atlasTexture != null) texture.filterMode = like.atlasTexture.filterMode;
            texture.name = asset.name + " Atlas";

            AccessTools.Field(typeof(TMP_FontAsset), "m_AtlasTextures").SetValue(asset, new[] { texture });
            if (asset.material != null)
            {
                if (like.material != null) asset.material.shader = like.material.shader;
                asset.material.SetTexture(ShaderUtilities.ID_MainTex, texture);
            }
            asset.ReadFontAssetDefinition();

            Plugin.Log.LogInfo("Atlas " + asset.name + ": rendered \"" + added + "\""
                + (failed.Length > 0 ? ", no glyph \"" + failed + "\"" : "") + ".");
            return asset;
        }

        // Dynamic raster atlas from the game's TTF, shader taken from the model atlas.
        private static TMP_FontAsset Create(string fontPath, int pointSize, int padding, TMP_FontAsset like)
        {
            var font = Resources.Load<Font>(fontPath);
            if (font == null) return null;
            var asset = TMP_FontAsset.CreateFontAsset(font, pointSize, padding,
                UnityEngine.TextCore.LowLevel.GlyphRenderMode.RASTER_HINTED, 1024, 1024,
                AtlasPopulationMode.Dynamic);
            if (asset == null) return null;
            asset.name = font.name + " " + pointSize + " (Not Geese)";
            // An atlas from CreateFontAsset has no character tables yet; without them TMP
            // fails when adding glyphs and silently takes the letter from the next fallback.
            Initialize(asset);
            if (like != null && like.material != null && asset.material != null)
            {
                var texture = asset.material.GetTexture(ShaderUtilities.ID_MainTex);
                asset.material.shader = like.material.shader;
                asset.material.SetTexture(ShaderUtilities.ID_MainTex, texture);
            }
            // Game atlases use Point filtering (pixel for pixel); the default bilinear blurs letters.
            if (like != null && like.atlasTexture != null && asset.atlasTexture != null)
                asset.atlasTexture.filterMode = like.atlasTexture.filterMode;
            return asset;
        }
    }
}
