import json
import re
import html
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlsplit

from aqt import mw


@dataclass
class CommentThread:
    id: str
    author: str
    timestamp: str
    content_html: str
    selected_text: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "CommentThread":
        return CommentThread(
            id=data["id"],
            author=data["author"],
            timestamp=data["timestamp"],
            content_html=data["content_html"],
            selected_text=data.get("selected_text", ""),
        )


@dataclass
class CommentData:
    resolved: bool
    threads: List[CommentThread]
    selected_text: str = ""
    original_thread_id: str = ""

    def to_dict(self) -> dict:
        return {
            "resolved": self.resolved,
            "threads": [t.to_dict() for t in self.threads],
            "selected_text": self.selected_text,
            "original_thread_id": self.original_thread_id,
        }

    @staticmethod
    def from_dict(data: dict) -> "CommentData":
        return CommentData(
            resolved=data.get("resolved", False),
            threads=[CommentThread.from_dict(t) for t in data.get("threads", [])],
            selected_text=data.get("selected_text", ""),
            original_thread_id=data.get("original_thread_id", ""),
        )


@dataclass
class FieldCommentStore:
    field_name: str
    field_ord: int
    comments: Dict[str, CommentData] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "field_name": self.field_name,
            "field_ord": self.field_ord,
            "comments": {cid: cd.to_dict() for cid, cd in self.comments.items()},
        }

    @staticmethod
    def from_dict(data: dict) -> "FieldCommentStore":
        return FieldCommentStore(
            field_name=data["field_name"],
            field_ord=data["field_ord"],
            comments={cid: CommentData.from_dict(cd) for cid, cd in data.get("comments", {}).items()},
        )


COMMENT_DATA_DIV_PATTERN = re.compile(
    r'<div\s+id="anki-comments-data-([^"]+)"\s+style="display:\s*none;">(.*?)</div>',
    re.DOTALL
)

MOBILE_SCRIPT_START = "<!-- ANKIDOCCOMMENTS-MOBILE-HELPER:START -->"
MOBILE_SCRIPT_END = "<!-- ANKIDOCCOMMENTS-MOBILE-HELPER:END -->"
MOBILE_SCRIPT_BLOCK_PATTERN = re.compile(
    re.escape(MOBILE_SCRIPT_START) + r".*?" + re.escape(MOBILE_SCRIPT_END),
    re.DOTALL,
)
LEGACY_MOBILE_SCRIPT_PATTERN = re.compile(
    r"""<style\b(?=[^>]*\bid\s*=\s*["']ankidoccomments-mobile-css["'])[^>]*>.*?</style>\s*"""
    r"""<script\b[^>]*>.*?</script>""",
    re.IGNORECASE | re.DOTALL,
)

MARK_PATTERN = re.compile(
    r'<mark\s+class="gdoc-comment"\s+data-cid="([^"]+)"\s+data-field="([^"]+)">(.*?)</mark>',
    re.DOTALL
)

RESOLVED_CLASS_PATTERN = re.compile(
    r'<mark\s+class="gdoc-comment resolved"\s+data-cid="([^"]+)"\s+data-field="([^"]+)">(.*?)</mark>',
    re.DOTALL
)


def get_config() -> dict:
    addon_package = __package__.split(".")[0] if __package__ else "AnkiDocComments"
    return mw.addonManager.getConfig(addon_package) or {}


def generate_cid() -> str:
    return f"c_{uuid.uuid4().hex[:12]}"


def generate_tid() -> str:
    return f"t_{uuid.uuid4().hex[:12]}"


def get_current_timestamp() -> str:
    return datetime.now().isoformat()


