# RestaurantRAG README

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
    + Helper function for parsing one row from spreadsheet to extract restaurant name and rough location
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
  


# Comments

In general, THINGS TYPED IN UPPERCASE means to indicate some sort of important variable / customisable element

things typed in lowercase (and sometimes surrounding blocks of code) mainly just point out what's happenning. This is used for maintenance purposes and the divide the code into clear regions


# AI usage

pls read AI usage. Overall I can confidently say that the amount of functional code written by the AI is within 30% and used at least in a purposeful and reasonable manner






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