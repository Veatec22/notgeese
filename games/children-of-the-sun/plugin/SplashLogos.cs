// Polish splash logos.
//
// The Unity splash screen shows three logo textures with baked English text (warning about
// flashing images, "presented by", "a game by"). The package carries our own redrawn PNGs
// (tools/splash.py, OFL fonts, nothing taken from the game's images); at startup we load them
// into the logo textures by name and give the logo sprites a full-quad mesh (the original mesh
// hugs the English letters). If the splash has already been shown, nothing is lost: the
// log says so. Missing PNG or texture: the English logo stays.

using System;
using System.IO;
using System.Reflection;
using UnityEngine;

namespace notgeese.ChildrenOfTheSun
{
    internal static class SplashLogos
    {
        private static readonly string[] Names = { "logowarning", "logodevolver", "agameby_logo" };

        internal static void Replace()
        {
            var folder = Path.Combine(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location), "splash");
            var replaced = 0;
            foreach (var texture in Resources.FindObjectsOfTypeAll<Texture2D>())
            {
                if (texture == null || Array.IndexOf(Names, texture.name) < 0) continue;
                var path = Path.Combine(folder, texture.name + ".png");
                if (!File.Exists(path))
                {
                    Plugin.Log.LogWarning("Missing " + path + "; splash logo stays English.");
                    continue;
                }
                try
                {
                    if (Load(texture, File.ReadAllBytes(path))) replaced++;
                }
                catch (Exception error)
                {
                    Plugin.Log.LogWarning("Splash logo \"" + texture.name + "\": " + error.Message);
                }
            }
            // The logo sprites have a tight mesh cut around the original letters; only pixels inside
            // it are drawn. Our text has other shapes, so each sprite becomes a full quad.
            var quads = 0;
            foreach (var sprite in Resources.FindObjectsOfTypeAll<Sprite>())
            {
                if (sprite == null || Array.IndexOf(Names, sprite.name) < 0) continue;
                try
                {
                    var w = sprite.rect.width;
                    var h = sprite.rect.height;
                    sprite.OverrideGeometry(
                        new[] { new Vector2(0, 0), new Vector2(w, 0), new Vector2(w, h), new Vector2(0, h) },
                        new ushort[] { 0, 2, 1, 0, 3, 2 });
                    quads++;
                }
                catch (Exception error)
                {
                    Plugin.Log.LogWarning("Splash sprite \"" + sprite.name + "\": " + error.Message);
                }
            }
            Plugin.Log.LogInfo("Splash sprites set to full quads: " + quads + ".");

            bool finished;
            try { finished = UnityEngine.Rendering.SplashScreen.isFinished; }
            catch (Exception) { finished = false; }
            Plugin.Log.LogInfo("Splash logos replaced: " + replaced + " of " + Names.Length
                + (finished ? " (splash already finished, effect only on next display)." : " (before the splash finished)."));
        }

        private static bool Load(Texture2D texture, byte[] png)
        {
            var format = texture.format;
            var mips = texture.mipmapCount;

            // Direct: decode into the logo texture itself.
            try
            {
                if (ImageConversion.LoadImage(texture, png, false))
                {
                    Plugin.Log.LogInfo(string.Format("Splash logo \"{0}\": loaded ({1} → {2}, {3}×{4}).",
                        texture.name, format, texture.format, texture.width, texture.height));
                    return true;
                }
            }
            catch (Exception error)
            {
                Plugin.Log.LogInfo("Splash logo \"" + texture.name + "\": direct load failed (" + error.Message + "), copying on GPU.");
            }

            // Fallback for a texture that refuses LoadImage: same size, format and mips, GPU copy.
            var source = new Texture2D(texture.width, texture.height, TextureFormat.RGBA32, mips, false);
            try
            {
                if (!ImageConversion.LoadImage(source, png, false) || source.width != texture.width || source.height != texture.height)
                    return false;
                if (source.format != format) source.Compress(true);
                if (source.format != format)
                {
                    Plugin.Log.LogWarning("Splash logo \"" + texture.name + "\": format " + source.format + " ≠ " + format + ".");
                    return false;
                }
                if (source.mipmapCount == mips) Graphics.CopyTexture(source, texture);
                else Graphics.CopyTexture(source, 0, 0, texture, 0, 0);
                Plugin.Log.LogInfo("Splash logo \"" + texture.name + "\": copied on GPU (" + format + ").");
                return true;
            }
            finally
            {
                UnityEngine.Object.Destroy(source);
            }
        }
    }
}
