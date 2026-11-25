
    )


# =============================================================================
# GUARDAR MAPA
# =============================================================================

plt.savefig(

    salida,

    dpi=300,

    bbox_inches="tight"

)


plt.show()


# =============================================================================
# CERRAR FIGURA
# =============================================================================

plt.close()


# =============================================================================
# CREAR ZIP DE LA CORRIDA
# =============================================================================

zip_salida = os.path.join(

    corrida_dir,

    f"{nombre_corrida}.zip"

)


print()
print("=" * 80)
print("                    CREANDO ZIP")
print("=" * 80)


with zipfile.ZipFile(

    zip_salida,

    "w",

    zipfile.ZIP_DEFLATED

) as zipf:


    # -------------------------------------------------------------------------
    # Archivos GRIB2
    # -------------------------------------------------------------------------

    for archivo in archivos:

        if os.path.exists(
            archivo
        ):

            zipf.write(

                archivo,

                arcname=os.path.join(

                    f"DATA_{fecha}",

                    os.path.basename(
                        archivo
                    )

                )

            )


    # -------------------------------------------------------------------------
    # Mapas
    # -------------------------------------------------------------------------

    if os.path.exists(
        salida
    ):

        zipf.write(

            salida,

            arcname=os.path.join(

                f"MAPAS_{fecha}",

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
print(f"✓ Corrida       : {nombre_corrida}")

print(
    f"✓ Fecha corrida : "
    f"{fecha_run:%d/%m/%Y %H}Z"
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
