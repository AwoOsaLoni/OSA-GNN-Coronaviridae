import torch
import torch.nn as nn
from torch.optim import Adam
from torch_geometric.loader import DataLoader
from sklearn.metrics import accuracy_score, f1_score, average_precision_score
import warnings

from dataset_loader import CoronaviridaeDataset
from modelo_gnn import RedOSA_GAT

# Ignorar advertencias de scikit-learn cuando hay etiquetas raras con 0 predicciones
warnings.filterwarnings('ignore')

def preparar_etiquetas_multi_hot(dataset):
    todos_los_go = set()
    for data in dataset:
        for go_term in data.y_raw:
            todos_los_go.add(go_term)
    return {go: i for i, go in enumerate(sorted(list(todos_los_go)))}

def codificar_lote(y_raw_list, vocabulario_go):
    batch_size = len(y_raw_list)
    num_clases = len(vocabulario_go)
    tensor_y = torch.zeros((batch_size, num_clases), dtype=torch.float)
    for i, go_terms in enumerate(y_raw_list):
        for go in go_terms:
            if go in vocabulario_go:
                tensor_y[i, vocabulario_go[go]] = 1.0
    return tensor_y

def calcular_metricas_multietiqueta(predicciones_prob, etiquetas_reales, umbral=0.5):
    """
    Calcula Exactitud, F1-Score (Micro/Macro) y AUPR (Micro/Macro).
    """
    # Predicciones binarias para Accuracy y F1-Score
    predicciones_binarias = (predicciones_prob > umbral).float().numpy()
    etiquetas_binarias = etiquetas_reales.numpy()
    
    # Probabilidades puras para AUPR
    probs = predicciones_prob.numpy()

    # Métricas de Umbral Fijo
    acc = accuracy_score(etiquetas_binarias, predicciones_binarias)
    f1_micro = f1_score(etiquetas_binarias, predicciones_binarias, average='micro')
    f1_macro = f1_score(etiquetas_binarias, predicciones_binarias, average='macro')
    
    # Métricas Independientes del Umbral (AUPR / Average Precision)
    # Protegemos el cálculo en caso de lotes pequeños sin ejemplos positivos
    try:
        aupr_micro = average_precision_score(etiquetas_binarias, probs, average='micro')
        aupr_macro = average_precision_score(etiquetas_binarias, probs, average='macro')
    except Exception:
        aupr_micro, aupr_macro = 0.0, 0.0
    
    return acc, f1_micro, f1_macro, aupr_micro, aupr_macro

def entrenar_semi_supervisado():
    print("=======================================================")
    print(" Entrenamiento OSA-GNN | Evaluación Clínica (F1 + AUPR) ")
    print("=======================================================\n")

    dataset = CoronaviridaeDataset("dataset_pyg_completo.json")
    loader = DataLoader(dataset, batch_size=8, shuffle=True)
    
    vocabulario_go = preparar_etiquetas_multi_hot(dataset)
    num_clases = len(vocabulario_go)
    print(f"📊 Vocabulario Funcional: {num_clases} términos GO únicos detectados.\n")
    
    #modelo = RedOSA_GNN(num_features_entrada=320, canales_ocultos=64, num_clases_salida=num_clases)
    modelo = RedOSA_GAT(num_features_entrada=320, canales_ocultos=64, num_clases_salida=num_clases, cabezas=4)
    criterio = nn.BCEWithLogitsLoss() 
    optimizador = Adam(modelo.parameters(), lr=0.005)

    epocas = 15
    umbral_confianza = 0.85
    
    # SIMULACIÓN SEMI-SUPERVISADA
    for i, data in enumerate(dataset.datos_crudos.values()):
        data['es_swiss_prot'] = True if i % 2 == 0 else False

    for epoca in range(1, epocas + 1):
        modelo.train()
        perdida_acumulada = 0
        nuevas_pseudo_etiquetas = 0
        
        # Recolectores de datos para las métricas globales de la época
        todas_predicciones = []
        todas_etiquetas = []
        
        for lote in loader:
            optimizador.zero_grad()
            
            # Pase hacia adelante
            predicciones_crudas = modelo(lote.x, lote.edge_index, lote.batch)
            probabilidades = torch.sigmoid(predicciones_crudas)
            etiquetas_reales = codificar_lote(lote.y_raw, vocabulario_go)
            
            # Máscara dinámica (Swiss-Prot original + Pseudo-etiquetadas previamente)
            mascara_entrenamiento = []
            for id_prot in lote.uniprot_id:
                es_maestra = dataset.datos_crudos[id_prot].get('es_swiss_prot', False)
                es_pseudo = dataset.datos_crudos[id_prot].get('es_pseudo_etiquetada', False)
                mascara_entrenamiento.append(es_maestra or es_pseudo)
                
            mascara_tensor = torch.tensor(mascara_entrenamiento, dtype=torch.bool)
            
            # Entrenamiento y cálculo de error (Loss)
            if mascara_tensor.sum() > 0:
                pred_validas = predicciones_crudas[mascara_tensor]
                etiq_validas = etiquetas_reales[mascara_tensor]
                
                perdida = criterio(pred_validas, etiq_validas)
                perdida.backward()
                optimizador.step()
                
                perdida_acumulada += perdida.item() * mascara_tensor.sum().item()
                
                # Guardar tensores para evaluar scikit-learn
                todas_predicciones.append(probabilidades[mascara_tensor].detach())
                todas_etiquetas.append(etiq_validas.detach())

            # Pseudo-Etiquetado (Propagación hacia TrEMBL)
            mascara_inversa = ~mascara_tensor
            if mascara_inversa.sum() > 0:
                prob_trembl = probabilidades[mascara_inversa]
                ids_trembl = [id_prot for idx, id_prot in enumerate(lote.uniprot_id) if mascara_inversa[idx]]
                
                for idx, probs_nodo in enumerate(prob_trembl):
                    # Si al menos una función biológica supera el 85% de seguridad
                    if torch.any(probs_nodo > umbral_confianza):
                        dataset.datos_crudos[ids_trembl[idx]]['es_pseudo_etiquetada'] = True
                        nuevas_pseudo_etiquetas += 1

        # ---- CÁLCULO DE MÉTRICAS AL FINAL DE LA ÉPOCA ----
        if len(todas_predicciones) > 0:
            tensor_pred_total = torch.cat(todas_predicciones, dim=0)
            tensor_etiq_total = torch.cat(todas_etiquetas, dim=0)
            
            grafos_entrenados = tensor_etiq_total.shape[0]
            perdida_media = perdida_acumulada / max(1, grafos_entrenados)
            
            acc, f1_micro, f1_macro, aupr_micro, aupr_macro = calcular_metricas_multietiqueta(tensor_pred_total, tensor_etiq_total)
            
            # Impresión de la radiografía clínica
            print(f"Época {epoca:03d} | TrEMBLs Propagados: {nuevas_pseudo_etiquetas:02d}")
            print(f"   -> Loss: {perdida_media:.4f} | Acc: {acc:.4f}")
            print(f"   -> F1   (Micro/Macro): {f1_micro:.4f} / {f1_macro:.4f}")
            print(f"   -> AUPR (Micro/Macro): {aupr_micro:.4f} / {aupr_macro:.4f}\n")
        else:
            print(f"Época {epoca:03d} | Sin datos para evaluar.")

if __name__ == "__main__":
    entrenar_semi_supervisado()