// This file is part of the Prowl Game Engine
// Licensed under the MIT License. See the LICENSE file in the project root for details.

using System;

namespace UnityEngine;

/// <summary>
/// UnityEngine.Debug: logging to the console. The subset has <c>Console.WriteLine</c> and no way to print a float, so a message is a string, built
/// by the caller (an int or a string joins one with <c>+</c>); on .NET the overloads that take any object exist too, as Unity's do.
/// </summary>
public static class Debug
{
    public static void Log(string message)
    {
        Console.WriteLine(message);
    }

    public static void LogWarning(string message)
    {
        Console.WriteLine("WARNING: " + message);
    }

    public static void LogError(string message)
    {
        Console.WriteLine("ERROR: " + message);
    }

    /// <summary>Logs an error if the condition is false.</summary>
    public static void Assert(bool condition)
    {
        if (!condition) Console.WriteLine("ERROR: Assertion failed");
    }

    /// <summary>Logs the message as an error if the condition is false.</summary>
    public static void Assert(bool condition, string message)
    {
        if (!condition) Console.WriteLine("ERROR: Assertion failed: " + message);
    }

#if !CRUST
    public static void Log(object message)
    {
        Console.WriteLine(message == null ? "Null" : message.ToString());
    }

    public static void LogWarning(object message)
    {
        Console.WriteLine("WARNING: " + (message == null ? "Null" : message.ToString()));
    }

    public static void LogError(object message)
    {
        Console.WriteLine("ERROR: " + (message == null ? "Null" : message.ToString()));
    }
#endif
}
