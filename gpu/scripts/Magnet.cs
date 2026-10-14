// Hold the left mouse button: the balls are pulled to the pointer. Space: kick them up.
[GpuKernel]
public class Magnet {
    public float Strength = 30f;
    public void Update(int i, ref float x, ref float y, ref float vx, ref float vy) {
        float dx = Input2D.MouseX - x;
        float dy = Input2D.MouseY - y;
        if (Input2D.MouseDown(0)) {
            vx += dx * Strength * dt;
            vy += dy * Strength * dt;
        }
        if (Input2D.Key(Input2D.Space)) {
            vy += 40f * dt;
        }
    }
}
