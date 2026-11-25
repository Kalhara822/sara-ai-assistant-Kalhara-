"""
Browser & Web Search Commands
Handles: search_google, search_youtube, open_website, open_linkedin,
         search_wikipedia, check_weather, download_file
"""

import webbrowser
import urllib.parse
import subprocess
from typing import Dict, Any
from commands.base import BaseCommand
from utils.logger import logger


class OpenWebsiteCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "open_website"

    @property
    def description(self) -> str:
        return "Open a specified website URL or domain in the default browser."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        url = str(params.get("query") or params.get("value") or "").strip()
        if not url:
            url = "https://www.google.com"

        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        try:
            webbrowser.open(url)
            logger.info(f"Opened website: '{url}'")
            domain = url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
            return {"status": "success", "message": f"Opening {domain.title()} in browser."}
        except Exception as e:
            logger.error(f"Failed to open URL '{url}': {e}")
            return {"status": "error", "message": str(e)}


class SearchGoogleCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "search_google"

    @property
    def description(self) -> str:
        return "Open Google search or Google homepage in the browser."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "").strip()
        if not query or query.lower() in ["home", "google", "homepage", "none"]:
            url = "https://www.google.com"
            msg = "Opening Google homepage."
        else:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            msg = f"Searching Google for '{query}'."

        webbrowser.open(url)
        logger.info(f"Google action: '{query}' -> {url}")
        return {"status": "success", "message": msg}


class SearchYouTubeCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "search_youtube"

    @property
    def description(self) -> str:
        return "Open YouTube homepage or search query on YouTube."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "").strip()
        if not query or query.lower() in ["home", "youtube", "homepage", "none"]:
            url = "https://www.youtube.com"
            msg = "Opening YouTube."
        else:
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            msg = f"Searching YouTube for '{query}'."

        webbrowser.open(url)
        logger.info(f"YouTube action: '{query}' -> {url}")
        return {"status": "success", "message": msg}


class OpenLinkedInCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "open_linkedin"

    @property
    def description(self) -> str:
        return "Open LinkedIn in the browser."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            webbrowser.open("https://www.linkedin.com")
            return {"status": "success", "message": "Opening LinkedIn."}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class SearchWikipediaCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "search_wikipedia"

    @property
    def description(self) -> str:
        return "Extract information from Wikipedia with formatted summary, bullet points, and emojis."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = (params.get("query") or params.get("application") or "").strip()
        if not query:
            webbrowser.open("https://www.wikipedia.org")
            return {"status": "success", "message": "Opening Wikipedia."}

        try:
            import wikipediaapi
            wiki = wikipediaapi.Wikipedia(
                user_agent="SARA_AI_Assistant/1.0 (https://github.com/Kalhara321/sara-ai-assistant)",
                language="en"
            )
            page = wiki.page(query)

            if not page.exists():
                page = wiki.page(query.title())

            if page.exists() and len(page.summary.strip()) > 20:
                summary_raw = page.summary.strip()
                paragraphs = [p.strip() for p in summary_raw.split('\n') if p.strip()]
                first_para = paragraphs[0] if paragraphs else summary_raw

                raw_sentences = [s.strip() for s in first_para.split('. ') if len(s.strip()) > 12]
                bullets = []
                emoji_icons = ["💡", "⚡", "🔬", "📌", "🌐", "🔍"]

                for i, sent in enumerate(raw_sentences[:4]):
                    if not sent.endswith('.'):
                        sent += '.'
                    icon = emoji_icons[i % len(emoji_icons)]
                    bullets.append(f"  {icon} {sent}")

                ignore_sections = {'see also', 'references', 'external links', 'further reading', 'notes'}
                main_sections = [
                    sec.title for sec in page.sections
                    if sec.title and sec.title.lower() not in ignore_sections
                ]
                topics_str = ", ".join(main_sections[:5]) if main_sections else "Overview, History, Key Concepts"

                formatted_chat = (
                    f"📖 **Wikipedia Information: {page.title}**\n\n"
                    f"📝 **Summary Highlights:**\n" + "\n".join(bullets) + "\n\n"
                    f"📂 **Main Topics Covered:** {topics_str}\n\n"
                    f"🔗 **Full Article:** {page.fullurl}"
                )

                speech_sentences = raw_sentences[:2]
                spoken_text = f"Here is information on {page.title} from Wikipedia: " + " ".join(speech_sentences)
                if not spoken_text.endswith('.'):
                    spoken_text += '.'
                if len(spoken_text) > 280:
                    spoken_text = spoken_text[:277] + '...'

                webbrowser.open(page.fullurl)
                logger.info(f"Wikipedia API extracted information for '{query}': '{page.title}'")
                return {
                    "status": "success",
                    "message": formatted_chat,
                    "speech": spoken_text,
                    "title": page.title,
                    "url": page.fullurl
                }

        except Exception as e:
            logger.warning(f"Wikipedia API lookup error for '{query}': {e}")

        # Fallback to browser URL search
        url = f"https://en.wikipedia.org/wiki/Special:Search?search={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return {
            "status": "success",
            "message": f"🔍 **Wikipedia Search:** Opening results for '{query}' in browser.\n🔗 {url}",
            "speech": f"Searching Wikipedia for {query}."
        }


class CheckWeatherCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "check_weather"

    @property
    def description(self) -> str:
        return "Open a weather forecast in the browser."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            location = (params.get("query") or "").strip()
            if location:
                url = f"https://www.google.com/search?q=weather+{urllib.parse.quote(location)}"
                msg = f"Checking weather for {location}."
            else:
                url = "https://www.google.com/search?q=weather+today"
                msg = "Checking today's weather."
            webbrowser.open(url)
            return {"status": "success", "message": msg}
        except Exception as e:
            logger.error(f"Weather check error: {e}")
            return {"status": "error", "message": str(e)}


class DownloadFileCommand(BaseCommand):
    @property
    def action_name(self) -> str:
        return "download_file"

    @property
    def description(self) -> str:
        return "Download a file from a URL using PowerShell Invoke-WebRequest (system-friendly)."

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            url = (params.get("query") or params.get("application") or "").strip()
            if not url:
                return {"status": "error", "message": "Please provide a URL to download. E.g. 'download https://example.com/file.zip'"}
            if not url.startswith("http"):
                url = "https://" + url
            import os
            downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            filename = url.split("/")[-1].split("?")[0] or "download"
            out_path = os.path.join(downloads, filename)
            ps_cmd = f'Invoke-WebRequest -Uri "{url}" -OutFile "{out_path}" -UseBasicParsing'
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps_cmd]
            )
            return {"status": "success", "message": f"Downloading to Downloads folder as '{filename}'. This may take a moment."}
        except Exception as e:
            logger.error(f"Download file error: {e}")
            return {"status": "error", "message": str(e)}
