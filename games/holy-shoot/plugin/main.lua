-- Holy Shoot PL: append "Polski" to the NiceSettings language selector.
--
-- The game builds its main and pause menus from templates: the settings panel's
-- class default object holds "Language Codes" (byte index -> culture), the panel
-- embedded in each menu template holds its own copy of that map, and the
-- switcher template holds the visible "Option Names". Patching these templates
-- before a menu is created gives every menu 11 languages, so the saved index 10
-- resolves to "pl" at startup. Live menus are never touched.
local plan = require("selector").plan
local VERSION = "0.1"
local BASE = "/Game/NiceSettingsMenu/UI/Theme_1/"
local PANELS = {
    BASE .. "WB_T1_PVDSettingsMenu.Default__WB_T1_PVDSettingsMenu_C",
    BASE .. "WB_T1_PVDMainMenu.WB_T1_PVDMainMenu_C:WidgetTree.WB_T1_PVDSettingsMenu",
    BASE .. "WB_T1_PVD_PauseMenu.WB_T1_PVD_PauseMenu_C:WidgetTree.WB_T1_PVDSettingsMenu",
}
local SWITCHER = BASE .. "WB_T1_PVDSettingsMenu.WB_T1_PVDSettingsMenu_C:WidgetTree.WB_T1_OptionSwitcher_Language"
local messages, done = {}, false

local function log(message)
    print("[notgeesePL " .. VERSION .. "] " .. message .. "\n")
end

local function once(message)
    if not messages[message] then messages[message] = true; log(message) end
end

local function text(value)
    if type(value) == "string" then return value end
    return value:ToString()
end

local function found(path)
    local object = StaticFindObject(path)
    if object and object:IsValid() then return object end
end

-- Returns true once the class default, both menu templates and the switcher
-- template carry Polish. Idempotent; templates not loaded yet are retried.
local function patch(trigger)
    local switcher, cdo = found(SWITCHER), found(PANELS[1])
    if not (switcher and cdo) then return false end
    local labels, codes = {}, {}
    switcher["Option Names"]:ForEach(function(_, value) labels[#labels + 1] = text(value:get()) end)
    cdo["Language Codes"]:ForEach(function(key, value) codes[key:get()] = text(value:get()) end)
    local labels_after, index = plan(labels, codes)
    local patched = 0
    for _, path in ipairs(PANELS) do
        local panel = found(path)
        if panel then
            local mapping, has = panel["Language Codes"], false
            mapping:ForEach(function(key) if key:get() == index then has = true end end)
            if not has then mapping:Add(index, "pl") end
            patched = patched + 1
        end
    end
    if #labels < #labels_after then
        local replacement = {}
        for i, label in ipairs(labels_after) do replacement[i] = FText(label) end
        switcher["Option Names"] = replacement
    end
    once("Polski at index " .. index .. " (" .. trigger .. "): templates " .. patched .. "/" .. #PANELS)
    return patched == #PANELS
end

local function try(trigger)
    if done then return end
    local ok, result = pcall(patch, trigger)
    if not ok then once("Not ready (" .. trigger .. "): " .. tostring(result)) end
    done = ok and result
end

log("Loaded")

-- Blueprints create menus through UWidgetBlueprintLibrary::Create; its prehook
-- runs with the widget class loaded but before the instance exists. Confirmed in
-- game (0.1.3 log: "Polski at index 10 (Create)" before the first menu).
local hooked = pcall(RegisterHook, "/Script/UMG.WidgetBlueprintLibrary:Create", function() try("Create") end)
if not hooked then log("Create Widget hook unavailable") end
