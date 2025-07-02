import bpy
from bpy.types import Panel

class NPGROWTH_PT_panel(Panel):
    bl_label = "NPGrowth Panel"
    bl_idname = "NPGROWTH_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    my_property: bpy.props.FloatProperty(
        name="velocity",
        min=0.0,
        max=100.0,
        default=0.0,
        precision=2,
    ) # type: ignore

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.operator("npgrowth.import_seed")
        col.operator("npgrowth.add_cannon_region")
        col.operator("npgrowth.add_target_region")
        col.operator("npgrowth.export_input")