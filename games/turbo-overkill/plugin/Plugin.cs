using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text.Json;
using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using HarmonyLib;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Events;
using UnityEngine.AddressableAssets;
using UnityEngine.Localization;
using UnityEngine.Localization.Settings;
using UnityEngine.Localization.Tables;
using UnityEngine.ResourceManagement.AsyncOperations;
using Object = UnityEngine.Object;
using GameLocale = UnityEngine.Localization.Locale;

namespace notgeese.TurboOverkill
{
    // The release before the project rename had a different GUID. If its folder is still in
    // plugins, BepInEx skips this plugin instead of loading two translations at once.
    [BepInIncompatibility("pl.niegesi.turbooverkill")]
    [BepInPlugin(Id, "Turbo Overkill PL", "0.1")]
    public sealed class Plugin : BasePlugin
    {
        public const string Id = "pl.notgeese.turbooverkill";
        internal static ManualLogSource Logger;
        internal static bool Failed, Ready;
        internal static GameLocale Polish;
        internal static readonly Dictionary<string, string> Texts = new Dictionary<string, string>();
        internal static readonly List<StringTable> Tables = new List<StringTable>();
        internal static readonly List<AsyncOperationHandle<StringTable>> Handles = new List<AsyncOperationHandle<StringTable>>();
        internal const string Preference = "notgeese.TurboOverkill.Locale";
        static Harmony harmony;
        static bool tablesRegistered;

        public override void Load()
        {
            Logger = Log;
            try
            {
                Log.LogInfo("PL 0.1; game=" + Application.version + "; Unity=" + Application.unityVersion);
                string folder = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
                foreach (var pair in JsonSerializer.Deserialize<Dictionary<string,string>>(File.ReadAllText(Path.Combine(folder, "pl.json"))))
                    Texts.Add(pair.Key, pair.Value);
                harmony = new Harmony(Id);
                // This hook runs after Unity clears its table cache on a locale change,
                // before it initializes the new locale and notifies UI subscribers.
                harmony.Patch(AccessTools.Method(typeof(LocalizationSettings), "GetInitializationOperation"),
                    prefix: new HarmonyMethod(typeof(Plugin), nameof(BeforeInitialization)));
                harmony.Patch(AccessTools.Method(typeof(LocalizationSettings), "SendLocaleChangedEvents"),
                    prefix: new HarmonyMethod(typeof(Plugin), nameof(BeforeLocaleChanged)));
                harmony.Patch(AccessTools.Method(typeof(UiLanguageSelector), "Awake"),
                    postfix: new HarmonyMethod(typeof(Plugin), nameof(AfterSelectorAwake)));
                harmony.Patch(AccessTools.PropertySetter(typeof(Text), "text"),
                    prefix: new HarmonyMethod(typeof(Fonts), nameof(Fonts.BeforeText)));
                harmony.Patch(AccessTools.Method(typeof(LocalizedFont), "TextUpdated"),
                    postfix: new HarmonyMethod(typeof(Fonts), nameof(Fonts.AfterFont)));
                AddComponent<Runtime>();
                Log.LogInfo("Plugin loaded; waiting for localization. Translated entries: " + Texts.Count);
            }
            catch (Exception e) { Disable(e); }
        }

        internal static bool IsPolish()
        {
            return Ready && !Failed && LocalizationSettings.SelectedLocale != null && LocalizationSettings.SelectedLocale.Identifier.Code == "pl";
        }

        internal static void Disable(Exception e)
        {
            if (Failed) return;
            Failed = true;
            Logger.LogError("PL disabled; original game remains available: " + e);
            try { harmony?.UnpatchSelf(); } catch (Exception cleanup) { Logger.LogWarning(cleanup.Message); }
            try
            {
                if (LocalizationSettings.HasSettings && LocalizationSettings.SelectedLocale?.Identifier.Code == "pl")
                    LocalizationSettings.SelectedLocale = LocalizationSettings.AvailableLocales.GetLocale(new LocaleIdentifier("en"));
                Fonts.Restore();
            }
            catch (Exception cleanup) { Logger.LogWarning(cleanup.Message); }
        }

        static void BeforeInitialization()
        {
            if (!Ready || Failed) return;
            try { RegisterTables(); } catch (Exception e) { Disable(e); }
        }

