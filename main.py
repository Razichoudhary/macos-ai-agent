import os
import re
import json
import sys
import select
try:
    import readline
except ImportError:
    pass

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

from rich.console import Console   
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.text import Text
from rich.theme import Theme

from tools import search_tool, wiki_tool, save_to_txt
from desktop_tools import desktop_tools, try_direct_routing

load_dotenv()

# Initialize Rich Console with customized aesthetic styling
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "bold yellow",
    "danger": "bold red",
    "success": "bold green",
    "primary": "bold bright_cyan",
    "accent": "bold magenta",
})
console = Console(theme=custom_theme)

# Structured agent response schema
class ResearchResponse(BaseModel):
    topic: str = Field(description="The subject researched or the action/task requested")
    summary: str = Field(description="A thorough summary of research findings or confirmation of actions performed")
    sources: list[str] = Field(default_factory=list, description="List of sources, websites, or applications cited or manipulated")
    tools_used: list[str] = Field(default_factory=list, description="List of tools utilized to accomplish the task")

# LLM setup using high-speed, high-rate-limit flash lite model
model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
llm = ChatGoogleGenerativeAI(model=model_name, max_retries=2)

# Output parser for Pydantic schema
parser = PydanticOutputParser(pydantic_object=ResearchResponse)

# Prompt with system instructions for research, memory, and desktop automation
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert AI Assistant and Desktop Automation Agent running on macOS.\n"
            "You have access to two categories of tools:\n"
            "1. Research Tools: 'search' (DuckDuckGo web search) and 'wikipedia' (encyclopedic summaries).\n"
            "2. macOS Desktop & System Tools:\n"
            "   - 'open_app', 'close_app', 'open_file_or_folder', 'open_website'\n"
            "   - 'play_youtube_video', 'open_youtube_video'\n"
            "   - 'create_note_file' (write files to Desktop), 'read_desktop_file' (read files from Desktop)\n"
            "   - 'send_email', 'send_or_compose_email' (automatically sends emails via Gmail)\n"
            "   - 'set_system_volume', 'mute_system_sound', 'take_screenshot', 'get_battery_status'\n"
            "   - 'toggle_dark_mode', 'manage_clipboard', 'show_system_notification', 'get_system_specs', 'speak_text'\n\n"
            "Guidelines:\n"
            "- CONVERSATION MEMORY: Refer to previous messages in the chat history when handling follow-up requests "
            "(e.g. 'save that to a note', 'read that note', 'send that summary in an email', 'what did you find earlier?').\n"
            "- CRITICAL APP & SERVICE DISTINCTIONS (Never confuse similar apps or services):\n"
            "  * 'mail' vs 'gmail': 'mail' (or 'apple mail', 'mac mail') refers to the native macOS Mail desktop application (Mail.app). 'gmail' (or 'google mail') refers to Google's webmail service (mail.google.com). If the user asks for 'mail', open Mail.app via open_app('mail'). If the user asks for 'gmail', open Gmail via open_app('gmail').\n"
            "  * 'antigravity' vs 'antigravity IDE': 'antigravity IDE' is the desktop IDE development environment (/Applications/Antigravity IDE.app). 'antigravity' can refer to Python's antigravity module/Google Gravity easter egg, or the IDE. When asked for 'antigravity ide' or 'antigravity', pass the exact name to 'open_app'.\n"
            "  * 'calendar' vs 'google calendar': 'calendar' is the macOS native Calendar app; 'google calendar' is the web service.\n"
            "  * 'notes' vs 'stickies' vs 'google keep' vs 'notion': 'notes' is macOS Notes.app; 'stickies' is Stickies.app; 'keep' is Google Keep.\n"
            "  * 'music' vs 'spotify' vs 'youtube music': 'music' is Apple Music (Music.app); 'spotify' is Spotify; 'youtube music' is YouTube Music.\n"
            "  * 'maps' vs 'google maps': 'maps' is Apple Maps (Maps.app); 'google maps' is Google Maps.\n"
            "  * 'photos' vs 'google photos': 'photos' is Apple Photos (Photos.app); 'google photos' is Google Photos.\n"
            "  * 'code' / 'vs code' vs 'antigravity ide' vs 'xcode': These are distinct programming IDEs/editors.\n"
            "- If the user asks to open, play, or watch a video or channel content on YouTube "
            "(e.g. 'open youtube apna college python course', 'play lofi music on youtube', 'open video python course on youtube'), "
            "ALWAYS invoke 'play_youtube_video' with the query. It will automatically find the exact video and play it directly in the browser.\n"
            "- If the user asks to open generic apps or websites (e.g. 'open calculator', 'open safari', 'open youtube', 'open mail', 'open gmail', 'open antigravity ide'), invoke 'open_app' or 'open_website'.\n"
            "- If the user asks to write, send, or email someone (e.g. 'send email to ...', 'email ...', 'send an email via gmail'), invoke 'send_email'. It will automatically transmit and send the email. Confirm clearly in your summary that the email has been automatically sent.\n"
            "- If the user asks an informational or research question, invoke the appropriate research tool.\n"
            "- Once the action is performed or research gathered, provide your final response ONLY as a JSON object matching this schema:\n"
            "{format_instructions}\n"
            "Return valid JSON only. Do not add markdown or conversational explanation outside the JSON."
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

