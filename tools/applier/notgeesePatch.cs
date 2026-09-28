// Not Geese patch applier: one file next to the patch, no install.
//
// Applies format 2 patches from tools/patch.py: text header with checksums,
// then an op list "copy from original" / "insert bytes" packed with DEFLATE.
// Format 3 adds "sources" (original assembled from game file slices) and "mode create"
// (result is a new file next to the game files; restoring = deleting it).
// Everything from .NET Framework 4, present on every Windows for years; no library.
//
// Usage:
//   notgeesePatch.exe                          applies every patch next to it, game = program dir
//   notgeesePatch.exe <game dir> [patch...]
//   notgeesePatch.exe --przywroc [game dir] [patch...]
//
// Deliberately C# 5 so the csc.exe shipped with Windows itself can compile it.
// Player-facing messages are Polish on purpose.

using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using System.Windows.Forms;

static class notgeesePatch
{
    const string Magic = "NOTGEESE-PATCH";
    const string Format = "2";
    const string FormatSources = "3";
    const string BackupSuffix = ".przed-spolszczeniem";

    class Failure : Exception
    {
        public Failure(string message) : base(message) { }
    }

    [STAThread]
    static int Main(string[] args)
    {
        try { Console.OutputEncoding = Encoding.UTF8; } catch (IOException) { }
        Console.WriteLine("Not Geese — nakładanie spolszczenia");
        Console.WriteLine();

        int code;
        try
        {
            code = Run(new List<string>(args));
        }
        catch (Failure failure)
        {
            Console.WriteLine("BŁĄD: " + failure.Message);
            Console.WriteLine();
            Console.WriteLine("Nic nie zostało zmienione.");
            code = 1;
        }
        catch (Exception error)
        {
            Console.WriteLine("Nieoczekiwany błąd: " + error);
            code = 2;
        }

        // After a double-click the window would close before the player reads the result.
        if (!Console.IsInputRedirected)
        {
            Console.WriteLine();
            Console.Write("Naciśnij Enter, aby zamknąć.");
            Console.ReadLine();
        }
        return code;
    }

    // One patch = one game file. A package may carry several; apply all or none.
    class Job
    {
        public string PatchPath;
        public Dictionary<string, string> Header;
        public byte[] Payload;
        public string Target;
        public string Backup { get { return Target + BackupSuffix; } }
        public bool Installed;
        public string Source;   // where the original is read from: the game file or the backup copy
        public string GameDir;
        public bool Create { get { string mode; return Header.TryGetValue("mode", out mode) && mode == "create"; } }
        public string Sources { get { string value; return Header.TryGetValue("sources", out value) ? value : null; } }
    }