        static void BeforeLocaleChanged()
        {
            // The native method clears both table caches before GetInitializationOperation.
            tablesRegistered = false;
        }

        internal static void RegisterTables()
        {
            if (tablesRegistered) return;
            var db = LocalizationSettings.StringDatabase;
            Logger.LogInfo("Registering PL table cache.");
            for (int i = 0; i < Tables.Count; i++)
            {
                var table = Tables[i];
                // Never pass ValueTuple<LocaleIdentifier,string> through generic interop.
                // The captured 0.1.0 crashes terminate inside Dictionary.ContainsKey;
                // RegisterTableOperation constructs and checks those keys natively.
                // Retain one root reference; the name and GUID cache own separate refs.
                Addressables.ResourceManager.Acquire((AsyncOperationHandle)Handles[i]);
                db.RegisterTableOperation(Handles[i], Polish.Identifier, table.TableCollectionName);
                Logger.LogInfo("Registered PL table: " + table.TableCollectionName);
            }
            tablesRegistered = true;
        }

        static void AfterSelectorAwake(UiLanguageSelector __instance)
        {
            if (!Ready || Failed) return;
            try
            {
                Selector.Add(__instance);
                if (PlayerPrefs.GetString(Preference, "") == "pl" && !IsPolish())
                    LocalizationSettings.SelectedLocale = Polish;
            }
            catch (Exception e) { Logger.LogWarning("Selector: " + e); }
        }

        internal static void SelectPolish(UiLanguageSelector selector)
        {
            if (!Ready || Failed) return;
            try
            {
                // Keep the game's own close-panel/settings behavior. English remains
                // the safe native preference when the plugin is removed.
                selector.SetLanguage_English();
                LocalizationSettings.SelectedLocale = Polish;
                PlayerPrefs.SetString(Preference, "pl");
                PlayerPrefs.Save();
                Logger.LogInfo("Selected Polski.");
            }
            catch (Exception e) { Disable(e); }
        }
    }

    public sealed class Runtime : MonoBehaviour
    {
        readonly List<AsyncOperationHandle<StringTable>> loads = new List<AsyncOperationHandle<StringTable>>();
        readonly string[] names = { "TurboStrings", "TurboVoices", "TurboGame", "TurboCodex", "TurboBestiary", "TurboItems", "TurboEx1", "TurboIndodex2" };
        bool started;
        float nextScan;
        string lastLocale;
        public Runtime(IntPtr ptr) : base(ptr) { }

        public void Update()
        {
            if (Plugin.Failed) return;
            try
            {
                if (!Plugin.Ready)
                {
                    if (!LocalizationSettings.HasSettings || !LocalizationSettings.InitializationOperation.IsDone) return;
                    if (!started)
                    {
                        var english = LocalizationSettings.AvailableLocales.GetLocale(new LocaleIdentifier("en"));
                        if (english == null) throw new InvalidOperationException("English locale not found.");
                        foreach (string name in names)
                            loads.Add(LocalizationSettings.StringDatabase.GetTableAsync((TableReference)name, english));
                        started = true;
                        return;
                    }
                    foreach (var load in loads) if (!load.IsDone) return;
                    BuildTables();
                    Plugin.Ready = true;
                    Plugin.RegisterTables();
                    if (PlayerPrefs.GetString(Plugin.Preference, "") == "pl")
                        LocalizationSettings.SelectedLocale = Plugin.Polish;
                    lastLocale = LocalizationSettings.SelectedLocale.Identifier.Code;
                    Plugin.Logger.LogInfo("Polski ready; EN tables intact, original fallback preserved.");
                }
                var locale = LocalizationSettings.SelectedLocale.Identifier.Code;
                if (locale != lastLocale)
                {
                    lastLocale = locale;
                    PlayerPrefs.SetString(Plugin.Preference, locale);
                    PlayerPrefs.Save();
                    if (locale != "pl") Fonts.Restore();
                    Plugin.Logger.LogInfo("Locale: " + locale);
                }
                if (Time.unscaledTime < nextScan) return;
                nextScan = Time.unscaledTime + 2;
                foreach (var selector in Object.FindObjectsOfType<UiLanguageSelector>(true)) Selector.Add(selector);
                if (Plugin.IsPolish())
                    foreach (var text in Object.FindObjectsOfType<Text>(true)) Fonts.Apply(text, text.text);
            }
            catch (Exception e) { Plugin.Disable(e); }
        }

