// Not Geese: Polish for Cyber Hook, swapped in at runtime.
//
// Each language is a CSV (key -> text) in a Language_SO; the language is picked by an enum
// value saved in settings. The enum can't be extended without replacing game code, so
// Polish takes English's place: while "en" is active, Language_SO answers from pl.tsv.
// Other languages work as before.
// No game file is replaced.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using TMPro;
using UnityEngine;

namespace notgeese.CyberHook
{
    // The release before the project rename had a different GUID. If its folder is still in
    // plugins, BepInEx skips this plugin instead of loading two translations at once.
    [BepInIncompatibility("cc.notgoose.cyberhook")]
    [BepInPlugin(Id, "Cyber Hook PL", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string Id = "cc.notgeese.cyberhook";
        public const string Version = "0.1";

        // Key of the language we replace. The menu labels it with entry option_en.
        internal const string LanguageKey = "en";
        internal const string TermsFile = "pl.tsv";

        internal static ManualLogSource Log;

        /// Game key (lower-case, edges trimmed, as in Language_SO) -> Polish text.
        internal static Dictionary<string, string> Terms;

        private void Awake()
        {
            Log = Logger;
            Logger.LogInfo(string.Format("PL {0}; game {1} {2}, Unity {3}.", Version,
                Application.productName, Application.version, Application.unityVersion));

            Terms = ReadTerms();
            if (Terms.Count == 0)
            {
                Logger.LogError("No texts found in " + TermsFile + "; the game stays English.");
                return;
            }

            try
            {
                var harmony = new Harmony(Id);
                harmony.PatchAll(typeof(LanguagePatch));
                harmony.PatchAll(typeof(FontPatch));
                harmony.PatchAll(typeof(DialogPatch));
                UnityEngine.SceneManagement.SceneManager.sceneLoaded += (scene, mode) => FontPatch.Refresh();
                var patched = 0;
                foreach (var method in harmony.GetPatchedMethods()) patched++;
                Logger.LogInfo("Loaded " + Terms.Count + " entries, patches applied: " + patched + ".");
            }
            catch (Exception error)
            {
                Logger.LogError("Could not hook into the language system, the game stays English: " + error.Message);
            }
        }

        /// File next to the library: key, tab, text. Newlines as \n.
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
            foreach (var line in File.ReadAllText(path, Encoding.UTF8).Split('\n'))
            {
                // A CRLF file would leave \r in the text, and TextMeshPro moves the pen back on it.
                var entry = line.TrimEnd('\r');
                if (entry.Length == 0) continue;
                var tab = entry.IndexOf('\t');
                if (tab <= 0) continue;
                terms[Normalize(entry.Substring(0, tab))] = entry.Substring(tab + 1).Replace("\\n", "\n");
            }
            return terms;
        }

        internal static string Normalize(string key)
        {
            return key.ToLowerInvariant().Trim();
        }

        /// Whether we translate: the English Language_SO is asked and it is the active language.
        /// Other languages ask English as a fallback; then English stays.
        internal static bool Active(Language_SO language)
        {
            if (Terms == null || language == null || language.LanguageKey != LanguageKey) return false;
            if (!GenericSingleton<LanguageManager>.IsInstantiated) return true;
            return GenericSingleton<LanguageManager>.Instance.LanguageKey == LanguageKey;
        }

        internal static bool TryGet(string key, out string text)
        {
            text = null;
            return key != null && Terms.TryGetValue(Normalize(key), out text);
        }
    }

    [HarmonyPatch]
    internal static class LanguagePatch
    {
        private static bool reported;

        [HarmonyPrefix]
        [HarmonyPatch(typeof(Language_SO), nameof(Language_SO.GetTranslatedKey))]
        private static bool GetTranslatedKey(Language_SO __instance, string key, ref string __result)
        {
            if (!Plugin.Active(__instance)) return true;
            FontPatch.RefreshIfPending();
            string text;
            if (!Plugin.TryGet(key, out text)) return true;
            __result = text;
            return false;
        }

        // Some lines carry plain English text instead of a key; the game treats it as a missing
        // key and shows the text as is. For the ones we translated, the key "exists".
        [HarmonyPostfix]
        [HarmonyPatch(typeof(Language_SO), nameof(Language_SO.KeyExists))]
        private static void KeyExists(Language_SO __instance, string key, ref bool __result)
        {
            string text;
            if (!__result && Plugin.Active(__instance) && Plugin.TryGet(key, out text)) __result = true;
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(Language_SO), "ParseLanguageFile")]
        private static void Parsed(Language_SO __instance, Dictionary<string, string> __result)
        {
            if (reported || __result == null || __instance.LanguageKey != Plugin.LanguageKey) return;
            reported = true;
            var missing = 0;
            foreach (var key in __result.Keys)
                if (!Plugin.Terms.ContainsKey(key)) missing++;
            if (missing > 0)
                Plugin.Log.LogWarning(missing + " of " + __result.Count + " texts of this game version are not in the translation; they stay English.");
            else
                Plugin.Log.LogInfo("All " + __result.Count + " game texts have a Polish translation.");
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(LanguageManager), nameof(LanguageManager.LanguageKey), MethodType.Setter)]
        private static void LanguageChanged()
        {
            FontPatch.Refresh();
        }
    }

    // The dialogue window (Dron, Numero) is masked just above the first text line.
    // English capitals fit, but the marks over Ś, Ć, Ż stick out and the mask would clip
    // them. The text is pushed down from the top edge by a quarter of the font size.
    [HarmonyPatch]
    internal static class DialogPatch
    {
        private static readonly HashSet<int> Done = new HashSet<int>();

        [HarmonyPostfix]
        [HarmonyPatch(typeof(DialogTextDisplay), nameof(DialogTextDisplay.Init))]
        private static void Init(DialogTextDisplay __instance)
        {
            try
            {
                var text = Traverse.Create(__instance).Field("_text").GetValue<TMPro.TextMeshProUGUI>();
                if (text == null || !Done.Add(text.GetInstanceID())) return;
                var margin = text.margin;
                margin.y += text.fontSize * 0.25f;
                text.margin = margin;
            }
            catch (Exception error)
            {
                Plugin.Log.LogWarning("Could not offset the dialogue text: " + error.Message);
            }
        }
    }

    // Fonts arrive from asset bundles at different times. A new font only flags work;
    // letters are composed before the next text translation.
    [HarmonyPatch]
    internal static class FontPatch
    {
        private static bool pending = true;

        [HarmonyPostfix]
        [HarmonyPatch(typeof(TMP_FontAsset), "Awake")]
        private static void FontLoaded()
        {
            pending = true;
        }

        internal static void RefreshIfPending()
        {
            if (pending) Refresh();
        }

        internal static void Refresh()
        {
            try
            {
                if (!GenericSingleton<LanguageManager>.IsInstantiated
                    || GenericSingleton<LanguageManager>.Instance.LanguageKey != Plugin.LanguageKey) return;
                pending = false;
                if (PolishGlyphs.PatchLoadedFonts() == 0) return;
                // Texts built before the patch would still show boxes instead of letters.
                foreach (var text in Resources.FindObjectsOfTypeAll<TMP_Text>())
                {
                    if (text == null || !text.isActiveAndEnabled) continue;
                    text.havePropertiesChanged = true;
                    text.SetAllDirty();
                }
            }
            catch (Exception error)
            {
                Plugin.Log.LogWarning("Font completion failed: " + error.Message);
            }
        }
    }
}
