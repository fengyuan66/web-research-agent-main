# RestaurantRAG README

# What it is

This is an agenetic RAG (Retrieval-Augmented Generation) pipeline for researching about restaurants. Essentially:

1. You give it a csv containing (restaurant name, general location of restaurant) e.g., (East is East, Vancouver Broadway)
2. You give it a series of fields you want the AI to fill out after conducting research (e.g., Menu items, price, address, website, etc)
3. For each restaurant in CSV, the AI autonomously researches that restaurant by (1) making targeted web searches (2) reading the results (3) deciding if it needs more info and do it again (4) reaching a point where it is able to synthesise the findings into an answer
4. The app returns the LLM-filled contents of the requested fields back to you in a uniform JSON structure


# Background

I need an agenetic RAG system that would gather specific info on a bunch of restaurants / places systematically. I tried to build my own, but it ended up working horrible, and fixing it is like stuffing cash into a pocket with a hole in it. 

Luckily, there was a pre-existing RAG system available on Github that I could use -> https://github.com/serpapi/web-research-agent

However, there were two things I need to resolve:

1. This repo used OpenAI (LLM provider) and SerpAPI's (web searching tool provider) APIs. I used Hack Club AI (which is apparently largely compatiable with OpenAI's API) and Serper.dev's API.
2. This repo was meant to be adapted in a conversation-like style. I needed to fetch data in bulk. Hence, I need a system where I can input restaurants and output a list of results featuring specific fields of each restaurant.

...and so that's exactly what I did.

# File structure

Examples.md contain a section of the Task Prompt, this file stores and describes the fields which we want the AI to research and provide per restaurant

(fields.md) is NOT it! (idk why I still have that I think it was just inspirational ideas about what fields to add next?)

full_test_list.md contains a full roster of restaurants organized in the CSV format. Simply paste them under the CSV headers in restaurants.csv

Speaking of restaurants.csv. This is the file the program is expected to intake to know the restaurants. Be careful! The header naming and other restrictions is very strict for restaurants.csv! (See around lines 491 - 509)

issues.md is just commentary for future improvements and current speculations of potential failure. The program I find is sufficiently good such that it can collect data thoroughly, and whenever it breaks re-calling it for a certain restaurant would probably work, so given the limited time and the APs I'm not going to bother touch it (archive.txt is also commentary / archive)

output.json is where the outputted data is stored, after the model researches about the restaurants and comes up with answers.

requirements.txt (duh)

research_agent.py THIS IS THE MAIN SCRPT! See below explanation

# Code structure


+ is big section
" " (nothing) is small section

