import os
import json
import requests
import time

def prediccion_masiva_esmfold(json_metadata="osa_gnn_metadata.json", carpeta_salida="estructuras_pdb"):
    print("==================================================")
    print("   Extracción Masiva de Estructuras (ESMFold API) ")
    print("==================================================\n")
    
    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

    try:
        with open(json_metadata, 'r', encoding='utf-8') as f:
            proteinas = json.load(f)
    except Exception as e:
        print(f"❌ Error leyendo el archivo JSON: {e}")
        return

    # Filtramos secuencias con el límite máximo seguro para la API pública (~400 AA)
    # Proteínas más largas que esto generarán un error 500/504 en el servidor de Meta.
    proteinas_viables = [p for p in proteinas if p.get('Secuencia') and len(p['Secuencia']) <= 400]
    
    # Ordenamos de menor a mayor para asegurar que las más fáciles se procesen primero
    lote_masivo = sorted(proteinas_viables, key=lambda x: x['Longitud'])

    if not lote_masivo:
        print("⚠️ No se encontraron proteínas en el rango aceptado por la API.")
        return

    print(f"🚀 Iniciando procesamiento intensivo para {len(lote_masivo)} proteínas viables...")
    print("Este proceso tomará tiempo. Puedes minimizar la terminal.\n")

    url = "https://api.esmatlas.com/foldSequence/v1/pdb/"
    exitos = 0
    errores = 0
    existentes = 0

    for i, prot in enumerate(lote_masivo, 1):
        uniprot_id = str(prot['Uniprot_ID']).strip()
        secuencia = str(prot['Secuencia']).strip()
        longitud = len(secuencia)
        archivo_salida = os.path.join(carpeta_salida, f"{uniprot_id}.pdb")

        if os.path.exists(archivo_salida):
            print(f"[{i}/{len(lote_masivo)}] ⏭️ {uniprot_id} ({longitud} AA) ya existe.")
            existentes += 1
            continue

        print(f"[{i}/{len(lote_masivo)}] 🧬 Prediciendo {uniprot_id} ({longitud} AA)...", end=" ", flush=True)
        
        try:
            # Aumentamos el timeout a 120 segundos para proteínas más grandes
            response = requests.post(url, data=secuencia, timeout=120)
            
            if response.status_code == 200:
                with open(archivo_salida, 'w') as f:
                    f.write(response.text)
                print("✅ Guardado")
                exitos += 1
            elif response.status_code == 429:
                print("⚠️ Demasiadas peticiones. Pausando 10s...")
                time.sleep(10)
                errores += 1
            else:
                print(f"❌ Fallo API (HTTP {response.status_code})")
                errores += 1
                
        except requests.exceptions.RequestException as e:
            print("❌ Timeout o error de red")
            errores += 1

        # Pausa obligatoria para ser corteses con el servidor y evitar bloqueos
        time.sleep(3)

    print("\n==================================================")
    print("             Resumen de Predicción Masiva         ")
    print("==================================================")
    print(f"Nuevas estructuras generadas : {exitos}")
    print(f"Estructuras previamente listas: {existentes}")
    print(f"Errores (Límite de API)      : {errores}")
    print(f"Total disponible para OSA-GNN: {exitos + existentes}")
    print("==================================================")

if __name__ == "__main__":
    prediccion_masiva_esmfold()