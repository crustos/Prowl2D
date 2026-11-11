// An arrow from a turret: flies straight, hurts the slime it hits (its tag becomes 3), is gone against a wall or after four seconds. Its tag is 4 (the bot looks for it).

let ARROW_SPEED: f32 = 9.0;
let DT: f32 = 0.016666668;

// script(max_instances = 8)
struct Arrow {
    node: i32,
    dx: f32,
    dy: f32,
    life: f32,
}

fn start(a: Arrow&) {
    let ang = node_angle(a.node);
    a.dx = math_cos(ang);
    a.dy = math_sin(ang);
    a.life = 4.0;
    set_tag(a.node, 4);
    add_sprite(a.node, 0, 0.7, 0.12, 0.9, 0.8, 0.5);
}

fn fixed_update(a: Arrow&) {
    a.life -= DT;
    let step = ARROW_SPEED * DT;
    let x = node_x(a.node);
    let y = node_y(a.node);
    if a.life <= 0.0 || raycast(x, y, a.dx, a.dy, step + 0.35, 1) >= 0 {
        destroy_node(a.node);
        return;
    }
    let nx = x + a.dx * step;
    let ny = y + a.dy * step;
    set_pos(a.node, nx, ny);
    let s = (get_global(21) as i32) - 1;
    if s >= 0 {
        let ex = node_x(s) - nx;
        let ey = node_y(s) - ny;
        if ex > -0.55 && ex < 0.55 && ey > -0.8 && ey < 0.8 {
            set_tag(s, 3);
            destroy_node(a.node);
        }
    }
}
