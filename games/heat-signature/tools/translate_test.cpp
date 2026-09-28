// Unit test of plugin/Translate.h with strings observed in the game's own log.
// Optional argument: path to a built pl.tsv, whose rows must all be accepted.
#include "../plugin/Translate.h"
#include <cassert>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <sstream>

static void Expect(tr::Engine& e, const std::string& en, const std::string& pl) {
    std::string got = e.Translate(en);
    if (got != pl) { printf("FAIL\n  EN:   %s\n  want: %s\n  got:  %s\n", en.c_str(), pl.c_str(), got.c_str()); exit(1); }
}

int main(int argc, char** argv) {
    tr::Engine e;
    std::vector<std::vector<std::string>> rows = {
        {"E", "Resume", u8"Wznów"},
        {"E", "Lucky", u8"Szczęściarz"},
        {"N", "Swapper", u8"Zamieniacz", "m"},
        {"N", "Glitch Trap", u8"Pułapka glitchowa", "f"},
        {"N", "Longblade", u8"Długie ostrze", "n"},
        {"N", "Gun", u8"Pistolet", "m"},
        {"A", "Rechargeable", u8"ładowalny", u8"ładowalna", u8"ładowalne"},
        {"A", "Armour-Piercing", u8"przeciwpancerny", u8"przeciwpancerna", u8"przeciwpancerne"},
        {"A", "Quiet", u8"cichy", u8"cicha", u8"ciche"},
        {"P", "High Capacity", u8"o dużej pojemności"},
        {"P", "Long Range", u8"dalekiego zasięgu"},
        {"T", "Kills: {0}", u8"Zabójstwa: {0}"},
        {"T", "Steal the {0} to make enough money to {1}", u8"Ukraść {0}, by zarobić na to, żeby {1}"},
        {"E", "pay off a debt", u8"spłacić dług"},
        {"T", "{0} was detected by {1}'s heat sensor.", u8"{1}: czujnik ciepła wykrył {0}."},
        {"F", ", Patrolling", u8", patroluje"},
        {"F", " to fire.", u8" za strzał."},
        {"E", "Fires a spray of acid. Costs $", u8"Pluje kwasem. Koszt: $"},
        {"D", "This is not how I pictured my retirement.", u8"Nie tak wyobrażałem sobie emeryturę."},
        {"E", "Traits", u8"Cechy"},
        {"E", "Ghost Vow", u8"Ślub ducha"},
    };
    for (auto& r : rows) assert(e.Add(r));
    e.Finish();

    Expect(e, "Resume", u8"Wznów");
    Expect(e, "RESUME", u8"WZNÓW");
    Expect(e, "  Resume ", u8"  Wznów ");
    Expect(e, "Rechargeable High Capacity Swapper", u8"Zamieniacz ładowalny o dużej pojemności");
    Expect(e, "Rechargeable High Capacity Glitch Trap", u8"Pułapka glitchowa ładowalna o dużej pojemności");
    Expect(e, "Quiet Armour-Piercing Longblade", u8"Długie ostrze przeciwpancerne ciche");
    Expect(e, "Quiet Gun", u8"Pistolet cichy");
    Expect(e, "Unknown Gun", "Unknown Gun");
    Expect(e, "Kills: 31", u8"Zabójstwa: 31");
    Expect(e, "Steal the Polk Mark III to make enough money to pay off a debt",
           u8"Ukraść Polk Mark III, by zarobić na to, żeby spłacić dług");
    Expect(e, "Gio Vanderstar was detected by Sly Grounder's heat sensor.",
           u8"Sly Grounder: czujnik ciepła wykrył Gio Vanderstar.");
    Expect(e, "Guard, Patrolling", u8"Guard, patroluje");
    Expect(e, "Fires a spray of acid. Costs $12 to fire.", u8"Pluje kwasem. Koszt: $12 za strzał.");
    Expect(e, "Traits#Ghost Vow", u8"Cechy#Ślub ducha");
    Expect(e, "Kills: 0\r\nLucky", u8"Zabójstwa: 0\r\nSzczęściarz");
    // A prefix of a dialogue line is not translated on display (it could be a name).
    Expect(e, "This is not", "This is not");
    Expect(e, "This is not how I pictured my retirement.", u8"Nie tak wyobrażałem sobie emeryturę.");
    // Dialogue files are translated at load, keeping the dialogue syntax intact.
    assert(e.Add({"T", "Hey {0}, how've you been?", u8"Hej, {0}, co u ciebie?"}));
    assert(e.Add({"E", "[Continue]", u8"[Dalej]"}));
    e.Finish();
    size_t done = 0, total = 0;
    std::string file = "\xEF\xBB\xBF[Start]\r\nThis is not how I pictured my retirement.\r\n# Resume {Next}\r\n#[Continue] {End}\r\n=Hey <PlayerName>, how've you been?\r\n#Unknown line.{End}\r\n\r\n";
    std::string want = "\xEF\xBB\xBF[Start]\r\n" u8"Nie tak wyobrażałem sobie emeryturę." "\r\n"
                       u8"# Wznów {Next}\r\n#[Continue] {End}\r\n=Hej, <PlayerName>, co u ciebie?\r\n#Unknown line.{End}\r\n\r\n";
    std::string got = e.TranslateDialogFile(file, done, total);
    if (got != want || done != 3 || total != 4) { printf("FAIL dialog file (%zu/%zu)\n%s\n", done, total, got.c_str()); return 1; }
    // Game shortens after measuring the (translated) full name.
    Expect(e, "Rechargeable Long Range Swapper", u8"Zamieniacz ładowalny dalekiego zasięgu");
    Expect(e, "Rechargeable Long Ran...", u8"Zamieniacz ładowalny dale...");
    // Names and numbers alone stay; Polish output is never logged as missing.
    size_t before = e.missingCount;
    Expect(e, "Gio Vanderstar", "Gio Vanderstar");
    Expect(e, u8"Wznów", u8"Wznów");
    assert(e.missingCount == before + 1);

    if (argc > 1) {
        tr::Engine full;
        std::ifstream in(argv[1], std::ios::binary);
        std::string line;
        size_t n = 0;
        while (std::getline(in, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            std::vector<std::string> row;
            size_t start = 0;
            for (size_t tab; (tab = line.find('\t', start)) != std::string::npos; start = tab + 1) row.push_back(line.substr(start, tab - start));
            row.push_back(line.substr(start));
            if (!full.Add(row)) { printf("FAIL: rejected row %zu: %s\n", n + 1, line.c_str()); return 1; }
            ++n;
        }
        full.Finish();
        printf("pl.tsv: %zu rows accepted\n", n);
        // Optional preview: one EN string per line (\n escapes), printed as EN => PL.
        if (argc > 2) {
            std::ifstream samples(argv[2], std::ios::binary);
            size_t same = 0, total = 0;
            while (std::getline(samples, line)) {
                if (!line.empty() && line.back() == '\r') line.pop_back();
                std::string en;
                for (size_t i = 0; i < line.size(); ++i) {
                    if (line[i] == '\\' && i + 1 < line.size() && line[i + 1] == 'n') { en += '\n'; ++i; }
                    else en += line[i];
                }
                if (en.empty()) continue;
                std::string pl = full.Translate(en);
                ++total;
                if (pl == en) ++same;
                printf("%s %s\n    => %s\n", pl == en ? "--" : "OK", en.c_str(), pl.c_str());
            }
            printf("preview: %zu of %zu unchanged\n", same, total);
        }
        // Optional: the game's Dialog folder, translated exactly as at load time.
        if (argc > 3) {
            size_t allDone = 0, allTotal = 0;
            for (const auto& entry : std::filesystem::directory_iterator(argv[3])) {
                if (entry.path().extension() != ".txt") continue;
                std::ifstream f(entry.path(), std::ios::binary);
                std::string content((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
                size_t done = 0, total = 0;
                std::string out = full.TranslateDialogFile(content, done, total);
                printf("%s: %zu/%zu\n", entry.path().filename().string().c_str(), done, total);
                allDone += done; allTotal += total;
                std::istringstream lines(out);
                std::string l;
                while (std::getline(lines, l)) {
                    bool ascii = std::all_of(l.begin(), l.end(), [](char c) { return static_cast<unsigned char>(c) < 0x80; });
                    if (ascii && l.find_first_of("abcdefghijklmnopqrstuvwxyz") != std::string::npos && l.find('[') != 0)
                        printf("    EN? %s\n", l.c_str());
                }
            }
            printf("dialogue files: %zu of %zu lines translated\n", allDone, allTotal);
        }
    }
    puts("PASS: exact, uppercase, item names with gender, templates, fragments, lines, dialogue files, truncation.");
}
