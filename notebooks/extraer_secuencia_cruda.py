import json

def obtener_secuencia_directa(json_metadata="osa_gnn_metadata.json"):
    print("==================================================")
    print("   Extractor de Secuencia para Inyección Directa  ")
    print("==================================================\n")
    
    try:
        with open(json_metadata, 'r', encoding='utf-8') as f:
            proteinas = json.load(f)
    except Exception as e:
        print(f"❌ Error leyendo el archivo JSON: {e}")
        return

    # Buscamos una proteína pequeña para que la predicción tarde menos de 2 minutos
    proteinas_cortas = [p for p in proteinas if p.get('Secuencia') and 50 < p['Longitud'] < 200]
    
    if not proteinas_cortas:
        print("⚠️ No hay proteínas menores a 200 AA. Tomando la primera disponible...")
        proteina_objetivo = proteinas[0]
    else:
        proteina_objetivo = proteinas_cortas[0]

    uniprot_id = str(proteina_objetivo['Uniprot_ID']).strip()
    secuencia = str(proteina_objetivo['Secuencia']).strip()

    print(f"🎯 Proteína seleccionada: {uniprot_id} (Longitud: {proteina_objetivo['Longitud']} AA)\n")
    print("PASO 1: Ve a Google ColabFold.")
    print("PASO 2: Borra lo que haya en la casilla 'query_sequence'.")
    print("PASO 3: Copia exactamente el texto que está entre las líneas punteadas y pégalo allí:\n")
    
    print("-" * 50)
    print(secuencia)
    print("-" * 50)
    
    print("\nPASO 4: En 'jobname', escribe:", uniprot_id)
    print("PASO 5: Dale a 'Entorno de ejecución' -> 'Ejecutar todo'.")

if __name__ == "__main__":
    obtener_secuencia_directa()