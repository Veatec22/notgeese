"""Apply reviewed numbered work batches to native IDs and keep EN/PL synchronized."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
from translations import polish_by_key, write_entries  # noqa: E402
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['show','apply']);p.add_argument('--start',type=int,default=0);p.add_argument('--end',type=int,default=1507);p.add_argument('--file',type=Path);a=p.parse_args()
 rows=json.loads((ROOT/'work/english.json').read_text(encoding='utf-8'))
 pl=polish_by_key(ROOT)
 if a.action=='show':
  for i,row in enumerate(rows):
   if a.start<=i<a.end and row['key'] not in pl:print(f"{i}|{row['key']}|{json.dumps(row['english'],ensure_ascii=False)}")
  return
 seen=set()
 for line in a.file.read_text(encoding='utf-8-sig').splitlines():
  if not line.strip():continue
  number,text=line.split('|',1);i=int(number);assert i not in seen;seen.add(i)
  assert 0<=i<len(rows) and text
  pl[rows[i]['key']]=text.replace('\\r\\n','\r\n').replace('\\n','\n')
 # Reuse only exact English duplicates; all authored values stay authoritative.
 known={}
 for row in rows:
  if row['key'] in pl:known.setdefault(row['english'],set()).add(pl[row['key']])
 for row in rows:
  values=known.get(row['english'],set())
  if row['key'] not in pl and len(values)==1:pl[row['key']]=next(iter(values))
 review=[dict(key=r['key'],english=r['english'],polish=pl[r['key']]) for r in rows if r['key'] in pl]
 write_entries(ROOT,review)
 print(f'{len(pl)}/{len(rows)}')
if __name__=='__main__':main()
