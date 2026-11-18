"""A chin: a small cleft, drawn as SVG text (so the same script could draw a whole jaw)."""


def generate(ctx):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 12" data-size="3,1.2">'
            '<path d="M3 3 C9 11 21 11 27 3" fill="none" stroke="#2a1a3a" stroke-width="2.2" stroke-linecap="round"/></svg>')
