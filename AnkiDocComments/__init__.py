import json
import os

from aqt import mw, gui_hooks
from aqt.qt import QAction, QApplication, QInputDialog
from aqt.webview import WebContent
from aqt.reviewer import Reviewer
from aqt.utils import showInfo, showWarning

from .core import (
    get_config,
    handle_pycmd_save,
    export_mobile_template,
    update_notetype_mobile_script,
)

COMMENTS_CSS = ""
COMMENTS_JS = ""
ADDON_DIR = os.path.dirname(__file__)
current_review_note_id = None
ADDON_PACKAGE = __package__.split(".")[0] if __package__ else "AnkiDocComments"

try:
    with open(os.path.join(ADDON_DIR, "web", "comments.css"), "r", encoding="utf-8") as f:
        COMMENTS_CSS = f.read()
except FileNotFoundError:
    pass

try:
    with open(os.path.join(ADDON_DIR, "web", "comments.js"), "r", encoding="utf-8") as f:
        COMMENTS_JS = f.read()
except FileNotFoundError:
    pass


def on_webview_will_set_content(web_content: WebContent, context) -> None:
    # Check if this is a reviewer webview context
    # In Anki 26.x, context has a `kind` attribute or we check the webview
    if context is None:
        return
    
    # Try multiple ways to identify reviewer context
    is_reviewer = False
    if hasattr(context, 'kind') and context.kind == 'reviewer':
        is_reviewer = True
    elif hasattr(context, '__class__') and 'Reviewer' in context.__class__.__name__:
        is_reviewer = True
    elif hasattr(context, 'webview') and hasattr(context.webview, 'kind') and context.webview.kind == 'reviewer':
        is_reviewer = True
    
    if not is_reviewer:
        return

    if COMMENTS_CSS:
        web_content.head += f'<style id="ankidoccomments-css">{COMMENTS_CSS}</style>'
    if COMMENTS_JS:
        web_content.head += f'<script id="ankidoccomments-js">{COMMENTS_JS}</script>'


def on_reviewer_did_show_question(card) -> None:
    _initialize_card(card, "question")


def on_reviewer_did_show_answer(card) -> None:
    _initialize_card(card, "answer")


def _initialize_card(card, side: str) -> None:
    global current_review_note_id
    current_review_note_id = card.note().id
    if not hasattr(mw, "reviewer") or not mw.reviewer or not mw.reviewer.web:
        return

    note = card.note()
    payload = {
        "note_id": note.id,
        "card_id": card.id,
        "fields": dict(note.items()),
        "config": get_config(),
    }

    try:
        mw.reviewer.web.eval(f"window.ankiDocCommentsInit && window.ankiDocCommentsInit({json.dumps(payload)});")
    except Exception as e:
        print(f"AnkiDocComments: Failed to initialize card: {e}")


def on_reviewer_will_end() -> None:
    global current_review_note_id
    current_review_note_id = None
    if hasattr(mw, "reviewer") and mw.reviewer and mw.reviewer.web:
        try:
            mw.reviewer.web.eval("window.ankiDocCommentsCleanup && window.ankiDocCommentsCleanup()")
        except Exception:
            pass


def on_js_message(handled: tuple, message: str, context: object) -> tuple:
    if not isinstance(context, Reviewer):
        return handled
    if message.startswith("ankicomments_save:"):
        payload_raw = message[len("ankicomments_save:"):]
        try:
            payload = json.loads(payload_raw)
            result = handle_pycmd_save(payload)
            return (True, result)
        except Exception as e:
            return (True, {"success": False, "error": str(e)})
    return handled


def on_webview_will_show_context_menu(webview, menu) -> None:
    if not current_review_note_id or not mw.reviewer or webview is not mw.reviewer.web:
        return
    if not webview.hasSelection():
        return

    menu.addSeparator()
    language = get_config().get("language", "vi")
    add_comment_action = menu.addAction("Add comment" if language == "en" else "Thêm nhận xét")
    add_comment_action.triggered.connect(
        lambda _checked=False: webview.eval(
            "window.ankiDocCommentsOpenCommentFromSelection && "
            "window.ankiDocCommentsOpenCommentFromSelection()"
        )
    )


