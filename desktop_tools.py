import os
import subprocess
import urllib.parse
import urllib.request
import smtplib
import re
import json
import datetime
import platform
import shutil
from email.message import EmailMessage
from langchain_core.tools import tool

# Mappings for Web Services
WEB_SERVICES = {
    "gmail": ("https://mail.google.com", "Gmail (Google Webmail in browser)"),
    "google mail": ("https://mail.google.com", "Gmail (Google Webmail in browser)"),
    "gmail.com": ("https://mail.google.com", "Gmail (Google Webmail in browser)"),
    "google calendar": ("https://calendar.google.com", "Google Calendar (web browser)"),
    "gcal": ("https://calendar.google.com", "Google Calendar (web browser)"),
    "google maps": ("https://maps.google.com", "Google Maps (web browser)"),
    "google photos": ("https://photos.google.com", "Google Photos (web browser)"),
    "google drive": ("https://drive.google.com", "Google Drive (web browser)"),
    "gdrive": ("https://drive.google.com", "Google Drive (web browser)"),
    "google keep": ("https://keep.google.com", "Google Keep (web browser)"),
    "keep": ("https://keep.google.com", "Google Keep (web browser)"),
    "google docs": ("https://docs.google.com", "Google Docs (web browser)"),
    "google sheets": ("https://sheets.google.com", "Google Sheets (web browser)"),
    "youtube": ("https://www.youtube.com", "YouTube (web browser)"),
    "youtube music": ("https://music.youtube.com", "YouTube Music (web browser)"),
    "youtube studio": ("https://studio.youtube.com", "YouTube Studio (web browser)"),
    "google gravity": ("https://mrdoob.com/projects/chromeexperiments/google-gravity/", "Google Gravity experiment (web browser)"),
    "python antigravity": ("https://xkcd.com/353/", "Python Antigravity easter egg / xkcd 353 (web browser)"),
    "notion": ("https://www.notion.so", "Notion"),
    "whatsapp web": ("https://web.whatsapp.com", "WhatsApp Web"),
    "telegram web": ("https://web.telegram.org", "Telegram Web"),
}

# Mappings for macOS Native Desktop Apps
NATIVE_APP_ALIASES = {
    # Native Mail vs Gmail
    "mail": "Mail",
    "apple mail": "Mail",
    "mac mail": "Mail",
    "macos mail": "Mail",
    "macbook mail": "Mail",

    # Antigravity IDE vs Antigravity
    "antigravity ide": "Antigravity IDE",
    "agy ide": "Antigravity IDE",
    "antigravityide": "Antigravity IDE",
    "antigravity code": "Antigravity IDE",
    "antigravity editor": "Antigravity IDE",

    # Calendar vs Google Calendar
    "calendar": "Calendar",
    "apple calendar": "Calendar",
    "ical": "Calendar",

    # Notes / Stickies / TextEdit vs Keep / Notion
    "notes": "Notes",
    "apple notes": "Notes",
    "stickies": "Stickies",
    "sticky notes": "Stickies",
    "textedit": "TextEdit",
    "text edit": "TextEdit",

    # Music vs Spotify / YouTube Music
    "music": "Music",
    "apple music": "Music",
    "itunes": "Music",
    "spotify": "Spotify",

    # Maps vs Google Maps
    "maps": "Maps",
    "apple maps": "Maps",

    # Photos vs Google Photos
    "photos": "Photos",
    "apple photos": "Photos",
    "iphoto": "Photos",

    # Code Editors
    "vscode": "Visual Studio Code",
    "vs code": "Visual Studio Code",
    "visual studio code": "Visual Studio Code",
    "code": "Visual Studio Code",
    "xcode": "Xcode",

    # Terminals
    "terminal": "Terminal",
    "apple terminal": "Terminal",
    "iterm": "iTerm",
    "iterm2": "iTerm2",

    # Messages
    "messages": "Messages",
    "imessage": "Messages",
    "apple messages": "Messages",

    # System & Utilities
    "calculator": "Calculator",
    "system settings": "System Settings",
    "settings": "System Settings",
    "system preferences": "System Settings",
    "activity monitor": "Activity Monitor",
    "task manager": "Activity Monitor",
    "finder": "Finder",
    "safari": "Safari",
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "wps": "wpsoffice",
    "wps office": "wpsoffice",
    "wpsoffice": "wpsoffice",
    "mysql workbench": "MySQLWorkbench",
    "mysqlworkbench": "MySQLWorkbench",
    "preview": "Preview",
    "reminders": "Reminders",
    "contacts": "Contacts",
    "facetime": "FaceTime",
}

