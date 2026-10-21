# SlipSurfaceIQ Settle 2026.1.0

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
