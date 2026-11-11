// The bot: plays the level by writing the numbers a player would (walk, jump, aim, shoot, lasso) into the globals, which the Slime script reads while G_BOT is 1.
// The T key switches it on and off. It looks with the engine's probes: walls and gaps ahead, vines, spikes (tag 9), worms (tag 2), arrows (tag 4) and anchors (tag 7).

let G_BOT: i32 = 6;
let G_IN_MOVE: i32 = 7;
let G_IN_JUMP: i32 = 8;
let G_IN_ATTACK: i32 = 9;
let G_AIM_X: i32 = 10;
let G_AIM_Y: i32 = 11;
let G_IN_LASSO: i32 = 12;
let G_GROUNDED: i32 = 15;
let G_CLIMBING: i32 = 16;
let G_ATTACHED: i32 = 18;
let G_PLAYER: i32 = 21;

// script(max_instances = 1)
struct Bot {
    node: i32,
    t_was: i32,
    phase: i32,         // 0 walking, 1 the lasso is out, 2 let go and flying
    anchor: i32,
    wait: i32,          // frames the lasso has been out and not caught
}

fn fixed_update(b: Bot&) {
    let t = key_down(84);
    if t != 0 && b.t_was == 0 { set_global(G_BOT, 1.0 - get_global(G_BOT)); }
    b.t_was = t;
    if get_global(G_BOT) < 0.5 { return; }
    let s = (get_global(G_PLAYER) as i32) - 1;
    if s < 0 { return; }
    let x = node_x(s);
    let y = node_y(s);
    let grounded = get_global(G_GROUNDED) as i32;
    let climbing = get_global(G_CLIMBING) as i32;
    let attached = get_global(G_ATTACHED) as i32;
    var jump: i32 = 0;
    var attack: i32 = 0;
    var lasso: i32 = 0;
    set_global(G_IN_MOVE, 1.0);

    if b.phase == 1 {                                   // on the rope: pump to the right and let go over the far side
        lasso = 1;
        if attached != 0 {
            if x > node_x(b.anchor) + 4.3 { b.phase = 2; lasso = 0; }
        } else {
            b.wait += 1;
            if b.wait > 40 { b.phase = 0; lasso = 0; }
        }
    } else if b.phase == 2 {
        if grounded != 0 { b.phase = 0; }
    } else {
        // what is ahead
        let wall = overlap_box(x + 0.55, y, 0.1, 0.3, 1);
        let vine = overlap_box(x + 0.4, y, 0.3, 0.3, 32768);
        if climbing != 0 || (wall > 0 && vine > 0) { jump = 1; }
        else if wall > 0 { jump = 1; }
        // a gap: the ground ahead is missing
        if grounded != 0 && climbing == 0 && raycast(x + 0.7, y, 0.0, -1.0, 1.6, 1) < 0 {
            var far: f32 = 0.0;
            var k: f32 = 1.0;
            while k < 14.0 {
                if far == 0.0 && raycast(x + k, y, 0.0, -1.0, 1.6, 1) >= 0 { far = k; }
                k += 1.0;
            }
            var a: i32 = -1;
            var i: i32 = 0;
            let n = node_slots();
            while i < n {
                if get_tag(i) == 7 && node_x(i) > x && node_x(i) - x < 7.6 && node_y(i) > y - 1.0 { a = i; }
                i += 1;
            }
            if (far == 0.0 || far > 9.0) && a >= 0 {
                b.phase = 1;
                b.anchor = a;
                b.wait = 0;
                set_global(G_AIM_X, node_x(a));
                set_global(G_AIM_Y, node_y(a));
                lasso = 1;
            } else {
                jump = 1;
            }
        }
        // spikes and arrows: jump over
        var i2: i32 = 0;
        let n2 = node_slots();
        while i2 < n2 {
            let tg = get_tag(i2);
            let dx = node_x(i2) - x;
            let dy = node_y(i2) - y;
            if tg == 9 && dx > 0.5 && dx < 2.4 && dy > -1.2 && dy < 1.0 { jump = 1; }
            if tg == 4 && dx > 0.0 && dx < 8.0 && dy > -1.0 && dy < 1.0 { jump = 1; }
            if tg == 2 && dx > 0.0 && dx < 9.0 && dy > -1.5 && dy < 1.5 && grounded != 0 {     // a worm ahead: shoot it
                attack = 1;
                set_global(G_AIM_X, node_x(i2));
                set_global(G_AIM_Y, node_y(i2));
            }
            i2 += 1;
        }
    }
    set_global(G_IN_JUMP, jump as f32);
    set_global(G_IN_ATTACK, attack as f32);
    set_global(G_IN_LASSO, lasso as f32);
}
