// Not Geese: Polish for Rain World as a separate game language.
//
// Rain World has its own BepInEx and mod system (Remix). Languages are an extensible
// ExtEnum, and the game reads texts from text/text_<first three letters of the name>/, mod
// folders included. So it's enough to register the language "Polish" (text_pol sits next to
// it in the same mod) and add it to the options menu language list, a fixed array in code.
// No game file is replaced; other languages work as before.

using System;
using System.Collections.Generic;
using System.Reflection;
using System.Reflection.Emit;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using UnityEngine;

namespace notgeese.RainWorldPL
{
    // The release before the project rename had a different GUID. If its folder is still in
    // plugins, BepInEx skips this plugin instead of loading two translations at once.
    [BepInIncompatibility("niegesi.rainworld.polski")]
    [BepInPlugin(Id, "Rain World PL", Version)]
    public class Plugin : BaseUnityPlugin
    {
        public const string Id = "notgeese.rainworld.polski";
        public const string Version = "0.1";

        // ExtEnum value name. The first three letters pick the text folder: text_pol.
        internal const string LanguageName = "Polish";

        internal static ManualLogSource Log;
        internal static InGameTranslator.LanguageID Polish;

        private void Awake()
        {
            Log = Logger;
            Logger.LogInfo(string.Format("PL {0}; game {1}, Unity {2}.", Version, GameVersion(), Application.unityVersion));

            try
            {
                Polish = new InGameTranslator.LanguageID(LanguageName, true);
                Logger.LogInfo("Registered language " + LanguageName + " (index " + Polish.Index + ").");
            }
            catch (Exception error)
            {
                Logger.LogError("Could not add the language, the game stays without Polish: " + error);
                return;
            }

            var harmony = new Harmony(Id);
            Patch(harmony, typeof(OptionsMenuPatch), "options language list");
            Patch(harmony, typeof(ShortStringsPatch), "Polish UI texts");
            Patch(harmony, typeof(DecryptPatch), "chatlogs and developer commentary");
            Patch(harmony, typeof(MissingPatch), "missing text log");
        }

        // Each patch separately: if a game update changes one place, the rest keeps working.
        private void Patch(Harmony harmony, Type patch, string what)
        {
            try
            {
                harmony.PatchAll(patch);
            }
            catch (Exception error)
            {
                Logger.LogWarning("Patch not applied (" + what + "): " + error.Message);
            }
        }

        private void OnApplicationQuit()
        {
            if (MissingPatch.Seen.Count > 0)
                Logger.LogInfo("Texts without Polish translation this session: " + MissingPatch.Seen.Count + ".");
        }

        // By name, not type: a missing field in another game version must not crash the plugin.
        private static string GameVersion()
        {
            try
            {
                var field = AccessTools.Field(typeof(global::RainWorld), "GAME_VERSION_STRING");
                return field != null ? (string)field.GetValue(null) : "?";
            }
            catch (Exception)
            {
                return "?";
            }
        }

        internal static bool PolishActive()
        {
            var world = RWCustom.Custom.rainWorld;
            return Polish != null && world != null && world.inGameTranslator != null
                && world.inGameTranslator.currentLanguage == Polish;
        }
    }

    /// The options menu builds buttons from the languageOrder array (ten languages in code).
    /// Polish is added right before the array is stored in the field.
    [HarmonyPatch(typeof(Menu.OptionsMenu), MethodType.Constructor, new[] { typeof(ProcessManager) })]
    internal static class OptionsMenuPatch
    {
        private static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
        {
            var field = AccessTools.Field(typeof(Menu.OptionsMenu), "languageOrder");
            var add = AccessTools.Method(typeof(OptionsMenuPatch), nameof(AddPolish));
            var done = false;
            foreach (var instruction in instructions)
            {
                if (!done && field != null && instruction.opcode == OpCodes.Stfld && Equals(instruction.operand, field))
                {
                    yield return new CodeInstruction(OpCodes.Call, add);
                    done = true;
                }
                yield return instruction;
            }
            if (!done)
                Plugin.Log.LogWarning("Options menu language list not found; Polish is selectable only if already set.");
        }

