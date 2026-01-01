# Metodología de Validación del Grafo de Conocimiento

Este documento explica la justificación, las herramientas y las ontologías seleccionadas para validar el grafo de Neuro-Knowledge Prediction.

## 1. Enfoque de Validación: Comparación con "Estándar de Oro"

Validamos el Grafo de Conocimiento (KG) extraído comparándolo con ontologías establecidas como "Estándar de Oro" (Gold Standard).

-   **¿Por qué?** Nuestro KG se extrae automáticamente del texto, lo que introduce ruido. Las ontologías son curadas manualmente por expertos.
-   **Método**: Utilizamos **Verificación de Inclusión de Términos**.
    -   Si un nodo extraído (ej. "Hippocampus") existe en la ontología, lo consideramos una **Entidad Válida**.
    -   Si no existe (y no tiene fuzzy match), es probablemente una alucinación, un error ortográfico o un término no estándar.

## 2. Ontologías Seleccionadas

Realizamos pruebas comparativas (benchmarking) contra cuatro ontologías distintas para capturar diferentes aspectos de los datos:

### A. NIFSTD (Neuroscience Information Framework Standard)
-   **Dominio**: Neurociencia Especializada.
-   **¿Por qué se eligió?** Es el estándar de facto para recursos amplios de neurociencia. Cubre regiones cerebrales, neuronas y moléculas.
-   **Expectativa**: Alta precisión para términos específicos de neurociencia.

### B. FMA (Foundational Model of Anatomy)
-   **Dominio**: Anatomía Humana.
-   **¿Por qué se eligió?** Proporciona la jerarquía estructural del cuerpo más estrictamente definida.
-   **Expectativa**: Valida términos anatómicos más amplios (ej. "Cortex", "Lobe") pero podría omitir detalles moleculares.

### C. CNO (Computational Neuroscience Ontology)
-   **Dominio**: Modelos computacionales y simulaciones.
-   **¿Por qué se eligió?** Si los artículos de entrada discuten simulaciones, redes o algoritmos, las bio-ontologías estándar los omitirán. CNO llena este vacío.

### D. HPO (Human Phenotype Ontology)
-   **Dominio**: Enfermedades y anomalías fenotípicas.
-   **¿Por qué se eligió?** Los artículos clínicos a menudo mencionan enfermedades ("Epilepsy", "Tumor"). HPO valida estos términos clínicos.

## 3. El Pipeline de Validación

1.  **Cargador (Loader)**: Usamos `owlready2` para analizar los archivos OWL.
2.  **Comparador (Matcher)**: Usamos coincidencia exacta de cadenas + fuzzy match (`difflib`) para manejar ligeras variaciones ortográficas.
3.  **Puntuación (Scoring)**:
    -   **Precisión** = $\frac{\text{Nodos Válidos}}{\text{Nodos Totales}}$
    -   Una mayor precisión con **NIFSTD** indica que el grafo se centra con éxito en la neurociencia.
    -   Una alta precisión con **HPO** implica que el grafo es fuertemente clínico.

## 4. Herramientas Utilizadas
-   **Python**: Lógica central.
-   **NetworkX**: Manipulación de grafos.
-   **Owlready2**: Análisis eficiente de ontologías (más rápido que `rdflib` para archivos grandes).
