import camelot

tables = camelot.read_pdf('res/Matter-1.2-Application-Cluster-Specification.pdf', pages='63', line_scale=30)
nbTables = tables.n
print(nbTables , "\n")

for table in tables:
    print(table)
    print(table.parsing_report)
    print(table.df)
    print("\n")
