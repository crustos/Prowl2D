// This file is part of the Prowl Game Engine
// Licensed under the MIT License. See the LICENSE file in the project root for details.

using Prowl.Core2D;

namespace UnityEngine;

/// <summary>
/// UnityEngine.Physics2D, for the current scene's simulation. Only the world's gravity is here so far; the queries (Raycast, OverlapCircle and the
/// rest) are not wired into <c>Prowl.Core2D</c> yet.
/// </summary>
public static class Physics2D
{
    /// <summary>The world's gravity in units per second squared: (0, -9.81) unless set. It may be changed at any time.</summary>
    public static Vector2 gravity
    {
        get
        {
            Scene2D s = Scene2D.Current;
            return new Vector2(s.Physics.Sim.GravityX, s.Physics.Sim.GravityY);
        }
        set { Scene2D.Current.SetGravity(value.x, value.y); }
    }
}
