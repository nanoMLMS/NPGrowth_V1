"""
Generate initial configurations for sintering simulations from a JSON config file.

Usage:
    python make-config-npgrowth.py config.json

JSON schema:
    element          (str)  — Element symbol, e.g. "Cu"
    cluster_size     (int)  — Atoms per cluster (55, 147, …)
    n_clusters       (int)  — 2, 3, or 4
    displacement     (float)  — Desired COM separation
    seed             (int)  — Random seed
    overlap_radius   (float)  — Half minimum interatomic distance
    geometry         (str, optional)   — "line", "tri", "square", "tetra", "y"
    directions       (list, optional)  — N×3 array, overrides geometry
    max_iter         (int, optional)   — Default 500000
    nequil_skip      (int, optional)   — Frames to skip (default 100)
    clusters.source  (str)  — Path to equilibrated .dump file
    clusters.frames  (str or list, optional)  — "random" (default) or frame indices
"""

import json
import sys
import os
import math
import numpy as np
from scipy.spatial.distance import pdist, squareform, cdist
from scipy.sparse.csgraph import connected_components
from ase.io import read as ase_read, write as ase_write
from ase import Atoms
from snow.descriptors.shape_descriptors import gyr_rad, geometric_com
from itertools import chain

COS30 = math.sqrt(3.0) / 2.0

GEOMETRIES_3 = {
    "tri":  np.array([[0., 1., 0.], [-COS30, -0.5, 0.], [COS30, -0.5, 0.]]),
    "line": np.array([[0., 0., 0.], [1., 0., 0.], [2., 0., 0.]]),
}

GEOMETRIES_4 = {
    "line":   np.array([[0., 0., 0.], [1., 0., 0.], [2., 0., 0.], [3., 0., 0.]]),
    "square": np.array([[1., 1., 0.], [1., -1., 0.], [-1., -1., 0.], [-1., 1., 0.]]),
    "tetra":  np.array([[1., 1., 1.], [1., -1., -1.], [-1., 1., -1.], [-1., -1., 1.]]),
    "y":      np.array([[-0.5, COS30, 0.], [0.5, COS30, 0.], [0., 0., 0.], [0., -1., 0.]]),
}

GEOMETRIES = {3: GEOMETRIES_3, 4: GEOMETRIES_4}


def count_clusters(positions, cutoff):
    """Count the number of distinct clusters via connected-components labelling."""
    dists = squareform(pdist(positions))
    adjacency = (dists < cutoff)
    nclusts, labels = connected_components(adjacency)
    return nclusts


def get_clusters(positions, cutoff):
    """Return a list of position arrays, one per cluster, via connected components."""
    dists = squareform(pdist(positions))
    adjacency = dists < cutoff
    nclusts, labels = connected_components(adjacency)
    return [positions[labels == i] for i in range(nclusts)]


def check_overlap(positions, radius):
    """Check if any two atoms are overlapping (|p1-p2| < 2*radius)."""
    dists = squareform(pdist(positions))
    np.fill_diagonal(dists, np.inf)
    overlaps = dists < (2 * radius)
    return np.any(overlaps)


def random_rotation_matrix():
    """Generate a uniformly random 3D rotation matrix via QR of a random normal matrix."""
    A = np.random.randn(3, 3)
    Q, R = np.linalg.qr(A)
    Q *= np.sign(np.linalg.det(Q))
    return Q


def rotate_cluster(atoms, R):
    """Apply rotation matrix *R* to an ASE Atoms object in-place about its centroid."""
    pos = atoms.get_positions()
    centroid = pos.mean(axis=0)
    rotated = (R @ (pos - centroid).T).T + centroid
    atoms.set_positions(rotated)
    return atoms


def randomly_rotate_all(clusters):
    """Apply a different random rotation to each cluster in-place."""
    for cluster in clusters:
        R = random_rotation_matrix()
        rotate_cluster(cluster, R)
    return clusters


