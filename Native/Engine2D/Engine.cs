// Engine: the 2D runtime (Prowl.Core2D) as a flat, handle-based C API, for a host that is not C#: prowl.py calls it through ctypes.
//
// This file is translated to C with the engine by CC# (tools/prowl2d_so.py) and built into libprowl2d.so; the functions below become the exported
// p2d_* functions of Native/Engine2D/engine_exports.c. So every signature here is ints and floats only (nothing a ctypes caller would have to build or free),
// a node is its slot index in the scene (-1: none), and nothing throws. The subset's limits apply (tools/ccsharp/README.md): no strings, no arrays across
// the boundary, one Scene2D per process. A node index, like any Node in this runtime, names whatever reuses its slot once the node is destroyed.
//
// The renderer (Native/Gfx2D) is not wrapped here: libprowl2d.so exports the gfx_* functions itself (textures, triangles, the window), so a host can draw its own
// things (a tile map, sprite frames) in the same frame as the scene's sprites.
using System;
using Prowl.Core2D;
using Prowl.Native.Box2D;
using Prowl.Native.Gfx2D;

static class Engine
{
    static Scene2D scene;
    static int ready;
    static int sprites;
    static Rigidbody2D[] bodies;           // a node's rigidbody by node index (set by AddBody), for velocities and impulses
    static Shatter2D blaster;              // only used for its AddExplosionForce
    static float[] shared;                 // the scripts' common numbers (GetGlobal / SetGlobal): what the C# sample keeps in a static class
    static float rayX;
    static float rayY;

    static Rigidbody2D BodyAt(int i) { return bodies[i]; }
    static void SetBodyAt(int i, Rigidbody2D rb) { bodies[i] = rb; }

    /// <summary>Bump when a function below changes its meaning: the host checks it.</summary>
    public static int Version() { return 5; }

    // ---- the process: renderer and scene -------------------------------------------------------------------------------------

    /// <summary>Makes the renderer's offscreen picture (width x height) and the scene. 1 if it worked, 0 if there is no GLES 3.1.</summary>
    public static int Init(int width, int height)
    {
        if (ready != 0) return 1;
        if (GFX.Init(width, height) == 0) return 0;
        if (scene == null)                    // the scene is an arena class of capacity 1: a second `new Scene2D()` would have no slot, so Init after Shutdown reuses it
        {
            Scripts.Init();
            Input2D.Init();
            scene = new Scene2D();
            bodies = new Rigidbody2D[CoreLimits.Nodes];
            blaster = new Shatter2D(scene, 1u);
            shared = new float[256];
        }
        ready = 1;
        return 1;
    }

    public static void Shutdown()
    {
        if (ready == 0) return;
        GFX.Shutdown();
        ready = 0;
    }

    public static void Camera(float x, float y, float halfHeight, float r, float g, float b)
    {
        GFX.Camera(x, y, halfHeight, r, g, b);
    }

    // ---- nodes -----------------------------------------------------------------------------------------------------------------

    /// <summary>A new root node: its index, or -1 if there is no room (CoreLimits.Nodes).</summary>
    public static int NewNode()
    {
        if (ready == 0) return -1;
        Node n = scene.NewNode(null);
        if (n == null) return -1;
        SetBodyAt(n.Index, null);
        return n.Index;
    }

    public static int NodeCount()
    {
        if (ready == 0) return 0;
        return scene.NodeCount;
    }

    public static void SetPos(int node, float x, float y)
    {
        if (ready == 0) return;
        Node n = scene.NodeAt(node);
        if (n == null) return;
        n.SetPosition(x, y);
    }

    public static void SetAngle(int node, float radians)
    {
        if (ready == 0) return;
        Node n = scene.NodeAt(node);
        if (n == null) return;
        n.SetAngle(radians);
    }

    public static void SetScale(int node, float sx, float sy)
    {
        if (ready == 0) return;
        Node n = scene.NodeAt(node);
        if (n == null) return;
        n.SetScale(sx, sy);
    }

    public static float NodeX(int node)
    {
        if (ready == 0) return 0f;
        Node n = scene.NodeAt(node);
        if (n == null) return 0f;
        return n.WorldX();
    }

    public static float NodeY(int node)
    {
        if (ready == 0) return 0f;
        Node n = scene.NodeAt(node);
        if (n == null) return 0f;
        return n.WorldY();
    }

    public static float NodeAngle(int node)
    {
        if (ready == 0) return 0f;
        Node n = scene.NodeAt(node);
        if (n == null) return 0f;
        return n.WorldAngle();
    }

