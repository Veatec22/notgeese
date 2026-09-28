"""Exercise Lua hooks on modeled UE4SS out parameters; not an in-game test."""
from pathlib import Path
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
lua = LuaRuntime()
lua.execute('''
hooks, objects = {}, {}
function RegisterHook(path, pre, post) hooks[path] = {pre, post}; return 1, 2 end
function StaticFindObject(path) return objects[path] end
function ExecuteInGameThread(fn) fn() end
function FText(s) return {ToString=function() return s end} end
function param(value)
    return {value=value, get=function(self) return self.value end,
            set=function(self, v) self.value=v; self.writes=(self.writes or 0)+1 end}
end
function array(values)
    return {ForEach=function(self, fn)
        for i, value in ipairs(values) do fn(i-1, param(FText(value))) end
    end}
end
function available(path) objects[path] = {IsValid=function() return true end} end
''')
lua.execute((ROOT/'plugin/main.lua').read_text(encoding='utf-8'))
lua.execute('''
settings = "/Game/Blueprints/Systems/Setting/Settings_BP.Settings_BP_C:Get Languages"
label = "/Game/Blueprints/UI/Menus/Settings/UI_Settings-Text_BP.UI_Settings-Text_BP_C:LanguageHack"
assert(hooks[settings] == nil)
available(settings)
hooks["/Script/Engine.GameplayStatics:LoadGameFromSlot"][2]()
assert(hooks[settings])
local original = {"de", "en-001", "fr", "no"}
local result = param(array(original))
hooks[settings][1](nil, result)
assert(#result.value == 5 and result.value[5] == "pl")
for i,v in ipairs(original) do assert(result.value[i] == v) end
local again = param(array(result.value))
hooks[settings][1](nil, again)
assert(again.writes == nil)
available(label)
hooks["/Script/UMG.WidgetBlueprintLibrary:Create"][1]()
local english = param(FText("English"))
hooks[label][1](nil, param(FText("en-001")), english)
assert(english.writes == nil and english.value:ToString() == "English")
local polish = param(FText("English"))
hooks[label][1](nil, param(FText("pl")), polish)
assert(polish.value:ToString() == "Polski")
-- A changed array signature fails closed and does not propagate a Lua error.
local malformed = param({})
hooks[settings][1](nil, malformed)
assert(malformed.writes == nil)
''')
print('PASS: late class loading, list preservation, idempotence, Polish label, error containment')
