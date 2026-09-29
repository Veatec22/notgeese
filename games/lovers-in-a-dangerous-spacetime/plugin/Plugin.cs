// Not Geese: Polish for Lovers in a Dangerous Spacetime, added at runtime.
//
// The game lists its languages in Language.SupportedLanguages() and loads one LocalizationSet
// per language from Resources. The plugin adds a twelfth language, "Polski": when it is chosen,
// the English set is loaded and its dictionary is overlaid with pl.tsv next to this DLL.
// Game files stay untouched; keys missing from pl.tsv stay English.
// A few texts live outside the tables (credits headings, the end screen); static.tsv maps their
// exact English to Polish and the plugin swaps them when those screens start.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using UnityEngine;

namespace notgeese.Lovers
{
    [BepInPlugin(Id, "Lovers in a Dangerous Spacetime PL", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string Id = "cc.notgeese.lovers";
        public const string Version = "0.1";

        internal const string TermsFile = "pl.tsv";
        internal const string StaticFile = "static.tsv";

        internal static ManualLogSource Log;
        internal static Dictionary<string, string> Terms;
        internal static Dictionary<string, string> StaticTexts;
        internal static Language Polish;

        private void Awake()
        {
            Log = Logger;
            Logger.LogInfo(string.Format("Game {0}, Unity {1}.", Application.version, Application.unityVersion));

            Terms = ReadTable(TermsFile);
            StaticTexts = ReadTable(StaticFile);
            if (Terms.Count == 0)
            {
                Logger.LogError("No texts found in " + TermsFile + "; Polish will not be added.");
                return;
            }

            // A future game version may rearrange the localizer; then the plugin drops out
            // quietly and the game stays as it was.
            try
            {
                Polish = new Language("Polski", "pl-pl", SystemLanguage.Polish);

                var harmony = new Harmony(Id);
                harmony.PatchAll(typeof(LanguagePatches));
                // Credits and end screen are extras: if they moved, the language still works.
                try
                {
                    harmony.PatchAll(typeof(ScreenPatches));
                }
                catch (Exception error)
                {
                    Logger.LogWarning("Credits and end screen stay English: " + error.Message);
                }

                var patched = 0;
                foreach (var method in harmony.GetPatchedMethods()) patched++;
                Logger.LogInfo(string.Format("Loaded {0} entries and {1} screen texts, patches applied: {2}.",
                    Terms.Count, StaticTexts.Count, patched));

                AddToExistingLocalizer();
            }
            catch (Exception error)
            {
                Logger.LogError("Could not hook into the localizer, the game stays as it was: " + error);
            }
        }

        /// The localizer is created lazily; if something touched it before the plugin loaded,
        /// its language list was built without Polish.
        private void AddToExistingLocalizer()
        {
            var field = AccessTools.Field(typeof(Localizer), "_sharedInstance");
            var localizer = field == null ? null : field.GetValue(null) as Localizer;
            if (localizer == null) return;

            var languages = localizer.supportedLanguages;
            if (Array.IndexOf(languages, Polish) >= 0) return;
            var extended = new Language[languages.Length + 1];
            languages.CopyTo(extended, 0);
            extended[languages.Length] = Polish;
            AccessTools.Property(typeof(Localizer), "supportedLanguages").SetValue(localizer, extended, null);
            Logger.LogInfo("Localizer existed before the plugin; Polish added to its list.");
        }

        internal static bool PolishActive
        {
            get { return Polish != null && Localizer.SharedInstance.currentLanguage == Polish; }
        }

        /// Polish for a text found on screen, or null. Compared without surrounding whitespace.
        internal static string StaticPolish(string english)
        {
            if (english == null || StaticTexts == null) return null;
            string polish;
            return StaticTexts.TryGetValue(english.Trim(), out polish) ? polish : null;
        }

        /// File next to the DLL: key (or English text), tab, text. Newlines stored as \n.
        private Dictionary<string, string> ReadTable(string name)
        {
            var terms = new Dictionary<string, string>(StringComparer.Ordinal);
            var folder = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            var path = Path.Combine(folder, name);

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
                terms[line.Substring(0, tab).Replace("\\n", "\n")] = line.Substring(tab + 1).TrimEnd('\r').Replace("\\n", "\n");
            }

            return terms;
        }
    }

