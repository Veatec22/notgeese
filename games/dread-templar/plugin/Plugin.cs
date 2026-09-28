// Not Geese: Polish for Dread Templar, added at runtime.
//
// The game data has an empty "pol" block left by the developers, and a disabled
// Italian button parked next to the language grid in the options menu.
// The plugin fills the first from pl.tsv and revives and renames the second,
// instead of replacing 35 game files weighing 789 MB.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using UnityEngine;

namespace notgeese.DreadTemplar
{
    // The release before the project rename had a different GUID. If its folder is still in
    // plugins, BepInEx skips this plugin instead of loading two translations at once.
    [BepInIncompatibility("cc.notgoose.dreadtemplar")]
    [BepInPlugin(Id, "Dread Templar PL", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string Id = "cc.notgeese.dreadtemplar";
        public const string Version = "0.1";

        internal const string LanguageCode = "pol";
        internal const string LanguageLabel = "Polski";
        internal const string TermsFile = "pl.tsv";

        /// Names from the scene hierarchy.
        internal const string ParkedButton = "LanguagePick_ita_03";
        internal const string ToggleGrid = "Language_ToggleGroup";

        internal static ManualLogSource Log;
        internal static Dictionary<string, string> Texts;
        internal static Dictionary<string, string> Names;

        private void Awake()
        {
            Log = Logger;
            Logger.LogInfo(string.Format("Game {0}, Unity {1}.",
                Application.productName, Application.unityVersion));

            Texts = new Dictionary<string, string>(StringComparer.Ordinal);
            Names = new Dictionary<string, string>(StringComparer.Ordinal);
            ReadTerms();
            if (Texts.Count == 0)
            {
                Logger.LogError("No texts found in " + TermsFile + "; Polish will not be added.");
                return;
            }

            try
            {
                var harmony = new Harmony(Id);
                harmony.PatchAll(typeof(TextPatch));
                harmony.PatchAll(typeof(NamePatch));
                harmony.PatchAll(typeof(MenuPatch));

                var patched = 0;
                foreach (var method in harmony.GetPatchedMethods()) patched++;
                if (patched == 0)
                {
                    Logger.LogError("No hook points found; this game version differs from the expected one.");
                    return;
                }
                Logger.LogInfo(string.Format("Loaded {0} texts and {1} names, patches applied: {2}.",
                    Texts.Count, Names.Count, patched));
            }
            catch (Exception error)
            {
                Logger.LogError("Could not hook into texts, the game stays English: " + error.Message);
            }
        }

        /// File next to the library: entry kind, category/key, text.
        /// Kind is "t" for content or "n" for a speaker name.
        private void ReadTerms()
        {
            var folder = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            var path = Path.Combine(folder, TermsFile);
            if (!File.Exists(path))
            {
                Logger.LogError("Missing file " + path);
                return;
            }

            foreach (var line in File.ReadAllText(path).Split('\n'))
            {
                var parts = line.Split('\t');
                if (parts.Length < 3 || parts[1].Length == 0) continue;
                var value = Unescape(parts[2]);
                if (parts[0] == "n") Names[parts[1]] = value;
                else Texts[parts[1]] = value;
            }
        }

        /// Inverse of escape() in build_plugin.py.
        private static string Unescape(string value)
        {
            if (value.IndexOf('\\') < 0) return value;

            var text = new StringBuilder(value.Length);
            for (var i = 0; i < value.Length; i++)
            {
                if (value[i] != '\\' || i + 1 >= value.Length)
                {
                    text.Append(value[i]);
                    continue;
                }
                i++;
                if (value[i] == 'n') text.Append('\n');
                else if (value[i] == 't') text.Append('\t');
                else text.Append(value[i]);
            }
            return text.ToString();
        }

        internal static bool PolishActive()
        {
            try
            {
                var vars = GlobalVars.instance;
                return vars != null && vars.curLanguage == LanguageCode;
            }
            catch
            {
                return false;
            }
        }
    }

    [HarmonyPatch(typeof(GlobalTextCtrl), "GetText")]
    internal static class TextPatch
    {
        private static int _served;
        private static int _missing;

        private static void Postfix(string type, string id, ref string __result)
        {
            if (!Plugin.PolishActive()) return;

            string polish;
            if (Plugin.Texts.TryGetValue(type + "/" + id, out polish))
            {
                __result = polish;
                if (++_served == 1) Plugin.Log.LogInfo("First Polish text served to the game.");
            }
            else if (++_missing <= 5)
            {
                Plugin.Log.LogWarning("Untranslated: " + type + "/" + id);
            }
        }
    }

    [HarmonyPatch(typeof(GlobalTextCtrl), "GetTextName")]
    internal static class NamePatch
    {
        private static void Postfix(string type, string id, ref string __result)
        {
            if (!Plugin.PolishActive()) return;

            string polish;
            if (Plugin.Names.TryGetValue(type + "/" + id, out polish)) __result = polish;
        }
    }

    /// The Italian button sits disabled next to the language grid in every scene.
    /// We revive it, rename it to Polish and put it into the grid.
    [HarmonyPatch(typeof(LanguageToggleGroup), "OnEnable")]
    internal static class MenuPatch
    {
        private static void Postfix(LanguageToggleGroup __instance)
        {
            try
            {
                Install(__instance);
            }
            catch (Exception error)
            {
                Plugin.Log.LogError("Could not revive the Polish button: " + error);
            }
        }

        private static void Install(LanguageToggleGroup group)
        {
            var button = FindInactive(Plugin.ParkedButton);
            if (button == null)
            {
                Plugin.Log.LogWarning("Parked button not found: " + Plugin.ParkedButton + ".");
                return;
            }

            var mapping = button.GetComponent<LanguageMapToggle>();
            if (mapping == null)
            {
                Plugin.Log.LogWarning("The button has no language picker component.");
                return;
            }

            var languageField = typeof(LanguageMapToggle).GetField("_language",
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            if (languageField == null)
            {
                Plugin.Log.LogWarning("The language picker component has no language code field.");
                return;
            }

            var already = Plugin.LanguageCode.Equals(languageField.GetValue(mapping) as string, StringComparison.Ordinal);
            if (already && button.activeSelf) return;

            languageField.SetValue(mapping, Plugin.LanguageCode);
            SetLabel(button);

            var grid = group.transform;
            if (button.transform.parent != grid) button.transform.SetParent(grid, false);
            button.SetActive(true);

            Plugin.Log.LogInfo("Polish button revived and put into the language grid.");
        }

        /// The label sits in a child text object; reached without binding to
        /// TextMeshPro, the "text" property is enough.
        private static void SetLabel(GameObject button)
        {
            foreach (var component in button.GetComponentsInChildren<Component>(true))
            {
                if (component == null) continue;
                var property = component.GetType().GetProperty("text", typeof(string));
                if (property == null || !property.CanWrite) continue;

                var current = property.GetValue(component, null) as string;
                if (string.IsNullOrEmpty(current)) continue;
                if (current == Plugin.LanguageLabel) return;

                property.SetValue(component, Plugin.LanguageLabel, null);
                return;
            }
            Plugin.Log.LogWarning("Button label not found; it stays Italian.");
        }

        /// GameObject.Find can't see disabled objects, and ours is one.
        private static GameObject FindInactive(string name)
        {
            foreach (var transform in Resources.FindObjectsOfTypeAll<Transform>())
            {
                if (transform != null && transform.name == name && transform.hideFlags == HideFlags.None)
                {
                    return transform.gameObject;
                }
            }
            return null;
        }
    }
}
