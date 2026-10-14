// Silver Pines minimap: BepInEx 6 IL2CPP plugin, personal-use QoL.
//
// The game has a gameplay quick map: QuickMapPanel (scene GameUI) shows QuickMapMinimap, a
// full-screen frame with a masked 1920x1080 RawImage of the 3D map camera, centred on the player
// every frame by UIMap3DPanel. QuickMapPanel.Update shows or hides it (speed-based DOFade) when
// m_shouldShow differs from m_isShowing. Before each Update we set m_shouldShow and the fade
// speeds, and switch the frame between a small corner box and the original layout. The player's
// own quick-map state (PlayerQuickMapControls) is never written. OpenFullMap is blocked while only
// the minimap is shown, so its button keeps working only on the native quick map.
//
// Free play only: hidden while the game's own UI reports a cutscene, dialogue (phone calls drive
// CinematicBarsUI), examination, item pickup, notes reader or inventory interaction. The frame
// uses the game's GrittyPanelDoubleSided sprite, already loaded by GameUI, for the map mask and a
// dark border. No game file is changed or shipped.

using System;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using HarmonyLib;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace notgeese.SilverPinesMinimap
{
    [BepInPlugin(Id, "Silver Pines Minimap", Version)]
    public sealed class Plugin : BasePlugin
    {
        public const string Id = "pl.notgeese.silverpines.minimap";
        public const string Version = "1.0.0";
        const string FrameSprite = "GrittyPanelDoubleSided";
        internal static ManualLogSource Logger;
        static Harmony harmony;
        static bool failed;

        static ConfigEntry<bool> enabled;
        static ConfigEntry<Key> toggleKey;
        static ConfigEntry<float> width, height, marginX, marginY, mapScale, fadeSeconds, settleSeconds, borderOpacity, borderWidth;
        static ConfigEntry<bool> top, right;

        static PlayerQuickMapControls controls;
        static int controlsFrame = -100;
        static string lastState = "";
        static float readySince = -1f;

        // Per panel instance: original layout and the game UI that tells us about interactions.
        static IntPtr owner;
        static CanvasGroup group;
        static RectTransform frame, view, prompts, floors;
        static Vector2 aMin, aMax, pivot, pos, size;
        static Vector3 viewScale, promptsScale, floorsScale;
        static float fadeIn, fadeOut;
        static Image mask, border;
        static Sprite maskSprite;
        static Image.Type maskType;
        static float maskPpu;
        static bool compact;
        static UIHideDuringCutscenes[] cutsceneHiders;
        static CinematicBarsUI bars;
        static DialoguePanel dialogue;
        static ExaminationInfoDisplay examine;
        static InventoryItemPickupPanel pickup;
        static GameNotesReaderPanel notes;
        static InventoryInteractionPanel interact;

        public override void Load()
        {
            Logger = Log;
            try
            {
                Log.LogInfo("Minimap " + Version + "; game=" + Application.version + "; Unity=" + Application.unityVersion);
                enabled = Config.Bind("Minimap", "Enabled", true, "Show the quick map as a corner minimap during free play.");
                toggleKey = Config.Bind("Minimap", "ToggleKey", Key.F7, "Key that turns the minimap on and off.");
                fadeSeconds = Config.Bind("Minimap", "FadeSeconds", 0.4f, "Minimap fade in/out time.");
                settleSeconds = Config.Bind("Minimap", "SettleSeconds", 0.5f, "Free play must last this long before the minimap returns.");
                width = Config.Bind("Layout", "Width", 420f, "Frame width in UI units (1920x1080 reference).");
                height = Config.Bind("Layout", "Height", 300f, "Frame height in UI units.");
                marginX = Config.Bind("Layout", "MarginX", 24f, "Distance from the left/right screen edge.");
                marginY = Config.Bind("Layout", "MarginY", 24f, "Distance from the top/bottom screen edge.");
                top = Config.Bind("Layout", "Top", true, "Top corner (false = bottom).");
                right = Config.Bind("Layout", "Right", true, "Right corner (false = left).");
                mapScale = Config.Bind("Layout", "MapScale", 0.5f, "Map image scale inside the frame; lower shows more area. 1 = quick map scale.");
                borderOpacity = Config.Bind("Layout", "BorderOpacity", 0.8f, "Opacity of the dark torn border (0 = none).");
                borderWidth = Config.Bind("Layout", "BorderWidth", 7f, "How far the dark border reaches past the map edge, in UI units.");

                harmony = new Harmony(Id);
                harmony.Patch(AccessTools.Method(typeof(QuickMapPanel), "Update"),
                    prefix: new HarmonyMethod(typeof(Plugin), nameof(BeforePanelUpdate)));
                harmony.Patch(AccessTools.Method(typeof(QuickMapPanel), "OpenFullMap"),
                    prefix: new HarmonyMethod(typeof(Plugin), nameof(BeforeOpenFullMap)));
                harmony.Patch(AccessTools.Method(typeof(PlayerQuickMapControls), "Update"),
                    postfix: new HarmonyMethod(typeof(Plugin), nameof(AfterControlsUpdate)));
                Log.LogInfo("Minimap ready; toggle " + toggleKey.Value + ", enabled " + enabled.Value + ".");
            }
            catch (Exception e) { Disable(e); }
        }

        static void Disable(Exception e)
        {
            if (failed) return;
            failed = true;
            Logger.LogError("Minimap disabled, the game keeps its own quick map: " + e);
            try { harmony?.UnpatchSelf(); } catch (Exception cleanup) { Logger.LogWarning(cleanup.Message); }
        }

        static void AfterControlsUpdate(PlayerQuickMapControls __instance)
        {
            controls = __instance;
            controlsFrame = Time.frameCount;
        }

        static bool NativeShowing()
        {
            return controls != null && Time.frameCount - controlsFrame <= 2 && controls.ShowingMap;
        }

        static bool BeforeOpenFullMap()
        {
            return failed || NativeShowing();
        }

        static string Interaction()
        {
            if (GameplayUIContainer.m_uiDisabled) return "gameplay UI disabled";
            foreach (var h in cutsceneHiders)
                if (h != null && (h.m_isCutscenePlaying || h.m_isInCutsceneLevel || h.m_dialoguePlaying)) return "cutscene/dialogue";
            if (bars != null && (bars.m_isInDialogue || bars.m_isPlayingInGameCutscene || bars.m_isPlayingVideoCutscene)) return "phone dialogue/cutscene";
            if (dialogue != null && dialogue.m_isShown) return "dialogue";
            if (examine != null && examine.m_isActive) return "examination";
            if (pickup != null && pickup.m_isShowing) return "item pickup";
            if (notes != null && notes.m_isActive) return "notes reader";
            if (interact != null && interact.m_isShowing) return "inventory interaction";
            return null;
        }

        static void BeforePanelUpdate(QuickMapPanel __instance)
        {
            if (failed) return;
            try
            {
                Capture(__instance);
                var keyboard = Keyboard.current;
                if (keyboard != null && keyboard[toggleKey.Value].wasPressedThisFrame)
                {
                    enabled.Value = !enabled.Value;
                    Logger.LogInfo("Minimap " + (enabled.Value ? "on" : "off") + ".");
                }

                bool native = NativeShowing();
                string state, why;
                if (native) state = "native quick map";
                else if (!enabled.Value) state = "off";
                else if (Time.frameCount - controlsFrame > 2) state = "hidden: player controls inactive";
                else if (!controls.IsMapEnabled()) state = "hidden: map disabled";
                else if (Time.timeScale == 0f) state = "hidden: paused";
                // The map's shared RenderTexture appears a little after the level; showing earlier
                // throws inside MapSceneManager.SetMapActive.
                else if (MapSceneManager.RenderTexture == null) state = "hidden: map not loaded";
                else if ((why = Interaction()) != null) state = "hidden: " + why;
                else state = "minimap";
                // Hide at once, show only after free play held for a moment.
                if (state == "minimap")
                {
                    if (readySince < 0f) readySince = Time.unscaledTime;
                    if (Time.unscaledTime - readySince < settleSeconds.Value) state = "waiting";
                }
                else readySince = -1f;
                if (state != lastState && state != "waiting")
                {
                    Logger.LogInfo("State: " + state + ".");
                    lastState = state;
                }

                bool show;
                if (native)
                {
                    SetCompact(false);
                    show = true;
                }
                else if (state == "minimap")
                {
                    // Leaving the native quick map: let it fade out full-size, then fade in small.
                    if (!compact && (__instance.m_isShowing || group.alpha > 0.01f)) show = false;
                    else { SetCompact(true); show = true; }
                }
                else show = false; // keep the current layout while it fades out
                float speed = 1f / Mathf.Max(0.05f, fadeSeconds.Value);
                __instance.m_fadeInSpeed = compact ? speed : fadeIn;
                __instance.m_fadeOutSpeed = compact ? speed : fadeOut;
                // The panel compares this with m_isShowing in its own Update right after us.
                __instance.m_shouldShow = show;
            }
            catch (Exception e) { SetCompact(false); Disable(e); }
        }

        static void Capture(QuickMapPanel panel)
        {
            if (owner == panel.Pointer && frame != null) return;
            owner = panel.Pointer;
            compact = false;
            group = panel.m_canvasGroup;
            frame = group.GetComponent<RectTransform>();
            aMin = frame.anchorMin; aMax = frame.anchorMax; pivot = frame.pivot;
            pos = frame.anchoredPosition; size = frame.sizeDelta;
            fadeIn = panel.m_fadeInSpeed; fadeOut = panel.m_fadeOutSpeed;
            view = panel.m_mapViewer.GetComponent<RectTransform>();
            viewScale = view.localScale;
            prompts = frame.Find("MenuButtonPrompts")?.GetComponent<RectTransform>();
            floors = frame.Find("MapFloorsInfo")?.GetComponent<RectTransform>();
            if (prompts != null) promptsScale = prompts.localScale;
            if (floors != null) floorsScale = floors.localScale;
            mask = frame.Find("Mask")?.GetComponent<Image>();
            if (mask != null) { maskSprite = mask.sprite; maskType = mask.type; maskPpu = mask.pixelsPerUnitMultiplier; }

            var root = panel.transform.root;
            cutsceneHiders = root.GetComponentsInChildren<UIHideDuringCutscenes>(true);
            bars = root.GetComponentInChildren<CinematicBarsUI>(true);
            dialogue = root.GetComponentInChildren<DialoguePanel>(true);
            examine = root.GetComponentInChildren<ExaminationInfoDisplay>(true);
            pickup = root.GetComponentInChildren<InventoryItemPickupPanel>(true);
            notes = root.GetComponentInChildren<GameNotesReaderPanel>(true);
            interact = root.GetComponentInChildren<InventoryInteractionPanel>(true);

            Sprite gritty = null;
            foreach (var image in root.GetComponentsInChildren<Image>(true))
                if (image.sprite != null && image.sprite.name == FrameSprite) { gritty = image.sprite; break; }
            border = null;
            if (gritty != null && mask != null)
            {
                var go = new GameObject("notgeese_MinimapBorder");
                var rt = go.AddComponent<RectTransform>();
                rt.SetParent(frame, false);
                rt.SetSiblingIndex(mask.transform.GetSiblingIndex());
                border = go.AddComponent<Image>();
                border.sprite = gritty;
                border.type = Image.Type.Sliced;
                border.pixelsPerUnitMultiplier = 4f;
                border.raycastTarget = false;
                go.SetActive(false);
                maskGritty = gritty;
            }
            Logger.LogInfo("Quick map captured: anchors " + aMin + "-" + aMax + ", fade " + fadeIn + "/" + fadeOut
                + ", cutscene hiders " + cutsceneHiders.Length + ", bars " + (bars != null) + ", dialogue " + (dialogue != null)
                + ", examine " + (examine != null) + ", pickup " + (pickup != null) + ", notes " + (notes != null)
                + ", interact " + (interact != null)
                + ", mask " + (mask != null) + ", frame sprite " + (gritty != null) + ".");
        }

        static Sprite maskGritty;

        static void SetCompact(bool on)
        {
            if (frame == null || on == compact) return;
            compact = on;
            if (!on) { Restore(); return; }
            float x = right.Value ? 1f : 0f, y = top.Value ? 1f : 0f;
            frame.anchorMin = frame.anchorMax = frame.pivot = new Vector2(x, y);
            frame.anchoredPosition = new Vector2(right.Value ? -marginX.Value : marginX.Value,
                                                 top.Value ? -marginY.Value : marginY.Value);
            frame.sizeDelta = new Vector2(width.Value, height.Value);
            view.localScale = viewScale * mapScale.Value;
            if (prompts != null) prompts.localScale = Vector3.zero;
            if (floors != null) floors.localScale = Vector3.zero;
            if (maskGritty != null)
            {
                mask.sprite = maskGritty;
                mask.type = Image.Type.Sliced;
                mask.pixelsPerUnitMultiplier = 5f;
            }
            if (border != null && borderOpacity.Value > 0f)
            {
                // Same rect as the mask (inset and shifted inside the frame), grown evenly.
                var m = mask.rectTransform;
                var b = border.rectTransform;
                b.anchorMin = m.anchorMin; b.anchorMax = m.anchorMax; b.pivot = m.pivot;
                b.anchoredPosition = m.anchoredPosition;
                b.sizeDelta = m.sizeDelta + Vector2.one * (2f * borderWidth.Value);
                border.color = new Color(0.05f, 0.05f, 0.05f, borderOpacity.Value);
                border.gameObject.SetActive(true);
            }
        }

        static void Restore()
        {
            compact = false;
            if (frame == null) return;
            frame.anchorMin = aMin; frame.anchorMax = aMax; frame.pivot = pivot;
            frame.anchoredPosition = pos; frame.sizeDelta = size;
            if (view != null) view.localScale = viewScale;
            if (prompts != null) prompts.localScale = promptsScale;
            if (floors != null) floors.localScale = floorsScale;
            if (mask != null) { mask.sprite = maskSprite; mask.type = maskType; mask.pixelsPerUnitMultiplier = maskPpu; }
            if (border != null) border.gameObject.SetActive(false);
        }
    }
}
