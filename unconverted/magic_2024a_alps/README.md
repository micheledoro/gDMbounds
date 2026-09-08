# MAGIC 2024a — not dark matter annihilation or decay bounds

Three files from *"Constraints on axion-like particles with the Perseus Galaxy
Cluster with MAGIC"*, held here because the schema cannot express them.

- `magic_2024a_fig1_sed.ecsv` — the spectral energy distribution of NGC 1275 in
  three activity states. An astrophysical measurement, not a limit on anything.
- `magic_2024a_fig2_95CL.ecsv`, `magic_2024a_fig2_99CL.ecsv` — exclusion contours
  for axion-like particles in the plane of ALP mass (eV) against ALP–photon
  coupling (GeV⁻¹).

The ALP files are dark matter results, but not in the observable this database
holds. Every bound in `gdmbounds/bounds/` constrains an annihilation cross
section or a decay lifetime as a function of DM mass; an ALP contour lives in a
different parameter plane and shares no axis with them. Admitting it means
deciding how the schema, the catalogue and eventually the plotting represent more
than one kind of parameter space — a design question, not a transcription.

They also use a third metadata convention, with capitalised keys (`Filename`,
`Source`, `Title`) unlike anything else in the project.
