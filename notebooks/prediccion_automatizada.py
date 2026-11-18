import os
import json
import requests
import time

def predecir_con_esmfold_api(json_metadata="osa_gnn_metadata.json", carpeta_salida="estructuras_pdb", limite=20):
    print("==================================================")
    print("   Predicción Estructural Automatizada (ESMFold)  ")
    print("==================================================\n")
    
    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

    try:
        with open(json_metadata, 'r', encoding='utf-8') as f:
            proteinas = json.load(f)
    except Exception as e:
        print(f"❌ Error leyendo el archivo JSON: {e}")
        return

    # ESMFold API es rapidísima, pero su límite público por petición es de ~400 aminoácidos.
    # Filtramos secuencias válidas dentro de este rango.
    proteinas_viables = [p for p in proteinas if p.get('Secuencia') and len(p['Secuencia']) <= 400]
    
    # Ordenar de la más corta a la más larga
    proteinas_ordenadas = sorted(proteinas_viables, key=lambda x: x['Longitud'])
    lote = proteinas_ordenadas[:limite]

    if not lote:
        print("⚠️ No se encontraron proteínas menores a 400 AA en tu dataset.")
        return

    print(f"🚀 Iniciando predicción en la nube de {len(lote)} proteínas...")
    print(f"Servidor: Meta AI (ESM Metagenomic Atlas)\n")

    url = "https://api.esmatlas.com/foldSequence/v1/pdb/"
    exitos = 0

    for i, prot in enumerate(lote, 1):
        uniprot_id = str(prot['Uniprot_ID']).strip()
        secuencia = str(prot['Secuencia']).strip()
        archivo_salida = os.path.join(carpeta_salida, f"{uniprot_id}.pdb")

        # Evitar re-trabajo si ya la descargamos o si ya la hiciste manual
        if os.path.exists(archivo_salida):
            print(f"[{i}/{len(lote)}] ⏭️ {uniprot_id} ya existe. Omitiendo.")
            exitos += 1
            continue

        print(f"[{i}/{len(lote)}] 🧬 Plegando {uniprot_id} ({len(secuencia)} AA)...", end=" ", flush=True)
        
        try:
            # Hacemos la petición POST directamente a la IA
            response = requests.post(url, data=secuencia, timeout=60)
            
            if response.status_code == 200:
                with open(archivo_salida, 'w') as f:
                    f.write(response.text)
                print("✅ ¡Éxito!")
                exitos += 1
            else:
                print(f"❌ Fallo de servidor (Código {response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de red.")

        # Pausa de seguridad de 2 segundos para no saturar el servidor gratuito
        time.sleep(2)

    print("\n==================================================")
    print(f"🎯 Proceso Finalizado: {exitos}/{len(lote)} estructuras generadas.")
    print("==================================================")
    print("Tus archivos .pdb están listos en la carpeta para pasar a la matriz de adyacencia.")

if __name__ == "__main__":
    # He puesto el límite inicial en 20 para que veas la velocidad.
    # Si funciona bien, simplemente cambia este número a 100 y ve por un café.
    predecir_con_esmfold_api(limite=20)