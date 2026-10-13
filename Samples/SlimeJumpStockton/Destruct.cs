using System;
using Prowl.Core2D;
using Prowl.Native.Box2D;
using Prowl.Runtime.Destruction2D;

// The world of SlimeJumpStockton: one terrain bitmap, a street of Stockton over a sewer, with falling sand and flowing water and sewage in it (PixelTerrain2D.EnableSand),
// and the things that break.
//
//   * The rock is the terrain's stone: 96 x 36 units at 8 pixels a unit (768 x 288 pixels, 8 x 3 chunks of 96 (the engine holds at most 64 chunks)): the street's slab and the sewer's bedrock, two brick
//     buildings with overhangs, and a sewer tunnel under the street (Level.cs). A bullet digs a 1.75-unit hole. Sand and water are pixels of the same bitmap: a pile of sand
//     is ground (the slime walks on it, it has colliders), water is not. The water that is in the sewer is sewage.
//   * Whatever is dug out lets what is above it move: a hole in the street lets what is on it run into the sewer, and a storm drain does that all the time.
//   * Crates and boulders (Shatter2D) are bodies a bullet detonates: they shatter into fragments, the blast pushes things away and digs a crater (a crate a big one),
//     and what is beside it goes off a moment later. A boulder also crumbles: a little sand is sprinkled where it was.
//   * Two things are sealed in rock, with a "plug" of rock that holds them back: a hopper of building sand in the first overhang and a water tank in the second. Shoot the
//     plug from the street and the contents fall.
//
// Everything runs from the game's loop (Step, once per fixed step, before Scripts.Tick), never from inside a script's callback.
static class Destruct
{
    public const int TagCrateBase = 200;           // item i has Tag TagCrateBase + i
    const float BlastRadius = 3.5f;
    const float BlastForce = 60f;
    const int ChainFuse = 12;                      // steps from one blast to the next
    const int Ppu = 8;                             // terrain pixels per unit
    const int PxW = 768;
    const int PxH = 288;
    const int CrateKind = 0;
    const int BoulderKind = 1;

    static PixelTerrain2D rock;
    static Shatter2D boom;
    static ExplodeOptions crateOpt;
    static ExplodeOptions rockOpt;
    static StampShape bulletHole;
    static StampShape crateHole;
    static StampShape boulderHole;
    static Node[] items;
    static int[] fuse;                             // -1 idle, -2 spent, otherwise steps until it detonates
    static int[] kind;
    static int itemCount;
    static float[] plugs;                          // x, y of each plug: a point inside the rock that closes a sealed bin or tank
    static int plugCount;
    static int frame;

    public static int Digs;
    public static int Detonations;
    public static int Fragments;
    public static int FragmentsGone;
    public static int BoulderCount;
    public static int RubbleGrains;

    static Node NodeAt(Node[] a, int i) { return a[i]; }
    static void SetNode(Node[] a, int i, Node n) { a[i] = n; }
    static int IntAt(int[] a, int i) { return a[i]; }
    static void SetInt(int[] a, int i, int v) { a[i] = v; }
    static float FloatAt(float[] a, int i) { return a[i]; }
    static void SetFloat(float[] a, int i, float v) { a[i] = v; }

    static int Px(float units) { return (int)(units * (float)Ppu + 0.5f); }

    public static PixelTerrain2D Terrain() { return rock; }

    // ---- building the street ---------------------------------------------------------------------------------------------------

