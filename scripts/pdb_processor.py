import pandas as pd
import json
import os

def procesar_excel_osa_gnn(file_path):
    print(f"--- Iniciando Procesamiento de Dataset OSA-GNN ---")
    
    # 1. Carga del archivo Excel
    try:
        # Cargamos el archivo que descargaste manualmente
        df = pd.read_excel(file_path)
        print(f"✅ Archivo '{file_path}' cargado exitosamente.")
    except Exception as e:
        print(f"❌ Error al abrir el archivo: {e}. Asegúrate de que el nombre sea exacto.")
        return None

    # 2. Renombrado preventivo para asegurar compatibilidad con los scripts anteriores
    # UniProt suele exportar con nombres largos; aquí los estandarizamos
    mapeo_columnas = {
        'Entry': 'Uniprot_ID',
        'Protein names': 'Nombre',
        'Reviewed': 'Revisada',
        'Sequence': 'Secuencia',
        'Length': 'Longitud',
        'Gene Ontology (molecular function)': 'Funciones_GO',
        'Organism': 'Organismo',
        'AlphaFoldDB': 'ID_AlphaFold'
    }
    df = df.rename(columns=mapeo_columnas)

    # 3. Limpieza de datos nulos en columnas críticas (Secuencia y Funciones)
    total_inicial = len(df)
    df = df.dropna(subset=['Secuencia', 'Funciones_GO'])
    print(f"📉 Filtrado: Se conservan {len(df)} de {total_inicial} proteínas con anotación funcional.")

    # 4. Creación de una columna de "Prioridad" para tu Tesis
    # Las proteínas 'reviewed' (Swiss-Prot) son tu "Ground Truth"
    df['Prioridad'] = df['Revisada'].apply(lambda x: 'Alta (Swiss-Prot)' if x == 'reviewed' else 'Baja (TrEMBL)')

    # 5. Guardar una versión limpia en JSON para la GNN
    # Esto facilita que tu contenedor Docker lea los datos sin depender de Excel
    dataset_dict = df.to_dict(orient='records')
    with open('osa_gnn_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(dataset_dict, f, indent=4, ensure_ascii=False)
    
    print(f"🚀 Metadata guardada en 'osa_gnn_metadata.json'.")
    print(f"📊 Distribución de Prioridad:\n{df['Prioridad'].value_counts()}")
    
    return df

# Ejecución en tu notebook
# Asegúrate de que el archivo Reviewed_DB.xlsx esté en la misma carpeta
df_limpio = procesar_excel_osa_gnn('Reviewed_DB.xlsx')

if df_limpio is not None:
    # Mostrar las primeras filas para tu revisión en Aguascalientes
    print(df_limpio[['Uniprot_ID', 'Nombre', 'Prioridad', 'Longitud']].head())