"""A Blender script that builds a few game sprites, as an example for prowl.py --blend-script. Run from the Prowl2D folder:

    python3 prowl.py --blend-script tools/examples/blender_sprites.py --blend-ppu 16 -o sprites.json

It runs inside Blender (in an empty scene) and does not save a .blend: prowl.py renders every collection under the scene's collection to a sprite named after it.
Put the objects of one sprite in one collection, and keep to one scale (1 Blender unit = one tile). A collection of lights, or one hidden from renders, is skipped.
A collection named Level_* is a level: its collection instances are the tiles (see the end of this file). Use --blend-ppu 16 so that a one unit tile is 16 pixels.
For a top-down game add --blend-view top. A Blender file works the same way: python3 prowl.py scene.blend
"""
import bpy


def new_collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def add(collection, make, colour, **kwargs):
    """Adds a primitive (bpy.ops.mesh.primitive_*_add) with a flat colour to `collection`."""
    make(**kwargs)
    obj = bpy.context.active_object
    material = bpy.data.materials.new("colour")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*colour, 1.0)
    obj.data.materials.append(material)
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


# the ground tile: one unit. A custom property "solid" makes its tiles solid in the level
grass = new_collection("grass")
grass["solid"] = True
add(grass, bpy.ops.mesh.primitive_cube_add, (0.2, 0.6, 0.2), size=1.0, location=(0, 0, 0))

# a crate: a bigger box with a lid
crate = new_collection("crate")
add(crate, bpy.ops.mesh.primitive_cube_add, (0.5, 0.3, 0.1), size=1.0, location=(3, 0, 0))
add(crate, bpy.ops.mesh.primitive_cube_add, (0.7, 0.45, 0.2), size=1.0, location=(3, -0.2, 0.5), scale=(1.0, 1.0, 0.1))

# a slime: a squashed ball with two eyes (everything in one collection is one sprite)
slime = new_collection("slime")
body = add(slime, bpy.ops.mesh.primitive_uv_sphere_add, (0.3, 0.8, 0.4), radius=0.5, location=(6, 0, 0.3))
body.scale = (1.0, 1.0, 0.7)
for x in (5.8, 6.2):
    add(slime, bpy.ops.mesh.primitive_uv_sphere_add, (0.05, 0.05, 0.05), radius=0.07, location=(x, -0.45, 0.4))

# a coin: a thin disc standing up, much smaller than the others (the scale is shared)
add(new_collection("coin"), bpy.ops.mesh.primitive_cylinder_add, (1.0, 0.8, 0.1), radius=0.25, depth=0.06, location=(9, 0, 0.3), rotation=(1.5708, 0, 0))


# a level: instances of the collections above, one per tile. Each instance's position (in whole units) is its cell: x to the right, z up in the front view.
level = new_collection("Level_1")
for x, z, source in [(x, 0, "grass") for x in range(10)] + [(4, 1, "crate"), (7, 1, "slime"), (2, 1, "coin"), (3, 2, "coin"), (4, 2, "coin")]:
    tile = bpy.data.objects.new("tile", None)                      # an Empty that instances a collection
    tile.instance_type = "COLLECTION"
    tile.instance_collection = bpy.data.collections[source]
    tile.location = (x, 0, z)
    level.objects.link(tile)
