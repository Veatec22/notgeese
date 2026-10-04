// DEADBOLT PL — plugin d3d9.dll (proxy). GameMaker Studio 1.4, VM, bytecode 15.
//
// The runner loads the whole data.win into a buffer, pre-scans it (remembers the base
// and the STRG list), only then creates the Direct3D device, and finally parses
// FONT, TXTR and CODE. Our d3d9.dll loads from the delayed import at Direct3DCreate9;
// in that gap we patch the buffer in memory:
//   - fonts: new structures with Polish letters composed from game letters and our marks,
//     texture pages re-encoded via WIC;
//   - strings: STRG list entries point at our texts (the runner computes base + offset
//     in 32 bits, so new data can live in our memory);
//   - dialogue dia_*.json: translated at start into notgeese\cache, opening redirected.
// No fixed addresses or checksums. Any error = game in English + a log line.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <objbase.h>
#include <shlwapi.h>
#include <wincodec.h>
#include <share.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
#include "MinHook.h"

static const char* kVersion = "0.2";

static HMODULE selfModule;
static std::wstring root;       // game dir (where our d3d9.dll lives)
static FILE* logfile;

static void Log(const char* fmt, ...) {
    if (!logfile) return;
    va_list args; va_start(args, fmt); vfprintf(logfile, fmt, args); va_end(args);
    fputc('\n', logfile); fflush(logfile);
}

static std::string Utf8(const std::wstring& w) {
    int n = WideCharToMultiByte(CP_UTF8, 0, w.c_str(), -1, nullptr, 0, nullptr, nullptr);
    std::string s(n > 0 ? n - 1 : 0, '\0');
    if (n > 1) WideCharToMultiByte(CP_UTF8, 0, w.c_str(), -1, &s[0], n, nullptr, nullptr);
    return s;
}

static bool ReadFileBytes(const std::wstring& path, std::vector<uint8_t>& out) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return false;
    out.assign(std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>());
    return true;
}

// ---------------------------------------------------------------- permanent memory

