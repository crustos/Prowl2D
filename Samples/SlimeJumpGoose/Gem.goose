// A gem: picked up when the slime comes close (and counted in the globals). It stays picked up once the slime has reached a checkpoint after it;
// if the slime dies first, it is back where it was.

// script(max_instances = 32)
struct Gem {
    node: i32,
    state: i32,         // 0 there, 1 picked up (not kept yet), 2 kept
    saves: i32,
    deaths: i32,
    home_y: f32,
}

fn start(g: Gem&) {
    g.saves = get_global(1) as i32;
    g.deaths = get_global(0) as i32;
    g.home_y = node_y(g.node);
}

fn fixed_update(g: Gem&) {
    let saves = get_global(1) as i32;
    let deaths = get_global(0) as i32;
    if saves != g.saves {
        g.saves = saves;
        if g.state == 1 { g.state = 2; }
    }
    if deaths != g.deaths {
        g.deaths = deaths;
        if g.state == 1 {
            g.state = 0;
            set_pos(g.node, node_x(g.node), g.home_y);
            set_global(4, get_global(4) - 1.0);
        }
    }
    if g.state != 0 { return; }
    let s = (get_global(21) as i32) - 1;
    if s < 0 { return; }
    let dx = node_x(s) - node_x(g.node);
    let dy = node_y(s) - node_y(g.node);
    if dx > -0.7 && dx < 0.7 && dy > -0.7 && dy < 0.7 {
        g.state = 1;
        set_pos(g.node, node_x(g.node), g.home_y - 100.0);       // (far below the level: not seen. A node that is switched off would not run to come back.)
        set_global(4, get_global(4) + 1.0);
    }
}
