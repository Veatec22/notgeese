"""Exercise the Lua selector patch against mocks; not an in-game test."""
from pathlib import Path
import unittest
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
BASE = '/Game/NiceSettingsMenu/UI/Theme_1/'
SWITCHER = BASE + 'WB_T1_PVDSettingsMenu.WB_T1_PVDSettingsMenu_C:WidgetTree.WB_T1_OptionSwitcher_Language'
CDO = BASE + 'WB_T1_PVDSettingsMenu.Default__WB_T1_PVDSettingsMenu_C'
MAIN = BASE + 'WB_T1_PVDMainMenu.WB_T1_PVDMainMenu_C:WidgetTree.WB_T1_PVDSettingsMenu'
PAUSE = BASE + 'WB_T1_PVD_PauseMenu.WB_T1_PVD_PauseMenu_C:WidgetTree.WB_T1_PVDSettingsMenu'


class SelectorTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('package.path = ... .. "/?.lua;" .. package.path', (ROOT / 'plugin').as_posix())
        self.lua.execute('''
            function FText(s) return {ToString=function() return s end} end
            function param(v) return {get=function() return v end} end
            function array(values)
                values.ForEach=function(self, fn) for i,v in ipairs(self) do fn(i,param(v)) end end
                return values
            end
            function map(values)
                return {values=values, ForEach=function(self,fn) for k,v in pairs(self.values) do fn(param(k),param(v)) end end,
                    Add=function(self,k,v) self.values[k]=v end}
            end
            function valid(fields) fields.IsValid=function() return true end; return fields end
            function panel() return valid({["Language Codes"]=map({[0]="en",[1]="de-DE"})}) end
            function switcher()
                local props={["Option Names"]=array({FText("English"),FText("Deutsch")})}
                return setmetatable(valid({}), {__index=props,
                    __newindex=function(_,k,v) props[k]=k=="Option Names" and array(v) or v end})
            end
            objects={}
            function StaticFindObject(path) return objects[path] or {IsValid=function() return false end} end
            function print() end
            hooks={}; function RegisterHook(path, fn) hooks[path]=fn end
            loops={}; function LoopAsync(delay, fn) loops[#loops+1]=fn end
            function ExecuteInGameThread(fn) fn() end
        ''')
        self.lua.execute((ROOT / 'plugin/main.lua').read_text(encoding='utf-8'))
        self.create = self.lua.eval('hooks["/Script/UMG.WidgetBlueprintLibrary:Create"]')

    def load(self, *paths):
        for path in paths:
            self.lua.execute('local p=...; objects[p]=(p:find("OptionSwitcher") and switcher() or panel())', path)

    def codes(self, path):
        return self.lua.eval(f'objects["{path}"]["Language Codes"].values[2]')

    def labels(self):
        return self.lua.eval(f'#objects["{SWITCHER}"]["Option Names"]')

    def test_create_hook_patches_templates_before_menu(self):
        self.load(SWITCHER, CDO, MAIN)
        self.create()
        self.assertEqual(self.labels(), 3)
        self.assertEqual(self.codes(CDO), 'pl')
        self.assertEqual(self.codes(MAIN), 'pl')
        self.load(PAUSE)
        self.create()
        self.assertEqual(self.codes(PAUSE), 'pl', 'pause template patched on a later Create')
        self.assertEqual(self.labels(), 3, 'no duplicate label on repeated calls')

    def test_nothing_loaded_is_harmless(self):
        self.create()
        self.assertEqual(self.lua.eval('#loops'), 0)

    def test_changed_schema_leaves_originals(self):
        self.load(SWITCHER, CDO, MAIN, PAUSE)
        self.lua.execute(f'objects["{CDO}"]["Language Codes"].values[1]=nil')
        self.create()
        self.assertEqual(self.labels(), 2)
        self.assertIsNone(self.codes(MAIN))


if __name__ == '__main__':
    unittest.main()
