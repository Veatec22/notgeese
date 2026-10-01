// Not Geese: Polish for I Am Your Beast, added at runtime.
//
// The game has no language system. Texts live in three places, all swapped in memory
// without touching game files:
//   1. Fleece bank (menus, HUD, tutorial, enemy barks): Passage.text field by ID;
//   2. AudioTextSynchronizer dialogue scenes: text of each PhraseAsset segment;
//   3. text hard-coded into TextMeshPro scenes: exact text match;
//   4. headers the game glues from single words in English order: rebuilt from a Polish
//      pattern; a few English string literals in code; key names from the Input System.
//
// Every Fleece entry and scene segment carries a fingerprint of the English original.
// When a game update puts different text under the same key it stays English and the
// plugin logs how many there were.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Reflection.Emit;
using System.Text;
using AudioTextSynchronizer;
using AudioTextSynchronizer.Core;
using AudioTextSynchronizer.TextEffects.Base;
using AudioTextSynchronizer.TextSplitters.Base;
using BepInEx;
using BepInEx.Logging;
using Fleece;
using HarmonyLib;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;

namespace notgeese.IAmYourBeast
{
    // The release before the project rename had a different GUID. If its folder is still in
    // plugins, BepInEx skips this plugin instead of loading two translations at once.
    [BepInIncompatibility("cc.notgoose.iamyourbeast")]
    [BepInPlugin(Id, "I Am Your Beast PL", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string Id = "cc.notgeese.iamyourbeast";
        public const string Version = "1.0";

        internal const string TermsFile = "pl.tsv";
        internal const string PolishLetters = "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ";

        internal static ManualLogSource Log;

        private void Awake()
        {
            Log = Logger;
            Logger.LogInfo(string.Format("Gra {0} {1}, Unity {2}.",
                Application.productName, Application.version, Application.unityVersion));

            if (!Texts.Load(Path.Combine(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location), TermsFile)))
            {
                return;
            }

            var harmony = new Harmony(Id);
            Patch(harmony, typeof(FleecePatch), "bank Fleece");
            Patch(harmony, typeof(PhrasePatch), "dialogue scenes");
            Patch(harmony, typeof(TmpPatch), "TextMeshPro labels");
            Patch(harmony, typeof(UnlockPatch), "unlock headers");
            Patch(harmony, typeof(CodePatch), "texts in code");
            Patch(harmony, typeof(KeyPatch), "key names");

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
                Logger.LogError("Could not hook (" + what + "), this part stays English: " + error.Message);
            }
        }

