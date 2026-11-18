import json

def preparar_lote_masivo(json_metadata="osa_gnn_metadata.json", output_fasta="lote_100_colabfold.fasta", limite=100):
    print("==================================================")
    print("   Generador de Lotes (FASTA) para ColabFold      ")
    print("==================================================\n")
    
    try:
        with open(json_metadata, 'r', encoding='utf-8') as f:
            proteinas = json.load(f)
    except Exception as e:
        print(f"❌ Error leyendo el archivo JSON: {e}")
        return

    # 1. Filtrar las proteínas que no tengan secuencia válida
    proteinas_validas = [p for p in proteinas if p.get('Secuencia') and len(p['Secuencia']) > 0]
    
    # 2. ORDENAMIENTO ESTRATÉGICO: De la más corta a la más larga
    # Esto evita que una proteína gigante sature el servidor en la primera hora
    proteinas_ordenadas = sorted(proteinas_validas, key=lambda x: x['Longitud'])
    
    # 3. Tomar las 100 primeras (o el máximo disponible si hay menos de 100)
    lote_final = proteinas_ordenadas[:limite]
    
    if not lote_final:
        print("⚠️ No se encontraron proteínas válidas.")
        return

    # 4. Escribir el archivo en formato FASTA
    with open(output_fasta, 'w', encoding='utf-8') as f:
        for prot in lote_final:
            uniprot_id = str(prot['Uniprot_ID']).strip()
            secuencia = str(prot['Secuencia']).strip()
            
            # El formato FASTA exige un ">" seguido del ID en la primera línea
            # y la secuencia de aminoácidos en la siguiente.
            f.write(f">{uniprot_id}\n")
            f.write(f"{secuencia}\n")
            
    print(f"✅ ¡Éxito! Archivo FASTA generado: '{output_fasta}'")
    print(f"Contiene {len(lote_final)} secuencias virales ordenadas por longitud.")
    
    # Mostrar un pequeño resumen de las 5 más largas del lote para estimar tiempos
    print("\nResumen de las 5 proteínas más largas de este lote de 100:")
    for p in lote_final[-5:]:
        print(f" - ID: {p['Uniprot_ID']} | Longitud: {p['Longitud']} AA")
        
    print("\nSiguiente paso: Subir este archivo a Google ColabFold.")

if __name__ == "__main__":
    preparar_lote_masivo()