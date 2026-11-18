import json

def preparar_micro_lote_seguro(json_metadata="osa_gnn_metadata.json", output_fasta="micro_lote_seguro.fasta"):
    print("==================================================")
    print("   Generador de Micro-Lote (Prueba de Estrés)     ")
    print("==================================================\n")
    
    try:
        with open(json_metadata, 'r', encoding='utf-8') as f:
            proteinas = json.load(f)
    except Exception as e:
        print(f"❌ Error leyendo el archivo JSON: {e}")
        return

    # 1. Filtro ultra-estricto: Solo proteínas minúsculas (entre 50 y 150 aminoácidos)
    # Esto garantiza que el uso de RAM sea casi cero y tarde menos de 2 minutos.
    proteinas_minis = [p for p in proteinas if p.get('Secuencia') and 50 < p['Longitud'] < 150]
    
    if not proteinas_minis:
        print("⚠️ No se encontraron proteínas tan cortas. Ampliando rango a 250...")
        proteinas_minis = [p for p in proteinas if p.get('Secuencia') and 50 < p['Longitud'] < 250]

    # 2. Tomamos estrictamente solo 2 secuencias
    lote_prueba = proteinas_minis[:2]
    
    # 3. Generar el FASTA limpio
    with open(output_fasta, 'w', encoding='utf-8') as f:
        for prot in lote_prueba:
            uniprot_id = str(prot['Uniprot_ID']).strip()
            secuencia = str(prot['Secuencia']).strip()
            f.write(f">{uniprot_id}\n{secuencia}\n")
            
    print(f"✅ ¡Éxito! Archivo generado: '{output_fasta}'")
    print("Este lote está diseñado para NO fallar por memoria.\n")
    print("Contenido exacto que se enviará a la IA:")
    for p in lote_prueba:
        print(f" - ID: {p['Uniprot_ID']} | Longitud: {p['Longitud']} AA")

if __name__ == "__main__":
    preparar_micro_lote_seguro()