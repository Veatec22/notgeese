// Not Geese: Polish for Children of the Sun, supplied at runtime.
//
// Every game text goes through LocalisationSystem.GetLocalisedValue(key, field, big), which
// reads the Unity Localization table "LOL" and puts the result into the TMP field. Polish is a
// layer over English: the game stays on locale "en" (its fonts, layout, saved language) and the
// plugin swaps the result for keys it has in pl.tsv; what we lack stays English.
// Options → Language gets "Polski" at the end of the dropdown; choosing it selects English in
// the game and turns the layer on. The choice is kept in our own PlayerPrefs key. Static TMP
// atlases lack Polish letters; PolishGlyphs composes them from the player's own fonts.
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
using UnityEngine.Localization.Settings;

namespace notgeese.ChildrenOfTheSun
{
    [BepInPlugin(Id, "Children of the Sun PL", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string Id = "cc.notgeese.childrenofthesun";
        public const string Version = "0.2";

        internal const string MenuName = "Polski";
        internal const string EnglishCode = "en";
        internal const string PolishKey = "notgeese.ChildrenOfTheSun.Polish";
        internal const string TermsFile = "pl.tsv";

        internal static ManualLogSource Log;

        /// Table key → Polish text.
        internal static Dictionary<string, string> Terms;

        /// Player chose Polski; applies only while the game's locale is English.
        internal static bool Chosen;

        private void Awake()
        {
            Log = Logger;
            Logger.LogInfo(string.Format("PL {0}; game {1} {2}, Unity {3}.", Version,
                Application.productName, Application.version, Application.unityVersion));

            Terms = ReadTerms();
            if (Terms.Count == 0)
            {
                Logger.LogError("No texts found in " + TermsFile + "; Polish will not appear in the language list.");
                return;
            }
            try { Chosen = PlayerPrefs.GetInt(PolishKey, 0) == 1; }
            catch (Exception) { Chosen = false; }

            // The splash screen runs before any scene: swap its logos as early as we can.
            if (Chosen)
            {
                try { SplashLogos.Replace(); }
                catch (Exception error) { Logger.LogWarning("Splash logos: " + error.Message); }
            }

            try
            {
                var harmony = new Harmony(Id);
                harmony.PatchAll(typeof(TextPatch));
                harmony.PatchAll(typeof(MenuPatch));
                UnityEngine.SceneManagement.SceneManager.sceneLoaded += (scene, mode) => Fonts.Refresh();
                var patched = 0;
                foreach (var method in harmony.GetPatchedMethods()) patched++;
                Logger.LogInfo("Loaded " + Terms.Count + " entries, patches applied: " + patched
                    + ", Polish " + (Chosen ? "chosen" : "not chosen") + ".");
            }
            catch (Exception error)
            {
                Logger.LogError("Could not hook into the language system, no Polish: " + error.Message);
            }
        }

        /// File next to the DLL: key, tab, text; line breaks as \n.
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

        internal static bool PolishActive()
        {
            if (!Chosen) return false;
            var locale = LocalizationSettings.SelectedLocale;
            return locale != null && locale.Identifier.Code == EnglishCode;
        }

        internal static void Choose(bool polish)
        {
            if (Chosen == polish) return;
            Chosen = polish;
            try
            {
                PlayerPrefs.SetInt(PolishKey, polish ? 1 : 0);
                PlayerPrefs.Save();
            }
            catch (Exception error)
            {
                Log.LogWarning("Could not save the language choice: " + error.Message);
            }
            Log.LogInfo(polish ? "Polish on." : "Polish off.");
        }

        /// Texts already on screen: the locale may not change (English → Polski), so the game
        /// sends no event; ask each LocalizeText to read its key again.
        internal static void RefreshTexts()
        {
            Fonts.Refresh();
            var update = AccessTools.Method(typeof(LocalizeText), "UpdateText");
            if (update == null) return;
            foreach (var text in UnityEngine.Object.FindObjectsOfType<LocalizeText>())
            {
                try { update.Invoke(text, null); }
                catch (Exception error) { Log.LogWarning("Text refresh: " + error.Message); }
            }
        }
    }

    [HarmonyPatch]
    internal static class TextPatch
    {
        private static readonly HashSet<string> Missing = new HashSet<string>(StringComparer.Ordinal);

        [HarmonyPrefix]
        [HarmonyPatch(typeof(LocalisationSystem), "GetLocalisedValue")]
        private static void Before()
        {
            if (Fonts.Pending) Fonts.Refresh();
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(LocalisationSystem), "GetLocalisedValue")]
        private static void After(string __0, TMPro.TextMeshProUGUI __1, ref string __result)
        {
            var key = __0;
            if (key == null || !Plugin.PolishActive()) return;
            string polish;
            if (!Plugin.Terms.TryGetValue(key, out polish))
            {
                if (Missing.Add(key)) Plugin.Log.LogInfo("No Polish for \"" + key + "\" (" + Missing.Count + " so far), English stays.");
                return;
            }
            __result = polish;
            if (__1 != null) __1.text = polish;
        }

        // Fonts arrive from scenes at different times. A new font only marks that there is work;
        // letters are composed before the next text lookup.
        [HarmonyPostfix]
        [HarmonyPatch(typeof(TMP_FontAsset), "Awake")]
        private static void FontLoaded()
        {
            Fonts.Pending = true;
        }
    }

