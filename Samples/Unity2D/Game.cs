// Unity2D: Headless2D's ball and floor, written the way a Unity script reads. `using UnityEngine;` is what turns the Unity-style API on (Vector2, Vector3,
// Quaternion, Mathf, Time, Debug, Physics2D); the members with Unity's names on Node, Rigidbody2D, Collider2D and Collision2D need only the value types.
//
// Nothing here is Unity's own code: `transform`, `gameObject` and the callbacks are plain members of a [Script] class. The script generator sets the two
// fields when they are declared, and calls OnCollisionEnter2D as it calls OnCollisionBegin2D (Unity's name for it).
//
// It is also written so that the C build can translate it: no operators (`a + b` on a Vector2 is Vector2.Add(a, b) here; with `#define UNITY_NATIVE_OPERATORS`
// in Vector2.cs it could be `a + b`), a struct is built into a local before it is passed on, and a float is printed as an int. The same source runs on .NET
// and as a native executable, and the output must match: `python3 build.py player -- Samples/Unity2D --verify --run`.
using System;
using UnityEngine;
using Prowl.Core2D;
using Prowl.Native.Box2D;

[Script, MaxInstances(4)]
class Bouncer
{
    public Component Self;
    public Node transform;                  // set by the generator, as MonoBehaviour.transform is
    public Node gameObject;
    public int Hits;
    public float BestUp;                    // the largest upward normal seen at a landing: 1 for a flat floor
    public int Layer;
    public float Seconds;

    public void Reset() { Hits = 0; BestUp = 0f; Layer = -1; Seconds = 0f; }

    public void Start()
    {
        Rigidbody2D rb = transform.rigidbody2D;       // Unity: GetComponent<Rigidbody2D>() (that one is .NET only)
        rb.gravityScale = 2f;                         // takes effect at once on the body
        Debug.Log("start: gravityScale " + Mathf.RoundToInt(rb.gravityScale * 10f));
    }

    public void Update()
    {
        Seconds += Time.deltaTime;
    }

    public void OnCollisionEnter2D(Collision2D collision)
    {
        Hits++;
        ContactPoint2D contact = collision.GetContact(0);
        Vector2 normal = contact.normal;
        if (normal.y > BestUp) BestUp = normal.y;
        Layer = collision.gameObject.layer;           // the other object's layer
    }
}

static class Game
{
    static int s_failed;

    static void Check(string what, bool ok)
    {
        if (ok)
        {
            Console.WriteLine("ok   " + what);
            return;
        }
        s_failed++;
        Console.WriteLine("FAIL " + what);
    }

