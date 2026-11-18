"""A nose: a small hook. (The light construction lines an artist draws toward the eyes are not its job: the figure's
underdrawing, `rough=1`, plans them from the whole face.)"""
from kaomojilang.brush import Stroke


def generate(ctx, stroke, width):
    x, y = ctx.at
    return [Stroke([(x - 0.7, y + 0.3), (x - 0.1, y + 0.9), (x + 0.6, y + 0.6)], width, stroke or "black")]