        void BuildTables()
        {
            Plugin.Polish = GameLocale.CreateLocale("pl");
            Plugin.Polish.LocaleName = "Polski";
            var fallback = new UnityEngine.Localization.Metadata.FallbackLocale();
            fallback.m_Locale = LocalizationSettings.AvailableLocales.GetLocale(new LocaleIdentifier("en"));
            Plugin.Polish.Metadata.AddMetadata(fallback.Cast<UnityEngine.Localization.Metadata.IMetadata>());
            Object.DontDestroyOnLoad(Plugin.Polish);
            int applied = 0, missing = 0;
            foreach (var load in loads)
            {
                if (load.Status != AsyncOperationStatus.Succeeded || load.Result == null)
                    throw new InvalidOperationException("Cannot load English table; " + load.OperationException);
                // Retain the English operation: PL copies still reference its shared data.
                Addressables.ResourceManager.Acquire((AsyncOperationHandle)load);
                // Only in-memory copies, never shipped or saved as modified game assets.
                var table = Object.Instantiate(load.Result);
                table.name = load.Result.name + " notgeese PL";
                table.LocaleIdentifier = new LocaleIdentifier("pl");
                Object.DontDestroyOnLoad(table);
                string guid = table.SharedData.m_TableCollectionNameGuidString;
                for (int i = 0; i < table.TableData.Count; i++)
                {
                    var entry = table.TableData[i];
                    if (entry.Pointer == load.Result.TableData[i].Pointer)
                        throw new InvalidOperationException("Clone shares mutable entry data with English.");
                    string value;
                    if (Plugin.Texts.TryGetValue(guid + ":" + entry.m_Id, out value))
                    { entry.m_Localized = value; applied++; }
                    else if (!string.IsNullOrEmpty(entry.m_Localized)) missing++;
                }
                table.OnAfterDeserialize();
                Plugin.Tables.Add(table);
                Plugin.Handles.Add(Addressables.ResourceManager.CreateCompletedOperation(table, null));
                Plugin.Logger.LogInfo("PL table: " + table.TableCollectionName + "; entries=" + table.Count);
            }
            if (applied == 0) throw new InvalidOperationException("No translation IDs matched the installed game.");
            LocalizationSettings.AvailableLocales.Locales.Add(Plugin.Polish);
            Plugin.Logger.LogInfo("Translated=" + applied + "; English fallback (missing PL)=" + missing);
        }
    }

    static class Selector
    {
        const string ButtonName = "notgeese_Polski";
        static Sprite flag;
        internal static void Add(UiLanguageSelector selector)
        {
            if (selector == null || selector.transform.Find(ButtonName) != null) return;
            Button english = null;
            var buttons = new List<Button>();
            foreach (var button in selector.GetComponentsInChildren<Button>(true))
            {
                bool language = false;
                // GetPersistentMethodName calls stripped PersistentCallGroup.GetListener.
                // The serialized fields still exist and are exposed by IL2CPP bindings.
                var calls = button.onClick.m_PersistentCalls?.m_Calls;
                for (int i = 0; calls != null && i < calls.Count; i++)
                {
                    string method = calls[i].m_MethodName ?? "";
                    if (method.StartsWith("SetLanguage_")) language = true;
                    if (method == "SetLanguage_English") english = button;
                }
                if (language) buttons.Add(button);
            }
            if (english == null) return;
            var go = Object.Instantiate(english.gameObject, english.transform.parent, false);
            go.name = ButtonName;
            var added = go.GetComponent<Button>();
            // New event also drops serialized persistent listeners from the clone.
            added.onClick = new Button.ButtonClickedEvent();
            added.onClick.AddListener((UnityAction)(Action)(() => Plugin.SelectPolish(selector)));
            foreach (var label in go.GetComponentsInChildren<Text>(true)) label.text = "Polski";
            foreach (var image in go.GetComponentsInChildren<Image>(true))
                if (image.gameObject != go) { image.sprite = Flag(); image.color = Color.white; image.type = Image.Type.Simple; image.preserveAspect = true; }
            buttons.Sort((a,b) => b.GetComponent<RectTransform>().anchoredPosition.y.CompareTo(a.GetComponent<RectTransform>().anchoredPosition.y));
            buttons.Add(added);
            var panel = english.transform.parent.Cast<RectTransform>();
            float height = panel.rect.height;
            if (height <= 0) height = panel.sizeDelta.y;
            if (height > 0)
            {
                float slot = height / (buttons.Count + 1);
                for (int i = 0; i < buttons.Count; i++)
                {
                    var rect = buttons[i].GetComponent<RectTransform>();
                    rect.anchoredPosition = new Vector2(rect.anchoredPosition.x, -slot * (i + 1));
                    rect.sizeDelta = new Vector2(rect.sizeDelta.x, Math.Min(rect.sizeDelta.y, slot * 0.85f));
                    var nav = buttons[i].navigation; nav.mode = Navigation.Mode.Automatic; buttons[i].navigation = nav;
                }
            }
            go.SetActive(true);
            Plugin.Logger.LogInfo("Selector extended: Polski + Polish flag; languages=" + buttons.Count);
        }