    public static void DestroyNode(int node)
    {
        if (ready == 0) return;
        Node n = scene.NodeAt(node);
        if (n == null) return;
        scene.Destroy(n);
    }

    /// <summary>Destroys every node (the scene itself stays: there is one per process).</summary>
    public static void Clear()
    {
        if (ready == 0) return;
        int high = scene.NodeHighWater;
        for (int i = 0; i < high; i++)
        {
            Node n = scene.NodeAt(i);
            if (n != null) scene.Destroy(n);
        }
        for (int g = 0; g < 256; g++) shared[g] = 0f;
        scene.SetGravity(0f, -9.81f);
        // destroyed nodes are freed at the end of a frame: run one empty one so their slots come back before the next NewNode
        Scripts.Tick(scene, 1f / 60f);
    }

    // ---- components ------------------------------------------------------------------------------------------------------------

    /// <summary>A box or disc (shape 0 or 1: GFX_SHAPE_BOX, GFX_SHAPE_DISC) of the given full size and tint on a node. 1 if it was added.</summary>
    public static int AddSprite(int node, int shape, float width, float height, float r, float g, float b)
    {
        if (ready == 0) return 0;
        Node n = scene.NodeAt(node);
        if (n == null) return 0;
        SpriteRenderer2D s = scene.AddSprite(n, shape, width, height, r, g, b);
        if (s == null) return 0;
        return 1;
    }

    /// <summary>A rigidbody: bodyType 0 static, 1 kinematic, 2 dynamic (PB2_BODY_*). 1 if it was added.</summary>
    public static int AddBody(int node, int bodyType)
    {
        if (ready == 0) return 0;
        Node n = scene.NodeAt(node);
        if (n == null) return 0;
        Rigidbody2D rb = scene.AddRigidbody(n, bodyType);
        if (rb == null) return 0;
        SetBodyAt(node, rb);
        return 1;
    }

    /// <summary>A rigidbody that does not rotate (freezeRotation 1: a character) and has the given gravity scale. 1 if it was added.</summary>
    public static int AddBodyEx(int node, int bodyType, int freezeRotation, float gravityScale)
    {
        if (ready == 0) return 0;
        Node n = scene.NodeAt(node);
        if (n == null) return 0;
        Rigidbody2D rb = scene.NewRigidbody(n, bodyType);
        if (rb == null) return 0;
        rb.FreezeRotation = freezeRotation != 0;
        rb.GravityScale = gravityScale;
        scene.Finish(rb.Self);
        SetBodyAt(node, rb);
        return 1;
    }

    public static int AddBox(int node, float width, float height)
    {
        if (ready == 0) return 0;
        Node n = scene.NodeAt(node);
        if (n == null) return 0;
        Collider2D c = scene.AddBoxCollider(n, width, height);
        if (c == null) return 0;
        return 1;
    }

    /// <summary>A box collider with the given friction (0: slides along walls).</summary>
    public static int AddBoxEx(int node, float width, float height, float friction)
    {
        if (ready == 0) return 0;
        Node n = scene.NodeAt(node);
        if (n == null) return 0;
        Collider2D c = scene.NewBoxCollider(n, width, height);
        if (c == null) return 0;
        c.Friction = friction;
        scene.Finish(c.Self);
        return 1;
    }

    /// <summary>A box that is a trigger (nothing bumps into it, but a probe over its layer finds it: a vine to climb).</summary>
    public static int AddBoxTrigger(int node, float width, float height)
    {
        if (ready == 0) return 0;
        Node n = scene.NodeAt(node);
        if (n == null) return 0;
        Collider2D c = scene.NewBoxCollider(n, width, height);
        if (c == null) return 0;
        c.IsTrigger = true;
        scene.Finish(c.Self);
        return 1;
    }

    public static int AddCircle(int node, float radius)
    {
        if (ready == 0) return 0;
        Node n = scene.NodeAt(node);
        if (n == null) return 0;
        Collider2D c = scene.AddCircleCollider(n, radius);
        if (c == null) return 0;
        return 1;
    }

    /// <summary>Sets a body's linear velocity (units per second).</summary>
    public static void SetVelocity(int node, float vx, float vy)
    {
        if (ready == 0 || node < 0 || node >= CoreLimits.Nodes) return;
        Rigidbody2D rb = BodyAt(node);
        if (rb == null || scene.NodeAt(node) == null) return;
        rb.SetVelocity(vx, vy);
    }

    /// <summary>Applies an instant impulse (mass times velocity change) to a body.</summary>
    public static void Impulse(int node, float ix, float iy)
    {
        if (ready == 0 || node < 0 || node >= CoreLimits.Nodes) return;
        Rigidbody2D rb = BodyAt(node);
        if (rb == null || scene.NodeAt(node) == null) return;
        rb.AddImpulse(ix, iy);
    }

