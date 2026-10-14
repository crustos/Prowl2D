// This file is part of the Prowl Game Engine
// Licensed under the MIT License. See the LICENSE file in the project root for details.

using Prowl.Runtime.Physics2D;
using UnityEngine;

namespace Prowl.Core2D;

/// <summary>
/// The data of a BoxCollider2D or CircleCollider2D component. Its shape is made when the component is enabled, on the nearest enabled rigidbody
/// at or above its node, or on a static body of its own when there is none, and destroyed when it is disabled. Its values are read then.
/// A collider with no rigidbody is static: it is placed where its node is when it is enabled, and does not follow the node afterwards.
/// <para/>
/// This is also what a script is given in <c>OnTriggerEnter2D(Collider2D other)</c>: <see cref="Self"/> leads to the node and its other components.
/// </summary>
[MaxInstances(CoreLimits.Colliders)]
internal sealed class Collider2D
{
    public const int Box = 0;
    public const int Circle = 1;
    public const int Polygon = 2;
    public const int Terrain = 3;         // no shape of its own: a collider index and a static body at its node, for whoever owns it to build the shapes on (PixelTerrain2D)

    public Component Self;
    public int ShapeKind;                // Box, Circle, Polygon or Terrain
    public float SizeX, SizeY;           // a box's full width and height (the node's scale multiplies them)
    public float Radius;                 // a circle's
    public float[] Poly;                 // a polygon's points (x, y pairs) in the node's space, before its scale: convex, at most CoreLimits.MeshVertices of them
    public int PolyCount;
    public float OffsetX, OffsetY;       // the shape's centre, in the node's space
    public float Density;
    public float Friction;
    public float Bounciness;
    public bool IsTrigger;

    public int ColliderIndex;            // the slot in the simulation's registry, -1 while there is no shape
    public uint Shape;                   // the native shape
    public uint OwnBody;                 // the static body made for a collider with no rigidbody, else 0
    public Rigidbody2D Attached;         // the body the shape is on, null for an own static body

    public Collider2D()
    {
        Poly = new float[CoreLimits.MeshVertices * 2];
    }

    public void Reset(int shapeKind)
    {
        PolyCount = 0;
        Self = null;
        ShapeKind = shapeKind;
        SizeX = 1f;
        SizeY = 1f;
        Radius = 0.5f;
        OffsetX = 0f;
        OffsetY = 0f;
        Density = 1f;
        Friction = 0.4f;
        Bounciness = 0f;
        IsTrigger = false;
        ColliderIndex = -1;
        Shape = 0;
        OwnBody = 0;
        Attached = null;
    }

    // ---- Unity-named members -------------------------------------------------------------
    //
    // The collider's settings are read when it is enabled and its shape made (see above); unlike Unity, changing one on a live collider does nothing
    // until <see cref="ApplyChanges"/> makes the shape again (the one that Unity does for you).

    public Node gameObject { get { return Self.Node; } }
    public Node transform { get { return Self.Node; } }

    public bool isTrigger
    {
        get { return IsTrigger; }
        set { IsTrigger = value; }
    }

    /// <summary>The shape's centre, in the node's space.</summary>
    public Vector2 offset
    {
        get { return new Vector2(OffsetX, OffsetY); }
        set
        {
            OffsetX = value.x;
            OffsetY = value.y;
        }
    }

    /// <summary>A box's full width and height (the node's scale multiplies them).</summary>
    public Vector2 size
    {
        get { return new Vector2(SizeX, SizeY); }
        set
        {
            SizeX = value.x;
            SizeY = value.y;
        }
    }

    /// <summary>A circle's radius.</summary>
    public float radius
    {
        get { return Radius; }
        set { Radius = value; }
    }

    public float density
    {
        get { return Density; }
        set { Density = value; }
    }

    /// <summary>Unity keeps this on the collider's shared material.</summary>
    public float friction
    {
        get { return Friction; }
        set { Friction = value; }
    }

    /// <summary>Unity keeps this on the collider's shared material.</summary>
    public float bounciness
    {
        get { return Bounciness; }
        set { Bounciness = value; }
    }

    /// <summary>The rigidbody the shape is on, or null for a static collider that has no body of its own to move.</summary>
    public Rigidbody2D attachedRigidbody
    {
        get { return Attached; }
    }

    /// <summary>Whether the component is enabled. Setting it enables or disables it, which makes or destroys its shape.</summary>
    public bool enabled
    {
        get { return Self.Enabled; }
        set { Scene2D.Current.SetEnabled(Self, value); }
    }

    /// <summary>Makes the shape again from the settings as they are now, for a collider that is enabled. Overlaps in progress may be reported again.</summary>
    public void ApplyChanges()
    {
        if (Self == null || !Self.Enabled) return;
        Scene2D.Current.SetEnabled(Self, false);
        Scene2D.Current.SetEnabled(Self, true);
    }
}

/// <summary>
/// The payload of the collision or trigger message being delivered. One object, reused: it is valid for the duration of the callback and must
/// not be kept. <see cref="Self"/> is the collider that is hearing it, <see cref="Other"/> the one it touched; the normal points from the other
/// collider toward self (as the engine's Collision2D.Normal does), so for a ball that lands on the floor its Y is about +1 and <c>NY &gt; 0.5f</c> is a
/// ground check. For trigger messages only the colliders are set.
/// </summary>
[MaxInstances(1)]
internal sealed class Collision2D
{
    public Collider2D Self;
    public Collider2D Other;
    public float X, Y, NX, NY, Impulse;

    // ---- Unity-named members -------------------------------------------------------------
    // As in Unity: <c>collider</c> is the other collider, <c>otherCollider</c> the one hearing the message, and <c>gameObject</c> the other's node.
    // Unity's relativeVelocity is not kept, and there is one contact point however many a pair really has.

    public Collider2D collider { get { return Other; } }
    public Collider2D otherCollider { get { return Self; } }
    public Node gameObject { get { return Other.Self.Node; } }
    public Node transform { get { return Other.Self.Node; } }

    public int contactCount { get { return 1; } }

    /// <summary>The contact point; the index is ignored (there is one).</summary>
    public ContactPoint2D GetContact(int index)
    {
        Vector2 p = new Vector2(X, Y);
        Vector2 n = new Vector2(NX, NY);
        return new ContactPoint2D(p, n, Impulse);
    }
}

/// <summary>UnityEngine.ContactPoint2D: where two colliders touched, with the normal pointing from the other collider toward the one hearing the message.</summary>
internal struct ContactPoint2D
{
    public Vector2 point;
    public Vector2 normal;
    public float normalImpulse;

    public ContactPoint2D(Vector2 p, Vector2 n, float impulse)
    {
        point = p;
        normal = n;
        normalImpulse = impulse;
    }
}
