import camelot

# Updating the current PATH inside Python

import os
from pathlib import Path


def update_app_path(app, new_path):
    # Get the PATH environment variable
    existing = [Path(p) for p in os.environ['PATH'].split(os.path.pathsep)]
    # Copy it, deleting any paths that refer to the application of interest
    new_path = [e for e in existing if not Path(e/app).exists()]
    # Append a the new entry
    new_path.append(new_path)
    # or you could use new_path.append(Path(new_path).parent)
    # Reconstruct and apply the PATH
    os.environ['PATH'] = os.path.pathsep.join(map(str, new_path))


update_app_path('ghostcript', Path(
    'C:\\Users\\Utilisateur\\Desktop\\cours\\ESIPE3\\LAST_PROJECT\\rush\\api\\poc\\.venv\\Lib\\site-packages\\ghostscript'))

tables = camelot.read_pdf(
    'res/Matter-1.2-Application-Cluster-Specification.pdf',
    pages='63',
    line_scale=30)
nbTables = tables.n
print(nbTables, "\n")


for table in tables:
    print(table)
    print(table.parsing_report)
    print(table.df)
    print("\n")
