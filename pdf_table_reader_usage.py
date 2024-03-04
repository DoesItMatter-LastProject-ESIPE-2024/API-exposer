import camelot

tables = camelot.read_pdf(
    'res/Matter-1.2-Application-Cluster-Specification.pdf',
    pages='1-end',
    line_scale=30
)

nb_tables = tables.n
print(nb_tables)

file = open("tmp.txt", "a")


for table in tables:
    numpy_table = table.df.to_numpy()
    # print(numpy_table[0])
    file.write(str(numpy_table[0]) + "\n")

file.close()
