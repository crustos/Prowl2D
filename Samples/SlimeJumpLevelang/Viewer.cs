// Viewer: draws the SlimeJumpLevelang game while the bot plays it, so the parallax layers and the smooth skin show.
//
// Everything is drawn as meshes in the order the picture needs (the renderer draws meshes over the sprite batch, so the batch is not used): the layers behind, the actors as plain coloured
// boxes (the physics shapes, the same data the colliders are made from), the lasso, then the layers in front. The simulation is the headless one in Game.cs: this only looks at it.
//
// Turn it on with Cfg.Draw = true. It writes frame_0000.ppm, frame_0001.ppm ... (every ShotEvery steps of the simulation, like Samples/Draw2D) for the player to turn into a picture.
using System;
using Prowl.Core2D;
using Prowl.Native.Gfx2D;

static class Viewer
{
    public const int Width = 640;
    public const int Height = 360;
    public const float HalfHeight = 10f;            // the level is 20 cells tall: the whole height is on screen
    public const int ShotEvery = 10;                // simulation steps (of Cfg.Dt) per saved picture: 10 fps
    public const int MaxShots = 600;

    static float[] none = new float[8];
    static float[] boxes = new float[8 * 6 * 1024];
    static int boxFloats;
    static int shots;
    static bool ready;

    public static int Init()
    {
        if (GFX.Init(Width, Height) == 0) { Console.WriteLine("no GLES 3 here"); return 1; }
        Scenery.Init();                             // a failed texture only means no layers
        ready = true;
        return 0;
    }

    public static void Shutdown()
    {
        if (!ready) return;
        Scenery.Shutdown();
        GFX.Shutdown();
        ready = false;
    }

    static void V(float x, float y, float r, float g, float b, float a)
    {
        boxes[boxFloats] = x;
        boxes[boxFloats + 1] = y;
        boxes[boxFloats + 2] = 0f;
        boxes[boxFloats + 3] = 0f;
        boxes[boxFloats + 4] = r;
        boxes[boxFloats + 5] = g;
        boxes[boxFloats + 6] = b;
        boxes[boxFloats + 7] = a;
        boxFloats += 8;
    }

    static void Flush()
    {
        if (boxFloats == 0) return;
        GFX.Triangles(boxes, boxFloats / 8, 0);     // texture 0: a white texel, so the vertex colour is the colour
        boxFloats = 0;
    }

    // a box centred on (cx, cy)
    static void Box(float cx, float cy, float w, float h, float r, float g, float b, float a)
    {
        if (boxFloats + 8 * 6 > boxes.Length) Flush();
        float x0 = cx - w * 0.5f;
        float x1 = cx + w * 0.5f;
        float y0 = cy - h * 0.5f;
        float y1 = cy + h * 0.5f;
        V(x0, y1, r, g, b, a);
        V(x1, y1, r, g, b, a);
        V(x1, y0, r, g, b, a);
        V(x0, y1, r, g, b, a);
        V(x1, y0, r, g, b, a);
        V(x0, y0, r, g, b, a);
    }

    static void Line(float ax, float ay, float bx, float by, float thick, float r, float g, float b, float a)
    {
        if (boxFloats + 8 * 6 > boxes.Length) Flush();
        float dx = bx - ax;
        float dy = by - ay;
        float len = MathF.Sqrt(dx * dx + dy * dy);
        if (len < 0.0001f) return;
        float nx = -dy / len * thick * 0.5f;
        float ny = dx / len * thick * 0.5f;
        V(ax + nx, ay + ny, r, g, b, a);
        V(bx + nx, by + ny, r, g, b, a);
        V(bx - nx, by - ny, r, g, b, a);
        V(ax + nx, ay + ny, r, g, b, a);
        V(bx - nx, by - ny, r, g, b, a);
        V(ax - nx, ay - ny, r, g, b, a);
    }

    static float Clamp(float v, float lo, float hi)
    {
        if (v < lo) return lo;
        if (v > hi) return hi;
        return v;
    }

