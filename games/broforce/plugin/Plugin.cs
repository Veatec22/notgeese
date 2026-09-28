// Not Geese: Polish for Broforce, added at runtime.
//
// The game has its own language system (Localisation.LanguageManager): a code list
// in LanguageManagerConfig and one text bank per language in resources.assets.
// The plugin adds "pl" to the list, loads the English banks for "pl",
// and GetLocalisedString returns text from pl.tsv. Game files stay untouched.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using Localisation;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace notgeese.Broforce
{
    // The release before the project rename had a different GUID. If its folder is still in
    // plugins, BepInEx skips this plugin instead of loading two translations at once.
    [BepInIncompatibility("cc.notgoose.broforce")]
    [BepInPlugin(Id, "Broforce PL", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string Id = "cc.notgeese.broforce";
        public const string Version = "0.1";

        internal const string LanguageCode = "pl";
        internal const string LanguageName = "Polski";
        internal const string SourceLanguage = "en";
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

            // If a future game version rebuilds the language system, the plugin must drop out
            // quietly, not crash the launch. The game then stays English.
            try
            {
                var harmony = new Harmony(Id);
                harmony.PatchAll(typeof(LanguagePatch));
                try
                {
                    harmony.PatchAll(typeof(PolishText3D));
                }
                catch (Exception error)
                {
                    Logger.LogWarning("3D titles will stay without Polish letters: " + error.Message);
                }

                var patched = 0;
                foreach (var method in harmony.GetPatchedMethods()) patched++;
                Logger.LogInfo("Patches applied: " + patched + ".");
            }
            catch (Exception error)
            {
                Logger.LogError("Could not hook into the language system, the game stays English: " + error);
                return;
            }

            SceneManager.sceneLoaded += (scene, mode) => PolishGlyphs.PatchLoadedFonts();
            PolishGlyphs.PatchLoadedFonts();
        }

        /// File next to the library: key, tab, text. Newlines stored as \n.
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

    [HarmonyPatch]
    internal static class LanguagePatch
    {
        private static readonly HashSet<string> Missing = new HashSet<string>(StringComparer.Ordinal);
        private static bool bankChecked;

        // Language list from the game config; the language menu is built straight from it.
        [HarmonyPostfix]
        [HarmonyPatch(typeof(LanguageManagerConfig), "get_Languages")]
        private static void AddLanguage(List<string> __result)
        {
            if (__result != null && !__result.Contains(Plugin.LanguageCode)) __result.Add(Plugin.LanguageCode);
        }

        // The game has no "pl" banks: English text, sprite, material and bubble banks are used.
        [HarmonyPrefix]
        [HarmonyPatch(typeof(LanguageManager), "LoadStringBank")]
        private static void StringBank(ref string __0) { UseSourceBank(ref __0); }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(LanguageManager), "LoadSpriteBank")]
        private static void SpriteBank(ref string __0) { UseSourceBank(ref __0); }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(LanguageManager), "LoadRawImageMaterialBank")]
        private static void RawImageMaterialBank(ref string __0) { UseSourceBank(ref __0); }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(LanguageManager), "LoadReactionBubbleConfigBank")]
        private static void ReactionBubbleConfigBank(ref string __0) { UseSourceBank(ref __0); }

        private static void UseSourceBank(ref string language)
        {
            if (language == Plugin.LanguageCode) language = Plugin.SourceLanguage;
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(LanguageManager), "LoadStringBank")]
        private static void CheckBank(LanguageManager __instance, bool __result)
        {
            if (bankChecked || !__result || Plugin.Terms == null) return;
            try
            {
                var bank = Traverse.Create(__instance).Field("stringBank").Field("languageValues").GetValue() as System.Collections.IList;
                if (bank == null) return;
                bankChecked = true;
                var missing = 0;
                foreach (var pair in bank)
                {
                    var key = Traverse.Create(pair).Field("key").GetValue<string>();
                    if (key != null && !Plugin.Terms.ContainsKey(key) && !key.StartsWith("LANGUAGE_", StringComparison.Ordinal)) missing++;
                }
                Plugin.Log.LogInfo(string.Format("Game text bank: {0} entries, without Polish {1}.", bank.Count, missing));
                // New texts after a game update stay English; not an error,
                // just a signal they are worth translating.
                if (missing > 0) Plugin.Log.LogWarning(missing + " texts of this game version are not in the translation; they stay English.");
            }
            catch (Exception error)
            {
                bankChecked = true;
                Plugin.Log.LogWarning("Could not count game texts: " + error.Message);
            }
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(LanguageManager), "GetLocalisedString")]
        private static void Translate(LanguageManager __instance, string __0, ref string __result)
        {
            if (string.IsNullOrEmpty(__0)) return;
            if (__0 == "LANGUAGE_NAME_" + Plugin.LanguageCode)
            {
                __result = Plugin.LanguageName;
                return;
            }
            if (Plugin.Terms == null || __instance == null || __instance.CurrentLanguage != Plugin.LanguageCode) return;

            string polish;
            if (Plugin.Terms.TryGetValue(__0, out polish))
            {
                __result = polish;
                PolishGlyphs.PatchLoadedFonts();
            }
            else if (!__0.StartsWith("LANGUAGE_", StringComparison.Ordinal) && Missing.Add(__0))
            {
                Plugin.Log.LogInfo("No Polish text: " + __0);
            }
        }

        // Polish system -> Polish at start, as the game does for its own languages.
        [HarmonyPostfix]
        [HarmonyPatch(typeof(LanguageManager), "GetSystemLanguage")]
        private static void SystemLanguage(ref string __result)
        {
            if (Application.systemLanguage == UnityEngine.SystemLanguage.Polish) __result = Plugin.LanguageCode;
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(LanguageManager), "ChangeLanguage")]
        private static void Changed(string __0)
        {
            if (__0 != null && __0.ToLowerInvariant() == Plugin.LanguageCode)
                Plugin.Log.LogInfo("Game language: Polish.");
        }
    }
}
