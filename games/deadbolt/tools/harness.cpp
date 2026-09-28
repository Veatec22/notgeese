// Plugin test without the game: does what the runner does (whole data.win in a heap buffer,
// then Direct3DCreate9 from the test dir's d3d9.dll) and dumps the buffer as the game will
// see it: STRG strings, font glyphs, texture pages and redirected JSON.
//   harness.exe <katalog testu>
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

static const uint8_t* At(const uint8_t* base, uint32_t off) {
    return reinterpret_cast<const uint8_t*>(static_cast<uint32_t>(reinterpret_cast<uintptr_t>(base) + off));
}
static uint32_t U32(const uint8_t* p) { uint32_t v; memcpy(&v, p, 4); return v; }

int wmain(int argc, wchar_t** argv) {
    if (argc < 2) return 2;
    SetCurrentDirectoryW(argv[1]);
    FILE* f = _wfopen(L"data.win", L"rb");
    if (!f) return 3;
    fseek(f, 0, SEEK_END); long size = ftell(f); fseek(f, 0, SEEK_SET);
    auto base = static_cast<uint8_t*>(malloc(size));
    fread(base, 1, size, f); fclose(f);

    HMODULE plugin = LoadLibraryW(L"d3d9.dll");
    if (!plugin) return 4;
    using Create = void* (WINAPI*)(UINT);
    auto create = reinterpret_cast<Create>(GetProcAddress(plugin, "Direct3DCreate9"));
    void* d3d = create ? create(32) : nullptr;
    if (d3d) (*reinterpret_cast<ULONG(__stdcall***)(void*)>(d3d))[2](d3d);   // Release

    // Chunki
    uint32_t strg = 0, font = 0, txtr = 0;
    for (uint32_t o = 8; o + 8 <= uint32_t(size);) {
        uint32_t len = U32(base + o + 4);
        if (!memcmp(base + o, "STRG", 4) && !strg) strg = o + 8;
        if (!memcmp(base + o, "FONT", 4)) font = o + 8;
        if (!memcmp(base + o, "TXTR", 4)) txtr = o + 8;
        o += 8 + len;
    }
    FILE* out = _wfopen(L"out-strings.txt", L"wb");
    for (uint32_t i = 0, n = U32(base + strg); i < n; ++i) {
        const char* s = reinterpret_cast<const char*>(At(base, U32(base + strg + 4 + 4 * i)) + 4);
        fprintf(out, "%u\t", i);
        for (; *s; ++s) {
            if (*s == '\n') fputs("\\n", out); else if (*s == '\r') fputs("\\r", out);
            else if (*s == '\\') fputs("\\\\", out); else if (*s == '\t') fputs("\\t", out); else fputc(*s, out);
        }
        fputc('\n', out);
    }
    fclose(out);
    out = _wfopen(L"out-fonts.txt", L"wb");
    for (uint32_t i = 0, n = U32(base + font); i < n; ++i) {
        const uint8_t* fs = At(base, U32(base + font + 4 + 4 * i));
        const char* name = reinterpret_cast<const char*>(At(base, U32(fs)));
        const uint8_t* tp = At(base, U32(fs + 0x1c));
        uint16_t t[11]; memcpy(t, tp, sizeof(t));
        for (uint32_t g = 0, count = U32(fs + 0x28); g < count; ++g) {
            const uint8_t* gl = At(base, U32(fs + 0x2c + 4 * g));
            uint16_t v[5]; int16_t so[2]; memcpy(v, gl, 10); memcpy(so, gl + 10, 4);
            fprintf(out, "%s\t%u\t%u\t%u\t%u\t%u\t%d\t%d\t%u\t%u\t%u\n", name, v[0], v[1], v[2], v[3], v[4],
                    so[0], so[1], t[10], t[0], t[1]);
        }
    }
    fclose(out);
    for (uint32_t i = 0, n = U32(base + txtr); i < n; ++i) {
        const uint8_t* entry = At(base, U32(base + txtr + 4 + 4 * i));
        const uint8_t* png = At(base, U32(entry + 4));
        size_t len = 8;
        while (memcmp(png + len - 8, "IEND", 4)) ++len;          // IEND + CRC
        wchar_t name[64]; swprintf(name, 64, L"out-page%u.png", i);
        FILE* p = _wfopen(name, L"wb"); fwrite(png, 1, len, p); fclose(p);
    }
    // Full buffer (code and lists) for checking in Python.
    out = _wfopen(L"out-buffer.bin", L"wb"); fwrite(base, 1, size, out); fclose(out);
    // JSON redirect: open like the runner does, with a relative path.
    HANDLE h = CreateFileW(L"dia_fp.json", GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, 0, nullptr);
    if (h != INVALID_HANDLE_VALUE) {
        std::vector<char> buf(1 << 20); DWORD got = 0;
        ReadFile(h, buf.data(), DWORD(buf.size()), &got, nullptr); CloseHandle(h);
        FILE* j = _wfopen(L"out-dia_fp.json", L"wb"); fwrite(buf.data(), 1, got, j); fclose(j);
    }
    printf("harness done\n");
    return 0;
}
