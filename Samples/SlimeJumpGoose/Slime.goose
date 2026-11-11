// The player, ported from SlimeJump's Player.cs and Lasso.cs: walk, a jump you can cut short, climbing the vines, a blaster, a lasso to swing on,
// back to the last checkpoint when hurt or fallen. (Input is the keyboard and mouse, or the Bot's numbers in the globals when it is switched on.)
//
// Goose, the Crust subset: the engine's calls are set_pos, set_velocity, raycast, overlap_box ... (Native/Engine2D/Engine.cs, in snake_case), nodes are i32 handles, and the scripts
// talk through node tags (1 slime, 2 worm, 3 "the slime was hurt", 4 arrow, 6 bullet) and the globals below.

let G_DEATHS: i32 = 0;
let G_SAVES: i32 = 1;
let G_SAVE_X: i32 = 2;
let G_SAVE_Y: i32 = 3;
let G_BOT: i32 = 6;          // 1: the bot plays (the numbers below come from it)
let G_IN_MOVE: i32 = 7;
let G_IN_JUMP: i32 = 8;
let G_IN_ATTACK: i32 = 9;
let G_AIM_X: i32 = 10;
let G_AIM_Y: i32 = 11;
let G_IN_LASSO: i32 = 12;
let G_IN_REEL: i32 = 13;
let G_GROUNDED: i32 = 15;    // what the bot looks at
let G_CLIMBING: i32 = 16;
let G_JUMPING: i32 = 17;
let G_ATTACHED: i32 = 18;
let G_PLAYER: i32 = 21;      // the slime's node + 1

let MASK_WALL: i32 = 1;          // layer 0: the walls (what the probes and the rope meet)
let MOVE_SPEED: f32 = 7.0;
let JUMP_SPEED: f32 = 12.5;
let CLIMB_SPEED: f32 = 7.0;
let CLIMB_FALL: f32 = 2.0;
let DT: f32 = 0.016666668;
let LASSO_MAX: f32 = 7.0;
let LASSO_SPEED: f32 = 20.0;
let SWING_ACCEL: f32 = 28.0;
let SWING_MAX: f32 = 11.0;

// script(max_instances = 1)
struct Slime {
    node: i32,
    rope: i32,
    jumping: i32,
    climbing: i32,
    lock: f32,          // seconds left of a respawn pause
    shoot_timer: f32,
    lasso: i32,         // 0 not out, 1 flying, 2 attached
    prev_lasso: i32,
    off_x: f32,         // the flying tip, from the slime
    off_y: f32,
    dir_x: f32,
    dir_y: f32,
    tip_x: f32,
    tip_y: f32,
    len: f32,
}

fn bot() -> i32 {
    if get_global(G_BOT) > 0.5 { return 1; }
    return 0;
}

fn in_move() -> f32 {
    if bot() != 0 { return get_global(G_IN_MOVE); }
    var dir: f32 = 0.0;
    if key_down(263) != 0 || key_down(65) != 0 { dir -= 1.0; }     // left arrow, A
    if key_down(262) != 0 || key_down(68) != 0 { dir += 1.0; }     // right arrow, D
    return dir;
}

fn in_jump() -> i32 {
    if bot() != 0 { if get_global(G_IN_JUMP) > 0.5 { return 1; } return 0; }
    if key_down(32) != 0 || key_down(265) != 0 || key_down(87) != 0 { return 1; }     // space, up arrow, W
    return 0;
}

fn in_attack() -> i32 {
    if bot() != 0 { if get_global(G_IN_ATTACK) > 0.5 { return 1; } return 0; }
    return mouse_down(0);
}

fn in_lasso() -> i32 {
    if bot() != 0 { if get_global(G_IN_LASSO) > 0.5 { return 1; } return 0; }
    return mouse_down(2);
}

fn in_reel() -> f32 {
    if bot() != 0 { return get_global(G_IN_REEL); }
    var r: f32 = 0.0;
    if key_down(87) != 0 || key_down(265) != 0 { r -= 1.0; }      // W reels in
    if key_down(83) != 0 || key_down(264) != 0 { r += 1.0; }      // S lets out
    return r;
}

fn aim_x() -> f32 {
    if bot() != 0 { return get_global(G_AIM_X); }
    return mouse_world_x();
}

