# import torch
#import torch.nn.functional as F
#from torch_geometric.nn import GCNConv, GATConv, global_mean_pool
#from torch.nn import Linear

# ==========================================
# MODELO 1: LÍNEA BASE (GCN - Convolución)
# ==========================================
#class RedOSA_GCN(torch.nn.Module):
    #def __init__(self, num_features_entrada=320, canales_ocultos=64, num_clases_salida=10):
        #super(RedOSA_GCN, self).__init__()
        #torch.manual_seed(12345)
        
        #self.conv1 = GCNConv(num_features_entrada, canales_ocultos)
        #self.conv2 = GCNConv(canales_ocultos, canales_ocultos)
        #self.conv3 = GCNConv(canales_ocultos, canales_ocultos)
        
        #self.clasificador = Linear(canales_ocultos, num_clases_salida)

    #def forward(self, x, edge_index, batch):
        #x = self.conv1(x, edge_index).relu()
        #x = self.conv2(x, edge_index).relu()
        #x = self.conv3(x, edge_index)
        
        #vector_proteina = global_mean_pool(x, batch)  
        #vector_proteina = F.dropout(vector_proteina, p=0.5, training=self.training)
        #return self.clasificador(vector_proteina)

# ==========================================
# MODELO 2: AVANZADO (GAT - Atención)
# ==========================================
#class RedOSA_GAT(torch.nn.Module):
    #def __init__(self, num_features_entrada=320, canales_ocultos=64, num_clases_salida=10, cabezas=4):
        #super(RedOSA_GAT, self).__init__()
        #torch.manual_seed(12345)
        
        # Capa 1: Multi-Head Attention (Concatena las cabezas)
        #self.conv1 = GATConv(num_features_entrada, canales_ocultos, heads=cabezas, concat=True)
        
        # Capa 2: La entrada ahora es canales_ocultos * cabezas
        #self.conv2 = GATConv(canales_ocultos * cabezas, canales_ocultos, heads=cabezas, concat=True)
        
        # Capa 3: Última capa de grafos. Usamos concat=False para promediar las cabezas y volver al tamaño normal
        #self.conv3 = GATConv(canales_ocultos * cabezas, canales_ocultos, heads=1, concat=False)
        
        #self.clasificador = Linear(canales_ocultos, num_clases_salida)

    #def forward(self, x, edge_index, batch):
        # En GAT se estila usar ELU (Exponential Linear Unit) en lugar de ReLU
        #x = F.elu(self.conv1(x, edge_index))
        #x = F.elu(self.conv2(x, edge_index))
        #x = self.conv3(x, edge_index)
        
        #vector_proteina = global_mean_pool(x, batch)  
        #vector_proteina = F.dropout(vector_proteina, p=0.5, training=self.training)
        #return self.clasificador(vector_proteina)
    

import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GATConv, global_mean_pool
from torch.nn import Linear

# 1. PIONERO DE SECUENCIA (Filosofía DeepGOPlus)
# Ignora la estructura 3D. Solo usa los embeddings de ESM-2.
class Red_Solo_Secuencia(torch.nn.Module):
    def __init__(self, num_features_entrada=320, canales_ocultos=64, num_clases_salida=10):
        super(Red_Solo_Secuencia, self).__init__()
        self.lin1 = Linear(num_features_entrada, canales_ocultos)
        self.lin2 = Linear(canales_ocultos, canales_ocultos)
        self.clasificador = Linear(canales_ocultos, num_clases_salida)

    def forward(self, x, edge_index, batch):
        # Ignoramos edge_index por completo (sin comunicación entre nodos)
        x = self.lin1(x).relu()
        x = self.lin2(x).relu()
        vector_proteina = global_mean_pool(x, batch)
        return self.clasificador(vector_proteina)

# 2. PIONERO DE ESTRUCTURA (Filosofía DeepFRI)
# Usa grafos (GCN) pero con información bioquímica básica (sin ESM-2)
# Nota: Para esta prueba usaremos una reducción de ESM para simular datos básicos
class Red_Solo_Estructura(torch.nn.Module):
    def __init__(self, num_features_entrada=320, canales_ocultos=64, num_clases_salida=10):
        super(Red_Solo_Estructura, self).__init__()
        self.conv1 = GCNConv(num_features_entrada, canales_ocultos)
        self.conv2 = GCNConv(canales_ocultos, canales_ocultos)
        self.clasificador = Linear(canales_ocultos, num_clases_salida)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index).relu()
        vector_proteina = global_mean_pool(x, batch)
        return self.clasificador(vector_proteina)

# 3. PIONERO HÍBRIDO (Filosofía GCN-PFP / HNetGO)
# Combina Grafos (GCN) + ESM-2 en un entrenamiento supervisado estándar
class Red_Hibrida_GCN(torch.nn.Module):
    def __init__(self, num_features_entrada=320, canales_ocultos=64, num_clases_salida=10):
        super(Red_Hibrida_GCN, self).__init__()
        self.conv1 = GCNConv(num_features_entrada, canales_ocultos)
        self.conv2 = GCNConv(canales_ocultos, canales_ocultos)
        self.conv3 = GCNConv(canales_ocultos, canales_ocultos)
        self.clasificador = Linear(canales_ocultos, num_clases_salida)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index).relu()
        x = self.conv3(x, edge_index).relu()
        vector_proteina = global_mean_pool(x, batch)
        return self.clasificador(vector_proteina)

# 4. PROPUESTA OSA-GNN (Tu modelo estrella)
# Usa Atención Multi-Cabeza (GAT) + ESM-2
class OSA_GNN_GAT(torch.nn.Module):
    def __init__(self, num_features_entrada=320, canales_ocultos=64, num_clases_salida=10, cabezas=4):
        super(OSA_GNN_GAT, self).__init__()
        self.conv1 = GATConv(num_features_entrada, canales_ocultos, heads=cabezas, concat=True)
        self.conv2 = GATConv(canales_ocultos * cabezas, canales_ocultos, heads=1, concat=False)
        self.clasificador = Linear(canales_ocultos, num_clases_salida)

    def forward(self, x, edge_index, batch):
        x = F.elu(self.conv1(x, edge_index))
        x = self.conv2(x, edge_index)
        vector_proteina = global_mean_pool(x, batch)
        vector_proteina = F.dropout(vector_proteina, p=0.5, training=self.training)
        return self.clasificador(vector_proteina)