// A crumbly platform: solid, but a second after the slime has stood on it, it dissolves (until the slime is back at its checkpoint).

let DT: f32 = 0.016666668;

// script(max_instances = 16)
struct Crumbly {
    node: i32,
    timer: f32,
    gone: i32,
    deaths: i32,
    home_x: f32,
    home_y: f32,
}

fn start(c: Crumbly&) {
    add_body(c.node, 0);
    add_box(c.node, 1.0, 1.0);
    c.deaths = get_global(0) as i32;
    c.home_x = node_x(c.node);
    c.home_y = node_y(c.node);
}

fn fixed_update(c: Crumbly&) {
    let d = get_global(0) as i32;
    if d != c.deaths {                       // the slime died: the platform is back
        c.deaths = d;
        c.timer = 0.0;
        if c.gone != 0 {
            c.gone = 0;
            set_pos(c.node, c.home_x, c.home_y);
        }
    }
    if c.gone != 0 { return; }
    let s = (get_global(21) as i32) - 1;
    if s < 0 { return; }
    let dx = node_x(s) - node_x(c.node);
    let dy = node_y(s) - node_y(c.node);
    if dx > -0.95 && dx < 0.95 && dy > 0.7 && dy < 1.1 { c.timer += DT; }
    if c.timer >= 1.0 {
        c.gone = 1;
        set_pos(c.node, c.home_x, c.home_y - 100.0);       // (far below the level: not solid, not seen. A node that is switched off would not run to come back.)
    }
}
