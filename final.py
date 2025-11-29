import os
from typing import List
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool, FirecrawlScrapeWebsiteTool
from pydantic import BaseModel, Field


from dotenv import load_dotenv
load_dotenv()

class Source(BaseModel):
    title: str = Field(description="The title of the website or article")
    url: str = Field(description="The URL of the source")

class VerificationResult(BaseModel):
    fake_confidence: float = Field(
        description="A score between 0.0 (Definitely Real) and 1.0 (Definitely Fake)."
    )
    reasoning: str = Field(
        description="A brief 1-sentence explanation of why this score was given."
    )
    sources: List[Source] = Field(
        description="A list of the top sources used for verification."
    )


# --- CONFIGURATION ---
# You can set these in a .env file or environment variables
# os.environ["SERPER_API_KEY"] = "your_serper_api_key"
# os.environ["GOOGLE_API_KEY"] = "your_gemini_api_key"
llm = LLM(
    model="gemini-2.5-flash",
    verbose=True,
    temperature=0.5,
)
def run_fact_check_pipeline(claim_input):
    print(f"\n🔎 Starting investigation for claim: '{claim_input}'...\n")

    # 2. SETUP TOOLS
    # Serper for finding the URLs
    search_tool = SerperDevTool()
    
    # Scraper for reading the actual content of the websites
    scrape_tool = FirecrawlScrapeWebsiteTool(api_key="fc-4d893012e69842f68e5b3a4134d286ad")

    # 3. DEFINE THE AGENT
    # This agent is responsible for the entire research pipeline
    researcher = Agent(
        role='Senior Information Architect',
        goal='Gather comprehensive context to verify a claim by scraping top sources.',
        backstory="""You are an expert investigative journalist. 
        You do not just read headlines; you dig into the full content of articles 
        to build a complete picture of the truth. You are meticulous about 
        using multiple sources.""",
        tools=[search_tool, scrape_tool],
        llm=llm,
        verbose=False,
        allow_delegation=False
    )

    # 4. DEFINE THE TASKS
    
    # Task 1: The "Architecture" logic you requested
    # Input -> Query -> Search -> Scrape Top 5 -> Build Context
    gather_evidence_task = Task(
        description=f"""
        Execute the following pipeline strictly for the claim: "{claim_input}"
        
        1. QUERY GENERATION: Analyze the claim and generate the most effective Google Search query to EITHER PROVE or DISPROVE the claim.
        2. SEARCH: Use the Search Tool with that query.
        3. SELECTION: Identify the top 3 most relevant URLs from the search results.
        4. SCRAPING: Use the Scrape Website Tool to extract the full text content from those 3 specific URLs.
        5. CONTEXTUALIZATION: Compile the scraped text into a single, cohesive "Wholesome Context" report.
        """,
        expected_output="""A detailed report containing the full context derived from the top 3 websites. 
        It should cite the sources used and provide the raw factual evidence found.""",
        agent=researcher,
        output_pydantic=VerificationResult
    )

    # 5. EXECUTE THE CREW
    crew = Crew(
        agents=[researcher],
        tasks=[gather_evidence_task],
        process=Process.sequential,
        verbose=False
    )

    crew_output = crew.kickoff()
    # We access the .pydantic attribute specifically
    if crew_output.pydantic:
        return crew_output.pydantic.model_dump_json(indent=2)
    else:
        # Fallback if the LLM failed to generate valid JSON
        return f'{{"error": "Failed to generate valid JSON", "raw_output": "{crew_output.raw}"}}'

# --- ENTRY POINT ---
if __name__ == "__main__":
    user_claim = """
        Australia captain Pat Cummins has been ruled out of the second Ashes Test in Brisbane as he continues to recover from a back injury, extending his absence after missing the side’s dramatic opening win over England in Perth. Despite bowling in the nets in both Perth and Sydney, the 32-year-old fast bowler has not completed the full return-to-play programme required for Test cricket, prompting selectors to retain an unchanged 14-man squad led once again by stand-in captain Steve Smith. Australia will also be without Josh Hazlewood, who remains sidelined with a hamstring injury, leaving Mitchell Starc, Scott Boland, Brendan Doggett, Cameron Green and Nathan Lyon as the likely attack for the day-night match at the Gabba. Questions remain over opener Usman Khawaja’s place after Travis Head’s exceptional century from the top of the order in Perth, while alternatives such as Josh Inglis or Michael Neser could come into contention if Australia reshuffle. Cummins will rejoin the squad in Brisbane as he targets a comeback in the third Test in Adelaide next month, while England have scheduled additional training sessions as they prepare for a venue where Australia have not lost an Ashes Test since 1986.
        """
    res = run_fact_check_pipeline(user_claim)

    # print("\n\n########################🧢🧢🧢🧢🧢🧢")
    print(res)