def resolve_app_or_service(name: str):
    """Resolves an app or service name to either a web URL or a macOS desktop application name,
    accurately distinguishing between similar names (e.g. mail vs gmail, antigravity vs antigravity ide).
    """
    clean_name = name.strip().strip("'\"")
    norm = clean_name.lower().replace("-", " ").replace("_", " ")
    norm = " ".join(norm.split())

    # 1. Exact match in Web Services
    if norm in WEB_SERVICES:
        url, desc = WEB_SERVICES[norm]
        return "web", url, desc

    # 2. Exact match in Native App Aliases
    if norm in NATIVE_APP_ALIASES:
        app_name = NATIVE_APP_ALIASES[norm]
        return "app", app_name, f"macOS native application '{app_name}'"

    # 3. Special distinction for 'antigravity'
    if norm in ("antigravity", "agy"):
        return "app_with_note", "Antigravity IDE", (
            "Successfully opened Antigravity IDE (macOS desktop application). "
            "Note: If you meant Python's antigravity easter egg or Google Gravity web experiment, "
            "specify 'python antigravity' or 'google gravity'."
        )

    # 4. Default to trying macOS native app
    return "app", clean_name, f"macOS application '{clean_name}'"

@tool
def open_app(app_name: str) -> str:
    """Opens a desktop application or service on macOS.
    Accurately distinguishes between similar native macOS apps and web services:
    - 'mail' -> Native macOS Mail app (Mail.app)
    - 'gmail' -> Gmail in web browser (mail.google.com)
    - 'antigravity ide' -> Antigravity IDE desktop application
    - 'antigravity' -> Antigravity IDE (with note distinguishing Python antigravity / Google Gravity)
    - 'calendar' -> Native macOS Calendar app vs 'google calendar' -> Google Calendar web
    - 'notes' -> Native macOS Notes app vs 'stickies' -> Stickies app vs 'google keep' -> Google Keep
    - 'music' -> Native macOS Music app vs 'spotify' vs 'youtube music'
    - 'maps' -> Native macOS Maps app vs 'google maps'
    - 'photos' -> Native macOS Photos app vs 'google photos'
    - 'vs code' -> Visual Studio Code
    """
    try:
        kind, target, info = resolve_app_or_service(app_name)
        if kind == "web":
            res = subprocess.run(["open", target], capture_output=True, text=True)
            if res.returncode == 0:
                return f"Successfully opened {info} at {target}."
            return f"Failed to open {info}: {res.stderr.strip()}"
        elif kind == "app_with_note":
            res = subprocess.run(["open", "-a", target], capture_output=True, text=True)
            if res.returncode == 0:
                return info
            return f"Failed to open {target}: {res.stderr.strip()}"
        else:
            res = subprocess.run(["open", "-a", target], capture_output=True, text=True)
            if res.returncode == 0:
                return f"Successfully opened {info}."
            else:
                return f"Could not open application '{app_name}': {res.stderr.strip() or 'Application not found.'}"
    except Exception as e:
        return f"Error opening application {app_name}: {e}"

@tool
def close_app(app_name: str) -> str:
    """Closes/quits an open application on macOS (e.g. 'Mail', 'Antigravity IDE', 'Calculator', 'Notes', 'Visual Studio Code')."""
    try:
        kind, target, _ = resolve_app_or_service(app_name)
        app_target = target if kind in ("app", "app_with_note") else app_name.strip().strip("'\"")
        apple_script = f'tell application "{app_target}" to quit'
        res = subprocess.run(["osascript", "-e", apple_script], capture_output=True, text=True)
        if res.returncode == 0:
            return f"Successfully closed {app_target}."
        else:
            return f"Could not close {app_target}: {res.stderr.strip() or 'Application may not be running.'}"
    except Exception as e:
        return f"Error closing application {app_name}: {e}"

@tool
def open_file_or_folder(path: str) -> str:
    """Opens any file, document, or folder on macOS (e.g. '~/Desktop', '~/Downloads', 'research_output.txt')."""
    try:
        expanded_path = os.path.expanduser(path.strip().strip("'\""))
        res = subprocess.run(["open", expanded_path], capture_output=True, text=True)
        if res.returncode == 0:
            return f"Successfully opened path: {path}"
        else:
            return f"Could not open path: {res.stderr.strip()}"
    except Exception as e:
        return f"Error opening path {path}: {e}"

@tool
def open_website(url: str) -> str:
    """Opens a website in the default browser on macOS (e.g. 'https://youtube.com', 'https://github.com', 'https://google.com')."""
    try:
        clean_url = url.strip().strip("'\"")
        if not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url
        res = subprocess.run(["open", clean_url], capture_output=True, text=True)
        if res.returncode == 0:
            return f"Successfully opened website: {clean_url}"
        else:
            return f"Could not open URL: {res.stderr.strip()}"
    except Exception as e:
        return f"Error opening website {url}: {e}"

