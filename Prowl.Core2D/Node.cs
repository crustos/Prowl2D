// This file is part of the Prowl Game Engine
// Licensed under the MIT License. See the LICENSE file in the project root for details.

using System;
using Prowl.Runtime.Physics2D;
using UnityEngine;

namespace Prowl.Core2D;

/// <summary>
/// A place in the scene: a position, an angle and a scale, in a tree. This is the engine's GameObject and Transform for the 2D runtime, with every
/// reference an arena reference, so the whole hierarchy translates to C and a node is a pointer into a small static array.
/// <para/>
/// <b>Transform.</b> Local position, angle (radians, counter-clockwise) and scale; the world transform is a 2x3 matrix
/// (<c>x' = a x + c y + tx</c>, <c>y' = b x + d y + ty</c>) built from the parent's and cached. The cache has one invariant, which is what keeps
/// invalidation cheap: <b>a node whose world is invalid has only invalid descendants</b>. A change therefore marks a subtree and stops at the first
/// node that is already stale, and a read recomputes only the stale path above it.
/// <para/>
/// <b>Versions.</b> <see cref="Version"/> is a unique, ever-increasing id given to a node whenever its local transform changes or it is reparented.
/// <see cref="WorldVersion"/> is the greatest id along the path to the root, so it rises when the node, or anything above it, is edited. A body that
/// writes its pose into a node remembers the world version it left behind and treats any other value as somebody else's edit.
/// <para/>
/// Non-uniform scale under a rotated parent shears the child, as in any 2D engine that stores matrices; <see cref="LossyScaleX"/> and
/// <see cref="WorldAngle"/> are the lengths and direction of the matrix's columns, and <see cref="SetParent"/> with keepWorld preserves position
/// and angle, not scale.
/// </summary>
[MaxInstances(CoreLimits.Nodes)]
internal sealed class Node
{
    private static int s_epoch;

    public int Index;                    // the node's slot in the scene
    public bool Alive;                   // false while its slot is free
    public int Tag;                      // for the game: what kind of thing this is
    public int Layer;                    // the physics layer of the node's colliders (0..31)
    public bool ActiveSelf;              // set by the game (Scene2D.SetActive)
    public bool ActiveInHierarchy;       // ActiveSelf, and every ancestor's too; kept by the scene
    public bool Destroyed;               // marked for removal at the end of the frame

    public Node Parent;
    public Node FirstChild;
    public Node LastChild;
    public Node NextSibling;
    public Node PrevSibling;
    public int ChildCount;

    public float X, Y;                   // local position
    public float Angle;                  // local angle
    public float ScaleX, ScaleY;
    public int Version;                  // unique id of the last change to the local transform or the parent

    private float _a, _b, _c, _d, _tx, _ty;
    private int _worldVersion;
    private bool _worldValid;

    /// <summary>Back to a new node's state, for a recycled slot.</summary>
    public void Reset(int index)
    {
        Index = index;
        Alive = true;
        Tag = 0;
        Layer = 0;
        ActiveSelf = true;
        ActiveInHierarchy = true;
        Destroyed = false;
        Parent = null;
        FirstChild = null;
        LastChild = null;
        NextSibling = null;
        PrevSibling = null;
        ChildCount = 0;
        X = 0f;
        Y = 0f;
        Angle = 0f;
        ScaleX = 1f;
        ScaleY = 1f;
        Version = 0;
        _worldValid = false;
    }

    // ---- local transform -----------------------------------------------------------------

    private void Touch()
    {
        s_epoch = s_epoch + 1;
        Version = s_epoch;
        InvalidateWorld();
    }

    // Stops at a node that is already stale: by the invariant, everything below it is too.
    private void InvalidateWorld()
    {
        if (!_worldValid) return;
        _worldValid = false;
        for (Node c = FirstChild; c != null; c = c.NextSibling) c.InvalidateWorld();
    }

    public void SetPosition(float x, float y)
    {
        X = x;
        Y = y;
        Touch();
    }

    public void SetAngle(float angle)
    {
        Angle = angle;
        Touch();
    }

    public void SetScale(float sx, float sy)
    {
        ScaleX = sx;
        ScaleY = sy;
        Touch();
    }

