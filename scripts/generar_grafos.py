import os
import json
import numpy as np
from Bio.PDB import PDBParser
from scipy.spatial import distance_matrix
import warnings
from Bio import BiopythonWarning

# Ignorar advertencias menores de formato de los PDBs de ESMFold
warnings.simplefilter('ignore', BiopythonWarning)

def procesar_pdb_a_grafo(ruta_pdb, umbral_angstroms=10.0):
    parser = PDBParser()
    estructura = parser.get_structure('PDB', ruta_pdb)
    
    coordenadas_ca = []
    
    for modelo in estructura:
        for cadena in modelo:
            for residuo in cadena:
                if residuo.id[0] == ' ': # Ignorar agua o ligandos
                    if 'CA' in residuo:
                        coordenadas_ca.append(residuo['CA'].get_coord())
                        
    if not coordenadas_ca:
        return None, None
        
    coords_array = np.array(coordenadas_ca)
    
    # Normalización (Mean Centering)
    centroide = np.mean(coords_array, axis=0)
    coords_normalizadas = coords_array - centroide
    
    # Matriz de Distancias y Adyacencia a 10 Å
    matriz_dist = distance_matrix(coords_normalizadas, coords_normalizadas)
    matriz_adyacencia = np.where((matriz_dist <= umbral_angstroms) & (matriz_dist > 0), 1, 0)
    
    # Formato Edge Index para PyTorch
    fuentes, destinos = np.nonzero(matriz_adyacencia)
    edge_index = np.vstack((fuentes, destinos))
    
    return coords_normalizadas, edge_index

def construir_dataset_grafos(carpeta_pdbs="estructuras_pdb_esmfold", output_json="osa_gnn_grafos.json"):
    print("==================================================")
    print("      Generador de Grafos Espaciales OSA-GNN      ")
    print("==================================================\n")
    
    archivos = [f for f in os.listdir(carpeta_pdbs) if f.endswith('.pdb')]
    print(f"⚙️ Procesando {len(archivos)} estructuras locales...\n")
    
    dataset_grafos = {}
    nodos_totales = 0
    aristas_totales = 0
    
    for i, archivo in enumerate(archivos, 1):
        uniprot_id = archivo.replace('.pdb', '')
        ruta_completa = os.path.join(carpeta_pdbs, archivo)
        
        try:
            coords, edge_index = procesar_pdb_a_grafo(ruta_completa)
            
            if coords is not None:
                num_nodos = len(coords)
                num_aristas = edge_index.shape[1]
                
                dataset_grafos[uniprot_id] = {
                    "num_nodos": num_nodos,
                    "num_aristas": num_aristas,
                    "coordenadas_nodos": coords.tolist(),
                    "edge_index": edge_index.tolist() 
                }
                
                nodos_totales += num_nodos
                aristas_totales += num_aristas
                print(f"[{i}/{len(archivos)}] ✅ {uniprot_id}: {num_nodos} nodos, {num_aristas} aristas.")
                
        except Exception as e:
            print(f"[{i}/{len(archivos)}] ❌ Error procesando {uniprot_id}: {e}")

    with open(output_json, 'w') as f:
        json.dump(dataset_grafos, f)

    print("\n==================================================")
    print("             Resumen Topológico                   ")
    print("==================================================")
    print(f"Proteínas procesadas   : {len(dataset_grafos)}")
    print(f"Total de Nodos (A.A.)  : {nodos_totales}")
    print(f"Total de Aristas       : {aristas_totales}")
    print("==================================================")

if __name__ == "__main__":
    construir_dataset_grafos()