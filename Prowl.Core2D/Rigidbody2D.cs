// This file is part of the Prowl Game Engine
// Licensed under the MIT License. See the LICENSE file in the project root for details.

using Prowl.Native.Box2D;
using Prowl.Runtime.Physics2D;
using UnityEngine;

namespace Prowl.Core2D;

/// <summary>
/// The data of a Rigidbody2D component: how its body is made, and the body itself once it exists. A body is made when the component is
/// enabled, with the values below at that moment (change one by disabling and enabling the component), and destroyed when it is disabled.
/// While it lives, the simulation writes its pose into <see cref="Record"/> and the scene copies that, interpolated, into the node.
/// <para/>
/// An arena class: a pool of <see cref="CoreLimits.Rigidbodies"/>, recycled when the component is freed.
/// </summary>
[MaxInstances(CoreLimits.Rigidbodies)]
internal sealed class Rigidbody2D
{
    private static float[] s_state;
    private static bool s_ready;            // (an array is a value in the subset: it has no null to test)

    public Component Self;
    public int BodyType;                 // PB2.BodyStatic, BodyKinematic or BodyDynamic
    public float GravityScale;
    public float LinearDamping;
    public float AngularDamping;
    public bool IsBullet;
    public bool CanSleep;
    public bool FreezeRotation;

    public int BodyIndex;                // the slot in the simulation's registry, -1 while there is no body
    public uint Handle;                  // the native body, 0 while there is none
    public BodyRecord Record;            // its pose history, written by the step
    public int SyncedVersion;            // the node's world version just after the scene last wrote the pose: any other value is an edit by the game
    public float WrittenX, WrittenY, WrittenAngle;
    public bool HasWritten;

    public void Reset(int bodyType)
    {
        Self = null;
        BodyType = bodyType;
        GravityScale = 1f;
        LinearDamping = 0f;
        AngularDamping = 0.05f;
        IsBullet = false;
        CanSleep = true;
        FreezeRotation = false;
        BodyIndex = -1;
        Handle = 0;
        Record = null;
        SyncedVersion = 0;
        WrittenX = 0f;
        WrittenY = 0f;
        WrittenAngle = 0f;
        HasWritten = false;
    }

    /// <summary>True while the body exists (the component is enabled and there was room for it).</summary>
    public bool IsSimulated => Handle != 0;

    public void SetVelocity(float vx, float vy)
    {
        if (Handle != 0) PB2.BodySetVelocity(Handle, vx, vy, AngularVelocity());
    }

    public void AddImpulse(float ix, float iy)
    {
        if (Handle != 0) PB2.BodyApplyImpulse(Handle, ix, iy, 0, 0f, 0f);
    }

    public void AddForce(float fx, float fy)
    {
        if (Handle != 0) PB2.BodyApplyForce(Handle, fx, fy, 0, 0f, 0f);
    }

    // The state is 10 floats: position, cos/sin, linear velocity, angular velocity, mass, inertia, awake.
    private void Refresh()
    {
        if (!s_ready)
        {
            s_state = new float[10];
            s_ready = true;
        }
        PB2.BodyGetState(Handle, s_state);
    }

    public float VelocityX() { if (Handle == 0) return 0f; Refresh(); return s_state[4]; }
    public float VelocityY() { if (Handle == 0) return 0f; Refresh(); return s_state[5]; }
    public float AngularVelocity() { if (Handle == 0) return 0f; Refresh(); return s_state[6]; }
    public bool IsAwake() { if (Handle == 0) return false; Refresh(); return s_state[9] > 0.5f; }

    // ---- Unity-named members -------------------------------------------------------------
    //
    // As in Unity: angles and angular velocity are degrees (the fields and methods above are radians), vectors are Vector2, and a setting takes effect
    // at once on a body that exists. On a component that is not enabled yet it is stored and used when the body is made. Differences: mass can only be
    // set on a body that exists (the body's own mass is then replaced); AddForce with a ForceMode2D is .NET only (the subset has no two overloads of a
    // name with the same number of parameters), so in a game that is also built as C use AddForce(Vector2) and AddImpulse(float, float).

    public Node gameObject { get { return Self.Node; } }
    public Node transform { get { return Self.Node; } }

    /// <summary>The body's linear velocity in units per second. Zero while there is no body.</summary>
    public Vector2 velocity
    {
        get { return new Vector2(VelocityX(), VelocityY()); }
        set { SetVelocity(value.x, value.y); }
    }

    /// <summary>The same as <see cref="velocity"/>: Unity 6 renamed it.</summary>
    public Vector2 linearVelocity
    {
        get { return new Vector2(VelocityX(), VelocityY()); }
        set { SetVelocity(value.x, value.y); }
    }

    /// <summary>The rotation speed in degrees per second.</summary>
    public float angularVelocity
    {
        get { return AngularVelocity() * 57.29578f; }
        set
        {
            if (Handle != 0) PB2.BodySetVelocity(Handle, VelocityX(), VelocityY(), value * 0.017453292f);
        }
    }

    public float gravityScale
    {
        get { return GravityScale; }
        set
        {
            GravityScale = value;
            if (Handle != 0) PB2.BodySetGravityScale(Handle, value);
        }
    }

    public float linearDamping
    {
        get { return LinearDamping; }
        set
        {
            LinearDamping = value;
            if (Handle != 0) PB2.BodySetDamping(Handle, LinearDamping, AngularDamping);
        }
    }

    public float angularDamping
    {
        get { return AngularDamping; }
        set
        {
            AngularDamping = value;
            if (Handle != 0) PB2.BodySetDamping(Handle, LinearDamping, AngularDamping);
        }
    }

