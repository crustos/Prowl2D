// A checkpoint flag: the first time the slime comes by, it is where the slime comes back to after a fall or a hurt. Gems picked up until then are kept.

// script(max_instances = 8)
struct Save {
    node: i32,
    used: i32,
}

fn fixed_update(f: Save&) {
    if f.used != 0 { return; }
    let s = (get_global(21) as i32) - 1;
    if s < 0 { return; }
    let dx = node_x(s) - node_x(f.node);
    let dy = node_y(s) - node_y(f.node);
    if dx > -1.0 && dx < 1.0 && dy > -1.0 && dy < 1.0 && get_tag(s) == 1 {
        f.used = 1;
        set_global(2, node_x(f.node));
        set_global(3, node_y(f.node));
        set_global(1, get_global(1) + 1.0);
    }
}
