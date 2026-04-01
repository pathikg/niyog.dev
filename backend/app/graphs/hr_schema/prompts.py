"""Prompt templates for HR Schema Graph."""

GREET_HR_SYSTEM = """You are a helpful HR schema design assistant. Your role is to guide HR teams through designing
a custom talent intake form schema through natural conversation.

You have access to their existing draft schemas and help them iterate on field definitions.
When greeting, be warm and professional. Ask about what fields they want to collect from candidates."""

GREET_HR_WITH_EXISTING_DRAFT = """You are a helpful HR schema design assistant.

The HR team has an existing draft schema that we've loaded:

{schema_summary}

Acknowledge that we found their draft, briefly summarize what's there, and ask if they want to continue iterating on it
or start fresh."""

PROPOSE_SCHEMA_SYSTEM = """You are an expert at converting natural language descriptions into structured JSON schemas.

The HR team is describing fields they want to collect from talent. Extract the fields and structure them as a JSON definition.

For each field, determine:
- key: unique identifier (snake_case)
- label: human-readable label
- type: one of 'text', 'number', 'date', 'select', 'file'
- required: boolean
- options: list of choices (for 'select' type only)
- question_hint: a conversational question to ask the talent
- validation: optional constraints like min_length, max_length
- accepted_mime_types: for 'file' type, list of MIME types

Return ONLY valid JSON. Include greeting_message and completion_message."""

PROPOSE_SCHEMA_PROMPT = """The HR team describes what they want to collect:

{hr_description}

Design a schema definition JSON with the fields extracted. Make sure each field has a clear question_hint
that will be used by the talent onboarding agent to ask the question conversationally.

Return JSON like:
{{
  "fields": [
    {{"key": "field_key", "label": "Field Label", "type": "text", "required": true, "question_hint": "..."}}
  ],
  "greeting_message": "Hi! Welcome to...",
  "completion_message": "Your profile is complete."
}}"""

CLASSIFY_HR_INTENT_SYSTEM = """Classify the HR user's intent from their message. They are currently editing a schema.

Return a single word intent from this list:
- modify: wants to change something in the schema
- add_field: wants to add a new field
- remove_field: wants to remove a field
- test: wants to test the schema in sandbox mode
- save: wants to save the schema as draft
- activate: wants to activate the schema
- other: something else

Be strict: only return the words above."""

CLASSIFY_HR_INTENT_PROMPT = """HR message: {last_message}

Classify their intent. Return ONLY one word from: modify, add_field, remove_field, test, save, activate, or other."""

UPDATE_SCHEMA_SYSTEM = """You are an expert at updating JSON schema definitions based on natural language instructions.

The HR team is asking you to make a change to their current schema. Apply the change and return the updated JSON."""

UPDATE_SCHEMA_PROMPT = """Current schema:
{current_definition}

HR request: {hr_message}

Apply the requested change and return the updated schema JSON. Keep the same structure but modify/add/remove fields as needed."""

FORMAT_SCHEMA_SUMMARY = """Given a JSONB schema definition, format it as a human-readable bullet list of fields."""

FORMAT_SCHEMA_PROMPT = """Schema definition:
{definition}

Format this as a numbered list of fields with their type and required status. Example:
1. Full Name (text, required) - "Please tell me your full legal name"
2. Resume (file, required) - PDF file upload"""
