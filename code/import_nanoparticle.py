import bpy
from bpy.types import Operator, AddonPreferences
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import (
        StringProperty,
        BoolProperty,
        EnumProperty,
        IntProperty,
        FloatProperty,
        )

from .xyz_import import import_xyz
from .xyz_import import ALL_FRAMES
from .xyz_import import ELEMENTS
from .xyz_import import STRUCTURE
from .xyz_import import build_frames

# -----------------------------------------------------------------------------
#                                                                     Operators

# This is the class for the file dialog.
class NPGrowthImportSeedOperator(Operator, ImportHelper):
    bl_idname = "npgrowth.import_nanoparticle"
    bl_label  = "Import nanoparticle (*.xyz)"
    bl_description = "Import a XYZ atomic structure"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".xyz"
    filter_glob: StringProperty(default="*.xyz", options={'HIDDEN'},) # type: ignore

    selected_deposition_entry = None

    @classmethod
    def poll(self, context):
        selected_objects = context.selected_objects
        if selected_objects:
            entries = list(filter(lambda x: x.depo_region == selected_objects[0], context.scene.deposition_entries))
            if entries:
                self.selected_deposition_entry = entries[0]
            else:
                self.selected_deposition_entry = None
        
        if (len(selected_objects) == 1) and self.selected_deposition_entry:
            return True

        return False
    
    def execute(self, context):
        del ALL_FRAMES[:]
        del ELEMENTS[:]
        del STRUCTURE[:]

        # This is to determine the path.
        filepath_xyz = bpy.path.abspath(self.filepath)

        self.selected_deposition_entry.nanoparticle_xyz_file = filepath_xyz

        return {'FINISHED'}