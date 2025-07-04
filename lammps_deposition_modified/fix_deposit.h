/* -*- c++ -*- ----------------------------------------------------------
   LAMMPS - Large-scale Atomic/Molecular Massively Parallel Simulator
   https://www.lammps.org/, Sandia National Laboratories
   LAMMPS development team: developers@lammps.org

   Copyright (2003) Sandia Corporation.  Under the terms of Contract
   DE-AC04-94AL85000 with Sandia Corporation, the U.S. Government retains
   certain rights in this software.  This software is distributed under
   the GNU General Public License.

   See the README file in the top-level LAMMPS directory.
------------------------------------------------------------------------- */

#ifdef FIX_CLASS
// clang-format off
FixStyle(deposit,FixDeposit);
// clang-format on
#else

#ifndef LMP_FIX_DEPOSIT_H
#define LMP_FIX_DEPOSIT_H

#include "fix.h"

namespace LAMMPS_NS {

class FixDeposit : public Fix {
 public:
  FixDeposit(class LAMMPS *, int, char **);
  ~FixDeposit() override;
  int setmask() override;
  void init() override;
  void setup_pre_exchange() override;
  void pre_exchange() override;
  double compute_scalar() override;
  void write_restart(FILE *) override;
  void restart(char *) override;
  void *extract(const char *, int &) override;

 private:
  int ninsert, ntype, nfreq, seed;
  int globalflag, localflag, maxattempt, rateflag, scaleflag, targetflag;
  int mode, rigidflag, shakeflag, idnext, distflag, orientflag, warnflag;
  int varflag, vvar, xvar, yvar, zvar;
  double lo, hi, deltasq, nearsq, rate, sigma;
  double vxlo, vxhi, vylo, vyhi, vzlo, vzhi;
  double xlo, xhi, ylo, yhi, zlo, zhi, xmid, ymid, zmid;
  double txlo, txhi, tylo, tyhi, tzlo, tzhi;
  double rx, ry, rz;
  class Region *iregion;
  char *idiregion;
  class Region *tregion;
  char *idtregion;
  char *idrigid, *idshake;
  char *vstr, *xstr, *ystr, *zstr;
  char *xstr_copy, *ystr_copy, *zstr_copy;

  class Molecule **onemols;
  int nmol, natom_max;
  double *molfrac;
  double **coords;
  imageint *imageflags;
  class Fix *fixrigid, *fixshake;
  double oneradius;

  int ninserted;
  bigint nfirst;
  tagint maxtag_all, maxmol_all;
  class RanPark *random;

  void find_maxid();
  void options(int, char **);
  int vartest(double, double, double);    // evaluate a variable with new atom position
};

}    // namespace LAMMPS_NS

#endif
#endif
