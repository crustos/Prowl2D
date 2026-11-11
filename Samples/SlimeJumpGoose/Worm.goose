// A worm (tag 2): crawls back and forth around where it starts. Touch it from the side and the slime is hurt; land on it and it is squashed; a bullet (which sets its tag to 5) kills it.

let DT: f32 = 0.016666668;

// script(max_instances = 8)
struct Worm {
    node: i32,
    home: f32,
    dir: f32,
}

fn start(w: Worm&) {
    w.home = node_x(w.node);
    w.dir = 1.0;
    set_tag(w.node, 2);
}

fn fixed_update(w: Worm&) {
    if get_tag(w.node) == 5 {
        destroy_node(w.node);
        return;
    }
    var x = node_x(w.node);
    x += w.dir * 2.0 * DT;
    if x > w.home + 3.0 { w.dir = -1.0; }
    if x < w.home - 3.0 { w.dir = 1.0; }
    set_pos(w.node, x, node_y(w.node));
    let s = (get_global(21) as i32) - 1;
    if s < 0 { return; }
    let dx = node_x(s) - x;
    let dy = node_y(s) - node_y(w.node);
    if dx > -0.8 && dx < 0.8 && dy > -0.8 && dy < 0.8 {
        if dy > 0.35 && velocity_y(s) < 0.0 {
            set_velocity(s, velocity_x(s), 11.0);       // squashed: the slime bounces off
            destroy_node(w.node);
        } else {
            set_tag(s, 3);
        }
    }
}