def add_separation(clusters, directions, displacement):
    """Shift each cluster by ``direction * displacement`` (in-place)."""
    for cluster, d in zip(clusters, directions):
        pos = cluster.get_positions()
        pos = pos + d * displacement
        cluster.positions = pos


def check_overlap_between_clusters(clusters, radius):
    """Check for overlaps between atoms belonging to *different* clusters (|p1-p2| < 2*radius)."""
    for i in range(len(clusters)):
        for j in range(i + 1, len(clusters)):
            pos_i = clusters[i].get_positions()
            pos_j = clusters[j].get_positions()
            dists = cdist(pos_i, pos_j)
            if np.any(dists < 2 * radius):
                return True
    return False


def separate_clusters_com(clusters, directions, overlap_radius, displacement=0.0,
                          max_iter=1000, return_movie=False):
    """
    Place clusters at a fixed COM separation and randomly rotate them until
    no inter-cluster atomic overlaps remain.

    Parameters
    ----------
    clusters : list of ase.Atoms
        Cluster objects to position.
    directions : (N, 3) array-like
        Unit vectors along which each cluster is displaced.
    overlap_radius : float
        Half the minimum allowed interatomic distance (|p1-p2| >= 2*radius).
    displacement : float
        Desired distance between cluster centres of mass.
    max_iter : int
        Maximum randomisation attempts before raising.
    return_movie : bool
        If True, return intermediate combined configurations.

    Returns
    -------
    clusters : list of ase.Atoms
        The (rotated, displaced) clusters.
    movie : list of ase.Atoms or None
        Intermediate frames (only if return_movie=True).
    """
    directions = np.asarray(directions, dtype=float)
    movie = []

    clusters = randomly_rotate_all(clusters)

    for c, d in zip(clusters, directions):
        c.positions += d * displacement

    print('displaced')

    if return_movie:
        combined = clusters[0].copy()
        for c in clusters[1:]:
            combined += c
        movie.append(combined)

    for i in range(max_iter):
        if check_overlap_between_clusters(clusters, overlap_radius):
            randomly_rotate_all(clusters)
            if return_movie:
                combined = clusters[0].copy()
                for c in clusters[1:]:
                    combined += c
                movie.append(combined)
        else:
            print(f'found ok random orientation after {i+1} tries')
            if return_movie and len(movie) > 0:
                return clusters, movie
            else:
                return clusters, None

    combined = clusters[0].copy()
    for c in clusters[1:]:
        combined += c
    ase_write('broken_config.xyz', combined)
    raise RuntimeError(
        f"Could not find a random orientation that avoids overlapping "
        f"in max_iter={max_iter} tries"
    )


def resolve_directions(config):
    """
    Determine the (N, 3) direction array from the config dict.

    Priority:
    1. ``config["directions"]`` — explicit array.
    2. ``config["geometry"]`` — looked up in ``GEOMETRIES``.
    3. For N=2, default to ``[[0,0,0], [1,0,0]]``.
    """
    n = config["n_clusters"]

    if "directions" in config:
        dirs = np.asarray(config["directions"], dtype=float)
        if dirs.shape != (n, 3):
            raise ValueError(
                f"directions must be ({n}, 3), got {dirs.shape}"
            )
        return dirs

    if n == 2:
        return np.array([[0., 0., 0.], [1., 0., 0.]])

    if n not in (3, 4):
        raise ValueError(f"n_clusters must be 2, 3, or 4, got {n}")

    geometry = config.get("geometry")
    if geometry is None:
        raise ValueError(
            f"geometry is required for {n} clusters "
            f"(or provide an explicit directions array)"
        )

    geom_dict = GEOMETRIES.get(n, {})
    if geometry not in geom_dict:
        available = list(geom_dict.keys())
        raise ValueError(
            f"Unknown geometry '{geometry}' for {n} clusters. "
            f"Available: {available}"
        )

    return geom_dict[geometry].copy()


