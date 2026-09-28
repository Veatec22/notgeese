// El Paso, Elsewhere PL: BepInEx 6 IL2CPP plugin.
//
// Dialogue, subtitles, tickers and chapter titles go through I2 Localization (the game's
// LocalizationHandler asks I2 for a term). After I2 loads its source we overwrite the English
// column in memory with Polish; the game keeps English as its language, nothing is saved, and
// without the plugin the original text is back. Menus and HUD labels are plain TextMeshPro
// texts in scenes and code: an exact-match map replaces them on scene load and in the text
// setter. Fonts get composed Polish letters (PolishGlyphs). No game file is changed or shipped.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text.Json;
using System.Text.RegularExpressions;
using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using HarmonyLib;
using I2.Loc;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

namespace notgeese.ElPaso
{
    [BepInPlugin(Id, "El Paso, Elsewhere PL", Version)]
    public sealed class Plugin : BasePlugin
    {
        public const string Id = "pl.notgeese.elpasoelsewhere";
        public const string Version = "0.1";
        internal static ManualLogSource Logger;
        internal static bool Failed;
        static Harmony harmony;

        public override void Load()
        {
            Logger = Log;
            try
            {
                Log.LogInfo("PL " + Version + "; game=" + Application.version + "; Unity=" + Application.unityVersion);
                var folder = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
                var data = JsonSerializer.Deserialize<Dictionary<string, Dictionary<string, string>>>(
                    File.ReadAllText(Path.Combine(folder, "pl.json")));
                Terms.Load(data["i2"]);
                Texts.Load(data["text"], data.TryGetValue("pattern", out var patterns) ? patterns : new Dictionary<string, string>());
                harmony = new Harmony(Id);
                // Unity calls Awake/Start of LocalizeText itself, so these always run before the
                // first lookup; the handler prefix covers code that asks earlier.
                Prefix(typeof(LocalizeText), "Awake", nameof(Terms.EnsureHook));
                Prefix(typeof(LocalizeText), "Start", nameof(Terms.EnsureHook));
                Prefix(typeof(LocalizationHandler), "GetLocalizedString", nameof(Terms.EnsureHook));
                harmony.Patch(AccessTools.Method(typeof(LocalizationHandler), "GetLocalizedString"),
                    postfix: new HarmonyMethod(typeof(Terms), nameof(Terms.AfterHandler)));
                foreach (var method in typeof(LocalizationManager).GetMethods(BindingFlags.Public | BindingFlags.Static))
                    if (method.Name == "GetTranslation" && method.ReturnType == typeof(string)
                        && method.GetParameters().Length > 0 && method.GetParameters()[0].ParameterType == typeof(string))
                        harmony.Patch(method, postfix: new HarmonyMethod(typeof(Terms), nameof(Terms.AfterI2)));
                harmony.Patch(AccessTools.PropertySetter(typeof(TMP_Text), "text"),
                    prefix: new HarmonyMethod(typeof(Texts), nameof(Texts.BeforeText)));
                AddComponent<Runtime>();
                Log.LogInfo("Loaded: I2 terms " + Terms.Count + ", texts " + Texts.Count + ".");
            }
            catch (Exception e) { Disable(e); }
        }

        static void Prefix(Type type, string method, string hook)
        {
            harmony.Patch(AccessTools.Method(type, method), prefix: new HarmonyMethod(typeof(Terms), hook));
        }

        internal static void Disable(Exception e)
        {
            if (Failed) return;
            Failed = true;
            Logger.LogError("PL disabled, the game keeps running in English: " + e);
            try { harmony?.UnpatchSelf(); } catch (Exception cleanup) { Logger.LogWarning(cleanup.Message); }
        }
    }

    public sealed class Runtime : MonoBehaviour
    {
        int scene = -1;
        float nextScan;
        public Runtime(IntPtr ptr) : base(ptr) { }

        public void Update()
        {
            if (Plugin.Failed) return;
            try
            {
                Terms.Ensure();
                var active = SceneManager.GetActiveScene().handle;
                if (active == scene && Time.unscaledTime < nextScan) return;
                if (active != scene) Plugin.Logger.LogInfo("Scene: " + SceneManager.GetActiveScene().name + "; " + Terms.Stats() + "; " + Texts.Stats());
                scene = active;
                nextScan = Time.unscaledTime + 1f;
                var composed = PolishGlyphs.PatchLoadedFonts();
                Texts.ReplaceLoaded(composed > 0);
            }
            catch (Exception e) { Plugin.Disable(e); }
        }
    }