    // what the rock looks like where it is: the street's asphalt (grey, with cracks), the brick of the buildings (running bond, with the odd painted-over patch: Stockton
    // has painted over its graffiti many times), and the concrete of the sewer
    static void RockPixel(int x, int y)
    {
        float wy = (float)y / (float)Ppu;
        float wx = (float)x / (float)Ppu;
        int h = (x * 7 + y * 13) % 5;
        if ((wy >= Level.StreetY - 0.4f && wy < Level.StreetY) || (wy < Level.SewerTop + 0.4f && wy >= Level.SewerTop))
        {
            if (wy >= Level.StreetY - 0.4f && y % 8 < 4 && wy >= Level.StreetY - 0.15f) { rock.SetPixel(x, y, 214, 176, 40, 255); return; }          // the walkway's edge: a hazard stripe
            rock.SetPixel(x, y, 128 + h * 3, 128 + h * 3, 122 + h * 3, 255);             // the walkway's concrete, and the underside of the slab
            return;
        }
        if (wy >= Level.StreetY)
        {
            // brick: courses 4 pixels high, bricks 8 wide, every other course shifted by half a brick; the mortar is a lighter grey
            int course = y / 4;
            int bx = (x + (course % 2) * 4) / 8;
            bool mortar = (y % 4 == 0) || ((x + (course % 2) * 4) % 8 == 0);
            if (mortar)
            {
                rock.SetPixel(x, y, 150 + h * 2, 140 + h * 2, 132 + h * 2, 255);
                return;
            }
            int v = (bx * 31 + course * 17) % 7;
            int patch = ((bx / 3) * 11 + (course / 3) * 7) % 17;                  // a patch of paint in one of several greys, now and then
            if (patch == 0) { rock.SetPixel(x, y, 118 + v * 4, 120 + v * 4, 124 + v * 4, 255); return; }
            if (patch == 1) { rock.SetPixel(x, y, 70 + v * 3, 96 + v * 4, 58 + v * 2, 255); return; }                // moss
            rock.SetPixel(x, y, 150 + v * 6 + h, 62 + v * 3, 48 + v * 2, 255);
            return;
        }
        int shade = h * 3 + ((y / 16) % 2) * 6;
        rock.SetPixel(x, y, 92 + shade, 94 + shade, 98 + shade, 255);                     // concrete and bedrock
    }

    static void Rock(float x0, float y0, float x1, float y1)
    {
        int ix0 = Px(x0), ix1 = Px(x1), iy0 = Px(y0), iy1 = Px(y1);
        for (int x = ix0; x < ix1; x++)
            for (int y = iy0; y < iy1; y++)
                RockPixel(x, y);
    }

    static void Air(float x0, float y0, float x1, float y1)
    {
        int ix0 = Px(x0), ix1 = Px(x1), iy0 = Px(y0), iy1 = Px(y1);
        for (int x = ix0; x < ix1; x++)
            for (int y = iy0; y < iy1; y++)
                rock.SetPixel(x, y, 0, 0, 0, 0);
    }

    static void Fill(float x0, float y0, float x1, float y1, int element)
    {
        int ix0 = Px(x0), ix1 = Px(x1), iy0 = Px(y0), iy1 = Px(y1);
        for (int x = ix0; x < ix1; x++)
            for (int y = iy0; y < iy1; y++)
                rock.AddElement(x, y, element);
    }

    static void AddPlug(float x, float y)
    {
        SetFloat(plugs, plugCount * 2, x);
        SetFloat(plugs, plugCount * 2 + 1, y);
        plugCount++;
    }

