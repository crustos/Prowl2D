// The goal flag: when the slime reaches it, its tag becomes 99 and the globals say so (the editor and the tests look at that).

// script(max_instances = 1)
struct Goal {
    node: i32,
}

fn start(g: Goal&) {
    set_tag(g.node, 8);
}

fn fixed_update(g: Goal&) {
    let s = (get_global(21) as i32) - 1;
    if s < 0 { return; }
    let dx = node_x(s) - node_x(g.node);
    let dy = node_y(s) - node_y(g.node);
    if dx > -0.8 && dx < 0.8 && dy > -0.8 && dy < 0.8 {
        set_tag(g.node, 99);
        set_global(5, 1.0);
    }
}
