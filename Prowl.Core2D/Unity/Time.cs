// This file is part of the Prowl Game Engine
// Licensed under the MIT License. See the LICENSE file in the project root for details.

using Prowl.Core2D;

namespace UnityEngine;

/// <summary>
/// UnityEngine.Time, read from the current scene (<c>Scene2D.Current</c>). As in Unity, inside a fixed step (FixedUpdate, and the physics messages) the
/// frame properties give the fixed step's values. <see cref="timeScale"/> works through <c>Scripts.Tick</c>: it scales the time the game loop is
/// given, so 0 stops Update and FixedUpdate from advancing the game, and the physics with them.
/// <para/>
/// Not here: realtimeSinceStartup, smoothDeltaTime, maximumDeltaTime, captureFramerate (the runtime has no clock of its own).
/// </summary>
public static class Time
{
    /// <summary>The seconds the last frame took (in a fixed step: <see cref="fixedDeltaTime"/>), scaled by <see cref="timeScale"/>.</summary>
    public static float deltaTime
    {
        get
        {
            Scene2D s = Scene2D.Current;
            if (s.InFixedStep) return s.FixedDeltaTime;
            return s.DeltaTime;
        }
    }

    /// <summary>The seconds the last frame took, before <see cref="timeScale"/>.</summary>
    public static float unscaledDeltaTime
    {
        get
        {
            Scene2D s = Scene2D.Current;
            if (s.InFixedStep) return s.FixedDeltaTime;
            return s.UnscaledDeltaTime;
        }
    }

    /// <summary>The time between fixed steps, 1/60 s unless set. It may be changed at any time.</summary>
    public static float fixedDeltaTime
    {
        get { return Scene2D.Current.FixedDeltaTime; }
        set { Scene2D.Current.FixedDeltaTime = value; }
    }

    /// <summary>1 is real time, 0 stops the game, 2 runs it twice as fast. Applied by <c>Scripts.Tick</c>.</summary>
    public static float timeScale
    {
        get { return Scene2D.Current.TimeScale; }
        set { Scene2D.Current.TimeScale = value; }
    }

    /// <summary>The seconds of game time at the start of this frame (in a fixed step: <see cref="fixedTime"/>).</summary>
    public static float time
    {
        get
        {
            Scene2D s = Scene2D.Current;
            if (s.InFixedStep) return s.ElapsedFixedTime;
            return s.ElapsedTime;
        }
    }

    /// <summary>The seconds of game time at the start of the latest fixed step.</summary>
    public static float fixedTime
    {
        get { return Scene2D.Current.ElapsedFixedTime; }
    }

    /// <summary>The number of frames begun.</summary>
    public static int frameCount
    {
        get { return Scene2D.Current.FrameIndex; }
    }

    /// <summary>True inside a fixed step: FixedUpdate and the collision and trigger messages.</summary>
    public static bool inFixedTimeStep
    {
        get { return Scene2D.Current.InFixedStep; }
    }
}