    /// I2 terms: Polish written over the English column of the loaded source. Also checked on
    /// the way out (handler and I2 lookups) and on screen (English of a translated term).
    static class Terms
    {
        static readonly Dictionary<string, string> polish = new Dictionary<string, string>(StringComparer.Ordinal);
        /// English of translated terms → Polish; English shared by terms with different Polish is left out.
        internal static readonly Dictionary<string, string> ByEnglish = new Dictionary<string, string>(StringComparer.Ordinal);
        static bool applied;
        static string sampleTerm;
        static int handlerCalls, handlerFixed, i2Calls, i2Fixed, resets;
        internal static int Count => polish.Count;
        internal static readonly HashSet<string> Values = new HashSet<string>(StringComparer.Ordinal);

        internal static void Load(Dictionary<string, string> map)
        {
            foreach (var pair in map) { polish[pair.Key] = pair.Value; Values.Add(pair.Value); }
        }

        internal static void EnsureHook()
        {
            try { Ensure(); } catch (Exception e) { Plugin.Disable(e); }
        }

        internal static void Ensure()
        {
            if (Plugin.Failed) return;
            if (applied) { Watch(); return; }
            LocalizationManager.InitializeIfNeeded();
            var sources = LocalizationManager.Sources;
            if (sources == null || sources.Count == 0) return;
            int replaced = 0, english = 0, total = 0;
            var conflicts = new HashSet<string>(StringComparer.Ordinal);
            var untranslated = new List<string>();
            for (var s = 0; s < sources.Count; s++)
            {
                var source = sources[s];
                var languages = source.mLanguages;
                if (languages == null || languages.Count == 0 || languages[0].Code != "en")
                    throw new InvalidOperationException("I2 source without English as the first language.");
                var terms = source.mTerms;
                for (var i = 0; i < terms.Count; i++)
                {
                    var term = terms[i];
                    var column = term.Languages;
                    if (column == null || column.Length == 0) continue;
                    total++;
                    var original = column[0];
                    if (polish.TryGetValue(term.Term, out var text))
                    {
                        if (original != text && !string.IsNullOrEmpty(original))
                        {
                            if (ByEnglish.TryGetValue(original, out var other) && other != text) conflicts.Add(original);
                            else ByEnglish[original] = text;
                        }
                        column[0] = text;
                        replaced++;
                        sampleTerm ??= term.Term;
                    }
                    else if (!string.IsNullOrEmpty(original)) { english++; untranslated.Add(original); }
                }
            }
            foreach (var c in conflicts) ByEnglish.Remove(c);
            foreach (var u in untranslated) if (!ByEnglish.ContainsKey(u)) Texts.Known.Add(u);
            if (replaced == 0) throw new InvalidOperationException("No I2 term matched the installed game.");
            if (resets == 0)
                Plugin.Logger.LogInfo("I2: current language " + LocalizationManager.CurrentLanguage + ", terms " + total +
                    ", Polish " + replaced + ", still English " + english + ", display fallback " + ByEnglish.Count + ".");
            applied = true;
        }

        /// The game or I2 may reload the English column (language load, cache import).
        static void Watch()
        {
            var sources = LocalizationManager.Sources;
            if (sampleTerm == null || sources == null || sources.Count == 0) return;
            var data = sources[0].GetTermData(sampleTerm, false);
            if (data == null || data.Languages == null || data.Languages.Length == 0) return;
            if (data.Languages[0] == polish[sampleTerm]) return;
            resets++;
            Plugin.Logger.LogWarning("I2 column 0 was reset (" + resets + "), reapplying Polish. Language: " + LocalizationManager.CurrentLanguage);
            applied = false;
            Ensure();
        }

        internal static void AfterHandler(string __0, ref string __result)
        {
            try
            {
                handlerCalls++;
                if (__0 != null && polish.TryGetValue(__0, out var text) && __result != text)
                {
                    if (handlerFixed++ < 20) Plugin.Logger.LogInfo("Handler returned other text for " + __0 + ": " + __result);
                    __result = text;
                }
            }
            catch (Exception e) { Plugin.Logger.LogWarning("Handler: " + e.Message); }
        }

        internal static void AfterI2(string __0, ref string __result)
        {
            try
            {
                i2Calls++;
                if (__0 != null && polish.TryGetValue(__0, out var text) && __result != text)
                {
                    if (i2Fixed++ < 20) Plugin.Logger.LogInfo("I2 returned other text for " + __0 + ": " + __result);
                    __result = text;
                }
            }
            catch (Exception e) { Plugin.Logger.LogWarning("I2 lookup: " + e.Message); }
        }

        internal static string Stats() =>
            "handler calls " + handlerCalls + " (fixed " + handlerFixed + "), I2 calls " + i2Calls + " (fixed " + i2Fixed + "), resets " + resets;
    }

