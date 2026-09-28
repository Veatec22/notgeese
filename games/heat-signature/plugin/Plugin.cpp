// Native GameMaker 1.4 YYC localization probe. No fixed game addresses or hashes.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <cstdint>
#include <cstdio>
#include <share.h>
#include <cmath>
#include <cstdarg>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <algorithm>
#include "MinHook.h"
#include "Translate.h"

static HMODULE selfModule;
static std::wstring root;
static FILE* logfile;
static void Log(const char* fmt, ...) {
    if (!logfile) return;
    va_list args; va_start(args, fmt); vfprintf(logfile, fmt, args); va_end(args);
    fputc('\n', logfile); fflush(logfile);
}

struct YYString { const char* text; uint32_t refs, length; };
struct Value { union { double real; int32_t integer; YYString* str; }; uint32_t flags, type; };
static_assert(sizeof(Value) == 16, "x86 GameMaker value ABI");
using Builtin = void (__cdecl*)(Value*, void*, void*, int, Value*);
using SetFont = void (__cdecl*)(int);
using Split = void (__cdecl*)(const char*, int, void*);
static Builtin addFont, addSprite, spriteFrames, textWidth, textHeight;
using GetFont = BYTE* (__cdecl*)(int);
static GetFont getFont;
static SetFont originalSetFont;
static Split originalSplit;
struct Font { int size, bold, italic, replacement = -1; };
static std::vector<Font> fonts;
static bool fontsReady = false, fontsAttempted = false;
static tr::Engine engine;

struct Image {
    BYTE* base = reinterpret_cast<BYTE*>(GetModuleHandleW(nullptr));
    IMAGE_NT_HEADERS* nt = reinterpret_cast<IMAGE_NT_HEADERS*>(base + reinterpret_cast<IMAGE_DOS_HEADER*>(base)->e_lfanew);
    bool Contains(const void* p, size_t n = 1) const {
        auto v = reinterpret_cast<uintptr_t>(p), b = reinterpret_cast<uintptr_t>(base);
        return v >= b && n <= nt->OptionalHeader.SizeOfImage && v - b <= nt->OptionalHeader.SizeOfImage - n;
    }
    bool Executable(const void* p) const {
        auto s = IMAGE_FIRST_SECTION(nt);
        for (unsigned i=0; i<nt->FileHeader.NumberOfSections; ++i, ++s)
            if (p >= base+s->VirtualAddress && p < base+s->VirtualAddress+s->Misc.VirtualSize)
                return (s->Characteristics & IMAGE_SCN_MEM_EXECUTE) != 0;
        return false;
    }
    std::vector<BYTE*> Find(const void* data, size_t count, bool code) const {
        std::vector<BYTE*> result;
        auto s=IMAGE_FIRST_SECTION(nt);
        for (unsigned i=0; i<nt->FileHeader.NumberOfSections; ++i, ++s) {
            if (!(s->Characteristics & IMAGE_SCN_MEM_READ) || bool(s->Characteristics & IMAGE_SCN_MEM_EXECUTE)!=code) continue;
            size_t size=std::min(s->Misc.VirtualSize, s->SizeOfRawData);
            for (size_t j=0; j+count<=size; ++j)
                if (!memcmp(base+s->VirtualAddress+j,data,count)) result.push_back(base+s->VirtualAddress+j);
        }
        return result;
    }
    BYTE* BuiltinByName(const char* name) const {
        std::set<BYTE*> matches;
        for (BYTE* text:Find(name,strlen(name)+1,false)) {
            uint32_t pointer=reinterpret_cast<uint32_t>(text);
            for (BYTE* ref:Find(&pointer,4,true)) {
                // Registration: push builtin; push its name; call registrar.
                if (!Contains(ref-6,15) || ref[-6]!=0x68 || ref[-1]!=0x68 || ref[4]!=0xe8) continue;
                BYTE* target=*reinterpret_cast<BYTE**>(ref-5);
                if (Executable(target)) matches.insert(target);
            }
        }
        return matches.size()==1 ? *matches.begin() : nullptr;
    }
    BYTE* RelativeCall(BYTE* p) const {
        if (!Contains(p,5) || *p!=0xe8) return nullptr;
        BYTE* q=p+5+*reinterpret_cast<int32_t*>(p+1);
        return Executable(q) ? q : nullptr;
    }
};

