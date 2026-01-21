# Explicación Técnica de las Implementaciones

Este documento detalla la lógica y el funcionamiento de las nuevas características implementadas en tu proyecto de predicción de neuro-conocimiento.

## 1. Validación "Time-Travel" (`src/time_travel_experiment.ipynb`)

El objetivo de este experimento es simular el paso del tiempo para verificar si el modelo puede "predecir el futuro" del conocimiento médico.

### 🧠 Lógica del Experimento

El concepto central se basa en dividir tus documentos por año de publicación.

1.  **Corte Temporal Dinámico**:
    - Si estamos simulando el año **2015**, el modelo solo tiene acceso a papers publicados en 2015 o antes.
    - Todo lo publicado de 2016 en adelante se considera "futuro desconocido".

2.  **Construcción del Grafo ($G_{past}$)**:
    - Construimos un grafo donde los nodos son conceptos médicos y las aristas son relaciones extraídas de los textos "pasados".

3.  **Entrenamiento GCN (Graph Convolutional Network)**:
    - Usamos una red neuronal que aprende la topología del grafo.
    - El modelo aprende que si A se conecta con B, y B con C, es probable que A se conecte con C (transitividad).
    - **Función de Pérdida**: Usamos `FocalLoss` para manejar el desbalance de clases (hay muchas más "no-conexiones" que conexiones reales).

4.  **Predicción y Validación**:
    - El modelo predice nuevas aristas para $G_{past}$.
    - **Validación**: Verificamos si esas aristas predichas aparecen explícitamente en los documentos del "futuro".
    - Si el modelo predice `Fármaco-X -> Enfermedad-Y` en 2015, y en 2018 sale un paper validando esa relación, ¡es un acierto!

5.  **Análisis Robusto (Nuevo)**:
    - Dado que las redes neuronales inician con pesos aleatorios, una sola corrida no es confiable.
    - Implementamos un bucle que repite el entrenamiento **30 veces por año**.
    - Esto nos permite calcular la media y desviación estándar ($\mu \pm \sigma$), dando validez científica a los resultados.

---

## 2. Análisis Estadístico (`src/statistics.py`)

No basta con decir "el modelo tiene 85% de precisión". Debemos probar que esto no es suerte.

### 🎲 Valor P (P-value)

- **Hipótesis Nula ($H_0$)**: El modelo acierta por pura suerte (azar).
- **Permutaciones**: Generamos predicciones aleatorias simuladas y comparamos su rendimiento contra tu modelo.
- Si tu modelo supera al azar el 99% de las veces, el **P-value es < 0.01**, lo que confirma que el aprendizaje es real y significativo.

---

## 3. AutoML y Optimización (`src/Project.ipynb` y `src/automl.py`)

En el grafo principal (Knowledge Graph Embedding - KGE), no sabemos a priori qué modelo geométrico representa mejor los datos.

### 🤖 AutoML (Automated Machine Learning)

En lugar de adivinar, usamos un algoritmo de búsqueda:

1.  **Espacio de Búsqueda**: Definimos un rango de opciones:
    - **Modelos**: `TransE` (traslación vector), `RotatE` (rotación espacio complejo), `DistMult`, etc.
    - **Dimensiones**: ¿Vectores de tamaño 64, 128, o 256?
    - **Learning Rate**: ¿Qué tan rápido debe aprender la red?

2.  **Pipeline de PyKEEN**:
    - Usamos `pykeen.hpo` (Hyperparameter Optimization).
    - El sistema prueba combinaciones automáticamente (ej. `TransE` con dim=128, luego `RotatE` con dim=64).
    - Evalúa cada combinación usando métricas como MRR (Mean Reciprocal Rank).

3.  **Selección**:
    - Al final, el sistema te devuelve "El mejor modelo es `RotatE` con `dim=128`".
    - Usamos esta configuración óptima para hacer las predicciones finales en `src/ExtendedGraph`.

---

## Resumen de Flujo de Trabajo

| Componente            | Qué hace                                                          | Dónde vive                     |
| :-------------------- | :---------------------------------------------------------------- | :----------------------------- |
| **GCN (Time-Travel)** | Predice enlaces basándose en topología y valida contra el futuro. | `time_travel_experiment.ipynb` |
| **Robust Loop**       | Repite experimentos para calcular estabilidad y error.            | `time_travel_experiment.ipynb` |
| **P-Value**           | Calcula la probabilidad de que el acierto sea suerte.             | `src/statistics.py`            |
| **AutoML**            | Busca la mejor arquitectura de modelo KGE automáticamente.        | `src/automl.py`                |
| **KGE (Project)**     | Modelo semántico final usando la mejor arquitectura encontrada.   | `src/Project.ipynb`            |
