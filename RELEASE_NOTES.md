# SlipSurfaceIQ Settle 2026.1.0

- **Materials** are defined once, in their own dialog (**Properties › Define Materials…**,
  Ctrl+M), laid out as in SlipSurfaceIQ LE: the materials on the left, the properties
  of the selected one on the right, only those its behaviour uses. The soil profile is
  a short list of layers — a material, a thickness and, for a clay, the drainage — in
  the left panel. The band of tables under the drawing is gone.
- **Settlement from mv, mv,ur and cv only:** a cohesive material can be described by its
  coefficients of volume compressibility instead of Cc, Cr and e0:
  ε = mv,ur·Δσ' up to σ'p = OCR·σ'v0 and mv·Δσ' beyond it; cv gives the time and
  Cαε = Cα/(1 + e0) the secondary compression. A clay with E = 0 is given no immediate
  settlement.
- **Incompressible material** for rock and the like: it does not settle, while its
  weight still counts in the in-situ stresses.
- Study variables are edited in their own dialog (**Properties › Study Variables…**,
  Ctrl+K); a material property varies every layer of that material.
- The report lists the mv parameters and adds method notes for mv, incompressible
  layers and clays without a modulus; the section figure fills each layer with its
  material's colour.
- Projects saved by 2026.0.0 open unchanged: each distinct layer becomes a material and
  study variables follow it. Files are now saved as format 0.2.
- Dialog buttons and the unsaved-changes prompt follow the interface language.

# SlipSurfaceIQ Settle 2026.0.0

First release as a standalone desktop program.

- **Desktop interface (PySide6)** laid out like SlipSurfaceIQ LE: a workflow bar
  (Project › Foundation / Fill › Soil Profile › Options › Results › Study), the
  project tree and the input panel of each step in the left dock, results and
  figures in the middle, and the soil profile and study variables tables below.
- Results follow every committed input change (the analysis takes milliseconds);
  automatic recomputation can be switched off, in which case stale results are
  flagged until **Compute (F5)**.
- Parametric and reliability studies run in the background with a progress bar
  and can be cancelled; sweeps, histograms, scatter plots and tornado charts,
  the summary and the sampled table are shown beside the inputs.
- Undo / redo of every input, recent projects, four bundled examples (raft on soft
  clay, strip footing on sand, embankment on soft clay, circular tank).
- Light and dark themes, English and Turkish, switchable without losing work.
- PDF, HTML and Word calculation reports; figure export as PNG, SVG or PDF;
  study tables as CSV or XLSX.
- The command line remains for batch use: `run`, `study` and `example`.
- Native installers for Windows (MSI), Ubuntu (DEB), Fedora / openSUSE (RPM) and
  Arch Linux, built and smoke-tested by CI.

The analysis core (stresses, immediate, consolidation and secondary settlement,
consolidation time, checks and studies) is unchanged from the SlipSurface IQ suite;
see [docs/CHANGELOG.md](docs/CHANGELOG.md) for its history.