static bool Match(BYTE* p, const std::initializer_list<int>& bytes) {
    for (int b: bytes) { if (b>=0 && *p!=b) return false; ++p; } return true;
}

static bool ReadFonts(const Image& image) {
    for (BYTE* base:image.Find("FORM",4,false)) {
        if (!image.Contains(base,16) || memcmp(base+8,"GEN8",4)) continue;
        uint32_t length=*reinterpret_cast<uint32_t*>(base+4);
        if (!image.Contains(base,size_t(length)+8)) continue;
        BYTE* end=base+8+length;
        for (BYTE* chunk=base+8; chunk+8<=end;) {
            uint32_t size=*reinterpret_cast<uint32_t*>(chunk+4);
            if (size>size_t(end-chunk-8)) break;
            if (!memcmp(chunk,"FONT",4) && size>=4) {
                BYTE* entries=chunk+8; uint32_t count=*reinterpret_cast<uint32_t*>(entries);
                if (!count || count>128 || 4+count*4>size) return false;
                for (unsigned i=0;i<count;++i) {
                    uint32_t offset=*reinterpret_cast<uint32_t*>(entries+4+i*4);
                    if (offset>length || length-offset<44) return false;
                    auto f=reinterpret_cast<uint32_t*>(base+offset);
                    if (f[2]<1 || f[2]>256 || f[3]>1 || f[4]>1) return false;
                    fonts.push_back({int(f[2]),int(f[3]),int(f[4]),-1});
                }
                Log("Embedded font metadata: %u fonts",count); return true;
            }
            chunk+=8+size;
        }
    }
    return false;
}

static bool Writable(const void* pointer,size_t length) {
    MEMORY_BASIC_INFORMATION page={};
    if(!pointer || !VirtualQuery(pointer,&page,sizeof(page)) || page.State!=MEM_COMMIT ||
       (page.Protect&(PAGE_GUARD|PAGE_NOACCESS)) ||
       !(page.Protect&(PAGE_READWRITE|PAGE_WRITECOPY|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY))) return false;
    auto start=reinterpret_cast<uintptr_t>(pointer),base=reinterpret_cast<uintptr_t>(page.BaseAddress);
    return start>=base && start-base<=page.RegionSize && length<=page.RegionSize-(start-base);
}

static bool ApplyMetrics(int id,int sprite,const std::wstring& path,unsigned count) {
    struct Metric {int code,frame,advance,offset,height;};
    std::ifstream file(path);std::vector<Metric> metrics;Metric m;
    while(file>>m.code>>m.frame>>m.advance>>m.offset>>m.height) metrics.push_back(m);
    if(!file.eof() || metrics.size()!=count) return false;
    BYTE* font=getFont(id);
    if(!Writable(font,0x48) || *reinterpret_cast<int*>(font+0x20)!=sprite ||
       *reinterpret_cast<unsigned*>(font+0x40)!=count) return false;
    auto glyphs=*reinterpret_cast<int16_t***>(font+0x44);
    if(!Writable(glyphs,count*sizeof(void*))) return false;
    std::vector<int16_t*> checked;
    for(unsigned i=0;i<count;++i) {
        const auto& metric=metrics[i];int16_t* found=nullptr;
        if(metric.frame!=int(i) || metric.advance<=0 || metric.advance>512 ||
           metric.offset>0 || metric.offset < -512) return false;
        for(unsigned j=0;j<count;++j) {
            auto glyph=glyphs[j];
            if(!Writable(glyph,16)) return false;
            if(glyph[0]==metric.code) {
                if(found || glyph[3]!=metric.frame || glyph[4]!=metric.height) return false;
                found=glyph;
            }
        }
        if(!found) return false;
        checked.push_back(found);
    }
    // Modify only the font we just created, after validating the entire map.
    // Runtime sprite textures retain full cells, so the runner's proportional
    // constructor cannot infer ink bounds from these texture rectangles.
    for(unsigned i=0;i<count;++i) {
        checked[i][5]=int16_t(metrics[i].advance);
        checked[i][6]=int16_t(metrics[i].offset);
    }
    return true;
}

