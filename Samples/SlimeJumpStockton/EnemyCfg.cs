// From gen_slime.CONFIG (worm = kind 0, bat = kind 1) and then the emoji faces of tools/slime_faces (Grease Pencil heads from the emoji generator, on ASCII art bodies):
// kind 2 zany on a spring, 3 grump on a jetpack, 4 screamer on a spider, 5 boss (the exploding head) on a steam golem. The numbers are SlimeJumpHeads', unchanged.
// The faces float and hurt by touch, so they are all 'flying' (as the bat is).
static class EnemyCfg
{
    public static bool IsFlying(int kind) { return kind >= 1 && kind != 5; }       // the boss, the steam golem, walks (so that the slime can come down on its head)
    public static float Hp(int kind) { if (kind == 2) return 2f; if (kind == 3) return 3f; if (kind == 4) return 4f; if (kind == 5) return 10f; if (kind == 1) return 2f; return 3f; }
    public static float MoveSpeed(int kind) { if (kind == 2) return 2.2f; if (kind == 3) return 1.8f; if (kind == 4) return 1.4f; if (kind == 5) return 1f; if (kind == 1) return 7.5f; return 3.5f; }
    public static float VisionRange(int kind) { if (kind >= 2) return 9f; if (kind == 1) return 10f; return 9f; }
    public static float VisionAngle(int kind) { if (kind == 2) return 180f; if (kind == 3) return 180f; if (kind == 4) return 180f; if (kind == 5) return 180f; if (kind == 1) return 90f; return 90f; }
    public static float PatrolRange(int kind) { if (kind == 2) return 3f; if (kind == 3) return 3f; if (kind == 4) return 3f; if (kind == 5) return 2f; if (kind == 1) return 4f; return 5f; }
    public static float PatrolStopDist(int kind) { if (kind == 1) return 0.5f; return 0.3f; }
    public static float MinPatrolAngle(int kind) { if (kind == 1) return 90f; return 90f; }
    public static float PatrolStopMin(int kind) { if (kind == 1) return 0.25f; return 0.25f; }
    public static float PatrolStopMax(int kind) { if (kind == 1) return 0.75f; return 0.75f; }
    public static float LookToHurt(int kind) { if (kind == 1) return 0.5f; return 0.5f; }
    public static float AttackMin(int kind) { if (kind >= 2) return 0f; if (kind == 1) return 0f; return 3f; }
    public static float AttackMax(int kind) { if (kind >= 2) return 0f; if (kind == 1) return 0f; return 12f; }
    public static float ChaseStopMin(int kind) { if (kind >= 2) return 0f; if (kind == 1) return 0f; return 3f; }
    public static float ChaseStopMax(int kind) { if (kind >= 2) return 0f; if (kind == 1) return 0f; return 6f; }
    public static float ShootInterval(int kind) { if (kind >= 2) return 0f; if (kind == 1) return 0f; return 1.6f; }
    public static float BulletSpeed(int kind) { if (kind >= 2) return 0f; if (kind == 1) return 0f; return 10f; }
    public static float BulletDamage(int kind) { if (kind >= 2) return 0f; if (kind == 1) return 0f; return 1f; }
    public static float BulletLifetime(int kind) { if (kind >= 2) return 0f; if (kind == 1) return 0f; return 3f; }
    public static float ContactDamage(int kind) { if (kind == 1) return 1f; return 1f; }
    public static float ColliderW(int kind) { if (kind == 2) return 1.8f; if (kind == 3) return 1.8f; if (kind == 4) return 1.8f; if (kind == 5) return 2.8f; if (kind == 1) return 1f; return 1.1f; }
    public static float ColliderH(int kind) { if (kind == 2) return 1.6f; if (kind == 3) return 2.4f; if (kind == 4) return 2.4f; if (kind == 5) return 3.0f; if (kind == 1) return 0.6f; return 0.6f; }
    public static float GravityScale(int kind) { if (kind == 2) return 0f; if (kind == 3) return 0f; if (kind == 4) return 0f; if (kind == 1) return 0f; return 1f; }
}
