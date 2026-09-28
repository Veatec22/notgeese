"""Check data preservation and rejection of unrelated archive payloads."""
import tempfile
import zipfile
from pathlib import Path
from build import ROOT,PAKS,STEM,PL_PATH,VERSION,validate_payload
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
        validate_payload(stage,pl,widget)
        # A hidden game asset inside an otherwise correctly named PAK must fail.
        good_pak=base.with_suffix('.pak').read_bytes()
        base.with_suffix('.pak').write_bytes(pak.write({**files,'Shinigami/Content/Unrelated.uasset':b'game asset'}))
        try:validate_payload(stage,pl,widget)
        except ValueError:pass
        else:raise AssertionError('Unrelated packaged asset accepted')
        base.with_suffix('.pak').write_bytes(good_pak)
        extra=stage/'resources.assets';extra.write_bytes(b'game asset')
        try:validate_payload(stage,pl,widget)
        except ValueError:pass
        else:raise AssertionError('Loose game asset accepted')
        extra.unlink()
        # A damaged chunk fails content hashing before it can be packaged.
        ucas=base.with_suffix('.ucas');good=ucas.read_bytes();bad=bytearray(good);bad[100]^=1;ucas.write_bytes(bad)
        try:validate_payload(stage,pl,widget)
        except AssertionError:pass
        else:raise AssertionError('Corrupted selector accepted')
        ucas.write_bytes(good)
        validate_payload(stage,pl,widget)
        # Original labels are retained; only a single pl entry is appended.
        original=ROOT/'work/iostore'/PATH
        expected,report=patch(original.read_bytes())
        assert expected==widget and len(report['previous_languages'])==12
    print('PASS: archive allowlist, internal PAK allowlist, chunk corruption, original selector preservation')

if __name__=='__main__':main()
