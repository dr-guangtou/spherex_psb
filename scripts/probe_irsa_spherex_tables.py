"""List SPHEREx-related tables and collections at the IRSA TAP/SIA services.

Small-scale validation that current service names match the documentation.
"""

import pyvo

IRSA_TAP_URL = "https://irsa.ipac.caltech.edu/TAP"


def main() -> None:
    service = pyvo.dal.TAPService(IRSA_TAP_URL)
    query = (
        "SELECT schema_name, table_name, description FROM TAP_SCHEMA.tables "
        "WHERE lower(table_name) LIKE '%spherex%' OR lower(schema_name) LIKE '%spherex%'"
    )
    tables = service.search(query).to_table()
    tables.pprint_all(max_width=200)

    print("\n--- distinct collections in spherex.plane (if present) ---")
    try:
        collections = service.search("SELECT DISTINCT collection FROM spherex.plane").to_table()
        collections.pprint_all()
    except Exception as error:  # noqa: BLE001
        print("collection query failed:", error)

    print("\n--- distinct bandpass names ---")
    try:
        bands = service.search("SELECT DISTINCT energy_bandpassname FROM spherex.plane").to_table()
        bands.pprint_all()
    except Exception as error:  # noqa: BLE001
        print("bandpass query failed:", error)


if __name__ == "__main__":
    main()
