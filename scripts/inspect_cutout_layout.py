"""Download one QR2 and one QR3 spectral-image cutout at a position and print the MEF layout.

Small-scale validation of the extension names, VERSION keyword, flag-bit keywords,
and PSF/EPSF extension format for each release.
"""

import sys

import pyvo
from astropy.io import fits
from astropy.utils.data import conf

conf.remote_timeout = 180
IRSA_TAP_URL = "https://irsa.ipac.caltech.edu/TAP"


def latest_uri_for_collection(service, ra, dec, collection):
    query = f"""
    SELECT TOP 1 'https://irsa.ipac.caltech.edu/' || a.uri || '?center={ra},{dec}d&size=0.05' AS uri,
           p.provenance_version, p.energy_bandpassname, p.time_bounds_lower
    FROM spherex.artifact a
    JOIN spherex.plane p ON a.planeid = p.planeid
    JOIN spherex.observation o ON o.obsid = p.obsid
    WHERE 1 = CONTAINS(POINT('ICRS', {ra}, {dec}), p.poly)
      AND o.collection = '{collection}'
      AND p.energy_bandpassname = 'SPHEREx-D3'
    ORDER BY p.time_bounds_lower DESC
    """
    table = service.search(query).to_table()
    return table


def describe(uri):
    with fits.open(uri, cache=False) as hdulist:
        hdulist.info()
        primary = hdulist[0].header
        for key in ("VERSION", "FINAST", "OBSID", "DETECTOR", "PSF_FWHM"):
            if key in primary:
                print(f"  PRIMARY[{key}] = {primary[key]}")
        image_header = hdulist["IMAGE"].header
        for key in ("BUNIT", "FINAST", "WCSNAMEW", "PSF_FWHM", "PSF_NEFF"):
            if key in image_header:
                print(f"  IMAGE[{key}] = {image_header[key]}")
        hierarch = [k for k in image_header if k.startswith("L2 ")]
        print("  IMAGE HIERARCH L2 keys:", hierarch[:40])
        flags_header = hdulist["FLAGS"].header
        bits = {k[3:]: flags_header[k] for k in flags_header if k.startswith("MP_")}
        print("  FLAGS bit map:", bits)
        for name in ("PSF", "EPSF"):
            if name in hdulist:
                hdu = hdulist[name]
                print(f"  {name}: type={type(hdu).__name__}, shape={getattr(hdu.data, 'shape', None)}")
                if hasattr(hdu, "columns"):
                    print("   columns:", hdu.columns.names)
                for key in ("OVERSAMP", "OVSMPX", "OVSMPY", "NAXIS2", "TDIM11"):
                    if key in hdu.header:
                        print(f"   {name}[{key}] = {hdu.header[key]}")
        if "ZODI" in hdulist:
            zodi = hdulist["ZODI"]
            print("  ZODI median:", float(__import__("numpy").nanmedian(zodi.data)), zodi.header.get("BUNIT"))


def main():
    ra, dec = 210.80227, 54.34895  # M101, high ecliptic latitude
    service = pyvo.dal.TAPService(IRSA_TAP_URL)
    for collection in ("spherex_qr2", "spherex_qr3"):
        table = latest_uri_for_collection(service, ra, dec, collection)
        print(f"\n===== {collection} =====")
        if len(table) == 0:
            print("  no coverage yet at this position")
            continue
        print(table)
        describe(table["uri"][0])


if __name__ == "__main__":
    sys.exit(main())