    public static void Init(Scene2D scene, int maxItems)
    {
        rock = new PixelTerrain2D(scene, PxW, PxH, 8, 3, (float)Ppu, 0f, 0f, PixelTerrain2D.Boxes);
        rock.PhysicsLayer = Layers.Wall;
        rock.Friction = 0f;                        // the slime does not catch on rock
        // the street's slab and the sewer's bedrock, from the first wall to the last
        Rock(0f, 0f, Level.Width, Level.StreetY);
        Air(Level.SideWall, Level.SewerFloor, Level.Width - Level.SideWall, Level.SewerTop);
        // the storm drain, and the Deep Water Channel: openings in the slab, down into the sewer
        for (int i = 0; i < Level.Drains; i++)
            Air(Level.DrainX0(i), Level.SewerTop - 0.1f, Level.DrainX1(i), Level.StreetY + 0.1f);
        Air(Level.ChannelX0, Level.SewerTop - 0.1f, Level.ChannelX1, Level.StreetY + 0.1f);
        Air(1.5f, Level.SewerTop - 0.1f, 3.0f, Level.StreetY + 0.1f);          // the pipe's gutter at the top left: its sewage falls straight into the sewer
        // the gantries over the channel (floating: hung from the sky, as far as the terrain is concerned)
        for (int i = 0; i < Level.Gantries; i++)
            Rock(Level.GantryX0(i), Level.GantryBottom(i), Level.GantryX1(i), Level.GantryTop(i));
        // the sealed things: a hopper of building sand in the first gantry and a tank of water in the second, each a cavity in the slab with a lid of rock 0.9 thick under it.
        // Shoot the lid from the street (the plug) and the contents fall into the channel
        plugs = new float[8];
        plugCount = 0;
        Air(Level.GantryX0(0) + 1f, Level.GantryBottom(0) + 0.9f, Level.GantryX1(0) - 1f, Level.GantryTop(0) - 0.8f);
        AddPlug((Level.GantryX0(0) + Level.GantryX1(0)) * 0.5f, Level.GantryBottom(0) + 0.45f);
        Air(Level.GantryX0(1) + 1f, Level.GantryBottom(1) + 0.9f, Level.GantryX1(1) - 1f, Level.GantryTop(1) - 0.8f);
        AddPlug((Level.GantryX0(1) + Level.GantryX1(1)) * 0.5f, Level.GantryBottom(1) + 0.45f);

        rock.Build();
        rock.EnableSand();
        rock.Sand.Seed(2024u);

        // the sand: the hopper's, and a dune on the street beside the drain
        Fill(Level.GantryX0(0) + 1f, Level.GantryBottom(0) + 0.9f, Level.GantryX1(0) - 1f, Level.GantryTop(0) - 0.8f, SandSim.Sand);
        int cx = Px(15f);
        int hw = Px(2.6f);
        int hmax = Px(2.2f);
        for (int x = cx - hw; x <= cx + hw; x++)
        {
            float t = (float)(x - cx) / (float)hw;
            int h = (int)((1f - t * t) * (float)hmax);
            for (int y = 0; y < h; y++) rock.AddElement(x, Px(Level.StreetY) + y, SandSim.Sand);
        }
        // the water: the tank's, and the sewage, a shallow river along the sewer and down in the channel; a sandbar in it
        Fill(Level.GantryX0(1) + 1f, Level.GantryBottom(1) + 0.9f, Level.GantryX1(1) - 1f, Level.GantryTop(1) - 0.8f, SandSim.Water);
        Fill(Level.SideWall, Level.SewerFloor, Level.Width - Level.SideWall, Level.SewerFloor + Level.SewageDepth, SandSim.Water);
        Fill(20f, Level.SewerFloor, 27f, Level.SewerFloor + 1.2f, SandSim.Sand);
        // let it settle before the slime comes: the sewage levels out, the dune finds its slope, and the colliders are made
        for (int i = 0; i < 300; i++)
        {
            rock.SandStep();
            rock.Update();
        }

        boom = new Shatter2D(scene, 1234u);
        crateOpt = new ExplodeOptions();
        crateOpt.Mode = Fracturer.Voronoi;
        crateOpt.ExtraPoints = 3;
        crateOpt.FragmentLayer = Layers.Debris;
        crateOpt.RenderLayer = 3;
        crateOpt.Texture = 1;
        crateOpt.R = 0.85f; crateOpt.G = 0.6f; crateOpt.B = 0.35f;
        rockOpt = new ExplodeOptions();
        rockOpt.Mode = Fracturer.Voronoi;
        rockOpt.ExtraPoints = 5;
        rockOpt.FragmentLayer = Layers.Debris;
        rockOpt.RenderLayer = 3;
        rockOpt.Texture = 1;
        rockOpt.R = 0.55f; rockOpt.G = 0.55f; rockOpt.B = 0.6f;
        bulletHole = StampShape.GenerateShapeRect(14, 10);         // 1.75 x 1.25 units, with straight sides
        crateHole = StampShape.GenerateShapeCircle(16);            // 4 units: a crate's crater
        boulderHole = StampShape.GenerateShapeCircle(9);           // 2.25

        items = new Node[maxItems + 1];
        fuse = new int[maxItems + 1];
        kind = new int[maxItems + 1];
        itemCount = 0;
        frame = 0;
    }

    // ---- the things that break ------------------------------------------------------------------------------------------------

    static void AddItem(Scene2D scene, float x, float y, float w, float h, int k, float r, float g, float b)
    {
        Node n = scene.NewNode(null);
        n.SetPosition(x, y);
        n.Layer = Layers.Crate;
        n.Tag = TagCrateBase + itemCount;
        scene.AddRigidbody(n, PB2.BodyDynamic);
        scene.AddBoxCollider(n, w, h);
        scene.AddSprite(n, SpriteRenderer2D.Box, w, h, r, g, b);
        SetNode(items, itemCount, n);
        SetInt(fuse, itemCount, -1);
        SetInt(kind, itemCount, k);
        itemCount++;
    }

    public static void AddCrate(Scene2D scene, float x, float y) { AddItem(scene, x, y, 1f, 1f, CrateKind, 0.8f, 0.55f, 0.3f); }

    public static void AddBoulder(Scene2D scene, float x, float y)
    {
        AddItem(scene, x, y, 1.7f, 1.4f, BoulderKind, 0.5f, 0.5f, 0.56f);
        BoulderCount++;
    }

