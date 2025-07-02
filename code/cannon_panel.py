import bpy
from bpy.types import Panel

class NPGROWTH_PT_panel(Panel):
    bl_label = "Cannon Panel"
    bl_idname = "NPGROWTH_PT_cannon_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.operator("npgrowth.import_nanoparticle")