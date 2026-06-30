"""Преобразование Markdown в Jira ADF."""

from __future__ import annotations

from html import unescape
from typing import Any, Dict, List
from xml.etree import ElementTree as ET

import markdown as markdown_lib


def markdown_to_adf(markdown_text: str) -> Dict[str, Any]:
    html = markdown_lib.markdown(
        markdown_text,
        extensions=["fenced_code", "tables", "sane_lists"],
        output_format="xhtml",
    )
    wrapped = f"<root>{html}</root>"
    root = ET.fromstring(wrapped)
    content = []
    for child in list(root):
        node = convert_block(child)
        if node:
            content.append(node)
    return {
        "type": "doc",
        "version": 1,
        "content": content or [{"type": "paragraph", "content": []}],
    }


def convert_block(element: ET.Element) -> Dict[str, Any] | None:
    tag = strip_tag(element.tag)

    if tag == "p":
        return paragraph_node(element)
    if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = int(tag[1])
        return {
            "type": "heading",
            "attrs": {"level": level},
            "content": inline_content(element),
        }
    if tag == "blockquote":
        content = []
        for child in list(element):
            node = convert_block(child)
            if node:
                content.append(node)
        return {"type": "blockquote", "content": content or [{"type": "paragraph", "content": inline_content(element)}]}
    if tag == "ul":
        return {"type": "bulletList", "content": list_items(element)}
    if tag == "ol":
        return {"type": "orderedList", "content": list_items(element)}
    if tag == "pre":
        return code_block_node(element)
    if tag == "hr":
        return {"type": "rule"}
    if tag == "table":
        return table_node(element)
    return paragraph_from_text(element)


def paragraph_node(element: ET.Element) -> Dict[str, Any]:
    return {"type": "paragraph", "content": inline_content(element)}


def paragraph_from_text(element: ET.Element) -> Dict[str, Any]:
    text = collect_text(element).strip()
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]} if text else {"type": "paragraph", "content": []}


def code_block_node(element: ET.Element) -> Dict[str, Any]:
    code_element = next(iter(list(element)), None)
    code_text = collect_text(code_element or element)
    attrs: Dict[str, Any] = {}
    if code_element is not None:
        class_name = code_element.attrib.get("class", "")
        if class_name.startswith("language-"):
            attrs["language"] = class_name.removeprefix("language-")
    return {
        "type": "codeBlock",
        **({"attrs": attrs} if attrs else {}),
        "content": [{"type": "text", "text": code_text}],
    }


def list_items(element: ET.Element) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for child in list(element):
        if strip_tag(child.tag) != "li":
            continue
        content: List[Dict[str, Any]] = []
        paragraph_buffer = inline_content(child, stop_on_nested_list=True)
        if paragraph_buffer:
            content.append({"type": "paragraph", "content": paragraph_buffer})
        for nested in list(child):
            nested_tag = strip_tag(nested.tag)
            if nested_tag == "ul":
                content.append({"type": "bulletList", "content": list_items(nested)})
            elif nested_tag == "ol":
                content.append({"type": "orderedList", "content": list_items(nested)})
        items.append({"type": "listItem", "content": content or [{"type": "paragraph", "content": []}]})
    return items


def table_node(element: ET.Element) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for section in list(element):
        section_tag = strip_tag(section.tag)
        if section_tag in {"thead", "tbody"}:
            rows.extend(table_rows(section))
        elif section_tag == "tr":
            rows.extend(table_rows(element))
            break
    return {"type": "table", "content": rows}


def table_rows(container: ET.Element) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for tr in list(container):
        if strip_tag(tr.tag) != "tr":
            continue
        cells = []
        for cell in list(tr):
            cell_tag = strip_tag(cell.tag)
            cell_type = "tableHeader" if cell_tag == "th" else "tableCell"
            cells.append(
                {
                    "type": cell_type,
                    "content": [{"type": "paragraph", "content": inline_content(cell)}],
                }
            )
        rows.append({"type": "tableRow", "content": cells})
    return rows


def inline_content(element: ET.Element, *, stop_on_nested_list: bool = False) -> List[Dict[str, Any]]:
    content: List[Dict[str, Any]] = []
    if element.text:
        push_text(content, element.text)

    for child in list(element):
        child_tag = strip_tag(child.tag)
        if stop_on_nested_list and child_tag in {"ul", "ol"}:
            break
        content.extend(convert_inline(child))
        if child.tail:
            push_text(content, child.tail)
    return content


def convert_inline(element: ET.Element) -> List[Dict[str, Any]]:
    tag = strip_tag(element.tag)
    if tag == "br":
        return [{"type": "hardBreak"}]
    if tag in {"strong", "b"}:
        return marked_text_nodes(element, "strong")
    if tag in {"em", "i"}:
        return marked_text_nodes(element, "em")
    if tag == "code":
        return marked_text_nodes(element, "code")
    if tag == "a":
        href = element.attrib.get("href")
        return marked_text_nodes(element, "link", attrs={"href": href} if href else None)
    return inline_content(element)


def marked_text_nodes(element: ET.Element, mark_type: str, attrs: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    nodes = inline_content(element)
    marked: List[Dict[str, Any]] = []
    for node in nodes:
        if node.get("type") == "text":
            marks = list(node.get("marks") or [])
            mark: Dict[str, Any] = {"type": mark_type}
            if attrs:
                mark["attrs"] = attrs
            marks.append(mark)
            node = {**node, "marks": marks}
        marked.append(node)
    return marked


def push_text(content: List[Dict[str, Any]], text: str) -> None:
    normalized = normalize_text(text)
    if not normalized:
        return
    content.append({"type": "text", "text": normalized})


def collect_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    parts: List[str] = []
    if element.text:
        parts.append(element.text)
    for child in list(element):
        parts.append(collect_text(child))
        if child.tail:
            parts.append(child.tail)
    return normalize_text("".join(parts))


def strip_tag(tag: str) -> str:
    return tag.split("}", 1)[-1]


def normalize_text(text: str) -> str:
    return unescape(text).replace("\xa0", " ")
