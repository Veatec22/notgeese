// Not Geese: Polish for Void Bastards, added at runtime.
//
// The game has nine languages in an I2 Localization table compiled into its code. The plugin
// adds a tenth ("Polish") and fills it from pl.tsv. The language screen lists the table's
// languages and labels them with the term "Language/<name>", so Polish shows up by itself.
// No game file is replaced.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using I2.Loc;
using UnityEngine;

namespace notgeese.VoidBastards
{
    // The release before the project rename had a different GUID. If its folder is still in
    // plugins, BepInEx skips this plugin instead of loading two translations at once.
    [BepInIncompatibility("cc.notgoose.voidbastards")]
    [BepInPlugin(Id, "Void Bastards PL", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string Id = "cc.notgeese.voidbastards";
        public const string Version = "0.1";

        // The language name is also the menu label key: "Language/Polish".
        internal const string LanguageName = "Polish";
        internal const string LanguageCode = "pl";
        internal const string TermsFile = "pl.tsv";
        internal const string PolishLetters = "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ";

        internal static ManualLogSource Log;
        internal static Dictionary<string, string> Terms;

        private void Awake()
        {
            Log = Logger;
            Logger.LogInfo(string.Format("PL {0}; game {1} {2}, Unity {3}.", Version,
                Application.productName, Application.version, Application.unityVersion));

            Terms = ReadTerms();
            if (Terms.Count == 0)
            {
                Logger.LogError("No texts found in " + TermsFile + "; Polish will not be added.");
                return;
            }

            try
            {
                var harmony = new Harmony(Id);
                harmony.PatchAll(typeof(SourcePatch));
                harmony.PatchAll(typeof(LanguagePatch));
                UnityEngine.SceneManagement.SceneManager.sceneLoaded += (scene, mode) => LanguagePatch.RefreshFonts();
                var patched = 0;
                foreach (var method in harmony.GetPatchedMethods()) patched++;
                if (patched == 0)
                {
                    Logger.LogError("No I2 hook points found; this game version differs from the expected one.");
                    return;
                }
                Logger.LogInfo("Loaded " + Terms.Count + " entries, patches applied: " + patched + ".");
            }
            catch (Exception error)
            {
                Logger.LogError("Could not hook into I2, the game stays English: " + error.Message);
            }
        }

        /// File next to the library: entry key, tab, text. Newlines as \n.
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
                terms[entry.Substring(0, tab)] = entry.Substring(tab + 1).Replace("\\n", "\n");
            }
            return terms;
        }
    }

    // The BepInEx object can be destroyed on scene change, so instead of Update we hook the
    // language setter and scene loading.
    [HarmonyPatch]
    internal static class LanguagePatch
    {
        [HarmonyPostfix]
        [HarmonyPatch(typeof(LocalizationManager), "CurrentLanguage", MethodType.Setter)]
        private static void AfterSetLanguage()
        {
            RefreshFonts();
        }

        internal static void RefreshFonts()
        {
            try
            {
                if (LocalizationManager.CurrentLanguage != Plugin.LanguageName) return;
                PolishGlyphs.PatchLoadedFonts();
                FontReport.Write();
            }
            catch (Exception error)
            {
                Plugin.Log.LogWarning("Font completion failed: " + error.Message);
            }
        }
    }

    internal static class FontReport
    {
        private static readonly HashSet<string> Reported = new HashSet<string>();

        internal static void Write()
        {
            try
            {
                foreach (var font in Resources.FindObjectsOfTypeAll<Font>())
                    Report("Font", font.name, font.dynamic, c => font.HasCharacter(c));
                foreach (var font in Resources.FindObjectsOfTypeAll<TMPro.TMP_FontAsset>())
                {
                    if (font.name.StartsWith("notgeese", StringComparison.Ordinal)) continue;
                    var asset = font;
                    Report("TMP", font.name, false, c => HasWithFallback(asset, c));
                }
            }
            catch (Exception error)
            {
                Plugin.Log.LogWarning("Font report failed: " + error.Message);
            }
        }

        private static bool HasWithFallback(TMPro.TMP_FontAsset font, char c)
        {
            if (font.HasCharacter(c)) return true;
            if (font.fallbackFontAssets == null) return false;
            foreach (var fallback in font.fallbackFontAssets)
                if (fallback != null && fallback.HasCharacter(c)) return true;
            return false;
        }

        private static void Report(string kind, string name, bool dynamic, Func<char, bool> has)
        {
            if (!Reported.Add(kind + "/" + name)) return;
            var missing = new StringBuilder();
            foreach (var c in Plugin.PolishLetters)
                if (!has(c)) missing.Append(c);
            Plugin.Log.LogInfo(string.Format("Font {0} \"{1}\"{2}: {3}", kind, name,
                dynamic ? " (dynamic)" : "", missing.Length == 0 ? "all Polish letters" : "missing " + missing));
        }
    }

    // The translation source may be an asset, not a scene object, so its Awake may never
    // run. Registration of the source in the manager is the reliable hook.
    [HarmonyPatch]
    internal static class SourcePatch
    {
        private static readonly HashSet<LanguageSourceData> Done = new HashSet<LanguageSourceData>();

        [HarmonyPostfix]
        [HarmonyPatch(typeof(LocalizationManager), "AddSource")]
        private static void AfterAddSource(LanguageSourceData __0)
        {
            Apply(__0);
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(LocalizationManager), "InitializeIfNeeded")]
        private static void AfterInitialize()
        {
            if (LocalizationManager.Sources == null) return;
            foreach (var source in LocalizationManager.Sources) Apply(source);
        }

        private static void Apply(LanguageSourceData source)
        {
            if (source == null || Done.Contains(source)) return;
            try
            {
                Install(source);
            }
            catch (Exception error)
            {
                Done.Add(source);
                Plugin.Log.LogError("Could not add Polish: " + error);
            }
        }

        private static void Install(LanguageSourceData source)
        {
            if (source.mTerms == null || source.mTerms.Count == 0) return;

            var known = 0;
            foreach (var term in source.mTerms)
                if (Plugin.Terms.ContainsKey(term.Term) && ++known > 4) break;
            if (known == 0)
            {
                Plugin.Log.LogInfo("Skipping a source without our keys (" + source.mTerms.Count + " entries).");
                return;
            }
            Done.Add(source);

            if (source.GetLanguageIndexFromCode(Plugin.LanguageCode, false, false) >= 0)
            {
                Plugin.Log.LogInfo("Polish is already in the table; not adding it twice.");
                return;
            }

            var before = source.mLanguages.Count;
            source.AddLanguage(Plugin.LanguageName, Plugin.LanguageCode);
            var index = source.mLanguages.Count - 1;

            // Terms the game lacks but Polish needs (the language menu label).
            var added = 0;
            foreach (var pair in Plugin.Terms)
            {
                if (source.GetTermData(pair.Key, false) != null) continue;
                if (!pair.Key.StartsWith("Language/", StringComparison.Ordinal)) continue;
                var created = source.AddTerm(pair.Key);
                if (created != null) added++;
            }

            var filled = 0;
            var missing = 0;
            foreach (var term in source.mTerms)
            {
                if (term.Languages == null || index >= term.Languages.Length) continue;
                string polish;
                if (Plugin.Terms.TryGetValue(term.Term, out polish))
                {
                    term.Languages[index] = polish;
                    if (term.Flags != null && index < term.Flags.Length) term.Flags[index] = 0;
                    filled++;
                }
                else if (!string.IsNullOrEmpty(term.Languages[0]))
                {
                    missing++;
                }
            }

            source.UpdateDictionary(true);
            LanguagePatch.RefreshFonts();
            LocalizationManager.LocalizeAll(true);
            Plugin.Log.LogInfo(string.Format(
                "Polish added as language {0} of {1}: {2} texts, new terms {3}, untranslated {4}.",
                index + 1, before + 1, filled, added, missing));
            if (missing > 0)
                Plugin.Log.LogWarning(missing + " texts of this game version are not in the translation; they stay English.");
        }
    }
}
