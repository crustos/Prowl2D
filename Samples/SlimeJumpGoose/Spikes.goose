// Spikes: the slime is hurt when it touches them (tag 9 is how the bot knows where they are).

// script(max_instances = 32)
struct Spikes {
    node: i32,
}

fn start(sp: Spikes&) {
    set_tag(sp.node, 9);
}

fn fixed_update(sp: Spikes&) {
    let s = (get_global(21) as i32) - 1;
    if s < 0 { return; }
    let dx = node_x(s) - node_x(sp.node);
    let dy = node_y(s) - node_y(sp.node);
    if dx > -0.6 && dx < 0.6 && dy > -0.55 && dy < 0.55 { set_tag(s, 3); }
}