    /// <summary>Unity's older name for <see cref="linearDamping"/>.</summary>
    public float drag
    {
        get { return LinearDamping; }
        set
        {
            LinearDamping = value;
            if (Handle != 0) PB2.BodySetDamping(Handle, LinearDamping, AngularDamping);
        }
    }

    /// <summary>Unity's older name for <see cref="angularDamping"/>.</summary>
    public float angularDrag
    {
        get { return AngularDamping; }
        set
        {
            AngularDamping = value;
            if (Handle != 0) PB2.BodySetDamping(Handle, LinearDamping, AngularDamping);
        }
    }

    /// <summary>The body's mass, which its colliders' densities and sizes make. Setting it replaces that, and only works on a body that exists.</summary>
    public float mass
    {
        get
        {
            if (Handle == 0) return 0f;
            Refresh();
            return s_state[7];
        }
        set
        {
            if (Handle != 0) PB2.BodySetMass(Handle, value);
        }
    }

    public RigidbodyType2D bodyType
    {
        get
        {
            if (BodyType == PB2.BodyStatic) return RigidbodyType2D.Static;
            if (BodyType == PB2.BodyKinematic) return RigidbodyType2D.Kinematic;
            return RigidbodyType2D.Dynamic;
        }
        set
        {
            if (value == RigidbodyType2D.Static) BodyType = PB2.BodyStatic;
            else if (value == RigidbodyType2D.Kinematic) BodyType = PB2.BodyKinematic;
            else BodyType = PB2.BodyDynamic;
            if (Handle != 0) PB2.BodySetType(Handle, BodyType);
        }
    }

    public bool isKinematic
    {
        get { return BodyType == PB2.BodyKinematic; }
        set
        {
            if (value) BodyType = PB2.BodyKinematic;
            else BodyType = PB2.BodyDynamic;
            if (Handle != 0) PB2.BodySetType(Handle, BodyType);
        }
    }

    /// <summary>True while the body is in the simulation. Setting it enables or disables the component (a disabled one has no body).</summary>
    public bool simulated
    {
        get { return Handle != 0; }
        set { Scene2D.Current.SetEnabled(Self, value); }
    }

    public bool freezeRotation
    {
        get { return FreezeRotation; }
        set
        {
            FreezeRotation = value;
            ApplyFlags();
        }
    }

    // Rebuilds the body's flags from the fields that make them, as the body's creation does.
    private void ApplyFlags()
    {
        if (Handle == 0) return;
        uint flags = 0u;
        if (IsBullet) flags |= PB2.BfBullet;
        if (!CanSleep) flags |= PB2.BfNoSleep;
        if (FreezeRotation) flags |= PB2.BfLockRot;
        PB2.BodySetFlags(Handle, flags);
    }

    /// <summary>The body's world position. Setting it teleports the body (it edits the node, which is pushed into the body before the next step).</summary>
    public Vector2 position
    {
        get
        {
            Node n = Self.Node;
            return new Vector2(n.WorldX(), n.WorldY());
        }
        set { Self.Node.SetWorldPositionXY(value.x, value.y); }
    }

    /// <summary>The body's world rotation in degrees. Setting it turns the body.</summary>
    public float rotation
    {
        get { return Self.Node.WorldAngle() * 57.29578f; }
        set { Self.Node.SetWorldAngleDegrees(value); }
    }

    /// <summary>Moves the body to a world position. In this runtime that is an edit of the node, so a dynamic body is teleported and a kinematic one is moved there.</summary>
    public void MovePosition(Vector2 newPosition)
    {
        Self.Node.SetWorldPositionXY(newPosition.x, newPosition.y);
    }

    /// <summary>Turns the body to a world angle in degrees.</summary>
    public void MoveRotation(float angle)
    {
        Self.Node.SetWorldAngleDegrees(angle);
    }

    /// <summary>A force over time, in world space (ForceMode2D.Force).</summary>
    public void AddForce(Vector2 force)
    {
        AddForce(force.x, force.y);
    }

    /// <summary>A force at a world point, so it can turn the body too.</summary>
    public void AddForceAtPosition(Vector2 force, Vector2 point)
    {
        if (Handle != 0) PB2.BodyApplyForce(Handle, force.x, force.y, 1, point.x, point.y);
    }

    public void AddTorque(float torque)
    {
        if (Handle != 0) PB2.BodyApplyTorque(Handle, torque, 0);
    }

    public bool IsSleeping()
    {
        if (Handle == 0) return false;
        return !IsAwake();
    }

    public void WakeUp()
    {
        if (Handle != 0) PB2.BodySetAwake(Handle, 1);
    }

    public void Sleep()
    {
        if (Handle != 0) PB2.BodySetAwake(Handle, 0);
    }

#if !CRUST
    /// <summary>Unity's AddForce(force, mode). .NET only: see the note above.</summary>
    public void AddForce(Vector2 force, ForceMode2D mode)
    {
        if (mode == ForceMode2D.Impulse) AddImpulse(force.x, force.y);
        else AddForce(force.x, force.y);
    }

    /// <summary>Unity's AddForceAtPosition(force, point, mode). .NET only.</summary>
    public void AddForceAtPosition(Vector2 force, Vector2 point, ForceMode2D mode)
    {
        if (Handle == 0) return;
        if (mode == ForceMode2D.Impulse) PB2.BodyApplyImpulse(Handle, force.x, force.y, 1, point.x, point.y);
        else PB2.BodyApplyForce(Handle, force.x, force.y, 1, point.x, point.y);
    }

    /// <summary>Unity's AddTorque(torque, mode). .NET only.</summary>
    public void AddTorque(float torque, ForceMode2D mode)
    {
        if (Handle == 0) return;
        PB2.BodyApplyTorque(Handle, torque, mode == ForceMode2D.Impulse ? 1 : 0);
    }
#endif
}
