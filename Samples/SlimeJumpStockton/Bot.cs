using System;
using Prowl.Core2D;
using Prowl.Native.Box2D;

// The driver of the slime (a stand-in for a keyboard and mouse), going right along the street:
//   * it shoots a crate or a boulder it can see within 9 units (they are the things to break), and a sealed bin's or tank's plug (a wall of rock that holds sand or water back);
//   * it jumps what is in its way and the drains in the street;
//   * at the edge of the Deep Water Channel it jumps (it jumps what has no floor ahead), hooks the underside of the first gantry with the lasso, swings, lets go, hooks the next,
//     and so on across the channel, and lands on the far bank;
//   * on the far bank it walks to the goal.
[Script(Order = 0), MaxInstances(1)]
class BotScript
{
    public Component Self;
    Scene2D scene;
    uint solidMask;
    bool wasAttached;
    bool shortHop;              // the jump in progress is over a drain: let go of the button early, so that it is a hop of a few units, not 24
    float hopTime;
    float nearTime;
    float lastX, lastY, stuck, backOff;      // wedged against a crater's wall: back off a moment, then run at it again

    public void Start()
    {
        scene = Scene2D.Current;
        solidMask = (1u << Layers.Wall) | (1u << Layers.Climbable);
    }

    bool Probe(float cx, float cy, float halfW, float halfH)
    {
        return scene.Physics.Sim.OverlapBox(cx, cy, halfW, halfH, 0f, solidMask, false) > 0;
    }

    // is there ground straight below within d units (its feet may be wedged in a crater, not quite on it)?
    static bool GroundWithin(float x, float y, float d)
    {
        for (float k = 0.3f; k <= d; k += 0.1f)
            if (Destruct.SolidAt(x, y - k) || Destruct.SolidAt(x - 0.5f, y - k) || Destruct.SolidAt(x + 0.5f, y - k)) return true;
        return false;
    }

    // is there a clear line to a point (stopping a little short of it: the point may be inside the rock that is to be shot)?
    bool Clear(float x, float y, float tx, float ty, float short_)
    {
        float dx = tx - x;
        float dy = ty - y;
        float d = MathF.Sqrt(dx * dx + dy * dy) - short_;
        if (d <= 0.01f) return true;
        float l = d + short_;
        return scene.Physics.Sim.Raycast(x, y, dx / l, dy / l, d, solidMask, false) < 0;
    }

