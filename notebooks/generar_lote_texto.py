import json
import os

def generar_lote_para_inyeccion(json_metadata="osa_gnn_metadata.json", output_txt="lote_para_copiar.txt", cantidad=5):
    print("==================================================")
    print("   Generador de Lotes para Inyección en ColabFold ")
    print("==================================================\n")
    
    try:
        with open(json_metadata, 'r', encoding='utf-8') as f:
            proteinas = json.load(f)
    except Exception as e:
        print(f"❌ Error leyendo el archivo JSON: {e}")
        return

    # 1. Filtramos proteínas viables (menores a 300 AA para no saturar la RAM gratuita)
    proteinas_viables = [p for p in proteinas if p.get('Secuencia') and 50 < p['Longitud'] < 300]
    
    if not proteinas_viables:
        print("⚠️ No hay proteínas en ese rango de longitud.")
        return

    # 2. Tomamos la cantidad deseada (Ej. 5 para un lote seguro y rápido)
    lote = proteinas_viables[:cantidad]

    # 3. Guardamos el texto formateado en un archivo .txt plano
    with open(output_txt, 'w', encoding='utf-8') as f:
        for prot in lote:
            uniprot_id = str(prot['Uniprot_ID']).strip()
            secuencia = str(prot['Secuencia']).strip()
            # Formato FASTA crudo
            f.write(f">{uniprot_id}\n{secuencia}\n")

    print(f"✅ Archivo generado exitosamente: '{output_txt}'")
    print(f"Contiene {len(lote)} secuencias virales.\n")
    print("INSTRUCCIONES:")
    print(f"1. Abre el archivo '{output_txt}' aquí en VS Code.")
    print("2. Selecciona todo el texto (Ctrl+A) y cópialo (Ctrl+C).")
    print("3. Pégalo directamente en la casilla 'query_sequence' de ColabFold.")

if __name__ == "__main__":
    # Empecemos con un lote conservador de 5 proteínas para asegurar el éxito.
    # Una vez que esto funcione, puedes subir este número a 10 o 20.
    generar_lote_para_inyeccion(cantidad=5)