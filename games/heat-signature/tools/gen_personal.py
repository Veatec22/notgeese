"""Generate relation-aware templates for procedural personal missions.

The game joins "Rescue my " + relation + " from " + faction etc. Polish needs the
relation in the right case and the verb in its gender, so every relation gets its
own template. Writes work/batches/32-personal-runtime.json; tools/assemble.py merges it
into translations/en-pl-review.json.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# EN relation: nominative, accusative, genitive, gender, accusative with "idiot"
RELATIONS = {
    'brother': ('mój brat', 'mojego brata', 'mojego brata', 'm', 'mojego durnego brata'),
    'sister': ('moja siostra', 'moją siostrę', 'mojej siostry', 'f', 'moją durną siostrę'),
    'husband': ('mój mąż', 'mojego męża', 'mojego męża', 'm', 'mojego durnego męża'),
    'wife': ('moja żona', 'moją żonę', 'mojej żony', 'f', 'moją durną żonę'),
    'boyfriend': ('mój chłopak', 'mojego chłopaka', 'mojego chłopaka', 'm', 'mojego durnego chłopaka'),
    'girlfriend': ('moja dziewczyna', 'moją dziewczynę', 'mojej dziewczyny', 'f', 'moją durną dziewczynę'),
    'partner': ('moja druga połówka', 'moją drugą połówkę', 'mojej drugiej połówki', 'f', 'moją durną drugą połówkę'),
    'son': ('mój syn', 'mojego syna', 'mojego syna', 'm', 'mojego durnego syna'),
    'daughter': ('moja córka', 'moją córkę', 'mojej córki', 'f', 'moją durną córkę'),
    'kid': ('moje dziecko', 'moje dziecko', 'mojego dziecka', 'n', 'moje durne dziecko'),
    'friend': ('mój przyjaciel', 'mojego przyjaciela', 'mojego przyjaciela', 'm', 'mojego durnego przyjaciela'),
    'mum': ('moja mama', 'moją mamę', 'mojej mamy', 'f', 'moją durną mamę'),
    'mom': ('moja mama', 'moją mamę', 'mojej mamy', 'f', 'moją durną mamę'),
    'dad': ('mój tata', 'mojego tatę', 'mojego taty', 'm', 'mojego durnego tatę'),
}
WHO = {'m': 'który dał', 'f': 'która dała', 'n': 'które dało'}
VERBS = {'murdered': 'zamordował', 'tortured': 'torturował'}
CLAUSES = {
    ', killing as few other people as possible': ', zabijając jak najmniej innych osób',
    ', killing as few people as possible': ', zabijając jak najmniej osób',
    ', harming as few other people as possible': ', krzywdząc jak najmniej innych osób',
    ', being seen as little as possible': ', pokazując się jak najmniej',
    ', avoiding alarms as much as possible': ', unikając alarmów, jak się da',
    ', as fast as possible': ', jak najszybciej',
}


def main():
    out = {}
    for en, (nom, acc, gen, gender, idiot) in RELATIONS.items():
        out[f'Rescue my {en} from {{0}}'] = f'Uratuj {acc} z rąk {{0}}'
        out[f'Rescue my idiot {en}, who got captured by {{0}}'] = f'Uratuj {idiot}, {WHO[gender]} się złapać {{0}}'
        for verb, verb_pl in VERBS.items():
            out[f'Kill the {{0}} officer who {verb} my {en}'] = f'Zabij oficera {{0}}, który {verb_pl} {acc}'
            out[f'Bring in the {{0}} officer who {verb} my {en}'] = f'Dostarcz żywcem oficera {{0}}, który {verb_pl} {acc}'
        out[f"Kill the {{0}} {{1}} officers responsible for my {en}'s death"] = f'Zabij {{0}} oficerów {{1}} odpowiedzialnych za śmierć {gen}'
        out[f"Bring in the {{0}} {{1}} officers responsible for my {en}'s death"] = f'Dostarcz żywcem {{0}} oficerów {{1}} odpowiedzialnych za śmierć {gen}'
        out[f"pay off my {en}'s debt"] = f'spłacić dług {gen}'
        out[f'{{0}} took my {en}, heard you can help.'] = f'{nom[0].upper() + nom[1:]} jest w rękach {{0}}. Podobno możesz pomóc.'
    # A mission-style clause may follow any goal; the goal itself is the hole.
    for clause, clause_pl in CLAUSES.items():
        out['{0}' + clause] = '{0}' + clause_pl
    out.update({
        'Steal the {0} to make enough money to {1}': 'Ukradnij {0}, żeby zarobić dość, by {1}',
        'keep my family safe': 'zapewnić bezpieczeństwo rodzinie',
        'pay off a debt': 'spłacić dług',
        'retire': 'przejść na emeryturę',
        'Steal the {0} parts of the {1}': 'Ukradnij części ({0}) obiektu {1}',
        'Part of the {0}': 'Część: {0}',
        'I have a score to settle with {0}. Can you help?': 'Mam porachunki z {0}. Pomożesz?',
        'I want to steal the {0}. Can you help me steal the {1}?': 'Chcę ukraść {0}. Pomożesz mi ukraść {1}?',
        'I want to steal the {0}. Can you help?': 'Chcę ukraść {0}. Pomożesz?',
        "You'll be able to play as {0} again": 'Znów będzie można grać postacią {0}',
        "You'll unlock {0}'s character{1}": 'Odblokujesz postać {0}{1}',
        ', killing as few other people as possible': ', zabijając jak najmniej innych osób',
        ', killing as few people as possible': ', zabijając jak najmniej osób',
        ', harming as few other people as possible': ', krzywdząc jak najmniej innych osób',
        ', being seen as little as possible': ', pokazując się jak najmniej',
        ', avoiding alarms as much as possible': ', unikając alarmów, jak się da',
        ', as fast as possible': ', jak najszybciej',
        'the Glitchers': 'Glitchers', 'the Foundry': 'Foundry', 'the Sovereign': 'Sovereign',
        'the Offworld': 'Offworld', 'the Offworld Security': 'Offworld Security',
    })
    path = ROOT / 'work/batches/32-personal-runtime.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(out)} personal mission templates -> {path}')


if __name__ == '__main__':
    main()