        private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            try
            {
                foreach (var passage in Resources.FindObjectsOfTypeAll<Passage>()) Texts.Translate(passage);
                foreach (var phrase in Resources.FindObjectsOfTypeAll<PhraseAsset>()) Texts.Translate(phrase);
                foreach (var text in Resources.FindObjectsOfTypeAll<TMP_Text>()) TmpPatch.Replace(text);
                Fonts.Prepare();
                Texts.ReportOnce();
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

        private static readonly Dictionary<int, Entry> Passages = new Dictionary<int, Entry>();
        private static readonly Dictionary<string, Dictionary<int, Entry>> Phrases =
            new Dictionary<string, Dictionary<int, Entry>>(StringComparer.Ordinal);
        internal static readonly Dictionary<string, string> Fixed = new Dictionary<string, string>(StringComparer.Ordinal);
        internal static readonly Dictionary<string, string> Formats = new Dictionary<string, string>(StringComparer.Ordinal);
        internal static readonly Dictionary<string, string> Code = new Dictionary<string, string>(StringComparer.Ordinal);
        internal static readonly Dictionary<string, string> Keys = new Dictionary<string, string>(StringComparer.Ordinal);

        private static readonly HashSet<int> Done = new HashSet<int>();
        private static int translated, changed;
        private static bool reported;

        /// File next to the library: key, tab, English fingerprint, tab, text.
        /// Keys: fleece/<ID>, phrase/<asset>/<segment>, tmp/<English text>,
        /// format/<glued header>, code/<English string literal>, key/<Input System key name>.
        internal static bool Load(string path)
        {
            if (!File.Exists(path))
            {
                Plugin.Log.LogError("Missing file " + path + "; the game stays English.");
                return false;
            }

            foreach (var raw in File.ReadAllText(path, Encoding.UTF8).Split('\n'))
            {
                var line = raw.TrimEnd('\r');
                var parts = line.Split('\t');
                if (parts.Length != 3) continue;
                var key = Unescape(parts[0]);
                var text = Unescape(parts[2]);
                uint print;
                if (!uint.TryParse(parts[1], System.Globalization.NumberStyles.HexNumber, null, out print)) continue;
                var entry = new Entry { Print = print, Text = text };

                if (key.StartsWith("fleece/", StringComparison.Ordinal))
                {
                    int id;
                    if (int.TryParse(key.Substring(7), out id)) Passages[id] = entry;
                }
                else if (key.StartsWith("phrase/", StringComparison.Ordinal))
                {
                    var slash = key.LastIndexOf('/');
                    int index;
                    if (slash <= 7 || !int.TryParse(key.Substring(slash + 1), out index)) continue;
                    var name = key.Substring(7, slash - 7);
                    Dictionary<int, Entry> timings;
                    if (!Phrases.TryGetValue(name, out timings)) Phrases[name] = timings = new Dictionary<int, Entry>();
                    timings[index] = entry;
                }
                else if (key.StartsWith("tmp/", StringComparison.Ordinal))
                {
                    Fixed[key.Substring(4)] = text;
                }
                else if (key.StartsWith("format/", StringComparison.Ordinal))
                {
                    Formats[key.Substring(7)] = text;
                }
                else if (key.StartsWith("code/", StringComparison.Ordinal))
                {
                    Code[key.Substring(5)] = text;
                }
                else if (key.StartsWith("key/", StringComparison.Ordinal))
                {
                    Keys[key.Substring(4)] = text;
                }
            }

            Plugin.Log.LogInfo(string.Format("Loaded {0} Fleece entries, {1} scenes, {2} fixed labels.",
                Passages.Count, Phrases.Count, Fixed.Count));
            return Passages.Count + Phrases.Count + Fixed.Count > 0;
        }

        private static string Unescape(string value)
        {
            return value.Replace("\\n", "\n").Replace("\\t", "\t").Replace("\\\\", "\\");
        }

        /// FNV-1a fingerprint of letters and digits only: immune to \r, trailing spaces and
        /// characters asset readers decode differently. The same function is in build_plugin.py.
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

        internal static void Translate(Passage passage)
        {
            if (passage == null || !Done.Add(passage.GetInstanceID())) return;
            Entry entry;
            if (!Passages.TryGetValue(passage.id, out entry)) return;
            if (Fingerprint(passage.text) != entry.Print)
            {
                changed++;
                return;
            }
            passage.text = entry.Text;
            translated++;
        }

        internal static void Translate(PhraseAsset phrase)
        {
            if (phrase == null || phrase.Timings == null || !Done.Add(phrase.GetInstanceID())) return;
            Dictionary<int, Entry> timings;
            if (!Phrases.TryGetValue(phrase.name, out timings)) return;

            var any = false;
            for (var i = 0; i < phrase.Timings.Count; i++)
            {
                var timing = phrase.Timings[i];
                Entry entry;
                if (timing == null || !timings.TryGetValue(i, out entry)) continue;
                if (Fingerprint(timing.Text) != entry.Print)
                {
                    changed++;
                    continue;
                }
                timing.Text = entry.Text;
                translated++;
                any = true;
            }
            if (!any) return;

            // The full text is used to find successive segments (IndexOf from the previous end).
            // It is built from the segments so each can be found in order, repeats included.
            var full = new StringBuilder();
            foreach (var timing in phrase.Timings)
            {
                if (timing == null) continue;
                if (full.Length > 0) full.Append('\n');
                full.Append(timing.Text);
            }
            phrase.Text = full.ToString();
        }

        internal static void ReportOnce()
        {
            if (reported || translated == 0) return;
            reported = true;
            Plugin.Log.LogInfo("Swapped " + translated + " texts.");
            if (changed > 0)
            {
                Plugin.Log.LogWarning(changed + " texts of this game version differ from the translated ones; they stay English.");
            }
        }
    }