    public void SetLocal(float x, float y, float angle, float sx, float sy)
    {
        X = x;
        Y = y;
        Angle = angle;
        ScaleX = sx;
        ScaleY = sy;
        Touch();
    }

    // ---- world transform -----------------------------------------------------------------

    private void EnsureWorld()
    {
        if (_worldValid) return;
        float c = MathF.Cos(Angle), s = MathF.Sin(Angle);
        float la = c * ScaleX, lb = s * ScaleX, lc = -s * ScaleY, ld = c * ScaleY;
        if (Parent == null)
        {
            _a = la; _b = lb; _c = lc; _d = ld;
            _tx = X; _ty = Y;
            _worldVersion = Version;
        }
        else
        {
            Parent.EnsureWorld();
            Node p = Parent;
            _a = p._a * la + p._c * lb;
            _b = p._b * la + p._d * lb;
            _c = p._a * lc + p._c * ld;
            _d = p._b * lc + p._d * ld;
            _tx = p._a * X + p._c * Y + p._tx;
            _ty = p._b * X + p._d * Y + p._ty;
            _worldVersion = Version > p._worldVersion ? Version : p._worldVersion;
        }
        _worldValid = true;
    }

    public float WorldX() { EnsureWorld(); return _tx; }
    public float WorldY() { EnsureWorld(); return _ty; }
    public float WorldAngle() { EnsureWorld(); return MathF.Atan2(_b, _a); }
    public float LossyScaleX() { EnsureWorld(); return MathF.Sqrt(_a * _a + _b * _b); }

    /// <summary>The length of the matrix's second column, negative if the node is mirrored.</summary>
    public float LossyScaleY()
    {
        EnsureWorld();
        float sy = MathF.Sqrt(_c * _c + _d * _d);
        return _a * _d - _b * _c < 0f ? -sy : sy;
    }

    /// <summary>Changes whenever this node or any ancestor is edited or reparented, and never goes back.</summary>
    public int WorldVersion() { EnsureWorld(); return _worldVersion; }

    public void ToWorld(float lx, float ly, out float wx, out float wy)
    {
        EnsureWorld();
        wx = _a * lx + _c * ly + _tx;
        wy = _b * lx + _d * ly + _ty;
    }

    /// <summary>A world point in this node's space. A collapsed node (scale zero) has no inverse: it is treated as a translation.</summary>
    public void ToLocal(float wx, float wy, out float lx, out float ly)
    {
        EnsureWorld();
        float dx = wx - _tx, dy = wy - _ty;
        float det = _a * _d - _b * _c;
        if (det > -1e-12f && det < 1e-12f)
        {
            lx = dx;
            ly = dy;
            return;
        }
        float inv = 1f / det;
        lx = (_d * dx - _c * dy) * inv;
        ly = (-_b * dx + _a * dy) * inv;
    }

    /// <summary>Places the node at a world position and angle, by changing its local transform (scale is left alone).</summary>
    public void SetWorldPose(float wx, float wy, float wangle)
    {
        if (Parent == null)
        {
            X = wx;
            Y = wy;
            Angle = wangle;
        }
        else
        {
            float lx, ly;
            Parent.ToLocal(wx, wy, out lx, out ly);
            X = lx;
            Y = ly;
            Angle = Angle2D.WrapPi(wangle - Parent.WorldAngle());
        }
        Touch();
    }

    // ---- hierarchy -----------------------------------------------------------------------

    public bool IsDescendantOf(Node other)
    {
        for (Node n = Parent; n != null; n = n.Parent)
            if (n == other) return true;
        return false;
    }

    /// <summary>
    /// Moves the node under <paramref name="parent"/> (null for the root), as that parent's last child. Returns false, changing nothing, if that
    /// would make the node its own ancestor. With <paramref name="keepWorld"/> the node keeps its world position and angle; without, it keeps its
    /// local transform and so moves.
    /// </summary>
    public bool SetParent(Node parent, bool keepWorld)
    {
        if (parent == this || (parent != null && parent.IsDescendantOf(this))) return false;
        float wx = 0f, wy = 0f, wa = 0f;
        if (keepWorld)
        {
            wx = WorldX();
            wy = WorldY();
            wa = WorldAngle();
        }
        Unlink();
        LinkTo(parent);
        Touch();                                  // its world changed even though its local did not
        if (keepWorld) SetWorldPose(wx, wy, wa);
        return true;
    }

