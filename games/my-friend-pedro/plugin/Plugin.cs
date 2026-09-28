// Not Geese: Polish for My Friend Pedro, added at runtime.
//
// Instead of replacing resources.assets (205 MB), the plugin appends an eleventh language
// to the I2 Localization source right after it loads and fills it from pl.tsv next to this
// DLL. The original ten languages stay untouched and the game doesn't notice a change.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using I2.Loc;

namespace notgeese.Pedro
{
    // The release before the project rename had a different GUID. If its folder is still in
    // plugins, BepInEx skips this plugin instead of loading two translations at once.
    [BepInIncompatibility("cc.notgoose.myfriendpedro")]
    [BepInPlugin(Id, "My Friend Pedro PL", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string Id = "cc.notgeese.myfriendpedro";
        public const string Version = "0.1";

        internal const string LanguageName = "Polski";
        internal const string LanguageCode = "pl";
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
                UnityEngine.Application.version, UnityEngine.Application.unityVersion, Terms.Count));

            // If a future game version rearranges I2, the plugin must drop out quietly,
            // not crash the start. The game then stays English.
            try
            {
                var harmony = new Harmony(Id);
                harmony.PatchAll(typeof(SourcePatch));

                var patched = 0;
                foreach (var method in harmony.GetPatchedMethods()) patched++;
                if (patched == 0)
                {
                    Logger.LogError("No I2 hook points found; this game version differs from the expected one.");
                    return;
                }
                Logger.LogInfo("Patches applied: " + patched + ".");
            }
            catch (Exception error)
            {
                Logger.LogError("Could not hook into I2, the game stays English: " + error.Message);
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

    // I2 takes the global source straight from a prefab in Resources, so its Awake never
    // runs. Every source, prefab or scene, goes through LocalizationManager.AddSource,
    // which is the reliable hook.
    [HarmonyPatch]
    internal static class SourcePatch
    {
        [HarmonyPostfix]
        [HarmonyPatch(typeof(LocalizationManager), "AddSource")]
        private static void AfterAddSource(LanguageSource __0)
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

        private static void Apply(LanguageSource source)
        {
            try
            {
                Install(source);
            }
            catch (Exception error)
            {
                Plugin.Log.LogError("Could not add Polish: " + error);
            }
        }

        private static void Install(LanguageSource source)
        {
            if (source == null || source.mTerms == null || source.mTerms.Count == 0) return;

            // The game may have several sources; we want the one with our keys.
            var known = 0;
            foreach (var term in source.mTerms)
            {
                if (Plugin.Terms.ContainsKey(term.Term) && ++known > 4) break;
            }
            if (known == 0)
            {
                Plugin.Log.LogInfo("Skipping a source without our keys (" + source.mTerms.Count + " entries).");
                return;
            }

            // Idempotent: a source may wake more than once.
            foreach (var language in source.mLanguages)
            {
                if (string.Equals(language.Code, Plugin.LanguageCode, StringComparison.OrdinalIgnoreCase)) return;
            }

            var before = source.mLanguages.Count;
            source.AddLanguage(Plugin.LanguageName, Plugin.LanguageCode);
            var index = source.mLanguages.Count - 1;

            var filled = 0;
            var missing = 0;
            foreach (var term in source.mTerms)
            {
                string polish;
                if (!Plugin.Terms.TryGetValue(term.Term, out polish))
                {
                    missing++;
                    continue;
                }
                if (term.Languages != null && index < term.Languages.Length)
                {
                    term.Languages[index] = polish;
                    filled++;
                }
            }

            LocalizationManager.LocalizeAll(true);
            Plugin.Log.LogInfo(string.Format(
                "Polish added as language {0} of {1}: {2} texts, untranslated {3}.",
                index + 1, before + 1, filled, missing));

            // New texts after a game update stay English: not an error, a signal to translate them.
            if (missing > 0)
            {
                Plugin.Log.LogWarning(missing + " texts of this game version are not in the translation; they stay English.");
            }
        }
    }
}