    [HarmonyPatch]
    internal static class FleecePatch
    {
        [HarmonyPrefix]
        [HarmonyPatch(typeof(Passage), "get_parsedText")]
        private static void BeforeParsedText(Passage __instance)
        {
            Texts.Translate(__instance);
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(Story), "Find", new[] { typeof(int) })]
        private static void AfterFindById(Passage __result)
        {
            Texts.Translate(__result);
        }

        [HarmonyPostfix]
        [HarmonyPatch(typeof(Story), "Find", new[] { typeof(string) })]
        private static void AfterFindByName(Passage __result)
        {
            Texts.Translate(__result);
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(Drawstring), "Begin", new[] { typeof(Passage), typeof(bool) })]
        private static void BeforeBegin(Passage __0)
        {
            Texts.Translate(__0);
        }
    }

    [HarmonyPatch]
    internal static class PhrasePatch
    {
        [HarmonyPrefix]
        [HarmonyPatch(typeof(TextSynchronizer), "set_Timings")]
        private static void BeforeSetTimings(PhraseAsset value)
        {
            Texts.Translate(value);
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(TextSynchronizer), "SplitWords")]
        private static void BeforeSplitWords(TextSynchronizer __instance)
        {
            Texts.Translate(__instance.Timings);
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(TextSplitConfigBase), "Init")]
        private static void BeforeSplit(PhraseAsset __0)
        {
            Texts.Translate(__0);
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(TextEffectBase), "Init")]
        private static void BeforeEffect(TextSynchronizer __0)
        {
            if (__0 != null) Texts.Translate(__0.Timings);
        }
    }

    [HarmonyPatch]
    internal static class TmpPatch
    {
        private static readonly AccessTools.FieldRef<TMP_Text, string> Text =
            AccessTools.FieldRefAccess<TMP_Text, string>("m_text");

        [HarmonyPrefix]
        [HarmonyPatch(typeof(TMP_Text), "set_text")]
        private static void BeforeSetText(ref string value)
        {
            string polish;
            if (value != null && Texts.Fixed.TryGetValue(value, out polish)) value = polish;
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(TextMeshProUGUI), "Awake")]
        private static void BeforeAwakeUi(TextMeshProUGUI __instance)
        {
            Swap(__instance);
        }

        [HarmonyPrefix]
        [HarmonyPatch(typeof(TextMeshPro), "Awake")]
        private static void BeforeAwakeWorld(TextMeshPro __instance)
        {
            Swap(__instance);
        }

        /// Before Awake: swap the field only, TMP hasn't built anything yet.
        private static void Swap(TMP_Text text)
        {
            var value = Text(text);
            string polish;
            if (value != null && Texts.Fixed.TryGetValue(value, out polish)) Text(text) = polish;
        }

        /// After scene load: already awake objects go through the setter so they redraw.
        internal static void Replace(TMP_Text text)
        {
            if (text == null) return;
            var value = Text(text);
            string polish;
            if (value == null || !Texts.Fixed.TryGetValue(value, out polish)) return;
            if (text.gameObject.scene.IsValid()) text.text = polish;
            else Text(text) = polish;
        }
    }

    /// The level-select unlock panel glues headers from single Fleece words in English order
    /// ("Next" + category + "Unlock", "Watch" + category + "cutscene"). The words are already
    /// Polish by then; the glued result is recognized by them and rebuilt from a Polish pattern.
    /// Anything that doesn't match stays as the game built it.
    [HarmonyPatch]
    internal static class UnlockPatch
    {
        private static readonly AccessTools.FieldRef<UIContentUnlockIndicator, TMP_Text> Header =
            AccessTools.FieldRefAccess<UIContentUnlockIndicator, TMP_Text>("headerText");
        private static readonly AccessTools.FieldRef<UIContentUnlockIndicator, Jumper> Next =
            AccessTools.FieldRefAccess<UIContentUnlockIndicator, Jumper>("passageNext");
        private static readonly AccessTools.FieldRef<UIContentUnlockIndicator, Jumper> Unlock =
            AccessTools.FieldRefAccess<UIContentUnlockIndicator, Jumper>("passageUnlock");
        private static readonly AccessTools.FieldRef<UIContentUnlockIndicator, Jumper> New =
            AccessTools.FieldRefAccess<UIContentUnlockIndicator, Jumper>("passageNew");
        private static readonly AccessTools.FieldRef<UIContentUnlockIndicator, Jumper> Unlocked =
            AccessTools.FieldRefAccess<UIContentUnlockIndicator, Jumper>("passageUnlocked");

        [HarmonyPostfix]
        [HarmonyPatch(typeof(UIContentUnlockIndicator), "DisplayNextUnlock")]
        private static void AfterNext(UIContentUnlockIndicator __instance)
        {
            var header = Header(__instance);
            string category;
            if (header != null && Between(header.text, Read(Next(__instance)), Read(Unlock(__instance)), out category))
            {
                Apply(header, "next-unlock", category);
            }
        }

        /// "New" + (cutscene | category + " " + level) + "Unlocked".
        [HarmonyPostfix]
        [HarmonyPatch(typeof(UIContentUnlockIndicator), "DisplayNewUnlock")]
        private static void AfterNew(UIContentUnlockIndicator __instance)
        {
            var header = Header(__instance);
            var storer = Storer();
            string middle;
            if (header == null || storer == null ||
                !Between(header.text, Read(New(__instance)), Read(Unlocked(__instance)), out middle)) return;
            var level = Read(storer.passageLevel);
            if (middle == Read(storer.passageCutscene))
            {
                Apply(header, "new-cutscene-unlocked");
            }
            else if (!string.IsNullOrEmpty(level) && middle.EndsWith(" " + level, StringComparison.Ordinal))
            {
                Apply(header, "new-level-unlocked", middle.Substring(0, middle.Length - level.Length - 1));
            }
        }

        /// "Watch" + category + "cutscene"; "Complete" + category + level + number.
        [HarmonyPostfix]
        [HarmonyPatch(typeof(LevelUnlockCondition), "GetUnlockConditionDisplayStrings")]
        private static void AfterConditions(string[] __result)
        {
            var storer = Storer();
            if (__result == null || storer == null) return;
            var level = Read(storer.passageLevel);
            for (var i = 0; i < __result.Length; i++)
            {
                string middle;
                if (Between(__result[i], Read(storer.passageWatch), Read(storer.passageCutscene), out middle))
                {
                    __result[i] = Format("watch-cutscene", __result[i], middle);
                }
                else if (!string.IsNullOrEmpty(level) && Between(__result[i], Read(storer.passageComplete), null, out middle))
                {
                    var at = middle.LastIndexOf(" " + level + " ", StringComparison.Ordinal);
                    if (at > 0)
                    {
                        __result[i] = Format("complete-level", __result[i],
                            middle.Substring(0, at), middle.Substring(at + level.Length + 2));
                    }
                }
            }
        }

        private static TextStorerManager Storer()
        {
            return GameManager.instance != null ? GameManager.instance.textStorerManager : null;
        }

        private static string Read(Jumper jumper)
        {
            return jumper != null && jumper.passage != null ? jumper.passage.parsedText : null;
        }

        /// value = head + " " + middle + " " + tail (tail null: anything after head).
        private static bool Between(string value, string head, string tail, out string middle)
        {
            middle = null;
            if (string.IsNullOrEmpty(value) || string.IsNullOrEmpty(head)) return false;
            if (!value.StartsWith(head + " ", StringComparison.Ordinal)) return false;
            var end = value.Length;
            if (tail != null)
            {
                if (tail.Length == 0 || !value.EndsWith(" " + tail, StringComparison.Ordinal)) return false;
                end -= tail.Length + 1;
            }
            var start = head.Length + 1;
            if (end <= start) return false;
            middle = value.Substring(start, end - start);
            return true;
        }

        private static void Apply(TMP_Text header, string name, params object[] args)
        {
            header.text = Format(name, header.text, args);
        }

        private static string Format(string name, string fallback, params object[] args)
        {
            string pattern;
            if (!Texts.Formats.TryGetValue(name, out pattern)) return fallback;
            try
            {
                return string.Format(pattern, args);
            }
            catch (FormatException)
            {
                return fallback;
            }
        }
    }

    /// English string literals in game code, swapped in the IL. A literal that is gone after
    /// an update just isn't found.
    [HarmonyPatch]
    internal static class CodePatch
    {
        private static IEnumerable<MethodBase> TargetMethods()
        {
            foreach (var method in new[]
            {
                AccessTools.Method(typeof(UILevelSelectFeature), "Refresh"),
                AccessTools.Method(typeof(UISettingsOptionRebind), "RefreshText"),
            })
            {
                if (method != null) yield return method;
            }
        }

        [HarmonyTranspiler]
        private static IEnumerable<CodeInstruction> Literals(IEnumerable<CodeInstruction> code)
        {
            foreach (var instruction in code)
            {
                string polish;
                var literal = instruction.operand as string;
                if (instruction.opcode == OpCodes.Ldstr && literal != null && Texts.Code.TryGetValue(literal, out polish))
                {
                    instruction.operand = polish;
                }
                yield return instruction;
            }
        }
    }

    /// Key names on the rebind screen and in hints ("Space", "Left Button") come from the
    /// Input System's readable path; exact names in key/ are swapped, combos ("W/S/A/D") and
    /// single letters stay.
    [HarmonyPatch]
    internal static class KeyPatch
    {
        [HarmonyPostfix]
        [HarmonyPatch(typeof(InputControlPath), "ToHumanReadableString",
            new[] { typeof(string), typeof(InputControlPath.HumanReadableStringOptions), typeof(InputControl) })]
        private static void AfterReadable(ref string __result)
        {
            string polish;
            if (__result != null && Texts.Keys.TryGetValue(__result, out polish)) __result = polish;
        }
    }

    /// Game fonts are dynamic with a source face that has Polish letters. Letters are added
    /// to the atlas right away and the log says whether it worked.
    internal static class Fonts
    {
        private static readonly HashSet<int> Checked = new HashSet<int>();

        internal static void Prepare()
        {
            foreach (var font in Resources.FindObjectsOfTypeAll<TMP_FontAsset>())
            {
                if (font == null || !Checked.Add(font.GetInstanceID())) continue;
                try
                {
                    uint[] missing;
                    var complete = font.HasCharacters(Plugin.PolishLetters, out missing, true, true);
                    if (complete)
                    {
                        Plugin.Log.LogInfo("Font " + font.name + ": Polish letters present.");
                    }
                    else
                    {
                        var list = new StringBuilder();
                        if (missing != null) foreach (var c in missing) list.Append((char)c);
                        Plugin.Log.LogWarning("Font " + font.name + " (" + font.atlasPopulationMode + "): missing " + list + ".");
                    }
                }
                catch (Exception error)
                {
                    Plugin.Log.LogWarning("Font " + font.name + ": cannot check letters (" + error.Message + ").");
                }
            }
        }
    }
}