    public static float VelocityX(int node)
    {
        if (ready == 0 || node < 0 || node >= CoreLimits.Nodes) return 0f;
        Rigidbody2D rb = BodyAt(node);
        if (rb == null || scene.NodeAt(node) == null) return 0f;
        return rb.VelocityX();
    }

    public static float VelocityY(int node)
    {
        if (ready == 0 || node < 0 || node >= CoreLimits.Nodes) return 0f;
        Rigidbody2D rb = BodyAt(node);
        if (rb == null || scene.NodeAt(node) == null) return 0f;
        return rb.VelocityY();
    }

    /// <summary>An explosion at (x, y): pushes every body within radius away, the more the closer (Shatter2D.AddExplosionForce). Returns how many it pushed.</summary>
    public static int Blast(float x, float y, float radius, float force)
    {
        if (ready == 0) return 0;
        return blaster.AddExplosionForce(x, y, radius, force, 0f);
    }

    public static void Gravity(float x, float y)
    {
        if (ready == 0) return;
        scene.SetGravity(x, y);
    }

    // ---- scripts and input -----------------------------------------------------------------------------------------------------

    /// <summary>How many [Script] classes this library was built with (the editor's Build puts the project's scripts in, in the order of its manifest).</summary>
    public static int ScriptCount()
    {
        return ScriptTable.Count();
    }

    /// <summary>Adds the script with this number (its place in the manifest) to a node. 1 if it was added, 0 if the node is gone, the number is wrong or all of its instances are in use.</summary>
    public static int AttachScript(int node, int script)
    {
        if (ready == 0) return 0;
        Node n = scene.NodeAt(node);
        if (n == null) return 0;
        return ScriptTable.Add(n, script);
    }

    /// <summary>A key went down (1) or up (0): the codes are the viewport's (gfx2d.h), which are capital letters and digits as characters.</summary>
    public static void SetKey(int key, int down)
    {
        Input2D.SetKey(key, down);
    }

    /// <summary>The mouse in world units, and which buttons are held (bit 0 left, 1 middle, 2 right).</summary>
    public static void SetMouse(float x, float y, int buttons)
    {
        Input2D.SetMouse(x, y, buttons);
    }

    /// <summary>1 while the node exists (it was made, and not destroyed), else 0.</summary>
    public static int NodeAlive(int node)
    {
        if (ready == 0) return 0;
        if (scene.NodeAt(node) == null) return 0;
        return 1;
    }

    /// <summary>A number the game keeps on a node: what kind of thing it is, or a message to the scripts that look (0 until it is set).</summary>
    public static void SetTag(int node, int tag)
    {
        if (ready == 0) return;
        Node n = scene.NodeAt(node);
        if (n == null) return;
        n.Tag = tag;
    }

    /// <summary>The node's tag, or -1 if there is no such node: a script that scans the nodes for one kind of thing asks this.</summary>
    public static int GetTag(int node)
    {
        if (ready == 0) return -1;
        Node n = scene.NodeAt(node);
        if (n == null) return -1;
        return n.Tag;
    }

    /// <summary>How many node slots have been used (the highest index plus one): the range a scan of the nodes covers.</summary>
    public static int NodeSlots()
    {
        if (ready == 0) return 0;
        return scene.NodeHighWater;
    }

    // ---- what scripts that are not C# need to look around and to talk to each other --------------------------------------------------

    /// <summary>A number every script can read and write (index 0..255), 0 at the start of a play: the scripts' common memory, in place of a C# static class.</summary>
    public static void SetGlobal(int index, float value)
    {
        if (ready == 0 || index < 0 || index >= 256) return;
        shared[index] = value;
    }

    public static float GetGlobal(int index)
    {
        if (ready == 0 || index < 0 || index >= 256) return 0f;
        return shared[index];
    }

    /// <summary>The physics layer (0..31) of the node's colliders: set it before adding them. Layer 0 is what the editor's walls are.</summary>
    public static void SetLayer(int node, int layer)
    {
        if (ready == 0) return;
        Node n = scene.NodeAt(node);
        if (n == null) return;
        n.Layer = layer;
    }

    /// <summary>A node's collider (its first), by the number a ray reports, or -1 if it has none.</summary>
    public static int ColliderOf(int node)
    {
        if (ready == 0) return -1;
        Node n = scene.NodeAt(node);
        if (n == null) return -1;
        Component c = scene.Find(n, ComponentKind.BoxCollider2D);
        if (c == null) c = scene.Find(n, ComponentKind.CircleCollider2D);
        if (c == null || c.Collider == null) return -1;
        return c.Collider.ColliderIndex;
    }

