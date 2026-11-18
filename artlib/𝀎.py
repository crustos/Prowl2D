"""A curl of hair: the .svg of the same name, in the colour of `stroke`, and a loose strand that runs down to the nearest
line of the outline (light sketch passes under it, overshooting the end like an artist's first lines)."""
from kaomojilang.brush import curve, sketch


def generate(svg, ctx, stroke):
    art = svg.recolor({"#2a1a3a": stroke}) if stroke not in (None, "black") else svg
    near = ctx.nearest_ink()
    if near is None:
        return art
    point, _ = near
    strand = curve(ctx.at, point, bend=0.35)
    return [art] + sketch(strand, passes=3, overshoot=0.18, width=0.1, opacity=0.35, seed=ctx.seed)