# Create tool-calling agent combining research tools and desktop automation tools
agent_tools = [search_tool, wiki_tool] + desktop_tools
agent = create_tool_calling_agent(
    llm=llm,
    prompt=prompt,
    tools=agent_tools,
)

# Agent executor with iteration cap and error resilience (clean output without raw dumps)
agent_executor = AgentExecutor(
    agent=agent,
    tools=agent_tools,
    verbose=False,
    handle_parsing_errors=True,
    max_iterations=6,
    early_stopping_method="generate",
)

class RichToolCallbackHandler(BaseCallbackHandler):
    """Displays real-time sleek tool execution notices in the Rich terminal."""
    def __init__(self, rich_console: Console):
        self.console = rich_console

    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get("name", "Tool")
        clean_inp = str(input_str).strip()
        if len(clean_inp) > 55:
            clean_inp = clean_inp[:52] + "..."
        self.console.print(f"  [dim cyan]⚙️  Invoking Tool:[/dim cyan] [bold bright_cyan]{tool_name}[/bold bright_cyan] [dim]({clean_inp})[/dim]")

    def on_tool_error(self, error, **kwargs):
        self.console.print(f"  [bold red]⚠️  Tool Error:[/bold red] [dim]{error}[/dim]")

def extract_text_content(output) -> str:
    """Extract string content from strings or Gemini content-block lists."""
    if isinstance(output, str):
        return output
    if isinstance(output, list):
        texts = []
        for block in output:
            if isinstance(block, dict) and "text" in block:
                texts.append(block["text"])
            elif isinstance(block, str):
                texts.append(block)
        return "\n".join(texts)
    if hasattr(output, "content"):
        return extract_text_content(output.content)
    return str(output)

def parse_research_response(raw_output: str, query: str = "") -> ResearchResponse:
    """Extract JSON and parse into ResearchResponse with resilient fallbacks."""
    cleaned = raw_output.strip()

    # 1. Try to extract from markdown code blocks: ```json { ... } ``` or ``` { ... } ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
    else:
        # 2. Try to find the outermost JSON object { ... }
        json_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        json_str = json_match.group(1).strip() if json_match else cleaned

    # Try Pydantic parser first
    try:
        return parser.parse(json_str)
    except Exception:
        pass

    # Fallback A: standard json.loads
    try:
        data = json.loads(json_str)
        return ResearchResponse(
            topic=data.get("topic", query or "Task / Query"),
            summary=data.get("summary", json_str),
            sources=data.get("sources", []),
            tools_used=data.get("tools_used", [])
        )
    except Exception:
        pass

    # Fallback B: If Gemini returned pure text, construct ResearchResponse gracefully
    return ResearchResponse(
        topic=query or "Task / Query",
        summary=cleaned,
        sources=[],
        tools_used=[]
    )

