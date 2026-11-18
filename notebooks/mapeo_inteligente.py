import os
import json
import shutil
import re

def mapeo_inteligente_pdbs(ruta_local, json_meta="osa_gnn_metadata.json", carpeta_out="estructuras_pdb"):
    print("==================================================")
    print("   Iniciando Mapeo Inteligente (Heurística)       ")
    print("==================================================\n")
    
    if not os.path.exists(ruta_local):
        print(f"❌ Error: La carpeta '{ruta_local}' no existe.")
        return
        
    if not os.path.exists(carpeta_out):
        os.makedirs(carpeta_out)

    # 1. Cargar la metadata de la GNN
    with open(json_meta, 'r', encoding='utf-8') as f:
        proteinas = json.load(f)

    archivos_locales = [f for f in os.listdir(ruta_local) if f.endswith('.pdb')]
    print(f"📂 Analizando {len(archivos_locales)} archivos .pdb locales...\n")

    exitos = 0
    sin_coincidencia = []

    for archivo in archivos_locales:
        # 2. Limpiar el nombre del archivo para extraer palabras clave
        # Quitamos números iniciales, extensiones y separamos por guiones o guiones bajos
        nombre_limpio = re.sub(r'^\d+_', '', archivo) # Quita el "1_" o "19_" del inicio
        nombre_limpio = nombre_limpio.replace('_ranked_0.pdb', '').replace('_ranked_1.pdb', '').replace('.pdb', '')
        palabras_clave_archivo = set(re.split(r'[-_ ]+', nombre_limpio.lower()))

        mejor_match = None
        mejor_puntaje = 0

        # 3. Buscar estas palabras en nuestro JSON (Organismo y Nombre)
        for prot in proteinas:
            texto_referencia = f"{prot.get('Organismo', '')} {prot.get('Nombre', '')}".lower()
            palabras_referencia = set(re.split(r'[-_ ,()]+', texto_referencia))

            # Calculamos cuántas palabras coinciden (Intersección)
            coincidencias = palabras_clave_archivo.intersection(palabras_referencia)
            puntaje = len(coincidencias)

            # Si el puntaje es el más alto hasta ahora, lo guardamos
            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor_match = prot

        # 4. Evaluar si el match es lo suficientemente bueno (Umbral)
        # Si coinciden al menos 2 palabras clave fuertes, lo damos por bueno
        if mejor_match and mejor_puntaje >= 2:
            uniprot_id = mejor_match["Uniprot_ID"]
            ruta_origen = os.path.join(ruta_local, archivo)
            ruta_destino = os.path.join(carpeta_out, f"{uniprot_id}.pdb")
            
            if not os.path.exists(ruta_destino):
                shutil.copy2(ruta_origen, ruta_destino)
            
            print(f"✅ MATCH: '{archivo}' ---> {uniprot_id}.pdb")
            print(f"   (Basado en: {mejor_match['Organismo'][:50]}...)")
            exitos += 1
        else:
            sin_coincidencia.append(archivo)

    print("\n==================================================")
    print("             Resumen del Mapeo                    ")
    print("==================================================")
    print(f"Estructuras enlazadas y renombradas : {exitos}")
    print(f"Estructuras sin match claro         : {len(sin_coincidencia)}")
    print("==================================================")
    
    if sin_coincidencia:
        print("\n⚠️ Archivos que no cruzaron con el JSON (pueden ser de otras familias):")
        for sc in sin_coincidencia[:5]: # Mostrar solo los primeros 5
            print(f" - {sc}")

if __name__ == "__main__":
    # --- COLOCA AQUÍ EL NOMBRE DE LA CARPETA DONDE METISTE LAS FOTOS ---
    # Si la moviste a tu proyecto en VS Code, solo pon el nombre de la carpeta.
    CARPETA_CON_PDBS = "pdbs_locales" 
    
    mapeo_inteligente_pdbs(CARPETA_CON_PDBS)