    // One picture of the simulation at `step`, with the player at (px, py). Returns 1 once MaxShots pictures are saved.
    public static int Frame(int step, float px, float py)
    {
        if (!ready || step % ShotEvery != 0) return 0;
        if (shots >= MaxShots) return 1;
        float clock = step * Cfg.Dt;
        float halfW = HalfHeight * Width / Height;
        // follow the player sideways; the vertical camera stays on the level (it is exactly as tall as the screen)
        float cx = Clamp(px, Level.MinX() + halfW, Level.MaxX() - halfW);
        if (Level.MaxX() - Level.MinX() < halfW * 2f) cx = (Level.MinX() + Level.MaxX()) * 0.5f;
        float cy = SceneryData.LevelHeight * 0.5f;
        GFX.Camera(cx, cy, HalfHeight, 0.05f, 0.13f, 0.24f);
        GFX.Draw(none, 0);                          // starts the frame (nothing in the sprite batch)

        float camLeft = cx - halfW;                 // cells from the level's left edge
        float camTop = SceneryData.LevelHeight - (cy + HalfHeight);
        Scenery.Draw(false, camLeft, camTop, clock);

        for (int i = 0; i < Level.SpikeCount; i++)
            Box(Level.Spike(i, 0) + Level.Spike(i, 2) * 0.5f, Level.Spike(i, 1) + Level.Spike(i, 3) * 0.35f, Level.Spike(i, 2), Level.Spike(i, 3) * 0.7f, 0.95f, 0.35f, 0.4f, 1f);
        for (int i = 0; i < Level.CrumblyCount; i++)
        {
            float al = Shared.CrumblyAlpha(i);
            if (al > 0.02f)
                Box(Level.CrumblyTile(i, 0) + 0.5f, Level.CrumblyTile(i, 1) + 0.5f, Level.CrumblyTile(i, 2), Level.CrumblyTile(i, 3), 0.85f, 0.7f, 0.5f, al);
        }
        for (int i = 0; i < Level.SaveCount; i++)
        {
            float tt = 0.55f;
            if (Shared.SaveTouched(i)) tt = 1f;
            Box(Level.Save(i, 0), Level.Save(i, 1) + 0.7f, 0.5f, 1.4f, 0.4f * tt, 0.9f * tt, 0.7f * tt, 1f);
        }
        for (int i = 0; i < Level.GemCount; i++)
        {
            int st = Shared.GemState(i);
            if (st == 1) continue;                  // picked up, not saved yet: hidden, like the Unity game
            float a = 1f;
            if (st == 2) a = 0.25f;                 // saved: a faint ghost
            Box(Level.Gem(i, 0), Level.Gem(i, 1), 0.5f, 0.5f, 1f, 0.9f, 0.3f, a);
        }
        for (int i = 0; i < Level.ShooterCount; i++)
            Box(Level.Shooter(i, 0), Level.Shooter(i, 1), 0.5f, 0.5f, 0.9f, 0.3f, 0.3f, 1f);
        Box(Level.GoalX(), Level.GoalY(), 1.4f, 2f, 1f, 0.8f, 0.2f, 0.6f);
        for (int i = 0; i < Shared.EnemyCount(); i++)
        {
            if (!Shared.EnemyAlive(i)) continue;
            int kind = Shared.EnemyKind(i);
            Box(Shared.EnemyX(i), Shared.EnemyY(i), EnemyCfg.ColliderW(kind), EnemyCfg.ColliderH(kind), 0.9f, 0.45f, 0.2f, 1f);
        }
        if (Shared.LassoActive) Line(px, py, Shared.LassoTipX, Shared.LassoTipY, 0.08f, 0.95f, 0.9f, 0.8f, 1f);
        Box(px, py, Cfg.ColliderW, Cfg.ColliderH, 0.3f, 0.9f, 0.4f, 1f);
        Flush();

        Scenery.Draw(true, camLeft, camTop, clock);
        GFX.SaveFrame(shots);
        shots++;
        return 0;
    }
}
