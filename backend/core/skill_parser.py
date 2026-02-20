"""
core/skill_parser.py — Skill File Parser
==========================================
Parses .md and .yml skill files into structured data.

.md  → extracts frontmatter + splits into sections by ## headings
.yml → validates and returns as config dict

The structured output feeds into:
  - SkillRegistry (metadata + token counts)
  - SkillRAGEngine (chunked sections for embedding)
  - ContextBuilder (full content for direct injection)
"""

import re
import yaml
import frontmatter
from dataclasses import dataclass, field
from typing import Any
import structlog

log = structlog.get_logger(__name__)


@dataclass
class SkillSection:
    """One ## heading block from a markdown skill file."""
    title: str
    content: str
    level: int              # heading depth (2 = ##, 3 = ###)
    has_code_blocks: bool
    has_examples: bool


@dataclass
class ParsedMarkdownSkill:
    name: str
    description: str
    triggers: list[str]
    sections: list[SkillSection]
    full_content: str       # raw .md content for direct injection
    raw_frontmatter: dict[str, Any]


@dataclass
class ParsedYamlSkill:
    name: str
    description: str
    config: dict[str, Any]  # full parsed YAML as dict


class SkillParser:
    """
    Parses .md and .yml skill files.

    Usage:
        parser = SkillParser()
        result = parser.parse_markdown(md_content)
        result = parser.parse_yaml(yaml_content)
    """

    # ── Markdown Parser ───────────────────────────────────────────────────────

    def parse_markdown(self, content: str) -> dict[str, Any]:
        """
        Parse a .md skill file.

        Returns a dict with:
          - name, description, triggers (from frontmatter)
          - sections (list of {title, content, level, has_code_blocks, has_examples})
          - full_content (raw string)
        """
        try:
            post = frontmatter.loads(content)
            fm: dict = dict(post.metadata)
            body: str = post.content
        except Exception:
            # No frontmatter — treat entire file as body
            fm = {}
            body = content

        name        = fm.get("name", "")
        description = fm.get("description", "")
        triggers    = fm.get("triggers", [])
        if isinstance(triggers, str):
            triggers = [t.strip() for t in triggers.split(",")]

        sections = self._split_sections(body)

        # If no name in frontmatter, derive from first H1
        if not name:
            h1 = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            name = h1.group(1).strip() if h1 else "Unnamed Skill"

        return {
            "name": name,
            "description": description,
            "triggers": triggers,
            "sections": [self._section_to_dict(s) for s in sections],
            "full_content": content,
            "raw_frontmatter": fm,
        }

    def _split_sections(self, body: str) -> list[SkillSection]:
        """Split markdown body into sections at ## headings."""
        # Pattern: lines starting with ## or ###
        pattern = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)
        matches = list(pattern.finditer(body))

        if not matches:
            # No sections — treat entire body as one section
            return [SkillSection(
                title="Content",
                content=body.strip(),
                level=2,
                has_code_blocks="```" in body,
                has_examples=bool(re.search(r"example|e\.g\.|for instance", body, re.I)),
            )]

        sections = []
        for i, match in enumerate(matches):
            start = match.end()
            end   = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            text  = body[start:end].strip()
            level = len(match.group(1))   # ## = 2, ### = 3

            sections.append(SkillSection(
                title=match.group(2).strip(),
                content=text,
                level=level,
                has_code_blocks="```" in text,
                has_examples=bool(re.search(r"example|e\.g\.|for instance", text, re.I)),
            ))

        return sections

    def _section_to_dict(self, s: SkillSection) -> dict:
        return {
            "title": s.title,
            "content": s.content,
            "level": s.level,
            "has_code_blocks": s.has_code_blocks,
            "has_examples": s.has_examples,
        }

    # ── YAML Parser ───────────────────────────────────────────────────────────

    def parse_yaml(self, content: str) -> dict[str, Any]:
        """
        Parse a .yml skill/config file.

        Expected top-level keys (all optional):
          name, description, model, tools, constraints, system_prompt_append
        """
        try:
            config = yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            log.error("skill_parser.yaml_error", error=str(e))
            raise ValueError(f"Invalid YAML: {e}")

        if not isinstance(config, dict):
            raise ValueError("YAML skill must be a mapping (key: value) at the top level.")

        return {
            "name": config.get("name", "Unnamed Config"),
            "description": config.get("description", ""),
            "triggers": config.get("triggers", []),
            "sections": [],     # YAML skills don't split into sections
            "full_content": content,
            "config": config,   # full parsed config for ContextBuilder
        }

    # ── Chunk splitter (for embedding) ────────────────────────────────────────

    def chunk_for_embedding(
        self,
        sections: list[dict],
        max_chunk_tokens: int = 500,
    ) -> list[dict]:
        """
        Splits parsed sections into embedding-friendly chunks.
        Each chunk stays under max_chunk_tokens.

        Returns list of {chunk_id, title, content, section_index}
        """
        from core.token_counter import count_tokens

        chunks = []
        for idx, section in enumerate(sections):
            content = f"## {section['title']}\n\n{section['content']}"

            if count_tokens(content) <= max_chunk_tokens:
                chunks.append({
                    "chunk_id": f"{idx}_0",
                    "section_index": idx,
                    "title": section["title"],
                    "content": content,
                })
            else:
                # Split large sections by paragraph
                paragraphs = re.split(r"\n\n+", section["content"])
                current_chunk = f"## {section['title']}\n\n"
                chunk_num = 0

                for para in paragraphs:
                    candidate = current_chunk + para + "\n\n"
                    if count_tokens(candidate) > max_chunk_tokens and current_chunk.strip():
                        chunks.append({
                            "chunk_id": f"{idx}_{chunk_num}",
                            "section_index": idx,
                            "title": f"{section['title']} (part {chunk_num + 1})",
                            "content": current_chunk.strip(),
                        })
                        chunk_num += 1
                        current_chunk = para + "\n\n"
                    else:
                        current_chunk = candidate

                if current_chunk.strip():
                    chunks.append({
                        "chunk_id": f"{idx}_{chunk_num}",
                        "section_index": idx,
                        "title": f"{section['title']} (part {chunk_num + 1})" if chunk_num else section["title"],
                        "content": current_chunk.strip(),
                    })

        return chunks