    /// Options → Language: a TMP dropdown filled from the game's locales (by English name);
    /// ChangeLanguage(index) selects locale index. "Polski" is one index past the last locale.
    [HarmonyPatch]
    internal static class MenuPatch
    {
        private static readonly AccessTools.FieldRef<OptionsMenu, TMP_Dropdown> Dropdown =
            AccessTools.FieldRefAccess<OptionsMenu, TMP_Dropdown>("languageDropdown");

        /// Above zero while the game itself sets the language (menu start, saved settings).
        private static int loading;

        private static int PolishIndex()
        {
            return LocalizationSettings.AvailableLocales.Locales.Count;
        }

        private static int EnglishIndex()
        {
            var locales = LocalizationSettings.AvailableLocales.Locales;
            for (var i = 0; i < locales.Count; i++)
                if (locales[i] != null && locales[i].Identifier.Code == Plugin.EnglishCode) return i;
            return -1;
        }

        private static void ShowChoice(OptionsMenu menu)
        {
            var dropdown = Dropdown(menu);
            if (dropdown == null) return;
            var index = PolishIndex();
            if (dropdown.options.Count == index)
                dropdown.options.Add(new TMP_Dropdown.OptionData(Plugin.MenuName));
            if (dropdown.options.Count <= index) return;
            if (Plugin.PolishActive()) dropdown.SetValueWithoutNotify(index);
            dropdown.RefreshShownValue();
        }

        // Start fills the list and sets its value (set_value notifies: ChangeLanguage with the
        // current locale), then loads saved settings (ChangeLanguage with the saved locale).
        // Neither is the player leaving Polish. Counted, because Start calls the loader.
        [HarmonyPrefix]
        [HarmonyPatch(typeof(OptionsMenu), "Start")]
        private static void Starting()
        {
            loading++;
        }

        [HarmonyFinalizer]
        [HarmonyPatch(typeof(OptionsMenu), "Start")]
        private static void StartEnds()
        {
            loading--;
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(OptionsMenu), "Start")]
        private static void Started(OptionsMenu __instance)
        {
            try
            {
                ShowChoice(__instance);
                Plugin.RefreshTexts();
            }
            catch (Exception error)
            {
                Plugin.Log.LogWarning("Language list: " + error.Message);
            }
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(OptionsMenu), "LoadAndSetPlayerPrefs")]
        private static void LoadingStarts()
        {
            loading++;
        }

        [HarmonyFinalizer]
        [HarmonyPatch(typeof(OptionsMenu), "LoadAndSetPlayerPrefs")]
        private static void LoadingEnds(OptionsMenu __instance)
        {
            loading--;
            try { ShowChoice(__instance); }
            catch (Exception error) { Plugin.Log.LogWarning("Language list: " + error.Message); }
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(OptionsMenu), "ChangeLanguage")]
        private static void Changing(ref int __0)
        {
            if (__0 == PolishIndex())
            {
                var english = EnglishIndex();
                if (english < 0)
                {
                    Plugin.Log.LogWarning("No English locale in the game; Polish unavailable.");
                    __0 = 0;
                    return;
                }
                Plugin.Choose(true);
                __0 = english;
            }
            else if (loading == 0)
            {
                Plugin.Choose(false);
            }
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(OptionsMenu), "ChangeLanguage")]
        private static void Changed()
        {
            if (loading == 0) Plugin.RefreshTexts();
        }
    }

    internal static class Fonts
    {
        internal static bool Pending = true;

        internal static void Refresh()
        {
            try
            {
                if (!Plugin.PolishActive()) return;
                Pending = false;
                if (PolishGlyphs.PatchLoadedFonts() == 0) return;
                // Texts laid out before the patch would keep showing boxes instead of letters.
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