def load_config(config_path):
    """
    Load and validate a JSON configuration file.

    Required fields: ``element``, ``cluster_size``, ``n_clusters``,
    ``displacement``, ``seed``, ``overlap_radius``, ``clusters`` (with
    ``clusters.source``).

    Optional fields with defaults: ``max_iter`` (500000),
    ``nequil_skip`` (100), ``clusters.frames`` ("random").
    """
    with open(config_path) as f:
        cfg = json.load(f)

    required = ["element", "cluster_size", "n_clusters", "displacement",
                 "seed", "overlap_radius", "clusters"]
    for field in required:
        if field not in cfg:
            raise ValueError(f"Missing required field '{field}' in config")

    if "source" not in cfg["clusters"]:
        raise ValueError("Missing 'clusters.source' in config")

    config_dir = os.path.dirname(os.path.abspath(config_path))
    cfg["clusters"]["source"] = os.path.join(
        config_dir, cfg["clusters"]["source"]
    )

    cfg.setdefault("max_iter", 500000)
    cfg.setdefault("nequil_skip", 100)
    cfg["clusters"].setdefault("frames", "random")

    return cfg


def load_clusters(cfg):
    """
    Read cluster configurations from an equilibrated trajectory dump file.

    * Skips ``nequil_skip`` frames, then picks either ``n_clusters`` random
      frames or the specific frame indices given by ``clusters.frames``.
    """
    source = cfg["clusters"]["source"]
    nequil_skip = cfg["nequil_skip"]
    n_clusters = cfg["n_clusters"]
    frames = cfg["clusters"]["frames"]

    trajectory = ase_read(source, index=":")
    trajectory = trajectory[nequil_skip:]

    if frames == "random":
        if len(trajectory) < n_clusters:
            raise ValueError(
                f"Not enough frames ({len(trajectory)}) "
                f"for {n_clusters} clusters after skipping {nequil_skip}"
            )
        idx = np.random.choice(len(trajectory), size=n_clusters, replace=False)
    else:
        idx = np.asarray(frames, dtype=int)
        if len(idx) != n_clusters:
            raise ValueError(
                f"frames list has {len(idx)} entries, expected {n_clusters}"
            )

    clusters = [trajectory[i] for i in idx]

    gr = [gyr_rad(c.positions) for c in clusters]
    print(f'gyration radii: {gr}')
    print(f'selected frames: {idx.tolist()}')

    return clusters


def main():
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <config.json>")
        sys.exit(1)

    cfg = load_config(sys.argv[1])

    element = cfg["element"]
    cluster_size = cfg["cluster_size"]
    n_clusters = cfg["n_clusters"]
    displacement = cfg["displacement"]
    seed = int(cfg["seed"])
    overlap_radius = cfg["overlap_radius"]
    max_iter = cfg["max_iter"]

    np.random.seed(seed)

    directions = resolve_directions(cfg)
    print(f"directions:\n{directions}")

    clusters = load_clusters(cfg)

    clusters, movie = separate_clusters_com(
        clusters, directions, overlap_radius,
        displacement=displacement, max_iter=max_iter,
        return_movie=False,
    )

    combined = clusters[0].copy()
    for c in clusters[1:]:
        combined += c

    coms = np.array([geometric_com(c.positions) for c in clusters], dtype=float)
    coms_dists_mat = squareform(pdist(coms))
    np.fill_diagonal(coms_dists_mat, np.inf)
    min_separation = np.min(coms_dists_mat)

    xpos = combined.get_positions()[:, 0]
    ypos = combined.get_positions()[:, 1]
    zpos = combined.get_positions()[:, 2]
    dx = np.max(xpos) - np.min(xpos)
    dy = np.max(ypos) - np.min(ypos)
    dz = np.max(zpos) - np.min(zpos)
    max_len = max(dx, dy, dz)
    combined.center(vacuum=max_len + 10.0)

    name = cfg.get("name")
    if name is None:
        geometry = cfg.get("geometry", "custom")
        name = f"{element}_{geometry}_{displacement:.2f}_{min_separation:.2f}_{seed}"
    filename = f"{name}.data"
    ase_write(filename, combined, format='lammps-data')
    print(f"Written {len(combined)} atoms to {filename}")


if __name__ == '__main__':
    main()