+ Imports
+ Functions for parsing restaurant.csv
Mechanism and limitations for retrying
Validate empty or corrupted outputs
+ + + core research agent class
  Establish Hackclub LLM endpoint, set API keys
  + Toolbox definition for the agent!
  + Web searching function
    *Function used for searching with Serper.dev API
    + Parsing search results (regular web results, Google answer box, Google knowledge panel, geographically local results)
  + Main loop for the agent
    Logging (debug printing) helper function
    + Main infinite* loop until answer / conclusion reached
    + Check + format LLM tool calls
    *Use function to execute searches in parallel (# of concurrent searches customisable)
    + Results get added back to conversation, LLM reads it, decides what to do, and the main loop loops
    -> OR
    + When LLM is satisfied and decides to not call tools anymore, extract, format, and log the final answer.
  + Command line interface
    + Parse arguments given in command line
    + Helper function to build the task prompt for one specific restaurant
    + Helper function for parsing rows from spreadsheet to extract restaurant name and rough location
    Batch mode (with sheet) vs query mode (singular search)
    Print and save result


  
# How it works (basically)

Question comes -> LLM gets question (conversation history), and tools -> "do I need to use my tools to get more knowledge?"

if LLM called tools:
  Formulate the specific queries
  Perform search with queries
  Add results back to conversation

  LLM gets conversation history and tools again (LOOP)

if LLM doesn't call tools:
  Extract the output and return the final answer to user
  
# How to set it up (deployment)
Since this is a commandline-based program and still requires environment setup, the closest thing to a "deployment" would be to set up the repo on the other person's computer. Hence,

On Windows, open up Powershell

1. `git clone https://github.com/fengyuan66/web-research-agent-main.git`
2. `cd web-research-agent-main` or whatever this directory may be for you
3. `py -3 -m venv .venv`
4. `.venv\Scripts\Activate.ps1`
5. `python -m pip install --upgrade pip`
6. `pip install -r requirements.txt`
7. `setx HACKCLUB_API_KEY "YOUR_HACKCLUB_KEY"` Please put your actual Hack Club AI key in "YOUR_HACKCLUB_KEY"
8. `setx SERPERDEV_API_KEY "YOUR_SERPERDEV_KEY"` Please put your actual Serper.Dev key in "YOUR_SERPERDEV_KEY"
9. Close powershell
10. Open a new powershell in the repo's folder
11. `.venv\Scripts\Activate.ps1`
12. `python research_agent.py --sheet restaurants.csv --spec-file Examples.md -o output.json`, ensuring that restaurants.csv and Examples.md exists and its contents are adjusted to your liking

# How this could be used

I intend on feeding it my list of Vancouver restaurants and using its results to craft a dataset that I can then use to provide context for Voyago's agent, which will learn the user's preference to restaurants in coordination with knowledge of the restaurant's specific traits and thus be able to recommend relevant restaurants to the user.

# Comments guide

In general, THINGS TYPED IN UPPERCASE means to indicate some sort of important variable / customisable element

things typed in lowercase (and sometimes surrounding blocks of code) mainly just point out what's happenning. This is used for maintenance purposes and the divide the code into clear regions


# AI declaration

AI is used mainly for four things in my project:
1. Debugging (adding debugging statements that helped me find where the error was several times during the making, pointing out high-level issues that caused instability in the initial iteration the RAG system)
2. Prompt development (ChatGPT wrote prompts for the LLM because its very good at prompt engineering)
3. Difficult parsing (e.g., sorting info extracted from search into buckets based on their origins for better digestion). Some of these I found to be very tedious relative to its contribution to the program's function, mainly because although there are tutorials online, adapting the parsing to my own use case is a case in itself.
4. I used ChatGPT to help me summarise implementation documentation for particular APIs, namely the Serper.dev (web browsing tool) API.

AI was not used to write this very README!!!

Overall I can confidently say that the amount of my code written by the AI is <30% and used in a purposeful and reasonable manner

# DEMO:

Here is a brief video demo showcasing one runthorugh of the pipeline on a small list of restaurants

https://www.youtube.com/watch?v=_eLFlo78jj0

# How other people can contribute to it?

This pipeline is designed in a way that is universal to many tasks. If you are wishing to use RAG to research cars, for example, you would only need to change the fields and the prompts. You can also experiement with different web-browsing API, LLM API, or prompts to see which one works best for you and share the insight with the community

# One more thing...

Dear HCTG orgs, please note that I am 100% committed to attending HCTG, so if my projects are unable to be approved by May 8th for the 20 hour reduction, pls be soft on the deadline cuz I'll 100% be coming and make the 40 hour total by the later deadline.




### BELOW IS THE OLD REPO'S README!

-----------------------------------------------------------------------------------

### BELOW IS THE OLD REPO'S README!

# Research Agent

LLM-powered researcher that combines OpenAI chat models with Google results via SerpAPI. The agent asks the model to emit all needed searches at once, runs them concurrently, feeds snippets back, and returns a well‑cited answer. Includes a simple CLI.

## Features
- OpenAI Chat Completions with function calling
- Batches 2–50 `search_web` tool calls in one turn
- Concurrent Google searches via SerpAPI
- Optional JSON trace (`--outfile`) with steps and final answer

## Requirements
- Python 3.9+ (3.10+ recommended)
- OPENAI_API_KEY
- SERPAPI_API_KEY

## Install

Assuming you have Python 3.9+ and virtual env installed:

```bash
git clone https://github.com/vladm-serpapi/web-research-agent
cd web-research-agent
pip install -r requirements.txt
```

## Setup API keys
Option A — export in your shell (recommended):
```bash
export OPENAI_API_KEY="sk-..."
export SERPAPI_API_KEY="..."
```
Option B — .env file (don’t commit this file):
```bash
# .env
export OPENAI_API_KEY="sk-..."
export SERPAPI_API_KEY="..."
# load it
source .env
```
Security: Never share or commit your keys.

## Quick start
```bash
python research_agent.py -q "What are the latest approaches to retrieval‑augmented generation in 2025?"
# Save full JSON trace
python research_agent.py -q "State of LLM reasoning benchmarks in 2025" --outfile trace.json
```

## CLI
```bash
python research_agent.py -h
# usage: research_agent.py [-h] -q QUERY [-m {o3,o4-mini,gpt-4o}] [-n TOPN] [-o OUTFILE] [-d]
#   -q, --query        Research question (required)
#   -m, --model        o3 (default) | o4-mini | gpt-4o
#   -n, --topn         Organic results per search (default: 10)
#   -o, --outfile      Write JSON trace to file
#   -d, --debug        Print debug logs
```

## How it works (brief)
- System prompt asks the model to emit all `search_web` calls first
- Agent executes all requested Google searches concurrently (SerpAPI)
- Results are passed back as tool messages; model produces a final, cited answer
- Note on model tool behavior: o3 / o4-mini reasoning models prefer to output single tool call per prompt, so gpt-4o is preferred when many queries are required

## Examples
```bash
python research_agent.py -q "Compare FAISS vs. Milvus vs. Qdrant for RAG (2025)" -m o3 -n 8 -o rag_db_trace.json
```

### With debug mode
```bash
 python research_agent.py -q "airlines industry trend 2025, compare multiple trends by impact and research each deeper to provide a comphrehensive picture" --outfile trace.json --debug --model gpt-4o
```

### Sample output

```bash
 python research_agent.py -q "research the nuclear energy sector in 2025 and build a comprehensive thesis / report on it. I want this 
report to cover AI, uranium, energy, etc. Financial projections, key players, companies, etc. Do the research in iterative fashion, after each round of searches and getting new info
rmation, do another round of searches to dive deeper into each specific topic. Don't stop on surface findings. Think and analyze what data are you missing, and proceed to research it deeper." --outfile trace.json --debug --model gpt-4o
[DEBUG] → OpenAI chat.completions.create request …
[DEBUG] → SerpAPI query: 'nuclear energy sector 2025 overview'
[DEBUG] → SerpAPI query: 'AI in nuclear energy 2025'
[DEBUG] → SerpAPI query: 'uranium market 2025'
[DEBUG] → SerpAPI query: 'key companies in nuclear energy 2025'
[DEBUG] → OpenAI chat.completions.create request …
[DEBUG] → SerpAPI query: 'financial projections nuclear energy 2025'
[DEBUG] → SerpAPI query: 'nuclear energy policies 2025'
[DEBUG] → SerpAPI query: 'AI-driven nuclear technologies 2025'
[DEBUG] → SerpAPI query: 'key innovations in nuclear technology 2025'
[DEBUG] → OpenAI chat.completions.create request …
…
```

## JSON trace example (with --outfile)
```json
{
  "question": "...",
  "answer": "...",
  "steps": [
    { "type": "tool_call", "query": "first search" },
    { "type": "tool_result", "content": "- Title: snippet ..." },
    { "type": "assistant_answer", "content": "final answer text" }
  ]
}
```

## Programmatic use
```python
from research_agent import ResearchAgent

agent = ResearchAgent(model="o3", topn=10, debug=False)
result = agent.run("Summarize the most cited papers on RAG.")
print(result["answer"])  # final answer
print(len(result["steps"]))
```

## Troubleshooting
- "OPENAI_API_KEY and SERPAPI_API_KEY must be set." → export both keys or source your .env
- Model not available → switch to a supported one (o3, o4-mini, gpt-4o)
- Empty/failed searches → check SerpAPI key/quota and network settings

## License
MIT License — see LICENSE.