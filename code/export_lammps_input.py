import bpy
import os
from mathutils import Vector


def bounding_coords(obj):
    """
    Calculate the bounding box coordinates of an object in world space.
    """
    # Get the object's bounding box
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    
    # Calculate the min and max coordinates
    min_x = min(corner.x for corner in bbox_corners)
    max_x = max(corner.x for corner in bbox_corners)
    min_y = min(corner.y for corner in bbox_corners)
    max_y = max(corner.y for corner in bbox_corners)
    min_z = min(corner.z for corner in bbox_corners)
    max_z = max(corner.z for corner in bbox_corners)

    return (min_x, max_x, min_y, max_y, min_z, max_z)

def write_lammps_input(context, filepath):
    depo_entries = context.scene.deposition_entries
    f = open(filepath, 'w')
    for i, depo_entry in enumerate(depo_entries):
        depo_region = depo_entry.depo_region
        xlo, xhi, ylo, yhi, zlo, zhi = bounding_coords(depo_region)
        f.write(f'region deposit_box_{i} block ')
        f.write(f'{xlo} {xhi} ')
        f.write(f'{ylo} {yhi} ')
        f.write(f'{zlo} {zhi}\n')

        target_regions = depo_entry.target_regions
        target_regions_names = []
        for j, target_region in enumerate(target_regions):
            xlo, xhi, ylo, yhi, zlo, zhi = bounding_coords(target_region.target_region)
            f.write(f'region target_box_{i}{j} block ')
            f.write(f'{xlo} {xhi} ')
            f.write(f'{ylo} {yhi} ')
            f.write(f'{zlo} {zhi}\n')
            target_regions_names.append(f'target_box_{i}{j}')
        
        mol_command = None
        nanoparticle_xyz_file = depo_entry.nanoparticle_xyz_file
        if len(nanoparticle_xyz_file) > 0:
            np_f = open(nanoparticle_xyz_file, 'r')
            directory = os.path.dirname(filepath)
            mol_f = open(f'{directory}/molecule{i}.txt', 'w')
            mol_f.write(f'# Nanoparticle {nanoparticle_xyz_file}\n')
            natoms_np = int(np_f.readline())
            metadata = np_f.readline()
            atoms_types = []
            atoms_positions = []
            for line in np_f:
                atom_type, x, y, z, *_ = line.split()
                atoms_types.append(atom_type)
                atoms_positions.append((float(x), float(y), float(z)))
            mol_f.write(f'{natoms_np} atoms\n\n')
            mol_f.write('Coords\n\n')
            for k, p in enumerate(atoms_positions):
                x, y, z = p
                mol_f.write(f'{k+1} {x} {y} {z}\n')
            mol_f.write('\nTypes\n\n')
            for k, atom_type in enumerate(atoms_types):
                mol_f.write(f'{k+1} {atom_type}\n')
            mol_f.write('\n')
            mol_f.close()
            np_f.close()
            f.write(f'molecule molecule{i} molecule{i}.txt\n')
            mol_command = f'mol molecule{i}'
        regions_names = " ".join(target_regions_names)
        final_target_region_name = None

        if len(target_regions_names) > 1:
            f.write(f'region target_box_{i} union {len(target_regions_names)} {regions_names}\n')
            final_target_region_name = f'target_box_{i}'
        else:
            final_target_region_name = target_regions_names[0]
        if mol_command:
            f.write(f'fix deposit_{i} added deposit {depo_entry.to_deposit} 0 {depo_entry.every_step} {depo_entry.random_seed} region deposit_box_{i} near 4.0 vx {depo_entry.depo_min_velocity} {depo_entry.depo_max_velocity} target {final_target_region_name} {mol_command}\n')
        else:
            f.write(f'fix deposit_{i} added deposit {depo_entry.to_deposit} 1 {depo_entry.every_step} {depo_entry.random_seed} region deposit_box_{i} near 4.0 vx {depo_entry.depo_min_velocity} {depo_entry.depo_max_velocity} target {final_target_region_name}\n')


    f.close()

    return {'FINISHED'}


from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class NPGrowthExportLammpsInputFileOperator(Operator, ExportHelper):
    bl_idname = "npgrowth.export_input"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export LAMMPS input file"

    filename_ext = ".in"

    filter_glob: StringProperty(
        default="*.in",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    ) # type: ignore

    # # List of operator properties, the attributes will be assigned
    # # to the class instance from the operator settings before calling.
    # use_setting: BoolProperty(
    #     name="Example Boolean",
    #     description="Example Tooltip",
    #     default=True,
    # ) # type: ignore

    # type: EnumProperty(
    #     name="Example Enum",
    #     description="Choose between two items",
    #     items=(
    #         ('OPT_A', "First Option", "Description one"),
    #         ('OPT_B', "Second Option", "Description two"),
    #     ),
    #     default='OPT_A',
    # ) # type: ignore

    def execute(self, context):
        return write_lammps_input(context, self.filepath)