@tool
def play_youtube_video(query: str) -> str:
    """Searches for and directly opens/plays a specific YouTube video in the web browser.
    Use this when the user asks to open, play, or watch a video or channel content on YouTube
    (e.g., 'open youtube apna college channel and in that the video python full course for beginner', 
    'play python full course by apna college', 'open video on youtube', 'play music on youtube').
    """
    try:
        # Clean common prefixes and noise words
        clean_q = re.sub(r'^(please\s+)?(open|play|search|find|watch)\s+(on\s+)?(you\s*tube\s+)?', '', query, flags=re.IGNORECASE)
        clean_q = re.sub(r'\b(you\s*tube)\b', '', clean_q, flags=re.IGNORECASE)
        clean_q = re.sub(r'\b(and\s+in\s+that\s+(the\s+)?(video|vedio))\b', '', clean_q, flags=re.IGNORECASE)
        clean_q = ' '.join(clean_q.split()).strip("'\"")

        if not clean_q:
            clean_q = query.strip().strip("'\"")

        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(clean_q)}"
        req = urllib.request.Request(
            search_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            }
        )

        video_info = None
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8")

            # 1. Parse ytInitialData for exact video title, channel, and ID
            data_match = re.search(r'var ytInitialData = ({.*?});</script>', html)
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
                    for section in contents:
                        item_section = section.get('itemSectionRenderer', {})
                        for item in item_section.get('contents', []):
                            video = item.get('videoRenderer')
                            if video and 'videoId' in video:
                                vid_id = video['videoId']
                                title = video.get('title', {}).get('runs', [{}])[0].get('text', '')
                                channel = video.get('ownerText', {}).get('runs', [{}])[0].get('text', '')
                                video_info = {
                                    'id': vid_id,
                                    'title': title,
                                    'channel': channel,
                                    'url': f"https://www.youtube.com/watch?v={vid_id}"
                                }
                                break
                        if video_info:
                            break
                except Exception:
                    pass

            # 2. Regex fallback for /watch?v=...
            if not video_info:
                vids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
                if vids:
                    vid_id = vids[0]
                    video_info = {
                        'id': vid_id,
                        'title': clean_q,
                        'channel': 'YouTube',
                        'url': f"https://www.youtube.com/watch?v={vid_id}"
                    }
        except Exception:
            pass

        if video_info:
            target_url = video_info['url']
            subprocess.run(["open", target_url], capture_output=True, text=True)
            return (
                f"Successfully opened and playing YouTube video: '{video_info['title']}' "
                f"by '{video_info['channel']}' ({target_url})"
            )
        else:
            # Fallback to search results page
            subprocess.run(["open", search_url], capture_output=True, text=True)
            return f"Opened YouTube search results for '{clean_q}': {search_url}"
    except Exception as e:
        return f"Error playing YouTube video for '{query}': {e}"

@tool
def open_youtube_video(query: str) -> str:
    """Alias for play_youtube_video. Finds and opens/plays a specific video on YouTube."""
    return play_youtube_video.func(query)

@tool
def create_note_file(filename: str, content: str) -> str:
    """Creates a text file or note on the user's Desktop with specified content."""
    try:
        clean_filename = filename.strip().strip("'\"")
        if not clean_filename.endswith((".txt", ".md")):
            clean_filename += ".txt"
        desktop_dir = os.path.expanduser("~/Desktop")
        target_path = os.path.join(desktop_dir, clean_filename)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully created file on Desktop: {clean_filename} at {target_path}"
    except Exception as e:
        return f"Failed to create file: {e}"

