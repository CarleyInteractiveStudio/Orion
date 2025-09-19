# Orion Programming Language

Orion is a modern, bytecode-compiled programming language written in Python. It features a familiar C-style syntax, a growing standard library, and a simple UI toolkit for building graphical applications.

## Language Features

Orion supports a rich set of features that make it a flexible and powerful language:

*   **Variables:** Declare variables with `var` and assign values. Basic types include `number`, `string`, `bool`, and `nil`.
*   **Control Flow:** Use `if/else` for conditional logic and `while` for looping.
*   **Functions:** First-class functions with support for closures, allowing for powerful functional programming patterns.
*   **Operators:** Standard arithmetic (`+`, `-`, `*`, `/`), comparison (`==`, `>`, `<`), and logical (`!`) operators. The `+` operator is overloaded for string concatenation.
*   **Data Structures:**
    *   **Lists:** Ordered collections of items, e.g., `[1, "two", true]`.
    *   **Dictionaries:** Key-value stores (currently only string keys are fully supported).
*   **Object-Oriented Programming:**
    *   **Classes:** Define custom types using the `class` keyword.
    *   **Inheritance:** Support for single inheritance using the `<` symbol (e.g., `class Subclass < Superclass`).
    *   **Properties & Methods:** Classes can have both data properties and methods.
*   **Built-in Functions:** Includes `print()` for console output and `len()` to get the length of strings and lists.

## Standard Library

Orion comes with a set of built-in native modules for common tasks:

*   **`fs`:** Filesystem operations like `read()`, `write()`, `append()`, and `exists()`.
*   **`http`:** Make simple HTTP GET requests with `get()`.
*   **`json`:** Parse and stringify JSON data with `parse()` and `stringify()`.

## UI Toolkit (`ui.orion`)

We have built a foundational UI library that allows for creating simple graphical user interfaces.

*   **Layout:**
    *   `Column`: Arranges child components vertically.
    *   `Row`: Arranges child components horizontally.
    *   Supports `padding` and cross-axis `alignment`.
*   **Components:**
    *   `Label`: Displays text.
    *   `Image`: Displays images from a file path.
    *   `Button`: A clickable button with `onClick`, `onMouseEnter`, and `onMouseLeave` events.
    *   `Checkbox`: A stateful checkbox.
    *   `ScrollView`: A scrollable container for content that exceeds its bounds.
    *   `Slider`: An interactive slider with an `onChange` event.
*   **Event System:** A simple event system for handling user interactions like mouse clicks and movement.

## Project Status & Roadmap

This project has been under active development. We have successfully implemented a robust compiler and virtual machine from the ground up, tackling numerous complex features and bugs along the way.

**Completed Milestones:**
*   Core language syntax and semantics (parsing, compilation, execution).
*   Implementation of lists, dictionaries, classes, inheritance, and closures.
*   Fixing major bugs in the VM, including re-entrant calls and call frame management.
*   Adding proper line-number-based error reporting.
*   Building essential standard library modules (`fs`, `http`, `json`).
*   Developing a functional UI toolkit with layout and interactive components.

**Next Steps:**
The next major feature on our roadmap is the **Interactive Debugger**.

*   **`debug;` statement:** The language already supports a `debug;` statement to pause execution.
*   **Interactive Commands:** We will build a command-line interface for the debugger to support:
    *   `step`: Execute the next instruction.
    *   `continue`: Resume execution.
    *   `print <variable>`: Inspect variable values.
    *   `stack`: View the current call stack.

This will be a significant step towards making Orion a more mature and developer-friendly language.
