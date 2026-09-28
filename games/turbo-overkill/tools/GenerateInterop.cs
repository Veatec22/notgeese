// Build-time tool only: reads IL2CPP files, never loads/runs GameAssembly.dll.
using System;
using System.IO;
using System.Collections.Generic;
using Cpp2IL.Core.Api;
using Cpp2IL.Core;
using Il2CppInterop.Common;
using Cpp2IL.Core.InstructionSets;
using Cpp2IL.Core.OutputFormats;
using Cpp2IL.Core.ProcessingLayers;
using LibCpp2IL;
using AssetRipper.Primitives;
using Il2CppInterop.Generator;
using Il2CppInterop.Generator.Runners;
using Microsoft.Extensions.Logging.Abstractions;

class GenerateInterop
{
    sealed class Resolver : Mono.Cecil.IAssemblyResolver
    {
        public readonly Dictionary<string,Mono.Cecil.AssemblyDefinition> Assemblies=new Dictionary<string,Mono.Cecil.AssemblyDefinition>();
        public Mono.Cecil.AssemblyDefinition Resolve(Mono.Cecil.AssemblyNameReference name){return Assemblies[name.Name];}
        public Mono.Cecil.AssemblyDefinition Resolve(Mono.Cecil.AssemblyNameReference name,Mono.Cecil.ReaderParameters parameters){return Resolve(name);}
        public void Dispose(){}
    }
    static void Main(string[] args)
    {
        string game=args[0],work=args[1],unity=args[2];
        Directory.CreateDirectory(work+"/dummy");Directory.CreateDirectory(work+"/interop");
        InstructionSetRegistry.RegisterInstructionSet<X86InstructionSet>(DefaultInstructionSets.X86_64);
        LibCpp2IlBinaryRegistry.RegisterBuiltInBinarySupport();
        Cpp2IL.Core.Logging.Logger.InfoLog += (message,origin)=>Console.WriteLine(origin+": "+message);
        Cpp2IlApi.InitializeLibCpp2Il(game+"/GameAssembly.dll",game+"/Turbo Overkill_Data/il2cpp_data/Metadata/global-metadata.dat",UnityVersion.Parse("2021.3.11f1"),false);
        var layers=new List<Cpp2IlProcessingLayer>{new AttributeInjectorProcessingLayer()};
        foreach(var layer in layers)layer.PreProcess(Cpp2IlApi.CurrentAppContext,layers);
        foreach(var layer in layers)layer.Process(Cpp2IlApi.CurrentAppContext);
        var assemblies=new AsmResolverDllOutputFormatDefault().BuildAssemblies(Cpp2IlApi.CurrentAppContext);
        foreach(var a in assemblies)using(var stream=File.Create(work+"/dummy/"+a.Name.ToString()+".dll"))a.WriteManifest(stream);
        Console.WriteLine("Dummy assemblies written: "+assemblies.Count);
        var resolver=new Resolver();
        var source=new List<Mono.Cecil.AssemblyDefinition>();
        foreach(var path in Directory.GetFiles(work+"/dummy","*.dll"))
        {var a=Mono.Cecil.AssemblyDefinition.ReadAssembly(path,new Mono.Cecil.ReaderParameters{AssemblyResolver=resolver});source.Add(a);resolver.Assemblies.Add(a.Name.Name,a);}
        var options=new GeneratorOptions{GameAssemblyPath=game+"/GameAssembly.dll",Source=source,OutputDir=work+"/interop",UnityBaseLibsDir=unity};
        Il2CppInteropGenerator.Create(options).AddLogger(NullLogger.Instance).AddInteropAssemblyGenerator().Run();
        Console.WriteLine("Interop complete");
    }
}
