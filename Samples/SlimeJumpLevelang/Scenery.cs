// Scenery: draws the level's parallax layers and its smooth skin, the pictures levelang baked into SceneryData.cs.
//
// The renderer draws meshes (GFX.Triangles) OVER the sprite batch, so a layer "behind" the game cannot be drawn by the batch's order. Viewer.cs therefore draws everything as meshes, in
// the order it wants: Scenery.Draw(false, ...) first (the layers behind the tiles, and the skin, which is a layer too), then the actors, then Scenery.Draw(true, ...) (the foreground).
//
// This is a C# port of prowl_editor/parallax.py (item_vertices and plan): the editor draws the same layers the same way, and tools/levelang/tests/test_scenery.py checks a Python
// transcription of THIS file against it. Positions in a layer are cells from the level's top left, y down; a vertex is x, y (world, y up), u, v, r, g, b, a (8 floats).
using System;
using Prowl.Native.Gfx2D;

static class Scenery
{
    const float AnimPeriod = 2.4f;          // seconds for one sway or bob (the preview's)
    const float BobCells = 0.22f;
    const float TwoPi = 6.2831853f;
    const int MaxVerts = 60000;             // a multiple of 3, under the renderer's 65536 in one call
    const int Floats = 8;

    static int tex;
    static float[] buf;
    static int used;                        // floats in buf
    static int drawn;                       // vertices sent since the last ResetStats()

    public static int VerticesDrawn() { return drawn; }

    // Decodes the atlas into a texture. Returns 0, or 1 when the renderer will not make it (the layers are then skipped, the game still runs).
    public static int Init()
    {
        int w = SceneryData.AtlasW;
        int h = SceneryData.AtlasH;
        byte[] rgba = new byte[w * h * 4];
        int p = 0;
        for (int i = 0; i < SceneryData.RunCount; i++)
        {
            int run = SceneryData.Runs[i];
            int count = run / 256;
            int idx = run % 256;
            if (idx != 0)
            {
                byte r = (byte)SceneryData.Palette[idx * 4];
                byte g = (byte)SceneryData.Palette[idx * 4 + 1];
                byte b = (byte)SceneryData.Palette[idx * 4 + 2];
                byte a = (byte)SceneryData.Palette[idx * 4 + 3];
                for (int k = 0; k < count; k++)
                {
                    rgba[p] = r;
                    rgba[p + 1] = g;
                    rgba[p + 2] = b;
                    rgba[p + 3] = a;
                    p += 4;
                }
            }
            else p += count * 4;            // air: the array starts as zeros (transparent)
        }
        tex = GFX.Texture(w, h, 1, rgba);   // 1: linear filtering, the layers are scaled
        buf = new float[MaxVerts * Floats];
        used = 0;
        if (tex == 0) return 1;
        return 0;
    }

    public static void Shutdown()
    {
        if (tex != 0) GFX.TextureFree(tex);
        tex = 0;
    }

    // The layers behind the game (over = false) or in front of it (over = true), for a camera whose left edge is camLeft cells from the level's left and whose top edge is camTop cells below
    // the level's top. `clock` is in seconds. Draw the far layers first: they are stored that way.
    public static void Draw(bool over, float camLeft, float camTop, float clock)
    {
        if (tex == 0) return;
        used = 0;
        for (int l = 0; l < SceneryData.LayerCount; l++)
        {
            int lb = l * SceneryData.LayerStride;
            bool isOver = SceneryData.Layers[lb + 2] > 0.5f;
            if (isOver != over) continue;
            float offX = camLeft * (1f - SceneryData.Layers[lb]);
            float offY = camTop * (1f - SceneryData.Layers[lb + 1]);
            float tr = SceneryData.Layers[lb + 3];
            float tg = SceneryData.Layers[lb + 4];
            float tb = SceneryData.Layers[lb + 5];
            float ta = SceneryData.Layers[lb + 6];
            int first = (int)SceneryData.Layers[lb + 7];
            int count = (int)SceneryData.Layers[lb + 8];
            for (int k = first; k < first + count; k++)
                Item(k * SceneryData.ItemStride, offX, offY, clock, tr, tg, tb, ta);
        }
        Flush();
    }

