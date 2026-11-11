// Vines: a trigger on layer 15, which the slime's probe finds (it climbs while it overlaps one).

// script(max_instances = 32)
struct Vine {
    node: i32,
}

fn start(v: Vine&) {
    set_layer(v.node, 15);
    add_body(v.node, 0);
    add_box_trigger(v.node, 1.0, 1.0);
}
