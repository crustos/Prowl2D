/* A deterministic stub of the engine that logs every call (prowl_editor/test_goose_scripts.py): the same driver runs the Rust and the Goose builds of SlimeJump's scripts, and the two logs must agree. */
#include <math.h>
#include <stdio.h>
#include <string.h>
#define N 64
static float px[N], py[N], pa[N], vx[N], vy[N]; static int tag[N], alive[N], active[N], nodes_n = 1;
static float glob[64]; static int keys[512], mouse[4];
static unsigned rs = 12345;
static FILE *stub_logf;
static unsigned rnd(void) { rs = rs * 1664525u + 1013904223u; return rs >> 8; }
void stub_seed(unsigned s) { rs = s; }
void stub_log(FILE *f) { stub_logf = f; }
void stub_reset(void) { memset(px, 0, sizeof px); memset(py, 0, sizeof py); memset(pa, 0, sizeof pa); memset(vx, 0, sizeof vx); memset(vy, 0, sizeof vy);
    memset(tag, 0, sizeof tag); memset(alive, 0, sizeof alive); memset(active, 0, sizeof active); memset(glob, 0, sizeof glob); memset(keys, 0, sizeof keys); memset(mouse, 0, sizeof mouse); nodes_n = 1; }
void stub_node(int n, float x, float y) { px[n] = x; py[n] = y; alive[n] = 1; if (n >= nodes_n) nodes_n = n + 1; }
void stub_key(int k, int d) { keys[k] = d; }
void stub_mouse(int b, int d) { mouse[b] = d; }
void stub_global(int i, float v) { glob[i] = v; }
#define L(...) do { if (stub_logf) fprintf(stub_logf, __VA_ARGS__); } while (0)
int p2d_new_node(void) { int n = nodes_n++; alive[n] = 1; active[n] = 1; L("new_node -> %d\n", n); return n; }
int p2d_node_count(void) { return nodes_n; }
void p2d_set_pos(int n, float x, float y) { px[n] = x; py[n] = y; L("set_pos %d %.4f %.4f\n", n, x, y); }
void p2d_set_angle(int n, float a) { pa[n] = a; L("set_angle %d %.4f\n", n, a); }
void p2d_set_scale(int n, float x, float y) { L("set_scale %d %.4f %.4f\n", n, x, y); }
float p2d_node_x(int n) { return px[n]; }
float p2d_node_y(int n) { return py[n]; }
float p2d_node_angle(int n) { return pa[n]; }
void p2d_destroy_node(int n) { alive[n] = 0; L("destroy %d\n", n); }
int p2d_add_sprite(int n, int s, float w, float h, float r, float g, float b) { L("add_sprite %d %d %.3f %.3f %.3f %.3f %.3f\n", n, s, w, h, r, g, b); return 1; }
int p2d_add_body(int n, int t) { L("add_body %d %d\n", n, t); return 1; }
int p2d_add_body_ex(int n, int t, int f, float g) { L("add_body_ex %d %d %d %.3f\n", n, t, f, g); return 1; }
int p2d_add_box(int n, float w, float h) { L("add_box %d %.3f %.3f\n", n, w, h); return 1; }
int p2d_add_box_ex(int n, float w, float h, float f) { L("add_box_ex %d %.3f %.3f %.3f\n", n, w, h, f); return 1; }
int p2d_add_box_trigger(int n, float w, float h) { L("add_box_trigger %d %.3f %.3f\n", n, w, h); return 1; }
int p2d_add_circle(int n, float r) { L("add_circle %d %.3f\n", n, r); return 1; }
void p2d_set_velocity(int n, float x, float y) { vx[n] = x; vy[n] = y; L("set_velocity %d %.4f %.4f\n", n, x, y); }
void p2d_impulse(int n, float x, float y) { L("impulse %d %.4f %.4f\n", n, x, y); }
float p2d_velocity_x(int n) { return vx[n]; }
float p2d_velocity_y(int n) { return vy[n]; }
int p2d_attach_script(int n, int s) { L("attach_script %d %d\n", n, s); return 1; }
int p2d_node_alive(int n) { return alive[n]; }
void p2d_set_tag(int n, int t) { tag[n] = t; L("set_tag %d %d\n", n, t); }
int p2d_get_tag(int n) { return tag[n]; }
int p2d_node_slots(void) { return nodes_n; }
void p2d_set_global(int i, float v) { glob[i] = v; L("set_global %d %.4f\n", i, v); }
float p2d_get_global(int i) { return glob[i]; }
void p2d_set_layer(int n, int l) { L("set_layer %d %d\n", n, l); }
int p2d_raycast(float ox, float oy, float dx, float dy, float d, int m) { int r = (int)(rnd() % 3) - 1; L("raycast %.3f %.3f %.3f %.3f %.3f %d -> %d\n", ox, oy, dx, dy, d, m, r); return r; }
float p2d_ray_x(void) { return 3.25f; }
float p2d_ray_y(void) { return 2.5f; }
int p2d_overlap_box(float cx, float cy, float hw, float hh, int m) { int r = (int)(rnd() % 3); L("overlap_box %.3f %.3f %.3f %.3f %d -> %d\n", cx, cy, hw, hh, m, r); return r; }
void p2d_set_active(int n, int a) { active[n] = a; L("set_active %d %d\n", n, a); }
float p2d_math_sqrt(float x) { return sqrtf(x); }
float p2d_math_sin(float x) { return sinf(x); }
float p2d_math_cos(float x) { return cosf(x); }
float p2d_math_atan2(float y, float x) { return atan2f(y, x); }
int p2d_key_down(int k) { return keys[k]; }
int p2d_mouse_down(int b) { return mouse[b]; }
float p2d_mouse_world_x(void) { return 5.5f; }
float p2d_mouse_world_y(void) { return 4.5f; }
int p2d_collider_of(int n) { return 0; }
float p2d_sprite_info(int n, int f) { return 0; }
int p2d_node_active(int n) { return active[n]; }
int p2d_blast(float x, float y, float r, float f) { return 0; }
void p2d_gravity(float x, float y) { }
void stub_tag(int n, int t) { tag[n] = t; }
