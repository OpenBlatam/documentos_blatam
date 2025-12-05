# Top 10 Papers de Reasoning en LLMs

Este documento resume los 10 papers más importantes sobre razonamiento (chain, tree, graph of thoughts) en Large Language Models.

## 📚 Papers Implementados

### 1. SOLAR: Scalable Optimization of Large-scale Architecture for Reasoning
**Autores:** Chen, Li, Luo, Bolimera, Ahmed, Srinivasan, Gokhale, Savvides (2025)  
**Venue:** arXiv 2025  
**URL:** https://arxiv.org/abs/2503.04530

**Técnica Principal:**
- Framework para adaptar dinámicamente entre chain, tree y graph de pensamiento
- Optimiza precisión y eficiencia según la tarea
- Escalable para arquitecturas de gran escala

**Implementación:** `papers/research/paper_solar.py`

**Uso:**
```python
from papers.research.paper_solar import SOLARModule, SOLARConfig

config = SOLARConfig(hidden_dim=512, num_paradigms=3)
module = SOLARModule(config)

output, metadata = module(hidden_states)
# metadata contiene: selected_paradigm, paradigm_scores, precision_estimate, efficiency_estimate
```

---

### 2. Adaptive Graph of Thoughts: Test-Time Adaptive Reasoning
**Autores:** Pandey, Ghukasyan, Goktas, Radha (2025)  
**Venue:** arXiv 2025  
**URL:** https://arxiv.org/abs/[ID_PENDIENTE]

**Técnica Principal:**
- Usa un DAG dinámico para razonar solo donde es necesario
- Une chain, tree y graph en inferencia
- Adaptación en tiempo de test (test-time adaptation)

**Implementación:** `papers/research/paper_adaptive_got.py`

**Uso:**
```python
from papers.research.paper_adaptive_got import AdaptiveGoTModule, AdaptiveGoTConfig

config = AdaptiveGoTConfig(hidden_dim=512, max_nodes=20, importance_threshold=0.5)
module = AdaptiveGoTModule(config)

output, metadata = module(hidden_states)
# metadata contiene: num_nodes, num_edges, dag_density, num_reasoned_nodes, reasoning_ratio
```

---

### 3. What Makes a Good Reasoning Chain? Uncovering Structural Patterns in Long Chain-of-Thought Reasoning
**Autores:** LCoT2Tree (2025)  
**Venue:** ACL Anthology 2025  
**URL:** https://aclanthology.org/[ID_PENDIENTE]

**Técnica Principal:**
- Analiza patrones estructurales (exploración, backtracking, verificación) en cadenas de razonamiento largo
- Predice cuándo las cadenas son correctas
- Convierte cadenas largas en árboles para mejor análisis

**Implementación:** `papers/research/paper_lcot2tree.py`

**Uso:**
```python
from papers.research.paper_lcot2tree import LCoT2TreeModule, LCoT2TreeConfig

config = LCoT2TreeConfig(hidden_dim=512, correctness_threshold=0.7)
module = LCoT2TreeModule(config)

output, metadata = module(hidden_states)
# metadata contiene: correctness_score, is_correct, pattern_scores
```

---

### 4. Disentangling Memory and Reasoning Ability in Large Language Models
**Autores:** Yao, Yu, Zhang, Narasimhan, et al. (2025)  
**Venue:** ACL Anthology 2025  
**URL:** https://aclanthology.org/[ID_PENDIENTE]

**Técnica Principal:**
- Separa capacidad de memoria de capacidad de razonamiento en LLMs
- Identifica qué parte del razonamiento es "memoria latente" vs "pensamiento activo"
- Permite entender mejor las capacidades de los modelos

**Implementación:** `papers/research/paper_memory_reasoning_disentangle.py`

**Uso:**
```python
from papers.research.paper_memory_reasoning_disentangle import MemoryReasoningDisentangleModule, MemoryReasoningDisentangleConfig

config = MemoryReasoningDisentangleConfig(hidden_dim=512, disentanglement_weight=0.5)
module = MemoryReasoningDisentangleModule(config)

output, metadata = module(hidden_states)
# metadata contiene: memory_score, reasoning_score, memory_ratio, reasoning_ratio
```

---

### 5. Self-guided Knowledgeable Network of Thoughts (kNoT)
**Autores:** Chen, Yeh, Chen, Yang, Ming-Syan (2024)  
**Venue:** arXiv 2024  
**URL:** https://arxiv.org/abs/[ID_PENDIENTE]

**Técnica Principal:**
- Introduce red de "pensamientos" como nodos de un grafo
- Permite planes de razonamiento más complejos y flexibles
- No solo cadena o árbol, sino grafo completo

**Implementación:** `papers/research/paper_knot.py`

**Uso:**
```python
from papers.research.paper_knot import KNoTModule, KNoTConfig

config = KNoTConfig(hidden_dim=512, max_thoughts=15, network_density=0.4)
module = KNoTModule(config)

output, metadata = module(hidden_states)
# metadata contiene: num_thoughts, num_connections, network_density, guide_entropy
```

---

### 6. Graph Chain-of-Thought: Augmenting Large Language Models by Reasoning on Graphs
**Autores:** Jin, Xie, Zhang, et al. (2024)  
**Venue:** arXiv 2024  
**URL:** https://arxiv.org/abs/[ID_PENDIENTE]

**Técnica Principal:**
- Razonar sobre grafos de conocimiento
- Cada paso del modelo interactúa con un grafo para generar pensamiento más estructurado
- Integra conocimiento estructurado en el razonamiento

