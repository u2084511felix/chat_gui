# OpenAI Structured Output Generator GUI

## Overview
This is an interface I threw together in march 2023 after the GPT-4 API was released. I wanted more control over the conversation history, and also the ability to import and export projects, as well as switch between models. I came back to it after two years because I wanted to have a way to quickly generate, inspect, review and export useful schemas, and structured outputs. 
I moved the project to a new GUI framework, and have included a util script for the openai api. 

## Todo:
- Investigate why complex json objects in the legacy schema generator with multi level of nested objects and arrays are not being returned fully in the output schema.

## Features

### 1. **Structured Output Modes**
- **Current Structured Output**: Uses OpenAI's structured response format.
- **Legacy Structured Output**: Implements a function-calling-based method for structured data generation.
- **Schema Generator**: Automatically converts a JSON object into a JSON Schema for structured responses.

### 2. **Message History Editing**
- Allows users to review and edit previous messages.
- Enables quick modifications of assistant responses within the GUI.

### 3. **Configuration Panel**
- Adjust model parameters.
- Select and switch between OpenAI models.

### 4. **Schema and Structured Output Generation**
- Quickly generate and validate structured outputs.
- Inspect and edit schemas before generating structured responses.
- Export results for further use or analysis.

## Structured Output Generation

### **Switching Between Modes**
- Users can toggle between structured output modes using the "Structured Output Mode" dropdown.
- **Legacy structured output** uses function calling, while the **new mode** uses OpenAI's latest native structured format.
- Each step is clearly labeled for clarity.

### **Schema Generator**
I have included my built-in **Schema Generator**, which converts any JSON object into valid a JSON Schema as output. This specifically conforms to the OpenAI format for structured output generation, and automates the process of generating complex schemas for structured outputs. The generated schemas can be fed directly into the structured output generation process with the addition of simple instruction prompts. I have turned this into a simple two step process, which is very easy to use.

## Future Plans
- Additional OpenAI configuration options in the config tab.
- Multi-modality support (image and audio generation).
- Integration of alternative language models.
- Improved session handling and export features.

## Setup & Dependencies

### **Requirements**
- Python **3.12+**
- Poetry package manager
- Dependencies managed via Poetry:
  - `PySide6`
  - `qasync`
  - `openai`
  - `pydantic`

### **Installation Instructions**
1. Clone the repository.

2. Install python poetry.
   ```sh
   pipx install poetry
   ```
3. Install dependencies:
   ```sh
   poetry install
   ```

### **Running the Application**
To start the GUI, use:
```sh
poetry run python chatmod002.py
```