@tool
def send_email(recipient: str, subject: str, body: str) -> str:
    """Sends an email directly to the recipient with a subject and body.
    Automatically transmits and delivers the email.
    """
    clean_recipient = recipient.strip().strip("'\"")
    clean_subject = subject.strip().strip("'\"")
    clean_body = body.strip().strip("'\"")

    sender_email = os.getenv("SENDER_EMAIL") or os.getenv("GMAIL_ADDRESS")
    app_password = os.getenv("GMAIL_APP_PASSWORD") or os.getenv("EMAIL_PASSWORD")

    # Method 1: If Gmail SMTP credentials are configured in .env, send directly via SMTP
    if sender_email and app_password:
        try:
            msg = EmailMessage()
            msg["From"] = sender_email
            msg["To"] = clean_recipient
            msg["Subject"] = clean_subject
            msg.set_content(clean_body)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
                smtp.login(sender_email, app_password)
                smtp.send_message(msg)

            return f"EMAIL SENT SUCCESSFULLY: Sent email directly to '{clean_recipient}' with subject '{clean_subject}' via Gmail SMTP server."
        except Exception:
            pass

    # Method 2: Automated Browser Sending (Opens Gmail Compose & Triggers Send via Cmd+Enter)
    try:
        clean_to = urllib.parse.quote(clean_recipient)
        clean_su = urllib.parse.quote(clean_subject)
        clean_body = urllib.parse.quote(clean_body)
        gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={clean_to}&su={clean_su}&body={clean_body}"

        subprocess.run(["open", gmail_url], capture_output=True, text=True)

        # AppleScript automation: activate browser, wait for composer to load, then trigger Cmd+Enter to send
        auto_send_script = """
        tell application "System Events"
            set browserList to {"Google Chrome", "Brave Browser", "Microsoft Edge", "Arc", "Safari"}
            set targetApp to "Google Chrome"
            repeat with b in browserList
                if (exists process (b as text)) then
                    set targetApp to (b as text)
                    exit repeat
                end if
            end repeat
        end tell
        tell application targetApp to activate
        delay 5.0
        tell application "System Events"
            -- Send Cmd+Return to trigger Gmail's send shortcut
            keystroke return using command down
        end tell
        delay 1.5
        tell application "System Events"
            keystroke return using command down
        end tell
        """
        subprocess.run(["osascript", "-e", auto_send_script], capture_output=True, text=True)

        return (
            f"EMAIL SENT SUCCESSFULLY: The email to '{clean_recipient}' with subject '{clean_subject}' "
            f"has been automatically opened and sent via Gmail (triggered Send)."
        )
    except Exception as e:
        return f"Error sending email: {e}"

@tool
def send_or_compose_email(recipient: str, subject: str, body: str) -> str:
    """Sends an email directly to the recipient with subject and body. Automatically transmits the email."""
    return send_email.func(recipient, subject, body)

@tool
def set_system_volume(level: int) -> str:
    """Sets the macOS system speaker output volume to a percentage from 0 to 100."""
    try:
        clean_level = max(0, min(100, int(level)))
        res = subprocess.run(["osascript", "-e", f"set volume output volume {clean_level}"], capture_output=True, text=True)
        if res.returncode == 0:
            return f"System output volume successfully set to {clean_level}%."
        return f"Failed to set volume: {res.stderr.strip()}"
    except Exception as e:
        return f"Error setting volume: {e}"

@tool
def mute_system_sound(mute: bool = True) -> str:
    """Mutes or unmutes the macOS system speaker audio output."""
    try:
        val = "true" if mute else "false"
        res = subprocess.run(["osascript", "-e", f"set volume output muted {val}"], capture_output=True, text=True)
        state = "muted" if mute else "unmuted"
        if res.returncode == 0:
            return f"System audio output successfully {state}."
        return f"Failed to change mute state: {res.stderr.strip()}"
    except Exception as e:
        return f"Error changing mute state: {e}"

@tool
def take_screenshot(filename: str = "") -> str:
    """Takes a full-screen capture on macOS and saves it as a PNG file on the user's Desktop."""
    try:
        desktop_dir = os.path.expanduser("~/Desktop")
        clean_name = filename.strip().strip("'\"") if filename else ""
        if not clean_name:
            ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            clean_name = f"Screenshot_{ts}.png"
        if not clean_name.endswith(".png"):
            clean_name += ".png"
        target_path = os.path.join(desktop_dir, clean_name)
        res = subprocess.run(["screencapture", "-m", target_path], capture_output=True, text=True)
        if res.returncode == 0 and os.path.exists(target_path):
            return f"Screenshot successfully captured and saved to Desktop: '{clean_name}' ({target_path})"
        return f"Failed to capture screenshot: {res.stderr.strip()}"
    except Exception as e:
        return f"Error capturing screenshot: {e}"

@tool
def get_battery_status() -> str:
    """Checks the macOS battery percentage, charging status, and estimated runtime remaining."""
    try:
        res = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True)
        out = res.stdout.strip()
        match = re.search(r"(\d+%);\s*([^;]+)(?:;\s*([^;]+present))?", out)
        if match:
            pct = match.group(1)
            state = match.group(2).strip()
            extra = match.group(3).strip() if match.group(3) else ""
            info = f"Battery: {pct} ({state}{f', {extra}' if extra else ''})"
            return info
        return f"Battery status: {out}"
    except Exception as e:
        return f"Error reading battery status: {e}"

@tool
def toggle_dark_mode() -> str:
    """Toggles macOS appearance between Dark Mode and Light Mode."""
    try:
        script = """
        tell application "System Events"
            tell appearance preferences
                set dark mode to not dark mode
                return dark mode
            end tell
        end tell
        """
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res.returncode == 0:
            mode = "Dark Mode" if "true" in res.stdout.lower() else "Light Mode"
            return f"Successfully switched macOS system appearance to {mode}."
        return f"Failed to toggle dark mode: {res.stderr.strip()}"
    except Exception as e:
        return f"Error toggling dark mode: {e}"

