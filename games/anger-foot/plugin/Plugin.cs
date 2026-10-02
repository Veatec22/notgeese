// Not Geese: Polish for Anger Foot, added at runtime.
//
// The game has twelve translation slots; Italian is empty and hidden from the menu.
// The plugin renames that record to Polish and enables it, and swaps texts on the
// fly by intercepting LocalizedString.GetTranslation.
// No game file is replaced.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;

namespace notgeese.AngerFoot
{
    // The release before the project rename had a different GUID. If its folder is still in
    // plugins, BepInEx skips this plugin instead of loading two translations at once.
    [BepInIncompatibility("cc.notgoose.angerfoot")]
    [BepInPlugin(Id, "Anger Foot PL", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string Id = "cc.notgeese.angerfoot";
        public const string Version = "0.2";

        internal const string TermsFile = "pl.tsv";
        internal const string LanguageName = "Polski";
        internal const string LanguageTag = "pl";

        internal static ManualLogSource Log;
        internal static Dictionary<string, string> Terms;

        private void Awake()
        {
            Log = Logger;
            Logger.LogInfo(string.Format("Game {0}, Unity {1}.",
                UnityEngine.Application.productName, UnityEngine.Application.unityVersion));

            Terms = ReadTerms();
            if (Terms.Count == 0)
            {
                Logger.LogError("No texts found in " + TermsFile + "; Polish will not be added.");
                return;
            }

            try
            {
                var harmony = new Harmony(Id);
                harmony.PatchAll(typeof(LanguagePatch));
                harmony.PatchAll(typeof(TranslationPatch));

                var patched = 0;
                foreach (var method in harmony.GetPatchedMethods()) patched++;
                if (patched == 0)
                {
                    Logger.LogError("No hook points found; this game version differs from the expected one.");
                    return;
                }
                Logger.LogInfo("Loaded " + Terms.Count + " entries, patches applied: " + patched + ".");
            }
            catch (Exception error)
            {
                Logger.LogError("Could not hook into localization, the game stays English: " + error.Message);
            }
        }

        /// File next to the library: entry GUID, tab, text. Newlines as \n.
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

    /// The empty Italian slot becomes Polish. The spreadsheet key stays "ITALIAN",
    /// because the game derives each entry's translation position from it.
    [HarmonyPatch(typeof(LocalizationManager), "Initialize")]
    internal static class LanguagePatch
    {
        private static void Prefix()
        {
            try
            {
                var italian = LocalizationLanguage.Italian;
                if (italian == null)
                {
                    Plugin.Log.LogError("No Italian language record; nothing to rename.");
                    return;
                }
                if (italian.NativeName == Plugin.LanguageName) return;

                italian.NativeName = Plugin.LanguageName;
                italian.LanguageTag = Plugin.LanguageTag;
                italian.Supported = true;
                Plugin.Log.LogInfo("Italian slot renamed to Polish and enabled in the menu.");
            }
            catch (Exception error)
            {
                Plugin.Log.LogError("Could not enable Polish: " + error);
            }
        }
    }

    /// On-the-fly text swap: entries are recognized by GUID because terms
    /// repeat across categories (1518 unique of 1776 entries).
    [HarmonyPatch(typeof(LocalizedString), "GetTranslation")]
    internal static class TranslationPatch
    {
        private static int _served;
        private static int _missing;

        private static void Postfix(LocalizedString __instance, ref string __result)
        {
            try
            {
                if (__instance == null) return;
                if (LocalizationManager.CurrentLanguage != LocalizationLanguage.Italian) return;

                string polish;
                if (Plugin.Terms.TryGetValue(__instance.GUID, out polish))
                {
                    __result = polish;
                    if (++_served == 1) Plugin.Log.LogInfo("First Polish text served to the game.");
                }
                else if (++_missing <= 5)
                {
                    Plugin.Log.LogWarning("Untranslated: " + __instance.Term + " (" + __instance.GUID + ")");
                }
            }
            catch (Exception error)
            {
                Plugin.Log.LogError("Text swap error: " + error.Message);
            }
        }
    }
}
