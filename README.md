# Insurance Document Parser

This project extracts structured information from insurance documents (PDF or TXT) using an LLM (currently configured for OpenAI).

## Features

- Reads text from PDF and TXT files.
- Cleans extracted text.
- Uses an LLM (OpenAI GPT models) to extract predefined fields:
    - Policyholder Name
    - Policy Number
    - Coverage Start Date
    - Coverage End Date
    - Coverage Types
    - Risk Factors
- Validates the extracted data structure using Pydantic.
- Handles LLM API retries automatically.
- Saves the structured output as JSON files.
- Tracks estimated API costs for OpenAI calls.
- Provides a simple Web UI for uploading documents and viewing results.

## Setup

1. **Environment**  
   This project assumes you have a Python environment set up (like the `env` folder created using `venv`).

2. **Install Dependencies**  
    ```
    pip install -r requirements.txt
    ```

3. **API Key**  
    - Create a `.env` file in the project root if it doesn't exist.
    - Add your OpenAI API key:
    ```dotenv
    OPENAI_API_KEY=your-openai-api-key-here
    ```

## Usage (Command Line)

1. **Prepare Input Documents**  
    - Create a directory (e.g., `input_docs`) in the project root.
    - Place your insurance documents (.pdf or .txt files) into this directory.

2. **Run the Script**  
    ```bash
    python main.py input_docs -o output
    ```
    - `input_docs` is the folder containing your documents.
    - `-o output` specifies where to save the extracted JSON files (it will be created if it doesn't exist).
    - Optional arguments:
        - `--llm` to select the LLM provider (default is OpenAI).
        - `--model` to select the model (default is `gpt-3.5-turbo`).

3. **Output**  
    - The script processes each document.
    - Saves extracted structured data as JSON files in the output directory.
    - Progress and errors are logged in `processing.log`.

## Usage (Web API) User Interface

1. **Run the API Server**  
    ```bash
    uvicorn api:app --reload
    ```
    - API will be available at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

2. **Use the Web UI**  
    - Open your browser and visit [http://127.0.0.1:8000](http://127.0.0.1:8000)
    - Use the interface to:
        - Upload a document.
        - Choose the LLM model.
        - View extracted structured data.
        - View the cost of the LLM call.

3. **Use Swagger UI**  
    - Alternatively, you can use the automatic documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Project Structure




```
Insurance Document Parser
├─ 📁api_output
│  └─ 📄nfu-mutual-bespoke-insurance-policy-document.json
├─ 📁api_uploads
├─ 📁output
├─ 📁static
│  └─ 📄index.html
├─ 📁__pycache__
│  ├─ 📄api.cpython-310.pyc
│  ├─ 📄document_processor.cpython-310.pyc
│  ├─ 📄evaluate.cpython-310.pyc
│  └─ 📄llm_service.cpython-310.pyc
├─ 📄.env
├─ 📄.gitignore
├─ 📄api.py
├─ 📄document_processor.py
├─ 📄llm_service.py
├─ 📄main.py
├─ 📄processing.log
├─ 📄README_.md
└─ 📄requirements.txt
```