-- Somber Echoes PL: extend the native language list without replacing any culture.
local VERSION = "0.1"
local SETTINGS = "/Game/Blueprints/Systems/Setting/Settings_BP.Settings_BP_C:"
local UI = "/Game/Blueprints/UI/Menus/Settings/UI_Settings-Text_BP.UI_Settings-Text_BP_C:"
local installed, reported, disabled = {}, {}, {}

local function log(message)
    print("[notgeesePL " .. VERSION .. "] " .. message .. "\n")
end

local function once(message)
    if not reported[message] then reported[message] = true; log(message) end
end

local function string_value(value)
    if type(value) == "string" then return value end
    return value:ToString()
end

local function guard(name, callback)
    return function(...)
        if disabled[name] then return end
        local ok, failure = pcall(callback, ...)
        if not ok then
            disabled[name] = true
            once(name .. " disabled: " .. tostring(failure))
        end
    end
end

local callbacks = {
    [SETTINGS .. "Get Languages"] = guard("language list", function(_, output)
        local codes, present = {}, false
        output:get():ForEach(function(_, item)
            local code = string_value(item:get())
            assert(code ~= "", "Empty culture in the game's list")
            codes[#codes + 1] = code
            if code == "pl" then present = true end
        end)
        assert(#codes > 0, "The game's language list is empty")
        if not present then
            codes[#codes + 1] = "pl"
            output:set(codes)
            once("Polish appended to the native language list")
        end
    end),
    [UI .. "LanguageHack"] = guard("language label", function(_, id, label)
        if string_value(id:get()) == "pl" then
            label:set(FText("Polski"))
            once("Polski label supplied")
        end
    end),
}

local function install()
    for path, callback in pairs(callbacks) do
        if not installed[path] then
            local object = StaticFindObject(path)
            if object and object:IsValid() then
                local ok, failure = pcall(RegisterHook, path, callback)
                if ok then installed[path] = true; once("Hooked " .. path)
                else once("Hook unavailable: " .. tostring(failure)) end
            end
        end
    end
end

local safe_install = guard("hook registration", install)
log("Loaded; cultures are extended by name, without game-version checks")
-- The settings class is present after save deserialization or before construction.
-- This must run before Settings_BP:Init validates the saved culture on startup.
pcall(RegisterHook, "/Script/Engine.GameplayStatics:LoadGameFromSlot", function() end, safe_install)
pcall(RegisterHook, "/Script/Engine.GameplayStatics:CreateSaveGameObject", safe_install)
-- Widget class loading precedes Create; hook LanguageHack before menu construction.
pcall(RegisterHook, "/Script/UMG.WidgetBlueprintLibrary:Create", safe_install)
if RegisterLoadMapPostHook then pcall(RegisterLoadMapPostHook, safe_install) end
ExecuteInGameThread(safe_install)
