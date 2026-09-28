// Display-time translation engine. Pure C++: no Windows or game dependencies,
// so tools/translate_test.cpp can exercise exactly the code the plugin runs.
//
// Heat Signature builds much of its text by concatenating literals with numbers,
// names and other literals ("Kills: " + string(n)). Only the final string reaches
// the text splitter we hook, so the engine recognises, in order:
//   exact entries, UPPERCASE variants, procedural item names (noun + modifiers
//   with Polish gender agreement), templates with {0}..{9} holes, per-line
//   translation, names truncated with "...", and finally literal fragments
//   replaced at word boundaries. Dialogue files are translated when the game
//   loads them (TranslateDialogFile), so its letter-by-letter reveal shows Polish.
// Unknown text is returned unchanged; game logic never sees the translation.
#pragma once
#include <algorithm>
#include <deque>
#include <functional>
#include <map>
#include <set>
#include <string>
#include <unordered_map>
#include <vector>

namespace tr {

// ---- UTF-8 helpers (Polish letters only need two-byte sequences) -----------
inline size_t CodePoints(const std::string& s) {
    size_t n = 0;
    for (unsigned char c : s) if ((c & 0xc0) != 0x80) ++n;
    return n;
}
inline std::string FirstCodePoints(const std::string& s, size_t count) {
    size_t i = 0, n = 0;
    while (i < s.size()) {
        if ((static_cast<unsigned char>(s[i]) & 0xc0) != 0x80) { if (n == count) break; ++n; }
        ++i;
    }
    return s.substr(0, i);
}
inline std::string Upper(const std::string& s) {
    static const std::map<std::string, std::string> pl = {
        {u8"ą", u8"Ą"}, {u8"ć", u8"Ć"}, {u8"ę", u8"Ę"}, {u8"ł", u8"Ł"}, {u8"ń", u8"Ń"},
        {u8"ó", u8"Ó"}, {u8"ś", u8"Ś"}, {u8"ź", u8"Ź"}, {u8"ż", u8"Ż"}};
    std::string out;
    for (size_t i = 0; i < s.size();) {
        unsigned char c = s[i];
        if (c < 0x80) { out += char(c >= 'a' && c <= 'z' ? c - 32 : c); ++i; continue; }
        size_t len = (c & 0xe0) == 0xc0 ? 2 : (c & 0xf0) == 0xe0 ? 3 : 4;
        std::string cp = s.substr(i, len);
        auto it = pl.find(cp);
        out += it == pl.end() ? cp : it->second;
        i += len;
    }
    return out;
}
inline std::string Capitalise(const std::string& s) {
    if (s.empty()) return s;
    size_t len = (static_cast<unsigned char>(s[0]) & 0xe0) == 0xc0 ? 2 : 1;
    return Upper(s.substr(0, len)) + s.substr(len);
}
inline bool Alnum(unsigned char c) { return (c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || c >= 0x80; }
inline bool HasLetters(const std::string& s) {
    return std::any_of(s.begin(), s.end(), [](char c) { return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z'); });
}

struct Template {
    std::vector<std::string> literals;  // literals.size() == holes.size() + 1
    std::vector<int> holes;             // EN hole numbers in order of appearance
    std::string pl;                     // may reorder holes: "{1} ... {0}"
    size_t fixed = 0;                   // literal length: more specific first
};

struct Noun { std::string pl; char gender = 'm'; };
struct Modifier { std::string m, f, n; bool tail = false; };

class Engine {
public:
    std::unordered_map<std::string, std::string> exact, upperExact;
    std::vector<Template> templates;
    std::vector<std::pair<std::string, std::string>> fragments;
    std::vector<std::pair<std::string, Noun>> nouns;         // longest first
    std::vector<std::pair<std::string, Modifier>> modifiers;  // longest first
    std::set<std::string> polish;
    std::function<void(const std::string&)> onMissing;
    size_t translated = 0, missingCount = 0;

    // Row kinds from pl.tsv: E exact, D dialog line, T template, F fragment,
    // N item noun (pl, gender), A modifier (m, f, n), P tail modifier (one form).
    bool Add(const std::vector<std::string>& row) {
        if (row.size() < 3) return false;
        const std::string& kind = row[0];
        const std::string& en = row[1];
        if (kind == "E" || kind == "D") {
            exact[en] = row[2];
            if (HasLetters(en)) upperExact.emplace(Upper(en), Upper(row[2]));
            // Literals with a space or symbol at an edge are concatenation pieces.
            if (kind == "E" && en.size() >= 5 && (!Alnum(en.front()) || !Alnum(en.back())) && HasLetters(en))
                fragments.emplace_back(en, row[2]);
        } else if (kind == "T") {
            Template t;
            if (!ParseTemplate(en, t) || t.holes.empty()) return false;
            t.pl = row[2];
            templates.push_back(t);
            size_t hole = t.pl.find('{');
            if (hole != std::string::npos && hole >= 4) polishStarts.insert(t.pl.substr(0, hole));
        } else if (kind == "F") {
            fragments.emplace_back(en, row[2]);
        } else if (kind == "N" && row.size() >= 4 && row[3].size() == 1) {
            nouns.push_back({en, {row[2], row[3][0]}});
            exact.emplace(en, row[2]);
        } else if (kind == "A" && row.size() >= 5) {
            modifiers.push_back({en, {row[2], row[3], row[4], false}});
        } else if (kind == "P") {
            modifiers.push_back({en, {row[2], row[2], row[2], true}});
        } else {
            return false;
        }
        polish.insert(row[2]);
        return true;
    }

    void Finish() {
        auto longer = [](const auto& a, const auto& b) { return a.first.size() > b.first.size(); };
        std::stable_sort(nouns.begin(), nouns.end(), longer);
        std::stable_sort(modifiers.begin(), modifiers.end(), longer);
        std::stable_sort(fragments.begin(), fragments.end(), longer);
        std::stable_sort(templates.begin(), templates.end(),
                         [](const Template& a, const Template& b) { return a.fixed > b.fixed; });
        byFirst.clear();
        cache.clear();
        for (const auto& f : fragments) byFirst[static_cast<unsigned char>(f.first[0])].push_back(&f);
    }

    std::string Translate(const std::string& text) {
        auto hit = cache.find(text);
        if (hit != cache.end()) return hit->second;
        std::string out;
        bool changed = Run(text, out, 0);
        if (!changed) {
            out = text;
            if (text.size() > 2 && HasLetters(text) && !LooksPolish(text) && missing.size() < 5000 &&
                missing.insert(text).second) {
                ++missingCount;
                if (onMissing) onMissing(text);
            }
            // A shortened name may be drawn before its full form; retry it later.
            if (text.size() > 3 && text.compare(text.size() - 3, 3, "...") == 0) return out;
        } else {
            ++translated;
            Remember(text, out);
        }
        if (cache.size() > 20000) cache.clear();
        cache.emplace(text, out);
        return out;
    }

    // Translates the spoken text of a Dialog/*.txt file and keeps its syntax:
    // [Block] headers, leading # (response) or = (continuation), trailing {Target}
    // and <Token> substitutions. Bracketed responses such as [Continue] stay as
    // they are, because the game may recognise them; the display pass translates them.
    std::string TranslateDialogFile(const std::string& content, size_t& done, size_t& total) {
        std::string body = content, out;
        if (body.compare(0, 3, "\xEF\xBB\xBF") == 0) { out = body.substr(0, 3); body.erase(0, 3); }
        size_t start = 0;
        while (start < body.size()) {
            size_t end = body.find('\n', start);
            bool newline = end != std::string::npos;
            std::string line = body.substr(start, (newline ? end : body.size()) - start);
            bool cr = !line.empty() && line.back() == '\r';
            if (cr) line.pop_back();
            out += DialogLine(line, done, total);
            if (cr) out += '\r';
            if (newline) out += '\n';
            start = newline ? end + 1 : body.size();
        }
        return out;
    }

private:
    std::set<std::string> polishStarts;

    std::string DialogLine(const std::string& line, size_t& done, size_t& total) {
        size_t a = line.find_first_not_of(" \t");
        if (a == std::string::npos || line[a] == '[') return line;
        size_t b = a;
        if (line[b] == '#' || line[b] == '=') ++b;
        while (b < line.size() && line[b] == ' ') ++b;
        size_t e = line.size();
        size_t brace = line.rfind('{');
        if (brace != std::string::npos && brace >= b && line.find('}', brace) != std::string::npos &&
            line.find_first_not_of(" \t", line.find('}', brace) + 1) == std::string::npos)
            e = brace;
        while (e > b && (line[e - 1] == ' ' || line[e - 1] == '\t')) --e;
        std::string core = line.substr(b, e - b);
        if (core.empty() || (core.front() == '[' && core.back() == ']')) return line;
        ++total;
        std::string pl;
        auto x = exact.find(core);
        if (x != exact.end()) pl = x->second;
        else if (!Templates(core, pl, 0)) return line;
        ++done;
        return line.substr(0, b) + pl + line.substr(e);
    }

    // Polish output, or a Polish line still being revealed: never report as missing.
    bool LooksPolish(const std::string& s) const {
        if (polish.count(s)) return true;
        for (size_t i = 0; i + 1 < s.size(); ++i) {
            unsigned char c = s[i], d = s[i + 1];
            if (c == 0xC4 || c == 0xC5 || (c == 0xC3 && d == 0xB3) || (c == 0xC3 && d == 0x93)) return true;
        }
        auto it = polish.lower_bound(s);
        if (it != polish.end() && it->compare(0, s.size(), s) == 0) return true;
        auto st = polishStarts.upper_bound(s);
        if (st != polishStarts.begin() && s.compare(0, std::prev(st)->size(), *std::prev(st)) == 0) return true;
        return false;
    }

    std::unordered_map<std::string, std::string> cache;
    std::set<std::string> missing;
    std::deque<std::pair<std::string, std::string>> recent;
    std::map<unsigned char, std::vector<const std::pair<std::string, std::string>*>> byFirst;

    static bool ParseTemplate(const std::string& en, Template& t) {
        std::string literal;
        for (size_t i = 0; i < en.size(); ++i) {
            if (en[i] == '{' && i + 2 < en.size() && en[i + 1] >= '0' && en[i + 1] <= '9' && en[i + 2] == '}') {
                t.literals.push_back(literal);
                t.fixed += literal.size();
                literal.clear();
                t.holes.push_back(en[i + 1] - '0');
                i += 2;
            } else {
                literal += en[i];
            }
        }
        t.literals.push_back(literal);
        t.fixed += literal.size();
        return true;
    }

    // Leftmost literal placement with backtracking; holes are never empty.
    static bool MatchFrom(const Template& t, const std::string& s, size_t li, size_t pos, std::vector<std::string>& caps) {
        const std::string& lit = t.literals[li];
        if (li + 1 == t.literals.size()) {
            if (s.size() < pos + 1 + lit.size()) return false;
            if (s.compare(s.size() - lit.size(), lit.size(), lit) != 0) return false;
            caps.push_back(s.substr(pos, s.size() - lit.size() - pos));
            return true;
        }
        for (size_t at = s.find(lit, pos + 1); at != std::string::npos; at = s.find(lit, at + 1)) {
            caps.push_back(s.substr(pos, at - pos));
            if (MatchFrom(t, s, li + 1, at + lit.size(), caps)) return true;
            caps.pop_back();
            if (lit.empty()) break;
        }
        return false;
    }

    static bool Match(const Template& t, const std::string& s, std::vector<std::string>& caps) {
        const std::string& first = t.literals[0];
        if (s.compare(0, first.size(), first) != 0) return false;
        return MatchFrom(t, s, 1, first.size(), caps);
    }

    std::string Hole(const std::string& value, int depth) {
        std::string out;
        return Run(value, out, depth + 1) ? out : value;
    }

    bool Templates(const std::string& s, std::string& out, int depth) {
        for (const auto& t : templates) {
            std::vector<std::string> caps;
            if (!Match(t, s, caps)) continue;
            std::map<int, std::string> values;
            for (size_t i = 0; i < caps.size(); ++i) values[t.holes[i]] = Hole(caps[i], depth);
            out.clear();
            for (size_t i = 0; i < t.pl.size(); ++i) {
                if (t.pl[i] == '{' && i + 2 < t.pl.size() && t.pl[i + 2] == '}' && values.count(t.pl[i + 1] - '0')) {
                    out += values[t.pl[i + 1] - '0'];
                    i += 2;
                } else {
                    out += t.pl[i];
                }
            }
            return true;
        }
        return false;
    }

    // "[modifiers] Noun": EN modifiers precede the noun; Polish puts the noun
    // first, agreeing adjectives in mirrored order, invariant phrases last.
    bool ItemName(const std::string& s, std::string& out) {
        for (const auto& noun : nouns) {
            const std::string& key = noun.first;
            if (s.size() <= key.size() || s.compare(s.size() - key.size(), key.size(), key) != 0 ||
                s[s.size() - key.size() - 1] != ' ')
                continue;
            std::string rest = s.substr(0, s.size() - key.size() - 1);
            std::vector<const Modifier*> found;
            size_t pos = 0;
            while (pos < rest.size()) {
                const Modifier* match = nullptr;
                size_t length = 0;
                for (const auto& m : modifiers) {
                    const std::string& k = m.first;
                    if (rest.compare(pos, k.size(), k) == 0 && (pos + k.size() == rest.size() || rest[pos + k.size()] == ' ')) {
                        match = &m.second;
                        length = k.size();
                        break;
                    }
                }
                if (!match) break;
                found.push_back(match);
                pos += length;
                if (pos < rest.size()) ++pos;
            }
            if (pos < rest.size() || found.empty()) continue;
            out = noun.second.pl;
            auto form = [&](const Modifier* m) {
                return noun.second.gender == 'f' ? m->f : noun.second.gender == 'n' ? m->n : m->m;
            };
            for (auto it = found.rbegin(); it != found.rend(); ++it) if (!(*it)->tail) out += " " + form(*it);
            for (const Modifier* m : found) if (m->tail) out += " " + form(m);
            return true;
        }
        return false;
    }

    bool Lines(const std::string& s, std::string& out, int depth) {
        if (s.find_first_of("#\r\n") == std::string::npos) return false;
        bool changed = false;
        out.clear();
        size_t start = 0;
        while (start <= s.size()) {
            size_t end = s.find_first_of("#\r\n", start);
            if (end == std::string::npos) end = s.size();
            std::string line = s.substr(start, end - start), translatedLine;
            if (!line.empty() && Run(line, translatedLine, depth + 1)) { out += translatedLine; changed = true; }
            else out += line;
            if (end < s.size()) out += s[end];
            start = end + 1;
        }
        return changed;
    }

    // Names shortened by the game ("Rechargeable High Cap...") after it measured the Polish text.
    bool Truncated(const std::string& s, std::string& out) {
        if (s.size() < 4 || s.compare(s.size() - 3, 3, "...") != 0) return false;
        std::string head = s.substr(0, s.size() - 3);
        for (auto it = recent.rbegin(); it != recent.rend(); ++it) {
            if (it->first.size() > head.size() && it->first.compare(0, head.size(), head) == 0) {
                size_t keep = CodePoints(it->second) * CodePoints(head) / CodePoints(it->first);
                out = FirstCodePoints(it->second, std::max<size_t>(1, keep));
                while (!out.empty() && out.back() == ' ') out.pop_back();
                out += "...";
                return true;
            }
        }
        return false;
    }

    bool Fragments(const std::string& s, std::string& out) {
        bool changed = false;
        out.clear();
        for (size_t i = 0; i < s.size();) {
            bool boundary = i == 0 || !Alnum(s[i - 1]) || !Alnum(s[i]);
            auto list = boundary ? byFirst.find(static_cast<unsigned char>(s[i])) : byFirst.end();
            const std::pair<std::string, std::string>* match = nullptr;
            if (list != byFirst.end()) {
                for (const auto* f : list->second) {
                    const std::string& k = f->first;
                    if (s.compare(i, k.size(), k) != 0) continue;
                    size_t end = i + k.size();
                    if (end < s.size() && Alnum(k.back()) && Alnum(s[end])) continue;
                    match = f;
                    break;
                }
            }
            if (match) { out += match->second; i += match->first.size(); changed = true; }
            else out += s[i++];
        }
        return changed;
    }

    void Remember(const std::string& en, const std::string& pl) {
        if (en.size() < 6) return;
        recent.emplace_back(en, pl);
        if (recent.size() > 256) recent.pop_front();
    }

    bool Run(const std::string& s, std::string& out, int depth) {
        if (depth > 6 || s.empty()) return false;
        auto e = exact.find(s);
        if (e != exact.end()) { out = e->second; return true; }
        if (depth > 0) {
            auto c = cache.find(s);
            if (c != cache.end() && c->second != s) { out = c->second; return true; }
        }
        if (HasLetters(s) && Upper(s) == s) {
            auto u = upperExact.find(s);
            if (u != upperExact.end()) { out = u->second; return true; }
        }
        size_t first = s.find_first_not_of(' '), last = s.find_last_not_of(' ');
        if (first == std::string::npos) return false;
        if (first != 0 || last + 1 != s.size()) {
            std::string inner;
            if (Run(s.substr(first, last - first + 1), inner, depth + 1)) {
                out = s.substr(0, first) + inner + s.substr(last + 1);
                return true;
            }
        }
        if (ItemName(s, out)) return true;
        if (Templates(s, out, depth)) return true;
        if (Lines(s, out, depth)) return true;
        if (Truncated(s, out)) return true;
        return Fragments(s, out);
    }
};

}  // namespace tr
