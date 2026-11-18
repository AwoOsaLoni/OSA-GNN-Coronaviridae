import json
import torch
from torch_geometric.data import Data, Dataset
from torch_geometric.loader import DataLoader

class CoronaviridaeDataset(Dataset):
    def __init__(self, json_file, root='.', transform=None, pre_transform=None):
        self.json_file = json_file
        # Cargamos los datos en memoria al inicializar
        with open(self.json_file, 'r', encoding='utf-8') as f:
            self.datos_crudos = json.load(f)
            
        # Extraemos los IDs para poder iterar
        self.uniprot_ids = list(self.datos_crudos.keys())
        super().__init__(root, transform, pre_transform)

    def len(self):
        return len(self.uniprot_ids)

    def get(self, idx):
        uniprot_id = self.uniprot_ids[idx]
        grafo_dict = self.datos_crudos[uniprot_id]

        # 1. Matriz de características de los nodos (X) - Los embeddings de ESM-2
        x = torch.tensor(grafo_dict['x'], dtype=torch.float)

        # 2. Matriz de adyacencia (Edge Index) - La topología 3D
        edge_index = torch.tensor(grafo_dict['edge_index'], dtype=torch.long)

        # 3. Etiquetas (Y) - Las funciones moleculares GO
        y_labels = grafo_dict['y_labels']
        
        # 4. Máscaras para el entrenamiento
        # Como el dataset curado es 100% Swiss-Prot, afirmamos matemáticamente que 
        # todos los grafos son válidos para el entrenamiento.
        train_mask = torch.tensor([1], dtype=torch.bool)

        # Ensamblamos el objeto Data de PyTorch Geometric
        data = Data(x=x, edge_index=edge_index, y_raw=y_labels, train_mask=train_mask)
        data.uniprot_id = uniprot_id 

        return data

def probar_dataloader():
    print("==================================================")
    print("      Prueba del Cargador de Tensores PyG         ")
    print("==================================================\n")
    
    archivo_dataset = "dataset_pyg_completo.json"
    
    try:
        dataset = CoronaviridaeDataset(archivo_dataset)
        print(f"✅ Dataset cargado exitosamente con {len(dataset)} grafos virales.\n")
        
        # Inspeccionamos el primer grafo para verificar la integridad
        primer_grafo = dataset[0]
        print("Inspección topológica del primer tensor:")
        print(f" - ID Proteína: {primer_grafo.uniprot_id}")
        print(f" - Nodos (x)  : {primer_grafo.num_nodes} aminoácidos con {primer_grafo.num_node_features} dimensiones bioquímicas.")
        print(f" - Aristas    : {primer_grafo.num_edges} conexiones espaciales.")
        print(f" - Funciones  : {primer_grafo.y_raw}")
        print(f" - Revisado   : {'Sí (Uso para entrenamiento)' if primer_grafo.train_mask.item() else 'No (Uso para predicción)'}")
        
    except Exception as e:
        print(f"❌ Error al cargar los tensores: {e}")

if __name__ == "__main__":
    probar_dataloader()