// The node conformance tier compiles Node.cs on its own (see ccsharp_scan.py, CONFORMANCE "node"): the hierarchy and the transforms, with nothing of the
// scene or the physics. Node's Unity-named members (gameObject.SetActive, Destroy, GetComponent, ...) reach the scene, so the tier is given these empty
// stand-ins for the few scene types they name. They are never called by NodeConformance: they only let Node.cs bind, as the real ones do for the
// lifecycle and physics tiers (which compile the real Scene2D, Component and the rest).
namespace Prowl.Core2D
{
    internal static class ComponentKind
    {
        public const int Rigidbody2D = 1;
        public const int SpriteRenderer2D = 4;
    }

    [MaxInstances(1)]
    internal sealed class Rigidbody2D
    {
        public int Unused;
    }

    [MaxInstances(1)]
    internal sealed class Collider2D
    {
        public int Unused;
    }

    [MaxInstances(1)]
    internal sealed class SpriteRenderer2D
    {
        public int Unused;
    }

    [MaxInstances(1)]
    internal sealed class Component
    {
        public int Kind;
        public Node Node;
        public Component NextOnNode;
        public Rigidbody2D Body;
        public Collider2D Collider;
        public SpriteRenderer2D Sprite;
        public bool Destroyed;
    }

    [MaxInstances(1)]
    internal sealed class Scene2D
    {
        public static Scene2D Current;

        public bool SetParent(Node n, Node parent, bool keepWorld) { return false; }
        public void SetActive(Node n, bool active) { }
        public void Destroy(Node n) { }
        public Component Find(Node n, int kind) { return null; }
        public Component FirstComponent(Node n) { return null; }
    }
}
