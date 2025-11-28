import os
import json
from crewai import Agent, Task, Crew, LLM
from crewai.process import Process
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List

# --- 1. CONFIGURATION AND SCHEMA ---

# Load environment variables from .env file
load_dotenv()

# Define the structured output schema using Pydantic
class Claim(BaseModel):
    """Represents a single verifiable claim extracted from the text."""
    claim_id: int = Field(description="A unique integer ID for this claim, starting from 1.")
    statement: str = Field(description="The exact claim or assertion made in the text.")

class ClaimList(BaseModel):
    """The final list structure for all claims extracted."""
    claims: List[Claim] = Field(description="A list containing all claims extracted from the input text.")


# --- 2. LLM SETUP ---

# Initialize the Gemini LLM
# LiteLLM automatically uses the GEMINI_API_KEY environment variable.
gemini_llm = LLM(
    model='gemini/gemini-2.5-flash',
    temperature=0.0, # Low temperature for reliable extraction and JSON generation
    # Setting max_retries ensures robustness in structured output generation
    max_retries=3 
)

# --- 3. AGENT DEFINITION ---

claim_extractor_agent = Agent(
    role='Structured Claim Extractor',
    goal='Accurately identify all verifiable claims within a given text and structure them according to the required JSON schema.',
    backstory='You are a meticulous language model specializing in parsing unstructured text into clean, valid JSON format. You are highly reliable in detecting subtle assertions and assigning accurate confidence scores.',
    verbose=True,
    allow_delegation=False,
    llm=gemini_llm
)

# --- 4. TASK DEFINITION ---

INPUT_TEXT = """
🔥 BREAKING – UNBELIEVABLE!!! 🔥
Just came across this mind-blowing photo — all the biggest tech bosses hanging out together over Thanksgiving dinner! 😲🦃

There’s Elon Musk, Mark Zuckerberg, Sundar Pichai, Satya Nadella, Tim Cook — sitting around a table like old friends, laughing, talking, drinks on the table. 🍷🍽️
Someone is saying this was snapped right after a secret “super-AI summit” where they met to decide the future of AI & Web. 💡🤖

It’s “the most powerful dinner” ever — feels crazy that these guys, who usually fight behind closed doors, are chilling together! 😮

If this image is real, it means something big is cooking 👀… share this around so everyone sees! 🌐🔥
"""

extraction_task = Task(
    description=(
        f"Analyze the following text and extract all distinct, factual claims. "
        f"Ignore opinions, definitions, or predictions unless they contain a concrete, measurable assertion.\n\n"
        f"TEXT TO ANALYZE:\n---\n{INPUT_TEXT}\n---"
    ),
    expected_output="A list of claims strictly formatted as a JSON array conforming to the Pydantic ClaimList schema.",
    agent=claim_extractor_agent,
    # Crucial step: enforce structured output using the Pydantic model
    output_pydantic=ClaimList
)

# --- 5. CREW EXECUTION ---

claim_crew = Crew(
    agents=[claim_extractor_agent],
    tasks=[extraction_task],
    process=Process.sequential,
    verbose=1
)

# Execute the crew
print("--- Starting Claim Extraction ---")
crew_result = claim_crew.kickoff()

# --- 6. OUTPUT PROCESSING ---

# Access the structured Pydantic output directly
if crew_result.tasks_output and hasattr(crew_result.tasks_output[0], 'pydantic'):
    final_claim_list: ClaimList = crew_result.tasks_output[0].pydantic
    
    # Convert the Pydantic model to a Python dictionary
    json_data = final_claim_list.model_dump()

    # Define the output file path
    output_filename = "claims_output.json"
    
    # Write the dictionary to a JSON file
    with open(output_filename, 'w') as f:
        json.dump(json_data, f, indent=4)
    
    print(f"\n--- Final Structured JSON Output Saved to {output_filename} ---")
    print(json.dumps(json_data, indent=4))
    
    print("\n--- Programmatic Access Example ---")
    for claim in final_claim_list.claims:
        print(f"ID: {claim.claim_id} | Statement: {claim.statement}")
else:
    print("\n--- Error: Failed to retrieve structured Pydantic output. ---")