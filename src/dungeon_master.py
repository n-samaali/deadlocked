from google import generativeai as genai
import re

class DungeonMaster:

  # Create the model
  generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
  }

  model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config,
  )

  chat_session = model.start_chat(
    history=[
    ]
  )
  
  def __init__(self, API_KEY) :
      self.key = API_KEY
      genai.configure(api_key=self.key)  
  
  def _build_strict_prompt(self, event, context, extra_prompt):
    """
    Build a strict prompt that forces the model to return:
    1) A fenced code block with only the STORY
    2) A blank line
    3) The markdown table (with the 4 options)
    4) Optionally a fenced code block with DM content afterwards

    Provide a concrete example at the end.
    """
    instruction = (
        "You are the dungeon master. Produce exactly two main parts (optionally a third DM block):\n\n"
        "1) A fenced code block (triple backticks) containing ONLY the STORY text to show to the player.\n"
        "2) After the fenced block, one blank line, then a MARKDOWN TABLE with exactly these 4 rows: **Strength**, **Dexterity**, **Intelligence**, **Charisma**. "
        "Each row must be like: | **Strength** | description |\n\n"
        "OPTIONAL: after the table you may include another fenced code block with DM prompts. That block is for internal use only.\n\n"
        "IMPORTANT: Do not include any other text outside those blocks, do not ask for clarification, and do not put debugging text. "
        "If the card drawn is provided to you in 'event' (like '2H:'), incorporate that event at the start of the story line (e.g. '2H: ...').\n\n"
        "If the player's action causes hp changes, include a single marker somewhere in the STORY or DM block in the exact form 'Reduce:X' or 'Increase:X' where X is an integer.\n\n"
        "Example output (must match structure exactly):\n\n"
        "```\n"
        "2H: You squeeze through the gap and find a glittering pool. The light plays on the water and you feel a momentary calm.\n"
        "```\n\n"
        "| Option | Description |\n"
        "|---|---|\n"
        "| **Strength** | Use brute force to widen the gap. |\n"
        "| **Dexterity** | Carefully wriggle through the gap avoiding falling stones. |\n"
        "| **Intelligence** | Inspect the gap for weak points to pry open safely. |\n"
        "| **Charisma** | Call out, trying to lure whatever is on the other side. |\n\n"
        "``` \n"
        "# DM: internal prompts here if needed; may contain Reduce:5 or Increase:10\n"
        "```\n\n"
    )

    # combine context (which you pass as first-line context) and extra_prompt
    # event should be included by the caller (e.g., '2H:')
    base = f"EVENT: {event}\nCONTEXT: {context}\n\n{instruction}\n{extra_prompt}\n"
    return base

  def call_ai(self, event, context, prompt=""):
    """
    event: card key like '2H:' or 'JH:'
    context: short context or option description
    prompt: optional extra instructions appended
    This method will try up to max_attempts to get a response that matches the required format.
    """
    max_attempts = 3
    for attempt in range(max_attempts):
        built = self._build_strict_prompt(event, context, prompt)
        resp = self.chat_session.send_message(built).text

        # quick validation: we expect at least one fenced block and a markdown header row
        story, table = self.split_story_and_table(resp)

        if table and ("**Strength**" in table or "| **Strength**" in table):
            # good enough
            return resp


    # fallback: return last response anyway
    return resp

  def parse_options(self, markdown_table: str):
      """
      Parse a 4-option table into a dict:
      { "Strength": "Attempt to force open..." }
      """

      options = {}

      # Extract rows like:
      # | **Strength** | Attempt to... |
      rows = re.findall(
          r"\|\s*\*\*(.*?)\*\*\s*\|\s*(.*?)\s*\|",
          markdown_table,
          re.DOTALL
      )

      for opt, desc in rows:
          opt = opt.strip()
          desc = " ".join(desc.split())  # clean whitespace
          options[opt] = desc

      return options


  def split_story_and_table(self, text: str):
      import re
      story_match = re.search(r"```(.*?)```", text, re.DOTALL)
      story_text = story_match.group(1).strip() if story_match else ""
      story_text = re.sub(r"(Reduce|Increase)\s*:\s*\d+", "", story_text, flags=re.IGNORECASE).strip()

      remainder = re.sub(r"```.*?```", "", text, flags=re.DOTALL).strip()
      return story_text, remainder

  def extract_modifier(self, text: str):
      """
      Scans the entire paragraph and finds:
        - Reduce:X
        - Increase:X
      Returns (action, value) or (None, None)
      """
      match = re.search(r"(Reduce|Increase)\s*:\s*(\d+)", text, re.IGNORECASE)
      if match:
          action = match.group(1).capitalize()
          value = int(match.group(2))
          return action, value
      return None, None