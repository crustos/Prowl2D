// An anchor: a solid block the lasso can catch on (tag 7, which is how the bot finds it).

// script(max_instances = 8)
struct Anchor {
    node: i32,
}

fn start(a: Anchor&) {
    add_body(a.node, 0);
    add_box(a.node, 1.0, 1.0);
    set_tag(a.node, 7);
}