def sanitize_html(content: str) -> str:
    allowed_tags = {
        "b", "i", "u", "strong", "em", "span", "br",
        "p", "div", "ul", "ol", "li", "blockquote", "a", "font",
    }

    class CommentHtmlParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.output: List[str] = []
            self.open_tags: List[str] = []

        def handle_starttag(self, tag: str, attrs: list) -> None:
            tag = tag.lower()
            if tag not in allowed_tags:
                return
            if tag == "font":
                color = dict(attrs).get("color") or ""
                tag = "span"
                if re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                    self.output.append(f'<span style="color:{color.lower()}">')
                    self.open_tags.append(tag)
                    return
            if tag == "br":
                self.output.append("<br>")
                return

            safe_attribute = ""
            if tag == "span":
                style = dict(attrs).get("style") or ""
                match = re.fullmatch(r"\s*color\s*:\s*(#[0-9a-fA-F]{6})\s*;?\s*", style)
                attributes = []
                span_attrs = dict(attrs)
                if span_attrs.get("class") == "anki-comment-spoiler":
                    attributes.append('class="anki-comment-spoiler"')
                if match:
                    attributes.append(f'style="color:{match.group(1).lower()}"')
                safe_attribute = (" " + " ".join(attributes)) if attributes else ""
            elif tag == "a":
                href = dict(attrs).get("href") or ""
                if urlsplit(href).scheme.lower() in {"http", "https", "mailto"}:
                    safe_attribute = f' href="{html.escape(href, quote=True)}"'
            self.output.append(f"<{tag}{safe_attribute}>")
            self.open_tags.append(tag)

        def handle_endtag(self, tag: str) -> None:
            tag = tag.lower()
            if tag == "font":
                tag = "span"
            if tag not in self.open_tags:
                return
            while self.open_tags:
                open_tag = self.open_tags.pop()
                self.output.append(f"</{open_tag}>")
                if open_tag == tag:
                    break

        def handle_data(self, data: str) -> None:
            self.output.append(html.escape(data, quote=False))

    parser = CommentHtmlParser()
    parser.feed(str(content or ""))
    parser.close()
    while parser.open_tags:
        parser.output.append(f"</{parser.open_tags.pop()}>")
    return "".join(parser.output)


