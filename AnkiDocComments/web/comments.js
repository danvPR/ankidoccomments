(function () {
  "use strict";

  const translations = {
    vi: {
      selectText: "Hãy chọn một đoạn chữ trước khi thêm nhận xét.",
      bold: "In đậm", italic: "In nghiêng", underline: "Gạch chân",
      bulletList: "Danh sách dấu chấm", numberList: "Danh sách đánh số",
      quote: "Trích dẫn", link: "Chèn liên kết", textColor: "Màu chữ",
      spoiler: "Ẩn chữ (spoiler)", removeFormat: "Xóa định dạng",
      enterLink: "Nhập liên kết:",
      revealSpoiler: "Bấm để hiện hoặc ẩn",
      commentPrefix: "Nhận xét",
      placeholder: "Nhập ghi chú / comment của bạn...",
      cancel: "Hủy", saveComment: "Lưu nhận xét",
      fieldChoice: "Đoạn này nằm trong nhiều field. Chọn nơi lưu:",
      fieldSelect: "Chọn field để lưu nhận xét",
      chooseField: "— Chọn field —",
      saveToField: "Lưu vào field đã chọn",
      error: "Lỗi",
      savedComments: "Ghi chú đã lưu",
      notFound: "Không tìm thấy nội dung nhận xét.",
      original: "Gốc", edit: "Sửa", deleteOne: "Xóa riêng comment này",
      replyPlaceholder: "Phản hồi...",
      deleteAll: "Xóa toàn bộ ghi chú",
      reopen: "Mở lại ghi chú", resolve: "Đánh dấu đã giải quyết",
      reply: "Phản hồi", sendReply: "Gửi phản hồi",
      deleteOneConfirm: "Xóa riêng comment này?",
      deleteConfirm: "Xóa nhận xét này?",
      resolved: "Đã giải quyết",
      editComment: "Chỉnh sửa nhận xét",
      saveChanges: "Lưu thay đổi",
    },
    en: {
      selectText: "Select some text before adding a comment.",
      bold: "Bold", italic: "Italic", underline: "Underline",
      bulletList: "Bulleted list", numberList: "Numbered list",
      quote: "Quote", link: "Insert link", textColor: "Text color",
      spoiler: "Hide text (spoiler)", removeFormat: "Clear formatting",
      enterLink: "Enter link:",
      revealSpoiler: "Click to reveal or hide",
      commentPrefix: "Comment",
      placeholder: "Enter your comment...",
      cancel: "Cancel", saveComment: "Save comment",
      fieldChoice: "This text occurs in multiple fields. Choose where to save:",
      fieldSelect: "Choose a field for the comment",
      chooseField: "— Choose a field —",
      saveToField: "Save to selected field",
      error: "Error",
      savedComments: "Saved comments",
      notFound: "Comment content was not found.",
      original: "Original", edit: "Edit", deleteOne: "Delete this comment",
      replyPlaceholder: "Reply...",
      deleteAll: "Delete the entire comment",
      reopen: "Reopen comment", resolve: "Resolve comment",
      reply: "Reply", sendReply: "Send reply",
      deleteOneConfirm: "Delete this comment?",
      deleteConfirm: "Delete this comment?",
      resolved: "Resolved",
      editComment: "Edit comment",
      saveChanges: "Save changes",
    },
  };

  let currentLanguage = "vi";
  function t(key) {
    return (translations[currentLanguage] && translations[currentLanguage][key])
      || translations.vi[key]
      || key;
  }

  let currentPayload = null;
  let activePopover = null;
  let mousedownHandler = null;
  let markHoverHandler = null;
  let lastSelection = null;

  window.ankiDocCommentsInit = function (payload) {
    lastSelection = null;
    currentPayload = payload;
    currentLanguage = payload && payload.config && payload.config.language === "en" ? "en" : "vi";
    if (activePopover) {
      activePopover.remove();
      activePopover = null;
    }
    bindSelectionEvents();
  };

  window.ankiDocCommentsCleanup = function () {
    document.removeEventListener("contextmenu", handleContextMenu, true);
    document.removeEventListener("selectionchange", trackSelection);
    document.removeEventListener("click", toggleCommentSpoiler);
    document.removeEventListener("keydown", handleCommentSpoilerKeydown);
    if (mousedownHandler) {
      document.removeEventListener("mousedown", mousedownHandler);
      mousedownHandler = null;
    }
    document.removeEventListener("click", handleMarkClick, true);
    if (markHoverHandler) {
      document.removeEventListener("mouseover", markHoverHandler, true);
      markHoverHandler = null;
    }
    if (activePopover) {
      activePopover.remove();
      activePopover = null;
    }
  };

  function bindSelectionEvents() {
    document.removeEventListener("contextmenu", handleContextMenu, true);
    document.addEventListener("contextmenu", handleContextMenu, true);

    document.removeEventListener("selectionchange", trackSelection);
    document.addEventListener("selectionchange", trackSelection);
    document.removeEventListener("click", toggleCommentSpoiler);
    document.addEventListener("click", toggleCommentSpoiler);
    document.removeEventListener("keydown", handleCommentSpoilerKeydown);
    document.addEventListener("keydown", handleCommentSpoilerKeydown);

    if (mousedownHandler) {
      document.removeEventListener("mousedown", mousedownHandler);
    }
    mousedownHandler = (e) => {
      const target = e.target && e.target.nodeType === Node.ELEMENT_NODE ? e.target : null;
      if (activePopover && target && !activePopover.contains(target) && !target.closest(".gdoc-comment")) {
        activePopover.remove();
        activePopover = null;
      }
    };
    document.addEventListener("mousedown", mousedownHandler);

    document.removeEventListener("click", handleMarkClick, true);
    document.removeEventListener("mouseover", handleMarkHover, true);
    if (currentPayload && currentPayload.config && currentPayload.config.trigger_mode === "hover") {
      markHoverHandler = handleMarkHover;
      document.addEventListener("mouseover", markHoverHandler, true);
    } else {
      document.addEventListener("click", handleMarkClick, true);
    }

    applyConfigStyles();
  }

  function toggleCommentSpoiler(event) {
    const target = event.target && event.target.closest
      ? event.target.closest(".anki-comment-popover .comment-content .anki-comment-spoiler")
      : null;
    if (!target) return;
    const revealed = target.classList.toggle("revealed");
    target.setAttribute("aria-expanded", String(revealed));
  }

  function handleCommentSpoilerKeydown(event) {
    if (event.key !== "Enter" && event.key !== " ") return;
    const target = event.target && event.target.closest
      ? event.target.closest(".anki-comment-popover .comment-content .anki-comment-spoiler")
      : null;
    if (!target) return;
    event.preventDefault();
    const revealed = target.classList.toggle("revealed");
    target.setAttribute("aria-expanded", String(revealed));
  }

  function trackSelection() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.toString().trim()) {
      lastSelection = null;
      return;
    }
    try {
      const range = sel.getRangeAt(0).cloneRange();
      const element = range.commonAncestorContainer.nodeType === Node.ELEMENT_NODE
        ? range.commonAncestorContainer
        : range.commonAncestorContainer.parentElement;
      if (element && element.closest(".anki-comment-popover")) {
        lastSelection = null;
        return;
      }
      const rect = range.getBoundingClientRect();
      const fieldContainer = element && element.closest
        ? element.closest(".anki-field, [data-field-name]")
        : null;
      lastSelection = {
        text: sel.toString().trim(),
        range: range,
        rect: rect,
        fieldName: fieldContainer && fieldContainer.dataset ? fieldContainer.dataset.fieldName : null,
        time: Date.now(),
      };
    } catch (e) {
      console.warn("AnkiDocComments: Could not track text selection", e);
    }
  }

  function handleContextMenu() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.toString().trim()) {
      lastSelection = null;
      return;
    }
    trackSelection();
  }

  window.ankiDocCommentsOpenCommentFromSelection = function () {
    if (!lastSelection || Date.now() - lastSelection.time > 30000) {
      alert(t("selectText"));
      return;
    }
    openNewCommentBox(
      lastSelection.text,
      lastSelection.rect,
      lastSelection.range.cloneRange(),
      lastSelection.fieldName,
    );
  };

  function handleMarkClick(e) {
    const mark = e.target && e.target.closest ? e.target.closest("mark.gdoc-comment") : null;
    if (mark) {
      e.stopPropagation();
      showExistingComment(mark);
    }
  }

  function handleMarkHover(e) {
    const mark = e.target && e.target.closest ? e.target.closest("mark.gdoc-comment") : null;
    if (mark && !mark.contains(e.relatedTarget)) showExistingComment(mark);
  }

  function applyConfigStyles() {
    const config = currentPayload && currentPayload.config ? currentPayload.config : {};
    const colors = config.highlight_colors || {};
    const variables = {
      "--comment-highlight-bg-light": colors.light,
      "--comment-highlight-bg-dark": colors.dark,
      "--comment-resolved-bg-light": colors.resolved_light,
      "--comment-resolved-bg-dark": colors.resolved_dark,
    };
    Object.entries(variables).forEach(([name, value]) => {
      if (typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value)) {
        document.documentElement.style.setProperty(name, value);
      }
    });
    const sidebarWidth = Number(config.sidebar_width);
    if (Number.isInteger(sidebarWidth) && sidebarWidth >= 100 && sidebarWidth <= 1200) {
      document.documentElement.style.setProperty("--sidebar-width", `${sidebarWidth}px`);
    }
  }

  function formatTimestamp(timestamp) {
    const value = String(timestamp || "");
    const normalized = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(value)
      ? value.replace(" ", "T") + ":00"
      : value;
    const date = new Date(normalized);
    if (Number.isNaN(date.getTime())) return value;
    const format = (currentPayload && currentPayload.config && currentPayload.config.timestamp_format)
      || "YYYY-MM-DD HH:mm";
    const tokens = {
      YYYY: String(date.getFullYear()),
      MM: String(date.getMonth() + 1).padStart(2, "0"),
      DD: String(date.getDate()).padStart(2, "0"),
      HH: String(date.getHours()).padStart(2, "0"),
      mm: String(date.getMinutes()).padStart(2, "0"),
    };
    return format.replace(/YYYY|MM|DD|HH|mm/g, (token) => tokens[token]);
  }

  function renderToolbarHtml() {
    return `<div class="comment-toolbar">
      <button type="button" class="toolbar-btn" data-cmd="bold" title="${t("bold")}"><b>B</b></button>
      <button type="button" class="toolbar-btn" data-cmd="italic" title="${t("italic")}"><i>I</i></button>
      <button type="button" class="toolbar-btn" data-cmd="underline" title="${t("underline")}"><u>U</u></button>
      <button type="button" class="toolbar-btn" data-cmd="insertUnorderedList" title="${t("bulletList")}">•≡</button>
      <button type="button" class="toolbar-btn" data-cmd="insertOrderedList" title="${t("numberList")}">1≡</button>
      <button type="button" class="toolbar-btn" data-cmd="formatBlock" data-value="blockquote" title="${t("quote")}">❝</button>
      <button type="button" class="toolbar-btn" data-cmd="createLink" title="${t("link")}">🔗</button>
      <button type="button" class="toolbar-btn color-picker-btn" data-cmd="foreColor" title="${t("textColor")}">
        A<input type="color" value="#e6c94a" aria-label="${t("textColor")}">
      </button>
      <button type="button" class="toolbar-btn" data-cmd="spoiler" title="${t("spoiler")}" aria-label="${t("spoiler")}">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12s3.2-6 9-6 9 6 9 6-3.2 6-9 6-9-6-9-6Z"/><path d="m4 4 16 16M10 10a2.8 2.8 0 0 0 4 4"/></svg>
      </button>
      <button type="button" class="toolbar-btn" data-cmd="removeFormat" title="${t("removeFormat")}">Tx</button>
    </div>`;
  }

  function renderActionIcon(name) {
    const icons = {
      delete: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M10 11v6m4-6v6M5 7l1 14h12l1-14M9 7V4h6v3"/></svg>',
      resolve: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>',
      reopen: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 7v5h-5M4 17v-5h5"/><path d="M5.5 9A7 7 0 0 1 18 6l2 6M4 12l2 6a7 7 0 0 0 12.5-3"/></svg>',
      reply: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H6l-3 2v-6a7.5 7.5 0 1 1 17-3.5Z"/><path d="M12.5 8v7m-3.5-3.5h7"/></svg>',
      send: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>',
    };
    return icons[name] || "";
  }

  function escapeAttribute(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function bindToolbar(root, editor) {
    let savedRange = null;
    const saveRange = () => {
      const selection = window.getSelection();
      if (selection && selection.rangeCount && editor.contains(selection.anchorNode)) {
        savedRange = selection.getRangeAt(0).cloneRange();
      }
    };
    ["keyup", "mouseup", "input"].forEach((eventName) => {
      editor.addEventListener(eventName, saveRange);
    });

    function restoreRange() {
      if (!savedRange) return;
      editor.focus();
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(savedRange);
    }

    root.querySelectorAll(".toolbar-btn").forEach((btn) => {
      btn.addEventListener("mousedown", (e) => {
        if (!e.target.closest('input[type="color"]')) e.preventDefault();
      });
      btn.addEventListener("click", (e) => {
        if (e.target.closest('input[type="color"]')) return;
        e.preventDefault();
        const cmd = btn.dataset.cmd;
        if (cmd === "spoiler") {
          restoreRange();
          const selection = window.getSelection();
          if (!selection || !selection.rangeCount || selection.isCollapsed) return;
          const range = selection.getRangeAt(0);
          if (!editor.contains(range.commonAncestorContainer) || !selection.toString().trim()) return;

          const spoiler = document.createElement("span");
          spoiler.className = "anki-comment-spoiler";
          spoiler.appendChild(range.extractContents());
          range.insertNode(spoiler);
          range.setStartAfter(spoiler);
          range.collapse(true);
          selection.removeAllRanges();
          selection.addRange(range);
        } else if (cmd === "createLink") {
          const url = window.prompt(t("enterLink"));
          if (!url) return;
          restoreRange();
          document.execCommand(cmd, false, url);
        } else if (cmd) {
          restoreRange();
          const input = btn.querySelector('input[type="color"]');
          const value = input ? input.value : (btn.dataset.value || null);
          document.execCommand(cmd, false, value);
        }
        saveRange();
      });
      const colorInput = btn.querySelector('input[type="color"]');
      if (colorInput) {
        colorInput.addEventListener("change", () => {
          restoreRange();
          document.execCommand("foreColor", false, colorInput.value);
          saveRange();
        });
      }
    });
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  function sanitizeCommentHtml(content) {
    const template = document.createElement("template");
    template.innerHTML = String(content || "");
    const allowedTags = new Set([
      "B", "I", "U", "STRONG", "EM", "SPAN", "BR",
      "P", "DIV", "UL", "OL", "LI", "BLOCKQUOTE", "A", "FONT",
    ]);

    function renderNode(node) {
      if (node.nodeType === Node.TEXT_NODE) return escapeHtml(node.nodeValue);
      if (node.nodeType !== Node.ELEMENT_NODE) return "";

      const sourceTag = node.tagName.toLowerCase();
      const tag = sourceTag === "font" ? "span" : sourceTag;
      const children = Array.from(node.childNodes).map(renderNode).join("");
      if (!allowedTags.has(node.tagName)) return children;
      if (tag === "br") return "<br>";

      let style = "";
      if (tag === "span") {
        const color = node.style.color || node.getAttribute("color") || "";
        const className = node.getAttribute("class") === "anki-comment-spoiler"
          ? ` class="anki-comment-spoiler" role="button" tabindex="0" aria-expanded="false" title="${t("revealSpoiler")}"`
          : "";
        const colorStyle = /^#[0-9a-f]{6}$/i.test(color) ? ` style="color:${color}"` : "";
        style = className + colorStyle;
      } else if (tag === "a") {
        const href = node.getAttribute("href") || "";
        try {
          const protocol = new URL(href, window.location.href).protocol;
          if (["http:", "https:", "mailto:"].includes(protocol)) {
            style = ` href="${escapeAttribute(href)}"`;
          }
        } catch (e) {
          return children;
        }
      }
      return `<${tag}${style}>${children}</${tag}>`;
    }

    return Array.from(template.content.childNodes).map(renderNode).join("");
  }

  function updateDataDiv(field, comments) {
    if (!field) return;
    const dataDiv = document.getElementById("anki-comments-data-" + field);
    if (dataDiv) {
      dataDiv.textContent = JSON.stringify(comments);
    }
  }

  function positionPopover(popover, rect) {
    const margin = 8;
    const bounds = popover.getBoundingClientRect();
    const maxLeft = Math.max(margin, window.innerWidth - bounds.width - margin);
    const left = Math.min(Math.max(margin, rect.left), maxLeft);
    let top = rect.bottom + margin;
    if (top + bounds.height > window.innerHeight - margin) {
      top = Math.max(margin, rect.top - bounds.height - margin);
    }
    popover.style.left = `${left}px`;
    popover.style.top = `${top}px`;
  }

  function openNewCommentBox(selectedText, rect, range, fieldName) {
    if (!currentPayload) {
      console.warn("AnkiDocComments: not initialized");
      return;
    }
    if (activePopover) activePopover.remove();

    activePopover = document.createElement("div");
    activePopover.className = "anki-comment-popover";

    activePopover.innerHTML = `
      <div class="popover-header">
        <span>${t("commentPrefix")}: "<b>${escapeHtml(selectedText.slice(0, 30))}</b>"</span>
        <button class="popover-close">&times;</button>
      </div>
      ${renderToolbarHtml()}
      <div class="comment-input-wrapper">
        <div class="comment-editor" contenteditable="true" role="textbox" aria-multiline="true"
          data-placeholder="${t("placeholder")}"></div>
      </div>
      <div class="popover-actions">
        <button class="btn btn-secondary btn-sm" id="btn-cancel">${t("cancel")}</button>
        <button class="btn btn-primary btn-sm" id="btn-save">${t("saveComment")}</button>
      </div>
    `;

    document.body.appendChild(activePopover);
    positionPopover(activePopover, rect);

    const editor = activePopover.querySelector(".comment-editor");
    const saveButton = activePopover.querySelector("#btn-save");
    let selectedFieldName = fieldName;
    let fieldChoice = null;
    bindToolbar(activePopover, editor);
    editor.focus();

    activePopover.querySelector(".popover-close").onclick = () => {
      activePopover.remove();
      activePopover = null;
    };
    activePopover.querySelector("#btn-cancel").onclick = () => {
      activePopover.remove();
      activePopover = null;
    };

    saveButton.onclick = () => {
      const commentText = editor.innerHTML.trim();
      if (!editor.textContent.trim()) return;
      if (fieldChoice && !selectedFieldName) {
        fieldChoice.querySelector("select").focus();
        return;
      }

      const payload = {
        note_id: currentPayload.note_id,
        selected_text: selectedText,
        comment_text: commentText,
        field_name: selectedFieldName,
        action: "create",
      };

      window.pycmd("ankicomments_save:" + JSON.stringify(payload), (res) => {
        try {
          const response = typeof res === "string" ? JSON.parse(res) : res;
          if (response.success) {
            const mark = document.createElement("mark");
            mark.className = "gdoc-comment";
            mark.dataset.cid = response.cid;
            mark.dataset.field = response.field_name;
            try {
              mark.appendChild(range.extractContents());
              range.insertNode(mark);
            } catch (err) {
              console.error("AnkiDocComments: Could not highlight the selected text", err);
            }
            updateDataDiv(response.field_name, response.comments);
            if (activePopover) {
              activePopover.remove();
              activePopover = null;
            }
          } else if (Array.isArray(response.matching_fields) && response.matching_fields.length > 1) {
            if (!fieldChoice) {
              fieldChoice = document.createElement("label");
              fieldChoice.className = "field-choice";
              fieldChoice.appendChild(document.createTextNode(
                t("fieldChoice")
              ));

              const select = document.createElement("select");
              select.setAttribute("aria-label", t("fieldSelect"));
              const placeholder = document.createElement("option");
              placeholder.value = "";
              placeholder.textContent = t("chooseField");
              placeholder.disabled = true;
              placeholder.selected = true;
              select.appendChild(placeholder);
              response.matching_fields.forEach((name) => {
                const option = document.createElement("option");
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
              });
              select.onchange = () => {
                selectedFieldName = select.value;
              };
              fieldChoice.appendChild(select);
              activePopover.querySelector(".popover-actions").before(fieldChoice);
              saveButton.textContent = t("saveToField");
            }
            positionPopover(activePopover, rect);
          } else {
            alert(t("error") + ": " + response.error);
          }
        } catch (e) {
          console.error(e);
        }
      });
    };
  }

  function renderExistingCommentHtml(commentData, field) {
    let html = `<div class="popover-header"><span>${t("savedComments")}</span><button class="popover-close">&times;</button></div>`;
    if (!commentData) {
      html += `<div style="padding:8px 0;">${t("notFound")}</div>`;
      return html;
    }
    html += `<div class="popover-threads">`;
    const originalThreadId = commentData.original_thread_id
      || ((commentData.threads || [])[0] || {}).id;
    (commentData.threads || []).forEach((thread) => {
      const date = formatTimestamp(thread.timestamp);
      const author = String(thread.author || "?");
      const isOriginal = thread.id === originalThreadId;
      html += `
        <div class="comment-thread${isOriginal ? " comment-thread-original" : ""}">
          <div class="comment-thread-meta">
            <div class="comment-author-line">
              <span class="comment-avatar">${escapeHtml(author.charAt(0).toUpperCase())}</span>
              <span class="comment-author">${escapeHtml(author)}</span>
              <span class="comment-time">${escapeHtml(date)}</span>
              ${isOriginal ? `<span class="comment-original-label">${t("original")}</span>` : ""}
            </div>
            <div class="comment-thread-actions">
              <button type="button" class="thread-action btn-edit-thread" data-thread-id="${escapeAttribute(thread.id)}" title="${t("edit")}">${t("edit")}</button>
              <button type="button" class="thread-action thread-action-delete btn-delete-thread" data-thread-id="${escapeAttribute(thread.id)}" title="${t("deleteOne")}">${t("deleteOne")}</button>
            </div>
          </div>
          <div class="comment-content">${sanitizeCommentHtml(thread.content_html)}</div>
        </div>`;
    });
    html += `</div>`;
    html += `
      <div class="comment-input-wrapper reply-composer" hidden>
        ${renderToolbarHtml()}
        <div id="reply-input" class="comment-editor" contenteditable="true" role="textbox"
          aria-multiline="true" data-placeholder="${t("replyPlaceholder")}"></div>
      </div>
    `;
    html += `<div class="popover-actions">
      <button type="button" class="icon-action icon-action-danger" id="btn-delete"
        title="${t("deleteAll")}" aria-label="${t("deleteAll")}">${renderActionIcon("delete")}</button>
      <button type="button" class="icon-action" id="btn-resolve"
        title="${commentData.resolved ? t("reopen") : t("resolve")}"
        aria-label="${commentData.resolved ? t("reopen") : t("resolve")}">
        ${renderActionIcon(commentData.resolved ? "reopen" : "resolve")}
      </button>
      <button type="button" class="icon-action icon-action-primary" id="btn-reply"
        title="${t("reply")}" aria-label="${t("reply")}" aria-expanded="false">${renderActionIcon("reply")}</button>
    </div>`;
    if (commentData.resolved) {
      html += `<div class="popover-resolved">✓ ${t("resolved")}</div>`;
    }
    return html;
  }

  function showExistingComment(mark) {
    if (activePopover) activePopover.remove();

    const cid = mark.dataset.cid;
    const field = mark.dataset.field;

    let dataDiv = null;
    dataDiv = document.getElementById("anki-comments-data-" + field);

    let commentData = null;
    if (dataDiv) {
      try {
        const json = JSON.parse(dataDiv.textContent || dataDiv.innerText || "{}");
        commentData = json[cid];
      } catch (e) {
        console.warn('AnkiDocComments: Failed to parse comment data', e);
      }
    }

    const rect = mark.getBoundingClientRect();
    activePopover = document.createElement("div");
    activePopover.className = "anki-comment-popover comment-view-popover";

    activePopover.innerHTML = renderExistingCommentHtml(commentData, field);
    document.body.appendChild(activePopover);
    positionPopover(activePopover, rect);

    activePopover.querySelector(".popover-close").onclick = () => {
      activePopover.remove();
      activePopover = null;
    };

    activePopover.querySelectorAll(".btn-edit-thread").forEach((btn) => {
      btn.onclick = () => {
        const threadId = btn.dataset.threadId;
        const thread = (commentData && commentData.threads)
          ? commentData.threads.find((t) => t.id === threadId)
          : null;
        openEditCommentBox(mark, commentData, cid, field, thread, rect);
      };
    });

    activePopover.querySelectorAll(".btn-delete-thread").forEach((btn) => {
      btn.onclick = () => {
        if (!confirm(t("deleteOneConfirm"))) return;
        const payload = {
          note_id: currentPayload.note_id,
          cid: cid,
          thread_id: btn.dataset.threadId,
          field_name: field,
          action: "delete_thread",
        };
        window.pycmd("ankicomments_save:" + JSON.stringify(payload), (res) => {
          try {
            const response = typeof res === "string" ? JSON.parse(res) : res;
            if (!response.success) {
              alert(t("error") + ": " + response.error);
              return;
            }
            updateDataDiv(field, response.comments);
            if (!response.comments || !response.comments[cid]) {
              const parent = mark.parentNode;
              if (parent) {
                while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
                parent.removeChild(mark);
              }
              if (activePopover) {
                activePopover.remove();
                activePopover = null;
              }
            } else {
              showExistingComment(mark);
            }
          } catch (e) {
            console.error(e);
          }
        });
      };
    });

    const deleteBtn = activePopover.querySelector("#btn-delete");
    if (deleteBtn) {
      deleteBtn.onclick = () => {
        if (!confirm(t("deleteConfirm"))) return;
        const payload = {
          note_id: currentPayload.note_id,
          cid: cid,
          field_name: field,
          action: "delete",
        };
        window.pycmd("ankicomments_save:" + JSON.stringify(payload), (res) => {
          try {
            const response = typeof res === "string" ? JSON.parse(res) : res;
            if (response.success) {
              updateDataDiv(field, response.comments);
              // remove mark highlight
              const parent = mark.parentNode;
              if (parent) {
                while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
                parent.removeChild(mark);
              }
              if (activePopover) {
                activePopover.remove();
                activePopover = null;
              }
            } else {
              alert(t("error") + ": " + response.error);
            }
          } catch (e) {
            console.error(e);
          }
        });
      };
    }

    const resolveBtn = activePopover.querySelector("#btn-resolve");
    if (resolveBtn) {
      resolveBtn.onclick = () => toggleResolveComment(mark, commentData, cid, field);
    }

    const replyBtn = activePopover.querySelector("#btn-reply");
    if (replyBtn) {
      replyBtn.onclick = () => {
        const composer = activePopover.querySelector(".reply-composer");
        const editor = activePopover.querySelector("#reply-input");
        if (composer.hidden) {
          composer.hidden = false;
          replyBtn.innerHTML = renderActionIcon("send");
          replyBtn.title = t("sendReply");
          replyBtn.setAttribute("aria-label", t("sendReply"));
          replyBtn.setAttribute("aria-expanded", "true");
          positionPopover(activePopover, rect);
          editor.focus();
          return;
        }
        const commentText = editor ? editor.innerHTML.trim() : "";
        if (!editor || !editor.textContent.trim()) return;
        const payload = {
          note_id: currentPayload.note_id,
          cid: cid,
          comment_text: commentText,
          field_name: field,
          action: "reply",
        };
        window.pycmd("ankicomments_save:" + JSON.stringify(payload), (res) => {
          try {
            const response = typeof res === "string" ? JSON.parse(res) : res;
            if (response.success) {
              updateDataDiv(field, response.comments);
              showExistingComment(mark);
            } else {
              alert(t("error") + ": " + response.error);
            }
          } catch (e) {
            console.error(e);
          }
        });
      };
    }

    const replyEditor = activePopover.querySelector("#reply-input");
    if (replyEditor) {
      const toolbar = activePopover.querySelector(".comment-toolbar");
      if (toolbar) bindToolbar(toolbar, replyEditor);
    }
  }

  function openEditCommentBox(mark, commentData, cid, field, thread, rect) {
    if (!thread) return;
    if (activePopover) activePopover.remove();

    activePopover = document.createElement("div");
    activePopover.className = "anki-comment-popover";

    activePopover.innerHTML = `
      <div class="popover-header">
        <span>${t("editComment")}</span>
        <button class="popover-close">&times;</button>
      </div>
      ${renderToolbarHtml()}
      <div class="comment-input-wrapper">
        <div class="comment-editor" contenteditable="true" role="textbox" aria-multiline="true"></div>
      </div>
      <div class="popover-actions">
        <button class="btn btn-secondary btn-sm" id="btn-cancel">${t("cancel")}</button>
        <button class="btn btn-primary btn-sm" id="btn-save-edit">${t("saveChanges")}</button>
      </div>
    `;

    document.body.appendChild(activePopover);
    positionPopover(activePopover, rect);

    const editor = activePopover.querySelector(".comment-editor");
    editor.innerHTML = sanitizeCommentHtml(thread.content_html);
    bindToolbar(activePopover, editor);
    editor.focus();

    activePopover.querySelector(".popover-close").onclick = () => {
      activePopover.remove();
      activePopover = null;
    };
    activePopover.querySelector("#btn-cancel").onclick = () => {
      activePopover.remove();
      activePopover = null;
    };

    activePopover.querySelector("#btn-save-edit").onclick = () => {
      const commentText = editor.innerHTML.trim();
      if (!editor.textContent.trim()) return;

      const payload = {
        note_id: currentPayload.note_id,
        cid: cid,
        thread_id: thread.id,
        comment_text: commentText,
        field_name: field,
        action: "edit",
      };

      window.pycmd("ankicomments_save:" + JSON.stringify(payload), (res) => {
        try {
          const response = typeof res === "string" ? JSON.parse(res) : res;
          if (response.success) {
            updateDataDiv(field, response.comments);
            if (activePopover) {
              activePopover.remove();
              activePopover = null;
            }
            showExistingComment(mark);
          } else {
            alert(t("error") + ": " + response.error);
          }
        } catch (e) {
          console.error(e);
        }
      });
    };
  }

  function toggleResolveComment(mark, commentData, cid, field) {
    const resolved = commentData ? !commentData.resolved : false;
    const payload = {
      note_id: currentPayload.note_id,
      cid: cid,
      field_name: field,
      resolved: resolved,
      action: "resolve",
    };

    window.pycmd("ankicomments_save:" + JSON.stringify(payload), (res) => {
      try {
        const response = typeof res === "string" ? JSON.parse(res) : res;
        if (response.success) {
          if (activePopover) {
            activePopover.remove();
            activePopover = null;
          }
          if (resolved) {
            mark.classList.add("resolved");
          } else {
            mark.classList.remove("resolved");
          }
          updateDataDiv(field, response.comments);
        } else {
          alert(t("error") + ": " + response.error);
        }
      } catch (e) {
        console.error(e);
      }
    });
  }
})();
