// This file is part of the Prowl Game Engine
// Licensed under the MIT License. See the LICENSE file in the project root for details.

using System;

namespace UnityEngine;

/// <summary>
/// UnityEngine.Mathf: the same functions on floats, in the C# subset that translates to C.
/// <para/>
/// <b>Differences.</b> The subset has no two methods of one name with the same number of parameters, so Unity's int overloads of Abs, Min, Max and Clamp
/// are <see cref="AbsInt"/>, <see cref="MinInt"/>, <see cref="MaxInt"/> and <see cref="ClampInt"/> (on .NET the int overloads exist under Unity's names
/// too, but a game that is also built as C should use these); there is no <c>params</c> Min or Max; and the subset has no infinity, so
/// <see cref="Infinity"/> is the largest float.
/// </summary>
public static class Mathf
{
    public const float PI = 3.14159265358979f;
    public const float Deg2Rad = 0.017453292f;
    public const float Rad2Deg = 57.29578f;

    /// <summary>The smallest positive normal float (Unity's: with flush-to-zero on).</summary>
    public const float Epsilon = 1.17549435E-38f;

    /// <summary>The largest float: the subset has no infinity.</summary>
    public const float Infinity = 3.40282347E+38f;
    public const float NegativeInfinity = -3.40282347E+38f;

    // ---- the library's ----------------------------------------------------------------------

    public static float Sin(float f) { return MathF.Sin(f); }
    public static float Cos(float f) { return MathF.Cos(f); }
    public static float Tan(float f) { return MathF.Tan(f); }
    public static float Asin(float f) { return MathF.Asin(f); }
    public static float Acos(float f) { return MathF.Acos(f); }
    public static float Atan(float f) { return MathF.Atan(f); }
    public static float Atan2(float y, float x) { return MathF.Atan2(y, x); }
    public static float Sqrt(float f) { return MathF.Sqrt(f); }
    public static float Pow(float f, float p) { return MathF.Pow(f, p); }
    public static float Exp(float power) { return MathF.Exp(power); }

    /// <summary>The natural logarithm.</summary>
    public static float Log(float f) { return MathF.Log(f); }

    /// <summary>The logarithm to a base.</summary>
    public static float Log(float f, float p) { return MathF.Log(f) / MathF.Log(p); }

    public static float Log10(float f) { return MathF.Log(f) * 0.43429448f; }

    public static float Abs(float f) { return MathF.Abs(f); }
    public static float Min(float a, float b) { return MathF.Min(a, b); }
    public static float Max(float a, float b) { return MathF.Max(a, b); }

    public static int AbsInt(int value)
    {
        if (value < 0) return -value;
        return value;
    }

    public static int MinInt(int a, int b)
    {
        if (a < b) return a;
        return b;
    }

    public static int MaxInt(int a, int b)
    {
        if (a > b) return a;
        return b;
    }

    public static int ClampInt(int value, int min, int max)
    {
        if (value < min) return min;
        if (value > max) return max;
        return value;
    }

    public static float Floor(float f) { return MathF.Floor(f); }
    public static float Ceil(float f) { return MathF.Ceiling(f); }

    /// <summary>Rounds to the nearest whole number; a half goes to the even one (2.5 is 2, 3.5 is 4), as Unity's does.</summary>
    public static float Round(float f)
    {
        float fl = MathF.Floor(f);
        float diff = f - fl;
        if (diff < 0.5f) return fl;
        if (diff > 0.5f) return fl + 1f;
        float half = fl * 0.5f;
        if (MathF.Floor(half) == half) return fl;
        return fl + 1f;
    }

    public static int FloorToInt(float f) { return (int)MathF.Floor(f); }
    public static int CeilToInt(float f) { return (int)MathF.Ceiling(f); }
    public static int RoundToInt(float f) { return (int)Round(f); }

    /// <summary>1 for zero and above, -1 below (as Unity's: zero is positive).</summary>
    public static float Sign(float f)
    {
        if (f >= 0f) return 1f;
        return -1f;
    }

    // ---- limiting and interpolating ----------------------------------------------------------

    public static float Clamp(float value, float min, float max)
    {
        if (value < min) return min;
        if (value > max) return max;
        return value;
    }

    public static float Clamp01(float value)
    {
        if (value < 0f) return 0f;
        if (value > 1f) return 1f;
        return value;
    }

