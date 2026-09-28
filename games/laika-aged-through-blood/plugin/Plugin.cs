// Not Geese: Polish for Laika: Aged Through Blood, supplied at runtime.
//
// The game uses M2H Localization: a text sheet is the TextAsset "Languages/<CODE>_<SHEET>"
// in Resources, and the language list comes from the LanguageCode enum (which has PL) by
// checking whether the code's first sheet exists. The plugin tells the game PL sheets exist
// and serves them from pl.tsv, built on the English ones: what we lack stays English.
// In options it adds "POLSKI" to the language list. The game itself remembers the choice
// (PlayerPrefs "M2H_lastLanguage"). No game file is replaced.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Security;
using System.Text;
using System.Xml;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using TMPro;
using UnityEngine;
using SettingsViewItem = Laika.UI.Settings.SettingsViewItem;

namespace notgeese.Laika
{
    // The release before the project rename had a different GUID. If its folder is still in
    // plugins, BepInEx skips this plugin instead of loading two translations at once.
    [BepInIncompatibility("cc.notgoose.laika")]
    [BepInPlugin(Id, "Laika PL", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string Id = "cc.notgeese.laika";
        public const string Version = "0.1";

        internal const string Code = "PL";
        internal const string MenuName = "POLSKI";
        internal const string TermsFile = "pl.tsv";

        internal static ManualLogSource Log;

        /// Game key → Polish text.
        internal static Dictionary<string, string> Terms;

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

            // Patching the Language class can run its static constructor before the
            // HasLanguageFile patch works: the game then builds the language list without PL,
            // can't restore a saved PL and overwrites it in PlayerPrefs. So we read it first
            // and switch back after the first scene loads.
            try { saved = PlayerPrefs.GetString(LastLanguageKey, ""); }
            catch (Exception) { saved = ""; }

            try
            {
                var harmony = new Harmony(Id);
                harmony.PatchAll(typeof(LanguagePatch));
                harmony.PatchAll(typeof(MenuPatch));
                UnityEngine.SceneManagement.SceneManager.sceneLoaded += (scene, mode) =>
                {
                    RestoreSaved();
                    Fonts.Refresh();
                };
                var patched = 0;
                foreach (var method in harmony.GetPatchedMethods()) patched++;
                Logger.LogInfo("Loaded " + Terms.Count + " entries, patches applied: " + patched + ".");
            }
            catch (Exception error)
            {
                Logger.LogError("Could not hook into the language system, no Polish: " + error.Message);
            }
        }

        /// File next to the DLL: key, tab, text.
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
                terms[entry.Substring(0, tab)] = entry.Substring(tab + 1);
            }
            return terms;
        }

        internal const string LastLanguageKey = "M2H_lastLanguage";
        private static string saved;

        private static void RestoreSaved()
        {
            if (saved != Code) return;
            saved = null;
            try
            {
                if (Language.CurrentLanguage().ToString() == Code) return;
                Log.LogInfo("Restoring saved language PL.");
                Language.SwitchLanguage(Code);
            }
            catch (Exception error)
            {
                Log.LogWarning("Could not restore Polish: " + error.Message);
            }
        }

        private static readonly AccessTools.FieldRef<List<string>> Available =
            AccessTools.StaticFieldRefAccess<List<string>>(AccessTools.Field(typeof(Language), "availableLanguages"));

        /// The M2H language list must contain PL, or Language.SwitchLanguage refuses.
        internal static void EnsureAvailable()
        {
            var list = Available();
            if (list == null || list.Contains(Code)) return;
            list.Add(Code);
            Log.LogInfo("Game language list was built without PL; added.");
        }

        internal static bool PolishActive()
        {
            return Terms != null && Language.CurrentLanguage().ToString() == Code;
        }
    }

    /// PL sheets: the game's English XML with the texts we have replaced.
    internal static class Sheets
    {
        private static readonly Dictionary<string, string> Cache = new Dictionary<string, string>();
        private static readonly HashSet<string> Reported = new HashSet<string>();

        internal static TextAsset English(string sheet)
        {
            return Resources.Load("Languages/EN_" + sheet, typeof(TextAsset)) as TextAsset;
        }

        internal static string Build(string sheet)
        {
            string xml;
            if (Cache.TryGetValue(sheet, out xml)) return xml;
            var english = English(sheet);
            if (english == null) return "";

            var output = new StringBuilder(english.text.Length + 1024);
            output.Append("<entries>\n");
            int total = 0, missing = 0;
            using (var reader = XmlReader.Create(new StringReader(english.text)))
            {
                while (reader.ReadToFollowing("entry"))
                {
                    var key = reader.GetAttribute("name");
                    var text = reader.ReadElementContentAsString();
                    if (key == null) continue;
                    string polish;
                    if (Plugin.Terms.TryGetValue(key, out polish)) text = polish;
                    else if (text.Trim().Length > 0) missing++;
                    total++;
                    output.Append("<entry name=\"").Append(SecurityElement.Escape(key)).Append("\">")
                        .Append(SecurityElement.Escape(text)).Append("</entry>\n");
                }
            }
            // Options highlight the current language by the name in UI_SETTINGS_LANGUAGE_<CODE>,
            // which the English sheet naturally lacks for PL.
            if (sheet == "UI")
                output.Append("<entry name=\"UI_SETTINGS_LANGUAGE_").Append(Plugin.Code).Append("\">")
                    .Append(Plugin.MenuName).Append("</entry>\n");
            output.Append("</entries>\n");
            xml = output.ToString();
            Cache[sheet] = xml;

            if (Reported.Add(sheet))
            {
                if (missing > 0)
                    Plugin.Log.LogWarning(string.Format("Sheet {0}: {1} of {2} texts without Polish translation; they stay English.",
                        sheet, missing, total));
                else
                    Plugin.Log.LogInfo(string.Format("Sheet {0}: all {1} texts in Polish.", sheet, total));
            }
            return xml;
        }
    }

    [HarmonyPatch]
    internal static class LanguagePatch
    {
        // Game language list: PL "exists" if the matching English sheet exists.
        [HarmonyPrefix]
        [HarmonyPatch(typeof(Language), "HasLanguageFile")]
        private static bool HasLanguageFile(string lang, string sheetTitle, ref bool __result)
        {
            if (lang != Plugin.Code) return true;
            __result = Sheets.English(sheetTitle) != null;
            return false;
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(Language), "SwitchLanguage", new[] { typeof(LanguageCode) })]
        private static void BeforeSwitch()
        {
            try { Plugin.EnsureAvailable(); }
            catch (Exception error) { Plugin.Log.LogWarning("Language list: " + error.Message); }
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(Language), "GetLanguageFileContents")]
        private static bool GetLanguageFileContents(string sheetTitle, ref string __result)
        {
            if (!Plugin.PolishActive()) return true;
            try
            {
                __result = Sheets.Build(sheetTitle);
                return false;
            }
            catch (Exception error)
            {
                Plugin.Log.LogError("Sheet " + sheetTitle + ": " + error.Message + "; stays English.");
                var english = Sheets.English(sheetTitle);
                __result = english != null ? english.text : "";
                return false;
            }
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(Language), "DoSwitch")]
        private static void Switched()
        {
            Plugin.Log.LogInfo("Game language: " + Language.CurrentLanguage());
            Fonts.Refresh();
        }

        // Fonts arrive from scenes and assets at different times. A new font only marks that
        // there is work; letters are composed before the next text lookup.
        [HarmonyPostfix]
        [HarmonyPatch(typeof(TMP_FontAsset), "Awake")]
        private static void FontLoaded()
        {
            Fonts.Pending = true;
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(Language), "Get", new[] { typeof(string), typeof(string) })]
        private static void BeforeGet()
        {
            if (Fonts.Pending) Fonts.Refresh();
        }
    }

    /// Options → Language: names and codes are two parallel lists hardcoded in the game.
    [HarmonyPatch]
    internal static class MenuPatch
    {
        private static readonly AccessTools.FieldRef<SettingsViewItem, List<string>> Codes =
            AccessTools.FieldRefAccess<SettingsViewItem, List<string>>("languageCodes");

        [HarmonyPostfix]
        [HarmonyPatch(typeof(SettingsViewItem), "LanguageNamesList", MethodType.Getter)]
        private static void Names(ref List<string> __result)
        {
            if (__result != null && !__result.Contains(Plugin.MenuName)) __result.Add(Plugin.MenuName);
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(SettingsViewItem), "SetLayout")]
        private static void SetLayout(SettingsViewItem __instance)
        {
            var codes = Codes(__instance);
            if (codes != null && !codes.Contains(Plugin.Code)) codes.Add(Plugin.Code);
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
