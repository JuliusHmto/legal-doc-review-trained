"""
Legal Document Review System - NDA Cleanup Service
Performs bilingual NDA cleanup and completion using LLM.
"""
from typing import Dict, Any, List
import json
from openai import AsyncOpenAI

from app.config import get_settings

settings = get_settings()

# System prompt containing all NDA cleanup rules
NDA_CLEANUP_SYSTEM_PROMPT = """You are a legal-document cleanup and completion assistant.

INPUT:
I will give you a bilingual (Indonesian–English) NDA draft that may contain:
- tracked-change callouts like "Deleted: …" and "Formatted: …"
- stray characters (e.g., single letters like "p" or "t")
- inconsistent defined terms (e.g., "Secret" vs "Confidential Information")
- party labels ("First Party / Second Party", "Pihak Pertama / Pihak Kedua")
- redundant fragments (e.g., "other Parties", "Para Pihak.")
- dispute-resolution text that may include an arbitration block that must be removed.

YOUR TASK:
Produce a clean final NDA text (bilingual, keeping the two-column meaning aligned) and a short change summary.

HARD RULES (must follow):
1) Apply deletions:
   - Remove every phrase shown in "Deleted: …" notes, including stray letters ("p", "t") and paragraph marks ("¶").
   - If a deletion note is truncated (has "…") remove the matching fragment you find in the text.

2) Apply formatting instructions conceptually:
   - Body text must be consistent: Arial 10pt equivalent, NOT BOLD.
   - Clause numbering must be consistent and restart correctly:
     - Main clauses are numbered (1,2,3…) with consistent hanging indent.
     - Sub-items use a,b,c… with consistent indentation.
   - Special line "the rest of this page is intentionally left blank" must be italic and not bold.

3) Terminology normalization:
   - Use "Confidential Information" consistently. Do NOT use "Secret" / "Secret Information".
   - Do NOT use "First Party/Second Party" or "Pihak Pertama/Pihak Kedua".
     Prefer "Disclosing Party" and "Receiving Party" (and define them once).

4) Remove party-fragment noise:
   - Remove fragments like "other Parties", "Para Pihak.", "Parties", "one of the Parties", "salah satu Pihak" when they are flagged as deletions.
   - Rewrite the sentence cleanly after removing them so the meaning is still correct and grammatical.

5) Dispute resolution clause:
   - If the text includes the deleted arbitration paragraph ("…shall be referred to and finally resolved by arbitration…") remove it entirely in BOTH languages.
   - Keep/replace with the version that resolves disputes amicably and then proceeds to the District Court of South Jakarta (as in the remaining visible clause).

6) Signatures:
   - Remove any deleted signatory names/titles (e.g., "Kusnad Rahardja", "President").
   - Keep whatever signatory name/title remains in the draft as the current correct one.
   - If signatory fields are missing, leave placeholders like: [NAME], [TITLE].

You must respond with a valid JSON object containing the following fields:
- cleaned_indonesian: The full cleaned Indonesian text
- cleaned_english: The full cleaned English text
- change_summary: Array of strings describing key changes made
- open_items: Array of objects with "placeholder" and "context" fields for items that cannot be safely inferred
- issues: Array of objects with "type", "original_text", "location", and "rule" fields describing specific issues found"""

NDA_CLEANUP_USER_PROMPT = """Please analyze and clean up the following document:

---
{document_content}
---

Respond with a JSON object containing:
1. "cleaned_indonesian": Full cleaned Indonesian text
2. "cleaned_english": Full cleaned English text  
3. "change_summary": List of key cleanups performed (term normalization, removal of party labels, arbitration removal, signature cleanup, stray-letter cleanup, etc.)
4. "open_items": List of anything that cannot be safely inferred (dates, addresses, signatory names/titles) with the placeholders used
5. "issues": List of specific issues found with type, original_text, location, and rule violated"""


class NDACleanupService:
    """Service for performing NDA cleanup and completion using LLM."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    async def perform_cleanup(self, document_content: str) -> Dict[str, Any]:
        """
        Perform NDA cleanup analysis on the document.
        
        Args:
            document_content: The raw document text to analyze
            
        Returns:
            Dictionary containing cleaned texts, change summary, open items, and issues
        """
        prompt = NDA_CLEANUP_USER_PROMPT.format(
            document_content=document_content[:30000]  # Limit content to avoid token limits
        )
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": NDA_CLEANUP_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for consistent, deterministic output
            max_completion_tokens=16000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Validate and process the result
        return self._process_cleanup_result(result, document_content)
    
    def _process_cleanup_result(self, result: Dict[str, Any], original_content: str) -> Dict[str, Any]:
        """Process and validate the cleanup result from LLM."""
        
        # Ensure all required fields exist with proper defaults
        processed = {
            "cleaned_indonesian": result.get("cleaned_indonesian", ""),
            "cleaned_english": result.get("cleaned_english", ""),
            "change_summary": result.get("change_summary", []),
            "open_items": result.get("open_items", []),
            "issues": result.get("issues", []),
            "original_content": original_content
        }
        
        # Ensure change_summary is a list
        if not isinstance(processed["change_summary"], list):
            processed["change_summary"] = [str(processed["change_summary"])]
        
        # Ensure open_items is a list of objects
        if not isinstance(processed["open_items"], list):
            processed["open_items"] = []
        
        # Validate and normalize open_items
        normalized_open_items = []
        for item in processed["open_items"]:
            if isinstance(item, dict):
                normalized_open_items.append({
                    "placeholder": item.get("placeholder", "[UNKNOWN]"),
                    "context": item.get("context", "Unknown context")
                })
            elif isinstance(item, str):
                normalized_open_items.append({
                    "placeholder": item,
                    "context": "Unknown context"
                })
        processed["open_items"] = normalized_open_items
        
        # Ensure issues is a list of objects
        if not isinstance(processed["issues"], list):
            processed["issues"] = []
        
        # Validate and normalize issues
        normalized_issues = []
        for issue in processed["issues"]:
            if isinstance(issue, dict):
                normalized_issues.append({
                    "type": issue.get("type", "general"),
                    "original_text": issue.get("original_text", ""),
                    "location": issue.get("location", "Unknown"),
                    "rule": issue.get("rule", "General cleanup rule")
                })
        processed["issues"] = normalized_issues
        
        # Calculate statistics
        processed["stats"] = {
            "total_issues": len(processed["issues"]),
            "total_open_items": len(processed["open_items"]),
            "total_changes": len(processed["change_summary"]),
            "issue_types": self._count_issue_types(processed["issues"])
        }
        
        return processed
    
    def _count_issue_types(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count issues by type."""
        type_counts = {}
        for issue in issues:
            issue_type = issue.get("type", "general")
            type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        return type_counts
    
    async def quick_analysis(self, document_content: str) -> Dict[str, Any]:
        """
        Perform a quick analysis to identify potential issues without full cleanup.
        Useful for initial assessment before full processing.
        """
        quick_prompt = f"""Quickly analyze this document and identify potential NDA cleanup issues.

Document:
{document_content[:10000]}

Respond with JSON containing:
- has_tracked_changes: boolean
- has_terminology_issues: boolean  
- has_party_label_issues: boolean
- has_arbitration_clause: boolean
- has_signature_issues: boolean
- summary: brief description of issues found
- estimated_issue_count: number"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a legal document analyzer. Respond only with valid JSON."
                },
                {
                    "role": "user",
                    "content": quick_prompt
                }
            ],
            temperature=0.1,
            max_completion_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