def display_action_result(response: ResearchResponse, is_direct: bool = False):
    """Renders the response inside a styled Rich Panel with formatted Markdown and metadata."""
    badge = "[bold bright_green]⚡ Instant Direct Router (<50ms)[/bold bright_green]" if is_direct else "[bold bright_cyan]🧠 Gemini Flash Agent[/bold bright_cyan]"

    sources_str = ", ".join(response.sources) if response.sources else "None"
    tools_str = ", ".join(response.tools_used) if response.tools_used else "None"

    footer_text = Text()
    footer_text.append(f"Sources / Apps: {sources_str}\n", style="dim italic")
    footer_text.append(f"Tools Used:     {tools_str}", style="dim italic")

    content = Markdown(response.summary)

    panel = Panel(
        content,
        title=f"[bold bright_white]{response.topic}[/bold bright_white]  •  {badge}",
        subtitle=footer_text,
        border_style="bright_green" if is_direct else "bright_blue",
        padding=(1, 2),
    )
    console.print()
    console.print(panel)

    # Automatically save output cleanly to research_output.txt
    file_content = (
        f"Topic / Task: {response.topic}\n\n"
        f"Summary:\n{response.summary}\n\n"
        f"Sources / Apps: {sources_str}\n"
        f"Tools Used: {tools_str}"
    )
    save_status = save_to_txt(file_content)
    console.print(f"[dim green]💾 {save_status}[/dim green]\n")

def print_welcome_banner():
    """Prints a modern, vibrant header banner with capabilities and tips."""
    banner_text = Text()
    banner_text.append("MacOS AI Agent — Autonomous Desktop Assistant & Research Engine\n", style="bold bright_cyan")
    banner_text.append("⚡ Sub-50ms Instant Execution  •  🧠 Multi-Turn Memory  •  🔍 Live Web Intelligence", style="dim italic white")

    console.print(Panel(
        banner_text,
        border_style="bright_cyan",
        padding=(1, 2)
    ))
    console.print("[dim]Type [bold white]'help'[/bold white] for command reference, [bold white]'/clear'[/bold white] to reset conversation memory, or [bold white]'exit'[/bold white] to quit.[/dim]\n")

def print_help_table():
    """Prints a styled Rich table with command categories and examples."""
    table = Table(title="🤖 Agent Capabilities & Quick Reference", border_style="bright_blue", header_style="bold bright_cyan")
    table.add_column("Category", style="bold white", width=18)
    table.add_column("Capabilities / Features", style="dim", width=28)
    table.add_column("Example Commands", style="cyan", width=34)
    table.add_column("Speed", style="green", width=12)

    table.add_row(
        "⚡ System Controls",
        "Volume, mute, battery, dark mode, specs, screenshot",
        "'battery', 'specs', 'volume 45%', 'dark mode', 'screenshot'",
        "⚡ <50ms"
    )
    table.add_row(
        "🖥️ App & Window",
        "Open/close macOS apps & web apps",
        "'open calculator', 'close safari', 'open mail' vs 'open gmail'",
        "⚡ <50ms"
    )
    table.add_row(
        "📋 Clipboard & Audio",
        "Clipboard copy/paste, text-to-speech",
        "'copy Code to clipboard', 'clipboard', 'say Hello world'",
        "⚡ <50ms"
    )
    table.add_row(
        "🎬 YouTube & Media",
        "Direct search & playback of specific videos",
        "'play lofi music on youtube', 'open youtube apna college python'",
        "🧠 Agent"
    )
    table.add_row(
        "✉️ Email & Files",
        "Automated Gmail delivery, read/write files",
        "'send email to test@domain.com', 'create note on Desktop'",
        "🧠 Agent"
    )
    table.add_row(
        "🔍 Deep Research",
        "Live web search (DDG), Wikipedia facts",
        "'Search latest AI breakthroughs', 'What is CRISPR?'",
        "🧠 Agent"
    )
    table.add_row(
        "🧠 Context Memory",
        "Remembers previous research & tasks",
        "'Save that summary to a note file on Desktop'",
        "🧠 Agent"
    )

    console.print()
    console.print(table)
    console.print()