    /// Scene and code texts: exact English → Polish; patterns like "CHAPTER {0}".
    static class Texts
    {
        static readonly Dictionary<string, string> polish = new Dictionary<string, string>(StringComparer.Ordinal);
        static readonly List<KeyValuePair<Regex, string>> patterns = new List<KeyValuePair<Regex, string>>();
        internal static readonly HashSet<string> Known = new HashSet<string>(StringComparer.Ordinal);
        static readonly HashSet<string> logged = new HashSet<string>(StringComparer.Ordinal);
        static readonly Regex letters = new Regex("[A-Za-z]{2}");
        static readonly Regex tags = new Regex("<[^>]*>");
        static Dictionary<string, string> upper;
        static int setterCalls, fallbacks;
        internal static int Count => polish.Count;
        internal static string Stats() => "text setter calls " + setterCalls + ", display fallbacks " + fallbacks;

        internal static void Load(Dictionary<string, string> map, Dictionary<string, string> templates)
        {
            foreach (var pair in map) { polish[pair.Key] = pair.Value; Known.Add(pair.Value); }
            foreach (var pair in templates)
            {
                var regex = "^" + Regex.Escape(pair.Key).Replace(@"\{0}", "(.+?)").Replace(@"\{1}", "(.+?)") + "$";
                patterns.Add(new KeyValuePair<Regex, string>(new Regex(regex), pair.Value));
                Known.Add(pair.Value);
            }
        }

        internal static string Translate(string value)
        {
            if (string.IsNullOrEmpty(value)) return value;
            if (polish.TryGetValue(value, out var text)) return text;
            foreach (var pattern in patterns)
            {
                var match = pattern.Key.Match(value);
                if (!match.Success) continue;
                // Inserted parts are key names ("Left Shift") or numbers: translate them too.
                var result = pattern.Value;
                for (var g = 1; g < match.Groups.Count; g++)
                    result = result.Replace("{" + (g - 1) + "}", polish.TryGetValue(match.Groups[g].Value, out var part) ? part : match.Groups[g].Value);
                Known.Add(result);
                return result;
            }
            // Code upper-cases some names ("INTENDED"): same entry in capitals.
            if (value.Length > 1 && value == value.ToUpperInvariant() && Upper().TryGetValue(value, out text)) { Known.Add(text); return text; }
            if (Terms.ByEnglish.TryGetValue(value, out text))
            {
                if (fallbacks++ < 20) Plugin.Logger.LogInfo("Display fallback (I2 English on screen): " + JsonSerializer.Serialize(value));
                return text;
            }
            Unknown(value);
            return value;
        }

        static Dictionary<string, string> Upper()
        {
            if (upper != null) return upper;
            upper = new Dictionary<string, string>(StringComparer.Ordinal);
            foreach (var pair in polish)
            {
                var key = pair.Key.ToUpperInvariant();
                if (key != pair.Key && !polish.ContainsKey(key) && !upper.ContainsKey(key)) upper[key] = pair.Value.ToUpperInvariant();
            }
            return upper;
        }

        /// Visible English we have no entry for: logged once, to find texts set by code.
        static void Unknown(string value)
        {
            if (logged.Count >= 500 || Known.Contains(value) || Terms.Values.Contains(value) || !letters.IsMatch(value)) return;
            var bare = tags.Replace(value, "");  // code wraps our texts in tags: "<size=75%>RATUJ OFIARĘ"
            if (bare != value && (Known.Contains(bare) || Terms.Values.Contains(bare))) return;
            if (logged.Add(value)) Plugin.Logger.LogInfo("Untranslated text: " + JsonSerializer.Serialize(value));
        }

        internal static void BeforeText(ref string __0)
        {
            try { if (!Plugin.Failed) { setterCalls++; __0 = Translate(__0); } }
            catch (Exception e) { Plugin.Logger.LogWarning("Text: " + e.Message); }
        }

        /// Texts serialized in scenes never pass the setter.
        internal static void ReplaceLoaded(bool fontsChanged)
        {
            foreach (var text in Object.FindObjectsOfType<TMP_Text>(true))
            {
                if (text == null) continue;
                var original = text.text;
                var translated = Translate(original);
                if (!ReferenceEquals(translated, original) && translated != original) text.text = translated;
                else if (fontsChanged && text.isActiveAndEnabled)
                {
                    // Laid out before the Polish letters existed: would keep showing boxes.
                    text.havePropertiesChanged = true;
                    text.SetAllDirty();
                }
            }
            foreach (var text in Object.FindObjectsOfType<UnityEngine.UI.Text>(true))
            {
                if (text == null) continue;
                var translated = Translate(text.text);
                if (translated != text.text) text.text = translated;
            }
        }
    }
}