        private static InGameTranslator.LanguageID[] AddPolish(InGameTranslator.LanguageID[] order)
        {
            if (Plugin.Polish == null || Array.IndexOf(order, Plugin.Polish) >= 0) return order;
            var extended = new InGameTranslator.LanguageID[order.Length + 1];
            order.CopyTo(extended, 0);
            extended[order.Length] = Plugin.Polish;
            return extended;
        }
    }

    /// The game loads the English strings.txt, then the current language's table, but only if
    /// that sits in the base game dir (StreamingAssets/text/text_pol). Ours is in the mod folder,
    /// so we load it ourselves in the game's format. English stays underneath: what has no
    /// Polish shows in English.
    [HarmonyPatch(typeof(InGameTranslator), "LoadShortStrings")]
    internal static class ShortStringsPatch
    {
        internal const string File = "text/text_pol/strings.txt";
        internal static readonly HashSet<string> Keys = new HashSet<string>(StringComparer.Ordinal);
        private static int logged = -1;

        private static void Postfix(InGameTranslator __instance)
        {
            try
            {
                if (!Plugin.PolishActive()) return;
                var path = AssetManager.ResolveFilePath(File);
                if (!System.IO.File.Exists(path))
                {
                    Plugin.Log.LogWarning("Missing " + File + " in the mod; texts stay English.");
                    return;
                }
                var text = System.IO.File.ReadAllText(path, System.Text.Encoding.UTF8);
                if (text.Length > 0 && text[0] == '0') text = text.Substring(1);
                var table = MissingPatch.ShortStrings(__instance);
                var count = 0;
                foreach (var raw in text.Split(new[] { "\r\n", "\n" }, StringSplitOptions.None))
                {
                    var line = raw.Contains("///") ? raw.Split('/')[0].TrimEnd() : raw;
                    var bar = line.IndexOf('|');
                    if (bar <= 0 || bar == line.Length - 1) continue;
                    var key = line.Substring(0, bar);
                    table[key] = line.Substring(bar + 1);
                    Keys.Add(key);
                    count++;
                }
                if (count != logged)
                {
                    Plugin.Log.LogInfo("Loaded " + count + " Polish texts from " + path + ".");
                    logged = count;
                }
            }
            catch (Exception error)
            {
                Plugin.Log.LogError("Could not load Polish texts: " + error.Message);
            }
        }
    }

    /// Downpour chatlogs, broadcasts and developer commentary are decrypted unconditionally
    /// (ChatlogData.DecryptResult). Our files are plain text starting with marker 0; those pass
    /// unchanged. Encrypted originals start with 1 and go through as before.
    [HarmonyPatch(typeof(MoreSlugcats.ChatlogData), "DecryptResult")]
    internal static class DecryptPatch
    {
        private static bool Prefix(string __0, ref string __result)
        {
            var text = __0 == null ? null : __0.TrimStart('﻿');
            if (string.IsNullOrEmpty(text) || text[0] != '0') return true;
            __result = text;
            return false;
        }
    }

    /// The game already handles a missing Polish entry by showing English. Each such text is
    /// logged once so a player's report says what's missing.
    [HarmonyPatch(typeof(InGameTranslator), nameof(InGameTranslator.Translate))]
    internal static class MissingPatch
    {
        internal static readonly HashSet<string> Seen = new HashSet<string>(StringComparer.Ordinal);
        internal static readonly AccessTools.FieldRef<InGameTranslator, Dictionary<string, string>> ShortStrings =
            AccessTools.FieldRefAccess<InGameTranslator, Dictionary<string, string>>("shortStrings");

        private static void Postfix(InGameTranslator __instance, string s)
        {
            try
            {
                if (string.IsNullOrEmpty(s) || !Plugin.PolishActive()) return;
                if (ShortStringsPatch.Keys.Count > 0 && !ShortStringsPatch.Keys.Contains(s) && Seen.Add(s))
                    Plugin.Log.LogInfo("No translation: " + s.Replace("\n", "\\n"));
            }
            catch (Exception)
            {
                // Diagnostics only; never gets in the game's way.
            }
        }
    }
}
