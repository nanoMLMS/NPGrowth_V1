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
    bl_idname = "npgrowth.import_seed"
    bl_label  = "Import Seed (*.xyz)"
    bl_description = "Import a XYZ atomic structure"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".xyz"
    filter_glob: StringProperty(default="*.xyz", options={'HIDDEN'},) # type: ignore

    use_camera: BoolProperty(
        name="Camera", default=False,
        description="Do you need a camera?") # type: ignore
    use_lamp: BoolProperty(
        name="Lamp", default=False,
        description = "Do you need a lamp?") # type: ignore
    ball: EnumProperty(
        name="Type of ball",
        description="Choose ball",
        items=(('0', "NURBS", "NURBS balls"),
               ('1', "Mesh" , "Mesh balls"),
               ('2', "Meta" , "Metaballs")),
               default='0',) # type: ignore
    mesh_azimuth: IntProperty(
        name = "Azimuth", default=32, min=1,
        description = "Number of sectors (azimuth)") # type: ignore
    mesh_zenith: IntProperty(
        name = "Zenith", default=32, min=1,
        description = "Number of sectors (zenith)") # type: ignore
    scale_ballradius: FloatProperty(
        name = "Balls", default=1.0, min=0.0001,
        description = "Scale factor for all atom radii") # type: ignore
    scale_distances: FloatProperty (
        name = "Distances", default=1.0, min=0.0001,
        description = "Scale factor for all distances") # type: ignore
    atomradius: EnumProperty(
        name="Type of radius",
        description="Choose type of atom radius",
        items=(('0', "Pre-defined", "Use pre-defined radius"),
               ('1', "Atomic", "Use atomic radius"),
               ('2', "van der Waals", "Use van der Waals radius")),
               default='0',) # type: ignore
    use_center: BoolProperty(
        name = "Object to origin (first frames)", default=False,
        description = "Put the object into the global origin, the first frame only") # type: ignore
    use_center_all: BoolProperty(
        name = "Object to origin (all frames)", default=True,
        description = "Put the object into the global origin, all frames") # type: ignore
    datafile: StringProperty(
        name = "", description="Path to your custom data file",
        maxlen = 256, default = "", subtype='FILE_PATH') # type: ignore
    use_frames: BoolProperty(
        name = "Load all frames?", default=False,
        description = "Do you want to load all frames?") # type: ignore
    skip_frames: IntProperty(
        name="", default=0, min=0,
        description="Number of frames you want to skip") # type: ignore
    images_per_key: IntProperty(
        name="", default=1, min=1,
        description="Choose the number of images between 2 keys") # type: ignore

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "use_camera")
        row.prop(self, "use_lamp")
        row = layout.row()
        row.prop(self, "use_center")
        row = layout.row()
        row.prop(self, "use_center_all")
        # Balls
        box = layout.box()
        row = box.row()
        row.label(text="Balls / atoms")
        row = box.row()
        col = row.column()
        col.prop(self, "ball")
        row = box.row()
        row.active = (self.ball == "1")
        col = row.column(align=True)
        col.prop(self, "mesh_azimuth")
        col.prop(self, "mesh_zenith")
        row = box.row()
        col = row.column()
        col.label(text="Scaling factors")
        col = row.column(align=True)
        col.prop(self, "scale_ballradius")
        col.prop(self, "scale_distances")
        row = box.row()
        row.prop(self, "atomradius")
        # Frames
        box = layout.box()
        row = box.row()
        row.label(text="Frames")
        row = box.row()
        row.prop(self, "use_frames")
        row = box.row()
        row.active = self.use_frames
        col = row.column()
        col.label(text="Skip frames")
        col = row.column()
        col.prop(self, "skip_frames")
        row = box.row()
        row.active = self.use_frames
        col = row.column()
        col.label(text="Frames/key")
        col = row.column()
        col.prop(self, "images_per_key")

    def execute(self, context):
        # Switch to 'OBJECT' mode when in 'EDIT' mode.
        if bpy.context.mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        del ALL_FRAMES[:]
        del ELEMENTS[:]
        del STRUCTURE[:]

        # This is to determine the path.
        filepath_xyz = bpy.path.abspath(self.filepath)

        # Execute main routine
        import_xyz(self.ball,
                   self.mesh_azimuth,
                   self.mesh_zenith,
                   self.scale_ballradius,
                   self.atomradius,
                   self.scale_distances,
                   self.use_center,
                   self.use_center_all,
                   self.use_camera,
                   self.use_lamp,
                   filepath_xyz)

        # Load frames
        if len(ALL_FRAMES) > 1 and self.use_frames:

            build_frames(self.images_per_key, self.skip_frames)

        return {'FINISHED'}