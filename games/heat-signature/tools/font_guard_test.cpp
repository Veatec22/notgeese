// Exercises the real font-loading gate with the empty-font response observed
// in Heat Signature 0.1.0. Does not emulate GPU rendering or launch the game.
#include "../plugin/Plugin.cpp"
#include <cassert>

static int selected=-1, mode=0, probes=0, frameCount=0;
static std::string splitText;
static BYTE fontObject[0x90];
static int16_t glyphData[120][8];
static int16_t* glyphPointers[120];
static BYTE* __cdecl Get(int) {return fontObject;}
static void __cdecl Set(int id) {selected=id;}
static void __cdecl Sprite(Value* r,void*,void*,int n,Value* a) {
    assert(n==6);frameCount=int(a[1].real);r->type=0;r->real=400;
}
static void __cdecl Frames(Value* r,void*,void*,int,Value*) {r->type=0;r->real=frameCount-(mode==3);}
static void __cdecl Font(Value* r,void*,void*,int n,Value*) {
    assert(n==4);r->type=0;r->real=19;
    *reinterpret_cast<int*>(fontObject+0x20)=400;
    *reinterpret_cast<int*>(fontObject+0x40)=120;
    *reinterpret_cast<int16_t***>(fontObject+0x44)=glyphPointers;
    std::ifstream file(root+L"notgeese\\fonts\\font-12-0-0.metrics");
    int code,frame,advance,offset,height;
    while(file>>code>>frame>>advance>>offset>>height) {
        glyphPointers[frame]=glyphData[frame];
        glyphData[frame][0]=int16_t(code);glyphData[frame][3]=int16_t(frame);
        glyphData[frame][4]=int16_t(height);glyphData[frame][5]=24;glyphData[frame][6]=0;
    }
    if(mode==4)glyphData[1][3]=-1;
}
static void __cdecl Width(Value* r,void*,void*,int,Value* a) {
    ++probes;r->type=0;r->real=(mode==0 || (mode==2 && !strcmp(a->str->text,u8"ą"))) ? 0 : 8;
    if(mode==1) {if(!strcmp(a->str->text,"i"))r->real=4;if(!strcmp(a->str->text,"W"))r->real=16;}
}
static void __cdecl Height(Value* r,void*,void*,int,Value*) {r->type=0;r->real=mode==0 ? 0 : 16;}
static void __cdecl Lines(const char* text,int,void*) {splitText=text;}

int wmain(int argc,wchar_t** argv) {
    assert(argc==2);root=argv[1];root+=L"\\";
    addSprite=Sprite;spriteFrames=Frames;addFont=Font;textWidth=Width;textHeight=Height;
    originalSetFont=Set;originalSplit=Lines;getFont=Get;engine.Add({"E","Options",u8"Ustawienia"});engine.Finish();
    for(int scenario: {0,2,3,4,5,1}) {
        mode=scenario;fontsReady=fontsAttempted=false;fonts={{12,0,0,-1}};probes=0;
        OnSetFont(0);
        OnSplit("Options",-1,nullptr);
        if(mode==1) {
            assert(fontsReady && selected==19 && probes>=113);
            assert(splitText==u8"Ustawienia");
            assert(glyphData['i'-32][5]<glyphData['W'-32][5]);
            assert(glyphData['i'-32][5]<12 && glyphData[' '-32][5]<12);
        } else {
            assert(!fontsReady && selected==0 && splitText=="Options");
            int before=probes;OnSetFont(0);assert(probes==before);
        }
    }
    puts("PASS: variable advances replace full-cell spacing; empty fonts, missing Polish glyphs, wrong frame counts and incompatible layouts retain original font + English. GPU rendering not tested.");
}