**Implementación:** `papers/research/paper_graph_cot.py`

**Uso:**
```python
from papers.research.paper_graph_cot import GraphCoTModule, GraphCoTConfig

config = GraphCoTConfig(hidden_dim=512, graph_nodes=10, use_graph_attention=True)
module = GraphCoTModule(config)

output, metadata = module(hidden_states)
# metadata contiene: graph_nodes, graph_edges, interaction_applied
```

---

### 7. Demystifying Chains, Trees, and Graphs of Thoughts
**Autores:** Besta, Memedi, Zhang, et al. (2024)  
**Venue:** emergentmind.com 2024  
**URL:** https://emergentmind.com/[ID_PENDIENTE]

**Técnica Principal:**
- Análisis teórico y estructural de diferentes formas de pensamiento
- Compara chain, tree y graph para entender qué paradigmas funcionan mejor según la tarea
- Proporciona guías para selección de paradigma

**Implementación:** `papers/research/paper_demystifying_got.py`

**Uso:**
```python
from papers.research.paper_demystifying_got import DemystifyingGoTModule, DemystifyingGoTConfig

config = DemystifyingGoTConfig(hidden_dim=512, task_type='general')
module = DemystifyingGoTModule(config)

output, metadata = module(hidden_states)
# metadata contiene: optimal_paradigm, paradigm_scores, structure_scores, task_paradigm_match
```

---

### 8. Forest-of-Thought: Scaling Test-Time Compute for Enhancing LLM Reasoning
**Autores:** Bi, Han, Liu, Tang, Wang (2024)  
**Venue:** Kingy AI 2024  
**URL:** https://kingy.ai/[ID_PENDIENTE]

**Técnica Principal:**
- Mantiene múltiples árboles de razonamiento en paralelo ("forest")
- Activa solo los árboles más relevantes para mejorar precisión/eficiencia
- Escala computación en tiempo de test

**Implementación:** `papers/research/paper_forest_of_thought.py`

**Uso:**
```python
from papers.research.paper_forest_of_thought import ForestOfThoughtModule, ForestOfThoughtConfig

config = ForestOfThoughtConfig(hidden_dim=512, num_trees=5, selection_top_k=3)
module = ForestOfThoughtModule(config)

output, metadata = module(hidden_states)
# metadata contiene: num_trees, num_selected, relevance_scores, selection_ratio
```

---

### 9. Beyond Chain-of-Thought: Effective Graph-of-Thought Reasoning in Language Models
**Autores:** Yao, Li, Zhao (2024)  
**Venue:** bohrium.dp.tech 2024  
**URL:** https://bohrium.dp.tech/[ID_PENDIENTE]

**Técnica Principal:**
- Propone encoder para grafo de pensamientos
- Se fusiona con la entrada original para permitir razonamiento no secuencial
- Extiende chain-of-thought a graph-of-thought

**Implementación:** `papers/research/paper_beyond_cot.py`

**Uso:**
```python
from papers.research.paper_beyond_cot import BeyondCoTModule, BeyondCoTConfig

config = BeyondCoTConfig(hidden_dim=512, graph_nodes=12, fusion_method='attention')
module = BeyondCoTModule(config)

output, metadata = module(hidden_states)
# metadata contiene: graph_nodes, fusion_method, non_sequential_layers
```

---

### 10. Table as Thought: Exploring Structured Thoughts in LLM Reasoning
**Autores:** TRL 2025  
**Venue:** ACL Anthology / TRL 2025  
**URL:** https://aclanthology.org/[ID_PENDIENTE]

**Técnica Principal:**
- Organiza "pensamientos" en una estructura de tabla
- Nueva forma de estructurar la inferencia
- Permite razonamiento más organizado y estructurado

**Implementación:** `papers/research/paper_table_as_thought.py`

**Uso:**
```python
from papers.research.paper_table_as_thought import TableAsThoughtModule, TableAsThoughtConfig

config = TableAsThoughtConfig(hidden_dim=512, table_rows=5, table_cols=4)
module = TableAsThoughtModule(config)

output, metadata = module(hidden_states)
# metadata contiene: table_rows, table_cols, table_cells, structure_method
```

---

## 🔄 Comparación de Paradigmas

| Paradigma | Complejidad | Flexibilidad | Eficiencia | Mejor Para |
|-----------|-------------|--------------|------------|------------|
| Chain | Baja | Baja | Alta | Tareas secuenciales simples |
| Tree | Media | Media | Media | Búsqueda y exploración |
| Graph | Alta | Alta | Baja | Razonamiento complejo |
| Forest | Alta | Alta | Media | Múltiples hipótesis |
| Table | Media | Media | Media | Organización estructurada |

## 🎯 Mejores Prácticas

1. **Para tareas simples:** Usar Chain-of-Thought
2. **Para exploración:** Usar Tree-of-Thought o Forest-of-Thought
3. **Para razonamiento complejo:** Usar Graph-of-Thought o kNoT
4. **Para adaptación dinámica:** Usar SOLAR o Adaptive GoT
5. **Para análisis:** Usar LCoT2Tree o Demystifying GoT

## 📊 Métricas Reportadas

- **Precisión:** Mejora variable según paradigma y tarea
- **Eficiencia:** Chain > Tree > Graph (generalmente)
- **Flexibilidad:** Graph > Tree > Chain
- **Escalabilidad:** Forest y SOLAR muestran mejor escalabilidad

---

**Nota:** Los URLs de los papers son placeholders. Se deben actualizar cuando los papers estén disponibles públicamente.

