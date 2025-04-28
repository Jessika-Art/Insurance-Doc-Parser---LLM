import os
import shutil
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from llm_service import get_total_cost, reset_cost

from pathlib import Path
import uvicorn
from fastapi.concurrency import run_in_threadpool # Import run_in_threadpool

# Assuming main.py can be refactored or its core logic imported
# For now, let's simulate the processing logic
from document_processor import read_pdf, read_text
from llm_service import get_llm_client, extract_structured_data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="Insurance Document Parser API")

# Serve static files (for frontend UI)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


# Add a simple root endpoint
@app.get("/", summary="Root endpoint", include_in_schema=False)
async def read_root():
    return {"message": "Insurance Document Parser API is running. Visit /docs for documentation."}

# Define directories relative to the script location
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "api_uploads"
OUTPUT_DIR = BASE_DIR / "api_output"

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

@app.post("/upload/", summary="Upload and process an insurance document")
async def upload_document(file: UploadFile = File(...), llm_provider: str = Form("openai"), model: str = Form("gpt-3.5-turbo")):
    """
    Uploads a single insurance document (PDF or TXT), processes it using the LLM,
    and returns the extracted structured data.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in [".pdf", ".txt"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and TXT are supported.")

    # Save the uploaded file temporarily
    temp_file_path = UPLOAD_DIR / file.filename
    try:
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logging.info(f"File '{file.filename}' uploaded successfully.")

        # --- Processing Logic (adapted from main.py) ---
        logging.info(f"Processing document: {temp_file_path}")
        # Run blocking I/O in thread pool
        text_content = await run_in_threadpool(read_pdf, temp_file_path)

        if not text_content:
            logging.warning(f"Could not extract text from {temp_file_path}")
            raise HTTPException(status_code=400, detail=f"Could not extract text from file: {file.filename}")
        # --- Truncate very large documents if LLM has tokens limit ---
        MAX_CHAR_LIMIT = 20000
        if len(text_content) > MAX_CHAR_LIMIT:
            logging.warning(f"Document too large ({len(text_content)} characters). Truncating to {MAX_CHAR_LIMIT} characters.")
            text_content = text_content[:MAX_CHAR_LIMIT]


        llm_service = get_llm_client(llm_provider=llm_provider)
        if not llm_service:
             raise HTTPException(status_code=500, detail=f"Failed to initialize LLM service: {llm_provider}")

        # Run blocking LLM call in thread pool
        # TODO: Integrate cost tracking here when llm_service is updated
        logging.info(f"Calling LLM service ({llm_provider} - {model}) for {temp_file_path.name}") # Added logging
        try:
            structured_data = await run_in_threadpool(extract_structured_data, text_content, llm_provider=llm_provider, model=model)
            logging.info(f"LLM call successful for {temp_file_path.name}") # Added logging
        except Exception as llm_exc:
            logging.error(f"Error during LLM call for {temp_file_path.name}: {llm_exc}", exc_info=True) # Added detailed logging
            raise HTTPException(status_code=500, detail=f"Error during LLM processing for {file.filename}")

        if structured_data:
            output_filename = OUTPUT_DIR / f"{temp_file_path.stem}.json"
            logging.info(f"Attempting to save structured data to {output_filename}") # Added logging
            try:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    f.write(structured_data.model_dump_json(indent=4))
                logging.info(f"Successfully extracted data for {temp_file_path.name} to {output_filename}")

                # Return the extracted data directly
                # return structured_data.model_dump()
                return {
                    "extracted_data": structured_data.model_dump(),
                    "cost": round(get_total_cost(), 6)  # return the cost rounded
                }

            except Exception as e:
                logging.error(f"Error saving JSON for {temp_file_path.name}: {e}", exc_info=True) # Added detailed logging
                raise HTTPException(status_code=500, detail=f"Error saving extracted data for {file.filename}")
        else:
            logging.error(f"Failed to extract structured data for {temp_file_path.name} (LLM returned None)") # Clarified logging
            raise HTTPException(status_code=500, detail=f"LLM failed to extract data from {file.filename}")

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions
        raise http_exc
    except Exception as e:
        logging.error(f"An error occurred during processing {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal error occurred processing {file.filename}.")
    finally:
        # Clean up the uploaded file
        if temp_file_path.exists():
            try:
                os.remove(temp_file_path)
                logging.info(f"Removed temporary file: {temp_file_path}")
            except OSError as e:
                logging.error(f"Error removing temporary file {temp_file_path}: {e}")
        # Ensure the file object is closed
        await file.close()



if __name__ == "__main__":
    # Make sure to run with uvicorn for development
    # Example: uvicorn api:app --reload
    print("To run the API, use the command: uvicorn api:app --reload")
    # uvicorn.run(app, host="127.0.0.1", port=8000)