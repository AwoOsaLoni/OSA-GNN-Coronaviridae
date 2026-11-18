import os
import json
import requests
import time

def descargar_estructuras_resiliente(json_metadata="osa_gnn_metadata.json", carpeta_salida="estructuras_pdb"):
    print("==================================================")
    print("   Iniciando Módulo de Rescate Estructural 3D     ")
    print("==================================================\n")
    
    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

    with open(json_metadata, 'r', encoding='utf-8') as f:
        proteinas = json.load(f)

    total = len(proteinas)
    descargas_af = 0
    descargas_pdb = 0
    errores = 0

    print("🔍 Inspeccionando el primer registro para diagnóstico:")
    primer_id = str(proteinas[0].get("Uniprot_ID")).strip()
    print(f"ID Limpio: '{primer_id}'")
    print(f"URL de prueba: https://alphafold.ebi.ac.uk/files/AF-{primer_id}-F1-model_v4.pdb\n")
    print("-" * 50)

    for i, prot in enumerate(proteinas, 1):
        # LIMPIEZA CRÍTICA: Quitamos espacios vacíos que arruinan la URL
        uniprot_id = str(prot.get("Uniprot_ID")).strip()
        archivo_salida = os.path.join(carpeta_salida, f"{uniprot_id}.pdb")

        if os.path.exists(archivo_salida):
            print(f"[{i}/{total}] ⏭️ {uniprot_id} ya existe.")
            continue

        # INTENTO 1: AlphaFold DB
        url_af = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v4.pdb"
        try:
            res_af = requests.get(url_af, timeout=5)
            if res_af.status_code == 200:
                with open(archivo_salida, 'w') as f:
                    f.write(res_af.text)
                print(f"[{i}/{total}] ✅ {uniprot_id} descargado de AlphaFold.")
                descargas_af += 1
                time.sleep(0.2)
                continue
        except:
            pass

        # INTENTO 2: Protein Data Bank (Estructuras Experimentales Reales)
        # Usamos la API de Uniprot para ver si hay mapeo a PDB
        url_uniprot = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
        try:
            res_up = requests.get(url_uniprot, timeout=5)
            if res_up.status_code == 200:
                data = res_up.json()
                pdb_id = None
                for ref in data.get("crossReferences", []):
                    if ref["database"] == "PDB":
                        pdb_id = ref["id"]
                        break # Tomamos el primer PDB experimental disponible
                
                if pdb_id:
                    url_pdb = f"https://files.rcsb.org/download/{pdb_id}.pdb"
                    res_pdb = requests.get(url_pdb, timeout=5)
                    if res_pdb.status_code == 200:
                        with open(archivo_salida, 'w') as f:
                            f.write(res_pdb.text)
                        print(f"[{i}/{total}] 🔬 {uniprot_id} descargado de PDB (ID: {pdb_id}).")
                        descargas_pdb += 1
                        time.sleep(0.2)
                        continue
        except:
            pass
        
        print(f"[{i}/{total}] ❌ {uniprot_id} sin estructura 3D en la nube.")
        errores += 1

    print("\n--- RESUMEN FINAL ---")
    print(f"AlphaFold: {descargas_af}")
    print(f"PDB Exp. : {descargas_pdb}")
    print(f"Fallidos : {errores}")

if __name__ == "__main__":
    descargar_estructuras_resiliente()