// Everything the game points to lives until process exit: a simple arena, never freed.
static uint8_t* Keep(size_t size) {
    static uint8_t* cursor = nullptr;
    static size_t left = 0;
    const size_t block = 1 << 20;
    size = (size + 3) & ~size_t(3);
    if (size > block / 4) {
        auto p = static_cast<uint8_t*>(VirtualAlloc(nullptr, size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
        if (!p) throw std::bad_alloc();
        return p;
    }
    if (size > left) {
        cursor = static_cast<uint8_t*>(VirtualAlloc(nullptr, block, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
        if (!cursor) throw std::bad_alloc();
        left = block;
    }
    uint8_t* p = cursor;
    cursor += size; left -= size;
    return p;
}

// ---------------------------------------------------------------- data.win in memory

struct Form {
    uint8_t* base = nullptr;
    uint32_t size = 0;
    std::map<std::string, std::pair<uint32_t, uint32_t>> chunks;   // name -> (data start, size)

    uint32_t U32(uint32_t off) const {
        if (off > size - 4) throw std::runtime_error("read outside data.win");
        uint32_t v; memcpy(&v, base + off, 4); return v;
    }
    uint16_t U16(uint32_t off) const {
        if (off > size - 2) throw std::runtime_error("read outside data.win");
        uint16_t v; memcpy(&v, base + off, 2); return v;
    }
    int32_t I32(uint32_t off) const { return static_cast<int32_t>(U32(off)); }
    template <class T> T Get(uint32_t off) const {
        if (off > size - sizeof(T)) throw std::runtime_error("struct outside data.win");
        T v; memcpy(&v, base + off, sizeof(T)); return v;
    }
    void Put32(uint32_t off, uint32_t v) {
        if (off > size - 4) throw std::runtime_error("write outside data.win");
        memcpy(base + off, &v, 4);
    }
    std::string Str(uint32_t off) const {      // zero-terminated text at the offset
        if (off >= size) throw std::runtime_error("string outside data.win");
        const char* p = reinterpret_cast<const char*>(base + off);
        size_t n = strnlen(p, size - off);
        if (n == size - off) throw std::runtime_error("unterminated string");
        return std::string(p, n);
    }
    uint32_t Offset(const void* p) const {     // runner: address = base + offset (mod 2^32)
        return static_cast<uint32_t>(reinterpret_cast<uintptr_t>(p) - reinterpret_cast<uintptr_t>(base));
    }
    const uint8_t* At(uint32_t off) const {     // inverse of Offset, computed like the runner
        return reinterpret_cast<const uint8_t*>(static_cast<uint32_t>(reinterpret_cast<uintptr_t>(base) + off));
    }
    std::pair<uint32_t, uint32_t> Chunk(const char* name) const {
        auto it = chunks.find(name);
        if (it == chunks.end()) throw std::runtime_error(std::string("missing chunk ") + name);
        return it->second;
    }
    std::vector<uint32_t> List(const char* name) const {
        uint32_t s = Chunk(name).first, n = U32(s);
        if (n > 1000000) throw std::runtime_error("list too long");
        std::vector<uint32_t> out(n);
        for (uint32_t i = 0; i < n; ++i) out[i] = U32(s + 4 + 4 * i);
        return out;
    }
};

// Finds the data.win copy in the runner's memory: a FORM header of the file's length, then
// a chunk-by-chunk comparison. Chunks we change or read (STRG, FONT, TXTR, TPAG) must equal
// the file byte for byte: proof the runner hasn't parsed them yet.
// Differences in other chunks are only logged (the runner may have patched something there).
static bool FindForm(const std::vector<uint8_t>& file, Form& form) {
    const uint32_t size = static_cast<uint32_t>(file.size());
    std::vector<std::pair<std::string, std::pair<uint32_t, uint32_t>>> table;   // chunk -> (header start, length)
    for (uint32_t o = 8; o + 8 <= size;) {
        uint32_t len; memcpy(&len, file.data() + o + 4, 4);
        if (len > size - o - 8) { Log("data.win on disk is malformed: disabled"); return false; }
        table.push_back({std::string(reinterpret_cast<const char*>(file.data() + o), 4), {o, len + 8}});
        o += 8 + len;
    }
    static const std::set<std::string> required = {"GEN8", "STRG", "FONT", "TXTR", "TPAG"};
    std::vector<uint8_t*> found;
    size_t candidates = 0;
    SYSTEM_INFO si; GetSystemInfo(&si);
    auto p = static_cast<uint8_t*>(si.lpMinimumApplicationAddress);
    MEMORY_BASIC_INFORMATION mbi;
    const DWORD writable = PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY;
    while (p < si.lpMaximumApplicationAddress && VirtualQuery(p, &mbi, sizeof(mbi)) == sizeof(mbi)) {
        auto region = static_cast<uint8_t*>(mbi.BaseAddress);
        size_t len = mbi.RegionSize;
        if (mbi.State == MEM_COMMIT && (mbi.Protect & writable) && !(mbi.Protect & (PAGE_GUARD | PAGE_NOACCESS)) &&
            len >= size) {
            for (size_t i = 0; i + size <= len; i += 4) {
                uint8_t* at = region + i;
                if (at[0] != 'F' || memcmp(at, file.data(), 12) != 0 || at == file.data()) continue;
                ++candidates;
                std::string diffs;
                bool ok = true;
                for (auto& [name, range] : table) {
                    if (memcmp(at + range.first, file.data() + range.first, range.second) == 0) continue;
                    size_t n = 0;
                    for (uint32_t k = 0; k < range.second; ++k) n += at[range.first + k] != file[range.first + k];
                    diffs += " " + name + ":" + std::to_string(n);
                    if (required.count(name)) ok = false;
                }
                Log("Candidate at %p (region %p, %s): %s%s", at, region,
                    mbi.Type == MEM_PRIVATE ? "private" : mbi.Type == MEM_MAPPED ? "mapped" : "image",
                    diffs.empty() ? "identical to file" : "differs in", diffs.c_str());
                if (ok) found.push_back(at);
                i += size - 4;                              // one copy at a time, no overlap
            }
        }
        p = region + len;
    }
    if (found.size() != 1) {
        Log("data.win buffer: %zu candidates, %zu usable (need exactly 1): disabled", candidates, found.size());
        return false;
    }
    form.base = found[0];
    form.size = static_cast<uint32_t>(file.size());
    for (uint32_t o = 8; o + 8 <= form.size;) {
        std::string name(reinterpret_cast<char*>(form.base + o), 4);
        uint32_t len = form.U32(o + 4);
        if (len > form.size - o - 8) { Log("Chunk %s overruns file: disabled", name.c_str()); return false; }
        if (!form.chunks.count(name)) form.chunks[name] = {o + 8, len};
        o += 8 + len;
    }
    Log("data.win buffer found at %p (%u bytes, %zu chunks)", form.base, form.size, form.chunks.size());
    return true;
}

// ---------------------------------------------------------------- translations

struct Row { std::string kind, en, pl, context; };

static std::string Unescape(const std::string& s) {
    std::string out;
    for (size_t i = 0; i < s.size(); ++i) {
        if (s[i] == '\\' && i + 1 < s.size()) {
            char c = s[++i];
            if (c == 'n') out += '\n'; else if (c == 'r') out += '\r';
            else if (c == 't') out += '\t'; else if (c == '\\') out += '\\';
            else { out += '\\'; out += c; }
        } else out += s[i];
    }
    return out;
}

static std::vector<Row> LoadRows(const std::wstring& path) {
    std::vector<Row> rows;
    std::ifstream in(path, std::ios::binary);
    std::string line;
    while (std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty() || line[0] == '#') continue;
        std::vector<std::string> f;
        size_t start = 0;
        for (size_t tab; (tab = line.find('\t', start)) != std::string::npos; start = tab + 1)
            f.push_back(line.substr(start, tab - start));
        f.push_back(line.substr(start));
        if (f.size() < 3) continue;
        rows.push_back({f[0], Unescape(f[1]), Unescape(f[2]), f.size() > 3 ? f[3] : ""});
    }
    return rows;
}

// ---------------------------------------------------------------- PNG via WIC

struct Image { UINT w = 0, h = 0; std::vector<uint8_t> bgra; };

static IWICImagingFactory* factory = nullptr;

static IWICImagingFactory* Wic() {
    if (!factory && FAILED(CoCreateInstance(CLSID_WICImagingFactory, nullptr, CLSCTX_INPROC_SERVER,
                                            IID_PPV_ARGS(&factory)))) factory = nullptr;
    return factory;
}

static void ReleaseWic() {
    if (factory) { factory->Release(); factory = nullptr; }
}

template <class T> struct Com {
    T* p = nullptr;
    ~Com() { if (p) p->Release(); }
    T** operator&() { return &p; }
    T* operator->() { return p; }
};

static bool DecodePng(const uint8_t* data, size_t size, Image& img) {
    auto f = Wic(); if (!f) return false;
    Com<IStream> s; s.p = SHCreateMemStream(data, static_cast<UINT>(size));
    Com<IWICBitmapDecoder> dec; Com<IWICBitmapFrameDecode> frame; Com<IWICFormatConverter> conv;
    if (!s.p || FAILED(f->CreateDecoderFromStream(s.p, nullptr, WICDecodeMetadataCacheOnDemand, &dec)) ||
        FAILED(dec->GetFrame(0, &frame)) || FAILED(f->CreateFormatConverter(&conv)) ||
        FAILED(conv->Initialize(frame.p, GUID_WICPixelFormat32bppBGRA, WICBitmapDitherTypeNone, nullptr, 0,
                                WICBitmapPaletteTypeCustom)) ||
        FAILED(conv->GetSize(&img.w, &img.h)) || !img.w || !img.h || img.w > 16384 || img.h > 16384) return false;
    img.bgra.resize(size_t(img.w) * img.h * 4);
    return SUCCEEDED(conv->CopyPixels(nullptr, img.w * 4, static_cast<UINT>(img.bgra.size()), img.bgra.data()));
}

static bool EncodePng(const Image& img, std::vector<uint8_t>& out) {
    auto f = Wic(); if (!f) return false;
    Com<IStream> s; Com<IWICBitmapEncoder> enc; Com<IWICBitmapFrameEncode> frame; Com<IPropertyBag2> props;
    if (FAILED(CreateStreamOnHGlobal(nullptr, TRUE, &s)) ||
        FAILED(f->CreateEncoder(GUID_ContainerFormatPng, nullptr, &enc)) ||
        FAILED(enc->Initialize(s.p, WICBitmapEncoderNoCache)) ||
        FAILED(enc->CreateNewFrame(&frame, &props)) || FAILED(frame->Initialize(props.p)) ||
        FAILED(frame->SetSize(img.w, img.h))) return false;
    WICPixelFormatGUID fmt = GUID_WICPixelFormat32bppBGRA;
    if (FAILED(frame->SetPixelFormat(&fmt)) || fmt != GUID_WICPixelFormat32bppBGRA ||
        FAILED(frame->WritePixels(img.h, img.w * 4, static_cast<UINT>(img.bgra.size()),
                                  const_cast<BYTE*>(img.bgra.data()))) ||
        FAILED(frame->Commit()) || FAILED(enc->Commit())) return false;
    STATSTG st; HGLOBAL hg;
    if (FAILED(s->Stat(&st, STATFLAG_NONAME)) || FAILED(GetHGlobalFromStream(s.p, &hg))) return false;
    auto p = static_cast<uint8_t*>(GlobalLock(hg));
    if (!p) return false;
    out.assign(p, p + st.cbSize.LowPart);
    GlobalUnlock(hg);
    return true;
}

// ---------------------------------------------------------------- fonty

struct Recipe { std::string font; uint16_t code, base; int dx, extraW, extraShift, height; std::vector<std::pair<int, int>> marks; };

static std::vector<Recipe> LoadRecipes(const std::wstring& path) {
    std::vector<Recipe> out;
    std::ifstream in(path, std::ios::binary);
    std::string line;
    while (std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty()) continue;
        std::istringstream f(line);
        Recipe r; std::string marks;
        int code, base;
        std::getline(f, r.font, '\t');
        f >> code >> base >> r.dx >> r.extraW >> r.extraShift >> r.height;
        std::getline(f >> std::ws, marks);
        std::istringstream m(marks);
        for (std::string xy; m >> xy;) {
            size_t c = xy.find(',');
            r.marks.push_back({std::stoi(xy.substr(0, c)), std::stoi(xy.substr(c + 1))});
        }
        r.code = static_cast<uint16_t>(code); r.base = static_cast<uint16_t>(base);
        out.push_back(r);
    }
    return out;
}

#pragma pack(push, 1)
struct Glyph { uint16_t code, x, y, w, h; int16_t shift, offset; uint16_t kerning; };
struct Tpag { uint16_t sx, sy, sw, sh, tx, ty, tw, th, bw, bh, tex; };
#pragma pack(pop)
static_assert(sizeof(Glyph) == 16 && sizeof(Tpag) == 22, "GameMaker 1.4 layout");

struct Page { uint32_t entry = 0; Image img; bool dirty = false; };

struct FontPlan { uint32_t listSlot; uint8_t* structure; std::string name; size_t added; };

// Texture page decoded once, shared by fonts and labels.
static Page* LoadPage(Form& form, uint16_t tex, std::map<uint16_t, Page>& pages) {
    auto textureList = form.List("TXTR");
    if (tex >= textureList.size()) return nullptr;
    Page& page = pages[tex];
    if (page.img.bgra.empty()) {
        page.entry = textureList[tex];
        uint32_t png = form.U32(page.entry + 4);
        const uint8_t* start = form.base + png;
        const uint8_t* end = form.base + form.size;
        const uint8_t* iend = std::search(start, end, "IEND", "IEND" + 4);
        if (iend == end || !DecodePng(start, (iend + 8) - start, page.img)) { pages.erase(tex); return nullptr; }
    }
    return &page;
}

// Prepares new fonts (no write to the buffer). Returns false = change nothing.
static bool PrepareFonts(Form& form, const std::vector<Recipe>& recipes, std::map<uint16_t, Page>& pages,
                         std::vector<FontPlan>& plans) {
    auto fontList = form.List("FONT");
    uint32_t fontListStart = form.Chunk("FONT").first + 4;
    for (size_t fi = 0; fi < fontList.size(); ++fi) {
        uint32_t f = fontList[fi];
        std::string name = form.Str(form.U32(f));
        std::vector<const Recipe*> mine;
        for (auto& r : recipes) if (r.font == name) mine.push_back(&r);
        if (mine.empty()) continue;

        Tpag tp = form.Get<Tpag>(form.U32(f + 0x1c));
        Page* loaded = LoadPage(form, tp.tex, pages);
        if (!loaded) { Log("Font %s: texture page %u unavailable", name.c_str(), tp.tex); return false; }
        Page& page = *loaded;
        Image& img = page.img;
        if (UINT(tp.sx) + tp.sw > img.w || UINT(tp.sy) + tp.sh > img.h) { Log("Font %s: rect outside page", name.c_str()); return false; }

        uint32_t count = form.U32(f + 0x28);
        std::map<uint16_t, uint32_t> glyphs;              // char -> glyph structure offset
        int freeTop = 0;
        for (uint32_t i = 0; i < count; ++i) {
            uint32_t g = form.U32(f + 0x2c + 4 * i);
            Glyph gl = form.Get<Glyph>(g);
            glyphs[gl.code] = g;
            freeTop = std::max<int>(freeTop, gl.y + gl.h);
        }
        auto px = [&](int x, int y) { return &img.bgra[(size_t(tp.sy + y) * img.w + tp.sx + x) * 4]; };

        // New cells: rows in free space below the glyphs, inside the font rect,
        // 1 px apart (fontSmall has only 28 free rows below its glyphs).
        int cx = 1, cy = freeTop + 1, rowH = 0;
        std::map<uint16_t, uint8_t*> added;
        for (auto r : mine) {
            auto b = glyphs.find(r->base);
            if (b == glyphs.end()) { Log("Font %s: base U+%04X missing", name.c_str(), r->base); return false; }
            Glyph base = form.Get<Glyph>(b->second);
            int w = base.w + r->extraW, h = r->height ? r->height : base.h;
            if (cx + w > tp.sw) { cx = 1; cy += rowH + 1; rowH = 0; }
            if (cy + h > tp.sh || w <= 0 || h <= 0) { Log("Font %s: no room for U+%04X", name.c_str(), r->code); return false; }
            // The cell and its border (within the font rect) must be empty.
            for (int y = std::max(-1, -cy); y <= h && cy + y < tp.sh; ++y)
                for (int x = std::max(-1, -cx); x <= w && cx + x < tp.sw; ++x)
                    if (px(cx + x, cy + y)[3] != 0) { Log("Font %s: target area not empty", name.c_str()); return false; }
            for (int y = 0; y < std::min<int>(h, base.h); ++y)
                for (int x = 0; x < base.w; ++x)
                    if (x + r->dx < w) memcpy(px(cx + x + r->dx, cy + y), px(base.x + x, base.y + y), 4);
            for (auto& m : r->marks) {
                if (m.first < 0 || m.first >= w || m.second < 0 || m.second >= h) {
                    Log("Font %s: mark outside U+%04X", name.c_str(), r->code); return false;
                }
                uint8_t* q = px(cx + m.first, cy + m.second);
                q[0] = q[1] = q[2] = q[3] = 255;
            }
            auto g = reinterpret_cast<Glyph*>(Keep(sizeof(Glyph)));
            *g = {r->code, uint16_t(cx), uint16_t(cy), uint16_t(w), uint16_t(h),
                  int16_t(base.shift + r->extraShift), base.offset, 0};
            added[r->code] = reinterpret_cast<uint8_t*>(g);
            cx += w + 1; rowH = std::max(rowH, h);
        }
        page.dirty = true;

        // New font structure: header as in the original, glyph list sorted by char
        // (the runner binary-searches), our letters replace existing ones with the same code.
        std::vector<uint32_t> list;
        std::set<uint16_t> codes;
        for (auto& [code, off] : glyphs) if (!added.count(code)) { list.push_back(off); codes.insert(code); }
        for (auto& [code, ptr] : added) { list.push_back(form.Offset(ptr)); codes.insert(code); }
        std::sort(list.begin(), list.end(), [&](uint32_t a, uint32_t b) {
            return *reinterpret_cast<const uint16_t*>(form.At(a)) < *reinterpret_cast<const uint16_t*>(form.At(b));
        });
        uint8_t* fs = Keep(0x2c + 4 * list.size());
        memcpy(fs, form.base + f, 0x2c);
        uint32_t n = static_cast<uint32_t>(list.size()), last = *codes.rbegin();
        memcpy(fs + 0x28, &n, 4);
        uint32_t oldLast; memcpy(&oldLast, fs + 0x18, 4);
        if (last > oldLast) memcpy(fs + 0x18, &last, 4);
        memcpy(fs + 0x2c, list.data(), 4 * list.size());
        plans.push_back({fontListStart + 4 * static_cast<uint32_t>(fi), fs, name, added.size()});
    }
    return !plans.empty();
}

// ---------------------------------------------------------------- labels on graphics

// Recipe from labels.txt. Group = erase/fill + the masks after it; a group draws only when the
// old text's pixel count matches the build (a different graphic in a new game version = stays EN).
struct LabelOp {
    std::string kind, sprite;
    int frame = 0, x0 = 0, y0 = 0, x1 = 0, y1 = 0, tol = 0, w = 0, h = 0;
    long expected = -1;
    uint8_t color[4] = {};                        // RGBA
    std::vector<std::array<uint8_t, 4>> inks;
    std::string bits;
};

static bool ParseColor(const std::string& hex, uint8_t out[4]) {
    if (hex.size() != 6 && hex.size() != 8) return false;
    for (size_t i = 0; i < hex.size() / 2; ++i) out[i] = static_cast<uint8_t>(std::stoi(hex.substr(i * 2, 2), nullptr, 16));
    if (hex.size() == 6) out[3] = 255;
    return true;
}

static std::vector<LabelOp> LoadLabels(const std::wstring& path) {
    std::vector<LabelOp> ops;
    std::ifstream in(path, std::ios::binary);
    std::string line;
    while (std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        std::vector<std::string> f;
        size_t start = 0;
        for (size_t tab; (tab = line.find('\t', start)) != std::string::npos; start = tab + 1) f.push_back(line.substr(start, tab - start));
        f.push_back(line.substr(start));
        if (f.size() < 8) continue;
        LabelOp op;
        op.kind = f[0]; op.sprite = f[1]; op.frame = std::stoi(f[2]);
        op.x0 = std::stoi(f[3]); op.y0 = std::stoi(f[4]);
        if (op.kind == "erase" && f.size() >= 11) {
            op.x1 = std::stoi(f[5]); op.y1 = std::stoi(f[6]);
            if (!ParseColor(f[7], op.color)) continue;
            std::istringstream inks(f[8]);
            for (std::string ink; std::getline(inks, ink, ',');) {
                std::array<uint8_t, 4> c{}; if (ParseColor(ink, c.data())) op.inks.push_back(c);
            }
            op.tol = std::stoi(f[9]); op.expected = std::stol(f[10]);
        } else if (op.kind == "fill" && f.size() >= 9) {
            op.x1 = std::stoi(f[5]); op.y1 = std::stoi(f[6]);
            if (!ParseColor(f[7], op.color)) continue;
            op.expected = std::stol(f[8]);
        } else if (op.kind == "mask" && f.size() >= 9) {
            op.w = std::stoi(f[5]); op.h = std::stoi(f[6]);
            if (!ParseColor(f[7], op.color)) continue;
            op.bits = f[8];
        } else continue;
        ops.push_back(op);
    }
    return ops;
}

// Sprite frame by name: SPRT -> structure (name +0, frame count +0x38, TPAG list from +0x3C).
static bool FindFrame(Form& form, const std::string& sprite, int frame, Tpag& tp) {
    for (uint32_t p : form.List("SPRT")) {
        if (form.Str(form.U32(p)) != sprite) continue;
        uint32_t count = form.U32(p + 0x38);
        if (frame < 0 || uint32_t(frame) >= count) return false;
        tp = form.Get<Tpag>(form.U32(p + 0x3C + 4 * frame));
        return true;
    }
    return false;
}

static size_t ApplyLabels(Form& form, const std::vector<LabelOp>& ops, std::map<uint16_t, Page>& pages) {
    size_t groups = 0, skipped = 0;
    bool active = false;
    Page* page = nullptr; Tpag tp{};
    auto at = [&](int x, int y) { return &page->img.bgra[(size_t(tp.sy + y) * page->img.w + tp.sx + x) * 4]; };
    auto inside = [&](int x0, int y0, int x1, int y1) {
        return x0 >= 0 && y0 >= 0 && x1 < tp.sw && y1 < tp.sh && x0 <= x1 && y0 <= y1;
    };
    auto put = [](uint8_t* q, const uint8_t c[4]) { q[0] = c[2]; q[1] = c[1]; q[2] = c[0]; q[3] = c[3]; };
    for (auto& op : ops) {
        if (op.kind == "erase" || op.kind == "fill") {
            active = false;
            if (!FindFrame(form, op.sprite, op.frame, tp) || !(page = LoadPage(form, tp.tex, pages)) ||
                UINT(tp.sx) + tp.sw > page->img.w || UINT(tp.sy) + tp.sh > page->img.h || !inside(op.x0, op.y0, op.x1, op.y1)) {
                Log("Label %s/%d: frame not found or out of range: stays English", op.sprite.c_str(), op.frame);
                ++skipped; continue;
            }
            long count = 0;
            for (int y = op.y0; y <= op.y1; ++y)
                for (int x = op.x0; x <= op.x1; ++x) {
                    const uint8_t* q = at(x, y);
                    if (op.kind == "fill") { count += q[3] == 0; continue; }
                    if (!q[3]) continue;
                    for (auto& ink : op.inks)
                        if (abs(q[2] - ink[0]) + abs(q[1] - ink[1]) + abs(q[0] - ink[2]) <= op.tol) { ++count; break; }
                }
            if (labs(count - op.expected) > std::max(3L, op.expected / 10)) {
                Log("Label %s/%d: %ld pixels of old text, expected %ld: stays English", op.sprite.c_str(), op.frame, count, op.expected);
                ++skipped; continue;
            }
            for (int y = op.y0; y <= op.y1; ++y)
                for (int x = op.x0; x <= op.x1; ++x) {
                    uint8_t* q = at(x, y);
                    if (op.kind == "fill") { put(q, op.color); continue; }
                    if (!q[3]) continue;
                    for (auto& ink : op.inks)
                        if (abs(q[2] - ink[0]) + abs(q[1] - ink[1]) + abs(q[0] - ink[2]) <= op.tol) { put(q, op.color); break; }
                }
            page->dirty = true;
            active = true; ++groups;
        } else if (op.kind == "mask" && active) {
            if (!inside(op.x0, op.y0, op.x0 + op.w - 1, op.y0 + op.h - 1) ||
                op.bits.size() != size_t(op.w) * op.h + op.h - 1) {
                Log("Label %s/%d: mask out of range", op.sprite.c_str(), op.frame); continue;
            }
            for (int y = 0; y < op.h; ++y)
                for (int x = 0; x < op.w; ++x)
                    if (op.bits[size_t(y) * (op.w + 1) + x] == '1') put(at(op.x0 + x, op.y0 + y), op.color);
        }
    }
    Log("Labels: %zu drawn, %zu left in English", groups, skipped);
    return groups;
}

// ---------------------------------------------------------------- bytecode 15

struct CodeEntry { std::string name; uint32_t start, length; };

static std::vector<CodeEntry> CodeEntries(Form& form) {
    std::vector<CodeEntry> out;
    for (uint32_t p : form.List("CODE")) {
        CodeEntry e{form.Str(form.U32(p)), 0, form.U32(p + 4)};
        e.start = static_cast<uint32_t>(p + 12 + form.I32(p + 12));
        if (e.start >= form.size || e.length > form.size - e.start) throw std::runtime_error("bad CODE entry");
        out.push_back(e);
    }
    return out;
}

// Calls fn(operand offset, STRG index) for every push.s in the entry.
template <class F> static void ForEachPushString(Form& form, const CodeEntry& e, F fn) {
    for (uint32_t o = e.start, end = e.start + e.length; o < end;) {
        uint32_t word = form.U32(o), op = word >> 24, size = 4;
        if (op == 0xC0 || op == 0xC1 || op == 0xC2 || op == 0xC3 || op == 0x84) {
            uint32_t t = (word >> 16) & 0xF;
            size += t == 0 || t == 3 ? 8 : t == 15 ? 0 : 4;
            if (op == 0xC0 && t == 6) fn(o + 4, form.U32(o + 4));
        } else if (op == 0xD9 || op == 0x45) size = 8;
        o += size;
    }
}

// ---------------------------------------------------------------- JSON

static std::unordered_map<std::string, std::string> jsonRows;
static std::map<std::wstring, std::wstring> redirects;      // file name (lower-case) -> path in cache

static std::string JsonUnescape(const std::string& s, bool& ok) {
    std::string out; ok = true;
    for (size_t i = 0; i < s.size(); ++i) {
        if (s[i] != '\\') { out += s[i]; continue; }
        if (++i >= s.size()) { ok = false; break; }
        switch (s[i]) {
            case '"': out += '"'; break;  case '\\': out += '\\'; break; case '/': out += '/'; break;
            case 'n': out += '\n'; break; case 't': out += '\t'; break;  case 'r': out += '\r'; break;
            default: ok = false;
        }
    }
    return out;
}

static std::string JsonEscape(const std::string& s) {
    std::string out;
    for (char c : s) {
        if (c == '"' || c == '\\') out += '\\';
        if (c == '\n') { out += "\\n"; continue; }
        out += c;
    }
    return out;
}

static std::string TranslateJson(const std::string& text, size_t& done, size_t& missing) {
    std::string out;
    for (size_t i = 0; i < text.size();) {
        if (text[i] != '"') { out += text[i++]; continue; }
        size_t j = i + 1;
        while (j < text.size() && text[j] != '"') j += text[j] == '\\' ? 2 : 1;
        if (j >= text.size()) { out += text.substr(i); break; }
        std::string raw = text.substr(i + 1, j - i - 1);
        size_t k = j + 1;
        while (k < text.size() && isspace(static_cast<unsigned char>(text[k]))) ++k;
        bool isKey = k < text.size() && text[k] == ':';
        bool ok; std::string value = JsonUnescape(raw, ok);
        auto it = ok && !isKey ? jsonRows.find(value) : jsonRows.end();
        if (it != jsonRows.end()) { out += '"' + JsonEscape(it->second) + '"'; ++done; }
        else {
            out += text.substr(i, j - i + 1);
            if (!isKey && value.find(' ') != std::string::npos) ++missing;
        }
        i = j + 1;
    }
    return out;
}

static bool PrepareJson() {
    std::wstring cache = root + L"notgeese\\cache\\";
    CreateDirectoryW((root + L"notgeese").c_str(), nullptr);
    CreateDirectoryW(cache.c_str(), nullptr);
    WIN32_FIND_DATAW fd;
    HANDLE h = FindFirstFileW((root + L"dia_*.json").c_str(), &fd);
    if (h == INVALID_HANDLE_VALUE) { Log("No dia_*.json next to the game"); return true; }
    do {
        std::wstring name = fd.cFileName;
        std::vector<uint8_t> bytes;
        if (!ReadFileBytes(root + name, bytes)) continue;
        size_t done = 0, missing = 0;
        std::string out = TranslateJson(std::string(bytes.begin(), bytes.end()), done, missing);
        std::wstring target = cache + name;
        std::ofstream f(target, std::ios::binary | std::ios::trunc);
        f.write(out.data(), out.size());
        if (!f) { Log("Cannot write %s: dialogue stays English", Utf8(target).c_str()); continue; }
        std::wstring key = name; CharLowerW(&key[0]);
        redirects[key] = target;
        Log("%s: %zu strings translated, %zu untranslated", Utf8(name).c_str(), done, missing);
    } while (FindNextFileW(h, &fd));
    FindClose(h);
    return true;
}

using CreateFileW_t = HANDLE(WINAPI*)(LPCWSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
using CreateFileA_t = HANDLE(WINAPI*)(LPCSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
static CreateFileW_t originalCreateFileW;
static CreateFileA_t originalCreateFileA;

static const std::wstring* Redirect(const std::wstring& path, DWORD access, DWORD disposition) {
    if ((access & (GENERIC_WRITE | FILE_WRITE_DATA | FILE_APPEND_DATA)) || disposition != OPEN_EXISTING) return nullptr;
    size_t slash = path.find_last_of(L"\\/");
    std::wstring name = path.substr(slash == std::wstring::npos ? 0 : slash + 1);
    if (name.empty()) return nullptr;
    CharLowerW(&name[0]);
    auto it = redirects.find(name);
    return it == redirects.end() ? nullptr : &it->second;
}

static HANDLE WINAPI OnCreateFileW(LPCWSTR path, DWORD access, DWORD share, LPSECURITY_ATTRIBUTES sa,
                                   DWORD disposition, DWORD flags, HANDLE templ) {
    if (path) {
        if (auto target = Redirect(path, access, disposition))
            return originalCreateFileW(target->c_str(), access, share, sa, disposition, flags, templ);
    }
    return originalCreateFileW(path, access, share, sa, disposition, flags, templ);
}

static HANDLE WINAPI OnCreateFileA(LPCSTR path, DWORD access, DWORD share, LPSECURITY_ATTRIBUTES sa,
                                   DWORD disposition, DWORD flags, HANDLE templ) {
    if (path) {
        int n = MultiByteToWideChar(CP_ACP, 0, path, -1, nullptr, 0);
        std::wstring wide(n > 0 ? n - 1 : 0, L'\0');
        if (n > 1) MultiByteToWideChar(CP_ACP, 0, path, -1, &wide[0], n);
        if (auto target = Redirect(wide, access, disposition))
            return originalCreateFileW(target->c_str(), access, share, sa, disposition, flags, templ);
    }
    return originalCreateFileA(path, access, share, sa, disposition, flags, templ);
}

// ---------------------------------------------------------------- start

static void LogVersions(Form* form) {
    wchar_t exe[MAX_PATH] = {}; GetModuleFileNameW(nullptr, exe, MAX_PATH);
    DWORD unused = 0, size = GetFileVersionInfoSizeW(exe, &unused);
    std::vector<BYTE> data(size); VS_FIXEDFILEINFO* info = nullptr; UINT bytes = 0;
    if (size && GetFileVersionInfoW(exe, 0, size, data.data()) &&
        VerQueryValueW(data.data(), L"\\", reinterpret_cast<void**>(&info), &bytes))
        Log("Game EXE %s, PE version %u.%u.%u.%u", Utf8(exe).c_str(), HIWORD(info->dwFileVersionMS),
            LOWORD(info->dwFileVersionMS), HIWORD(info->dwFileVersionLS), LOWORD(info->dwFileVersionLS));
    if (form) {
        uint32_t g = form->Chunk("GEN8").first;
        Log("GEN8: %s, bytecode %u, version %u.%u.%u.%u", form->Str(form->U32(g + 0x28)).c_str(),
            form->base[g + 1], form->U32(g + 0x2c), form->U32(g + 0x30), form->U32(g + 0x34), form->U32(g + 0x38));
    }
}

static void Init() {
    wchar_t path[MAX_PATH] = {};
    GetModuleFileNameW(selfModule, path, MAX_PATH);
    root = path; root.resize(root.find_last_of(L"\\/") + 1);
    CreateDirectoryW((root + L"notgeese").c_str(), nullptr);
    logfile = _wfsopen((root + L"notgeese\\LogOutput.log").c_str(), L"w", _SH_DENYNO);
    Log("notgeese DEADBOLT PL %s; GameMaker Studio 1.4 VM; data.win patched in memory", kVersion);
    auto started = std::chrono::steady_clock::now();

    auto rows = LoadRows(root + L"notgeese\\pl.tsv");
    auto recipes = LoadRecipes(root + L"notgeese\\fonts.txt");
    if (rows.empty() || recipes.empty()) { LogVersions(nullptr); Log("Missing pl.tsv or fonts.txt: disabled"); return; }

    std::vector<uint8_t> file;
    if (!ReadFileBytes(root + L"data.win", file) || file.size() < 16) {
        LogVersions(nullptr); Log("Cannot read data.win next to the plugin: disabled"); return;
    }
    Form form;
    if (!FindForm(file, form)) { LogVersions(nullptr); return; }
    LogVersions(&form);
    // Code is read from the file on disk: the runner rewrites CODE before Direct3DCreate9
    // (70 616 bytes differ in game), and instruction offsets are the same in both copies.
    Form disk = form;
    disk.base = file.data();

    // 1. Fonts: preparation (no write).
    HRESULT com = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    std::map<uint16_t, Page> pages;
    std::vector<FontPlan> fonts;
    bool fontsOk = PrepareFonts(form, recipes, pages, fonts);
    // Labels on graphics (main menu, tutorial, mission select): only together with fonts.
    if (fontsOk) ApplyLabels(form, LoadLabels(root + L"notgeese\\labels.txt"), pages);
    std::map<uint32_t, std::vector<uint8_t>> encoded;      // TXTR entry -> new PNG
    if (fontsOk) {
        for (auto& [index, page] : pages) {
            if (!page.dirty) continue;
            if (!EncodePng(page.img, encoded[page.entry])) { Log("Texture page %u encode failed", index); fontsOk = false; break; }
        }
    }
    ReleaseWic();
    if (SUCCEEDED(com)) CoUninitialize();
    if (!fontsOk) { Log("Polish fonts unavailable: game stays English"); return; }

    // 2. Napisy — przygotowanie.
    auto strg = form.List("STRG");
    uint32_t strgList = form.Chunk("STRG").first + 4;
    std::unordered_map<std::string, std::vector<uint32_t>> byText;
    for (uint32_t i = 0; i < strg.size(); ++i) byText[form.Str(strg[i] + 4)].push_back(i);
    auto code = CodeEntries(disk);
    std::set<uint32_t> pushed;
    for (auto& e : code) ForEachPushString(disk, e, [&](uint32_t, uint32_t idx) { pushed.insert(idx); });
    std::vector<uint32_t> spare;
    // Free slots (strings the code never pushes: asset names) are taken from the list's end.
    for (uint32_t i = static_cast<uint32_t>(strg.size()); i-- > 1;) if (!pushed.count(i)) spare.push_back(i);
    std::map<std::string, const CodeEntry*> codeByName;
    for (auto& e : code) codeByName[e.name] = &e;

    std::vector<std::pair<uint32_t, uint32_t>> writes;     // (offset in buffer, new value)
    size_t stringRows = 0, stringMissing = 0, codeRows = 0, codeMissing = 0;
    size_t nextSpare = 0;
    auto store = [&](const std::string& text) {
        uint8_t* p = Keep(4 + text.size() + 1);
        uint32_t len = static_cast<uint32_t>(text.size());
        memcpy(p, &len, 4); memcpy(p + 4, text.data(), text.size()); p[4 + text.size()] = 0;
        return form.Offset(p);
    };
    for (auto& r : rows) {
        if (r.kind == "j") { jsonRows[r.en] = r.pl; continue; }
        auto it = byText.find(r.en);
        if (r.kind == "s") {
            if (it == byText.end()) { if (++stringMissing <= 5) Log("Not in STRG: %s", r.en.c_str()); continue; }
            uint32_t off = store(r.pl);
            for (uint32_t idx : it->second) writes.push_back({strgList + 4 * idx, off});
            ++stringRows;
        } else if (r.kind == "c") {
            auto ce = codeByName.find(r.context);
            if (it == byText.end() || ce == codeByName.end() || nextSpare >= spare.size()) {
                if (++codeMissing <= 5) Log("Code-scoped row not applied: %s @ %s", r.en.c_str(), r.context.c_str());
                continue;
            }
            std::set<uint32_t> want(it->second.begin(), it->second.end());
            uint32_t slot = spare[nextSpare++];
            size_t hits = 0;
            ForEachPushString(disk, *ce->second, [&](uint32_t operand, uint32_t idx) {
                // The operand in the game buffer must still point at the same string as in the file.
                if (want.count(idx) && form.U32(operand) == idx) { writes.push_back({operand, slot}); ++hits; }
            });
            if (!hits) { if (++codeMissing <= 5) Log("No push of \"%s\" in %s", r.en.c_str(), r.context.c_str()); continue; }
            writes.push_back({strgList + 4 * slot, store(r.pl)});
            ++codeRows;
        }
    }
    Log("Strings: %zu rows matched, %zu missing; code-scoped: %zu applied, %zu missing; %zu spare slots",
        stringRows, stringMissing, codeRows, codeMissing, spare.size());
    file.clear(); file.shrink_to_fit();

    // 3. Write to the buffer, only when everything is ready.
    for (auto& f : fonts) {
        form.Put32(f.listSlot, form.Offset(f.structure));
        Log("Font %s: %zu Polish glyphs", f.name.c_str(), f.added);
    }
    for (auto& [entry, png] : encoded) {
        uint8_t* p = Keep(png.size());
        memcpy(p, png.data(), png.size());
        form.Put32(entry + 4, form.Offset(p));
        Log("Texture page entry %08x re-encoded: %zu bytes", entry, png.size());
    }
    for (auto& [off, value] : writes) form.Put32(off, value);

    // 4. Dialogi JSON.
    PrepareJson();
    if (!redirects.empty()) {
        auto kernel = GetModuleHandleW(L"kernel32.dll");
        auto w = reinterpret_cast<void*>(GetProcAddress(kernel, "CreateFileW"));
        auto a = reinterpret_cast<void*>(GetProcAddress(kernel, "CreateFileA"));
        if (MH_Initialize() != MH_OK ||
            MH_CreateHook(w, reinterpret_cast<void*>(OnCreateFileW), reinterpret_cast<void**>(&originalCreateFileW)) != MH_OK ||
            MH_CreateHook(a, reinterpret_cast<void*>(OnCreateFileA), reinterpret_cast<void**>(&originalCreateFileA)) != MH_OK ||
            MH_EnableHook(MH_ALL_HOOKS) != MH_OK) {
            MH_Uninitialize(); redirects.clear();
            Log("File hooks failed: dialogues stay English");
        }
    }
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - started).count();
    Log("Ready in %lld ms. Untranslated lines stay English.", static_cast<long long>(ms));
}

extern "C" FARPROC __cdecl Resolve(const char* name) {
    static HMODULE real = [] {
        wchar_t path[MAX_PATH] = {}; GetSystemDirectoryW(path, MAX_PATH);
        wcscat_s(path, L"\\d3d9.dll"); return LoadLibraryW(path);
    }();
    static bool attempted = false;
    if (!attempted && (!strcmp(name, "Direct3DCreate9") || !strcmp(name, "Direct3DCreate9Ex"))) {
        attempted = true;
        try { Init(); }
        catch (const std::exception& e) { Log("Initialization error (%s): game stays English", e.what()); }
        catch (...) { Log("Initialization exception: game stays English"); }
    }
    return real ? GetProcAddress(real, name) : nullptr;
}

BOOL WINAPI DllMain(HMODULE module, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) { selfModule = module; DisableThreadLibraryCalls(module); }
    return TRUE;
}
