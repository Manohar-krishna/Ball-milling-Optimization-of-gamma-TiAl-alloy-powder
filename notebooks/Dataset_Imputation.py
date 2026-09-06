# MICE imputation for the processed Dataset
# 1. Imports and paths
from pathlib import Path
import re

import numpy as np
import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge

# Works when the notebook is run from either the repository root or notebooks/.
PROJECT_ROOT = Path.cwd()
if not (PROJECT_ROOT / 'Data').exists():
    PROJECT_ROOT = PROJECT_ROOT.parent

DATA_PATH = PROJECT_ROOT / 'Data/Processed/TiAl_Ball_Milling_clean_dataset.csv'
OUTPUT_PATH = PROJECT_ROOT / 'Data/Processed/TiAl_Ball_Milling_imputed_dataset.csv'
TARGET_COLUMNS = ['hardness_hv', 'strength_hv']
REQUIRED_COLUMNS = [
    'sample_id', 'sample_name', 'mill_type', 'rpm', 'Time', 'bpr_reported',
    *TARGET_COLUMNS,
]

# 2. Load the cleaned data and normalize every textual missing-value marker.
df = pd.read_csv(
    DATA_PATH,
    na_values=['NA', 'na', 'N/A', 'n/a', '', 'NaN', '<NA>', 'null', 'None'],
    keep_default_na=True,
)
df = df.replace(r'^\s*$', np.nan, regex=True)

missing_columns = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
if missing_columns:
    raise KeyError(f'Required columns are missing: {missing_columns}')

# Coercion makes non-numeric text in modelled numerical columns missing instead of failing later.
for column in ['rpm', 'Time', *TARGET_COLUMNS]:
    df[column] = pd.to_numeric(df[column], errors='coerce')

print(f'Loaded {len(df)} rows from {DATA_PATH.name}')
audit = pd.DataFrame({
    'missing_count': df.isna().sum(),
    'missing_%': (df.isna().mean() * 100).round(1),
    'dtype': df.dtypes.astype(str),
})
display(audit)

# 3. Prepare the numeric MICE matrix.
def parse_bpr(value):
    """Return the leading number from a BPR such as '10:1', otherwise NaN."""
    if pd.isna(value):
        return np.nan
    match = re.match(r'^\s*(\d+(?:\.\d+)?)\s*:\s*1\s*$', str(value))
    return float(match.group(1)) if match else np.nan

df['bpr_numeric'] = df['bpr_reported'].map(parse_bpr)

# A deterministic map makes the category decoding reproducible.
mill_types = sorted(df['mill_type'].dropna().astype(str).unique())
if not mill_types:
    raise ValueError('mill_type has no observed values, so it cannot be imputed.')
mill_type_to_code = {label: code for code, label in enumerate(mill_types)}
code_to_mill_type = {code: label for label, code in mill_type_to_code.items()}
df['mill_type_code'] = df['mill_type'].map(mill_type_to_code)

MICE_COLUMNS = ['rpm', 'Time', 'bpr_numeric', 'mill_type_code', *TARGET_COLUMNS]
X_mice = df[MICE_COLUMNS].copy()

empty_model_columns = X_mice.columns[X_mice.notna().sum().eq(0)].tolist()
if empty_model_columns:
    raise ValueError(f'Cannot impute columns with no observed values: {empty_model_columns}')

print('MICE matrix missing values:')
display(X_mice.isna().sum().rename('missing_count').to_frame().T)
print('mill_type encoding:', mill_type_to_code)

# 4. Multivariate regression MICE. Each incomplete column is regressed on the others.
# BayesianRidge is a multivariate linear regression estimator and is reproducible here.
mice = IterativeImputer(
    estimator=BayesianRidge(),
    max_iter=25,
    tol=1e-3,
    random_state=42,
    skip_complete=True,
)
X_imputed = mice.fit_transform(X_mice)
df_mice = pd.DataFrame(X_imputed, columns=MICE_COLUMNS, index=df.index)

if not mice.n_iter_ < mice.max_iter:
    print('Warning: MICE reached max_iter; consider more observations or a simpler feature set.')

display(df_mice)

# 5. Merge imputed values back, restoring units and category labels.
df_out = df.drop(columns=['bpr_numeric', 'mill_type_code']).copy()

# Preserve observed values; only write MICE estimates into originally missing cells.
for column in ['rpm', 'Time', *TARGET_COLUMNS]:
    missing_mask = df[column].isna()
    df_out.loc[missing_mask, column] = df_mice.loc[missing_mask, column]

# RPM and time are recorded as whole numbers. Hardness and strength retain two decimal places.
df_out['rpm'] = df_out['rpm'].round().astype('Int64')
df_out['Time'] = df_out['Time'].round().astype('Int64')
df_out[TARGET_COLUMNS] = df_out[TARGET_COLUMNS].round(2)

missing_bpr = df['bpr_reported'].isna()
df_out.loc[missing_bpr, 'bpr_reported'] = (
    df_mice.loc[missing_bpr, 'bpr_numeric'].round(2).map(lambda value: f'{value:g}:1')
)

missing_mill_type = df['mill_type'].isna()
rounded_codes = (
    df_mice['mill_type_code'].round().clip(0, len(mill_types) - 1).astype(int)
)
df_out.loc[missing_mill_type, 'mill_type'] = rounded_codes.loc[missing_mill_type].map(code_to_mill_type)

imputed_cells = pd.DataFrame({
    'column': ['rpm', 'Time', 'bpr_reported', 'mill_type', *TARGET_COLUMNS],
    'cells_imputed': [
        int(df['rpm'].isna().sum()), int(df['Time'].isna().sum()),
        int(df['bpr_reported'].isna().sum()), int(df['mill_type'].isna().sum()),
        *(int(df[column].isna().sum()) for column in TARGET_COLUMNS),
    ],
})
display(imputed_cells)

# 6. Validate and export. Identifiers/names are deliberately never fabricated.
OUTPUT_COLUMNS = REQUIRED_COLUMNS
unmodelled_missing = df_out[['sample_id', 'sample_name']].isna().sum()
if unmodelled_missing.any():
    raise ValueError(
        'sample_id or sample_name is missing. These identifiers cannot be statistically imputed; '
        f'fix the source rows first: {unmodelled_missing[unmodelled_missing.gt(0)].to_dict()}'
    )

remaining = df_out[OUTPUT_COLUMNS].isna().sum()
display(remaining.rename('remaining_missing').to_frame().T)
assert remaining.sum() == 0, f'Imputation incomplete: {remaining[remaining.gt(0)].to_dict()}'

df_out[OUTPUT_COLUMNS].to_csv(OUTPUT_PATH, index=False, na_rep='NA')
print(f'Saved fully imputed data to: {OUTPUT_PATH}')
print(f'Output shape: {df_out[OUTPUT_COLUMNS].shape}')