static bool LoadFonts() {
    if (fontsAttempted) return fontsReady;
    fontsAttempted=true;
    std::ifstream mapFile(root+L"notgeese\\fonts\\charmap.txt",std::ios::binary);
    std::string chars((std::istreambuf_iterator<char>(mapFile)),std::istreambuf_iterator<char>());
    unsigned count=0;
    for(unsigned char c:chars) if((c&0xc0)!=0x80) ++count;
    if(count<113 || count>512) {Log("Missing/invalid font charmap: disabled");return false;}
    YYString charmap={chars.c_str(),1,uint32_t(chars.size())};
    for (size_t i=0;i<fonts.size();++i) {
        auto& font=fonts[i];
        // Reuse identical variants; keep each sprite alive as long as its font.
        for(size_t j=0;j<i;++j) if(fonts[j].size==font.size && fonts[j].bold==font.bold && fonts[j].italic==font.italic)
            font.replacement=fonts[j].replacement;
        if(font.replacement>=0) continue;
        std::wstring path=root+L"notgeese\\fonts\\font-"+std::to_wstring(font.size)+L"-"+
            std::to_wstring(font.bold)+L"-"+std::to_wstring(font.italic)+L".png";
        if(GetFileAttributesW(path.c_str())==INVALID_FILE_ATTRIBUTES) {Log("Missing font variant %zu: disabled",i);return false;}
        int bytes=WideCharToMultiByte(CP_UTF8,0,path.c_str(),-1,nullptr,0,nullptr,nullptr);
        std::string filename(bytes,'\0');
        WideCharToMultiByte(CP_UTF8,0,path.c_str(),-1,&filename[0],bytes,nullptr,nullptr);
        YYString file={filename.c_str(),1,uint32_t(bytes-1)};
        Value args[6]={}, result={};
        args[0].str=&file; args[0].type=1;
        args[1].real=count; // sprite_add: file, frames, removeback, smooth, xorigin, yorigin
        addSprite(&result,nullptr,nullptr,6,args);
        if(result.type!=0 || !std::isfinite(result.real) || result.real<0 || result.real>100000) {
            Log("Sprite creation failed at %zu: disabled",i);return false;
        }
        Value sprite=result, frameCount={};
        spriteFrames(&frameCount,nullptr,nullptr,1,&sprite);
        if(frameCount.type!=0 || frameCount.real!=count) {Log("Sprite frames invalid at %zu: disabled",i);return false;}
        Value fontArgs[4]={}; fontArgs[0]=sprite; fontArgs[1].type=1; fontArgs[1].str=&charmap;
        fontArgs[2].real=1; fontArgs[3].real=std::max(1,font.size/12); // proportional, extra spacing
        addFont(&result,nullptr,nullptr,4,fontArgs);
        if(result.type!=0 || !std::isfinite(result.real) || result.real<0 || result.real>100000) {
            Log("Sprite font creation failed at %zu: disabled",i);return false;
        }
        if(!ApplyMetrics(int(result.real),int(sprite.real),path.substr(0,path.size()-4)+L".metrics",count)) {
            Log("Sprite glyph layout/metrics validation failed at %zu: disabled",i);return false;
        }
        // A nonnegative ID is NOT proof that letters exist: font_add returned
        // valid IDs with zero glyphs in 0.1.0. Measure every character through
        // the runner before any font substitution or translation is enabled.
        originalSetFont(int(result.real));
        double narrow=0,wide=0;
        for(size_t start=0;start<chars.size();) {
            size_t end=start+1;
            while(end<chars.size() && (static_cast<unsigned char>(chars[end])&0xc0)==0x80) ++end;
            std::string glyph=chars.substr(start,end-start);
            // GameMaker treats # as a line break before measuring text.
            if(glyph=="#") {start=end;continue;}
            YYString letter={glyph.c_str(),1,uint32_t(glyph.size())};
            Value arg={}, w={}, h={};arg.type=1;arg.str=&letter;
            textWidth(&w,nullptr,nullptr,1,&arg);textHeight(&h,nullptr,nullptr,1,&arg);
            if(glyph=="i")narrow=w.real;
            if(glyph=="W")wide=w.real;
            if(w.type!=0 || h.type!=0 || !std::isfinite(w.real) || !std::isfinite(h.real) ||
               w.real<=0 || h.real<=0 || w.real>512 || h.real>512) {
                Log("Empty/invalid glyph at font %zu, UTF-8 offset %zu (width %.1f height %.1f): disabled",i,start,w.real,h.real);
                return false;
            }
            start=end;
        }
        if(narrow<=0 || narrow>=wide) {Log("Proportional spacing check failed at font %zu: disabled",i);return false;}
        font.replacement=int(result.real);
        Log("Font %zu -> sprite font %d (%d pt bold=%d italic=%d): %u glyph metrics passed, i=%.1f W=%.1f",i,font.replacement,font.size,font.bold,font.italic,count,narrow,wide);
    }
    fontsReady=true;
    Log("Polish fonts ready; translations enabled");
    return true;
}