    /// <summary>Takes the node out of its parent's children (it keeps its local transform).</summary>
    public void Detach()
    {
        if (Parent == null) return;
        Unlink();
        Touch();
    }

    private void LinkTo(Node parent)
    {
        Parent = parent;
        NextSibling = null;
        PrevSibling = null;
        if (parent == null) return;
        if (parent.LastChild == null)
        {
            parent.FirstChild = this;
            parent.LastChild = this;
        }
        else
        {
            PrevSibling = parent.LastChild;
            parent.LastChild.NextSibling = this;
            parent.LastChild = this;
        }
        parent.ChildCount++;
    }

    private void Unlink()
    {
        if (Parent != null)
        {
            if (PrevSibling != null) PrevSibling.NextSibling = NextSibling;
            else Parent.FirstChild = NextSibling;
            if (NextSibling != null) NextSibling.PrevSibling = PrevSibling;
            else Parent.LastChild = PrevSibling;
            Parent.ChildCount--;
        }
        Parent = null;
        NextSibling = null;
        PrevSibling = null;
    }

    // ---- Unity-named members -------------------------------------------------------------
    //
    // A Node is what Unity splits in two: the GameObject (active, layer, destroy, its components) and its Transform (position, rotation, scale, the
    // tree). Both sets of members are here, and <c>transform</c> and <c>gameObject</c> are the node itself, so Unity's chains
    // (<c>collision.gameObject.transform.position</c>) work. Everything above keeps its meaning: Angle is radians, SetPosition takes two floats.
    //
    // As in Unity, angles here are degrees and positions are Vector3; z is carried as 0 and ignored. Differences: there is no name and no string tag
    // (the subset has no string-keyed lookup), so <c>Tag</c> is an int and <c>CompareTag</c> takes one; GetChild returns null for a bad index
    // where Unity throws; Rotate about x or y does nothing (a 2D node turns about z only). Setting a position or rotation is an edit of the node like
    // any other: a rigidbody on it is teleported to it before the next step.

    public Node transform { get { return this; } }
    public Node gameObject { get { return this; } }

    private static float Degrees360(float radians)
    {
        float d = radians * 57.29578f;
        d = d % 360f;
        if (d < 0f) d = d + 360f;
        if (d >= 360f) d = d - 360f;
        return d;
    }

    // These touch only what they set. (SetWorldPose(x, y, WorldAngle()) would not do for a position: a mirrored node's WorldAngle is its angle
    // plus pi, and writing that back would turn it over.)

    /// <summary>Places the node at a world position and leaves its angle and scale alone.</summary>
    public void SetWorldPositionXY(float wx, float wy)
    {
        if (Parent == null)
        {
            SetPosition(wx, wy);
            return;
        }
        float lx, ly;
        Parent.ToLocal(wx, wy, out lx, out ly);
        SetPosition(lx, ly);
    }

    /// <summary>Turns the node to a world angle in radians and leaves its position and scale alone.</summary>
    public void SetWorldAngleRadians(float wangle)
    {
        if (Parent == null)
        {
            SetAngle(wangle);
            return;
        }
        SetAngle(Angle2D.WrapPi(wangle - Parent.WorldAngle()));
    }

    /// <summary>The same, in degrees.</summary>
    public void SetWorldAngleDegrees(float degrees)
    {
        SetWorldAngleRadians(degrees * 0.017453292f);
    }

    public Vector3 position
    {
        get { return new Vector3(WorldX(), WorldY(), 0f); }
        set { SetWorldPositionXY(value.x, value.y); }
    }

    public Vector3 localPosition
    {
        get { return new Vector3(X, Y, 0f); }
        set { SetPosition(value.x, value.y); }
    }

    /// <summary>The world rotation as euler angles in degrees (0..360): only z is ever not 0.</summary>
    public Vector3 eulerAngles
    {
        get { return new Vector3(0f, 0f, Degrees360(WorldAngle())); }
        set { SetWorldAngleRadians(value.z * 0.017453292f); }
    }

