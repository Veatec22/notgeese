// Dump of string literals from Assembly-CSharp.dll: "Type::method<TAB>literal" per line.
// Rain World's strings.txt keys are English texts written in code, so this tells where an
// entry appears in the game (options menu, HUD, tutorial...).
// Compiled and run by extract.py; Mono.Cecil.dll comes from the game's Managed dir.
using System;
using System.IO;
using System.Text;
using Mono.Cecil;
using Mono.Cecil.Cil;

static class StrMap
{
    static string Escape(string s)
    {
        return s.Replace("\\", "\\\\").Replace("\t", "\\t").Replace("\r", "\\r").Replace("\n", "\\n");
    }

    static void Main(string[] args)
    {
        var resolver = new DefaultAssemblyResolver();
        resolver.AddSearchDirectory(Path.GetDirectoryName(args[0]));
        var assembly = AssemblyDefinition.ReadAssembly(args[0], new ReaderParameters { AssemblyResolver = resolver });
        using (var output = new StreamWriter(args[1], false, new UTF8Encoding(false)))
        {
            foreach (var type in assembly.MainModule.GetTypes())
                foreach (var method in type.Methods)
                {
                    if (!method.HasBody) continue;
                    foreach (var instruction in method.Body.Instructions)
                        if (instruction.OpCode == OpCodes.Ldstr)
                            output.WriteLine(type.FullName + "::" + method.Name + "\t" + Escape((string)instruction.Operand));
                }
        }
    }
}