def get_user_query(prompt_text: str = "\n[bold bright_blue]You ▶ [/bold bright_blue]") -> str:
    """Reads user input cleanly, gracefully handling pasted multi-line text, 
    carriage returns, and terminal bracketed paste escape sequences."""
    try:
        first_line = console.input(prompt_text)
    except (EOFError, KeyboardInterrupt):
        return "exit"

    lines = [first_line]

    # If the user pasted multi-line text, read the remaining buffered lines from stdin
    try:
        while select.select([sys.stdin], [], [], 0.05)[0]:
            extra = sys.stdin.readline()
            if extra:
                lines.append(extra)
            else:
                break
    except Exception:
        pass

    full_input = "\n".join(lines).strip()

    # Clean bracketed paste escape sequences (\x1b[200~ ... \x1b[201~)
    cleaned = re.sub(r"\x1b\[20[01]~", "", full_input)

    # Normalize carriage returns and line endings into spaces for unified prompt
    cleaned = cleaned.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")

    return cleaned.strip()

# Maximum rolling history messages (5 complete turns)
MAX_HISTORY_MESSAGES = 10

def execute_query(query: str, chat_history: list = None):
    """Executes a single user query or desktop automation command with speed routing and memory."""
    if chat_history is None:
        chat_history = []
    # 1. Check sub-50ms instant direct router first
    direct_result = try_direct_routing(query)
    if direct_result:
        structured_response = ResearchResponse(
            topic=direct_result.get("topic", query),
            summary=direct_result.get("summary", ""),
            sources=direct_result.get("sources", []),
            tools_used=direct_result.get("tools_used", ["Instant Direct Router"])
        )
        display_action_result(structured_response, is_direct=True)

        # Update conversation memory with this interaction
        chat_history.append(HumanMessage(content=query))
        chat_history.append(AIMessage(content=structured_response.summary))
        if len(chat_history) > MAX_HISTORY_MESSAGES:
            del chat_history[:len(chat_history) - MAX_HISTORY_MESSAGES]
        return

    # 2. Complex or reasoning query -> Route to Gemini Agent with multi-turn memory
    with console.status("[bold bright_cyan]Agent coordinating tools & reasoning...[/bold bright_cyan]", spinner="dots"):
        callback = RichToolCallbackHandler(console)
        try:
            raw_response = agent_executor.invoke(
                {"query": query, "chat_history": chat_history},
                config={"callbacks": [callback]}
            )
            raw_text = extract_text_content(raw_response.get("output", ""))
        except Exception as e:
            console.print(f"[bold red]❌ Error executing agent:[/bold red] {e}")
            return

    try:
        structured_response = parse_research_response(raw_text, query=query)
        display_action_result(structured_response, is_direct=False)

        # Update conversation memory
        chat_history.append(HumanMessage(content=query))
        chat_history.append(AIMessage(content=structured_response.summary))
        if len(chat_history) > MAX_HISTORY_MESSAGES:
            del chat_history[:len(chat_history) - MAX_HISTORY_MESSAGES]
    except Exception as e:
        console.print(f"[bold red]❌ Unexpected error formatting response:[/bold red] {e}")
        console.print("[dim]Raw Response:[/dim]\n", raw_text)

def main():
    print_welcome_banner()
    chat_history = []

    while True:
        try:
            query = get_user_query()
            if not query:
                continue

            clean_q = query.lower().strip()
            if clean_q in ("exit", "quit", "q"):
                console.print("\n[bold bright_cyan]Goodbye! Have a productive day.[/bold bright_cyan]\n")
                break

            if clean_q in ("help", "/help", "?"):
                print_help_table()
                continue

            if clean_q in ("/clear", "clear memory", "reset", "reset memory"):
                chat_history.clear()
                console.print("[italic bright_green]✨ Conversation memory has been cleared.[/italic bright_green]\n")
                continue

            execute_query(query, chat_history)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold bright_cyan]Session ended. Goodbye![/bold bright_cyan]\n")
            break

if __name__ == "__main__":
    main()
