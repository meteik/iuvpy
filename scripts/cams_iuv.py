# ZIP
# =============================================================================

zip_salida = os.path.join(

    corrida_dir,

    f"{nombre_corrida}_{run_id}.zip"

)


print()
print(
    "Creando ZIP..."
)


with zipfile.ZipFile(

    zip_salida,

    "w",

    zipfile.ZIP_DEFLATED

) as zipf:


    # -------------------------------------------------------------------------
    # GRIB
    # -------------------------------------------------------------------------

    if os.path.exists(
        grib_file
    ):

        zipf.write(

            grib_file,

            arcname=os.path.join(

                f"DATA_{run_id}",

                os.path.basename(
                    grib_file
                )

            )

        )


    # -------------------------------------------------------------------------
    # MAPA
    # -------------------------------------------------------------------------

    if os.path.exists(
        salida
    ):

        zipf.write(

            salida,

            arcname=os.path.join(

                f"MAPAS_{run_id}",

                os.path.basename(
                    salida
                )

            )

        )


# =============================================================================
# RESUMEN FINAL
# =============================================================================

print()
print("=" * 80)
print("                    PROCESO FINALIZADO")
print("=" * 80)

print()

print(
    f"✓ Modelo       : ECMWF / CAMS"
)

print(
    f"✓ Fecha        : "
    f"{fecha_run:%d/%m/%Y}"
)

print(
    f"✓ Corrida      : "
    f"{hora}Z"
)

print(
    f"✓ Identificador: "
    f"{run_id}"
)

print()

print(
    f"✓ DATA:\n{data_dir}"
)

print()

print(
    f"✓ MAPAS:\n{mapas_dir}"
)

print()

print(
    f"✓ MAPA:\n{salida}"
)

print()

print(
    f"✓ ZIP:\n{zip_salida}"
)

print()
print("=" * 80)
