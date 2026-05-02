#!/usr/bin/env python3
import typing as t
import argparse, json, os
import csv
import re
import time
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI


#(Old!) stripping Qwen3's thinking blocks from results
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
def strip_thinking(text: str) -> str:
    return _THINK_RE.sub("", text).strip()








# restaurant parsing functions
def load_spec_text(spec_path: Path) -> str:
    if not spec_path.exists():
        raise RuntimeError(f"Spec file not found: {spec_path}")
    spec = spec_path.read_text(encoding="utf-8").strip()
    if not spec:
        raise RuntimeError(f"Spec file is empty: {spec_path}")
    return spec


def load_restaurant_sheet(sheet_path: Path) -> list[dict[str, str]]:
    if not sheet_path.exists():
        raise RuntimeError(f"Sheet file not found: {sheet_path}")
    suf = sheet_path.suffix.lower()
    if suf not in {".csv", ".tsv"}:
        raise RuntimeError("Only .csv and .tsv are supported in this minimal version.")

    with sheet_path.open("r", encoding="utf-8-sig", newline="") as f:
        if suf == ".tsv":
            reader = csv.DictReader(f, dialect=csv.excel_tab)
        else:
            sample = f.read(2048); f.seek(0)
            reader = csv.DictReader(f, dialect=csv.Sniffer().sniff(sample or "a,b\n1,2\n", delimiters=",;\t"))
        return [{str(k).strip().lower(): (v or "").strip() for k, v in row.items() if k} for row in reader]


def extract_first_json_object(text: str) -> t.Optional[dict[str, t.Any]]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned)
    for candidate in (cleaned, re.search(r"\{.*\}", cleaned, re.DOTALL).group(0) if re.search(r"\{.*\}", cleaned, re.DOTALL) else None):
        if not candidate:
            continue
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    return None
# restaurant parsing functions










def run_with_retries(
    agent: "ResearchAgent",
    task: str,
    step_callback: t.Optional[t.Callable[[dict], None]] = None,

    
    max_attempts: int = 3, # MAX ATTEMPTS VARIABLE HERE


    base_backoff_seconds: float = 1.0,
    validate_result: t.Optional[t.Callable[[dict[str, t.Any]], None]] = None,
) -> dict[str, t.Any]:
    
    

    last_err: t.Optional[Exception] = None
    current_task = task
    for attempt in range(1, max_attempts + 1):
        try:
            result = agent.run(current_task, step_callback=step_callback)
            if validate_result:
                validate_result(result)
            return result
        except Exception as err:
            last_err = err
            # If the model returns empty/invalid output, tighten the instruction for next attempt
            if "Empty model output" in str(err) or "not a valid JSON object" in str(err):
                current_task = (
                    task
                    + "\n\nIMPORTANT: Return exactly one valid JSON object now. "
                    + "No prose, no markdown, no code fences."
                )

            if attempt >= max_attempts:
                break

            #backoff times will increase exponentially with every retry
            sleeptimer = base_backoff_seconds * (2 ** (attempt - 1))


            # debugging
            if agent.debug:
                print(f"[DEBUG] row attempt {attempt}/{max_attempts} failed: {err}; retrying in {sleeptimer:.1f}s")
            time.sleep(sleeptimer)
    raise RuntimeError(f"Restaurant processing failed after {max_attempts} attempts: {last_err}")


def validate_nonempty_json_answer(result: dict[str, t.Any]) -> None:
    answertxt = str(result.get("answer") or "").strip()
    if not answertxt:
        raise ValueError("Empty model output")
    if extract_first_json_object(answertxt) is None:
        raise ValueError("Model output is not valid JSON")






# Important bit starts here...




class ResearchAgent:


    HACKCLUB_URL = "https://ai.hackclub.com/proxy/v1"

    def __init__(
        self,
        model: str = "meta-llama/llama-3.1-70b-instruct",
        topn: int = 10,
        debug: bool = False,
        hackclub_key: t.Optional[str] = None,
        serperdev_key: t.Optional[str] = None,
    ) -> None:
        
        self.model = model
        self.topn = topn
        self.debug = debug

        self.openai_key = hackclub_key or os.getenv("HACKCLUB_API_KEY")
        self.serperdev_key = serperdev_key or os.getenv("SERPERDEV_API_KEY")
        
        if not self.openai_key or not self.serperdev_key:
            raise RuntimeError("HACKCLUB_API_KEY and SERPERDEV_API_KEY must be set.")

        self.client = OpenAI(api_key=self.openai_key,
        base_url = self.HACKCLUB_URL,                     
        )

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": (
                        "Search Google and return the top result snippets. "
                        "Use concise, targeted queries. "
                        "You may call this multiple times in a single turn to cover different angles of the question simultaneously."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Specific Google search string",
                            }
                        },
                        "required": ["query"],
                    },
                },
            }
            
        ]
        

