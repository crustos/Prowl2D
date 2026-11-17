"""analyze_audio.py TRACK.mp3 -> audio.json: what the video needs to know about the sound (needs ffmpeg, numpy, scipy).

    energy   loudness per frame (0..1, `fps` per second): drives the mouths while somebody talks, and the flashes
    onsets   [[seconds, strength 0..1], ...] the hits of the music: where the cuts go
    tempo    the beat of the music part, in bpm, from the onsets
Nothing of the audio itself is kept, only these numbers.
"""
import json
import subprocess
import sys
import tempfile

import numpy as np
import scipy.io.wavfile as wav
import scipy.signal as sg

FPS = 8
MUSIC_FROM = 277.0          # where the quiet gap before the beat ends (found by looking at the loudness)


def main(track, out="audio.json"):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", track, "-ac", "1", "-ar", "22050", f"{d}/a.wav"], check=True)
        sr, x = wav.read(f"{d}/a.wav")
    x = x.astype(np.float32) / 32768
    dur = len(x) / sr
    hop = sr // FPS
    n = len(x) // hop
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) for i in range(n)])
    energy = np.clip(rms / max(rms.max(), 1e-6), 0, 1)

    # onsets: spectral flux of the low and mid bands, peak picked
    f, t, S = sg.stft(x, sr, nperseg=1024, noverlap=1024 - 256)
    mag = np.abs(S)
    low = mag[(f > 40) & (f < 250)].sum(axis=0)
    mid = mag[(f >= 250) & (f < 3000)].sum(axis=0)
    flux = np.maximum(0, np.diff(low, prepend=low[0])) / (low.max() + 1e-9) * 1.4 + np.maximum(0, np.diff(mid, prepend=mid[0])) / (mid.max() + 1e-9)
    flux = flux / flux.max()
    peaks, props = sg.find_peaks(flux, height=0.12, distance=int(0.11 * sr / 256))
    onsets = [[round(float(t[p]), 3), round(float(flux[p]), 3)] for p in peaks]

    # tempo of the music part: autocorrelation of the onset curve
    m = (t > MUSIC_FROM) & (t < 620)
    env = flux[m]
    env = env - env.mean()
    ac = np.correlate(env, env, "full")[len(env) - 1:]
    fr = sr / 256
    lo, hi = int(fr * 60 / 220), int(fr * 60 / 90)
    lag = lo + int(np.argmax(ac[lo:hi]))
    tempo = 60 * fr / lag
    json.dump({"duration": round(dur, 2), "fps": FPS, "music_from": MUSIC_FROM, "tempo": round(tempo, 1),
               "energy": [round(float(v), 2) for v in energy], "onsets": onsets}, open(out, "w"), separators=(",", ":"))
    print(f"{out}: {dur:.1f}s, {len(onsets)} onsets, tempo about {tempo:.0f} bpm")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "audio.json")