    /// <summary>a + (b - a) * t, with t clamped to 0..1.</summary>
    public static float Lerp(float a, float b, float t)
    {
        return a + (b - a) * Clamp01(t);
    }

    public static float LerpUnclamped(float a, float b, float t)
    {
        return a + (b - a) * t;
    }

    /// <summary>Where a value lies between a and b, as 0..1 (0 if they are the same).</summary>
    public static float InverseLerp(float a, float b, float value)
    {
        if (a != b) return Clamp01((value - a) / (b - a));
        return 0f;
    }

    /// <summary>Lerp for angles in degrees: it goes the short way round.</summary>
    public static float LerpAngle(float a, float b, float t)
    {
        float delta = Repeat(b - a, 360f);
        if (delta > 180f) delta = delta - 360f;
        return a + delta * Clamp01(t);
    }

    public static float MoveTowards(float current, float target, float maxDelta)
    {
        if (MathF.Abs(target - current) <= maxDelta) return target;
        return current + Sign(target - current) * maxDelta;
    }

    public static float MoveTowardsAngle(float current, float target, float maxDelta)
    {
        float deltaAngle = DeltaAngle(current, target);
        if (-maxDelta < deltaAngle && deltaAngle < maxDelta) return target;
        target = current + deltaAngle;
        return MoveTowards(current, target, maxDelta);
    }

    /// <summary>Eases in and out between two values; t is clamped to 0..1.</summary>
    public static float SmoothStep(float a, float b, float t)
    {
        t = Clamp01(t);
        t = -2f * t * t * t + 3f * t * t;
        return b * t + a * (1f - t);
    }

    /// <summary>t wrapped into 0..length.</summary>
    public static float Repeat(float t, float length)
    {
        return Clamp(t - MathF.Floor(t / length) * length, 0f, length);
    }

    /// <summary>t bounced back and forth between 0 and length.</summary>
    public static float PingPong(float t, float length)
    {
        t = Repeat(t, length * 2f);
        return length - MathF.Abs(t - length);
    }

    /// <summary>The shortest turn from one angle to another, in degrees (-180..180).</summary>
    public static float DeltaAngle(float current, float target)
    {
        float delta = Repeat(target - current, 360f);
        if (delta > 180f) delta = delta - 360f;
        return delta;
    }

    /// <summary>True if two floats are the same but for the last bits.</summary>
    public static bool Approximately(float a, float b)
    {
        return MathF.Abs(b - a) < MathF.Max(0.000001f * MathF.Max(MathF.Abs(a), MathF.Abs(b)), Epsilon * 8f);
    }

    // ---- smoothing --------------------------------------------------------------------------

    /// <summary>
    /// Eases a value toward a target without overshooting, over about smoothTime seconds; currentVelocity is kept between calls. The frame's
    /// time is <see cref="Time.deltaTime"/>.
    /// </summary>
    public static float SmoothDamp(float current, float target, ref float currentVelocity, float smoothTime)
    {
        return SmoothDamp(current, target, ref currentVelocity, smoothTime, Infinity, Time.deltaTime);
    }

    public static float SmoothDamp(float current, float target, ref float currentVelocity, float smoothTime, float maxSpeed, float deltaTime)
    {
        smoothTime = MathF.Max(0.0001f, smoothTime);
        float omega = 2f / smoothTime;
        float x = omega * deltaTime;
        float exp = 1f / (1f + x + 0.48f * x * x + 0.235f * x * x * x);
        float change = current - target;
        float originalTo = target;
        float maxChange = maxSpeed * smoothTime;
        change = Clamp(change, -maxChange, maxChange);
        target = current - change;
        float temp = (currentVelocity + omega * change) * deltaTime;
        currentVelocity = (currentVelocity - omega * temp) * exp;
        float output = target + (change + temp) * exp;
        if ((originalTo - current > 0f) == (output > originalTo))
        {
            output = originalTo;
            currentVelocity = (output - originalTo) / deltaTime;
        }
        return output;
    }

#if !CRUST
    // Unity's int overloads, under Unity's names. .NET only: the subset cannot tell two overloads with the same number of parameters apart.
    public static int Abs(int value) { return value < 0 ? -value : value; }
    public static int Min(int a, int b) { return a < b ? a : b; }
    public static int Max(int a, int b) { return a > b ? a : b; }
    public static int Clamp(int value, int min, int max) { return value < min ? min : (value > max ? max : value); }
#endif
}
