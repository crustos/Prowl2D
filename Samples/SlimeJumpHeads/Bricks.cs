using System;
using Prowl.Core2D;
using Prowl.Native.Box2D;

// A head that is shot comes apart into bricks: small boxes thrown out of where it was, which fall, bounce on the rock and lie there a while, then go (DebrisScript).
// They are on the debris layer, so they meet the walls and the crates and nothing else: the slime and its shots pass through them.
static class Bricks
{
    public const int Tag = 10;
    public static int Made;

    public static int CountFor(int kind) { return kind == 5 ? 14 : 8; }

    // `count` bricks from (x, y), thrown a little away from the way the shot was going (dx, dy)
    public static void Burst(Scene2D scene, float x, float y, int count, float dx, float dy)
    {
        float m = MathF.Sqrt(dx * dx + dy * dy);
        float pushX = 0f;
        float pushY = 0f;
        if (m > 0.001f) { pushX = dx / m * 2.5f; pushY = dy / m * 2.5f; }
        for (int i = 0; i < count; i++)
        {
            float bx = x + (Shared.Rand01() - 0.5f) * 1.2f;
            float by = y + (Shared.Rand01() - 0.5f) * 1.2f;
            Node n = scene.NewNode(null);
            if (n == null) return;
            n.SetPosition(bx, by);
            n.Layer = Layers.Debris;
            n.Tag = Tag;
            Rigidbody2D rb = scene.NewRigidbody(n, PB2.BodyDynamic);
            rb.LinearDamping = 0.2f;
            rb.AngularDamping = 0.5f;
            scene.Finish(rb.Self);
            Collider2D c = scene.NewBoxCollider(n, 0.42f, 0.22f);
            c.Friction = 0.6f;
            c.Bounciness = 0.25f;
            scene.Finish(c.Self);
            rb.SetVelocity((bx - x) * 6f + pushX + (Shared.Rand01() - 0.5f) * 3f, (by - y) * 6f + pushY + 3f + Shared.Rand01() * 3f);
            Scripts.AddDebrisScript(n);
            Made++;
        }
    }
}
