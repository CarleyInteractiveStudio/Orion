# Orion Language Interpreter

Este repositorio contiene la implementación inicial de un intérprete para el lenguaje de programación Orion, un nuevo lenguaje diseñado con las siguientes metas en mente:

- **Visualidad como CSS:** Sintaxis declarativa para UI y componentes.
- **Control como C++:** Acceso de bajo nivel.
- **Seguridad como Rust:** Tipos fuertes y manejo de memoria seguro.
- **Simplicidad como Python:** Sintaxis limpia e intuitiva.
- **Modularidad como Go:** Sistema de módulos para código organizado.
- **Multiplataforma real:** Compilación a diferentes objetivos.

## Estado Actual del Proyecto

Este proyecto fue construido desde cero y contiene un intérprete funcional escrito en Python que soporta un subconjunto del lenguaje Orion.

### Características Implementadas

- **Lexer y Parser:** Un analizador léxico y sintáctico completo que procesa el código fuente de Orion y construye un Árbol de Sintaxis Abstracta (AST).
- **Intérprete (Evaluador):** Un intérprete tree-walking que ejecuta el AST.
  - **Tipos de Datos:** `Integer`, `String`, `Boolean`, `Array`, `Hash`.
  - **Variables:** Declaraciones con `let` y `var`.
  - **Operadores:** Aritméticos (`+`, `-`, `*`, `/`), lógicos (`!`), y de comparación (`<`, `>`, `==`, `!=`).
  - **Control de Flujo:** Sentencias `if/else` y `return`.
  - **Funciones:** Soporte para funciones de primera clase, incluyendo closures.
  - **Estructuras de Datos:** Arrays (`[1, 2]`) y Hashes (`{"key": "val"}`) con acceso por índice (`arr[0]`).
  - **Sistema de Módulos:** Soporte para `use` para importar código de otros archivos (simulado en `main.py`).
  - **Componentes:** El parser entiende la sintaxis de `component` y el evaluador crea una representación en memoria de ellos.
  - **Funciones Built-in:** Un sistema para funciones nativas, con `len()` implementado.

### Próximos Pasos (Características Faltantes)

- **Argumentos con Nombre:** Implementar el "azúcar sintáctico" para `miFuncion(nombre: valor)`.
- **Sistema de Componentes Completo:** Evaluación completa de estilos anidados y un motor de renderizado.
- **Más Tipos de Datos:** `float`, `enum`, `struct`.
- **Biblioteca Estándar:** Expandir las funciones built-in.
- **Compilador:** Para alcanzar las metas de rendimiento y multiplataforma, el siguiente gran paso sería construir un compilador (ej. a LLVM o WebAssembly) en lugar de solo un intérprete.

## Estructura del Proyecto

```
orion/
├── ast/         # Define el Árbol de Sintaxis Abstracta (AST)
├── evaluator/   # El intérprete/evaluador del código
├── lexer/       # El analizador léxico (tokenizer)
├── object/      # El sistema de objetos para valores en tiempo de ejecución
└── parser/      # El analizador sintáctico
main.py          # Punto de entrada para ejecutar el intérprete
test.orion       # Archivo de ejemplo con código Orion
```

## Cómo Ejecutar

Para ejecutar el intérprete con el archivo de ejemplo, simplemente corre:

```bash
python3 main.py
```

El script `main.py` está configurado para cargar y ejecutar `test.orion`, que demuestra muchas de las características implementadas.