    /// <summary>A ray from (ox, oy) along (dx, dy), a unit direction, over layers in `mask` (bit n = layer n): the collider it hits first, or -1; where is RayX / RayY.</summary>
    public static int Raycast(float ox, float oy, float dx, float dy, float distance, int mask)
    {
        if (ready == 0) return -1;
        int hit = scene.Physics.Sim.Raycast(ox, oy, dx, dy, distance, (uint)mask, false);
        if (hit >= 0)
        {
            rayX = scene.Physics.Sim.HitX;
            rayY = scene.Physics.Sim.HitY;
        }
        return hit;
    }

    public static float RayX() { return rayX; }

    public static float RayY() { return rayY; }

    /// <summary>How many colliders on the layers in `mask` overlap the box centred at (cx, cy) with half sizes (hw, hh).</summary>
    public static int OverlapBox(float cx, float cy, float hw, float hh, int mask)
    {
        if (ready == 0) return 0;
        return scene.Physics.Sim.OverlapBox(cx, cy, hw, hh, 0f, (uint)mask, true);
    }

    /// <summary>Switches a node (and what is on it) off or on: an inactive node has no collisions, no callbacks and is not drawn.</summary>
    public static void SetActive(int node, int active)
    {
        if (ready == 0) return;
        Node n = scene.NodeAt(node);
        if (n == null) return;
        scene.SetActive(n, active != 0);
    }

    public static int NodeActive(int node)
    {
        if (ready == 0) return 0;
        Node n = scene.NodeAt(node);
        if (n == null) return 0;
        if (n.ActiveInHierarchy) return 1;
        return 0;
    }

    /// <summary>What a node looks like, for the host to draw: field 0 shape (-1: no sprite), 1 width, 2 height (the scale counted), 3 red, 4 green, 5 blue, 6 alpha.</summary>
    public static float SpriteInfo(int node, int field)
    {
        if (ready == 0) return -1f;
        Node n = scene.NodeAt(node);
        if (n == null) return -1f;
        Component c = scene.Find(n, ComponentKind.SpriteRenderer2D);
        if (c == null || c.Sprite == null) return -1f;
        SpriteRenderer2D s = c.Sprite;
        if (field == 0) return s.Shape;
        if (field == 1) return s.Width * n.LossyScaleX();
        if (field == 2) return s.Height * n.LossyScaleY();
        if (field == 3) return s.R;
        if (field == 4) return s.G;
        if (field == 5) return s.B;
        return s.A;
    }

    public static float MathSqrt(float x) { return MathF.Sqrt(x); }

    public static float MathSin(float x) { return MathF.Sin(x); }

    public static float MathCos(float x) { return MathF.Cos(x); }

    public static float MathAtan2(float y, float x) { return MathF.Atan2(y, x); }

    /// <summary>1 while the key is held (the codes of SetKey), else 0: what a script that is not C# asks.</summary>
    public static int KeyDown(int key)
    {
        if (Input2D.Key(key)) return 1;
        return 0;
    }

    /// <summary>1 while the mouse button (0 left, 1 middle, 2 right) is held, else 0.</summary>
    public static int MouseDown(int button)
    {
        if (Input2D.MouseDown(button)) return 1;
        return 0;
    }

    /// <summary>The mouse's place in world units.</summary>
    public static float MouseWorldX() { return Input2D.MouseX; }

    public static float MouseWorldY() { return Input2D.MouseY; }

    /// <summary>Lets go of every key and button (the play mode starts or stops).</summary>
    public static void ClearInput()
    {
        Input2D.Clear();
    }

    // ---- a frame ---------------------------------------------------------------------------------------------------------------

    /// <summary>Advances the scene by dt seconds: the engine's fixed-step loop, with the frame's callbacks and physics.</summary>
    public static void Step(float dt)
    {
        if (ready == 0) return;
        Scripts.Tick(scene, dt);
    }

    /// <summary>Draws the scene's sprites into the renderer's picture (it clears it first). Returns how many it drew.</summary>
    public static int Draw()
    {
        if (ready == 0) return 0;
        sprites = GFX.Draw(scene.Render.DrawData, scene.CollectSprites());
        return sprites;
    }

    // The translator needs an entry point; the library has none of its own (its host calls the functions above), so this one only proves it links.
    public static int Main()
    {
        if (Init(64, 64) == 0) return 0;      // no GLES here is not a failure of the build
        int n = NewNode();
        AddSprite(n, 0, 1f, 1f, 1f, 1f, 1f);
        Draw();
        Shutdown();
        return 0;
    }
}