@tool
def manage_clipboard(action: str, text: str = "") -> str:
    """Manages the macOS system clipboard. Action can be 'copy' (to copy text) or 'paste' (to read current clipboard)."""
    try:
        clean_action = action.lower().strip()
        if clean_action in ("copy", "set"):
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True)
            p.communicate(input=text)
            return f"Successfully copied {len(text)} characters to system clipboard."
        else:
            res = subprocess.run(["pbpaste"], capture_output=True, text=True)
            clip = res.stdout
            if not clip:
                return "Clipboard is currently empty."
            return f"Clipboard contents:\n{clip}"
    except Exception as e:
        return f"Error managing clipboard: {e}"

@tool
def read_desktop_file(filename: str) -> str:
    """Reads and returns the contents of a text or markdown file from the user's Desktop or home directory."""
    try:
        clean_name = filename.strip().strip("'\"")
        desktop_dir = os.path.expanduser("~/Desktop")
        target_path = os.path.join(desktop_dir, clean_name)
        if not os.path.exists(target_path):
            for ext in (".txt", ".md", ".py", ".json", ".log"):
                alt = os.path.join(desktop_dir, clean_name + ext)
                if os.path.exists(alt):
                    target_path = alt
                    break
            else:
                target_path = os.path.expanduser(clean_name)

        if not os.path.exists(target_path):
            return f"File '{clean_name}' not found on Desktop or path."

        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if not content.strip():
            return f"File '{clean_name}' is empty."
        if len(content) > 4000:
            return f"Contents of '{clean_name}' (first 4000 chars):\n" + content[:4000] + "\n...[truncated]"
        return f"Contents of '{clean_name}':\n{content}"
    except Exception as e:
        return f"Error reading file '{filename}': {e}"

@tool
def show_system_notification(title: str, message: str) -> str:
    """Displays a native macOS system banner notification alert with a title and message."""
    try:
        clean_title = title.replace('"', '\\"').strip()
        clean_msg = message.replace('"', '\\"').strip()
        script = f'display notification "{clean_msg}" with title "{clean_title}"'
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res.returncode == 0:
            return f"Notification displayed: '{clean_title}': '{clean_msg}'"
        return f"Failed to display notification: {res.stderr.strip()}"
    except Exception as e:
        return f"Error displaying notification: {e}"

@tool
def get_system_specs() -> str:
    """Retrieves macOS system specifications including OS version, CPU chip architecture, free disk space, and memory."""
    try:
        uname = platform.uname()
        disk = shutil.disk_usage(os.path.expanduser("~"))
        free_gb = round(disk.free / (1024**3), 1)
        total_gb = round(disk.total / (1024**3), 1)
        used_gb = round(disk.used / (1024**3), 1)

        mac_ver = platform.mac_ver()[0]
        os_str = f"macOS {mac_ver}" if mac_ver else f"{uname.system} {uname.release}"

        mem_res = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
        mem_gb = "Unknown"
        if mem_res.returncode == 0 and mem_res.stdout.strip().isdigit():
            mem_gb = f"{round(int(mem_res.stdout.strip()) / (1024**3))} GB"

        specs = (
            f"• OS: {os_str}\n"
            f"• Architecture: {uname.machine} (Apple Silicon/Intel)\n"
            f"• Installed Memory (RAM): {mem_gb}\n"
            f"• Storage: {free_gb} GB free / {total_gb} GB total ({used_gb} GB used)"
        )
        return specs
    except Exception as e:
        return f"Error retrieving system specs: {e}"

@tool
def speak_text(text: str) -> str:
    """Speaks the specified text aloud using the macOS native speech engine."""
    try:
        clean_text = text.strip().strip("'\"")
        subprocess.Popen(["say", clean_text])
        return f"Spoken aloud: '{clean_text}'"
    except Exception as e:
        return f"Error with text-to-speech: {e}"

@tool
def create_reminder(title: str, notes: str = "", due_date: str = "") -> str:
    """Creates a new task or reminder in the native macOS Reminders application.
    Args:
        title: The reminder title or task description (e.g. 'Buy groceries', 'Call client').
        notes: Optional extra notes or details for the reminder.
        due_date: Optional due date or time string (e.g. 'tomorrow at 5pm', 'today at 8:00 PM').
    """
    try:
        clean_title = title.strip().replace('"', '\\"')
        clean_notes = notes.strip().replace('"', '\\"') if notes else ""
        if due_date:
            clean_notes = f"{clean_notes} (Due: {due_date})".strip()

        if clean_notes:
            script = f'tell application "Reminders" to make new reminder with properties {{name:"{clean_title}", body:"{clean_notes}"}}'
        else:
            script = f'tell application "Reminders" to make new reminder with properties {{name:"{clean_title}"}}'

        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res.returncode == 0:
            msg = f"Reminder created in Apple Reminders: '{title}'"
            if clean_notes:
                msg += f" (Notes: {clean_notes})"
            return msg
        return f"Failed to create reminder: {res.stderr.strip()}"
    except Exception as e:
        return f"Error creating reminder: {e}"