    static void Flush()
    {
        if (used == 0) return;
        int verts = used / Floats;
        GFX.Triangles(buf, verts, tex);
        drawn += verts;
        used = 0;
    }

    static void Vertex(float x, float y, float u, float v, float r, float g, float b, float a)
    {
        if (used + Floats > MaxVerts * Floats) Flush();
        buf[used] = x;
        buf[used + 1] = y;
        buf[used + 2] = u;
        buf[used + 3] = v;
        buf[used + 4] = r;
        buf[used + 5] = g;
        buf[used + 6] = b;
        buf[used + 7] = a;
        used += Floats;
    }

    static float Frac(float v) { return v - (float)(int)v; }       // v is never negative here: the clock and the phases are not

    // How far a swaying item leans at a line `above` cells over its foot.
    static float Lean(float amp, float above, float u) { return amp * above * MathF.Sin(TwoPi * u - 0.9f * above); }

    static void Item(int o, float offX, float offY, float clock, float tr, float tg, float tb, float ta)
    {
        float[] it = SceneryData.Items;
        float u0 = it[o];
        float v0 = it[o + 1];
        float u1 = it[o + 2];
        float v1 = it[o + 3];
        float x = it[o + 4] + offX;
        float y = it[o + 5] + offY;
        float w = it[o + 6];
        float h = it[o + 7];
        bool flipped = it[o + 8] > 0.5f;
        float swimN = it[o + 9];
        float swimPeriod = it[o + 10];
        float bob = it[o + 11];
        float sway = it[o + 12];
        float baseUp = it[o + 13];
        float phase = it[o + 14];
        float swayPhase = it[o + 15];

        if (swimN > 0f)
        {
            float t = Frac(clock / swimPeriod + phase);
            float tri = 1f - MathF.Abs(2f * t - 1f);
            x += tri * swimN;
            if (t > 0.5f) flipped = !flipped;
        }
        if (bob > 0.5f) y += MathF.Sin(TwoPi * Frac(clock / AnimPeriod + phase)) * BobCells;

        // the picture's own left/right edges in u (mirrored when flipped); v runs from the top (v0) to the bottom (v1)
        float uLeft = u0;
        float uRight = u1;
        if (flipped)
        {
            uLeft = u1;
            uRight = u0;
        }
        int n = 1;
        float u = 0f;
        if (sway >= 0f)
        {
            float want = h * 2f;
            n = (int)want;
            if ((float)n < want) n++;
            if (n < 4) n = 4;
            if (n > 16) n = 16;
            u = Frac(clock / AnimPeriod + swayPhase);
        }
        float height = SceneryData.LevelHeight;
        for (int k = 0; k < n; k++)
        {
            float va = (float)k / (float)n;
            float vb = (float)(k + 1) / (float)n;
            float leanA = 0f;
            float leanB = 0f;
            if (sway >= 0f)
            {
                leanA = Lean(sway, baseUp + h * (1f - va), u);
                leanB = Lean(sway, baseUp + h * (1f - vb), u);
            }
            float tlx = x + leanA;
            float trx = x + w + leanA;
            float ty = height - (y + h * va);
            float blx = x + leanB;
            float brx = x + w + leanB;
            float by = height - (y + h * vb);
            float tv = v0 + (v1 - v0) * va;
            float bv = v0 + (v1 - v0) * vb;
            Vertex(tlx, ty, uLeft, tv, tr, tg, tb, ta);
            Vertex(trx, ty, uRight, tv, tr, tg, tb, ta);
            Vertex(brx, by, uRight, bv, tr, tg, tb, ta);
            Vertex(tlx, ty, uLeft, tv, tr, tg, tb, ta);
            Vertex(brx, by, uRight, bv, tr, tg, tb, ta);
            Vertex(blx, by, uLeft, bv, tr, tg, tb, ta);
        }
    }
}