    [HarmonyPatch]
    internal static class LanguagePatches
    {
        // Set only while SetCurrentLanguage(Polish) runs: the English set it loads gets our overlay.
        private static bool loadingPolish;

        [HarmonyPostfix]
        [HarmonyPatch(typeof(Language), "SupportedLanguages")]
        private static void AddPolish(ref Language[] __result)
        {
            if (__result == null || Array.IndexOf(__result, Plugin.Polish) >= 0) return;
            var extended = new Language[__result.Length + 1];
            __result.CopyTo(extended, 0);
            extended[__result.Length] = Plugin.Polish;
            __result = extended;
        }

        // Per-platform whitelist of system languages; Polish is on no list.
        [HarmonyPostfix]
        [HarmonyPatch(typeof(PlatformLocalizationSupport), "PlatformSupportsLanguage")]
        private static void AllowPolish(SystemLanguage __0, ref bool __result)
        {
            if (__0 == SystemLanguage.Polish) __result = true;
        }

        // First start on a Polish system picks Polish, as the game does for its own languages.
        [HarmonyPostfix]
        [HarmonyPatch(typeof(Localizer), "languageFromSystemLanguage")]
        private static void PolishSystem(SystemLanguage __0, ref Language __result)
        {
            if (__0 == SystemLanguage.Polish) __result = Plugin.Polish;
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(Localizer), "SetCurrentLanguage", typeof(Language))]
        private static void BeforeSetLanguage(Language __0)
        {
            loadingPolish = __0 == Plugin.Polish;
        }

        [HarmonyFinalizer]
        [HarmonyPatch(typeof(Localizer), "SetCurrentLanguage", typeof(Language))]
        private static void AfterSetLanguage()
        {
            loadingPolish = false;
        }

        // There is no Localization-pl-pl resource: Polish loads the English set.
        [HarmonyPostfix]
        [HarmonyPatch(typeof(Localizer), "localizationPath", typeof(Language))]
        private static void EnglishPathForPolish(Language __0, ref string __result)
        {
            if (__0 == Plugin.Polish) __result = __result.Substring(0, __result.Length - Plugin.Polish.code.Length) + Language.en_us.code;
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(LocalizationSet), "GenerateDictionaryRepresentation")]
        private static void Overlay(Dictionary<string, string> __result)
        {
            if (!loadingPolish || __result == null) return;
            try
            {
                var filled = 0;
                var keys = new List<string>(__result.Keys);
                foreach (var key in keys)
                {
                    string polish;
                    if (!Plugin.Terms.TryGetValue(key, out polish)) continue;
                    __result[key] = polish;
                    filled++;
                }
                var missing = keys.Count - filled;
                Plugin.Log.LogInfo(string.Format("Polish active: {0} of {1} texts.", filled, keys.Count));
                // New texts after a game update stay English: not an error, a signal to translate them.
                if (missing > 0) Plugin.Log.LogWarning(missing + " texts are not in the translation; they stay English.");
            }
            catch (Exception error)
            {
                Plugin.Log.LogError("Could not apply Polish texts: " + error);
            }
        }
    }

    // Texts the game never sends through its localizer.
    [HarmonyPatch]
    internal static class ScreenPatches
    {
        // End screen: game over / victory labels are set from string constants.
        [HarmonyPostfix]
        [HarmonyPatch(typeof(ThanksForPlayingController), "Setup")]
        private static void EndScreen(ThanksForPlayingController __instance)
        {
            if (!Plugin.PolishActive) return;
            Swap(__instance.topLabel);
            Swap(__instance.bottomLabel);
        }

        // Credits: headings are plain UI texts in the scene; names stay as they are.
        [HarmonyPostfix]
        [HarmonyPatch(typeof(CreditsController), "Start")]
        private static void Credits(CreditsController __instance)
        {
            if (!Plugin.PolishActive || __instance.creditsContainer == null) return;
            var swapped = 0;
            foreach (var text in __instance.creditsContainer.GetComponentsInChildren<UnityEngine.UI.Text>(true))
            {
                var polish = Plugin.StaticPolish(text.text);
                if (polish == null) continue;
                text.text = polish;
                swapped++;
            }
            Plugin.Log.LogInfo("Credits: " + swapped + " headings in Polish.");
        }

        private static void Swap(TextMesh label)
        {
            if (label == null) return;
            var polish = Plugin.StaticPolish(label.text);
            if (polish != null) label.text = polish;
        }
    }
}
