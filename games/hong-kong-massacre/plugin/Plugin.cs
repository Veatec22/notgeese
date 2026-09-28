// Not Geese: Polish for The Hong Kong Massacre, added at runtime.
//
// The game has no language system and only English. Texts are swapped in memory, no game
// file is touched:
//   1. Dialogue System database: the "Dialogue Text" field of each entry (dlg/<conv>/<id>);
//   2. UnityEngine.UI.Text labels from scenes, level data and code: exact English match
//      (ui/<text>), label + value patterns (fmt/<text with {0}>), also DOTween DOText targets;
//   3. Rewired control mapper LanguageData fields (rewired/<field>).
//
// Dialogue entries and Rewired fields carry a fingerprint of the English original. When a
// game update puts different text under the same key it stays English and the log says how
// many. The game's two main fonts lack some Polish letters; the missing ones come from a
// similar system font (Unity's dynamic font fallback).

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using System.Text.RegularExpressions;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using PixelCrushers.DialogueSystem;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace notgeese.HongKongMassacre
{
    [BepInPlugin(Id, "The Hong Kong Massacre PL", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string Id = "cc.notgeese.hongkongmassacre";
        public const string Version = "0.1";

        internal const string TermsFile = "pl.tsv";
        internal const string UntranslatedFile = "untranslated.txt";

        internal static ManualLogSource Log;
        internal static string Folder;

        private void Awake()
        {
            Log = Logger;
            Folder = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            Logger.LogInfo(string.Format("Game {0} {1}, Unity {2}.",
                Application.productName, Application.version, Application.unityVersion));

            if (!Texts.Load(Path.Combine(Folder, TermsFile))) return;

            var harmony = new Harmony(Id);
            Patch(harmony, typeof(TextPatch), "UI labels");
            Patch(harmony, typeof(DialoguePatch), "dialogue database");
            PatchDoText(harmony);

            SceneManager.sceneLoaded += OnSceneLoaded;
        }

        private void Patch(Harmony harmony, Type patches, string what)
        {
            try
            {
                harmony.PatchAll(patches);
            }
            catch (Exception error)
            {
                Logger.LogError("Could not hook " + what + ", this part stays English: " + error.Message);
            }
        }

        /// DOTween's typewriter tween for UI.Text keeps its own copy of the end text.
        private void PatchDoText(Harmony harmony)
        {
            try
            {
                var type = AccessTools.TypeByName("DG.Tweening.ShortcutExtensions46");
                var method = type == null ? null : AccessTools.Method(type, "DOText");
                if (method == null)
                {
                    Logger.LogWarning("DOTween DOText not found; animated labels stay English.");
                    return;
                }
                harmony.Patch(method, prefix: new HarmonyMethod(typeof(TextPatch), "BeforeDoText"));
            }
            catch (Exception error)
            {
                Logger.LogError("Could not hook DOTween: " + error.Message);
            }
        }

        private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            try
            {
                foreach (var database in Resources.FindObjectsOfTypeAll<DialogueDatabase>()) Texts.Translate(database);
                Texts.TranslateRewired();
                foreach (var text in Resources.FindObjectsOfTypeAll<Text>()) TextPatch.Replace(text);
                Fonts.Prepare();
                Texts.Report(scene.name);
            }
            catch (Exception error)
            {
                Logger.LogError("Error in scene " + scene.name + ": " + error);
            }
        }
    }

    internal static class Texts
    {
        private struct Entry
        {
            public uint Print;
            public string Text;
        }

        private struct Pattern
        {
            public Regex English;
            public string Polish;
        }

        private static readonly Dictionary<string, Entry> Dialogue = new Dictionary<string, Entry>(StringComparer.Ordinal);
        private static readonly Dictionary<string, Entry> Rewired = new Dictionary<string, Entry>(StringComparer.Ordinal);
        private static readonly Dictionary<string, string> Fixed = new Dictionary<string, string>(StringComparer.Ordinal);
        private static readonly List<Pattern> Patterns = new List<Pattern>();
        private static readonly HashSet<string> PolishValues = new HashSet<string>(StringComparer.Ordinal);

        private static readonly HashSet<string> Unmatched = new HashSet<string>(StringComparer.Ordinal);
        private static readonly List<string> UnmatchedNew = new List<string>();
        private static readonly Regex Wordy = new Regex("[A-Za-z]{2}");

        private static int translated, changed, reportedTranslated, reportedChanged;

        /// File next to the library: key, tab, English fingerprint (hex), tab, text.
        internal static bool Load(string path)
        {
            if (!File.Exists(path))
            {
                Plugin.Log.LogError("Missing file " + path + "; the game stays English.");
                return false;
            }

            foreach (var raw in File.ReadAllText(path, Encoding.UTF8).Split('\n'))
            {
                var parts = raw.TrimEnd('\r').Split('\t');
                if (parts.Length != 3) continue;
                uint print;
                if (!uint.TryParse(parts[1], System.Globalization.NumberStyles.HexNumber, null, out print)) continue;
                var key = Unescape(parts[0]);
                var text = Unescape(parts[2]);
                var entry = new Entry { Print = print, Text = text };
                PolishValues.Add(text);

                if (key.StartsWith("dlg/", StringComparison.Ordinal)) Dialogue[key.Substring(4)] = entry;
                else if (key.StartsWith("rewired/", StringComparison.Ordinal)) Rewired[key.Substring(8)] = entry;
                else if (key.StartsWith("ui/", StringComparison.Ordinal)) Fixed[key.Substring(3)] = text;
                else if (key.StartsWith("fmt/", StringComparison.Ordinal))
                {
                    var english = "^" + Regex.Escape(key.Substring(4)).Replace(@"\{0}", "(.*?)").Replace("{0}", "(.*?)") + "$";
                    Patterns.Add(new Pattern { English = new Regex(english, RegexOptions.Singleline), Polish = text });
                }
            }

            Plugin.Log.LogInfo(string.Format("Loaded {0} dialogue lines, {1} labels, {2} patterns, {3} control mapper texts.",
                Dialogue.Count, Fixed.Count, Patterns.Count, Rewired.Count));
            return Dialogue.Count + Fixed.Count + Patterns.Count + Rewired.Count > 0;
        }

        private static string Unescape(string value)
        {
            var result = new StringBuilder(value.Length);
            for (var i = 0; i < value.Length; i++)
            {
                if (value[i] == '\\' && i + 1 < value.Length)
                {
                    var next = value[++i];
                    result.Append(next == 'n' ? '\n' : next == 't' ? '\t' : next == 'r' ? '\r' : next);
                }
                else result.Append(value[i]);
            }
            return result.ToString();
        }

        /// FNV-1a over ASCII letters and digits only: immune to \r, spacing and punctuation
        /// the asset reader may decode differently. Same function in build_plugin.py.
        internal static uint Fingerprint(string text)
        {
            uint hash = 2166136261;
            if (text == null) return hash;
            foreach (var c in text)
            {
                if (c > 127 || !char.IsLetterOrDigit(c)) continue;
                hash ^= c;
                hash *= 16777619;
            }
            return hash;
        }

        /// Label text: exact, then with surrounding whitespace kept, then label + value patterns.
        internal static string Label(string value)
        {
            if (string.IsNullOrEmpty(value)) return value;
            string polish;
            if (Fixed.TryGetValue(value, out polish)) return polish;

            var trimmed = value.Trim();
            if (trimmed.Length != value.Length && trimmed.Length > 0 && Fixed.TryGetValue(trimmed, out polish))
            {
                var start = value.IndexOf(trimmed, StringComparison.Ordinal);
                return value.Substring(0, start) + polish + value.Substring(start + trimmed.Length);
            }

            foreach (var pattern in Patterns)
            {
                var match = pattern.English.Match(value);
                if (!match.Success) continue;
                var inserted = match.Groups[1].Value;
                string insertedPolish;
                if (Fixed.TryGetValue(inserted, out insertedPolish)) inserted = insertedPolish;
                return pattern.Polish.Replace("{0}", inserted);
            }

            Remember(value);
            return value;
        }

        /// Collects English-looking labels without a translation, for the vertical test.
        private static void Remember(string value)
        {
            if (value.Length > 400 || PolishValues.Contains(value) || !Wordy.IsMatch(value)) return;
            if (Unmatched.Add(value)) UnmatchedNew.Add(value);
        }

        internal static void Translate(DialogueDatabase database)
        {
            if (database == null || database.conversations == null) return;
            foreach (var conversation in database.conversations)
            {
                if (conversation == null || conversation.dialogueEntries == null) continue;
                var title = Field.LookupValue(conversation.fields, "Title") ?? "";
                foreach (var dialogueEntry in conversation.dialogueEntries)
                {
                    Entry entry;
                    if (dialogueEntry == null || !Dialogue.TryGetValue(title + "/" + dialogueEntry.id, out entry)) continue;
                    var field = Field.Lookup(dialogueEntry.fields, "Dialogue Text");
                    if (field == null || field.value == entry.Text) continue;
                    if (Fingerprint(field.value) != entry.Print)
                    {
                        changed++;
                        continue;
                    }
                    field.value = entry.Text;
                    translated++;
                }
            }
        }

        private static Type languageData;
        private static bool languageDataLooked;

        internal static void TranslateRewired()
        {
            if (Rewired.Count == 0) return;
            if (!languageDataLooked)
            {
                languageDataLooked = true;
                languageData = AccessTools.TypeByName("Rewired.UI.ControlMapper.LanguageData");
                if (languageData == null) Plugin.Log.LogWarning("Rewired LanguageData not found; control mapper stays English.");
            }
            if (languageData == null) return;

            foreach (var data in Resources.FindObjectsOfTypeAll(languageData))
            {
                foreach (var pair in Rewired)
                {
                    var field = AccessTools.Field(languageData, pair.Key);
                    if (field == null || field.FieldType != typeof(string)) continue;
                    var value = (string)field.GetValue(data);
                    if (value == pair.Value.Text) continue;
                    if (Fingerprint(value) != pair.Value.Print)
                    {
                        changed++;
                        continue;
                    }
                    field.SetValue(data, pair.Value.Text);
                    translated++;
                }
            }
        }

        internal static void Report(string scene)
        {
            if (translated != reportedTranslated || changed != reportedChanged)
            {
                Plugin.Log.LogInfo("Scene " + scene + ": swapped " + translated + " texts so far.");
                if (changed > reportedChanged)
                {
                    Plugin.Log.LogWarning(changed + " texts of this game version differ from the translated ones; they stay English.");
                }
                reportedTranslated = translated;
                reportedChanged = changed;
            }
            if (UnmatchedNew.Count == 0) return;
            try
            {
                var lines = new StringBuilder();
                foreach (var value in UnmatchedNew)
                {
                    lines.Append(scene).Append('\t').Append(value.Replace("\\", "\\\\").Replace("\n", "\\n").Replace("\t", "\\t")).Append('\n');
                }
                File.AppendAllText(Path.Combine(Plugin.Folder, Plugin.UntranslatedFile), lines.ToString(), Encoding.UTF8);
                UnmatchedNew.Clear();
            }
            catch (Exception error)
            {
                Plugin.Log.LogWarning("Cannot write " + Plugin.UntranslatedFile + ": " + error.Message);
                UnmatchedNew.Clear();
            }
        }
    }

    [HarmonyPatch]
    internal static class TextPatch
    {
        private static readonly AccessTools.FieldRef<Text, string> Field = AccessTools.FieldRefAccess<Text, string>("m_Text");

        [HarmonyPrefix]
        [HarmonyPatch(typeof(Text), "set_text")]
        private static void BeforeSetText(ref string value)
        {
            value = Texts.Label(value);
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(Text), "OnEnable")]
        private static void BeforeEnable(Text __instance)
        {
            var value = Field(__instance);
            var polish = Texts.Label(value);
            if (!ReferenceEquals(polish, value)) Field(__instance) = polish;
        }

        internal static void BeforeDoText(ref string __1)
        {
            __1 = Texts.Label(__1);
        }

        /// After scene load: live labels go through the setter so they redraw; prefab
        /// templates get the field only.
        internal static void Replace(Text text)
        {
            if (text == null) return;
            var value = Field(text);
            var polish = Texts.Label(value);
            if (ReferenceEquals(polish, value)) return;
            if (text.gameObject.scene.IsValid()) text.text = polish;
            else Field(text) = polish;
        }
    }

    [HarmonyPatch]
    internal static class DialoguePatch
    {
        [HarmonyPrefix]
        [HarmonyPatch(typeof(DatabaseManager), "Add")]
        private static void BeforeAdd(DialogueDatabase __0)
        {
            Texts.Translate(__0);
        }
    }

    /// Fjalla One (menus, titles) lacks ą ć ę ś ź ż and Ostrich Sans (dialogue) lacks ą ę.
    /// Unity draws a glyph the font lacks from the fonts named in fontNames; the list gets a
    /// similar condensed Windows font first, then generic ones. Nothing ships.
    internal static class Fonts
    {
        private static readonly string[] Fallbacks =
        {
            "Bahnschrift SemiBold Condensed", "Bahnschrift Condensed", "Bahnschrift", "Arial Narrow", "Arial",
        };
        private static readonly HashSet<int> Done = new HashSet<int>();
        private static bool logged;

        internal static void Prepare()
        {
            if (!logged)
            {
                logged = true;
                try
                {
                    var found = new List<string>();
                    foreach (var name in Font.GetOSInstalledFontNames())
                    {
                        if (name.StartsWith("Bahnschrift", StringComparison.Ordinal) || name.StartsWith("Arial", StringComparison.Ordinal)) found.Add(name);
                    }
                    Plugin.Log.LogInfo("System fonts for missing letters: " + string.Join(", ", found.ToArray()));
                }
                catch (Exception error)
                {
                    Plugin.Log.LogWarning("Cannot list system fonts: " + error.Message);
                }
            }

            foreach (var font in Resources.FindObjectsOfTypeAll<Font>())
            {
                if (font == null || !font.dynamic || !Done.Add(font.GetInstanceID())) continue;
                if (font.name != "FjallaOne-Regular" && font.name != "OstrichSans-Heavy") continue;
                try
                {
                    var names = new List<string>(font.fontNames ?? new string[0]);
                    foreach (var fallback in Fallbacks) if (!names.Contains(fallback)) names.Add(fallback);
                    font.fontNames = names.ToArray();
                    Plugin.Log.LogInfo("Font " + font.name + ": fallback " + string.Join(", ", font.fontNames));
                }
                catch (Exception error)
                {
                    Plugin.Log.LogWarning("Font " + font.name + ": " + error.Message);
                }
            }
        }
    }
}