    public static int ItemCount() { return itemCount; }
    public static bool ItemIsCrate(int i) { return IntAt(kind, i) == CrateKind; }
    // (a node is an arena slot: once an item is destroyed, its slot is handed to a fragment, which would pass for it: so an item that has gone off is marked spent)
    public static bool ItemLive(Scene2D scene, int i) { return IntAt(fuse, i) != -2 && scene.IsLive(NodeAt(items, i)); }
    public static float ItemX(int i) { return NodeAt(items, i).WorldX(); }
    public static float ItemY(int i) { return NodeAt(items, i).WorldY(); }

    public static void Queue(int i, int steps)
    {
        if (i < 0 || i >= itemCount) return;
        if (IntAt(fuse, i) < 0 && IntAt(fuse, i) != -2) SetInt(fuse, i, steps);
    }

    // ---- looking at the terrain ----------------------------------------------------------------------------------------------

    public static bool SolidAt(float wx, float wy)
    {
        int px = (int)(wx * (float)Ppu);
        int py = (int)(wy * (float)Ppu);
        if (wx < 0f || wy < 0f || px >= PxW || py >= PxH) return false;
        return rock.IsSolid(px, py);
    }

    public static bool WaterAt(float wx, float wy)
    {
        int px = (int)(wx * (float)Ppu);
        int py = (int)(wy * (float)Ppu);
        if (wx < 0f || wy < 0f || px >= PxW || py >= PxH) return false;
        return rock.Sand.ElementAt(px, py) == SandSim.Water;
    }

    public static int PlugCount() { return plugCount; }
    public static float PlugX(int i) { return FloatAt(plugs, i * 2); }
    public static float PlugY(int i) { return FloatAt(plugs, i * 2 + 1); }
    public static bool PlugClosed(int i) { return SolidAt(PlugX(i), PlugY(i)); }

    // grains of an element in a box of the world
    public static int Count(float x0, float y0, float x1, float y1, int element)
    {
        int n = 0;
        int ix0 = Px(x0), ix1 = Px(x1), iy0 = Px(y0), iy1 = Px(y1);
        if (ix0 < 0) ix0 = 0;
        if (iy0 < 0) iy0 = 0;
        if (ix1 > PxW) ix1 = PxW;
        if (iy1 > PxH) iy1 = PxH;
        for (int y = iy0; y < iy1; y++)
            for (int x = ix0; x < ix1; x++)
                if (rock.Sand.ElementAt(x, y) == element) n++;
        return n;
    }

    // the sewage is the water down in the sewer (below the street's slab); the rest of the water is on the street
    public static int Sewage() { return Count(0f, 0f, Level.Width, Level.SewerTop, SandSim.Water); }
    public static int StreetWater() { return Count(0f, Level.SewerTop, Level.Width, Level.Height, SandSim.Water); }
    public static int StreetSand() { return Count(0f, Level.StreetY - 0.2f, Level.Width, Level.Height, SandSim.Sand); }
    public static int SewerSand() { return Count(0f, 0f, Level.Width, Level.SewerTop, SandSim.Sand); }

    public static int GroundPixels()
    {
        int n = 0;
        for (int y = 0; y < PxH; y++)
            for (int x = 0; x < PxW; x++)
                if (rock.IsSolid(x, y)) n++;
        return n;
    }

    // what a terrain pixel is, for drawing it: 0 air, 1 rock, 2 sand, 3 water, 4 sewage
    const int InflowFrames = 1600;

    public static int Code(int x, int y)
    {
        int e = rock.Sand.ElementAt(x, y);
        if (e == SandSim.Sand) return 2;
        if (e == SandSim.Water)
        {
            float wx = (float)x / (float)Ppu;
            if ((float)y / (float)Ppu < Level.SewerTop) return 4;
            if (wx > 58f && wx < 70f) return 3;               // the water tank's, falling
            return 4;                                        // the rest above the sewer is sewage from the pipe
        }
        if (rock.IsSolid(x, y)) return 1;
        return 0;
    }

    public static int SandHash() { return (int)(rock.Sand.Hash() & 0x7fffffffu); }
    public static int AwakeCount() { return rock.Sand.AwakeChunks(); }

    // ---- breaking things ---------------------------------------------------------------------------------------------------------

    // a bullet struck something solid at (x, y), moving along (dx, dy) (a unit vector): if that is rock or sand, it digs
    public static bool BulletHitsDirt(float x, float y, float dx, float dy)
    {
        for (int k = 0; k < 10; k++)
        {
            float px = x + dx * (0.05f + 0.1f * k);
            float py = y + dy * (0.05f + 0.1f * k);
            if (SolidAt(px, py))
            {
                Dig(px, py, bulletHole, 7, 5);
                return true;
            }
        }
        return false;
    }

