import torch
import torch.nn as nn
import numpy as np
import re
import warnings
from torch.utils.data import Subset
from torch_geometric.loader import DataLoader
from sklearn.model_selection import KFold
from sklearn.metrics import f1_score, average_precision_score

from dataset_loader import CoronaviridaeDataset
from modelo_gnn import Red_Solo_Secuencia, Red_Solo_Estructura, Red_Hibrida_GCN, OSA_GNN_GAT

warnings.filterwarnings('ignore')

K_FOLDS = 5
EPOCAS = 15
BATCH_SIZE = 8
LR = 0.005
UMBRAL_PSEUDO = 0.85

def extraer_terminos_go(y_raw_input):
    if isinstance(y_raw_input, (list, tuple, set)):
        texto = " ".join([str(item) for item in y_raw_input])
    else:
        texto = str(y_raw_input)
    encontrados = re.findall(r'GO:\d+', texto)
    return list(set(encontrados))

def encontrar_top_go(dataset):
    conteo = {}
    for data in dataset:
        gos = extraer_terminos_go(data.y_raw)
        for go in gos:
            conteo[go] = conteo.get(go, 0) + 1
    # Ordenar por mayor cantidad de muestras
    ordenados = sorted(conteo.items(), key=lambda x: x[1], reverse=True)
    return ordenados

def preparar_vocabulario(dataset):
    todos_los_go = set()
    for data in dataset:
        go_limpios = extraer_terminos_go(data.y_raw)
        for go in go_limpios:
            todos_los_go.add(go)
    return {go: i for i, go in enumerate(sorted(list(todos_los_go)))}

def codificar_lote(y_raw_list, vocabulario_go):
    tensor_y = torch.zeros((len(y_raw_list), len(vocabulario_go)), dtype=torch.float)
    for i, y_item in enumerate(y_raw_list):
        go_terms = extraer_terminos_go(y_item)
        for go in go_terms:
            if go in vocabulario_go:
                tensor_y[i, vocabulario_go[go]] = 1.0
    return tensor_y

def calcular_metricas(predicciones_prob, etiquetas_reales, vocabulario, funciones_top, umbral=0.5):
    pred_binarias = (predicciones_prob > umbral).float().numpy()
    etiq_binarias = etiquetas_reales.numpy()
    probs = predicciones_prob.numpy()

    # 1. Métricas Macro Globales
    f1_macro = f1_score(etiq_binarias, pred_binarias, average='macro', zero_division=0)
    try:
        aupr_macro = average_precision_score(etiq_binarias, probs, average='macro')
    except:
        aupr_macro = 0.0
        
    # 2. Extracción para las Funciones Dinámicas Top
    especificos = {f: {'F1': 0.0, 'AUPR': 0.0} for f in funciones_top}
    
    for target in funciones_top:
        idx = vocabulario[target]
        y_true_col = etiq_binarias[:, idx]
        y_pred_col = pred_binarias[:, idx]
        y_prob_col = probs[:, idx]
        
        f1_c = f1_score(y_true_col, y_pred_col, zero_division=0)
        
        if np.sum(y_true_col) > 0:
            try:
                aupr_c = average_precision_score(y_true_col, y_prob_col)
            except:
                aupr_c = 0.0
        else:
            aupr_c = f1_c
            
        especificos[target] = {'F1': f1_c, 'AUPR': aupr_c}
            
    return f1_macro, aupr_macro, especificos

