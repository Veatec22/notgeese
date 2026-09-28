// Not Geese: Polish for Wild Bastards, added at runtime.
//
// The game has ten languages in an I2 Localization table compiled into its code. The plugin
// adds an eleventh ("Polish") filled from pl.tsv, adds a "Polski" button to the main menu
// language panel (LanguageButton.cs) and completes fonts with Polish letters from the game's
// TTF files (PolishFonts.cs). No game file is replaced.

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

namespace notgeese.WildBastards
{
    // The release before the project rename had a different GUID. If its folder is still in
    // plugins, BepInEx skips this plugin instead of loading two translations at once.
    [BepInIncompatibility("cc.notgoose.wildbastards")]
    [BepInPlugin(Id, "Wild Bastards PL", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string Id = "cc.notgeese.wildbastards";
        public const string Version = "0.1";

        internal const string LanguageName = "Polish";
        internal const string LanguageCode = "pl";
        internal const string ButtonLabel = "Polski";
        internal const string TermsFile = "pl.tsv";
        internal const string PolishLetters = "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ„”";

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
                harmony.PatchAll(typeof(LanguageButton));
                UnityEngine.SceneManagement.SceneManager.sceneLoaded += (scene, mode) => LanguagePatch.RefreshFonts();
                var patched = 0;
                foreach (var method in harmony.GetPatchedMethods()) patched++;
                Logger.LogInfo("Loaded " + Terms.Count + " entries, patches applied: " + patched + ".");
            }
            catch (Exception error)
            {
                Logger.LogError("Could not hook into the game, it stays English: " + error);
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
                if (line.Length == 0) continue;
                var tab = line.IndexOf('\t');
                if (tab <= 0) continue;
                terms[line.Substring(0, tab)] = line.Substring(tab + 1).Replace("\\n", "\n");
            }
            return terms;
        }
    }

    // The BepInEx object can be destroyed on scene change, so instead of Update we hook the
    // language setter and scene loading (this game reloads the scene after a language change).
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
                PolishFonts.PatchLoadedFonts();
            }
            catch (Exception error)
            {
                Plugin.Log.LogWarning("Font completion failed: " + error.Message);
            }
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
                "Polish added as language {0} of {1}: {2} texts, untranslated {3}.",
                index + 1, before + 1, filled, missing));
            if (missing > 0)
                Plugin.Log.LogWarning(missing + " texts of this game version are not in the translation; they stay English.");
        }
    }
}
