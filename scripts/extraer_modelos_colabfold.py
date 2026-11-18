import os
import shutil

def extraer_mejores_modelos(carpeta_origen="resultados_colabfold", carpeta_destino="estructuras_pdb_esmfold"):
    print("==================================================")
    print("   Extractor de Mejores Modelos (ColabFold -> OSA-GNN) ")
    print("==================================================\n")
    
    if not os.path.exists(carpeta_origen):
        print(f"❌ Error: No se encontró la carpeta '{carpeta_origen}'.")
        return

    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
            
    archivos = os.listdir(carpeta_origen)
    extraidos = 0
    
    print(f"🔍 Escaneando {len(archivos)} archivos en '{carpeta_origen}'...\n")
    
    for archivo in archivos:
        # Filtramos solo el mejor modelo (rank_001) en formato PDB
        if archivo.endswith(".pdb") and "rank_001" in archivo:
            
            # AISLAMIENTO PURO DEL ID:
            # Divide '381_Q80872_len...' y extrae la posición [1] ('Q80872')
            uniprot_id = archivo.split("_")[1]
            
            ruta_origen = os.path.join(carpeta_origen, archivo)
            ruta_destino = os.path.join(carpeta_destino, f"{uniprot_id}.pdb")
            
            shutil.copy2(ruta_origen, ruta_destino)
            print(f"✅ Modelo aislado: {uniprot_id}.pdb")
            extraidos += 1
            
    print("\n==================================================")
    print("             Resumen de Extracción                ")
    print("==================================================")
    print(f"Total de PDBs (rank_001) listos: {extraidos}")
    print(f"Carpeta de salida: {carpeta_destino}")
    print("==================================================")

if __name__ == "__main__":
    carpeta_descargas = "resultados_colabfold" 
    carpeta_para_red = "estructuras_pdb_esmfold"
    
    extraer_mejores_modelos(carpeta_origen=carpeta_descargas, carpeta_destino=carpeta_para_red)