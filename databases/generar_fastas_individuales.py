import os
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Ruta absoluta de tu base de datos
EXCEL_PATH = r"d:\Escuela\TESIS\Tesis Nueva\Prototipo O.S.A.-GNN\databases\Reviewed_DB.xlsx"
CARPETA_SALIDA = r"d:\Escuela\TESIS\Tesis Nueva\Prototipo O.S.A.-GNN\databases\fastas_individuales_ordenadas"

os.makedirs(CARPETA_SALIDA, exist_ok=True)

if not os.path.exists(EXCEL_PATH):
    print(f"[ERROR] No se encontró el archivo en la ruta: {EXCEL_PATH}")
else:
    df = pd.read_excel(EXCEL_PATH)
    
    # 1. ORDENAR ESTRICTAMENTE DE MAYOR A MENOR LONGITUD (ascending=False)
    df = df.sort_values(by='Length', ascending=False)
    
    print(f"Total de proteínas a procesar: {len(df)}")
    print(f"La proteína más grande tiene: {df['Length'].iloc[0]} aminoácidos ({df['Entry'].iloc[0]})")
    print(f"La proteína más pequeña tiene: {df['Length'].iloc[-1]} aminoácidos ({df['Entry'].iloc[-1]})\n")

    # 2. Generar un archivo .fasta independiente para cada proteína
    for index, row in df.iterrows():
        uniprot_id = row['Entry']
        longitud = row['Length']
        secuencia = row['Sequence']
        
        # Nombre del archivo incluye el orden, el ID y la longitud para tener control visual
        # Ejemplo: 001_P0DTC2_len_1352.fasta
        nombre_archivo = f"{index+1:03d}_{uniprot_id}_len_{longitud}.fasta"
        ruta_archivo = os.path.join(CARPETA_SALIDA, nombre_archivo)
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(f">{uniprot_id}\n{secuencia}\n")

    print(f"¡Listo! Se generaron 488 archivos FASTA individuales ordenados de mayor a menor en:\n{CARPETA_SALIDA}")