    public void FixedUpdate()
    {
        if (!InputState.BotOn) return;
        Node pn = Shared.PlayerNode;
        if (pn == null) return;
        float x = pn.WorldX();
        float y = pn.WorldY();
        float halfW = Cfg.ColliderW * 0.5f;
        float halfH = Cfg.ColliderH * 0.5f;
        // the nearest thing to shoot: a crate or boulder in sight, else a plug of this room
        bool headInSight = false;
        bool headChase = false;
        float headD = 0f;
        float headX = 0f;
        float headY = 0f;
        bool engage = false;
        float bestD = 9f;
        float plugRange = 20f;
        float aimX = 0f;
        float aimY = 0f;
        for (int i = 0; i < Destruct.ItemCount(); i++)
        {
            if (!Destruct.ItemLive(scene, i)) continue;
            float dx = Destruct.ItemX(i) - x;
            float dy = Destruct.ItemY(i) - y;
            float d = MathF.Sqrt(dx * dx + dy * dy);
            if (d >= bestD || d < 0.001f) continue;
            if (!Clear(x, y, Destruct.ItemX(i), Destruct.ItemY(i), 0f)) continue;
            bestD = d;
            aimX = Destruct.ItemX(i);
            aimY = Destruct.ItemY(i);
            engage = true;
        }
        for (int i = 0; i < Shared.EnemyCount(); i++)          // a face in sight is the first thing to shoot: it hurts by touch
        {
            if (!Shared.EnemyAlive(i)) continue;
            if (Shared.EnemyKind(i) != 4) continue;                    // all but the screamer (on its spider) are stomped, not shot
            float dx = Shared.EnemyX(i) - x;
            float dy = Shared.EnemyY(i) - y;
            float d = MathF.Sqrt(dx * dx + dy * dy);
            if (d >= 12f || d < 0.001f) continue;
            if (!Clear(x, y, Shared.EnemyX(i), Shared.EnemyY(i), 0f)) continue;
            if (!headInSight || d < headD) { headInSight = true; headD = d; headX = Shared.EnemyX(i); headY = Shared.EnemyY(i); headChase = Shared.EnemyChase(i); }
        }
        if (headInSight) { engage = true; bestD = headD; aimX = headX; aimY = headY; }
        if (!engage)
        {
            // a plug (the lid of a hopper in an overhang) is shot from the street, well within the bullet's reach (30 units a second for 1.2 seconds)
            float plugBest = plugRange;
            for (int i = 0; i < Destruct.PlugCount(); i++)
            {
                if (!Destruct.PlugClosed(i)) continue;
                float dx = Destruct.PlugX(i) - x;
                float dy = Destruct.PlugY(i) - y;
                float d = MathF.Sqrt(dx * dx + dy * dy);
                if (d >= plugBest || d < 0.001f || dy < 2f) continue;
                if (!Clear(x, y, Destruct.PlugX(i), Destruct.PlugY(i), 1.5f)) continue;
                plugBest = d;
                aimX = Destruct.PlugX(i);
                aimY = Destruct.PlugY(i);
                engage = true;
                bestD = 0f;
            }
        }

        // where to go: right, along the street; up onto a roof by swinging from the overhang that hangs out over the street before it, then on to the goal
        float dir = 1f;
        if (Level.GoalX() - x < -0.3f) dir = -1f;
        int next = Shared.SwingsDone < Level.AnchorCount ? Shared.SwingsDone : -1;      // the next gantry to swing from
        // a face that has seen us and is close: do not walk toward it, the gun is what the slime fights with (the walk resumes when it is dead or out of sight)
        if (headInSight && headChase && headD < 10f && dir * (headX - x) > 0f && Shared.PlayerGrounded) dir = 0f;
        InputState.Attack = engage;
        InputState.AimX = aimX;
        InputState.AimY = aimY;
        // stand still to shoot (not in the air)
        if (engage && Shared.PlayerGrounded && !Shared.PlayerClimbing && bestD < 9f) dir = 0f;

        // the lasso: in the air below the next gantry, hook its underside (aiming well up into it); let go once swung far enough forward
        bool lasso = false;
        if (Shared.LassoAttached)
        {
            lasso = true;
            float rx = x - Shared.LassoTipX;
            float ry = Shared.LassoTipY - y;
            float forward = MathF.Atan2(rx, ry) * 57.29578f;      // degrees ahead of straight down
            if (forward >= Level.ReleaseAngle(Shared.SwingsDone)) lasso = false;
        }
        else if (Shared.LassoActive)
            lasso = true;                  // the hook is in flight: let it fly on until it finds the gantry (or its rope runs out)
        else if (!Shared.PlayerGrounded && !Shared.PlayerClimbing && next >= 0)
        {
            float ax = Level.Anchor(next, 0);
            float ay = Level.Anchor(next, 1);
            float dx = ax - x;
            float dy = ay - y;
            if (dy > 1f && dx > 1.5f && MathF.Sqrt(dx * dx + dy * dy) < Cfg.LassoMaxLength + 1f)
            {
                lasso = true;
                InputState.AimX = ax - 2f;
                InputState.AimY = ay + 8f;
                InputState.Attack = false;
            }
        }
        if (wasAttached && !Shared.LassoAttached) Shared.SwingsDone++;                    // let go: that swing is done
        wasAttached = Shared.LassoAttached;
        InputState.Lasso = lasso;
        InputState.ChangeLassoLength = 0;

        // a face to stomp: walk up to it, jump when it is close, and steer in the air to land on its head
        bool stompJump = false;
        int stomp = -1;
        float stompD = 12f;
        for (int i = 0; i < Shared.EnemyCount(); i++)
        {
            if (!Shared.EnemyAlive(i) || Shared.EnemyKind(i) == 4) continue;
            float sd = MathF.Abs(Shared.EnemyX(i) - x);
            if (sd < stompD && Shared.EnemyY(i) - y < 6f) { stompD = sd; stomp = i; }
        }
        if (stomp >= 0 && !Shared.LassoAttached)
        {
            float sdx = Shared.EnemyX(stomp) - x;
            float sdir = sdx > 0f ? 1f : -1f;
            if (Shared.PlayerGrounded && !Shared.PlayerClimbing)
            {
                if (MathF.Abs(sdx) < 3.6f) { stompJump = true; dir = sdir; }
            }
            else if (!Shared.PlayerGrounded)
            {
                if (MathF.Abs(sdx) > 0.3f) dir = sdir; else dir = 0f;                       // above its head: come down on it
            }
        }
        bool jump = false;
        if (Shared.LassoAttached)
            jump = false;
        else if (Shared.PlayerGrounded && !Shared.PlayerClimbing)
        {
            bool wallAhead = Probe(x + dir * (halfW + 0.25f), y, 0.15f, halfH * 0.6f) || Probe(x + dir * (halfW + 1.2f), y + 0.4f, 0.1f, halfH * 0.5f);      // a wall a run-up away: jump early, so as to arc over it (a jump at its foot catches a corner)
            bool floorAhead = Probe(x + dir * (halfW + 0.2f), y - halfH - 0.15f, 0.1f, 0.12f);
            shortHop = false;
            hopTime = 0f;
            if (dir != 0f && (wallAhead || !floorAhead)) jump = true;
            if (stompJump) jump = true;
            if (dir != 0f && !wallAhead && !floorAhead && x < Level.ChannelX0 - 4f) shortHop = true;       // a drain: a short hop. (The channel is crossed with a full jump and the lasso)
        }
        else if (Shared.PlayerJumping)
        {
            hopTime += Cfg.Dt;
            jump = !shortHop || hopTime < 0.2f;           // full-height jumps (a short hop over a drain lets go early)
        }
        if (MathF.Abs(x - lastX) < 0.02f && MathF.Abs(y - lastY) < 0.02f && !Shared.LassoAttached) stuck += Cfg.Dt; else stuck = 0f;
        lastX = x;
        lastY = y;
        if (Probe(x + dir * (halfW + 0.12f), y, 0.1f, halfH * 0.6f)) nearTime += Cfg.Dt; else nearTime = 0f;      // pressed against a wall for long: it is no use to jump at its foot
        if (nearTime > 0.5f) { stuck = 1f; nearTime = 0f; }
        if (stuck > 0.4f) { backOff = 0.6f; stuck = 0f; }
        if (backOff > 0f)
        {
            backOff -= Cfg.Dt;
            dir = -1f;
            jump = false;
            if (!Probe(x - halfW - 0.4f, y - halfH - 0.15f, 0.1f, 0.12f)) { dir = 0f; backOff = 0f; }      // not off a ledge, into a drain
        }
        InputState.Move = dir;
        InputState.Jump = jump;
    }
}