def copy_mobile_template() -> None:
    template = export_mobile_template()
    clipboard = QApplication.clipboard()
    clipboard.setText(template)
    from aqt.utils import tooltip
    tooltip("Mobile template copied to clipboard!")


def manage_mobile_template_script(remove: bool) -> None:
    if not mw.col:
        showWarning("Please open a profile before managing card templates.")
        return

    note_types = mw.col.models.all()
    if not note_types:
        showInfo("No note types were found in this collection.")
        return

    names = [notetype["name"] for notetype in note_types]
    name, confirmed = QInputDialog.getItem(
        mw,
        "Remove AnkiDocComments mobile script" if remove else "Add/update AnkiDocComments mobile script",
        "Choose a note type:",
        names,
        0,
        False,
    )
    if not confirmed:
        return

    notetype = next((item for item in note_types if item["name"] == name), None)
    if notetype is None:
        showWarning("The selected note type could not be found.")
        return

    try:
        updated_count = update_notetype_mobile_script(notetype, remove=remove)
    except ValueError as error:
        showWarning(str(error))
        return

    if updated_count:
        verb = "removed from" if remove else "added/updated in"
        from aqt.utils import tooltip
        tooltip(f"AnkiDocComments mobile script {verb} {updated_count} card template(s).")
    else:
        message = (
            "No AnkiDocComments mobile script was found in that note type."
            if remove
            else "The AnkiDocComments mobile script is already up to date."
        )
        showInfo(message)


def open_settings() -> None:
    from .settings_dialog import SettingsDialog
    dialog = SettingsDialog(mw)
    dialog.exec()


def ensure_language_selected() -> None:
    config = get_config()
    if config.get("language") in {"vi", "en"}:
        return

    names = ["Tiếng Việt", "English"]
    name, confirmed = QInputDialog.getItem(
        mw,
        "AnkiDocComments - Language / Ngôn ngữ",
        "Chọn ngôn ngữ / Choose language:",
        names,
        0,
        False,
    )
    if not confirmed:
        name = "Tiếng Việt"

    config["language"] = "vi" if name == "Tiếng Việt" else "en"
    mw.addonManager.writeConfig(ADDON_PACKAGE, config)


def setup_menu() -> None:
    language = get_config().get("language", "vi")
    localized = {
        "vi": {
            "addon": "AnkiDocComments",
            "copy": "Sao chép mã mẫu di động",
            "add": "Thêm/cập nhật mã di động vào kiểu thẻ...",
            "remove": "Gỡ mã di động khỏi kiểu thẻ...",
            "settings": "Cài đặt",
        },
        "en": {
            "addon": "AnkiDocComments",
            "copy": "Copy Mobile Template Code",
            "add": "Add/update mobile script for a note type...",
            "remove": "Remove mobile script from a note type...",
            "settings": "Settings",
        },
    }[language]
    menu = mw.form.menuTools
    submenu = menu.addMenu(localized["addon"])

    copy_action = QAction(localized["copy"], mw)
    copy_action.triggered.connect(copy_mobile_template)
    submenu.addAction(copy_action)

    add_mobile_script_action = QAction(localized["add"], mw)
    add_mobile_script_action.triggered.connect(
        lambda _checked=False: manage_mobile_template_script(remove=False)
    )
    submenu.addAction(add_mobile_script_action)

    remove_mobile_script_action = QAction(localized["remove"], mw)
    remove_mobile_script_action.triggered.connect(
        lambda _checked=False: manage_mobile_template_script(remove=True)
    )
    submenu.addAction(remove_mobile_script_action)

    settings_action = QAction(localized["settings"], mw)
    settings_action.triggered.connect(open_settings)
    submenu.addAction(settings_action)


def init_addon() -> None:
    gui_hooks.webview_will_set_content.append(on_webview_will_set_content)
    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_show_question)
    gui_hooks.reviewer_did_show_answer.append(on_reviewer_did_show_answer)
    gui_hooks.reviewer_will_end.append(on_reviewer_will_end)
    gui_hooks.webview_did_receive_js_message.append(on_js_message)
    gui_hooks.webview_will_show_context_menu.append(on_webview_will_show_context_menu)
    if hasattr(gui_hooks, "profile_did_open"):
        gui_hooks.profile_did_open.append(ensure_language_selected)

    ensure_language_selected()
    setup_menu()


init_addon()