    public Vector3 localEulerAngles
    {
        get { return new Vector3(0f, 0f, Degrees360(Angle)); }
        set { SetAngle(value.z * 0.017453292f); }
    }

    public Quaternion rotation
    {
        get { return Quaternion.Euler(0f, 0f, WorldAngle() * 57.29578f); }
        set { SetWorldAngleRadians(Angle2D.FromQuaternionZ(value.x, value.y, value.z, value.w)); }
    }

    public Quaternion localRotation
    {
        get { return Quaternion.Euler(0f, 0f, Angle * 57.29578f); }
        set { SetAngle(Angle2D.FromQuaternionZ(value.x, value.y, value.z, value.w)); }
    }

    public Vector3 localScale
    {
        get { return new Vector3(ScaleX, ScaleY, 1f); }
        set { SetScale(value.x, value.y); }
    }

    public Vector3 lossyScale
    {
        get { return new Vector3(LossyScaleX(), LossyScaleY(), 1f); }
    }

    /// <summary>The node's x axis in the world. Setting it turns the node so that its x axis points that way.</summary>
    public Vector3 right
    {
        get
        {
            float a = WorldAngle();
            return new Vector3(MathF.Cos(a), MathF.Sin(a), 0f);
        }
        set { SetWorldAngleRadians(MathF.Atan2(value.y, value.x)); }
    }

    /// <summary>The node's y axis in the world. Setting it turns the node so that its y axis points that way.</summary>
    public Vector3 up
    {
        get
        {
            float a = WorldAngle();
            return new Vector3(-MathF.Sin(a), MathF.Cos(a), 0f);
        }
        set { SetWorldAngleRadians(MathF.Atan2(-value.x, value.y)); }
    }

    public Vector3 forward
    {
        get { return new Vector3(0f, 0f, 1f); }
    }

    // ---- moving and turning ----------------------------------------------------------------

    /// <summary>Moves along the node's own axes (Unity's default, Space.Self).</summary>
    public void Translate(Vector3 translation)
    {
        Translate(translation.x, translation.y, translation.z);
    }

    public void Translate(Vector3 translation, Space relativeTo)
    {
        if (relativeTo == Space.World) SetWorldPositionXY(WorldX() + translation.x, WorldY() + translation.y);
        else Translate(translation.x, translation.y, translation.z);
    }

    /// <summary>Moves along the node's own axes: x to its right, y to its up (z is ignored).</summary>
    public void Translate(float x, float y, float z)
    {
        float a = WorldAngle();
        float c = MathF.Cos(a);
        float s = MathF.Sin(a);
        SetWorldPositionXY(WorldX() + c * x - s * y, WorldY() + s * x + c * y);
    }

    /// <summary>Turns by eulers.z degrees; x and y do nothing. Unity's default, Space.Self: in a plane it is the same as Space.World.</summary>
    public void Rotate(Vector3 eulers)
    {
        SetAngle(Angle + eulers.z * 0.017453292f);
    }

    public void Rotate(Vector3 eulers, Space relativeTo)
    {
        SetAngle(Angle + eulers.z * 0.017453292f);
    }

    public void Rotate(float xAngle, float yAngle, float zAngle)
    {
        SetAngle(Angle + zAngle * 0.017453292f);
    }

    /// <summary>Turns the node about a world point by angle degrees, moving it round the point. The axis must be z (up to its sign); any other does nothing.</summary>
    public void RotateAround(Vector3 point, Vector3 axis, float angle)
    {
        if (axis.z == 0f) return;
        float r = angle * 0.017453292f;
        if (axis.z < 0f) r = -r;
        float c = MathF.Cos(r);
        float s = MathF.Sin(r);
        float dx = WorldX() - point.x;
        float dy = WorldY() - point.y;
        SetWorldPositionXY(point.x + c * dx - s * dy, point.y + s * dx + c * dy);
        SetWorldAngleRadians(WorldAngle() + r);
    }

    // ---- between the node's space and the world's -------------------------------------------

    public Vector3 TransformPoint(Vector3 point)
    {
        float wx, wy;
        ToWorld(point.x, point.y, out wx, out wy);
        return new Vector3(wx, wy, point.z);
    }