static void __cdecl OnSetFont(int id) {
    // Font creation happens on the game thread, after the graphics device exists.
    try {if (id>=0 && size_t(id)<fonts.size() && LoadFonts()) id=fonts[id].replacement;}
    catch(...) {fontsReady=false;fontsAttempted=true;Log("Font loading exception: using original fonts");}
    originalSetFont(id);
}

static std::string Translate(const char* input) {
    if (!strcmp(input,"Resume") && (GetAsyncKeyState(VK_F8)&0x8000))
        return u8"ąćęłńóśźż ĄĆĘŁŃÓŚŹŻ";
    return engine.Translate(input);
}

static void __cdecl OnSplit(const char* text,int width,void* lines) {
    if (!text || !fontsReady) { originalSplit(text,width,lines); return; }
    // The original function copies UTF-8 into its own UTF-16 line buffer.
    // Result survives only the synchronous call; game owns all output allocations.
    std::string translated;
    try { translated=Translate(text); }
    catch (...) { originalSplit(text,width,lines); return; }
    originalSplit(translated.c_str(),width,lines);
}

// Dialogue files: the game reads Dialog\<name>.txt when a conversation starts.
// We hand it a copy under notgeese\cache with only the spoken text translated,
// made from the player's own file, so the letter-by-letter reveal is Polish.
// Any failure opens the original file; no game file is ever written.
using CreateFileWFn = HANDLE (WINAPI*)(LPCWSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
using CreateFileAFn = HANDLE (WINAPI*)(LPCSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
static CreateFileWFn originalCreateFileW;
static CreateFileAFn originalCreateFileA;
static bool inDialogRedirect = false;
static std::map<std::wstring, std::wstring> dialogCopies;

static std::wstring DialogCopy(const std::wstring& requested, DWORD access, DWORD disposition) {
    if (!fontsReady || inDialogRedirect || disposition != OPEN_EXISTING || (access & GENERIC_WRITE)) return L"";
    std::wstring lower = requested;
    for (auto& c : lower) { c = towlower(c); if (c == L'/') c = L'\\'; }
    size_t slash = lower.rfind(L'\\');
    if (slash == std::wstring::npos || lower.size() < 4 || lower.compare(lower.size() - 4, 4, L".txt") != 0) return L"";
    size_t folder = lower.rfind(L'\\', slash - 1);
    std::wstring parent = lower.substr(folder == std::wstring::npos ? 0 : folder + 1, slash - (folder == std::wstring::npos ? 0 : folder + 1));
    if (parent != L"dialog") return L"";
    std::wstring name = requested.substr(slash + 1);
    auto known = dialogCopies.find(name);
    if (known != dialogCopies.end()) return known->second;
    inDialogRedirect = true;
    std::wstring copy;
    try {
        std::ifstream in(requested, std::ios::binary);
        std::string content((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
        size_t done = 0, total = 0;
        std::string translated = in ? content : std::string();
        if (!content.empty()) translated = engine.TranslateDialogFile(content, done, total);
        std::wstring dir = root + L"notgeese\\cache\\Dialog\\";
        CreateDirectoryW((root + L"notgeese\\cache").c_str(), nullptr);
        CreateDirectoryW(dir.c_str(), nullptr);
        std::ofstream out(dir + name, std::ios::binary | std::ios::trunc);
        out.write(translated.data(), std::streamsize(translated.size()));
        if (!content.empty() && out) {
            copy = dir + name;
            int bytes = WideCharToMultiByte(CP_UTF8, 0, name.c_str(), -1, nullptr, 0, nullptr, nullptr);
            std::string utf8(bytes, '\0');
            WideCharToMultiByte(CP_UTF8, 0, name.c_str(), -1, &utf8[0], bytes, nullptr, nullptr);
            Log("Dialog %s: %zu of %zu lines translated", utf8.c_str(), done, total);
        }
    } catch (...) { copy.clear(); }
    inDialogRedirect = false;
    if (!copy.empty()) dialogCopies[name] = copy;
    else Log("Dialog copy failed: using original file");
    return copy;
}

static HANDLE WINAPI OnCreateFileW(LPCWSTR path, DWORD access, DWORD share, LPSECURITY_ATTRIBUTES sa, DWORD disposition, DWORD flags, HANDLE temp) {
    if (path) {
        std::wstring copy = DialogCopy(path, access, disposition);
        if (!copy.empty()) {
            HANDLE h = originalCreateFileW(copy.c_str(), access, share, sa, disposition, flags, temp);
            if (h != INVALID_HANDLE_VALUE) return h;
        }
    }
    return originalCreateFileW(path, access, share, sa, disposition, flags, temp);
}

static HANDLE WINAPI OnCreateFileA(LPCSTR path, DWORD access, DWORD share, LPSECURITY_ATTRIBUTES sa, DWORD disposition, DWORD flags, HANDLE temp) {
    if (path) {
        int length = MultiByteToWideChar(CP_ACP, 0, path, -1, nullptr, 0);
        std::wstring wide(length > 0 ? length - 1 : 0, L'\0');
        if (length > 1) MultiByteToWideChar(CP_ACP, 0, path, -1, &wide[0], length);
        std::wstring copy = DialogCopy(wide, access, disposition);
        if (!copy.empty()) {
            HANDLE h = originalCreateFileW(copy.c_str(), access, share, sa, disposition, flags, temp);
            if (h != INVALID_HANDLE_VALUE) return h;
        }
    }
    return originalCreateFileA(path, access, share, sa, disposition, flags, temp);
}

static std::string Unescape(const std::string& input) {
    std::string out;
    for(size_t i=0;i<input.size();++i) {
        if(input[i]=='\\' && i+1<input.size()) {
            char c=input[++i];
            if(c=='n')out+='\n';else if(c=='r')out+='\r';else if(c=='\\')out+='\\';
            else {out+='\\';out+=c;}
        } else out+=input[i];
    }
    return out;
}

static void Init() {
    wchar_t path[32768]={}; GetModuleFileNameW(selfModule,path,32768);
    root=path; root.resize(root.find_last_of(L"\\/")+1);
    logfile=_wfsopen((root+L"notgeese\\LogOutput.log").c_str(),L"w",_SH_DENYNO);
    Log("notgeese Heat Signature 0.1; engine GameMaker Studio YYC x86; proportional Xolonium sprite fonts");
    DWORD unused=0; wchar_t gamePath[32768]={};GetModuleFileNameW(nullptr,gamePath,32768);
    DWORD size=GetFileVersionInfoSizeW(gamePath,&unused);
    std::vector<BYTE> version(size); VS_FIXEDFILEINFO* info=nullptr; UINT bytes=0;
    if(size && GetFileVersionInfoW(gamePath,0,size,version.data()) && VerQueryValueW(version.data(),L"\\",reinterpret_cast<void**>(&info),&bytes))
        Log("Game PE version %u.%u.%u.%u",HIWORD(info->dwFileVersionMS),LOWORD(info->dwFileVersionMS),HIWORD(info->dwFileVersionLS),LOWORD(info->dwFileVersionLS));
    std::ifstream in(root+L"notgeese\\pl.tsv",std::ios::binary);
    std::string line;size_t rows=0,rejected=0;
    while(std::getline(in,line)) {
        if(!line.empty()&&line.back()=='\r')line.pop_back();
        std::vector<std::string> row;size_t start=0;
        for(size_t tab;(tab=line.find('\t',start))!=std::string::npos;start=tab+1) row.push_back(Unescape(line.substr(start,tab-start)));
        row.push_back(Unescape(line.substr(start)));
        if(engine.Add(row)) ++rows; else ++rejected;
    }
    engine.Finish();
    engine.onMissing=[](const std::string& text){
        Log("Untranslated observed=%zu; translated=%zu; EN=%s",engine.missingCount,engine.translated,text.c_str());
    };
    if(!rows) {Log("No translations: disabled");return;}
    Log("Translation rows: %zu loaded, %zu rejected; %zu exact, %zu templates, %zu fragments, %zu item nouns",
        rows,rejected,engine.exact.size(),engine.templates.size(),engine.fragments.size(),engine.nouns.size());
    Image image;
    BYTE* set=image.BuiltinByName("draw_set_font");
    BYTE* width=image.BuiltinByName("string_width");
    BYTE* font=image.BuiltinByName("font_add_sprite_ext");
    BYTE* getter=image.BuiltinByName("font_get_first");
    if(!getter || !image.Contains(getter,38) ||
       !Match(getter,{0x8b,0x44,0x24,0x14,0x56,0x6a,0,0x50,0x83,0xce,0xff,0xe8,-1,-1,-1,-1,0x50,0xe8,-1,-1,-1,-1,0x83,0xc4,0x0c,0x85,0xc0,0x74,-1,0x8b,0xc8,0xe8})) {
        Log("Font accessor ABI validation failed: disabled");return;
    }
    getFont=reinterpret_cast<GetFont>(image.RelativeCall(getter+17));
    addSprite=reinterpret_cast<Builtin>(image.BuiltinByName("sprite_add"));
    spriteFrames=reinterpret_cast<Builtin>(image.BuiltinByName("sprite_get_number"));
    textWidth=reinterpret_cast<Builtin>(width);
    textHeight=reinterpret_cast<Builtin>(image.BuiltinByName("string_height"));
    if (!set || !width || !font || !getFont || !addSprite || !spriteFrames || !textHeight || !ReadFonts(image)) {Log("Builtin discovery failed: disabled");return;}
    // Validate wrapper instructions before interpreting their relative calls.
    if (!image.Contains(set,22) || !Match(set,{0x8b,0x44,0x24,0x14,0x6a,0,0x50,0xe8,-1,-1,-1,-1,0x50,0xe8,-1,-1,-1,-1,0x83,0xc4,0x0c,0xc3}) ||
        !image.Contains(width,48) || !Match(width+31,{0x6a,0xff,0x8b,0xf0,0x6a,0xff,0x56,0xe8})) {
        Log("Builtin ABI validation failed: disabled");return;
    }
    BYTE* setCore=image.RelativeCall(set+13);
    BYTE* widthCore=image.RelativeCall(width+38);
    BYTE* splitter=nullptr;
    if (widthCore && image.Contains(widthCore,256)) {
        for(int j=0;j<230;++j) {
            if(Match(widthCore+j,{0x8b,0x4c,0x24,0x40,0x8b,0x54,0x24,0x38,0x8d,0x44,0x24,0x18,0x50,0x51,0x52,0xe8})) {
                if(splitter){Log("Ambiguous splitter: disabled");return;}
                splitter=image.RelativeCall(widthCore+j+15);
            }
        }
    }
    if(!setCore || !splitter || !image.Contains(splitter,10) ||
       !Match(splitter,{0x83,0xec,0x0c,0x56,0x8b,0x74,0x24,0x14,0x85,0xf6}) ||
       !image.Contains(font,14) || !Match(font,{0x53,0x56,0x8b,0x74,0x24,0x1c,0x57,0x6a,0,0x56,0x83,0xcb,0xff,0xe8})) {
        Log("Font/splitter ABI validation failed: disabled");return;
    }
    addFont=reinterpret_cast<Builtin>(font);
    if(MH_Initialize()!=MH_OK ||
       MH_CreateHook(setCore,OnSetFont,reinterpret_cast<void**>(&originalSetFont))!=MH_OK ||
       MH_CreateHook(splitter,OnSplit,reinterpret_cast<void**>(&originalSplit))!=MH_OK) {
        MH_Uninitialize();Log("Hook preparation failed: disabled");return;
    }
    // Optional: dialogue files. Without these hooks spoken lines are still translated when drawn.
    if(MH_CreateHookApi(L"kernel32","CreateFileW",OnCreateFileW,reinterpret_cast<void**>(&originalCreateFileW))!=MH_OK ||
       MH_CreateHookApi(L"kernel32","CreateFileA",OnCreateFileA,reinterpret_cast<void**>(&originalCreateFileA))!=MH_OK) {
        MH_RemoveHook(GetProcAddress(GetModuleHandleW(L"kernel32"),"CreateFileW"));
        MH_RemoveHook(GetProcAddress(GetModuleHandleW(L"kernel32"),"CreateFileA"));
        Log("Dialog file hooks unavailable; dialogue translated only when drawn");
    }
    if(MH_EnableHook(MH_ALL_HOOKS)!=MH_OK) {
        MH_DisableHook(MH_ALL_HOOKS);MH_Uninitialize();Log("Hook activation failed: disabled");return;
    }
    Log("Hooks ready. Waiting for game's first font selection.");
}

extern "C" FARPROC __cdecl Resolve(const char* name) {
    static HMODULE real=[](){wchar_t path[MAX_PATH]={};GetSystemDirectoryW(path,MAX_PATH);wcscat_s(path,L"\\d3d9.dll");return LoadLibraryW(path);}();
    static bool attempted=false;
    if(!attempted && (!strcmp(name,"Direct3DCreate9") || !strcmp(name,"Direct3DCreate9Ex"))) {
        attempted=true;
        try {Init();} catch(...) {Log("Initialization exception: disabled");}
    }
    return real ? GetProcAddress(real,name) : nullptr;
}

BOOL WINAPI DllMain(HMODULE module,DWORD reason,LPVOID) {
    if(reason==DLL_PROCESS_ATTACH){selfModule=module;DisableThreadLibraryCalls(module);}return TRUE;
}