#---------------------------------------- SYSTEM PROMPT HERE

        self._sys_prompt = (
            "You are a meticulous research assistant with access to real-time web search.\n\n"
            "STRATEGY:\n"
            "1. Before reading ANY results, emit ALL your search_web tool calls in a "
            "SINGLE response — batch 2 to 15 targeted searches covering different angles.\n"
            "2. Use specific, varied queries — not just rephrasing the same question.\n"
            "3. Only after ALL search results are returned, synthesize a comprehensive, "
            "well-cited answer.\n\n"
            "ANSWER FORMAT:\n"
            "- Use clear headings (##) to structure multi-part answers\n"
            "- Cite sources inline as [Title](URL) markdown links\n"
            "- Be direct and thorough; end with a short summary for complex topics\n"
            "/no_think"
        )
        self.sys_prompt = self._sys_prompt

#------------------------------------------


    def search_web(self, query: str) -> str:
        if self.debug:
            print(f"[DEBUG] → SerperAPI query: '{query}'")
        try:
            resp = requests.post(
                url = "https://google.serper.dev/search",
                headers = {
                    "X-API-KEY": self.serperdev_key,
                    "Content-Type": "application/json",
                },

                json={"q": query, "num": self.topn},

                #WEB SEARCHING API TIMEOUT VARIABLE HERE

                timeout = 7, 
            )

            resp.raise_for_status()
            data = resp.json()

        except Exception as err:
            return f"Search error: {err}"
        
        lines: list[str] = []






    # THE FOLLOWING SEARCH RESULT PARSING SECTION IS LARGELY GENERATED BY AI TO FORMAT AND CATEGORISE PULLED RESULTS

        ab = data.get("answerBox") or data.get("answer_box") or {}
        if isinstance(ab, dict) and ab:
            text = (
                ab.get("answer")
                or ab.get("snippet")
                or ab.get("snippetHighlighted")
                or ""
            )
            if text:
                link = ab.get("link") or ab.get("source") or ""
                lines.append(
                    f"- [FEATURED - {ab.get('title', 'Answer')}]"
                    f"({link}): {text}"
                )

        kg = data.get("knowledgeGraph") or data.get("knowledge_graph") or {}
        if isinstance(kg, dict) and kg:
            desc = kg.get("description", "")
            attrs = kg.get("attributes", {})
            extras = [f"{k}: {v}" for k, v in attrs.items()] if isinstance(attrs, dict) else []
            detail = " | ".join(filter(None, [desc] + extras))
            if detail:
                link = kg.get("website") or kg.get("descriptionLink") or ""
                lines.append(
                    f"- [KNOWLEDGE PANEL - {kg.get('title', 'Entity')}]"
                    f"({link}): {detail}"
                )

        # 3) Organic web results.
        # Serper docs show `organic`; keep `organic_results` fallback.
        organic = data.get("organic") or data.get("organic_results") or []
        for r in organic[: self.topn]:
            lines.append(
                f"- [{r.get('title', '(untitled)')}]({r.get('link', '')}): "
                f"{r.get('snippet', '(no snippet)')}"
            )

        # 4) Local business / maps pack.
        # Serper docs show `places`; keep SerpAPI-style `local_results` fallback.
        places = data.get("places") or []
        if not places:
            local_results = data.get("local_results") or {}
            if isinstance(local_results, dict):
                places = local_results.get("places") or []
            elif isinstance(local_results, list):
                places = local_results

        for r in places[: self.topn]:
            rating = r.get("rating", "")
            reviews = r.get("ratingCount", "")
            address = r.get("address", "")
            phone = r.get("phoneNumber", "")
            parts = [
                x
                for x in [
                    f"Rating: {rating}" + (f" ({reviews} reviews)" if reviews else "") if rating else "",
                    address,
                    phone,
                ]
                if x
            ]
            link = r.get("website") or r.get("link") or ""
            lines.append(
                f"- [{r.get('title', '(untitled)')}]({link}): "
                f"{' | '.join(parts)}"
            )

        if not lines:
            available = [k for k in data if k != "searchParameters"]
            return f"No results found. (Serper returned keys: {available})"

        return "\n".join(lines)
    
    #END RESULT CATEGORISATION SECTION

    




    def run(self, question: str, step_callback: t.Optional[t.Callable[[dict], None]] = None,) -> dict[str, t.Any]:



        messages = [
            {"role": "system", "content": self.sys_prompt},
            {"role": "user", "content": question},
        ]


        step_history: list[dict] = []
        steps = step_history

        def log(step: dict):
            step_history.append(step)
            if step_callback:
                step_callback(step)



        while True:
            if self.debug:
                print(f"[DEBUG] API request for model {self.model}")


            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
            )
            msg = resp.choices[0].message

            if msg.tool_calls:
                # append assistant message FIRST (per API contract)
                tool_calls = []
                for tc in msg.tool_calls:
                    tool_call_dict = {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    tool_calls.append(tool_call_dict)

                messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": tool_calls,
                })

                log({"type": "batch_start", "count": len(msg.tool_calls)})

                # fetch all tools from the tool call concurrently
                def fetch(call):
                    try:
                        args = json.loads(call.function.arguments)
                    
                    except json.JSONDecodeError:
                        args = {}
                    query = args.get("query", "")

                    log({"type": "tool_call", "query": query})
                    


                    result = self.search_web(query)
                    result_count = len([l for l in result.split("\n") if l.strip().startswith("-")])

                    log({"type": "tool_result", "query": query, "content": result, "result_count": result_count})

                    steps.append({"type": "tool_call", "query": query})
                    return call.id, result




                # CUSTOMISE PARAMETER FOR # OF CONCURRENT SEARCHES
                MAX_CONCURRENT_SEARCHES = 5
                with ThreadPoolExecutor(max_workers=min(len(msg.tool_calls), MAX_CONCURRENT_SEARCHES)) as pool:
                    results = list(pool.map(fetch, msg.tool_calls))




                #if there's still more tool calls, append them back
                for call_id, result in results:
                    steps.append({"type": "tool_result", "content": result})
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call_id,
                            "content": result,
                        }
                    )
                continue
            
           
            #if final answer is reached, no more tool calling
            raw = msg.content or ""
            answer = strip_thinking(raw)

            steps.append({"type": "assistant_answer", "content": answer})
            
            log({"type": "assistant_answer", "content": answer})

            result: dict[str, t.Any] = {"question": question, "answer": answer, "steps": steps}
            return result