fn aim_y() -> f32 {
    if bot() != 0 { return get_global(G_AIM_Y); }
    return mouse_world_y();
}

fn dist(dx: f32, dy: f32) -> f32 {
    return math_sqrt(dx * dx + dy * dy);
}

fn start(s: Slime&) {
    let x = node_x(s.node);
    let y = node_y(s.node);
    if get_global(G_SAVES) < 0.5 {
        set_global(G_SAVE_X, x);
        set_global(G_SAVE_Y, y);
    }
    set_layer(s.node, 6);
    add_body_ex(s.node, 2, 1, 1.0);        // dynamic, does not tumble
    add_box_ex(s.node, 0.9, 0.75, 0.0);    // no friction: it slides down a wall instead of sticking to it
    set_tag(s.node, 1);
    set_global(G_PLAYER, (s.node as f32) + 1.0);
    s.rope = new_node();
    add_sprite(s.rope, 0, 1.0, 0.07, 0.85, 0.65, 0.3);
    set_active(s.rope, 0);
}

fn die(s: Slime&) {
    set_global(G_DEATHS, get_global(G_DEATHS) + 1.0);
    set_pos(s.node, get_global(G_SAVE_X), get_global(G_SAVE_Y));
    set_velocity(s.node, 0.0, 0.0);
    set_tag(s.node, 1);
    s.jumping = 0;
    s.climbing = 0;
    s.lasso = 0;
    set_active(s.rope, 0);
    s.lock = 0.5;
}

// The lasso: the right mouse button throws a hook toward the pointer; it flies until it meets a wall, then the slime swings on the rope
// (W / S reel it in and out, A / D pump the swing); letting go of the button lets go of the rope and keeps the swing's speed.
fn update_lasso(s: Slime&, x: f32, y: f32) {
    let input = in_lasso();
    if input != 0 && s.prev_lasso == 0 {
        var ax = aim_x() - x;
        var ay = aim_y() - y;
        let al = dist(ax, ay);
        if al < 0.001 { ax = 0.0; ay = 1.0; }
        let n = dist(ax, ay);
        s.dir_x = ax / n;
        s.dir_y = ay / n;
        s.off_x = 0.0;
        s.off_y = 0.0;
        s.lasso = 1;
    } else if input == 0 && s.prev_lasso != 0 {
        s.lasso = 0;
    }
    s.prev_lasso = input;
    if s.lasso == 1 {
        let reach = dist(s.off_x, s.off_y);
        var step = LASSO_SPEED * DT;
        if LASSO_MAX - reach < step { step = LASSO_MAX - reach; }
        var hit: i32 = -1;
        if step > 0.0 { hit = raycast(x + s.off_x, y + s.off_y, s.dir_x, s.dir_y, step, MASK_WALL); }
        if hit >= 0 {
            s.tip_x = ray_x();
            s.tip_y = ray_y();
            s.len = dist(s.tip_x - x, s.tip_y - y);
            s.lasso = 2;
        } else if step <= 0.0 {
            s.lasso = 0;
        } else {
            s.off_x += s.dir_x * step;
            s.off_y += s.dir_y * step;
            s.tip_x = x + s.off_x;
            s.tip_y = y + s.off_y;
        }
    }
    if s.lasso == 2 {
        let reel = in_reel();
        s.len += reel * 7.0 * DT;
        if s.len < 0.5 { s.len = 0.5; }
        if s.len > LASSO_MAX { s.len = LASSO_MAX; }
        let dx = x - s.tip_x;
        let dy = y - s.tip_y;
        let d = dist(dx, dy);
        var vx = velocity_x(s.node);
        var vy = velocity_y(s.node);
        if d > 0.001 {
            let nx = dx / d;
            let ny = dy / d;
            if d >= s.len - 0.02 {                          // taut: no speed away from the hook, and a pull back onto the circle if it has drifted out
                let vn = vx * nx + vy * ny;
                if vn > 0.0 { vx -= nx * vn; vy -= ny * vn; }
                if d > s.len {
                    vx -= nx * (d - s.len) * 12.0;
                    vy -= ny * (d - s.len) * 12.0;
                }
            }
            let m = in_move();
            if m != 0.0 {                                      // pump the swing along the circle, toward where the player pushes
                var tx = -ny;
                var ty = nx;
                if tx * m < 0.0 { tx = -tx; ty = -ty; }
                if vx * tx + vy * ty < SWING_MAX {                  // (up to a top speed)
                    vx += tx * SWING_ACCEL * DT;
                    vy += ty * SWING_ACCEL * DT;
                }
            }
            set_velocity(s.node, vx, vy);
        }
    }
    if s.lasso != 0 {
        let sx = s.tip_x - x;
        let sy = s.tip_y - y;
        set_active(s.rope, 1);
        set_pos(s.rope, x + sx * 0.5, y + sy * 0.5);
        set_angle(s.rope, math_atan2(sy, sx));
        set_scale(s.rope, dist(sx, sy), 1.0);
    } else {
        set_active(s.rope, 0);
    }
}

