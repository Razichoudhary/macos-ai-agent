from datetime import datetime
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import Tool

# DuckDuckGo search tool
search = DuckDuckGoSearchRun()

def safe_search(query: str) -> str:
    """Safely execute web search with error handling."""
    try:
        return search.run(query)
    except Exception as e:
        return f"Web search could not retrieve results: {e}"

search_tool = Tool(
    name="search",
    func=safe_search,
    description="Search the web for current information, news, and facts.",
)
search_tools = search_tool  # Alias for backward compatibility

# Wikipedia search tool (optimized for speed and concise context)
wikipedia_api = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=1200)
wikipedia_run = WikipediaQueryRun(api_wrapper=wikipedia_api)

def safe_wikipedia(query: str) -> str:
    """Safely query Wikipedia with error handling."""
    try:
        return wikipedia_run.run(query)
    except Exception as e:
        return f"Wikipedia query could not retrieve results: {e}"

wiki_tool = Tool(
    name="wikipedia",
    func=safe_wikipedia,
    description="Search Wikipedia for encyclopedic background, scientific articles, and detailed facts.",
)

# Save to file tool
def save_to_txt(data: str, filename: str = "research_output.txt") -> str:
    """Save structured research data or summary to a text file with timestamp."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_text = f"--- Research Output ---\nTimestamp: {timestamp}\n\n{data}\n\n"
        with open(filename, "a", encoding="utf-8") as f:
            f.write(formatted_text)
        return f"Output successfully saved to {filename}"
    except Exception as e:
        return f"Failed to save output to file: {e}"

save_tool = Tool(
    name="save_text_to_file",
    func=save_to_txt,
    description="Save research data, summary, or report to a text file.",
)

# Only give research gathering tools to the LLM agent
tools = [search_tool, wiki_tool]

