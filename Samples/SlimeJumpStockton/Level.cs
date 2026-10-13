// Stockton, California, from the side: the street, the sewer under it, and the Deep Water Channel: a gap of 36 units that cuts the street in two and opens into the sewer. The slime
// cannot jump it (it jumps about 24); it crosses on the lasso, swinging from the undersides of three gantries (billboards and signs hung out over the channel) one after another.
// A sewer runs under the whole street with sewage in it, and the storm drains open into it. The whole world is one terrain bitmap (Destruct.cs) 96 units wide and 36 high, in
// world units (x to the right, y up).
//
//        y 36  ...........................................................................
//        y 30  .                                     ######    ######    ######            <- the gantries: their undersides are what the lasso hooks
//        y 16  =====street======= drain ======street==|                                |==street========goal
//        y 7.5 ################# slab ###############|           the channel          |#####################
//        y 2   ~~~~ sewage ~~~~~~ the sewer tunnel ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
static class Level
{
    // the faces (tools/slime_faces: Grease Pencil heads on ASCII art bodies), floating about their posts: 2 zany over the first lot, 3 grump past the drain, 4 screamer
    // over the channel's near edge, 5 the boss over the goal
    public const int EnemyCount = 4;
    public static int EnemyKind(int i) { return 2 + i; }
    public static float EnemyX(int i)
    {
        if (i == 0) return 19f;
        if (i == 1) return 36f;
        if (i == 2) return 47f;
        return 87f;
    }
    public static float EnemyY(int i)
    {
        if (i == 0) return StreetY + 1.7f;
        if (i == 1) return StreetY + 2.1f;
        if (i == 2) return StreetY + 5.5f;
        return StreetY + 1.7f;
    }

    public const float Width = 96f;
    public const float Height = 36f;
    public const float StreetY = 16f;         // the top of the street
    public const float SewerTop = 7.5f;       // the roof of the sewer tunnel, the underside of the street's slab
    public const float SewerFloor = 2f;       // the top of the bedrock under it
    public const float SideWall = 1.5f;
    public const float SewageDepth = 1.8f;

    // the Deep Water Channel: no street between these
    public const float ChannelX0 = 44f;
    public const float ChannelX1 = 80f;

    // the gantries over it: from where each starts to where it ends, its underside and its top. The first holds a sealed hopper of sand and the second a tank of water (Destruct.cs)
    public const int Gantries = 3;
    public static float GantryX0(int i) { return i == 0 ? 49f : (i == 1 ? 60f : 71f); }
    public static float GantryX1(int i) { return i == 0 ? 56f : (i == 1 ? 67f : 78f); }
    public static float GantryBottom(int i) { return 28f; }
    public static float GantryTop(int i) { return 32f; }

    // the storm drains: openings in the street's slab that let into the sewer (the slime jumps them)
    public const int Drains = 1;
    public static float DrainX0(int i) { return 27f; }
    public static float DrainX1(int i) { return 32f; }

    // where the slime hooks (the middle of each gantry's underside), and where it lets go (degrees ahead of straight down)
    public const int AnchorCount = 2;
    public static float Anchor(int i, int k)
    {
        float mid = (GantryX0(i) + GantryX1(i)) * 0.5f;
        float under = GantryBottom(i);
        if (k == 0) return mid;
        return under;
    }
    public static float ReleaseAngle(int i) { return 25f; }

    // the checkpoints: where a slime that has fallen into the sewer starts again
    public const int Checkpoints = 2;
    public static float CheckpointX(int i) { return i == 0 ? 4.3f : 40f; }
    public static float CheckpointTrigger(int i) { return i == 0 ? 0f : 39f; }

    public static float SpawnX() { return 4.3f; }
    public static float SpawnY() { return StreetY + Cfg.ColliderH * 0.5f + 0.05f; }
    public static float GoalX() { return 90f; }
    public static float GoalY() { return StreetY + 1f; }
    public static float MinY() { return 0f; }

