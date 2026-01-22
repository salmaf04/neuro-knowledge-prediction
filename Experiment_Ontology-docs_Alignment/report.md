Informe de Evaluación de Alineamiento Semántico

Proyecto: Link Prediction en Grafos Híbridos

Fecha: 2026
Resumen

Este documento detalla los experimentos realizados para medir el Document-in-Ontology Recall (Rdo​) mediante el alineamiento semántico de entidades extraídas de un corpus de neurociencia frente a la ontología de referencia NIFSTD. Se analizan diversas configuraciones de umbrales y modelos de representación.
1. Definición de la Ontología de Referencia

Para este experimento se utiliza la ontología NIFSTD (Neuroscience Information Framework Standard Ontology).

    Fuente: NIFSTD.csv.gz

    Volumen: ~180,000 clases técnicas

    Campos Utilizados: Preferred Label, Synonyms y Definitions

    Representación: Enriquecimiento de texto mediante concatenación de etiquetas y definiciones para generación de embeddings biomédicos optimizados con SapBERT.

2. Configuración del Experimento

En esta sección se definen los parámetros constantes y las variables de control.

    Modelo de Embedding: SapBERT-from-PubMedBERT-fulltext

    Motor de Búsqueda: FAISS (IndexFlatIP)

    Métrica Core:
    Rdo​=∣Etotal​∣∣Emapped​∣​

    Donde una entidad e se considera mapeada si max(simcos​(e,O))≥θ.

3. Resultados por Corrida (Iteraciones)
3.1 Corrida #1: Análisis de Diversidad Documental

Selección del Corpus: La corrida inicial se realizó sobre un corpus piloto de diez (n=10) documentos seleccionados bajo criterios de heterogeneidad editorial y cronológica. La muestra integra monografías, artículos científicos, guías clínicas y tesis doctorales publicados en la última década.

Parámetros: * θ=0.85

    Documentos: 10 PDFs

    Modelo: SapBERT

Figura 1(dentro del directorio Corrida#1): Distribución de la similitud semántica (score). La línea indica el umbral θ=0.85.

Resumen de Métricas:

    Total de términos únicos analizados: 1,419

    Términos Mapeados (score≥0.85): 90

    Términos Residuales: 1,329

    Recall del Documento en la Ontología (Rdo​): 0.0634

Análisis de la Frontera de Decisión: Se identificaron 589 términos en el rango crítico [0.70,0.85). A continuación se muestran ejemplos representativos:
Entidad extraída (NER)	Concepto NIFSTD Sugerido	Score
neurologica	Nervous system	0.8500
contaminacion	increased contamination	0.8491
neoplasia	Cancer	0.8475
glandula	gland	0.8475
aureus	Staphylococcus aureus subsp. aureus COL	0.8470

Interpretación de Resultados: El bajo valor de Rdo​ (6.34%) indica una discrepancia significativa entre el vocabulario técnico de los documentos y las etiquetas preferidas de NIFSTD. No obstante, la calidad de los matches en la frontera sugiere que una flexibilización del umbral podría incrementar la cobertura.


3.2 Corrida #2: Escalabilidad y Flexibilización del Umbral

Selección del Corpus: Selección aleatoria del 50% de la base de datos total aproximadamente. Esta metodología busca evaluar la consistencia de la extracción de entidades y el desempeño del alineamiento en un volumen significativamente mayor de datos.

Parámetros:

    θ: 0.75

    Volumen: ~50% del dataset total

    Modelo: SapBERT

Figura 2(dentro del directorio Corrida#2): Distribución de la similitud semántica (score). La línea indica el umbral θ=0.75.

Resumen de Métricas:

    Total de términos únicos analizados: 7,310

    Términos Mapeados (score≥0.75): 1,836

    Términos Residuales: 5,474

    Recall del Documento en la Ontología (Rdo​): 0.2512

Análisis de la Frontera de Decisión: Con la flexibilización del umbral a 0.75, se identificaron 3,505 términos en el rango crítico [0.65,0.75). A continuación, se listan ejemplos representativos de los nuevos alineamientos obtenidos:
Entidad extraída (NER)	Concepto NIFSTD Sugerido	Score
superior petroclivalclival	petrosal bone	0.7500
caracteristicas	Carica	0.7499
otro tumor	olfactory neural tumor	0.7499
el abor	miscarriage	0.7499
otro tumor	olfactory neural tumor	0.7499

Principales Términos Residuales (Top 10): mas tenso, iz quierdo, elevacion de, ubicacion, hominivorax, apetito, sobrecarga, clínicas, aguda, mucopolisacarido.

Interpretación de Resultados: El incremento del Recall a un 25.12% (comparado con el 6.34% de la Corrida #1) demuestra que una gran parte del conocimiento extraído se encuentra en una zona de "proximidad semántica" que requiere umbrales menos restrictivos. Sin embargo, se observa ruido en el alineamiento (ej. caracteristicas asociado a Carica o el abor a miscarriage), lo que sugiere que aunque el Recall aumenta, la precisión del mapeo comienza a degradarse. Los términos residuales como hominivorax o mucopolisacarido confirman la existencia de entidades altamente específicas que la ontología NIFSTD no logra cubrir completamente bajo esta configuración.

4. Análisis Comparativo y Discusión

La comparación entre la Corrida #1 (θ=0.85) y la Corrida #2 (θ=0.75) revela una dinámica crítica en el alineamiento semántico de este corpus:

    Sensibilidad del Recall: Al reducir el umbral en un 11.7%, el Rdo​ se incrementó casi cuatro veces (de 0.0634 a 0.2512). Esto indica que la terminología de neurociencia presente en los documentos no utiliza necesariamente las etiquetas preferidas de NIFSTD, pero mantiene una fuerte cercanía vectorial.

    Compromiso entre Recall y Precisión: Mientras que la Corrida #1 ofrecía mapeos de alta fidelidad, la Corrida #2 introdujo "falsos positivos semánticos" debido a la ambigüedad (ej. el término funcional características alineado erróneamente con el taxón botánico Carica).

    Naturaleza de los Residuales: El análisis del Top 10 de residuales revela dos desafíos distintos para la construcción del grafo:

        Ruido Estructural (NER): Términos como iz quierdo o mas tenso evidencian errores en la segmentación de texto o en el reconocimiento de entidades, que no deberían formar parte del grafo de conocimiento.

        Gaps Ontológicos: Términos como mucopolisacarido o hominivorax representan entidades biológicas legítimas que, a pesar de su relevancia, no se encuentran bajo el paraguas de NIFSTD.

5. Conclusiones para Link Prediction

Basado en los resultados experimentales, se extraen las siguientes conclusiones para la fase de construcción del grafo:

    Insuficiencia de la Ontología Pura: Incluso con umbrales flexibles, el 74.88% de los términos del corpus permanecen sin mapear. Un grafo basado exclusivamente en NIFSTD ignoraría la mayor parte del conocimiento extraído de los documentos.

    Refinamiento del Umbral: Se sugiere un umbral híbrido o dinámico donde θ≈0.82 actúe como filtro de identidad y el rango [0.70,0.81] sea tratado mediante técnicas de desambiguación adicionales para minimizar el ruido observado en la Corrida #2.