    static int Run(List<string> args)
    {
        bool restore = args.Remove("--przywroc");
        string here = AppDomain.CurrentDomain.BaseDirectory;

        string[] patchPaths = args.Count > 1 ? args.GetRange(1, args.Count - 1).ToArray() : FindPatches(here);
        List<Job> jobs = new List<Job>();
        foreach (string patchPath in patchPaths)
        {
            Job job = new Job { PatchPath = patchPath };
            ReadPatch(File.ReadAllBytes(patchPath), out job.Header, out job.Payload);
            jobs.Add(job);
        }

        string gameDir = args.Count > 0 ? args[0] : here;
        if (args.Count == 0 && !File.Exists(AnchorIn(gameDir, jobs[0])))
        {
            Console.WriteLine("Nie widzę plików gry obok programu. Wskaż katalog gry.");
            gameDir = AskForFolder(jobs[0].Header["file"]);
        }
        foreach (Job job in jobs)
        {
            job.Target = TargetIn(gameDir, job);
            job.GameDir = gameDir;
            if (!File.Exists(AnchorIn(gameDir, job)))
                throw new Failure("Nie znalazłem pliku gry: " + AnchorIn(gameDir, job) +
                                  "\nWypakuj paczkę do katalogu gry albo podaj go jako parametr.");
            Console.WriteLine("Łatka " + Path.GetFileName(job.PatchPath) + " -> " + job.Header["file"]);
        }
        Console.WriteLine();

        if (restore)
            return Restore(jobs);

        // Najpierw sprawdzamy wszystkie pliki, dopiero potem cokolwiek zapisujemy.
        Console.WriteLine("Sprawdzam sumy kontrolne…");
        foreach (Job job in jobs)
        {
            if (job.Sources != null)
            {
                job.Installed = File.Exists(job.Target) && Sha256(File.ReadAllBytes(job.Target)) == job.Header["target-sha256"];
                if (!job.Installed && Sha256(ReadSources(job)) != job.Header["source-sha256"])
                    throw new Failure("Pliki gry nie są tymi, pod które zrobiono łatkę " + job.Header["file"] + ".\n" +
                                      "Spolszczenie sprawdzono na wersji gry podanej w READ-ME.txt; inna wersja\n" +
                                      "albo wydanie z innego sklepu może mieć pliki ułożone inaczej.");
                continue;
            }
            string digest = Sha256(File.ReadAllBytes(job.Target));
            job.Installed = digest == job.Header["target-sha256"];
            job.Source = job.Target;
            // Older translation version: the game file is already changed but the backed-up
            // original lies next to it. Apply the new patch to that; this is an update.
            if (!job.Installed && digest != job.Header["source-sha256"] && File.Exists(job.Backup)
                && Sha256(File.ReadAllBytes(job.Backup)) == job.Header["source-sha256"])
            {
                job.Source = job.Backup;
                Console.WriteLine("  " + job.Header["file"] + ": inna wersja spolszczenia, aktualizuję z kopii oryginału");
            }
            else if (!job.Installed && digest != job.Header["source-sha256"])
                throw new Failure("Plik " + job.Header["file"] + " nie jest tym, pod który zrobiono łatkę.\n" +
                                  "  oczekiwano " + job.Header["source-sha256"] + "\n" +
                                  "  jest       " + digest + "\n" +
                                  "Jeśli gra dostała aktualizację, potrzebna jest nowa łatka.");
        }

        if (jobs.TrueForAll(delegate(Job job) { return job.Installed; }))
        {
            Console.WriteLine("Spolszczenie jest już wgrane.");
            if (Console.IsInputRedirected || !jobs.TrueForAll(delegate(Job job) { return job.Create || File.Exists(job.Backup); }))
                return 0;
            Console.Write("Przywrócić oryginał gry? [t/N] ");
            string answer = (Console.ReadLine() ?? "").Trim().ToLowerInvariant();
            return answer == "t" || answer == "tak" ? Restore(jobs) : 0;
        }

        foreach (Job job in jobs)
        {
            if (job.Installed)
                continue;
            Console.WriteLine("Nakładam łatkę na " + job.Header["file"] + "…");
            byte[] source = job.Sources != null ? ReadSources(job) : File.ReadAllBytes(job.Source);
            byte[] result = Apply(source, Inflate(job.Payload), long.Parse(job.Header["target-size"]));
            if (Sha256(result) != job.Header["target-sha256"])
                throw new Failure("Odtworzony plik " + job.Header["file"] + " ma inną sumę kontrolną niż powinien.");

            if (job.Create)
            {
                // New file next to the game files: nothing to back up, an older version is just replaced.
                string fresh = job.Target + ".notgeese-tmp";
                File.WriteAllBytes(fresh, result);
                if (File.Exists(job.Target))
                    File.Delete(job.Target);
                File.Move(fresh, job.Target);
                Console.WriteLine("  utworzono: " + job.Target);
                continue;
            }

            // Backup first, then write to a temp file, then swap;
            // an interruption never leaves a broken file in the game.
            if (!File.Exists(job.Backup))
                File.Copy(job.Target, job.Backup);
            string temporary = job.Target + ".notgeese-tmp";
            File.WriteAllBytes(temporary, result);
            File.Delete(job.Target);
            File.Move(temporary, job.Target);
            Console.WriteLine("  kopia oryginału: " + job.Backup);
        }

        Console.WriteLine();
        Console.WriteLine("Gotowe. Spolszczenie wgrane.");
        return 0;
    }

    static string TargetIn(string gameDir, Job job)
    {
        return Path.Combine(gameDir, job.Header["file"].Replace('/', Path.DirectorySeparatorChar));
    }

    static int Restore(List<Job> jobs)
    {
        foreach (Job job in jobs)
        {
            if (job.Create)
                continue;
            if (!File.Exists(job.Backup))
                throw new Failure("Nie ma kopii oryginału (" + job.Backup + ").\n" +
                                  "Zweryfikuj pliki gry w Steamie albo GOG Galaxy.");
            if (Sha256(File.ReadAllBytes(job.Backup)) != job.Header["source-sha256"])
                throw new Failure("Kopia " + job.Backup + " nie jest oryginałem, pod który zrobiono łatkę.");
        }
        foreach (Job job in jobs)
        {
            if (job.Create)
            {
                if (File.Exists(job.Target))
                    File.Delete(job.Target);
                continue;
            }
            File.Copy(job.Backup, job.Target, true);
            File.Delete(job.Backup);
        }
        Console.WriteLine("Przywrócono oryginał.");
        return 0;
    }

    // File that identifies the game dir: the first source slice or the game file itself.
    static string AnchorIn(string gameDir, Job job)
    {
        if (job.Sources == null)
            return TargetIn(gameDir, job);
        string first = job.Sources.Split(';')[0];
        return Path.Combine(gameDir, first.Substring(0, first.LastIndexOf('@')).Replace('/', Path.DirectorySeparatorChar));
    }

