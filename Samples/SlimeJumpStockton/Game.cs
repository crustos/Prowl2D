// SlimeJumpStockton: a side-scroller in Stockton, California. The world is one destructible terrain (PixelTerrain2D with the sand simulation switched on): a street over a
// sewer, two brick buildings whose upper floors hang out over the street, a sand bin and a water tank sealed in rock, storm drains, and crates and boulders (Shatter2D) lying
// about. The slime runs right, shatters what it meets with its blaster, and swings up onto each roof on the lasso, from the underside of the overhang. Sand and water flow
// (the water in the sewer is sewage), and the slime swims in it. Headless, like SlimeJumpDestructSand: a bot plays, the program prints, and the same source runs on .NET (the
// reference) and as a native or wasm executable with the same output.
using System;
using Prowl.Core2D;
using Prowl.Native.Box2D;
using Prowl.Runtime.Destruction2D;

static class Game
{
    const int MaxFrames = 14000;

    static int Milli(float v) { return (int)(v * 1000f); }

    static void PrintWorld(string title)
    {
        string line = title + " street sand=" + Destruct.StreetSand() + " street water=" + Destruct.StreetWater() + " sewage=" + Destruct.Sewage() + " sewer sand=" + Destruct.SewerSand();
        Console.WriteLine(line);
    }

    static void DumpAround(float cx, float cy)
    {
        Scene2D scene2 = World.scene;
        for (float y = cy + 6f; y > cy - 6f; y -= 0.25f)
        {
            string row = "";
            for (float x = cx - 6f; x < cx + 6f; x += 0.25f)
            {
                string c = ".";
                if (Destruct.SolidAt(x, y)) c = "#";
                if (Destruct.WaterAt(x, y)) c = "~";
                if (!Destruct.SolidAt(x, y) && scene2.Physics.Sim.OverlapBox(x, y, 0.06f, 0.06f, 0f, 1u << Layers.Wall, false) > 0) c = "o";
                if (MathF.Abs(x - cx) < 0.2f && MathF.Abs(y - cy) < 0.2f) c = "@";
                row = row + c;
            }
            Console.WriteLine(row);
        }
    }

    public static int Main()
    {
        World.Build();
        Scene2D scene = World.scene;
        Node player = World.player;
        int sewage0 = Destruct.Sewage();
        int water0 = Destruct.StreetWater();
        int sand0 = Destruct.StreetSand();
        int items0 = Destruct.ItemCount();
        int plugs0 = Destruct.PlugCount();
        string head = "stockton " + Milli(Level.Width) / 1000 + " x " + Milli(Level.Height) / 1000 + " units: items=" + items0 + " plugs=" + plugs0 + " ground=" + Destruct.GroundPixels();
        Console.WriteLine(head);
        PrintWorld("start");

        int wonFrame = -1;
        int roofs = 0;
        int swingsSeen = 0;
        float maxY = Level.SpawnY();
        float maxX = Level.SpawnX();
        int maxAwake = 0;
        int swimFrames = 0;
        for (int frame = 0; frame < MaxFrames && !Shared.Won; frame++)
        {
            Shared.Time_Debug = false;
            if (frame == 99999) DumpAround(52.5f, 29f);
            World.Tick();
            float px = player.WorldX();
            float py = player.WorldY();
            if (py > maxY) maxY = py;
            if (px > maxX) maxX = px;
            if (Destruct.WaterAt(px, py)) swimFrames++;
            if (swingsSeen < Shared.SwingsDone)
            {
                swingsSeen = Shared.SwingsDone;
                Console.WriteLine("swing " + swingsSeen + " done: frame=" + frame + " x*1000=" + Milli(px) + " y*1000=" + Milli(py));
            }
            if (roofs == 0 && px > Level.ChannelX1 + 1f && py > Level.StreetY)
            {
                roofs = 1;                                    // across
                Console.WriteLine("across the channel: frame=" + frame + " x*1000=" + Milli(px) + " y*1000=" + Milli(py) + " swings=" + Shared.SwingsDone);
                PrintWorld("      ");
            }
            int awake = Destruct.AwakeCount();
            if (awake > maxAwake) maxAwake = awake;
            if (frame % 500 == 0)
            {
                string tick = "t=" + (frame / 100) + "s x*1000=" + Milli(px) + " y*1000=" + Milli(py) + " lasso=" + (Shared.LassoAttached ? 1 : 0) + " sand hash=" + Destruct.SandHash();
                Console.WriteLine(tick);
            }
            if (Shared.Won) wonFrame = frame;
        }
        int won = Shared.Won ? 1 : 0;
        Console.WriteLine("won=" + won + " frame=" + wonFrame + " deaths=" + Shared.Deaths + " across=" + roofs + " swings=" + Shared.SwingsDone + " max y*1000=" + Milli(maxY) + " max x*1000=" + Milli(maxX));
        PrintWorld("end  ");
        int plugsOpen = 0;
        for (int i = 0; i < Destruct.PlugCount(); i++)
            if (!Destruct.PlugClosed(i)) plugsOpen++;
        int liveItems = 0;
        for (int i = 0; i < Destruct.ItemCount(); i++)
            if (Destruct.ItemLive(scene, i)) liveItems++;
        Console.WriteLine("sand " + sand0 + " -> " + Destruct.StreetSand() + ", street water " + water0 + " -> " + Destruct.StreetWater() + ", sewage " + sewage0 + " -> " + Destruct.Sewage() + " (rubble made " + Destruct.RubbleGrains + ") digs=" + Destruct.Digs + " plugs open=" + plugsOpen + "/" + plugs0 + " swimming frames=" + swimFrames);
        Console.WriteLine("items=" + items0 + " detonated=" + Destruct.Detonations + " live=" + liveItems + " fragments=" + Destruct.Fragments + " gone=" + Destruct.FragmentsGone + " most awake chunks=" + maxAwake + " sand hash=" + Destruct.SandHash());
        int problems = scene.Validate();
        Console.WriteLine("scene problems=" + problems);
        int slain = 0;
        for (int i = 0; i < Shared.EnemyCount(); i++)
            if (!Shared.EnemyAlive(i)) slain++;
        Console.WriteLine("faces=" + Shared.EnemyCount() + " slain=" + slain + " bullets that hit=" + Shared.EnemyHits + " bricks=" + Bricks.Made + " stomps=" + Shared.Stomps);
        Destruct.Shutdown();
        bool ok = won == 1 && roofs == 1 && Shared.SwingsDone >= Level.AnchorCount && plugsOpen == plugs0 && Destruct.Detonations > 3 && problems == 0 && Shared.Deaths == 0 && slain == Shared.EnemyCount() && Shared.Stomps >= 2;
        if (!ok) Console.WriteLine("FAIL: the run did not swing across the channel and get to the goal, open the hopper and the tank, break things and stay consistent");
        return ok ? 0 : 1;
    }
}