    public Vector3 InverseTransformPoint(Vector3 point)
    {
        float lx, ly;
        ToLocal(point.x, point.y, out lx, out ly);
        return new Vector3(lx, ly, point.z);
    }

    /// <summary>A direction in the node's space as a direction in the world: turned by the node's rotation, not scaled.</summary>
    public Vector3 TransformDirection(Vector3 direction)
    {
        float a = WorldAngle();
        float c = MathF.Cos(a);
        float s = MathF.Sin(a);
        return new Vector3(c * direction.x - s * direction.y, s * direction.x + c * direction.y, direction.z);
    }

    public Vector3 InverseTransformDirection(Vector3 direction)
    {
        float a = WorldAngle();
        float c = MathF.Cos(a);
        float s = MathF.Sin(a);
        return new Vector3(c * direction.x + s * direction.y, -s * direction.x + c * direction.y, direction.z);
    }

    // ---- the tree --------------------------------------------------------------------------

    /// <summary>The parent node, or null. Setting it keeps the node where it is in the world (Unity's SetParent with worldPositionStays).</summary>
    public Node parent
    {
        get { return Parent; }
        set { Scene2D.Current.SetParent(this, value, true); }
    }

    public int childCount { get { return ChildCount; } }

    public Node root
    {
        get
        {
            Node n = this;
            while (n.Parent != null) n = n.Parent;
            return n;
        }
    }

    /// <summary>The child at an index, in the order they were added; null if there is none (Unity throws).</summary>
    public Node GetChild(int index)
    {
        Node c = FirstChild;
        for (int i = 0; i < index && c != null; i++) c = c.NextSibling;
        return c;
    }

    /// <summary>Moves the node under a parent (null for the root), keeping it where it is in the world, and settles whether it is now active.</summary>
    public void SetParent(Node newParent)
    {
        Scene2D.Current.SetParent(this, newParent, true);
    }

    /// <summary>True if the node is the other, or somewhere under it.</summary>
    public bool IsChildOf(Node other)
    {
        return this == other || IsDescendantOf(other);
    }

    // ---- the GameObject's ------------------------------------------------------------------

    public bool activeSelf { get { return ActiveSelf; } }
    public bool activeInHierarchy { get { return ActiveInHierarchy; } }

    public void SetActive(bool value)
    {
        Scene2D.Current.SetActive(this, value);
    }

    public int layer
    {
        get { return Layer; }
        set { Layer = value; }
    }

    public bool CompareTag(int tag)
    {
        return Tag == tag;
    }

    /// <summary>Unity's <c>Destroy(gameObject)</c>: the node and everything under it go at the end of the frame.</summary>
    public void Destroy()
    {
        Scene2D.Current.Destroy(this);
    }

    // ---- its components (Unity had these as shortcuts, before GetComponent) --------------------

    public Rigidbody2D rigidbody2D
    {
        get
        {
            Component c = Scene2D.Current.Find(this, ComponentKind.Rigidbody2D);
            if (c == null) return null;
            return c.Body;
        }
    }

    /// <summary>The node's first collider of any shape, or null.</summary>
    public Collider2D collider2D
    {
        get
        {
            for (Component c = Scene2D.Current.FirstComponent(this); c != null; c = c.NextOnNode)
                if (c.Collider != null && !c.Destroyed) return c.Collider;
            return null;
        }
    }

    public SpriteRenderer2D spriteRenderer
    {
        get
        {
            Component c = Scene2D.Current.Find(this, ComponentKind.SpriteRenderer2D);
            if (c == null) return null;
            return c.Sprite;
        }
    }

#if !CRUST
    /// <summary>The first component of type T on the node: Rigidbody2D, Collider2D or SpriteRenderer2D, else null. .NET only (a generic method does not translate).</summary>
    public T GetComponent<T>() where T : class
    {
        if (typeof(T) == typeof(Rigidbody2D)) return rigidbody2D as T;
        if (typeof(T) == typeof(Collider2D)) return collider2D as T;
        if (typeof(T) == typeof(SpriteRenderer2D)) return spriteRenderer as T;
        return null;
    }
#endif
}