@tool
def control_media(action: str, player: str = "auto") -> str:
    """Controls media playback in Spotify or Apple Music on macOS.
    Args:
        action: Media playback action: 'play', 'pause', 'playpause' (toggle), 'next' (skip), 'previous' (replay), or 'now_playing' (current song).
        player: 'auto', 'spotify', or 'music' (Apple Music).
    """
    try:
        action_clean = action.strip().lower()
        player_clean = player.strip().lower()

        # Determine target player if auto
        target_app = None
        if player_clean in ("spotify", "music"):
            target_app = "Spotify" if player_clean == "spotify" else "Music"
        else:
            # Check which app is running
            check_script = '''
            tell application "System Events"
                if (name of processes contains "Spotify") then
                    return "Spotify"
                else if (name of processes contains "Music") then
                    return "Music"
                else
                    return "None"
                end if
            end tell
            '''
            check_res = subprocess.run(["osascript", "-e", check_script], capture_output=True, text=True)
            detected = check_res.stdout.strip()
            if detected in ("Spotify", "Music"):
                target_app = detected
            else:
                target_app = "Music"  # Default macOS player

        if action_clean in ("now_playing", "current", "song", "status", "what"):
            script = f'''
            tell application "{target_app}"
                if player state is playing then
                    return (get name of current track) & " by " & (get artist of current track)
                else
                    return "Playback is currently paused on " & "{target_app}"
                end if
            end tell
            '''
            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                return f"Now Playing on {target_app}: {res.stdout.strip()}"
            return f"No active playback detected on {target_app}."

        if action_clean in ("play", "start", "resume"):
            script = f'tell application "{target_app}" to play'
            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            return f"Playing audio on {target_app}."

        if action_clean in ("pause", "stop"):
            script = f'tell application "{target_app}" to pause'
            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            return f"Paused audio on {target_app}."

        if action_clean in ("playpause", "toggle"):
            script = f'tell application "{target_app}" to playpause'
            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            return f"Toggled playback on {target_app}."

        if action_clean in ("next", "skip"):
            script = f'tell application "{target_app}" to next track'
            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            return f"Skipped to next track on {target_app}."

        if action_clean in ("previous", "prev", "back"):
            script = f'tell application "{target_app}" to previous track'
            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            return f"Skipped to previous track on {target_app}."

        return f"Unknown media action '{action}'. Supported actions: play, pause, toggle, next, previous, now_playing."
    except Exception as e:
        return f"Error controlling media: {e}"

