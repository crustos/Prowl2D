// A turret: a solid block that, once a second, shoots an arrow along the ground toward the slime when the slime is within twelve units, about as high as the turret, and nothing is in the way.

let ARROW_COOLDOWN: f32 = 1.0;
let DT: f32 = 0.016666668;

// script(max_instances = 4)
struct Turret {
    node: i32,
    timer: f32,
}

fn start(t: Turret&) {
    add_body(t.node, 0);
    add_box(t.node, 1.0, 1.0);
    t.timer = 0.5;
}

fn fixed_update(t: Turret&) {
    t.timer -= DT;
    if t.timer > 0.0 { return; }
    let s = (get_global(21) as i32) - 1;
    if s < 0 { return; }
    let x = node_x(t.node);
    let y = node_y(t.node);
    let sx = node_x(s) - x;
    let sy = node_y(s) - y;
    let d: f32 = if sx < 0.0 { -sx } else { sx };
    if d > 12.0 || d < 1.0 || sy > 4.0 || sy < -4.0 { return; }
    let dx: f32 = if sx < 0.0 { -1.0 } else { 1.0 };
    let dy: f32 = 0.0;
    if raycast(x + dx * 0.8, y + dy * 0.8, dx, dy, d - 0.8, 1) >= 0 { return; }      // a wall between
    t.timer = ARROW_COOLDOWN;
    let a = new_node();
    if a >= 0 {
        set_pos(a, x + dx * 0.8, y + dy * 0.8);
        set_angle(a, math_atan2(dy, dx));
        attach_script(a, SCRIPT_ARROW);
    }
}