def ejecutar_benchmark():
    print("\n" + "="*65)
    print(" ESTUDIO DE ABLACIÓN: COMPARATIVA METODOLÓGICA (5-FOLD CV)")
    print("="*65 + "\n")

    dataset = CoronaviridaeDataset("dataset_pyg_completo.json")
    vocabulario = preparar_vocabulario(dataset)
    num_clases = len(vocabulario)
    
    # Encontrar las 2 funciones con más datos
    top_gos_list = encontrar_top_go(dataset)
    top_2_keys = [top_gos_list[0][0], top_gos_list[1][0]] if len(top_gos_list) >= 2 else [k[0] for k in top_gos_list]

    print(f"-> Vocabulario GO procesado: {num_clases} términos encontrados.")
    print("-> Funciones seleccionadas para evaluación específica (Mayor densidad de muestras):")
    print(f"   1. {top_gos_list[0][0]} (Presente en {top_gos_list[0][1]} proteínas)")
    print(f"   2. {top_gos_list[1][0]} (Presente en {top_gos_list[1][1]} proteínas)\n")

    for i, data in enumerate(dataset.datos_crudos.values()):
        data['es_swiss_prot'] = True if i % 2 == 0 else False
        data['es_pseudo_etiquetada'] = False 

    modelos_a_probar = [
        ("DeepGOPlus (Secuencia)", Red_Solo_Secuencia, False),
        ("DeepFRI    (Estructura)", Red_Solo_Estructura, False),
        ("GCN-PFP    (Híbrido)", Red_Hibrida_GCN, False),
        ("OSA-GNN    (Propuesta)", OSA_GNN_GAT, True)
    ]

    resultados_globales = {}
    indices = np.arange(len(dataset))
    kf = KFold(n_splits=K_FOLDS, shuffle=True, random_state=42)

    for nombre_modelo, ClaseModelo, usa_semi_supervisado in modelos_a_probar:
        print(f"Entrenando y evaluando: {nombre_modelo} ...")
        f1_pliegues = []
        aupr_pliegues = []
        spec_pliegues = {k: {'F1': [], 'AUPR': []} for k in top_2_keys}

        for fold, (train_idx, test_idx) in enumerate(kf.split(indices)):
            train_loader = DataLoader(Subset(dataset, train_idx), batch_size=BATCH_SIZE, shuffle=True)
            test_loader = DataLoader(Subset(dataset, test_idx), batch_size=BATCH_SIZE, shuffle=False)

            if ClaseModelo == OSA_GNN_GAT:
                modelo = ClaseModelo(num_features_entrada=320, canales_ocultos=64, num_clases_salida=num_clases, cabezas=4)
            else:
                modelo = ClaseModelo(num_features_entrada=320, canales_ocultos=64, num_clases_salida=num_clases)

            optimizador = torch.optim.Adam(modelo.parameters(), lr=LR)
            criterio = nn.BCEWithLogitsLoss()

            for epoca in range(EPOCAS):
                modelo.train()
                for lote in train_loader:
                    optimizador.zero_grad()
                    predicciones = modelo(lote.x, lote.edge_index, lote.batch)
                    probabilidades = torch.sigmoid(predicciones)
                    etiquetas_reales = codificar_lote(lote.y_raw, vocabulario)

                    mascara_train = []
                    for id_prot in lote.uniprot_id:
                        es_maestra = dataset.datos_crudos[id_prot].get('es_swiss_prot', False)
                        es_pseudo = dataset.datos_crudos[id_prot].get('es_pseudo_etiquetada', False)
                        
                        if usa_semi_supervisado:
                            mascara_train.append(es_maestra or es_pseudo)
                        else:
                            mascara_train.append(es_maestra)
                            
                    mascara_tensor = torch.tensor(mascara_train, dtype=torch.bool)

                    if mascara_tensor.sum() > 0:
                        perdida = criterio(predicciones[mascara_tensor], etiquetas_reales[mascara_tensor])
                        perdida.backward()
                        optimizador.step()

                    if usa_semi_supervisado:
                        mascara_inversa = ~mascara_tensor
                        if mascara_inversa.sum() > 0:
                            prob_trembl = probabilidades[mascara_inversa]
                            ids_trembl = [id_prot for idx, id_prot in enumerate(lote.uniprot_id) if mascara_inversa[idx]]
                            for idx, probs_nodo in enumerate(prob_trembl):
                                if torch.any(probs_nodo > UMBRAL_PSEUDO):
                                    dataset.datos_crudos[ids_trembl[idx]]['es_pseudo_etiquetada'] = True

            modelo.eval()
            todas_predicciones = []
            todas_etiquetas = []
            
            with torch.no_grad():
                for lote in test_loader:
                    predicciones = modelo(lote.x, lote.edge_index, lote.batch)
                    todas_predicciones.append(torch.sigmoid(predicciones))
                    todas_etiquetas.append(codificar_lote(lote.y_raw, vocabulario))
            
            if len(todas_predicciones) > 0:
                tensor_pred = torch.cat(todas_predicciones, dim=0)
                tensor_etiq = torch.cat(todas_etiquetas, dim=0)
                f1_mac, aupr_mac, spec = calcular_metricas(tensor_pred, tensor_etiq, vocabulario, top_2_keys)
                
                f1_pliegues.append(f1_mac)
                aupr_pliegues.append(aupr_mac)
                for t in top_2_keys:
                    spec_pliegues[t]['F1'].append(spec[t]['F1'])
                    spec_pliegues[t]['AUPR'].append(spec[t]['AUPR'])

        resultados_globales[nombre_modelo] = {
            "F1-Macro": np.mean(f1_pliegues),
            "AUPR-Macro": np.mean(aupr_pliegues),
            "Func_1_F1": np.mean(spec_pliegues[top_2_keys[0]]['F1']),
            "Func_1_AUPR": np.mean(spec_pliegues[top_2_keys[0]]['AUPR']),
            "Func_2_F1": np.mean(spec_pliegues[top_2_keys[1]]['F1']),
            "Func_2_AUPR": np.mean(spec_pliegues[top_2_keys[1]]['AUPR'])
        }
        print(f"  ✓ Completado.\n")

    print("="*75)
    print("  RESUMEN FINAL DE MÉTRICAS GLOBALES Y ESPECÍFICAS (5-FOLD) ")
    print("="*75)
    
    for nombre, metricas in resultados_globales.items():
        print(f"\n[{nombre}]")
        print(f"  ▶ Global   -> F1-Macro: {metricas['F1-Macro']:.4f} | AUPR-Macro: {metricas['AUPR-Macro']:.4f}")
        print(f"  ▶ {top_2_keys[0]} -> F1:       {metricas['Func_1_F1']:.4f} | AUPR:       {metricas['Func_1_AUPR']:.4f}")
        print(f"  ▶ {top_2_keys[1]} -> F1:       {metricas['Func_2_F1']:.4f} | AUPR:       {metricas['Func_2_AUPR']:.4f}")
        print("-" * 75)

if __name__ == "__main__":
    ejecutar_benchmark()