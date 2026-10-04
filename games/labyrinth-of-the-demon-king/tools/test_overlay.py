"""Check data preservation and rejection of unrelated archive payloads."""
import tempfile
import zipfile
from pathlib import Path
from build import ROOT,PAKS,STEM,PL_PATH,VERSION,RUNTIME,MOD,validate_payload,mod_payload,split
from translations import load_entries
from iostore import Store
from language_slot import PATH,patch
import pak

def main():
    with tempfile.TemporaryDirectory() as temp:
        stage=Path(temp)
        with zipfile.ZipFile(ROOT/f'dist/Labyrinth-of-the-Demon-King-PL-{VERSION}.zip') as z:z.extractall(stage)
        base=stage/PAKS/STEM
        _,files=pak.read(base.with_suffix('.pak').read_bytes());pl=files[PL_PATH]
        store=Store(base);widget=store.read(store.paths[PATH])
        _,subtitles,hardcoded=split(load_entries(ROOT));mod=mod_payload(RUNTIME,subtitles,hardcoded)
        validate_payload(stage,pl,widget,mod)
        # A hidden game asset inside an otherwise correctly named PAK must fail.
        good_pak=base.with_suffix('.pak').read_bytes()
        base.with_suffix('.pak').write_bytes(pak.write({**files,'Shinigami/Content/Unrelated.uasset':b'game asset'}))
        try:validate_payload(stage,pl,widget,mod)
        except ValueError:pass
        else:raise AssertionError('Unrelated packaged asset accepted')
        base.with_suffix('.pak').write_bytes(good_pak)
        extra=stage/'resources.assets';extra.write_bytes(b'game asset')
        try:validate_payload(stage,pl,widget,mod)
        except ValueError:pass
        else:raise AssertionError('Loose game asset accepted')
        extra.unlink()
        # A stray UE4SS mod or a changed script must fail too.
        stray=stage/MOD.replace('notgeesePL','Other')/'main.lua';stray.parent.mkdir(parents=True);stray.write_bytes(b'-- x')
        try:validate_payload(stage,pl,widget,mod)
        except ValueError:pass
        else:raise AssertionError('Foreign mod accepted')
        stray.unlink();stray.parent.rmdir();stray.parent.parent.rmdir()
        script=stage/MOD/'main.lua';good_script=script.read_bytes();script.write_bytes(good_script+b'-- changed')
        try:validate_payload(stage,pl,widget,mod)
        except ValueError:pass
        else:raise AssertionError('Changed script accepted')
        script.write_bytes(good_script)
        # A damaged chunk fails content hashing before it can be packaged.
        ucas=base.with_suffix('.ucas');good=ucas.read_bytes();bad=bytearray(good);bad[100]^=1;ucas.write_bytes(bad)
        try:validate_payload(stage,pl,widget,mod)
        except AssertionError:pass
        else:raise AssertionError('Corrupted selector accepted')
        ucas.write_bytes(good)
        validate_payload(stage,pl,widget,mod)
        # Original labels are retained; only a single pl entry is appended.
        original=ROOT/'work/iostore'/PATH
        expected,report=patch(original.read_bytes())
        assert expected==widget and len(report['previous_languages'])==12
    print('PASS: archive allowlist, mod allowlist, internal PAK allowlist, chunk corruption, original selector preservation')

if __name__=='__main__':main()
