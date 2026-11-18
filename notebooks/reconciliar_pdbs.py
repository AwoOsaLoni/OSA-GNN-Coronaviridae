import os
import json
import shutil

def reconciliar_estructuras_locales(ruta_carpeta_tus_pdbs, json_metadata="osa_gnn_metadata.json", carpeta_oficial_gnn="estructuras_pdb"):
    print("==================================================")
    print("   Auditoría de Estructuras Locales para OSA-GNN  ")
    print("==================================================\n")
    
    # 1. Verificar que tus archivos existan
    if not os.path.exists(ruta_carpeta_tus_pdbs):
        print(f"❌ Error: No encuentro la carpeta '{ruta_carpeta_tus_pdbs}'.")
        return
        
    if not os.path.exists(carpeta_oficial_gnn):
        os.makedirs(carpeta_oficial_gnn)

    # 2. Cargar los IDs que la GNN necesita (las 236 proteínas)
    with open(json_metadata, 'r', encoding='utf-8') as f:
        proteinas = json.load(f)
        
    ids_necesarios = {str(p["Uniprot_ID"]).strip() for p in proteinas}
    print(f"🎯 El modelo OSA-GNN está buscando {len(ids_necesarios)} estructuras específicas.")

    # 3. Escanear tu carpeta local
    archivos_locales = os.listdir(ruta_carpeta_tus_pdbs)
    pdbs_locales = [f for f in archivos_locales if f.endswith('.pdb')]
    print(f"📂 Se encontraron {len(pdbs_locales)} archivos .pdb en tu carpeta personal.\n")

    coincidencias = 0
    
    print("-" * 50)
    for archivo in pdbs_locales:
        # Asumimos que el nombre del archivo contiene el ID de UniProt (ej. P0DTC2.pdb o AF-P0DTC2-F1.pdb)
        # Limpiamos el nombre para extraer solo el código
        nombre_base = archivo.replace('.pdb', '').replace('AF-', '').replace('-F1-model_v4', '').strip()
        
        # Buscamos si ese código está dentro de nuestra lista de necesidades
        for id_necesario in ids_necesarios:
            if id_necesario in nombre_base:
                # ¡HAY MATCH! Copiamos el archivo a la carpeta oficial del modelo
                ruta_origen = os.path.join(ruta_carpeta_tus_pdbs, archivo)
                ruta_destino = os.path.join(carpeta_oficial_gnn, f"{id_necesario}.pdb")
                
                # Solo copiamos si no existe ya
                if not os.path.exists(ruta_destino):
                    shutil.copy2(ruta_origen, ruta_destino)
                    
                coincidencias += 1
                ids_necesarios.remove(id_necesario) # Lo quitamos de la lista de pendientes
                break # Pasamos al siguiente archivo

    # 4. Resultados para la Tesis
    print("\n==================================================")
    print("             Resultados de la Auditoría           ")
    print("==================================================")
    print(f"✅ Estructuras recuperadas e integradas : {coincidencias}")
    print(f"⚠️ Estructuras aún faltantes            : {len(ids_necesarios)}")
    print("==================================================")
    
    if len(ids_necesarios) > 0:
        print("💡 Próximo paso: Usaremos ColabFold para generar las faltantes.")

if __name__ == "__main__":
    # --- CAMBIA ESTA RUTA POR LA CARPETA DONDE TIENES TUS PDBS ---
    # Ejemplo en Windows: r"C:\Users\Silvio\Desktop\Mis_Estructuras_Coronaviridae"
    MI_CARPETA_CON_PDBS = r"pdbs_locales" 
    
    reconciliar_estructuras_locales(MI_CARPETA_CON_PDBS)