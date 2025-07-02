import bpy
import colorsys
from bpy.types import Operator

class AddTargetRegionOperator(Operator):
    bl_idname = "npgrowth.add_target_region"
    bl_label = "Add Target Region"
    bl_description = "Add region where atoms will be deposited"
    bl_options = {'PRESET', 'UNDO'}

    selected_deposition_entry = None

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0), size=4.0)  # Adds a cube at the origin
        target = bpy.context.object

        item = self.selected_deposition_entry.target_regions.add()
        item.target_region = target
        
        context.area.tag_redraw()
        
        # Create a new material
        mat = bpy.data.materials.new(name="MyMaterial")
        mat.use_nodes = True
        
        # Access the Principled BSDF node
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        
        color = self.selected_deposition_entry["depo_region"].active_material.diffuse_color
        mat.diffuse_color = color
        mat.diffuse_color[3] = 1.0  # Set alpha to 1.0
        
        # Assign the material to the cube
        if target.data.materials:
            target.data.materials[0] = mat
        else:
            target.data.materials.append(mat)
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        selected_objects = bpy.context.selected_objects
        if selected_objects:
            entries = list(filter(lambda x: x.depo_region == selected_objects[0], bpy.context.scene.deposition_entries))
            if entries:
                self.selected_deposition_entry = entries[0]
        
        if (len(selected_objects) == 1) and self.selected_deposition_entry:
            self.execute(context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "A single deposition region must be selected")
            return {'CANCELLED'}