fn fixed_update(s: Slime&) {
    let x = node_x(s.node);
    let y = node_y(s.node);
    if s.lock > 0.0 {
        s.lock -= DT;
        set_velocity(s.node, 0.0, 0.0);
        return;
    }
    if get_tag(s.node) == 3 || y < -3.0 {
        die(s);
        return;
    }
    let half_w: f32 = 0.45;
    let half_h: f32 = 0.375;

    update_lasso(s, x, y);
    let attached: i32 = if s.lasso == 2 { 1 } else { 0 };

    // the blaster, toward the aim point
    s.shoot_timer -= DT;
    if in_attack() != 0 && s.shoot_timer <= 0.0 {
        var ax = aim_x() - x;
        var ay = aim_y() - y;
        let al = dist(ax, ay);
        if al < 0.001 { ax = 1.0; ay = 0.0; }
        s.shoot_timer = 0.35;
        let b = new_node();
        if b >= 0 {
            set_pos(b, x, y);
            set_angle(b, math_atan2(ay, ax));
            set_tag(b, 6);
            attach_script(b, SCRIPT_BULLET);
        }
    }

    var vy = velocity_y(s.node);
    var vx = velocity_x(s.node);
    let m = in_move();
    let jump = in_jump();
    let grounded: i32 = if overlap_box(x, y - half_h - 0.05, half_w * 0.9, 0.06, MASK_WALL) > 0 { 1 } else { 0 };    // something solid just under its feet

    // walking: a wall in the way stops it (so it can slide down it)
    var hitting_wall: i32 = 0;
    if m != 0.0 {
        let side: f32 = if m > 0.0 { 1.0 } else { -1.0 };
        if overlap_box(x + side * (half_w + 0.03), y, 0.03, half_h * 0.9, MASK_WALL) > 0 { hitting_wall = 1; }
    }
    if attached == 0 {
        if hitting_wall == 0 && grounded != 0 && m != 0.0 && vx > -0.5 && vx < 0.5 && s.lock <= 0.0 {
            set_pos(s.node, x, y + 0.03);                // stopped by nothing it can see: the seam between two blocks catching its corner; a hop over it
        }
        vx = 0.0;
        if hitting_wall == 0 { vx = m * MOVE_SPEED; }
    }

    // climbing: touching a vine; jump climbs, otherwise slide down slowly
    let was_climbing = s.climbing;
    s.climbing = 0;
    if attached == 0 && overlap_box(x, y, 0.6, 0.225, 32768) > 0 { s.climbing = 1; }

    // jumping (let go early for a short hop)
    if s.climbing == 0 && attached == 0 {
        if jump != 0 && grounded != 0 && s.jumping == 0 {
            vy = JUMP_SPEED;
            s.jumping = 1;
        } else if s.jumping != 0 {
            if jump == 0 {
                if vy > 0.0 { vy = vy * 0.4; }
                s.jumping = 0;
            } else if vy <= 0.0 {
                s.jumping = 0;
            }
        }
    }
    if s.climbing != 0 {
        if jump != 0 { vy = CLIMB_SPEED; s.jumping = 1; } else { vy = -CLIMB_FALL; s.jumping = 0; }
    } else if was_climbing != 0 && jump != 0 {
        vy = JUMP_SPEED * 0.8;                 // pop over the lip
    }
    if attached == 0 { set_velocity(s.node, vx, vy); }

    set_global(G_GROUNDED, grounded as f32);
    set_global(G_CLIMBING, s.climbing as f32);
    set_global(G_JUMPING, s.jumping as f32);
    set_global(G_ATTACHED, attached as f32);
}
