import os
import argparse
import json
import logging
from typing import Optional
from document_processor import process_document
from llm_service import extract_structured_data, InsuranceData, get_total_cost, reset_cost # Import cost functions

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("processing.log"), # Log to a file
                        logging.StreamHandler() # Also log to console
                    ])

# --- Argument Parsing ---
def parse_arguments():
    parser = argparse.ArgumentParser(description='Extract structured data from insurance documents.')
    parser.add_argument('input_path', type=str, help='Path to an input document (PDF/TXT) or a directory containing documents.')
    parser.add_argument('-o', '--output_dir', type=str, default='output', help='Directory to save the structured JSON output.')
    parser.add_argument('--llm', type=str, default='openai', help='LLM provider to use (e.g., openai).')
    parser.add_argument('--model', type=str, default='gpt-3.5-turbo', help='Specific LLM model to use.')
    return parser.parse_args()

# --- Main Pipeline ---
def main():
    reset_cost() # Reset cost at the beginning of the run
    args = parse_arguments()

    input_path = args.input_path
    output_dir = args.output_dir
    llm_provider = args.llm
    model = args.model

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    files_to_process = []
    if os.path.isdir(input_path):
        logging.info(f"Processing directory: {input_path}")
        for filename in os.listdir(input_path):
            if filename.lower().endswith(('.pdf', '.txt')):
                files_to_process.append(os.path.join(input_path, filename))
            else:
                 logging.warning(f"Skipping unsupported file in directory: {filename}")
    elif os.path.isfile(input_path):
        if input_path.lower().endswith(('.pdf', '.txt')):
            files_to_process.append(input_path)
        else:
            logging.error(f"Unsupported file type provided: {input_path}")
            return
    else:
        logging.error(f"Input path not found: {input_path}")
        return

    if not files_to_process:
        logging.warning("No supported documents found to process.")
        return

    logging.info(f"Found {len(files_to_process)} documents to process.")

    for file_path in files_to_process:
        logging.info(f"--- Processing file: {os.path.basename(file_path)} ---")
        
        # 1. Process Document
        document_text = process_document(file_path)
        if not document_text:
            logging.error(f"Failed to read or process document: {file_path}")
            continue
        logging.info(f"Successfully read and cleaned document: {os.path.basename(file_path)}")

        # 2. Extract Data using LLM
        logging.info(f"Sending document to LLM ({llm_provider} - {model})...")
        structured_data: Optional[InsuranceData] = extract_structured_data(
            document_text,
            llm_provider=llm_provider,
            model=model
        )

        # 3. Save Output
        if structured_data:
            output_filename = os.path.splitext(os.path.basename(file_path))[0] + '.json'
            output_filepath = os.path.join(output_dir, output_filename)
            try:
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    # Use by_alias=True to get the original field names in JSON
                    json.dump(structured_data.dict(by_alias=True), f, indent=4)
                logging.info(f"Successfully extracted data and saved to: {output_filepath}")
            except Exception as e:
                logging.error(f"Failed to save output JSON for {file_path}: {e}")
        else:
            logging.error(f"Failed to extract structured data for: {file_path}")
        
        logging.info(f"--- Finished processing file: {os.path.basename(file_path)} ---")

    total_cost = get_total_cost()
    logging.info(f"Pipeline finished. Total estimated cost for this run: ${total_cost:.6f}")

if __name__ == "__main__":
    main()