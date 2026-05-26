# NPGrowth_V1 — Installation Guide

## Requirements

- [Conda](https://docs.conda.io/en/latest/) (Miniconda or Anaconda)
- [Git](https://git-scm.com/)
- CMake ≥ 3.16
- A C++ compiler with MPI support (e.g. OpenMPI via Homebrew on macOS)
- Python 3.12

---

## Step 1 — Clone the NPGrowth_V1 repository

```bash
git clone https://github.com/nanoMLMS/NPGrowth_V1.git
cd NPGrowth_V1
```

---

## Step 2 — Create and activate the Conda environment

```bash
conda create -n NPGrowth_V1 python=3.12
conda activate NPGrowth_V1
```

---

## Step 3 — Clone LAMMPS

From inside the `NPGrowth_V1` directory:

```bash
git clone https://github.com/lammps/lammps.git
cd lammps
git checkout stable
```

---

## Step 4 — Replace the modified LAMMPS source files

NPGrowth_V1 requires a patched version of `fix_deposit` that supports the `target` keyword. Copy the modified files into the LAMMPS source tree:

```bash
cp ../lammps_deposition_modified/fix_deposit.cpp src/
cp ../lammps_deposition_modified/fix_deposit.h src/
```

### Fix API compatibility

The patched file uses an older `minimum_image` API. Update it to match the current LAMMPS version:

```bash
sed -i '' 's/domain->minimum_image(delx,dely,delz)/domain->minimum_image(FLERR, delx, dely, delz)/g' src/fix_deposit.cpp
```

> **Note (Linux):** omit the `''` after `-i`:
> ```bash
> sed -i 's/domain->minimum_image(delx,dely,delz)/domain->minimum_image(FLERR, delx, dely, delz)/g' src/fix_deposit.cpp
> ```

Verify the fix was applied (should show 2 lines with `FLERR`):

```bash
grep "minimum_image" src/fix_deposit.cpp
```

---

## Step 5 — Build LAMMPS

```bash
mkdir build
cd build

cmake ../cmake \
  -DCMAKE_INSTALL_PREFIX=$HOME/lammps \
  -DPKG_MOLECULE=on \
  -DPKG_MANYBODY=on \
  -DPKG_KSPACE=on

make -j 8
make install
```

The compiled binary will be installed at `$HOME/lammps/bin/lmp`.

---

## Step 6 — Run a sample simulation

Navigate to the `sample` directory and launch LAMMPS with MPI:

```bash
cd ../../sample
mpirun -np 4 $HOME/lammps/bin/lmp -in sample.in
```

Adjust `-np 4` to match the number of CPU cores available on your machine.

---

## Directory structure

```
NPGrowth_V1/
├── code/                          # Python scripts
├── lammps/                        # LAMMPS source (cloned in Step 3)
├── lammps_deposition_modified/    # Patched fix_deposit files
│   ├── fix_deposit.cpp
│   └── fix_deposit.h
├── sample/                        # Example simulation
│   ├── sample.in                  # Main LAMMPS input script
│   ├── molecule0.txt
│   ├── potentials/
│   ├── make_deposit/
│   └── seeds/
