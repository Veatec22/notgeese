// Ultrawide mod (ultrawide\settings.ini, Enabled=1). All writes are prepared and validated before applying.
static std::wstring UltrawideIni() { return root + L"ultrawide\\settings.ini"; }

// GMS1 ROOM/View layout: UndertaleModLib/Models/UndertaleRoom.cs.
// GEN8 dimensions have already been cached at this entry point. Locate their stores
// by instructions and validate each destination against writable PE data sections.
static bool RunnerDimensions(std::vector<uint32_t*>& sizes, uint32_t flags) {
    auto image = reinterpret_cast<uint8_t*>(GetModuleHandleW(nullptr));
    auto dos = reinterpret_cast<IMAGE_DOS_HEADER*>(image);
    if (dos->e_magic != IMAGE_DOS_SIGNATURE) return false;
    auto nt = reinterpret_cast<IMAGE_NT_HEADERS*>(image + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE || nt->FileHeader.Machine != IMAGE_FILE_MACHINE_I386) return false;
    auto sections = IMAGE_FIRST_SECTION(nt);
    // mov eax,[esi+3c]; store width; mov ecx,[esi+40]; store height;
    // mov edx,[esi+44]; store flags; store application width; store application height.
    const uint8_t pattern[] = {0x8b,0x46,0x3c,0xa3,0,0,0,0,0x8b,0x4e,0x40,0x89,0x0d,0,0,0,0,
        0x8b,0x56,0x44,0x89,0x15,0,0,0,0,0xa3,0,0,0,0,0x89,0x0d,0,0,0,0};
    const size_t operand[] = {4,13,22,27,33};
    size_t matches = 0;
    for (unsigned i = 0; i < nt->FileHeader.NumberOfSections; ++i) {
        auto& s = sections[i];
        if (!(s.Characteristics & IMAGE_SCN_MEM_EXECUTE)) continue;
        for (size_t o = 0; o + sizeof(pattern) <= s.Misc.VirtualSize; ++o) {
            const auto p = image + s.VirtualAddress + o;
            bool match = true;
            for (size_t k = 0; k < sizeof(pattern); ++k) {
                bool wildcard = false;
                for (size_t a : operand) if (k >= a && k < a + 4) wildcard = true;
                if (!wildcard && p[k] != pattern[k]) { match = false; break; }
            }
            if (!match) continue;
            std::vector<uint32_t*> targets;
            for (size_t a : operand) {
                uint32_t address; memcpy(&address, p + a, 4);
                uintptr_t relative = address - reinterpret_cast<uintptr_t>(image);
                bool writable = false;
                for (unsigned j = 0; j < nt->FileHeader.NumberOfSections; ++j) {
                    const auto& ds = sections[j];
                    if ((ds.Characteristics & IMAGE_SCN_MEM_WRITE) && ds.Misc.VirtualSize >= 4 &&
                        relative >= ds.VirtualAddress && relative - ds.VirtualAddress <= ds.Misc.VirtualSize - 4)
                        writable = true;
                }
                if (!writable) return false;
                targets.push_back(reinterpret_cast<uint32_t*>(address));
            }
            if (*targets[0] != 960 || *targets[1] != 540 || *targets[2] != flags ||
                *targets[3] != 960 || *targets[4] != 540) return false;
            if (targets[0] == targets[3] || targets[1] == targets[4]) return false;
            sizes = {targets[0], targets[3]};
            ++matches;
        }
    }
    return matches == 1;
}

