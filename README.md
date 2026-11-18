🔬💻OSA-GNN: Optimized Spatial Attention - Graph Neural Network

Prototipo de investigación aplicada para la predicción de funciones moleculares (**GO:MF**) en proteínas de la familia **Coronaviridae** mediante Redes Neuronales de Grafos con Atención Anisotrópica (**GAT**), embeddings evolutivos (**ESM-2**), estructuras 3D predichas con **AlphaFold2** y Aprendizaje Semi-Supervisado (**SSL**).

## Estructura del Proyecto
scripts/pdb_processor.py & generar_grafos.py: Construcción de matrices de adyacencia espacial (umbral de contacto de 10 Å entre carbonos alfa).

scripts/generar_embeddings.py: Extracción de representaciones bioquímicas de 320 dimensiones usando ESM-2.

scripts/dataset_loader.py: Serialización hacia objetos Data de PyTorch Geometric.

scripts/modelo_gnn.py & entrenamiento.py: Arquitectura OSA-GNN (3 capas GATConv + global_mean_pool) y ciclo iterativo de pseudo-etiquetado.

scripts/comparativa_metodologica.py: Estudio de ablación **in silico** con validación cruzada de 5 pliegues (5-Fold CV).

resultados_colabfold/: Salidas de métricas estructurales (pLDDT, PAE) generadas con ColabFold v1.6.2.

## Reproducibilidad con Docker

1. **Construir la imagen del contenedor:**
   docker build -t osa-gnn-app .

2. **Ejecutar el pipeline de entrenamiento y ablación:**
   docker run --rm -v $(pwd):/app osa-gnn-app python scripts/comparativa_metodologica.py


**Autor:**
Ing. Silvio Rainel Garcia Rondón

Maestría en Informática y Tecnologías Computacionales

Universidad Autónoma de Aguascalientes (UAA).
