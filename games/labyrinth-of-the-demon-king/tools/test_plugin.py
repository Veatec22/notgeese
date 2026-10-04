"""Verify actor-authored text replacement in reused HUD TextBlocks, using Lua doubles."""
import unittest

from lupa.lua54 import LuaRuntime

from build import ROOT, split, texts_lua, load_entries


class InteractionTextTests(unittest.TestCase):
    def test_actor_messages_replace_reused_text_block(self):
        lua = LuaRuntime()
        _, _, entries = split(load_entries(ROOT))
        lua.globals().generated = lua.execute(texts_lua(entries).decode())
        lua.execute('''
            function require(name) return name == "texts" and generated or {} end
            function print() end
            function LoopAsync() error("translation polling must not run through async Lua") end
            function LoopInGameThreadWithDelay(_,f) periodic = f end
            function FText(s) return s end
            local owner = {IsValid=function() return true end,
                GetClass=function() return {GetFName=function() return
                    {ToString=function() return "UI_HUD_C" end} end} end}
            local tree = {IsValid=function() return true end, GetOuter=function() return owner end}
            tb = {text="", IsValid=function() return true end, GetOuter=function() return tree end,
                GetText=function(self) return self.text end, SetText=function(self,s) self.text=s end}
            actors = {}
            function FindFirstOf(class) return actors[class] end
            function FindAllOf(class) return class == "TextBlock" and {tb} or {} end
        ''')
        lua.execute((ROOT / 'plugin/main.lua').read_text(encoding='utf-8') + '\nreplace = replace_texts')
        lua.execute('''
            local actor = {IsValid=function() return true end}
            actors.BP_Puzzle_ItemSocket_SkywalkSlot_Base_C = actor
            actors.BP_OpeningDoor_TowerCorridor_PaintedDoor_001_C = actor
            tb.text = "There is an empty socket with space for a circular object."
            replace()
            assert(tb.text == "Puste gniazdo. Jest w nim miejsce na okrągły przedmiot.")
            tb.text = "The painting depicts Dainichi Nyorai, one of the Five Wisdom Buddhas."
            replace()
            assert(tb.text == "Obraz przedstawia Dainichi Nyorai, jednego z Pięciu Buddów Mądrości.")
            tb.text = "There is an empty socket with space for a circular object."
            replace()
            assert(tb.text == "Puste gniazdo. Jest w nim miejsce na okrągły przedmiot.")
            tb.text = "Unrelated text"; replace(); assert(tb.text == "Unrelated text")
            actors = {}
            tb.text = "There is an empty socket with space for a circular object."
            replace(); assert(tb.text:sub(1,5) == "There")
            local enqueued = 0
            ExecuteInGameThread = function() enqueued = enqueued + 1 end
            for i=1,100 do assert(periodic() == false) end
            assert(enqueued == 0, "periodic translation polling crossed the async queue")
        ''')


if __name__ == '__main__':
    unittest.main()