# -------------------------------------------------------------------------
# CLI wrapper
# -------------------------------------------------------------------------

def _cli():
    p = argparse.ArgumentParser(description="ResearchAgent CLI")
    p.add_argument("-q", "--query")

    p.add_argument("--sheet", type=Path)
    p.add_argument("--spec-file", type=Path, default=Path("Examples.md"))
    
    p.add_argument("-m", "--model", default="meta-llama/llama-3.1-70b-instruct")
    p.add_argument("-n", "--topn", type=int, default=10)
    p.add_argument("-o", "--outfile", type=Path)
    p.add_argument("-d", "--debug", action="store_true")
    cfg = p.parse_args()

    if cfg.debug:
        def step_callback(step):
            pass
    else:
        step_callback = None

    agent = ResearchAgent(model=cfg.model, topn=cfg.topn, debug=cfg.debug)



    #TASK PROMPT CONSTRUCTION
    def build_research_task(name: str, location: str, spec: str)-> str:
        
        return ("Research this restaurant.\n"
        f"Restaurant name: {name}\n"
        f"Approximate location tag: {location}\n"
        "Follow the output spec exactly as written below.\n\n"
        f"{spec}\n\n"
        "Return only the final answer in the format required by the spec.")
        




    def process_restaurant_row(
            agent,
            row: dict,
            spec_text: str,
            step_callback
    ) -> dict:
    #Possible headers for restaurants
        name = (
                row.get("restaurant")
                or row.get("restaurant_name")
                or row.get("name")
                or row.get("business")
        )

    #Possible headers for locations

        location = (
                row.get("location")
                or row.get("location_tag")
                or row.get("approx_location")
                or row.get("area")
                or row.get("neighborhood")
                or row.get("tag")
                or ""
        )

        task = build_research_task(name, location, spec_text)

        try:
            item_result = run_with_retries(
                agent,
                task,
                step_callback = step_callback,
                validate_result = validate_nonempty_json_answer
            )

            parsed = extract_first_json_object(item_result["answer"])
            if parsed is not None:
                result_value = parsed
            else:
                result_value = item_result["answer"]

            return {
                "restaurant_name": name,
                "location": location,
                "status": "good",
                "result": result_value,
                "raw_answer": item_result["answer"]
            }
        except Exception as err:
            return{
                "restaurant_name": name,
                "location": location,
                "status": "failed!",
                "error": str(err),
                "result": None,
                "raw_answer": "  RAW ANSWER ERR  "

            }



    #restaurant addition
    if cfg.sheet:

        spec_text = load_spec_text(cfg.spec_file)
        rows = load_restaurant_sheet(cfg.sheet)
        if not rows:
            raise RuntimeError(f"No data rows found in sheet: {cfg.sheet}")

        all_results: list[dict[str, t.Any]] = []
        
        for row in rows:
            result = process_restaurant_row(agent, row, spec_text, step_callback)
            all_results.append(result)


        result = {
            "mode": "restaurant_sheet",
            "sheet": str(cfg.sheet),
            "spec_file": str(cfg.spec_file),
            "count": len(all_results),
            "results": all_results,
        }


    else:
        if not cfg.query:
            p.error("Provide either --query or --sheet")
        result = agent.run(cfg.query, step_callback=step_callback)
    # restaurant addition



    
    print("" + "=" * 80)
    print(result["answer"] if "answer" in result else json.dumps(result, indent=2))
    print("=" * 80)

    if cfg.outfile:
        cfg.outfile.write_text(json.dumps(result, indent=2))
        print(f"Saved full trace → {cfg.outfile}")


if __name__ == "__main__":
    _cli()
