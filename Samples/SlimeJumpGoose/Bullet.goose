// A bullet from the blaster: flies straight (the Slime script puts it at the slime, turns it toward the aim point and gives it this script), is gone when it meets a wall
// or after a second and a bit, and shoots a worm (tag 2) it comes to: the worm's tag becomes 5 and the worm takes it from there.

let BULLET_SPEED: f32 = 30.0;
let DT: f32 = 0.016666668;

// script(max_instances = 8)
struct Bullet {
    node: i32,
    dx: f32,
    dy: f32,
    life: f32,
}

fn start(b: Bullet&) {
    let ang = node_angle(b.node);
    b.dx = math_cos(ang);
    b.dy = math_sin(ang);
    b.life = 1.2;
    add_sprite(b.node, 1, 0.3, 0.3, 1.0, 0.9, 0.3);
}

fn fixed_update(b: Bullet&) {
    b.life -= DT;
    let step = BULLET_SPEED * DT;
    let x = node_x(b.node);
    let y = node_y(b.node);
    if b.life <= 0.0 || raycast(x, y, b.dx, b.dy, step + 0.2, 1) >= 0 {
        destroy_node(b.node);
        return;
    }
    let nx = x + b.dx * step;
    let ny = y + b.dy * step;
    set_pos(b.node, nx, ny);
    var i: i32 = 0;
    let n = node_slots();
    while i < n {
        if get_tag(i) == 2 {
            let ex = node_x(i) - nx;
            let ey = node_y(i) - ny;
            if ex > -0.6 && ex < 0.6 && ey > -0.6 && ey < 0.6 {
                set_tag(i, 5);
                destroy_node(b.node);
                return;
            }
        }
        i += 1;
    }
}
