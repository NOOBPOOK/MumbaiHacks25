import os
import json
from crewai import Agent, Task, Crew, LLM
from crewai.process import Process
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List

# --- 1. CONFIGURATION AND SCHEMA ---

# Load environment variables from .env file
# Assumes GEMINI_API_KEY="YOUR_API_KEY_HERE" is set in the .env file
load_dotenv()

# Define the structured output schema using Pydantic
class KeywordList(BaseModel):
    """The structured output containing a list of keywords."""
    keywords: List[str] = Field(
        description="A list of 5 to 8 of the most important and representative keywords extracted from the text."
    )


# --- 2. LLM SETUP ---

# Initialize the Gemini LLM
# LiteLLM automatically uses the GEMINI_API_KEY environment variable.
gemini_llm = LLM(
    model='gemini/gemini-2.5-pro',
    temperature=0.0, # Low temperature for reliable extraction and JSON generation
    max_retries=3 
)

# --- 3. AGENT DEFINITION ---

keyword_extractor_agent = Agent(
    role='Information Keyword Extractor',
    goal='Identify and return the core technical and subject keywords from an input text, strictly adhering to the JSON schema.',
    backstory='You are a skilled text analyst specializing in natural language processing (NLP) and subject matter indexing. Your primary function is to distill complex documents into essential keywords.',
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
        f"Analyze the following text and extract 5 to 8 of the most relevant and technical keywords. "
        f"The output must be a clean JSON array of strings.\n\n"
        f"TEXT TO ANALYZE:\n---\n{INPUT_TEXT}\n---"
    ),
    expected_output="A JSON array of strings containing the key terms, conforming strictly to the KeywordList schema.",
    agent=keyword_extractor_agent,
    # Crucial step: enforce structured output using the Pydantic model
    output_pydantic=KeywordList
)

# --- 5. CREW EXECUTION ---

keyword_crew = Crew(
    agents=[keyword_extractor_agent],
    tasks=[extraction_task],
    process=Process.sequential,
    verbose=1
)

# Execute the crew
print("--- Starting Keyword Extraction ---")
crew_result = keyword_crew.kickoff()

# --- 6. OUTPUT PROCESSING ---

# Access the structured Pydantic output directly
if crew_result.tasks_output and hasattr(crew_result.tasks_output[0], 'pydantic'):
    final_keyword_list: KeywordList = crew_result.tasks_output[0].pydantic
    
    # Convert the Pydantic model to a Python dictionary
    json_data = final_keyword_list.model_dump()

    # Define the output file path
    output_filename = "keywords_output.json"
    
    # Write the dictionary to a JSON file
    with open(output_filename, 'w') as f:
        json.dump(json_data, f, indent=4)
    
    print(f"\n--- Final Structured JSON Output Saved to {output_filename} ---")
    print(json.dumps(json_data, indent=4))
    
    print("\n--- Programmatic Access Example ---")
    print(f"Keywords Found: {', '.join(final_keyword_list.keywords)}")
else:
    print("\n--- Error: Failed to retrieve structured Pydantic output. ---")