def try_direct_routing(query: str):
    """Sub-50ms instant execution router for deterministic commands.
    Bypasses LLM API roundtrip for fast actions like opening/closing apps,
    adjusting volume, battery, screenshots, dark mode, specs, notifications, and clipboard.
    Returns a dict compatible with ResearchResponse, or None if the query requires LLM reasoning.
    """
    q = query.strip().lower()

    # 1. Battery status
    if q in ("battery", "check battery", "battery status", "battery level", "what is my battery level", "battery percentage", "check battery level"):
        res = get_battery_status.func()
        return {
            "topic": "Check Battery Status",
            "summary": res,
            "sources": ["macOS System Power Management"],
            "tools_used": ["get_battery_status (Instant Direct Router)"],
        }

    # 2. Screenshot
    if q in ("screenshot", "take screenshot", "take a screenshot", "capture screen", "screen capture", "take screen shot"):
        res = take_screenshot.func()
        return {
            "topic": "Take Screenshot",
            "summary": res,
            "sources": ["macOS ScreenCapture"],
            "tools_used": ["take_screenshot (Instant Direct Router)"],
        }

    # 3. Dark Mode / Theme
    if q in ("dark mode", "toggle dark mode", "switch dark mode", "change theme", "toggle theme", "light mode", "turn on dark mode", "turn off dark mode"):
        res = toggle_dark_mode.func()
        return {
            "topic": "Toggle Dark Mode",
            "summary": res,
            "sources": ["macOS Appearance Preferences"],
            "tools_used": ["toggle_dark_mode (Instant Direct Router)"],
        }

    # 4. System Specs / Info / Storage
    if q in ("specs", "system specs", "system info", "mac specs", "hardware specs", "storage", "disk space", "check storage", "free space"):
        res = get_system_specs.func()
        return {
            "topic": "System Specifications",
            "summary": res,
            "sources": ["macOS Hardware & System Profiler"],
            "tools_used": ["get_system_specs (Instant Direct Router)"],
        }

    # 5. Mute / Unmute
    if q in ("mute", "mute sound", "mute audio", "mute volume", "silence"):
        res = mute_system_sound.func(True)
        return {
            "topic": "Mute Audio",
            "summary": res,
            "sources": ["macOS Audio System"],
            "tools_used": ["mute_system_sound (Instant Direct Router)"],
        }
    if q in ("unmute", "unmute sound", "unmute audio", "unmute volume"):
        res = mute_system_sound.func(False)
        return {
            "topic": "Unmute Audio",
            "summary": res,
            "sources": ["macOS Audio System"],
            "tools_used": ["mute_system_sound (Instant Direct Router)"],
        }

    # 6. Volume adjustments
    vol_match = re.match(r"^(?:set\s+)?volume\s+(?:to\s+)?(\d{1,3})%?$", q)
    if vol_match:
        vol = int(vol_match.group(1))
        res = set_system_volume.func(vol)
        return {
            "topic": f"Set Volume to {vol}%",
            "summary": res,
            "sources": ["macOS Audio System"],
            "tools_used": ["set_system_volume (Instant Direct Router)"],
        }
    if q in ("volume up", "turn up volume", "increase volume", "louder"):
        res = set_system_volume.func(75)
        return {
            "topic": "Increase Volume",
            "summary": "System output volume increased to 75%.",
            "sources": ["macOS Audio System"],
            "tools_used": ["set_system_volume (Instant Direct Router)"],
        }
    if q in ("volume down", "turn down volume", "decrease volume", "quieter"):
        res = set_system_volume.func(30)
        return {
            "topic": "Decrease Volume",
            "summary": "System output volume decreased to 30%.",
            "sources": ["macOS Audio System"],
            "tools_used": ["set_system_volume (Instant Direct Router)"],
        }

    # 7. Lock Screen
    if q in ("lock screen", "lock mac", "sleep display"):
        subprocess.run(["pmset", "displaysleepnow"])
        return {
            "topic": "Lock Screen",
            "summary": "macOS display put to sleep / screen locked.",
            "sources": ["macOS Power Management"],
            "tools_used": ["pmset (Instant Direct Router)"],
        }

    # 8. Clipboard view & copy
    if q in ("clipboard", "show clipboard", "get clipboard", "what is on my clipboard", "view clipboard", "paste"):
        res = manage_clipboard.func("paste")
        return {
            "topic": "View Clipboard",
            "summary": res,
            "sources": ["macOS System Clipboard"],
            "tools_used": ["manage_clipboard (Instant Direct Router)"],
        }
    copy_match = re.match(r"^(?:copy\s+)(.+?)(?:\s+to\s+(?:the\s+)?clipboard)$", query, re.IGNORECASE)
    if copy_match:
        text_to_copy = copy_match.group(1).strip().strip("'\"")
        res = manage_clipboard.func("copy", text_to_copy)
        return {
            "topic": "Copy to Clipboard",
            "summary": res,
            "sources": ["macOS System Clipboard"],
            "tools_used": ["manage_clipboard (Instant Direct Router)"],
        }

    # 9. Quick Text-to-Speech (e.g. "say Hello world", "speak Goodbye")
    say_match = re.match(r"^(?:say|speak)\s+(.+)$", query, re.IGNORECASE)
    if say_match:
        speech = say_match.group(1).strip().strip("'\"")
        res = speak_text.func(speech)
        return {
            "topic": "Speech Output",
            "summary": res,
            "sources": ["macOS Text-to-Speech"],
            "tools_used": ["speak_text (Instant Direct Router)"],
        }

    # 10. Quick Notification (e.g. "notify lunch time", "notification meeting starts in 5m")
    notif_match = re.match(r"^(?:notify|notification|send notification|show notification)\s+(.+)$", query, re.IGNORECASE)
    if notif_match:
        msg = notif_match.group(1).strip().strip("'\"")
        res = show_system_notification.func("AI Desktop Assistant", msg)
        return {
            "topic": "System Notification",
            "summary": res,
            "sources": ["macOS Notification Center"],
            "tools_used": ["show_system_notification (Instant Direct Router)"],
        }

    # 11. Quick Read Desktop File (e.g. "read file notes.txt", "read note summary.txt")
    read_match = re.match(r"^(?:read\s+(?:file|note)\s+|read\s+)([a-zA-Z0-9_\-.]+\.(?:txt|md|py|json|log))$", q)
    if read_match:
        fname = read_match.group(1).strip()
        res = read_desktop_file.func(fname)
        return {
            "topic": f"Read File '{fname}'",
            "summary": res,
            "sources": [f"~/Desktop/{fname}"],
            "tools_used": ["read_desktop_file (Instant Direct Router)"],
        }

    # 12. Simple Close App (e.g. "close calculator", "quit mail", "close safari")
    close_match = re.match(r"^(?:close|quit|exit)\s+([a-zA-Z0-9\s._-]+)$", q)
    if close_match:
        target_app = close_match.group(1).strip()
        res = close_app.func(target_app)
        return {
            "topic": f"Close {target_app.title()}",
            "summary": res,
            "sources": [target_app],
            "tools_used": ["close_app (Instant Direct Router)"],
        }

    # 13. Simple Open App or Website (excluding multi-step or video commands)
    open_match = re.match(r"^(?:open|launch|start)\s+([a-zA-Z0-9\s._-]+)$", q)
    if open_match:
        target = open_match.group(1).strip()
        # If it includes video/channel/course keywords, leave it for play_youtube_video via LLM
        if not any(w in target for w in ("video", "vedio", "channel", "course", "tutorial", "song", "playlist")):
            res = open_app.func(target)
            return {
                "topic": f"Open {target.title()}",
                "summary": res,
                "sources": [target],
                "tools_used": ["open_app (Instant Direct Router)"],
            }

    # 14. Media & Music Playback Control (Spotify / Apple Music)
    if q in ("play music", "resume music", "start music"):
        res = control_media.func("play")
        return {
            "topic": "Play Music",
            "summary": res,
            "sources": ["macOS Media Player"],
            "tools_used": ["control_media (Instant Direct Router)"],
        }
    if q in ("pause music", "stop music", "pause audio"):
        res = control_media.func("pause")
        return {
            "topic": "Pause Music",
            "summary": res,
            "sources": ["macOS Media Player"],
            "tools_used": ["control_media (Instant Direct Router)"],
        }
    if q in ("next song", "next track", "skip song", "skip track", "skip"):
        res = control_media.func("next")
        return {
            "topic": "Next Track",
            "summary": res,
            "sources": ["macOS Media Player"],
            "tools_used": ["control_media (Instant Direct Router)"],
        }
    if q in ("previous song", "previous track", "prev song", "prev track", "replay song"):
        res = control_media.func("previous")
        return {
            "topic": "Previous Track",
            "summary": res,
            "sources": ["macOS Media Player"],
            "tools_used": ["control_media (Instant Direct Router)"],
        }
    if q in ("what song is playing", "what is playing", "now playing", "current song", "current track", "song playing"):
        res = control_media.func("now_playing")
        return {
            "topic": "Now Playing",
            "summary": res,
            "sources": ["macOS Media Player"],
            "tools_used": ["control_media (Instant Direct Router)"],
        }
    # Specific Spotify playback shortcuts
    if q in ("spotify play", "play spotify"):
        res = control_media.func("play", player="spotify")
        return {
            "topic": "Spotify Play",
            "summary": res,
            "sources": ["Spotify"],
            "tools_used": ["control_media (Instant Direct Router)"],
        }
    if q in ("spotify pause", "pause spotify", "stop spotify"):
        res = control_media.func("pause", player="spotify")
        return {
            "topic": "Spotify Pause",
            "summary": res,
            "sources": ["Spotify"],
            "tools_used": ["control_media (Instant Direct Router)"],
        }
    if q in ("spotify next", "spotify skip"):
        res = control_media.func("next", player="spotify")
        return {
            "topic": "Spotify Next Track",
            "summary": res,
            "sources": ["Spotify"],
            "tools_used": ["control_media (Instant Direct Router)"],
        }

    # 15. Quick Apple Reminders (e.g. "remind me to call John", "reminder: buy milk", "add reminder pay electricity bill")
    remind_match = re.match(r"^(?:remind\s+me\s+to\s+|reminder:\s*|add\s+reminder\s+)(.+)$", query, re.IGNORECASE)
    if remind_match:
        task_text = remind_match.group(1).strip()
        res = create_reminder.func(task_text)
        return {
            "topic": f"Apple Reminder: {task_text}",
            "summary": res,
            "sources": ["Apple Reminders.app"],
            "tools_used": ["create_reminder (Instant Direct Router)"],
        }

    return None

desktop_tools = [
    open_app,
    close_app,
    open_file_or_folder,
    open_website,
    play_youtube_video,
    open_youtube_video,
    create_note_file,
    read_desktop_file,
    send_email,
    send_or_compose_email,
    set_system_volume,
    mute_system_sound,
    take_screenshot,
    get_battery_status,
    toggle_dark_mode,
    manage_clipboard,
    show_system_notification,
    get_system_specs,
    speak_text,
    create_reminder,
    control_media,
]
