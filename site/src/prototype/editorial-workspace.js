// THROWAWAY. All server actions are simulated; never calls Supabase or GitHub.
const root = document.getElementById('workspace');
const dialog = document.getElementById('pw-dialog');
const data = JSON.parse(document.getElementById('pw-data').textContent);
const slug = 'shotgun-cop-man';
const storageKey = 'notgeese:prototype:editorial:v1';
const labels = { review: 'Do przejrzenia', accepted: 'Zaakceptowane', pending: 'Do wdrożenia', conflict: 'Konflikt' };
const variants = { A: 'EN i PL obok siebie', B: 'Czytanie rozmowy', C: 'Jedna kwestia' };
const groups = [
  ['menu', 'Menu i nawigacja'], ['settings', 'Ustawienia i sterowanie'],
  ['tutorial', 'Samouczek'], ['game', 'Rozgrywka i wyniki'], ['dialogue', 'Wypowiedzi i dialogi'],
  ['editor', 'Edytor i kampanie'], ['achievements', 'Osiągnięcia'], ['other', 'Pozostałe'],
];
const originals = structuredClone(data.rows);
let saved = {}, drafts = {}, overrides = {}, journal = [], visited = false;
let currentGame = null, group = 'menu', query = '', stateFilter = '', page = 0, focusKey = null, onlyPl = false;
let variant = new URLSearchParams(location.search).get('variant') || 'A';
if (!variants[variant]) variant = 'A';
let storageWorking = true, toastTimer;
let pageSize = 50;
try { const value = Number(localStorage.getItem('notgeese:prototype:page-size')); if ([50,100,200].includes(value)) pageSize = value; } catch {}
try {
  const state = JSON.parse(localStorage.getItem(storageKey) || 'null');
  if (state) ({ saved = {}, drafts = {}, overrides = {}, journal = [], visited = false } = state);
} catch { storageWorking = false; }
function persist() {
  try { localStorage.setItem(storageKey, JSON.stringify({ saved, drafts, overrides, journal, visited })); }
  catch { storageWorking = false; toast('Nie udało się utrwalić szkiców w przeglądarce. Pozostają tylko w pamięci tej karty.'); }
}
function esc(value = '') { return String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]); }
function notice(message) { return `<div class="pw-callout"><p>${esc(message)}</p></div>`; }
function toast(message) {
  clearTimeout(toastTimer); document.getElementById('pw-toast').textContent = message;
  toastTimer = setTimeout(() => { document.getElementById('pw-toast').textContent = ''; }, 6000);
}
function log(message) { journal.unshift({ at: new Date().toISOString(), message }); }
function rows() { return originals.map(row => ({ ...row, ...(overrides[row.key] || {}) })); }
function rowFor(key) { return rows().find(row => row.key === key); }
function groupFor(row) {
  const key = row.key;
  if (/^(PedroDLCSpeech|pSpeech|satanSpeech)/.test(key)) return 'dialogue';
  if (/^(e[a-zA-Z]|mcc|PedroDLCep)/.test(key)) return 'editor';
  if (/^ach/.test(key)) return 'achievements';
  if (/^t[A-Z]/.test(key)) return 'tutorial';
  if (/^(a[A-Z]|a(up|down|left|right)$|waitForInput|m(Video|Resolution|Fullscreen|VSync|TargetFPS|FPS|Audio|SFX|Music|GameSettings|Blood|Screenshake|Rumble|ShowTimer|Clear|Language|Accessibility|Acc|Controls|Confine|Mouse|AllInOne))/.test(key)) return 'settings';
  if (/^(g[A-Z]|m(Lvl|BestTime|WorldMap|KillAll|Speedrun|NoDamage|HitsTaken|Continue|Timer)|PedroDLCBoss)/.test(key)) return 'game';
  if (/^m[A-Z]|^LangName$/.test(key)) return 'menu';
  return 'other';
}
function stateOf(row) {
  const s = saved[row.key];
  if (!s || s.action === 'review') return 'review';
  if (s.action === 'accept') return s.english === row.english && s.after === row.polish ? 'accepted' : 'review';
  if (s.english !== row.english) return 'conflict';
  if (s.after === row.polish) return 'accepted';
  return s.before === row.polish ? 'pending' : 'conflict';
}
function stale(row) { const d = drafts[row.key]; return Boolean(d && (d.english !== row.english || d.before !== row.polish)); }
function textOf(row) { return drafts[row.key]?.after ?? (saved[row.key]?.action === 'correct' ? saved[row.key].after : row.polish); }
function stage(key, action, after) {
  const row = rowFor(key), previous = drafts[key];
  drafts[key] = { ...previous, confirmed: true, action, after: after ?? row.polish, english: row.english, before: row.polish };
  persist();
}
function counts() { const c = { review: 0, accepted: 0, pending: 0, conflict: 0 }; for (const row of rows()) c[stateOf(row)]++; return c; }
function pendingCount() { return rows().filter(row => stateOf(row) === 'pending').length; }
function stats() { const c = counts(); return `<div class="pw-stats">${Object.entries(labels).map(([key,label]) => `<span><b>${c[key]}</b> ${label.toLowerCase()}</span>`).join('')}<span class="pw-draft"><b data-draft-count>${Object.keys(drafts).length}</b> szkiców</span></div>`; }
function groupRows() {
  const items = rows().filter(row => group === 'sequence' ? /^PedroDLCSpeech\d+$/.test(row.key) : groupFor(row) === group);
  return group === 'sequence' ? items.sort((a,b) => Number(a.key.replace('PedroDLCSpeech','')) - Number(b.key.replace('PedroDLCSpeech',''))) : items;
}
function filteredRows() {
  const q = query.toLocaleLowerCase('pl');
  return groupRows().filter(row => (!stateFilter || stateOf(row) === stateFilter) && (!q || `${row.key} ${row.english} ${textOf(row)}`.toLocaleLowerCase('pl').includes(q)));
}
function speaker(key) {
  const n = Number(key.replace('PedroDLCSpeech',''));
  if ([2,4,5,7,8,9,11,12].includes(n)) return 'Pedro';
  if ([1,3,6,10].includes(n)) return 'Shotgun Cop Man';
  return 'Mówca nieustalony';
}
function flag(language) {
  const label = language === 'en' ? 'Oryginał angielski' : 'Polskie tłumaczenie';
  const shapes = language === 'en'
    ? '<path fill="#012169" d="M0 0h60v30H0z"/><path stroke="#fff" stroke-width="6" d="m0 0 60 30M60 0 0 30"/><path stroke="#c8102e" stroke-width="2" d="m0 0 60 30M60 0 0 30"/><path stroke="#fff" stroke-width="10" d="M30 0v30M0 15h60"/><path stroke="#c8102e" stroke-width="6" d="M30 0v30M0 15h60"/>'
    : '<path fill="#fff" d="M0 0h60v30H0z"/><path fill="#dc143c" d="M0 15h60v15H0z"/>';
  return `<svg class="pw-flag" viewBox="0 0 60 30" role="img" aria-label="${label}"><title>${label}</title>${shapes}</svg>`;
}
// Lucide triangle-alert, ISC, © Lucide Icons and Contributors (see site icon attribution).
const alertIcon = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>';
function stateBadge(state) { return `<span class="pw-status" data-state="${state}">${state==='conflict'?alertIcon:''}${labels[state]}</span>`; }
function stateDropdown() { return `<details class="pw-filter"><summary aria-label="Filtr stanu">${stateFilter?stateBadge(stateFilter):'Wszystkie stany'} ▾</summary><div class="pw-filter-options"><button data-action="filter" data-state="">Wszystkie stany</button>${Object.keys(labels).map(state=>`<button data-action="filter" data-state="${state}" aria-pressed="${stateFilter===state}">${stateBadge(state)}</button>`).join('')}</div></details>`; }
function visibleRows() { const size=variant==='C'?1:pageSize; return filteredRows().slice(page*size,(page+1)*size); }
function badges(row) {
  const draft = drafts[row.key];
  const state = draft && draft.confirmed !== false && !stale(row) && draft.action
    ? ({ accept: 'accepted', correct: 'pending', review: 'review' }[draft.action])
    : stateOf(row);
  return `${stateBadge(state)}${draft ? `<span class="pw-draft-badge">${draft.confirmed===false?'Szkic':'Niezapisane'}</span>` : ''}`;
}
function entry(row) {
  const status = stateOf(row), draft = drafts[row.key], old = saved[row.key];
  const isSequence = /^PedroDLCSpeech\d+$/.test(row.key);
  let special = '';
  if (stale(row)) special = `<div class="pw-callout"><h3>Nieaktualny szkic</h3><p>Tekst zmienił się od rozpoczęcia pracy. Zapis tej gry jest zablokowany.</p><div class="pw-compare"><div><small>Teraz w repo — symulacja</small><p>${esc(row.polish)}</p></div><div><small>Twój szkic</small><p>${esc(draft.after)}</p></div></div><div class="pw-actions"><button data-action="keep-draft" data-key="${esc(row.key)}">Zachowaj na nowej bazie</button><button data-action="discard" data-key="${esc(row.key)}">Porzuć szkic</button></div></div>`;
  else if (status === 'conflict' && !draft) special = `<div class="pw-callout"><h3>Konflikt</h3><p>W repo jest inne brzmienie niż przed i po korekcie.</p><div class="pw-compare"><div><small>Przed korektą</small><p>${esc(old.before)}</p></div><div><small>Teraz w repo — symulacja</small><p>${esc(row.polish)}</p></div></div><div class="pw-actions"><button data-action="accept" data-key="${esc(row.key)}">Przyjmij main</button><button data-action="keep-own" data-key="${esc(row.key)}">Zostań przy swoim</button></div></div>`;
  return `<article class="pw-entry" data-entry="${esc(row.key)}"><div class="pw-meta"><div><h3 class="pw-key">${esc(row.key)}</h3>${isSequence ? `<span class="pw-speaker">${speaker(row.key)}</span>` : ''}</div><span class="pw-badges">${badges(row)}</span></div>${special}<div class="pw-pair"><div class="pw-source"><div class="pw-language">${flag('en')}</div><div class="pw-en">${esc(row.english)}</div></div><div><label class="pw-language" for="entry-${esc(row.key)}">${flag('pl')}<span class="ng-visually-hidden">Polskie tłumaczenie — ${esc(row.key)}</span></label><textarea id="entry-${esc(row.key)}" data-edit="${esc(row.key)}" ${stale(row) ? 'disabled' : ''}>${esc(textOf(row))}</textarea></div></div>${row.context ? `<p class="pw-muted">${esc(row.context)}</p>` : ''}<div class="pw-actions"><button data-action="confirm-correction" data-key="${esc(row.key)}" ${!draft || draft.confirmed!==false || stale(row)?'disabled':''}>Zatwierdź poprawkę</button><button data-action="accept" data-key="${esc(row.key)}" ${stale(row) || status === 'conflict' ? 'disabled' : ''}>Akceptuj</button><button data-action="undo" data-key="${esc(row.key)}" ${stale(row) || status === 'conflict' || (status === 'review' && !draft) ? 'disabled' : ''}>${status === 'pending' ? 'Wycofaj korektę' : 'Cofnij akceptację'}</button>${draft ? `<button data-action="discard" data-key="${esc(row.key)}">Porzuć szkic</button>` : ''}</div></article>`;
}
function render() {
  root.className = `pw-layout-${variant}${onlyPl ? ' pw-only-pl' : ''}`;
  if (!currentGame) {
    root.innerHTML = `<div class="pw-top"><div><div class="pw-overline">Not Geese / pracownia korekty</div><h1>Do której gry wracamy?</h1><p class="pw-muted">Lista ze strony. Prototyp podłącza teksty tylko Shotgun Cop Mana. Szkice zapisuje się i odrzuca w grze.</p></div></div><div class="pw-game-list">${data.games.map(game => `<section class="pw-game"><div class="pw-overline">${esc(game.version)} · ${game.entries} wpisów</div>${game.id === slug && Object.keys(drafts).length ? `<span class="pw-draft-badge">Niezapisane szkice: ${Object.keys(drafts).length}</span>` : ''}<h2>${esc(game.title)}</h2><p class="pw-muted">${game.id === slug && visited ? `${counts().accepted} zaakceptowanych` : 'Jeszcze nie otwierana'}</p><button data-action="open" data-game="${esc(game.id)}">Otwórz grę</button></section>`).join('')}</div>`;
    return;
  }
  const items = filteredRows(), allGroup = groupRows();
  const size = variant === 'C' ? 1 : pageSize;
  page = Math.max(0,Math.min(page,Math.ceil(items.length/size)-1));
  if (focusKey) { const index = items.findIndex(row => row.key === focusKey); if (index >= 0) page = Math.floor(index/size); focusKey = null; }
  const visible = items.slice(page*size,page*size+size);
  const eligible = visible.filter(row => stateOf(row) === 'review' && !drafts[row.key]);
  const heading = group === 'sequence' ? 'Spotkanie z Pedro' : groups.find(g => g[0] === group)?.[1];
  root.innerHTML = `<div class="pw-top"><div><button class="pw-link" data-action="home">← Wszystkie gry</button><h1>Shotgun Cop Man</h1><p class="pw-muted">485 wpisów · lokalna próbka repo · main i zapis do bazy są symulowane</p></div><div class="pw-actions"><button data-action="refresh">Odśwież</button><button class="pw-primary" data-action="save">Zapisz grę (<span data-draft-count>${Object.keys(drafts).length}</span>)</button><button data-action="discard-all" ${Object.keys(drafts).length?'':'disabled'}>Cofnij wszystko</button><button data-action="export">Eksportuj korekty</button></div></div>${stats()}<div class="pw-shell"><aside class="pw-sidebar"><h3>Grupy</h3>${groups.map(([id,name]) => `<button data-action="group" data-group="${id}" aria-current="${group===id}"><span>${name}</span><small>${rows().filter(r=>groupFor(r)===id).length}</small></button>`).join('')}<hr><h3>Sekwencje</h3><button data-action="group" data-group="sequence" aria-current="${group==='sequence'}">Spotkanie z Pedro <small>15</small></button><hr><button data-action="journal">Dziennik gry</button><button data-action="scenarios">Sprawdź sytuacje</button><p class="pw-muted">Szkice tylko w tej przeglądarce. Localhost jest osobny od notgeese.cc.</p>${storageWorking?'':notice('Brak trwałego zapisu lokalnego.')}</aside><section class="pw-content"><div class="pw-toolbar"><div class="pw-top"><div><h2>${heading}</h2><p class="pw-muted">${items.length} z ${allGroup.length} wpisów w grupie</p></div><label>Tryb redakcji <select id="pw-variant">${Object.entries(variants).map(([id,name])=>`<option value="${id}" ${id===variant?'selected':''}>${name}</option>`).join('')}</select></label><button data-action="reading">${onlyPl?'Pokaż EN i PL':'Czytaj tylko PL'}</button></div>${group==='sequence'?notice('Kolejność według numeracji kluczy. Mówcy odtworzeni z biblii; końcowe kwestie nie mają ustalonego mówcy.'):''}<div class="pw-actions"><input id="pw-search" type="search" value="${esc(query)}" aria-label="Szukaj w grze" placeholder="Szukaj w grze: tekst lub klucz…">${stateDropdown()}<button data-action="search-game">Szukaj w całej grze</button></div><div class="pw-actions"><button data-action="accept-rest" ${!eligible.length?'disabled':''}>Zaakceptuj na stronie (${eligible.length})</button><small class="pw-muted">Tylko widoczne wpisy do przejrzenia. Pomija szkice.</small></div></div><div>${visible.map(entry).join('') || '<p class="pw-empty">Brak wpisów w tym widoku.</p>'}</div><div class="pw-pagination"><label>Wpisów na stronie <select id="pw-page-size" ${variant==='C'?'disabled':''}>${[50,100,200].map(n=>`<option ${n===pageSize?'selected':''}>${n}</option>`).join('')}</select></label><button data-action="prev-page" ${page===0?'disabled':''}>← Poprzednie</button><span class="pw-muted">${items.length ? page*size+1 : 0}–${Math.min((page+1)*size,items.length)} / ${items.length}</span><button data-action="next-page" ${(page+1)*size>=items.length?'disabled':''}>Następne →</button></div></section></div>`;
}
function modal(title,body,actions='') {
  dialog.innerHTML = `<h2 id="pw-dialog-title">${title}</h2>${body}<div class="pw-actions">${actions}<button data-action="close">Zamknij</button></div>`;
  if (!dialog.open) dialog.showModal();
}
function saveGame() {
  if (rows().some(stale)) { toast('Najpierw rozstrzygnij nieaktualny szkic. Żaden szkic tej gry nie został zapisany.'); return; }
  if(Object.values(drafts).some(d=>d.confirmed===false)){toast('Najpierw zatwierdź poprawki przy wpisach albo porzuć szkice.');return;}
  const count = Object.keys(drafts).length;
  for (const [key,draft] of Object.entries(drafts)) {
    if (draft.action) {
      saved[key] = { action:draft.action, english:draft.english, before:draft.before, after:draft.after };
      log(`${key}: ${draft.action==='correct'?'korekta do wdrożenia':draft.action==='accept'?'akceptacja':'cofnięcie akceptacji / korekty'}`);
    }
  }
  drafts={};persist();render();toast(`Zapisano ${count} szkiców w symulacji. Supabase pozostaje bez zmian.`);
}
function exportData(comment='') {
  return { format:1, game:slug, source:{kind:'prototype-local',main_sha:null}, exported_at:new Date().toISOString(), comment,
    corrections:rows().filter(row=>stateOf(row)==='pending').map(row=>({namespace:'',key:row.key,english:saved[row.key].english,before:saved[row.key].before,after:saved[row.key].after})),
    conflicts:rows().filter(row=>stateOf(row)==='conflict').map(row=>({namespace:'',key:row.key,english:saved[row.key].english,before:saved[row.key].before,after:saved[row.key].after,main_english:row.english,main_polish:row.polish})) };
}
function switchVariant(delta) {
  const keys=Object.keys(variants);variant=keys[(keys.indexOf(variant)+delta+keys.length)%keys.length];page=0;
  const url=new URL(location.href);url.searchParams.set('variant',variant);history.replaceState({},'',url);render();
}
function scenario(kind) {
  if (kind==='conflict') {
    const row=originals.find(r=>r.key==='mOptions');
    saved[row.key]={action:'correct',english:row.english,before:row.polish,after:'Ustawienia'};
    overrides[row.key]={polish:'Konfiguracja'};delete drafts[row.key];group='menu';
    log('SCENARIUSZ: konflikt mOptions; „Konfiguracja” symuluje zmianę main.');
  } else if (kind==='stale') {
    const row=originals.find(r=>r.key==='mQuit');
    drafts[row.key]={action:'correct',english:row.english,before:row.polish,after:'Zakończ grę'};
    overrides[row.key]={polish:'Zamknij grę'};group='menu';
    log('SCENARIUSZ: nieaktualny szkic mQuit.');
  } else if (kind==='applied') {
    for (const row of rows()) if (stateOf(row)==='pending') {
      overrides[row.key]={...overrides[row.key],polish:saved[row.key].after};
      saved[row.key]={...saved[row.key],action:'accept'};log(`${row.key}: korekta obecna na main → zaakceptowany (symulacja)`);
    }
  } else if (kind==='reset') {
    saved={};drafts={};overrides={};journal=[];visited=true;group='menu';
  }
  page=0;query='';stateFilter='';persist();dialog.close();render();
}
function handle(event) {
  const button=event.target.closest('button[data-action]');if(!button)return;
  const {action,key}=button.dataset;
  if(action==='open') { if(button.dataset.game!==slug){toast('W tym prototypie podłączony jest tylko Shotgun Cop Man.');return;}currentGame=slug;visited=true;persist();render(); }
  else if(action==='home'){currentGame=null;render();}
  else if(action==='group'){group=button.dataset.group;page=0;query='';stateFilter='';render();}
  else if(action==='discard-all'){drafts={};persist();render();toast('Cofnięto niezapisane zmiany w tej grze.');}
  else if(action==='filter'){stateFilter=button.dataset.state;page=0;render();}
  else if(action==='reading'){onlyPl=!onlyPl;render();}
  else if(action==='accept'||action==='confirm-correction'){
    const row=rowFor(key);
    const after=action==='accept' && stateOf(row)==='conflict' ? row.polish : textOf(row);
    stage(key,after===row.polish?'accept':'correct',after);render();
  }
  else if(action==='undo'){stage(key,'review');render();}
  else if(action==='discard'){delete drafts[key];persist();render();}
  else if(action==='keep-own'){stage(key,'correct',saved[key].after);render();}
  else if(action==='keep-draft'){const d=drafts[key],r=rowFor(key);d.before=r.polish;d.english=r.english;if(d.action==='accept')d.after=r.polish;persist();render();}
  else if(action==='accept-rest'){const items=visibleRows().filter(r=>stateOf(r)==='review'&&!drafts[r.key]);for(const row of items)stage(row.key,'accept');render();toast(`${items.length} akceptacji na bieżącej stronie. Zapisz grę, aby je utrwalić.`);}
  else if(action==='save'){saveGame();}
  else if(action==='prev-page'){page--;render();}
  else if(action==='next-page'){page++;render();}
  else if(action==='close'){dialog.close();}
  else if(action==='journal'){modal('Dziennik gry',journal.length?`<ol>${journal.map(j=>`<li><small>${new Date(j.at).toLocaleTimeString('pl')}</small> ${esc(j.message)}</li>`).join('')}</ol>`:'<p>Brak zapisanych akcji. Szkice nie trafiają do dziennika.</p>');}
  else if(action==='export'){
    const blocked=counts().conflict>0;
    modal('Eksport korekt · Shotgun Cop Man',`<p>${pendingCount()} korekt. Eksport obejmuje wyłącznie zapisany wynik pracy.</p>${Object.keys(drafts).length?notice(`${Object.keys(drafts).length} lokalnych szkiców nie trafi do eksportu. Zapisz je osobno, jeśli mają być uwzględnione.`):''}${blocked?notice(`${counts().conflict} wpisów w konflikcie nie trafi do korekt; eksport wypisze je osobno.`):''}<label for="pw-comment">Komentarz dla agenta</label><textarea id="pw-comment" placeholder="Co agent powinien wiedzieć przy nanoszeniu korekt?"></textarea><details><summary>Pokaż strukturę JSON</summary><pre>${esc(JSON.stringify(exportData(),null,2))}</pre></details><p class="pw-muted">Próbka jest oznaczona jako prototyp, nie jako eksport z main. Pobranie niczego nie zmienia.</p>`,`<button class="pw-primary" data-action="download">Pobierz JSON prototypu</button>`);
  } else if(action==='download'){
    const payload=exportData(document.getElementById('pw-comment').value);const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)+'\n'],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;a.download=`shotgun-cop-man-PROTOTYP-korekty-${new Date().toISOString().slice(0,10)}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Pobrano JSON prototypu. Stan wpisów nie zmienił się.');
  } else if(action==='refresh'){render();toast('Odświeżenie symulacji. Użyj „Sprawdź sytuacje”, aby zasymulować zmianę main.');}
  else if(action==='scenarios'){modal('Sytuacje do sprawdzenia','<p>Poniższe przyciski zmieniają tylko dane demonstracyjne. „Konfiguracja” i pozostałe warianty nie pochodzą z repo.</p>',`<button data-action="scenario" data-kind="conflict">Konflikt</button><button data-action="scenario" data-kind="stale">Nieaktualny szkic</button><button data-action="scenario" data-kind="applied">Agent naniósł korekty</button><button data-action="scenario" data-kind="reset">Wyczyść demonstrację</button>`);}
  else if(action==='scenario'){scenario(button.dataset.kind);}
  else if(action==='search-game'){
    const q=query.toLocaleLowerCase('pl');const hits=rows().filter(r=>`${r.key} ${r.english} ${textOf(r)}`.toLocaleLowerCase('pl').includes(q));
    modal('Wyniki w grze',`<p>${hits.length} trafień. Przejdź do wpisu w grupie lub sekwencji.</p>${hits.slice(0,60).map(r=>`<p><button data-action="jump" data-key="${esc(r.key)}">${esc(r.key)}</button> ${esc(textOf(r).slice(0,90))}</p>`).join('')}${hits.length>60?'<p>Doprecyzuj wyszukiwanie — pokazano pierwsze 60 trafień.</p>':''}`);
  } else if(action==='jump'){const row=rowFor(key);group=/^PedroDLCSpeech/.test(key)?'sequence':groupFor(row);query='';stateFilter='';focusKey=key;dialog.close();render();root.querySelector(`[data-entry="${key}"]`)?.scrollIntoView({block:'center'});}
}
root.addEventListener('click',handle);dialog.addEventListener('click',handle);
root.addEventListener('input',event=>{
  if(event.target.dataset.edit){const key=event.target.dataset.edit;const row=rowFor(key);stage(key,event.target.value===row.polish?'accept':'correct',event.target.value);drafts[key].confirmed=false;persist();event.target.closest('article').querySelector('[data-action=confirm-correction]').disabled=false;root.querySelector('[data-action=discard-all]').disabled=false;root.querySelectorAll('[data-draft-count]').forEach(el=>el.textContent=Object.keys(drafts).length);event.target.closest('article').querySelector('.pw-badges').innerHTML=badges(row);}
  if(event.target.id==='pw-search')query=event.target.value;
});
root.addEventListener('change',event=>{
  if(event.target.id==='pw-page-size'){pageSize=Number(event.target.value);try{localStorage.setItem('notgeese:prototype:page-size',String(pageSize));}catch{toast('Nie udało się zapamiętać liczby wpisów.');}page=0;render();}
  if(event.target.id==='pw-variant'){variant=event.target.value;page=0;const url=new URL(location.href);url.searchParams.set('variant',variant);history.replaceState({},'',url);render();}
});
root.addEventListener('keydown',event=>{if(event.target.id==='pw-search'&&event.key==='Enter'){page=0;render();}});
document.addEventListener('keydown',event=>{if(dialog.open||event.target.closest('input,textarea,select,[contenteditable]'))return;if(event.key==='ArrowLeft'){event.preventDefault();switchVariant(-1);}if(event.key==='ArrowRight'){event.preventDefault();switchVariant(1);}});
render();
