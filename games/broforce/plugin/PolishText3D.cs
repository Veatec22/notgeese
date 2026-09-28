// Polish letters for 3D titles (Text3D: "DOŁĄCZ DO GRY", screen titles).
//
// Text3D doesn't draw with a font: each letter is a separate mesh from the A–Z list
// (charA…charZ), extruded along z, no UV (look comes from lighting). A character
// outside the list becomes a space. Before each title is built we add Ą Ć Ę Ł Ń Ó Ś Ź Ż
// to the list: base letter mesh plus a prism for the mark (acute, dot, ogonek, stroke)
// with the "I" stem width and letter depth. Text3D takes character width from the
// K-TYPE font, which gets Polish letters in PolishGlyphs.

using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace notgeese.Broforce
{
    [HarmonyPatch]
    internal static class PolishText3D
    {
        private enum Mark { Acute, Dot, Ogonek, Stroke }

        private struct Recipe
        {
            public char Letter, Base;
            public Mark Mark;
            public Recipe(char letter, char baseChar, Mark mark) { Letter = letter; Base = baseChar; Mark = mark; }
        }

        private static readonly Recipe[] Recipes =
        {
            new Recipe('Ą', 'A', Mark.Ogonek), new Recipe('Ć', 'C', Mark.Acute), new Recipe('Ę', 'E', Mark.Ogonek),
            new Recipe('Ł', 'L', Mark.Stroke), new Recipe('Ń', 'N', Mark.Acute), new Recipe('Ó', 'O', Mark.Acute),
            new Recipe('Ś', 'S', Mark.Acute), new Recipe('Ź', 'Z', Mark.Acute), new Recipe('Ż', 'Z', Mark.Dot),
        };

        private static readonly Dictionary<string, Mesh> Cache = new Dictionary<string, Mesh>();
        private static bool reported, failed;

        [HarmonyPrefix]
        [HarmonyPatch(typeof(Text3D), "UpdateText", new[] { typeof(string) })]
        private static void BeforeUpdateText(Text3D __instance)
        {
            if (failed || __instance == null) return;
            try
            {
                PolishGlyphs.PatchLoadedFonts();
                Extend(__instance);
            }
            catch (Exception error)
            {
                failed = true;
                Plugin.Log.LogWarning("3D titles: could not add Polish letters: " + error);
            }
        }

        private static void Extend(Text3D text)
        {
            var traverse = Traverse.Create(text);
            var letters = traverse.Field("characterList").GetValue<char[]>();
            var meshes = traverse.Field("meshList").GetValue<Mesh[]>();
            if (letters == null || meshes == null || letters.Length != meshes.Length) return;
            if (Array.IndexOf(letters, 'Ą') >= 0) return;

            var index = new Dictionary<char, Mesh>();
            for (var i = 0; i < letters.Length; i++)
                if (meshes[i] != null) index[letters[i]] = meshes[i];
            Mesh baseI, baseL;
            if (!index.TryGetValue('A', out baseI) || !index.ContainsKey('Z')) return;

            // Stroke width = width of "I" (stem only); screen "right" = the side the foot of
            // "L" leaves its stem to (Text3D lays letters toward negative x).
            var stroke = index.TryGetValue('I', out baseI) ? baseI.bounds.size.x : index['A'].bounds.size.y * 0.25f;
            var right = -1f;
            if (index.TryGetValue('L', out baseL)) right = RightDirection(baseL);

            var newLetters = new List<char>(letters);
            var newMeshes = new List<Mesh>(meshes);
            foreach (var recipe in Recipes)
            {
                Mesh source;
                if (Array.IndexOf(letters, recipe.Letter) >= 0 || !index.TryGetValue(recipe.Base, out source)) continue;
                var key = source.GetInstanceID() + ":" + recipe.Letter;
                Mesh composed;
                if (!Cache.TryGetValue(key, out composed) || composed == null)
                {
                    composed = Compose(source, recipe, stroke, right);
                    Cache[key] = composed;
                }
                newLetters.Add(recipe.Letter);
                newMeshes.Add(composed);
            }
            traverse.Field("characterList").SetValue(newLetters.ToArray());
            traverse.Field("meshList").SetValue(newMeshes.ToArray());

            if (!reported)
            {
                reported = true;
                Plugin.Log.LogInfo(string.Format("3D titles: added {0} letters (stroke {1:0.0}, right = {2}x).",
                    newLetters.Count - letters.Length, stroke, right > 0 ? "+" : "-"));
            }
        }

        private static float RightDirection(Mesh l)
        {
            var vertices = l.vertices;
            var bounds = l.bounds;
            float sum = 0;
            var count = 0;
            foreach (var v in vertices)
            {
                if (v.y < bounds.min.y + bounds.size.y * 0.9f) continue;
                sum += v.x;
                count++;
            }
            if (count == 0) return -1f;
            // The stem is on the screen's left, so right is from the stem toward the center.
            return bounds.center.x > sum / count ? 1f : -1f;
        }

        // ---------- geometria ----------

        private static Mesh Compose(Mesh source, Recipe recipe, float t, float right)
        {
            var b = source.bounds;
            // Screen space (u right, v up) -> x = u * right.
            var uLeft = right > 0 ? b.min.x : -b.max.x;
            var uRight = right > 0 ? b.max.x : -b.min.x;
            var bottom = b.min.y;
            var top = b.max.y;
            var height = b.size.y;
            var cx = (uLeft + uRight) * 0.5f;
            var polygons = new List<Vector2[]>();

            switch (recipe.Mark)
            {
                case Mark.Acute:
                {
                    var y0 = top + t * 0.3f;
                    polygons.Add(Bar(new Vector2(cx - t * 0.35f, y0 + t * 0.25f), new Vector2(cx + t * 0.35f, y0 + t * 0.8f), t * 0.65f));
                    break;
                }
                case Mark.Dot:
                {
                    var y0 = top + t * 0.3f;
                    var h = t * 0.375f;
                    polygons.Add(new[]
                    {
                        new Vector2(cx - h, y0), new Vector2(cx + h, y0), new Vector2(cx + h, y0 + 2 * h), new Vector2(cx - h, y0 + 2 * h),
                    });
                    break;
                }
                case Mark.Ogonek:
                {
                    var a = new Vector2(uRight - t * 0.35f, bottom + t * 0.3f);
                    var m = new Vector2(uRight - t * 0.75f, bottom - t * 0.6f);
                    var e = new Vector2(uRight - t * 0.05f, bottom - t * 0.95f);
                    polygons.Add(Bar(a, m, t * 0.6f));
                    polygons.Add(Bar(m, e, t * 0.5f));
                    break;
                }
                case Mark.Stroke:
                {
                    var stem = uLeft + t * 0.5f;
                    polygons.Add(Bar(new Vector2(stem - t * 0.75f, bottom + height * 0.36f), new Vector2(stem + t * 0.95f, bottom + height * 0.6f), t * 0.5f));
                    break;
                }
            }

            var vertices = new List<Vector3>(source.vertices);
            var normals = new List<Vector3>(source.normals);
            var triangles = new List<int>(source.GetTriangles(0));
            foreach (var polygon in polygons)
                Extrude(polygon, right, b.min.z, b.max.z, vertices, normals, triangles);

            var mesh = new Mesh { name = "char" + recipe.Letter };
            mesh.SetVertices(vertices);
            if (normals.Count == vertices.Count) mesh.SetNormals(normals);
            var uv = source.uv;
            if (uv != null && uv.Length > 0)
            {
                var uvs = new List<Vector2>(uv);
                while (uvs.Count < vertices.Count) uvs.Add(uv[0]);
                mesh.SetUVs(0, uvs);
            }
            var colors = source.colors;
            if (colors != null && colors.Length > 0)
            {
                var list = new List<Color>(colors);
                while (list.Count < vertices.Count) list.Add(colors[0]);
                mesh.SetColors(list);
            }
            mesh.subMeshCount = source.subMeshCount;
            mesh.SetTriangles(triangles, 0);
            for (var i = 1; i < source.subMeshCount; i++) mesh.SetTriangles(source.GetTriangles(i), i);
            if (normals.Count != vertices.Count) mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            UnityEngine.Object.DontDestroyOnLoad(mesh);
            return mesh;
        }

        /// Thickened segment a–b as a convex quad.
        private static Vector2[] Bar(Vector2 a, Vector2 b, float thickness)
        {
            var dir = (b - a).normalized;
            var n = new Vector2(-dir.y, dir.x) * (thickness * 0.5f);
            return new[] { a + n, b + n, b - n, a - n };
        }

        /// Extrudes a convex polygon (screen space) between z0 and z1; flat faces, normals outward.
        private static void Extrude(Vector2[] polygon, float right, float z0, float z1,
            List<Vector3> vertices, List<Vector3> normals, List<int> triangles)
        {
            var count = polygon.Length;
            var centre = Vector3.zero;
            var front = new Vector3[count];
            var back = new Vector3[count];
            for (var i = 0; i < count; i++)
            {
                front[i] = new Vector3(polygon[i].x * right, polygon[i].y, z0);
                back[i] = new Vector3(polygon[i].x * right, polygon[i].y, z1);
                centre += front[i];
            }
            centre /= count;

            Face(front, new Vector3(0, 0, -1), vertices, normals, triangles);
            Face(back, new Vector3(0, 0, 1), vertices, normals, triangles);
            for (var i = 0; i < count; i++)
            {
                var j = (i + 1) % count;
                var edge = front[j] - front[i];
                var outward = new Vector3(edge.y, -edge.x, 0).normalized;
                if (Vector3.Dot(outward, (front[i] + front[j]) * 0.5f - centre) < 0) outward = -outward;
                Face(new[] { front[i], front[j], back[j], back[i] }, outward, vertices, normals, triangles);
            }
        }

        /// Convex face as a triangle fan, wound to be visible from the normal's side.
        private static void Face(Vector3[] points, Vector3 normal, List<Vector3> vertices, List<Vector3> normals, List<int> triangles)
        {
            var start = vertices.Count;
            foreach (var p in points)
            {
                vertices.Add(p);
                normals.Add(normal);
            }
            var flip = Vector3.Dot(Vector3.Cross(points[1] - points[0], points[2] - points[0]), normal) < 0;
            for (var i = 1; i + 1 < points.Length; i++)
            {
                triangles.Add(start);
                triangles.Add(flip ? start + i + 1 : start + i);
                triangles.Add(flip ? start + i : start + i + 1);
            }
        }
    }
}