static void ApplyUltrawide(Form& live, Form& disk) {
    const auto ini = UltrawideIni();
    if (!GetPrivateProfileIntW(L"Ultrawide", L"Enabled", 0, ini.c_str())) return;
    int width = GetPrivateProfileIntW(L"Ultrawide", L"VirtualWidth", 0, ini.c_str());
    if (!width) {
        int sw = GetSystemMetrics(SM_CXSCREEN), sh = GetSystemMetrics(SM_CYSCREEN);
        if (sh <= 0) return;
        width = static_cast<int>((540LL * sw + sh / 2) / sh);
        width = (width + 1) & ~1;
    }
    if (width <= 960 || width > 3840) { Log("Ultrawide: unsupported width %d; disabled", width); return; }
    if (disk.base[disk.Chunk("GEN8").first + 1] != 15) {
        Log("Ultrawide: unknown bytecode; disabled"); return;
    }
    std::vector<std::pair<uint32_t, uint32_t>> changes;
    uint32_t gen = disk.Chunk("GEN8").first;
    if (disk.U32(gen + 0x3c) != 960 || disk.U32(gen + 0x40) != 540) {
        Log("Ultrawide: unknown output dimensions; disabled"); return;
    }
    std::vector<uint32_t*> runnerSizes;
    if (!RunnerDimensions(runnerSizes, disk.U32(gen + 0x44))) {
        Log("Ultrawide: runner output signature/state not found; disabled"); return;
    }
    changes.push_back({gen + 0x3c, static_cast<uint32_t>(width)});
    auto room = disk.Chunk("ROOM");
    if (memcmp(live.base + room.first, disk.base + room.first, room.second)) {
        Log("Ultrawide: ROOM already parsed; disabled"); return;
    }
    size_t views = 0, constants = 0;
    for (auto p : disk.List("ROOM")) {
        uint32_t list = disk.U32(p + 44), n = disk.U32(list);
        if (n != 8) { Log("Ultrawide: unknown view list; disabled"); return; }
        for (uint32_t i = 0; i < n; ++i) {
            uint32_t v = disk.U32(list + 4 + 4 * i);
            if (!disk.U32(v)) continue;
            if (disk.U32(v + 12) != 960 || disk.U32(v + 16) != 540 ||
                disk.U32(v + 28) != 960 || disk.U32(v + 32) != 540) {
                Log("Ultrawide: unknown view dimensions; disabled"); return;
            }
            changes.push_back({v + 12, static_cast<uint32_t>(width)});
            changes.push_back({v + 28, static_cast<uint32_t>(width)});
            ++views;
        }
    }
    // Keep the proven full-width render path. Center the main menu's coordinate
    // origin and fix the load list's hard-coded hit-test center instead of its viewport.
    std::map<uint32_t, std::string> variableSites;
    auto vari = disk.Chunk("VARI");
    for (uint32_t p = vari.first + 12; p + 20 <= vari.first + vari.second; p += 20) {
        auto name = disk.Str(disk.U32(p));
        if (name != "view_xview" && name != "view_wview") continue;
        uint32_t addr = disk.U32(p + 16), count = disk.U32(p + 12);
        if (count > 100000) { Log("Ultrawide: invalid variable chain; disabled"); return; }
        for (uint32_t i = 0; i < count; ++i) {
            variableSites[addr] = name;
            addr += disk.U32(addr + 4) & 0x07ffffff;
        }
    }
    std::set<uint32_t> rewrittenReferences;
    size_t menuReads = 0, hitCenters = 0;
    for (const auto& e : CodeEntries(disk)) {
        if (e.name == "gml_Object_oMain_Draw_0") {
            for (const auto& [off, name] : variableSites) {
                if (off < e.start + 8 || off + 8 > e.start + e.length) continue;
                if (disk.U32(off - 8) != 0x840fffff || disk.U32(off - 4) != 0x840f0000 ||
                    disk.U32(off) != 0xc0050000) {
                    Log("Ultrawide: menu array read changed; disabled"); return;
                }
                double value = name == "view_xview" ? (width - 960) / 2.0 : 960.0;
                uint32_t words[2]; memcpy(words, &value, sizeof(value));
                // Replace the 16-byte array read with a double push and conversion
                // to variant. Same stack effect and length; no branch/chain relocation.
                changes.push_back({off - 8, 0xc0000000});
                changes.push_back({off - 4, words[0]});
                changes.push_back({off, words[1]});
                changes.push_back({off + 4, 0x07500000});
                rewrittenReferences.insert(off + 4);
                ++menuReads;
            }
        } else if (e.name == "gml_Object_oLoadGame_Draw_0") {
            for (uint32_t o = e.start; o + 20 <= e.start + e.length; o += 4) {
                if (disk.U32(o) != 0xc305ffff || disk.U32(o + 8) != 0x840f0212 ||
                    disk.U32(o + 12) != 0x0d520000 || disk.U32(o + 16) != 0xd9020001) continue;
                changes.push_back({o + 8, 0x840f0000u | static_cast<uint32_t>(530 + (width - 960) / 2)});
                ++hitCenters;
            }
        }
    }
    if (menuReads != 9 || hitCenters != 1) {
        Log("Ultrawide: menu plan incomplete (%zu reads, %zu hits); disabled", menuReads, hitCenters); return;
    }
    // Match named entries and complete instruction sequences, never fixed file offsets.
    for (const auto& e : CodeEntries(disk)) {
        if (e.name == "gml_Script_init_screen") {
            size_t hits = 0;
            for (uint32_t o = e.start; o + 20 <= e.start + e.length; o += 4) {
                if (disk.U32(o) != 0x840f03c0 || disk.U32(o + 4) != 0x4525ffff ||
                    disk.U32(o + 12) != 0x840f021c || disk.U32(o + 16) != 0x4525ffff) continue;
                changes.push_back({o, 0x840f0000u | static_cast<uint32_t>(width)});
                ++hits;
            }
            if (hits != 1) { Log("Ultrawide: init_screen pattern changed; disabled"); return; }
            constants += hits;
        } else if (e.name == "gml_Object_oLoadRoom_Other_10") {
            size_t hits = 0;
            // room_set_view arguments, reverse stack order: hport,wport,xport,yport,hview,wview.
            const uint32_t pattern[] = {0x840f021c, 0x07520000, 0x840f03c0, 0x07520000,
                0x840f0000, 0x07520000, 0x840f0000, 0x07520000,
                0x840f021c, 0x07520000, 0x840f03c0, 0x07520000};
            for (uint32_t o = e.start; o + sizeof(pattern) <= e.start + e.length; o += 4) {
                if (memcmp(disk.base + o, pattern, sizeof(pattern))) continue;
                changes.push_back({o + 8, 0x840f0000u | static_cast<uint32_t>(width)});
                changes.push_back({o + 40, 0x840f0000u | static_cast<uint32_t>(width)});
                ++hits;
            }
            if (hits != 1) { Log("Ultrawide: mission camera pattern changed; disabled"); return; }
            constants += 2 * hits;
        }
    }
    if (!views || constants != 3) { Log("Ultrawide: incomplete plan; disabled"); return; }
    for (auto [off, value] : changes) {
        (void)value;
        if (!rewrittenReferences.count(off) && live.U32(off) != disk.U32(off)) {
            Log("Ultrawide: operand already rewritten at %08x; disabled", off); return;
        }
    }
    for (auto [off, value] : changes) live.Put32(off, value);
    for (auto target : runnerSizes) *target = static_cast<uint32_t>(width);
    Log("Ultrawide output: cached window and application widths 960 -> %d; heights 540", width);
    Log("Ultrawide: %dx540, %zu room views, %zu code constants", width, views, constants);
    Log("Ultrawide menus: %zu coordinate reads centered, %zu load hit center; full-width viewport", menuReads, hitCenters);
}