class _VisibleTextParser(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=False)
        self.source = source
        self.line_starts = [0]
        self.line_starts.extend(
            index + 1 for index, character in enumerate(source) if character == "\n"
        )
        self.characters: List[str] = []
        self.source_spans: List[Tuple[int, int]] = []
        self.ignored_tags: List[str] = []

    def _source_offset(self) -> int:
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def handle_starttag(self, tag: str, attrs: list) -> None:
        tag = tag.lower()
        attributes = dict(attrs)
        if tag in {"script", "style", "template"} or (
            tag == "div" and (attributes.get("id") or "").startswith("anki-comments-data-")
        ):
            self.ignored_tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.ignored_tags:
            index = len(self.ignored_tags) - 1 - self.ignored_tags[::-1].index(tag)
            del self.ignored_tags[index:]

    def handle_data(self, data: str) -> None:
        if self.ignored_tags:
            return
        start = self._source_offset()
        self.characters.extend(data)
        self.source_spans.extend((start + index, start + index + 1) for index in range(len(data)))

    def handle_entityref(self, name: str) -> None:
        self._handle_reference(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self._handle_reference(f"&#{name};")

    def _handle_reference(self, reference: str) -> None:
        if self.ignored_tags:
            return
        start = self._source_offset()
        decoded = html.unescape(reference)
        self.characters.extend(decoded)
        self.source_spans.extend((start, start + len(reference)) for _ in decoded)


def _find_text_ranges(field_html: str, selected_text: str) -> List[Tuple[int, int]]:
    parser = _VisibleTextParser(field_html)
    parser.feed(field_html)
    parser.close()
    visible_text = "".join(parser.characters)

    ranges = []
    search_from = 0
    while selected_text:
        start = visible_text.find(selected_text, search_from)
        if start < 0:
            break
        end = start + len(selected_text)
        if end <= len(parser.source_spans):
            ranges.append((parser.source_spans[start][0], parser.source_spans[end - 1][1]))
        search_from = start + 1
    return ranges


def _wrap_selected_text(field_html: str, selected_text: str, cid: str, field_name: str, resolved: bool = False) -> Optional[str]:
    matches = _find_text_ranges(field_html, selected_text)
    if not matches:
        return None
    start, end = matches[0]
    open_tag = (
        f'<mark class="gdoc-comment{" resolved" if resolved else ""}" '
        f'data-cid="{html.escape(cid, quote=True)}" '
        f'data-field="{html.escape(field_name, quote=True)}">'
    )
    wrapped_text = field_html[start:end].replace("{{", "&#123;&#123;").replace("}}", "&#125;&#125;")
    return field_html[:start] + open_tag + wrapped_text + "</mark>" + field_html[end:]


def _serialize_comment_data(comments: dict) -> str:
    serialized = html.escape(json.dumps(comments, ensure_ascii=False), quote=False)
    return serialized.replace("{", "&#123;").replace("}", "&#125;")


def parse_comment_data(field_html: str, field_name: str) -> Tuple[str, Dict[str, CommentData]]:
    data_div_id = f"anki-comments-data-{field_name}"
    pattern = re.compile(
        rf'<div\s+id="{re.escape(data_div_id)}"\s+style="display:\s*none;">(.*?)</div>',
        re.DOTALL
    )

    match = pattern.search(field_html)
    comments: Dict[str, CommentData] = {}

    if match:
        try:
            data_json = html.unescape(match.group(1))
            data = json.loads(data_json)
            comments = {cid: CommentData.from_dict(cd) for cid, cd in data.items()}
        except (json.JSONDecodeError, KeyError, TypeError):
            comments = {}

        field_html = pattern.sub("", field_html)

    return field_html, comments


def inject_comment_anchors(field_html: str, comments: Dict[str, CommentData], field_name: str) -> str:
    field_html = re.sub(MARK_PATTERN, r'\3', field_html)
    field_html = re.sub(RESOLVED_CLASS_PATTERN, r'\3', field_html)

    for cid, comment_data in comments.items():
        search_text = comment_data.selected_text or next(
            (thread.selected_text for thread in comment_data.threads if thread.selected_text),
            "",
        )
        if not search_text and comment_data.threads:
            search_text = comment_data.threads[0].content_html
        if search_text:
            wrapped = _wrap_selected_text(field_html, search_text, cid, field_name, comment_data.resolved)
            if wrapped is not None:
                field_html = wrapped

    data_div = (
        f'<div id="anki-comments-data-{html.escape(field_name, quote=True)}" '
        f'style="display: none;">{_serialize_comment_data({cid: cd.to_dict() for cid, cd in comments.items()})}</div>'
    )
    field_html += data_div

    return field_html


def save_comment(note_id: int, field_name: str, cid: str, comment_data: CommentData, action: str = "update") -> bool:
    note = mw.col.get_note(note_id)
    if not note:
        return False

    if field_name not in note:
        return False

    field_html = note[field_name]
    cleaned_html, comments = parse_comment_data(field_html, field_name)

    if action == "create" or action == "update":
        comments[cid] = comment_data
    elif action == "delete":
        if cid in comments:
            del comments[cid]
    elif action == "resolve":
        if cid in comments:
            comments[cid].resolved = comment_data.resolved
    elif action == "add_reply":
        if cid in comments:
            new_thread = CommentThread.from_dict(comment_data.threads[0].to_dict())
            new_thread.id = generate_tid()
            comments[cid].threads.append(new_thread)
    elif action == "edit_reply":
        if cid in comments:
            for i, thread in enumerate(comments[cid].threads):
                if thread.id == comment_data.threads[0].id:
                    comments[cid].threads[i] = comment_data.threads[0]
                    break

    updated_html = inject_comment_anchors(cleaned_html, comments, field_name)
    note[field_name] = updated_html

    mw.col.update_note(note)
    mw.checkpoint("Add/Edit Comment")
    return True


def delete_comment(note_id: int, field_name: str, cid: str) -> bool:
    return save_comment(note_id, field_name, cid, CommentData(resolved=False, threads=[]), action="delete")


def resolve_comment(note_id: int, field_name: str, cid: str, resolved: bool) -> bool:
    note = mw.col.get_note(note_id)
    if not note:
        return False

    if field_name not in note:
        return False

    field_html = note[field_name]
    cleaned_html, comments = parse_comment_data(field_html, field_name)

    if cid in comments:
        comments[cid].resolved = resolved
        updated_html = inject_comment_anchors(cleaned_html, comments, field_name)
        note[field_name] = updated_html
        mw.col.update_note(note)
        mw.checkpoint("Resolve Comment")
        return True

    return False


def get_all_field_comments(note_id: int) -> Dict[str, Dict[str, CommentData]]:
    note = mw.col.get_note(note_id)
    if not note:
        return {}

    result = {}
    for field_name in note.keys():
        field_html = note[field_name]
        _, comments = parse_comment_data(field_html, field_name)
        if comments:
            result[field_name] = comments
    return result


def get_field_comments_for_card(note_id: int, field_names: List[str]) -> Dict[str, Dict[str, CommentData]]:
    note = mw.col.get_note(note_id)
    if not note:
        return {}

    result = {}
    for field_name in field_names:
        if field_name in note:
            field_html = note[field_name]
            _, comments = parse_comment_data(field_html, field_name)
            result[field_name] = comments
    return result


def build_init_payload(note_id: int, card_id: int, field_names: List[str]) -> dict:
    note = mw.col.get_note(note_id)
    if not note:
        return {"note_id": note_id, "card_id": card_id, "fields": {}, "config": get_config()}

    fields = {}
    for field_name in field_names:
        if field_name in note:
            field_html = note[field_name]
            field_ord = list(note.keys()).index(field_name)
            fields[field_name] = {"html": field_html, "ord": field_ord}

    return {
        "note_id": note_id,
        "card_id": card_id,
        "fields": fields,
        "config": get_config(),
    }


def handle_pycmd_save(payload: dict) -> dict:
    note_id = payload.get("note_id")
    selected_text = payload.get("selected_text", "").strip()
    comment_text = payload.get("comment_text", "").strip()
    cid = payload.get("cid") or generate_cid()
    field_name = payload.get("field_name")  # NEW: provided by frontend
    action = payload.get("action", "create")  # NEW: create, edit, resolve
    profile_name = getattr(getattr(mw, "pm", None), "name", None)
    if action in ("create", "reply"):
        if not isinstance(profile_name, str) or not profile_name.strip():
            return {"success": False, "error": "Không lấy được tên profile Anki hiện tại."}
        author = profile_name.strip()

    if not note_id:
        return {"success": False, "error": "Thiếu note_id"}

    note = mw.col.get_note(note_id)
    if not note:
        return {"success": False, "error": "Không tìm thấy Note"}

    # Use field_name from frontend if provided, otherwise fallback to searching
    target_field = field_name if isinstance(field_name, str) and field_name in note else None
    if not target_field and selected_text:
        matching_fields = [
            field_name_iter
            for field_name_iter, field_content in note.items()
            if _find_text_ranges(field_content, selected_text)
        ]
        if len(matching_fields) == 1:
            target_field = matching_fields[0]
        elif len(matching_fields) > 1:
            return {
                "success": False,
                "error": "Đoạn được chọn xuất hiện trong nhiều field. Hãy chọn field cần lưu.",
                "matching_fields": matching_fields,
            }

    if not target_field:
        return {"success": False, "error": f"Không tìm thấy đoạn '{selected_text}' trong thẻ"}

    field_html = note[target_field]

    # Đọc dữ liệu JSON comment ở cuối thẻ
    store_pattern = re.compile(
        rf'<div\s+id="anki-comments-data-{re.escape(target_field)}"\s+style="display:\s*none;">(.*?)</div>',
        re.DOTALL,
    )
    match = store_pattern.search(field_html)
    comments_dict = {}
    if match:
        try:
            comments_dict = json.loads(html.unescape(match.group(1)))
        except (json.JSONDecodeError, TypeError) as error:
            return {"success": False, "error": f"Dữ liệu comment đã lưu không hợp lệ: {error}"}
        field_html = store_pattern.sub("", field_html)

    # Convert newlines to <br> for HTML display
    comment_text_html = sanitize_html(comment_text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>'))

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    if action == "create":
        if not selected_text or not comment_text:
            return {"success": False, "error": "Thiếu dữ liệu để lưu comment"}

        original_thread_id = generate_tid()
        comments_dict[cid] = {
            "resolved": False,
            "selected_text": selected_text,
            "original_thread_id": original_thread_id,
            "threads": [{
                "id": original_thread_id,
                "author": author,
                "timestamp": now_str,
                "content_html": comment_text_html,
                "selected_text": selected_text,
            }],
        }

        # Bọc thẻ mark bôi vàng
        wrapped = _wrap_selected_text(field_html, selected_text, cid, target_field)
        if wrapped is None:
            return {"success": False, "error": "Không tìm thấy chính xác đoạn được chọn trong field."}
        field_html = wrapped

    elif action == "edit":
        if not cid or cid not in comments_dict:
            return {"success": False, "error": "Không tìm thấy comment để chỉnh sửa"}
        if not comment_text:
            return {"success": False, "error": "Nội dung comment trống"}

        thread_id = payload.get("thread_id")
        threads = comments_dict[cid].get("threads", [])
        target_thread = None
        for t in threads:
            if thread_id and t.get("id") == thread_id:
                target_thread = t
                break
        if target_thread is None and threads:
            target_thread = threads[0]

        if target_thread is None:
            return {"success": False, "error": "Không tìm thấy thread để chỉnh sửa"}

        target_thread["content_html"] = comment_text_html
        target_thread["timestamp"] = now_str

    elif action == "reply":
        if not cid or cid not in comments_dict:
            return {"success": False, "error": "Không tìm thấy comment"}
        if not comment_text:
            return {"success": False, "error": "Nội dung phản hồi trống"}

        new_thread = {
            "id": generate_tid(),
            "author": author,
            "timestamp": now_str,
            "content_html": comment_text_html,
            "selected_text": "",
        }
        comments_dict[cid]["threads"].append(new_thread)

    elif action == "delete_thread":
        if not cid or cid not in comments_dict:
            return {"success": False, "error": "Không tìm thấy ghi chú"}
        thread_id = payload.get("thread_id")
        threads = comments_dict[cid].get("threads", [])
        target_thread = next((thread for thread in threads if thread.get("id") == thread_id), None)
        if target_thread is None:
            return {"success": False, "error": "Không tìm thấy comment cần xóa"}

        if not comments_dict[cid].get("selected_text"):
            comments_dict[cid]["selected_text"] = next(
                (thread.get("selected_text", "") for thread in threads if thread.get("selected_text")),
                "",
            )
        if not comments_dict[cid].get("original_thread_id") and threads:
            comments_dict[cid]["original_thread_id"] = threads[0].get("id", "")
        comments_dict[cid]["threads"] = [
            thread for thread in threads if thread.get("id") != thread_id
        ]

        if not comments_dict[cid]["threads"]:
            del comments_dict[cid]
            mark_pattern = re.compile(
                rf'<mark\s+class="gdoc-comment(?:\s+resolved)?"\s+data-cid="{re.escape(cid)}"\s+data-field="{re.escape(target_field)}">(.*?)</mark>',
                re.DOTALL,
            )
            field_html = mark_pattern.sub(r'\1', field_html)

    elif action == "resolve":
        if not cid or cid not in comments_dict:
            return {"success": False, "error": "Không tìm thấy comment"}
        
        resolved = bool(payload.get("resolved", False))
        comments_dict[cid]["resolved"] = resolved

        # Update highlight mark class in field html
        mark_pattern = re.compile(
            rf'(<mark\s+class="gdoc-comment)(\s+resolved)?("\s+data-cid="{re.escape(cid)}"\s+data-field="{re.escape(target_field)}">)',
            re.DOTALL
        )
        if resolved:
            field_html = mark_pattern.sub(r'\1 resolved\3', field_html)
        else:
            field_html = mark_pattern.sub(r'\1\3', field_html)

    elif action == "delete":
        if not cid or cid not in comments_dict:
            return {"success": False, "error": "Không tìm thấy comment để xóa"}
        del comments_dict[cid]
        # Remove highlight mark from field html
        mark_pattern = re.compile(
            rf'<mark\s+class="gdoc-comment(?:\s+resolved)?"\s+data-cid="{re.escape(cid)}"\s+data-field="{re.escape(target_field)}">(.*?)</mark>',
            re.DOTALL
        )
        field_html = mark_pattern.sub(r'\1', field_html)

    else:
        return {"success": False, "error": f"Hành động không hợp lệ: {action}"}

    data_div = (
        f'<div id="anki-comments-data-{html.escape(target_field, quote=True)}" '
        f'style="display: none;">{_serialize_comment_data(comments_dict)}</div>'
    )
    note[target_field] = field_html + data_div

    mw.col.update_note(note)
    mw.checkpoint("Add/Edit Comment")

    return {
        "success": True,
        "cid": cid,
        "field_name": target_field,
        "comments": comments_dict,
    }



def export_mobile_template() -> str:
    template_path = os.path.join(os.path.dirname(__file__), "mobile_template_helper.html")
    with open(template_path, "r", encoding="utf-8") as template_file:
        return template_file.read()


def _remove_mobile_script(template: str) -> Tuple[str, bool]:
    start_count = template.count(MOBILE_SCRIPT_START)
    end_count = template.count(MOBILE_SCRIPT_END)
    if start_count != end_count:
        raise ValueError("Marker script AnkiDocComments bị thiếu đầu hoặc cuối trong template.")

    updated = MOBILE_SCRIPT_BLOCK_PATTERN.sub("", template)
    if MOBILE_SCRIPT_START in updated or MOBILE_SCRIPT_END in updated:
        raise ValueError("Marker script AnkiDocComments không hợp lệ trong template.")

    updated, legacy_count = LEGACY_MOBILE_SCRIPT_PATTERN.subn("", updated)
    return updated, start_count > 0 or legacy_count > 0


def update_mobile_card_template(template: str, helper_html: str) -> str:
    template, _ = _remove_mobile_script(template)
    base = template.rstrip()
    block = f"{MOBILE_SCRIPT_START}\n{helper_html.strip()}\n{MOBILE_SCRIPT_END}"
    return f"{base}\n\n{block}\n" if base else f"{block}\n"


def remove_mobile_card_template_script(template: str) -> Tuple[str, bool]:
    return _remove_mobile_script(template)


def update_notetype_mobile_script(notetype: dict, remove: bool = False) -> int:
    helper_html = "" if remove else export_mobile_template()
    replacements = []

    for template in notetype.get("tmpls", []):
        updated_fields = {}
        for field_name in ("qfmt", "afmt"):
            original = template.get(field_name, "")
            if remove:
                updated, changed = remove_mobile_card_template_script(original)
            else:
                updated = update_mobile_card_template(original, helper_html)
                changed = updated != original
            if changed:
                updated_fields[field_name] = updated
        if updated_fields:
            replacements.append((template, updated_fields))

    for template, updated_fields in replacements:
        template.update(updated_fields)

    if replacements:
        mw.col.models.update_dict(notetype)
    return len(replacements)
