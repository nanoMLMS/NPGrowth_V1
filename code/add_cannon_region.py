import bpy
import colorsys
from bpy.types import Operator

def get_distinct_color(n, total_colors=10):
    # Evenly distribute hue around the color wheel
    hue = (total_colors - n % total_colors) / total_colors  
    saturation = 0.9  # vivid
    value = 0.9       # bright
    
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    # Convert to RGB in 0-255 range
    return (r, g, b, 0.5)

class AddCannonRegionOperator(Operator):
    bl_idname = "npgrowth.add_cannon_region"
    bl_label = "Add Cannon Region"
    bl_description = "Add region from where new atoms will be added"
    bl_options = {'PRESET', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0), size=4.0)  # Adds a cube at the origin
        cube = bpy.context.object

        deposition_entry = bpy.context.scene.deposition_entries.add()
        deposition_entry.depo_region = cube
        
        context.area.tag_redraw()
        
        # Create a new material
        mat = bpy.data.materials.new(name="MyMaterial")
        mat.use_nodes = True
        
        # Access the Principled BSDF node
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        
        mat.diffuse_color = get_distinct_color(len(context.scene.deposition_entries))
        
        # Assign the material to the cube
        if cube.data.materials:
            cube.data.materials[0] = mat
        else:
            cube.data.materials.append(mat)
        
        return {'FINISHED'}

