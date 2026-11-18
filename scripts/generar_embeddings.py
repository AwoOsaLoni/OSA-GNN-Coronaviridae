import json
import torch
from transformers import AutoTokenizer, AutoModel
import os

def generar_features_esm2(json_metadata="osa_gnn_metadata.json", json_grafos="osa_gnn_grafos.json", output_final="dataset_pyg_completo.json"):
    print("==================================================")
    print("      Inyectando Inteligencia ESM-2 en OSA-GNN    ")
    print("==================================================\n")

    print("⏳ Cargando modelo ESM-2 (8M parámetros)...")
    modelo_nombre = "facebook/esm2_t6_8M_UR50D"
    tokenizer = AutoTokenizer.from_pretrained(modelo_nombre)
    modelo = AutoModel.from_pretrained(modelo_nombre)
    modelo.eval() 
    print("✅ Modelo cargado.\n")

    with open(json_metadata, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
        
    with open(json_grafos, 'r', encoding='utf-8') as f:
        grafos = json.load(f)

    meta_dict = {str(p["Uniprot_ID"]).strip(): p for p in metadata}
    dataset_final = {}
    exitos = 0

    print("🧬 Extrayendo Embeddings y validando dimensiones...\n")
    
    with torch.no_grad():
        for uniprot_id, grafo_data in grafos.items():
            if uniprot_id not in meta_dict:
                continue

            secuencia = meta_dict[uniprot_id]["Secuencia"]
            num_nodos_3d = grafo_data["num_nodos"]

            inputs = tokenizer(secuencia, return_tensors="pt", add_special_tokens=True)
            outputs = modelo(**inputs)
            
            # Extraer embeddings quitando los tokens especiales <cls> y <eos>
            embeddings = outputs.last_hidden_state[0, 1:-1, :] 

            # ¡La validación crucial de tu tesis!
            if embeddings.shape[0] != num_nodos_3d:
                print(f"⚠️ {uniprot_id}: Desajuste. Secuencia ({embeddings.shape[0]}) vs Nodos 3D ({num_nodos_3d}).")
                continue

            # Ensamblar el Grafo para PyTorch Geometric
            dataset_final[uniprot_id] = {
                "x": embeddings.tolist(), 
                "edge_index": grafo_data["edge_index"], 
                "y_labels": meta_dict[uniprot_id]["Funciones_GO"], 
                "prioridad": meta_dict[uniprot_id].get("Prioridad", "Desconocida") 
            }
            
            exitos += 1
            print(f"✅ {uniprot_id}: Grafo validado (Tensor X: {embeddings.shape[0]}x{embeddings.shape[1]})")

    with open(output_final, 'w') as f:
        json.dump(dataset_final, f)

    print("\n==================================================")
    print("             Dataset Final Ensamblado             ")
    print("==================================================")
    print(f"Grafos listos para PyTorch Geometric: {exitos}")
    print(f"Archivo generado: {output_final}")
    print("==================================================")

if __name__ == "__main__":
    generar_features_esm2()