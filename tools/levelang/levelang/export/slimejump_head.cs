static class Level
{
    static float spawnX, spawnY, goalX, goalY, minY, minX, maxX, maxY;
    public static float MinX() { return minX; }
    public static float MaxX() { return maxX; }
    public static float MaxY() { return maxY; }
    public static float SpawnX() { return spawnX; }
    public static float SpawnY() { return spawnY; }
    public static float GoalX() { return goalX; }
    public static float GoalY() { return goalY; }
    public static float MinY() { return minY; }
    static float[] Walls;
    public static int WallCount;
    public static float Wall(int i, int k) { return At(Walls, i * 4 + k); }
    static float[] Climbs;
    public static int ClimbCount;
    public static float Climb(int i, int k) { return At(Climbs, i * 4 + k); }
    static float[] Spikes;
    public static int SpikeCount;
    public static float Spike(int i, int k) { return At(Spikes, i * 4 + k); }
    static float[] Saves;
    public static int SaveCount;
    public static float Save(int i, int k) { return At(Saves, i * 2 + k); }
    static float[] Gems;
    public static int GemCount;
    public static float Gem(int i, int k) { return At(Gems, i * 2 + k); }
    static float[] Anchors;
    public static int AnchorCount;
    public static float Anchor(int i, int k) { return At(Anchors, i * 2 + k); }
    static float[] Crumbles;
    public static int CrumblyCount;
    public static float CrumblyTile(int i, int k) { return At(Crumbles, i * 4 + k); }
    static float[] Shooters;
    public static int ShooterCount;
    public static float Shooter(int i, int k) { return At(Shooters, i * 4 + k); }
    static float[] Enemies;
    public static int EnemyCount;
    public static int EnemyKind(int i) { return (int)At(Enemies, i * 3); }
    public static float EnemyX(int i) { return At(Enemies, i * 3 + 1); }
    public static float EnemyY(int i) { return At(Enemies, i * 3 + 2); }
    static float At(float[] a, int i) { return a[i]; }
    static void Set4(float[] a, int i, float x, float y, float w, float h) { a[i * 4] = x; a[i * 4 + 1] = y; a[i * 4 + 2] = w; a[i * 4 + 3] = h; }
    static void Set2(float[] a, int i, float x, float y) { a[i * 2] = x; a[i * 2 + 1] = y; }

    public static void Init()
    {