    // Layer collision matrix: rows[a] bit b set == layers a and b collide.
    public static uint[] LayerRows()
    {
        uint[] r = new uint[32];
        for (int i = 0; i < 32; i++) r[i] = 0xFFFFFFFFu;
        r[0] &= ~(1u << 20); r[20] &= ~(1u << 0);
        r[1] &= ~(1u << 20); r[20] &= ~(1u << 1);
        r[2] &= ~(1u << 20); r[20] &= ~(1u << 2);
        r[3] &= ~(1u << 20); r[20] &= ~(1u << 3);
        r[4] &= ~(1u << 20); r[20] &= ~(1u << 4);
        r[5] &= ~(1u << 20); r[20] &= ~(1u << 5);
        r[6] &= ~(1u << 19); r[19] &= ~(1u << 6);
        r[6] &= ~(1u << 20); r[20] &= ~(1u << 6);
        r[6] &= ~(1u << 25); r[25] &= ~(1u << 6);
        r[8] &= ~(1u << 9); r[9] &= ~(1u << 8);
        r[8] &= ~(1u << 19); r[19] &= ~(1u << 8);
        r[8] &= ~(1u << 20); r[20] &= ~(1u << 8);
        r[8] &= ~(1u << 25); r[25] &= ~(1u << 8);
        r[8] &= ~(1u << 26); r[26] &= ~(1u << 8);
        r[9] &= ~(1u << 9); r[9] &= ~(1u << 9);
        r[9] &= ~(1u << 10); r[10] &= ~(1u << 9);
        r[9] &= ~(1u << 19); r[19] &= ~(1u << 9);
        r[9] &= ~(1u << 20); r[20] &= ~(1u << 9);
        r[9] &= ~(1u << 25); r[25] &= ~(1u << 9);
        r[9] &= ~(1u << 26); r[26] &= ~(1u << 9);
        r[10] &= ~(1u << 19); r[19] &= ~(1u << 10);
        r[10] &= ~(1u << 20); r[20] &= ~(1u << 10);
        r[10] &= ~(1u << 25); r[25] &= ~(1u << 10);
        r[10] &= ~(1u << 26); r[26] &= ~(1u << 10);
        r[11] &= ~(1u << 20); r[20] &= ~(1u << 11);
        r[12] &= ~(1u << 20); r[20] &= ~(1u << 12);
        r[13] &= ~(1u << 20); r[20] &= ~(1u << 13);
        r[14] &= ~(1u << 20); r[20] &= ~(1u << 14);
        r[16] &= ~(1u << 20); r[20] &= ~(1u << 16);
        r[17] &= ~(1u << 20); r[20] &= ~(1u << 17);
        r[18] &= ~(1u << 20); r[20] &= ~(1u << 18);
        r[19] &= ~(1u << 20); r[20] &= ~(1u << 19);
        r[19] &= ~(1u << 25); r[25] &= ~(1u << 19);
        r[19] &= ~(1u << 26); r[26] &= ~(1u << 19);
        r[20] &= ~(1u << 20); r[20] &= ~(1u << 20);
        r[20] &= ~(1u << 21); r[21] &= ~(1u << 20);
        r[20] &= ~(1u << 22); r[22] &= ~(1u << 20);
        r[20] &= ~(1u << 23); r[23] &= ~(1u << 20);
        r[20] &= ~(1u << 24); r[24] &= ~(1u << 20);
        r[20] &= ~(1u << 25); r[25] &= ~(1u << 20);
        r[20] &= ~(1u << 26); r[26] &= ~(1u << 20);
        r[20] &= ~(1u << 27); r[27] &= ~(1u << 20);
        r[20] &= ~(1u << 28); r[28] &= ~(1u << 20);
        r[20] &= ~(1u << 29); r[29] &= ~(1u << 20);
        r[20] &= ~(1u << 30); r[30] &= ~(1u << 20);
        r[20] &= ~(1u << 31); r[31] &= ~(1u << 20);
        r[25] &= ~(1u << 25); r[25] &= ~(1u << 25);
        r[26] &= ~(1u << 26); r[26] &= ~(1u << 26);
        // crates (27) and debris (28) meet the walls (7), the climbable walls (15) and each other, and nothing else: the slime, bullets and pickups pass through them
        for (int k = 0; k < 32; k++)
        {
            if (k == Layers.Wall || k == Layers.Climbable || k == Layers.Crate || k == Layers.Debris) continue;
            r[Layers.Crate] &= ~(1u << k); r[k] &= ~(1u << Layers.Crate);
            r[Layers.Debris] &= ~(1u << k); r[k] &= ~(1u << Layers.Debris);
        }
        return r;
    }
}
