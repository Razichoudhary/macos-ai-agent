import os
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

custom_theme = Theme({
    "info": "dim cyan",
    "warning": "bold yellow",
    "danger": "bold red",
    "success": "bold green",
    "primary": "bold bright_cyan",
    "accent": "bold magenta",
})

def create_mac_terminal_html(rich_html_snippet: str, title: str = "MacOS AI Agent — zsh") -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    margin: 0;
    padding: 30px;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }}
  .window {{
    width: 950px;
    background: #0d1117;
    border-radius: 14px;
    box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.1);
    overflow: hidden;
  }}
  .titlebar {{
    background: #161b22;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }}
  .dots {{
    display: flex;
    gap: 8px;
  }}
  .dot {{
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }}
  .dot-red {{ background: #ff5f56; border: 1px solid #e0443e; }}
  .dot-yellow {{ background: #ffbd2e; border: 1px solid #dea123; }}
  .dot-green {{ background: #27c93f; border: 1px solid #1aab29; }}
  .title {{
    flex: 1;
    text-align: center;
    color: #8b949e;
    font-size: 13px;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    font-weight: 500;
    margin-right: 40px;
  }}
  .terminal-body {{
    padding: 24px;
    font-family: 'JetBrains Mono', 'Fira Code', 'Menlo', 'Monaco', monospace;
    font-size: 13.5px;
    line-height: 1.45;
  }}
</style>
</head>
<body>
  <div class="window">
    <div class="titlebar">
      <div class="dots">
        <div class="dot dot-red"></div>
        <div class="dot dot-yellow"></div>
        <div class="dot dot-green"></div>
      </div>
      <div class="title">{title}</div>
    </div>
    <div class="terminal-body">
      {rich_html_snippet}
    </div>
  </div>
</body>
</html>
"""

def generate_shots():
    # -------------------------------------------------------------
    # Screenshot 1: Welcome Banner + Help Capabilities Table
    # -------------------------------------------------------------
    c1 = Console(theme=custom_theme, record=True, width=95)
    
    banner_text = Text()
    banner_text.append("MacOS AI Agent — Autonomous Desktop Assistant & Research Engine\n", style="bold bright_cyan")
    banner_text.append("⚡ Sub-50ms Instant Execution  •  🧠 Multi-Turn Memory  •  🔍 Live Web Intelligence", style="dim italic white")

    c1.print(Panel(
        banner_text,
        border_style="bright_cyan",
        padding=(1, 2)
    ))
    c1.print("[dim]Type [bold white]'help'[/bold white] for command reference, [bold white]'/clear'[/bold white] to reset conversation memory, or [bold white]'exit'[/bold white] to quit.[/dim]\n")

    table = Table(title="🤖 Agent Capabilities & Quick Reference", border_style="bright_blue", header_style="bold bright_cyan")
    table.add_column("Category", style="bold white", width=18)
    table.add_column("Capabilities / Features", style="dim", width=28)
    table.add_column("Example Commands", style="cyan", width=34)
    table.add_column("Speed", style="green", width=10)

    table.add_row("⚡ System Controls", "Volume, battery, dark mode, specs, screenshot", "'battery', 'specs', 'volume 45%', 'dark mode'", "⚡ <50ms")
    table.add_row("🖥️ App & Window", "Open/close macOS apps & web apps", "'open calculator', 'close safari', 'open mail'", "⚡ <50ms")
    table.add_row("📋 Clipboard & Audio", "Clipboard copy/paste, text-to-speech", "'copy Code to clipboard', 'say Welcome Razi'", "⚡ <50ms")
    table.add_row("🎬 YouTube & Media", "Direct search & playback of specific videos", "'open youtube apna college python full course'", "🧠 Agent")
    table.add_row("✉️ Email & Files", "Automated Gmail delivery, read/write files", "'send email to team@domain.com', 'create note'", "🧠 Agent")
    table.add_row("🔍 Deep Research", "Live web search (DDG), Wikipedia facts", "'Search latest AI breakthroughs', 'What is CRISPR?'", "🧠 Agent")
    table.add_row("🧠 Context Memory", "Remembers previous research & tasks", "'Save that summary to a note file on Desktop'", "🧠 Agent")

    c1.print(table)
    
    html1 = c1.export_html(inline_styles=True)
    full_html1 = create_mac_terminal_html(html1, "chaudhary@MacBook-Air: ~/macos-ai-agent (python main.py)")
    with open("screenshots/shot1.html", "w") as f:
        f.write(full_html1)

    # -------------------------------------------------------------
    # Screenshot 2: Sub-50ms Direct Execution Demo (Battery, Specs, Volume)
    # -------------------------------------------------------------
    c2 = Console(theme=custom_theme, record=True, width=95)
    c2.print("[bold bright_blue]You ▶ [/bold bright_blue][bold white]specs[/bold white]")
    
    specs_summary = (
        "• Model: Apple MacBook Air (Apple M-Series Silicon)\n"
        "• Memory (RAM): 8.0 GB Unified Memory\n"
        "• OS Version: macOS Version 15.x (Darwin Kernel)\n"
        "• Disk Storage: 245.1 GB total, 168.4 GB available"
    )
    c2.print(Panel(
        specs_summary,
        title="[bold green]⚡ Instant Direct Action — System Specs[/bold green]",
        subtitle="[dim]Latency: 32ms (LLM bypassed)[/dim]",
        border_style="green",
        padding=(1, 2)
    ))

    c2.print("\n[bold bright_blue]You ▶ [/bold bright_blue][bold white]battery[/bold white]")
    battery_summary = (
        "• Charge: 87%\n"
        "• State: Discharging (On Battery Power)\n"
        "• Health: Normal (Cycle Count: 42)"
    )
    c2.print(Panel(
        battery_summary,
        title="[bold green]⚡ Instant Direct Action — Battery Status[/bold green]",
        subtitle="[dim]Latency: 28ms (LLM bypassed)[/dim]",
        border_style="green",
        padding=(1, 2)
    ))

    c2.print("\n[bold bright_blue]You ▶ [/bold bright_blue][bold white]volume 65%[/bold white]")
    c2.print(Panel(
        "System output volume set to 65% successfully.",
        title="[bold green]⚡ Instant Direct Action — Volume Control[/bold green]",
        subtitle="[dim]Latency: 24ms (LLM bypassed)[/dim]",
        border_style="green",
        padding=(1, 2)
    ))

    html2 = c2.export_html(inline_styles=True)
    full_html2 = create_mac_terminal_html(html2, "chaudhary@MacBook-Air: ~/macos-ai-agent (Sub-50ms Instant Execution)")
    with open("screenshots/shot2.html", "w") as f:
        f.write(full_html2)

    # -------------------------------------------------------------
    # Screenshot 3: Deep Research + Memory to Desktop Note
    # -------------------------------------------------------------
    c3 = Console(theme=custom_theme, record=True, width=95)
    c3.print("[bold bright_blue]You ▶ [/bold bright_blue][bold white]What are the latest breakthroughs in Quantum Computing in 2026?[/bold white]")
    c3.print("  [dim cyan]⚙️  Invoking Tool:[/dim cyan] [bold bright_cyan]search[/bold bright_cyan] [dim](quantum computing breakthroughs 2026 advances...)[/dim]")
    c3.print("  [dim cyan]⚙️  Invoking Tool:[/dim cyan] [bold bright_cyan]wikipedia[/bold bright_cyan] [dim](Quantum supremacy and fault-tolerant qubits)[/dim]")

    research_summary = (
        "Recent breakthroughs in quantum computing focus on fault-tolerant logical qubits and quantum error correction (QEC):\n\n"
        "1. Logical Qubit Scalability: Transition from physical qubits to error-corrected logical qubits demonstrating 1000x lower error rates.\n"
        "2. Neutral Atom & Trapped-Ion Systems: Dual-rail architecture achieving record fidelity in multi-qubit entanglement.\n"
        "3. Hybrid Quantum-Classical Algorithms: Practical quantum utility demonstrated in material science simulation and quantum chemistry."
    )
    c3.print(Panel(
        research_summary,
        title="[bold bright_cyan]🔍 Deep Research Summary — Quantum Computing Breakthroughs[/bold bright_cyan]",
        subtitle="[dim]Sources: DuckDuckGo Search, Wikipedia API | Verified Schema: Pydantic v2[/dim]",
        border_style="bright_cyan",
        padding=(1, 2)
    ))

    c3.print("\n[bold bright_blue]You ▶ [/bold bright_blue][bold white]Save that summary into a note file on my Desktop named quantum_2026.txt[/bold white]")
    c3.print("  [dim cyan]⚙️  Invoking Tool:[/dim cyan] [bold bright_cyan]create_note_file[/bold bright_cyan] [dim](filename='quantum_2026.txt', content=...)[/dim]")
    c3.print(Panel(
        "Successfully created file on Desktop: /Users/chaudhary/Desktop/quantum_2026.txt\nFile contains formatted research summary with timestamps.",
        title="[bold green]📁 File Automation — Saved to Desktop[/bold green]",
        subtitle="[dim]Multi-Turn Conversational Memory active[/dim]",
        border_style="green",
        padding=(1, 2)
    ))

    html3 = c3.export_html(inline_styles=True)
    full_html3 = create_mac_terminal_html(html3, "chaudhary@MacBook-Air: ~/macos-ai-agent (Autonomous Research & Context Memory)")
    with open("screenshots/shot3.html", "w") as f:
        f.write(full_html3)

if __name__ == "__main__":
    generate_shots()
    print("HTML mockups generated successfully.")
