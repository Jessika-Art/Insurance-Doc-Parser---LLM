import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI
from dotenv import load_dotenv
import time
import logging

# Configure logging (use the same configuration as main.py/api.py if possible)
# Basic config for this module if run standalone or imported early
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Cost Tracking --- 
# Placeholder costs - replace with actual OpenAI pricing
# Prices per 1,000 tokens
MODEL_COSTS = {
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4o-2024-08-06": {"input": 0.01, "output": 0.03},
    # Add other models as needed
}

_total_cost = 0.0

def get_total_cost():
    """Returns the total accumulated cost since the last reset."""
    global _total_cost
    return _total_cost

def reset_cost():
    """Resets the total accumulated cost to zero."""
    global _total_cost
    _total_cost = 0.0

def _calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculates the cost for a given API call."""
    cost_info = MODEL_COSTS.get(model)
    if not cost_info:
        logging.warning(f"Cost information not found for model: {model}. Cost will not be calculated.")
        return 0.0
    
    input_cost = (prompt_tokens / 1000) * cost_info["input"]
    output_cost = (completion_tokens / 1000) * cost_info["output"]
    return input_cost + output_cost

# Load environment variables from .env file
load_dotenv()

# --- Pydantic Model for Structured Output ---
class InsuranceData(BaseModel):
    policyholder_name: Optional[str] = Field(None, alias="Policyholder Name")
    policy_number: Optional[str] = Field(None, alias="Policy Number")
    start_date: Optional[str] = Field(None, alias="Start Date")
    end_date: Optional[str] = Field(None, alias="End Date")
    coverage_types: Optional[List[str]] = Field(None, alias="Coverage Types")
    risk_factors: Optional[List[str]] = Field(None, alias="Risk Factors")

# --- LLM Interaction Logic ---
def get_llm_client(llm_provider: str = "openai"):
    """Initializes and returns the appropriate LLM client."""
    if llm_provider.lower() == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        return OpenAI(api_key=api_key)
    # Add logic for other LLM providers here if needed
    # elif llm_provider.lower() == "other_llm":
    #     api_key = os.getenv("OTHER_LLM_API_KEY")
    #     # Initialize and return other LLM client
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")

def extract_structured_data(
    document_text: str,
    llm_provider: str = "openai",
    model: str = "gpt-3.5-turbo", # Or another suitable model
    max_retries: int = 2,
    retry_delay: int = 5 # seconds
) -> Optional[InsuranceData]:
    """Sends document text to the LLM and attempts to extract structured data."""

    prompt = f"""Extract the following information from this insurance document:
    1. Policyholder Name
    2. Policy Number
    3. Start Date
    4. End Date
    5. Coverage Types (list of strings)
    6. Risk Factors (list of strings)

    Return the information ONLY in JSON format with the exact keys specified above (e.g., "Policyholder Name"). If a field is not found, omit it or set its value to null.

    Document Text:
    ```
    {document_text}
    ```

    JSON Output:
    """

    client = get_llm_client(llm_provider)
    attempt = 0

    while attempt < max_retries:
        try:
            if llm_provider.lower() == "openai":
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an expert assistant specialized in extracting structured data from insurance documents into JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}, # Request JSON output if supported
                    temperature=0.2 # Lower temperature for more deterministic output
                )
                raw_json_output = response.choices[0].message.content
            # Add logic for other LLMs here
            # elif llm_provider.lower() == "other_llm":
            #     # ... call other LLM API ...
            #     raw_json_output = ...
            else:
                 return None # Should not happen if get_llm_client worked

            if not raw_json_output:
                print(f"Attempt {attempt + 1}: LLM returned empty response.")
                raise ValueError("Empty response from LLM")

            # Basic cleaning in case the LLM includes markdown backticks
            cleaned_json_output = raw_json_output.strip().strip('```json').strip('```').strip()

            # Parse the JSON string
            data = json.loads(cleaned_json_output)

            # Validate with Pydantic
            validated_data = InsuranceData.parse_obj(data)
            logging.info("Successfully extracted and validated data.")

            # --- Cost Calculation ---
            global _total_cost
            if llm_provider.lower() == "openai" and hasattr(response, 'usage') and response.usage:
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                call_cost = _calculate_cost(model, prompt_tokens, completion_tokens)
                _total_cost += call_cost
                logging.info(f"API Call Cost ({model}): ${call_cost:.6f} (Prompt: {prompt_tokens}, Completion: {completion_tokens})")
                logging.info(f"Accumulated Cost: ${_total_cost:.6f}")
            else:
                logging.warning("Could not calculate cost: Usage data missing or unsupported provider.")
            # --- End Cost Calculation ---

            return validated_data

        except json.JSONDecodeError as e:
            logging.error(f"Attempt {attempt + 1}: Failed to decode JSON from LLM response: {e}")
            logging.debug(f"Raw response: {raw_json_output}") # Log raw response only at debug level
        except ValidationError as e:
            logging.error(f"Attempt {attempt + 1}: Validation error: {e}")
            logging.debug(f"Parsed data: {data}") # Log parsed data only at debug level
        except Exception as e:
            logging.error(f"Attempt {attempt + 1}: An unexpected error occurred: {e}", exc_info=True)

        attempt += 1
        if attempt < max_retries:
            logging.warning(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

    logging.error("Failed to extract structured data after multiple retries.")
    return None

# Example Usage (for testing)
if __name__ == '__main__':
    # Example Usage (for testing)
    # Ensure logging is configured for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    reset_cost() # Reset cost for standalone test

    # Replace with actual text from a test document
    test_text = """
    INSURANCE POLICY
    Policyholder: John Doe
    Policy Number: ABC123456789
    Effective Date: 2024-01-01
    Expiration Date: 2025-01-01
    Coverage: Fire, Theft
    This policy covers risks associated with standard residential properties.
    Notable Risk Factors: Located in flood zone B.
    """

    extracted_info = extract_structured_data(test_text)

    if extracted_info:
        logging.info("\nExtracted Data:")
        logging.info(extracted_info.model_dump_json(indent=2, by_alias=True))
        logging.info(f"\nTotal cost for this run: ${get_total_cost():.6f}")
    else:
        logging.error("\nCould not extract data.")