    // Original assembled from game file slices: path@offset+length;...
    static byte[] ReadSources(Job job)
    {
        MemoryStream output = new MemoryStream();
        foreach (string part in job.Sources.Split(';'))
        {
            int at = part.LastIndexOf('@');
            string[] span = part.Substring(at + 1).Split('+');
            long offset = long.Parse(span[0]);
            int length = int.Parse(span[1]);
            string path = Path.Combine(job.GameDir, part.Substring(0, at).Replace('/', Path.DirectorySeparatorChar));
            using (FileStream file = File.OpenRead(path))
            {
                if (file.Length < offset + length)
                    throw new Failure("Plik " + path + " jest krótszy, niż zakłada łatka.");
                file.Seek(offset, SeekOrigin.Begin);
                byte[] chunk = new byte[length];
                int read = 0;
                while (read < length)
                {
                    int got = file.Read(chunk, read, length - read);
                    if (got == 0)
                        throw new Failure("Nie da się odczytać " + path + ".");
                    read += got;
                }
                output.Write(chunk, 0, length);
            }
        }
        return output.ToArray();
    }

    static string[] FindPatches(string directory)
    {
        string[] found = Directory.GetFiles(directory, "*.patch");
        if (found.Length == 0)
            throw new Failure("Nie ma pliku .patch obok programu. Wypakuj całą paczkę razem.");
        Array.Sort(found, StringComparer.OrdinalIgnoreCase);
        return found;
    }

    static string AskForFolder(string relative)
    {
        using (FolderBrowserDialog dialog = new FolderBrowserDialog())
        {
            dialog.Description = "Wskaż katalog gry — ten, w którym leży " + relative.Split('/')[0];
            dialog.ShowNewFolderButton = false;
            if (dialog.ShowDialog() != DialogResult.OK)
                throw new Failure("Nie wybrano katalogu gry.");
            return dialog.SelectedPath;
        }
    }

    static void ReadPatch(byte[] raw, out Dictionary<string, string> header, out byte[] payload)
    {
        int split = -1;
        for (int i = 0; i + 1 < raw.Length; i++)
            if (raw[i] == '\n' && raw[i + 1] == '\n') { split = i; break; }
        if (split <= 0)
            throw new Failure("To nie jest łatka Not Geese.");

        string[] lines = Encoding.UTF8.GetString(raw, 0, split).Split('\n');
        // Compatibility with patches distributed before the project rename.
        if (lines[0] != Magic && lines[0] != "NIEGESI-PATCH")
            throw new Failure("To nie jest łatka Not Geese.");

        header = new Dictionary<string, string>();
        for (int i = 1; i < lines.Length; i++)
        {
            int space = lines[i].IndexOf(' ');
            if (space > 0)
                header[lines[i].Substring(0, space)] = lines[i].Substring(space + 1);
        }
        string format;
        if (!header.TryGetValue("format", out format) || (format != Format && format != FormatSources))
            throw new Failure("Nieznana wersja formatu łatki: " + format + ". Pobierz nowszy aplikator.");

        payload = new byte[raw.Length - split - 2];
        Buffer.BlockCopy(raw, split + 2, payload, 0, payload.Length);
    }

    static byte[] Inflate(byte[] data)
    {
        using (DeflateStream inflater = new DeflateStream(new MemoryStream(data), CompressionMode.Decompress))
        using (MemoryStream output = new MemoryStream())
        {
            inflater.CopyTo(output);
            return output.ToArray();
        }
    }

    static long ReadVarint(byte[] data, ref int at)
    {
        long value = 0;
        int shift = 0;
        while (true)
        {
            byte current = data[at++];
            value |= (long)(current & 0x7F) << shift;
            shift += 7;
            if ((current & 0x80) == 0)
                return value;
        }
    }

    static byte[] Apply(byte[] source, byte[] ops, long size)
    {
        byte[] output = new byte[size];
        long written = 0, cursor = 0;
        int at = 0;
        while (true)
        {
            byte op = ops[at++];
            if (op == 0)
                break;
            long length = ReadVarint(ops, ref at);
            if (written + length > size)
                throw new Failure("Łatka daje za duży plik.");
            if (op == 1)
            {
                long delta = ReadVarint(ops, ref at);
                long origin = cursor + ((delta >> 1) ^ -(delta & 1));
                if (origin < 0 || origin + length > source.Length)
                    throw new Failure("Łatka sięga poza oryginał.");
                Array.Copy(source, origin, output, written, length);
                cursor = origin + length;
            }
            else if (op == 2)
            {
                Array.Copy(ops, at, output, written, length);
                at += (int)length;
            }
            else
            {
                throw new Failure("Nieznana operacja w łatce: " + op);
            }
            written += length;
        }
        if (written != size)
            throw new Failure("Łatka dała plik innej długości niż powinna.");
        return output;
    }

    static string Sha256(byte[] data)
    {
        using (SHA256 hasher = SHA256.Create())
        {
            byte[] hash = hasher.ComputeHash(data);
            StringBuilder text = new StringBuilder(hash.Length * 2);
            foreach (byte b in hash)
                text.Append(b.ToString("x2"));
            return text.ToString();
        }
    }
}