        static Sprite Flag()
        {
            if (flag != null) return flag;
            var texture = new Texture2D(32, 20, TextureFormat.RGBA32, false);
            for (int y = 0; y < 20; y++) for (int x = 0; x < 32; x++)
                texture.SetPixel(x, y, y >= 10 ? Color.white : new Color(0.86f, 0.078f, 0.235f, 1));
            texture.Apply(); texture.name = "notgeese Polish flag";
            Object.DontDestroyOnLoad(texture);
            flag = Sprite.Create(texture, new Rect(0, 0, 32, 20), new Vector2(0.5f, 0.5f));
            Object.DontDestroyOnLoad(flag);
            return flag;
        }
    }

    static class Fonts
    {
        static Font fallback;
        static readonly Dictionary<int, Tuple<Text, Font>> originals = new Dictionary<int, Tuple<Text, Font>>();
        internal static void BeforeText(Text __instance, ref string __0)
        {
            try
            {
                if (!Plugin.IsPolish()) return;
                var original = originals.TryGetValue(__instance.GetInstanceID(), out var saved) ? saved.Item2 : __instance.font;
                // Disket renders lowercase Latin letters as capitals. Preserve that look
                // when replacing it, without changing rich-text tags or sprite names.
                if (original != null && original.name.StartsWith("Disket") && __0 != null)
                    __0 = System.Text.RegularExpressions.Regex.Replace(__0, @"<[^>]*>|\[[^\]]*\]|\{[^}]*\}|[^<\[{]+", m => "<[{".IndexOf(m.Value[0]) >= 0 ? m.Value : m.Value.ToUpperInvariant());
                Apply(__instance, __0);
            }
            catch (Exception e) { Plugin.Logger.LogWarning("Font: " + e.Message); }
        }
        internal static void AfterFont(LocalizedFont __instance)
        { try { if (Plugin.IsPolish()) { var t = __instance.GetComponent<Text>(); if (t != null) Apply(t,t.text); } } catch (Exception e) { Plugin.Logger.LogWarning("Font: " + e.Message); } }
        internal static void Apply(Text text, string value)
        {
            if (text == null || text.font == null || string.IsNullOrEmpty(value)) return;
            // Font.HasCharacter can report OS fallback glyphs as present. These local
            // font families were checked in their actual cmap and lack Polish glyphs.
            string name = text.font.name;
            bool missing = name.StartsWith("Disket") || name.StartsWith("ZeF RAVE") || name == "TapeFont_HighQuality" || name == "TapeFont_LowQuality";
            foreach (char c in value)
                if ("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ".IndexOf(c) >= 0 && !text.font.HasCharacter(c)) { missing = true; break; }
            if (!missing) return;
            if (fallback == null)
            {
                foreach (var f in Resources.FindObjectsOfTypeAll<Font>())
                    if (f.name == "Oxanium-Regular") { fallback = f; break; }
                if (fallback == null) fallback = Font.CreateDynamicFontFromOSFont("Arial", 32);
                Object.DontDestroyOnLoad(fallback);
                Plugin.Logger.LogInfo("Polish glyph fallback: " + fallback.name);
            }
            if (!originals.ContainsKey(text.GetInstanceID())) originals.Add(text.GetInstanceID(), Tuple.Create(text, text.font));
            text.font = fallback;
        }
        internal static void Restore()
        {
            foreach (var pair in originals.Values)
                if (pair.Item1 != null && pair.Item1.font == fallback) pair.Item1.font = pair.Item2;
            originals.Clear();
        }
    }
}

