from bpy.types import Panel, UIList

class NPGROWTH_PT_DepositionEntryPanel(Panel):
    bl_label = "Deposition entries"
    bl_idname = "NPGROWTH_PT_deposition_regions"
    bl_space_type = "VIEW_3D"  # Change to appropriate space if needed
    bl_region_type = "UI"
    bl_category = "Cannon"
    bl_parent_id = "NPGROWTH_PT_panel"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Deposition entries Data:")
        # Iterate over your list of objects, displaying their name and position.
        deposition_entries = context.scene.deposition_entries
        for deposition_entry in deposition_entries:
            box = layout.box()
            box.prop(deposition_entry, "depo_region", text="Deposition Region")
            box.prop(deposition_entry, "nanoparticle_xyz_file", text="NP xyz File")
            row = box.row()
            row.prop(deposition_entry, "depo_min_velocity", text="Deposition Min Velocity")
            row.prop(deposition_entry, "depo_max_velocity", text="Deposition Max Velocity")
            row = box.row()
            row.prop(deposition_entry, "to_deposit", text="N to deposit")
            row.prop(deposition_entry, "every_step", text="Every N steps")
            box.prop(deposition_entry, "random_seed", text="Random Seed")
            box.prop(deposition_entry, "target_regions", text="Target Regions")
