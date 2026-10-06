# Data conventions

`raw/`: immutable source downloads. `interim/`: cleaning and geographic/time
harmonisation. `processed/`: analysis-ready tables. These directories are ignored
by Git; metadata is versioned. Never overwrite a raw release with a newer vintage.

Use source-specific subdirectories and descriptive release-based filenames.
Processed tables should carry geography level/code, period, measure, unit, value,
source ID and observation status. Keep denominators and sample coverage explicit.
A missing observation must not be encoded as zero. Do not publish microdata or
third-party downloads without verified redistribution rights.

Metadata templates:
- `source_register.csv`: candidate datasets and access audit.
- `dataset_manifest.csv`: one row per real downloaded input file.
- `variable_dictionary.csv`: one row per defined variable.
- `policy_register.csv`: one row per concrete implemented policy measure.

The manifest and policy register intentionally contain only headers until real
inputs and verified legal records are available.
