import json
import math
import tempfile


def deg_to_rad(deg):
    return deg * math.pi / 180


def rotate_point(x, y, z, rot):
    rx, ry, rz = map(deg_to_rad, rot)
    cos = math.cos
    sin = math.sin

    # Rotate around X
    y, z = y*cos(rx) - z*sin(rx), y*sin(rx) + z*cos(rx)
    # Rotate around Y
    x, z = x*cos(ry) + z*sin(ry), -x*sin(ry) + z*cos(ry)
    # Rotate around Z
    x, y = x*cos(rz) - y*sin(rz), x*sin(rz) + y*cos(rz)

    return [x, y, z]


def format_block(region):
    return "{:.6f} {:.6f} {:.6f} {:.6f} {:.6f} {:.6f}".format(*region)


def regions_from_shape(shape):
    dx, dy, dz = (edge / 2 for edge in shape["size"])
    regions = []

    for x, y, z in shape["positions"]:
        region = [x - dx, x + dx, y - dy, y + dy, z - dz, z + dx]
        regions.append(region)

    return regions


def apply_transformations(shape, translation, rotation):
    transformed_positions = []

    for x, y, z in shape["positions"]:
        rotated = rotate_point(x, y, z, rotation)
        translated = [p + t for p, t in zip(rotated, translation)]
        transformed_positions.append(translated)

    return {"size": shape["size"], "positions": transformed_positions}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def write_region(output_file, name, region):
    output_file.write(f"region {name} block {format_block(region)}\n")


def write_target_regions(output_file, target, i, j):
    shape = load_json(target["shape_file"])
    transformed_shape = apply_transformations(
        shape, target["position"], target["rotation"])
    regions = regions_from_shape(transformed_shape)

    region_names = []
    for k, region in enumerate(regions):
        region_name = f"target_{i}_{j}_{k}"
        write_region(output_file, region_name, region)
        region_names.append(region_name)

    return region_names


def parse_xyz(path):
    with open(path, "r") as f:
        natoms = int(f.readline())
        _ = f.readline()  # comment line
        atoms = []
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                atom_type, x, y, z = parts[:4]
                atoms.append((atom_type, float(x), float(y), float(z)))

    return natoms, atoms


def write_molecule(molecule_file, molecule_name):
    lammps_file = tempfile.NamedTemporaryFile("w", delete=False)
    natoms, atoms = parse_xyz(molecule_file)

    with open(lammps_file.name, "w") as f:
        f.write(f"# Nanoparticle {molecule_file}\n")
        f.write(f"{natoms} atoms\n\n")
        f.write("Coords\n\n")
        for i, (_, x, y, z) in enumerate(atoms, start=1):
            f.write(f"{i} {x} {y} {z}\n")
        f.write("\nTypes\n\n")
        for i, (atom_type, _, _, _) in enumerate(atoms, start=1):
            f.write(f"{i} {atom_type}\n")
        f.write("\n")

    return lammps_file.name


def generate_script(config_path, output_path):
    configs = load_json(config_path)

    with open(output_path, "w") as output_file:
        for i, config in enumerate(configs):
            # Deposit region
            deposit_region_name = f"deposi_box_{i}"
            write_region(output_file, deposit_region_name,
                         config["deposit_region"])

            # Molecule
            molecule_file = config.get("molecule_xyz")
            molecule_name = f"molecule_{i}"
            mol_clause = f"mol {molecule_name}" if molecule_file else ""
            if molecule_file:
                lammps_molecule_file = write_molecule(
                    molecule_file, molecule_name)
                output_file.write(f"""molecule {molecule_name} {
                                  lammps_molecule_file}\n""")

            # Targets
            all_region_names = []
            for j, target in enumerate(config["targets"]):
                region_names = write_target_regions(output_file, target, i, j)
                all_region_names.extend(region_names)

            # Union region
            union_name = None
            if len(all_region_names) > 1:
                union_name = f"target_box_{i}"
                output_file.write(f"""region {union_name} union {
                    len(all_region_names)} {
                    ' '.join(all_region_names)}\n""")
            else:
                union_name = all_region_names[0]

            # Fix deposit
            output_file.write(
                f"""fix deposit_{i} added deposit {config['n_depo']} {
                    config['type']} {config['every']} """
                f"""{config['seed']} region {
                    deposit_region_name} near {config['near']} """
                f"""vx {config['v'][0]} {config['v'][1]} target {
                    union_name} {mol_clause}\n"""
            )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True,
                        help="Path to deposition config json")
    parser.add_argument("--output", required=True, help="Path to output file")
    args = parser.parse_args()

    generate_script(args.config, args.output)
    print(f"LAMMPS deposition input written to: {args.output}")
