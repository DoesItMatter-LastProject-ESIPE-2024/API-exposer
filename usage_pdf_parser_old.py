import camelot

from typing import List

if __name__ == '__main__':
    tables = camelot.read_pdf(
        'res/Matter-1.2-Application-Cluster-Specification.pdf',
        # pages='1-end',
        pages='109',
        line_scale=30,
    )

    nb_tables = tables.n
    print(nb_tables)

    file = open("pdf_parser/out/tmp.txt", "w")

    for table in tables:
        numpy_table = table.df.to_numpy()
        # print(numpy_table[0])
        file.write(str(numpy_table[0]) + "\n")

    file.close()


def header_match(header: List[str]) -> bool:
    match header:
        case ['ID', 'Name']:  # Cluster
            return True
        case ['Bit', 'Code', 'Feature', 'Summary']:  # Feature
            return True
        case ['Bit', 'Code', 'Name', 'Summary']:  # Feature
            return True
        case ['ID', 'Name', 'Type', 'Constraint', 'Quality', 'Default', 'Access', 'Conformance']:  # Attribute
            return True
        case ['ID', 'Name', 'Direction', 'Response', 'Access', 'Conformance']:  # Command
            return True
        case _:
            return False