    static void Dig(float wx, float wy, StampShape shape, int offX, int offY)
    {
        int px = (int)(wx * (float)Ppu) - offX;
        int py = (int)(wy * (float)Ppu) - offY;
        if (rock.Paint(shape, px, py, true, 0, 0, 0)) Digs++;
    }

    // once per fixed step, before the physics step: the sand and water move, the colliders that changed are rebuilt, the fuses burn
    public static void Step(Scene2D scene)
    {
        frame++;
        // the inflows: sewage from a pipe at the top left (it runs along the walkway to the storm drains and down into the sewer), and sand from a chute over the dune in the first lot (once the slime is past it)
        if (frame < InflowFrames)
        {
            for (int k = 0; k < 6; k++)
                rock.AddElement(Px(1.7f) + k, Px(32.2f), SandSim.Water);
            if (frame >= 400 && frame < 1100)
                for (int k = 0; k < 3; k++)
                    rock.AddElement(Px(14.9f) + k, Px(32.4f), SandSim.Sand);
        }
        rock.SandStep();
        rock.Update();
        for (int i = 0; i < itemCount; i++)
        {
            int f = IntAt(fuse, i);
            if (f < 0) continue;
            if (f == 0) { Detonate(scene, i); continue; }
            SetInt(fuse, i, f - 1);
        }
    }

    static void Detonate(Scene2D scene, int i)
    {
        Node n = NodeAt(items, i);
        bool live = ItemLive(scene, i);
        int k = IntAt(kind, i);
        SetInt(fuse, i, -2);                                        // spent
        if (!live) return;
        float cx = n.WorldX();
        float cy = n.WorldY();
        int made = 0;
        if (k == BoulderKind) made = boom.Explode(n, rockOpt);
        else made = boom.Explode(n, crateOpt);
        Detonations++;
        Fragments += made;
        for (int f = 0; f < boom.Fragments.Count; f++)
        {
            Node frag = boom.Fragments[f];                              // (a list element cannot be passed straight into a call, in the C build)
            Scripts.AddDebrisScript(frag);
        }
        float radius = BlastRadius;
        float force = BlastForce;
        if (k == BoulderKind) { radius = 2.5f; force = 35f; }
        int pushed = boom.AddExplosionForce(cx, cy, radius, force, 0f);

        // the crater: a crate's is big enough to open a floor most of the way; a boulder crumbles into a little sand where it stood
        int rubble = 0;
        if (k == BoulderKind)
        {
            Dig(cx, cy - 0.2f, boulderHole, 9, 9);
            rubble = rock.Sprinkle((int)(cx * (float)Ppu), (int)((cy + 0.2f) * (float)Ppu), 7, SandSim.Sand);
            RubbleGrains += rubble;
        }
        else
            Dig(cx, cy - 0.3f, crateHole, 16, 16);

        // whatever is within reach goes off a little later
        int chained = 0;
        for (int j = 0; j < itemCount; j++)
        {
            if (j == i || IntAt(fuse, j) != -1) continue;
            if (!ItemLive(scene, j)) continue;
            Node o = NodeAt(items, j);
            float dx = o.WorldX() - cx;
            float dy = o.WorldY() - cy;
            if (dx * dx + dy * dy < radius * radius) { SetInt(fuse, j, ChainFuse); chained++; }
        }
        string what = "crate";
        if (k == BoulderKind) what = "boulder";
        string line = "boom step=" + frame + " " + what + "=" + i + " x*1000=" + (int)(cx * 1000f) + " y*1000=" + (int)(cy * 1000f) + " fragments=" + made + " pushed=" + pushed + " rubble=" + rubble + " chained=" + chained;
        Console.WriteLine(line);
    }

    public static void Shutdown()
    {
        rock.Destroy();
    }
}

// A fragment's lifetime: it lies there for a while, then goes (its body, collider and mesh with it), which also gives the scene's pools back.
[Script(Order = 30), MaxInstances(64)]
class DebrisScript
{
    public Component Self;
    float life;
    Scene2D scene;
    Node node;

    public void Start()
    {
        scene = Scene2D.Current;
        node = Self.Node;
        life = 2.5f;
    }

    public void FixedUpdate()
    {
        life -= Cfg.Dt;
        if (life > 0f) return;
        Destruct.FragmentsGone++;
        scene.Destroy(node);
    }
}