    public static int Main()
    {
        Scripts.Init();
        Scene2D scene = new Scene2D();

        // ---- the world, built with Unity's names where they exist
        Vector2 g = Physics2D.gravity;
        Check("default gravity is Unity's (0, -9.81)", Mathf.RoundToInt(g.y * 100f) == -981 && Mathf.RoundToInt(g.x) == 0);

        Node ground = scene.NewNode(null);
        Vector3 groundAt = new Vector3(0f, -0.5f, 0f);
        ground.position = groundAt;                   // Unity: transform.position = ...
        ground.layer = 8;                             // Unity: gameObject.layer = ...
        scene.AddBoxCollider(ground, 100f, 1f);       // no rigidbody: static; its top is at y = 0

        Node ball = scene.NewNode(null);
        Vector3 ballAt = new Vector3(0f, 5f, 0f);
        ball.position = ballAt;
        scene.AddRigidbody(ball, PB2.BodyDynamic);
        scene.AddCircleCollider(ball, 0.5f);
        Bouncer script = Scripts.AddBouncer(ball);

        Check("the script was given its node", script.transform == ball && script.gameObject == ball);
        Check("position reads back", Mathf.RoundToInt(ball.position.y * 100f) == 500);

        // ---- play: 4 seconds of frames
        for (int frame = 0; frame < 240; frame++)
        {
            Scripts.Tick(scene, 1f / 60f);
        }
        int rest = Mathf.RoundToInt(ball.position.y * 1000f);
        Console.WriteLine("rest y*1000=" + rest + " hits=" + script.Hits + " frames=" + Time.frameCount);
        Check("it came to rest half a unit above the floor", rest > 450 && rest < 550);
        Check("it landed at least once, on a flat floor", script.Hits >= 1 && script.BestUp > 0.9f);
        Check("it heard the floor's layer", script.Layer == 8);
        Check("Time.frameCount counted the frames", Time.frameCount == 240);
        int ms = Mathf.RoundToInt(Time.time * 1000f);
        Check("Time.time is the game's seconds", ms > 3990 && ms < 4010);
        int scriptMs = Mathf.RoundToInt(script.Seconds * 1000f);
        Check("Update saw Time.deltaTime", scriptMs > 3990 && scriptMs < 4010);

        // ---- Time.timeScale = 0 stops the game, as in Unity
        int before = Mathf.RoundToInt(ball.position.y * 1000f);
        Time.timeScale = 0f;
        for (int frame = 0; frame < 30; frame++)
        {
            Scripts.Tick(scene, 1f / 60f);
        }
        Time.timeScale = 1f;
        int after = Mathf.RoundToInt(ball.position.y * 1000f);
        int pausedMs = Mathf.RoundToInt(script.Seconds * 1000f);
        Check("paused: nothing moved, nothing counted", before == after && pausedMs == scriptMs);

        // ---- a Transform's members
        Node parent = scene.NewNode(null);
        Vector3 parentAt = new Vector3(1f, 2f, 0f);
        parent.position = parentAt;
        Vector3 turn = new Vector3(0f, 0f, 90f);
        parent.eulerAngles = turn;                    // 90 degrees, counter-clockwise
        Node child = scene.NewNode(parent);
        Vector3 childLocal = new Vector3(1f, 0f, 0f);
        child.localPosition = childLocal;
        Check("a child of a turned parent is where Unity puts it",
              Mathf.RoundToInt(child.position.x * 100f) == 100 && Mathf.RoundToInt(child.position.y * 100f) == 300);

        Vector3 step = new Vector3(0f, 1f, 0f);
        child.Translate(step);                        // along the child's own axes: up is the parent's -x
        Check("Translate moves along the node's own axes", Mathf.RoundToInt(child.position.x * 100f) == 0 && Mathf.RoundToInt(child.position.y * 100f) == 300);

        Quaternion q = Quaternion.Euler(0f, 0f, 90f);
        Vector3 e = q.eulerAngles;
        Check("Quaternion.Euler and eulerAngles agree", Mathf.RoundToInt(e.z) == 90 && Mathf.RoundToInt(e.x) == 0);
        Check("the node's rotation is a quaternion about z", Mathf.RoundToInt(parent.rotation.z * 1000f) == 707);

        // ---- the maths
        Vector2 a = new Vector2(0f, 0f);
        Vector2 b = new Vector2(3f, 4f);
        Check("Vector2.Distance", Mathf.RoundToInt(Vector2.Distance(a, b) * 100f) == 500);
        Vector2 mid = Vector2.Lerp(a, b, 0.5f);
        Check("Vector2.Lerp", Mathf.RoundToInt(mid.x * 100f) == 150 && Mathf.RoundToInt(mid.y * 100f) == 200);
        Vector2 sum = Vector2.Add(a, b);              // `a + b` on .NET, and in C with UNITY_NATIVE_OPERATORS
        Check("Vector2.magnitude", Mathf.RoundToInt(sum.magnitude * 100f) == 500);
        Check("Mathf.Round goes to even", Mathf.RoundToInt(Mathf.Round(2.5f)) == 2 && Mathf.RoundToInt(Mathf.Round(3.5f)) == 4);
        Check("Mathf.DeltaAngle goes the short way", Mathf.RoundToInt(Mathf.DeltaAngle(350f, 10f)) == 20);
        Check("Mathf.Clamp", Mathf.RoundToInt(Mathf.Clamp(7f, 0f, 5f)) == 5);

        Console.WriteLine("failed checks: " + s_failed);
        return s_failed == 0 ? 0 : 1;
    }
}
