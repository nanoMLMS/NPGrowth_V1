from bpy.types import PropertyGroup, Object, Scene
import bpy

def update_regions_entries(scene):
    for i in range(len(scene.deposition_entries) - 1, -1, -1):
        deposition_entry = scene.deposition_entries[i]
        if bpy.context.scene.objects.get(deposition_entry.depo_region.name) is None:
            scene.deposition_entries.remove(i)

# Register the handler so it updates on frame changes or scene updates
if update_regions_entries not in bpy.app.handlers.depsgraph_update_post:
    bpy.app.handlers.depsgraph_update_post.clear()
    bpy.app.handlers.depsgraph_update_post.append(update_regions_entries)

def update_target_entries(scene):
    for i in range(len(scene.deposition_entries) - 1, -1, -1):
        deposition_entry = scene.deposition_entries[i]
        for j in range(len(deposition_entry.target_regions) - 1, -1, -1):
            target_region = deposition_entry.target_regions[j]
            if bpy.context.scene.objects.get(target_region.target_region.name) is None:
                deposition_entry.target_regions.remove(i)

# Register the handler so it updates on frame changes or scene updates
if update_target_entries not in bpy.app.handlers.depsgraph_update_post:
    # bpy.app.handlers.depsgraph_update_post.clear()
    bpy.app.handlers.depsgraph_update_post.append(update_target_entries)


class TargetRegion(PropertyGroup):
    target_region: bpy.props.PointerProperty(
        name="Target Region",
        type=Object,
    ) # type: ignore

class DepositionEntry(PropertyGroup):
    depo_region: bpy.props.PointerProperty(
        name="Deposition Region",
        type=Object,
    ) # type: ignore
    target_regions: bpy.props.CollectionProperty(
        type=TargetRegion
    ) # type: ignore
    nanoparticle_xyz_file: bpy.props.StringProperty(
        name="Nanoparticle XYZ File",
        description="Path to the nanoparticle XYZ file",
        default="",
    ) # type: ignore
    depo_min_velocity: bpy.props.FloatProperty(
        name="Deposition Velocity",
        description="Minimum velocity of the deposited nanoparticles A/ps",
        default=5.0,
        min=0.0,
        precision=2,
    ) # type: ignore
    depo_max_velocity: bpy.props.FloatProperty(
        name="Deposition Velocity",
        description="Maximum velocity of the deposited nanoparticles A/ps",
        default=8.0,
        min=0.0,
        precision=2,
    ) # type: ignore
    to_deposit: bpy.props.IntProperty(
        name="N to deposit",
        description="Number of nanoparticles to deposit",
        min=1,
        default=1,
    ) # type: ignore
    every_step: bpy.props.IntProperty(
        name="Every step",
        description="Number of steps between deposits",
        min=1,
        default=200
    ) # type: ignore
    random_seed: bpy.props.IntProperty(
        name="Random seed for deposition",
        description="Random seed of deposition for reproducibility",
        min=1,
        default=42,
    ) # type: ignore



# Register the property group and add a collection property to the Scene.
def register():
    Scene.deposition_entries = bpy.props.CollectionProperty(type=DepositionEntry)
    Scene.deposition_entries_index = bpy.props.IntProperty(default=0)

def unregister():
    del Scene.deposition_entries
    del Scene.deposition_entries_index