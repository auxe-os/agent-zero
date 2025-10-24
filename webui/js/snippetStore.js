import { createStore } from "./AlpineStore.js";

const STORAGE_KEY = "agentZero.promptSnippets";

function safeJsonParse(value) {
  try {
    if (!value) return [];
    const parsed = JSON.parse(value);
    if (Array.isArray(parsed)) return parsed;
    return [];
  } catch (_error) {
    return [];
  }
}

function safeJsonStringify(value) {
  try {
    return JSON.stringify(value);
  } catch (_error) {
    return "[]";
  }
}

function generateId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2, 10);
}

const snippetsStore = createStore("snippets", {
  isOpen: false,
  mode: "list", // list | form
  snippets: [],
  activeIndex: 0,
  previewedId: null,
  filterTag: null,
  form: {
    id: null,
    name: "",
    content: "",
    tagsInput: "",
  },
  error: "",

  togglePanel(event) {
    event?.stopPropagation?.();
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  },

  open() {
    this.loadSnippets();
    this.isOpen = true;
    this.mode = "list";
    this.error = "";
    Promise.resolve().then(() => {
      const panel = document.getElementById("snippets_panel");
      panel?.focus({ preventScroll: true });
      this.setActiveIndex(0);
    });
  },

  close() {
    this.isOpen = false;
    this.previewedId = null;
    this.cancelEditing();
  },

  loadSnippets() {
    const stored = safeJsonParse(globalThis.localStorage?.getItem(STORAGE_KEY));
    this.snippets = stored.map((item) => ({
      id: item.id ?? generateId(),
      name: item.name ?? "Untitled",
      content: item.content ?? "",
      tags: Array.isArray(item.tags)
        ? item.tags
        : typeof item.tags === "string"
        ? item.tags
            .split(",")
            .map((tag) => tag.trim())
            .filter(Boolean)
        : [],
    }));
  },

  persistSnippets() {
    try {
      globalThis.localStorage?.setItem(
        STORAGE_KEY,
        safeJsonStringify(
          this.snippets.map((item) => ({
            id: item.id,
            name: item.name,
            content: item.content,
            tags: item.tags ?? [],
          }))
        )
      );
    } catch (_error) {
      this.error = "Unable to save snippets";
    }
  },

  visibleSnippets() {
    if (!this.filterTag) return this.snippets;
    return this.snippets.filter((item) =>
      item.tags?.some((tag) => tag.toLowerCase() === this.filterTag?.toLowerCase())
    );
  },

  availableTags() {
    const tagSet = new Set();
    for (const snippet of this.snippets) {
      (snippet.tags ?? []).forEach((tag) => {
        if (tag) tagSet.add(tag);
      });
    }
    return Array.from(tagSet).sort((a, b) => a.localeCompare(b));
  },

  toggleTagFilter(tag) {
    if (!tag) {
      this.filterTag = null;
    } else if (
      this.filterTag &&
      this.filterTag.toLowerCase() === tag.toLowerCase()
    ) {
      this.filterTag = null;
    } else {
      this.filterTag = tag;
    }
    this.setActiveIndex(0);
  },

  setActiveIndex(index) {
    const list = this.visibleSnippets();
    if (list.length === 0) {
      this.activeIndex = -1;
      this.previewedId = null;
      return;
    }
    const capped = Math.max(0, Math.min(index, list.length - 1));
    this.activeIndex = capped;
    this.previewedId = list[capped]?.id ?? null;
  },

  isActive(id) {
    const list = this.visibleSnippets();
    if (this.activeIndex < 0 || this.activeIndex >= list.length) return false;
    return list[this.activeIndex]?.id === id;
  },

  handleKeydown(event) {
    if (!this.isOpen || this.mode !== "list") return;
    const list = this.visibleSnippets();
    if (!list.length) return;

    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        this.setActiveIndex(this.activeIndex + 1);
        break;
      case "ArrowUp":
        event.preventDefault();
        this.setActiveIndex(this.activeIndex - 1);
        break;
      case "Enter":
        event.preventDefault();
        this.applySnippet(list[this.activeIndex]?.id, "insert");
        break;
      case "Delete":
      case "Backspace":
        if (event.metaKey || event.ctrlKey) {
          event.preventDefault();
          const snippet = list[this.activeIndex];
          if (snippet) this.deleteSnippet(snippet.id, { force: true });
        }
        break;
      default:
        break;
    }
  },

  startCreate() {
    this.mode = "form";
    this.form = {
      id: null,
      name: "",
      content: "",
      tagsInput: this.filterTag ? `${this.filterTag}, ` : "",
    };
    this.error = "";
  },

  startEdit(id) {
    const snippet = this.snippets.find((item) => item.id === id);
    if (!snippet) return;
    this.mode = "form";
    this.form = {
      id: snippet.id,
      name: snippet.name,
      content: snippet.content,
      tagsInput: (snippet.tags ?? []).join(", "),
    };
    this.error = "";
  },

  cancelEditing() {
    this.mode = "list";
    this.form = {
      id: null,
      name: "",
      content: "",
      tagsInput: "",
    };
    this.error = "";
  },

  saveCurrent() {
    const name = this.form.name.trim();
    const content = this.form.content.trim();
    const tags = this.form.tagsInput
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);

    if (!name) {
      this.error = "Give the snippet a name";
      return;
    }
    if (!content) {
      this.error = "Add some prompt text";
      return;
    }

    const existingIndex = this.snippets.findIndex(
      (item) => item.id === this.form.id
    );

    const snippetRecord = {
      id: this.form.id ?? generateId(),
      name,
      content,
      tags,
    };

    if (existingIndex >= 0) {
      this.snippets.splice(existingIndex, 1, snippetRecord);
    } else {
      this.snippets.push(snippetRecord);
    }

    this.persistSnippets();
    this.cancelEditing();
    const list = this.visibleSnippets();
    const idx = list.findIndex((item) => item.id === snippetRecord.id);
    this.setActiveIndex(idx >= 0 ? idx : 0);
  },

  deleteSnippet(id, options = { force: false }) {
    const index = this.snippets.findIndex((item) => item.id === id);
    if (index < 0) return;
    if (!options.force) {
      const confirmed = globalThis.confirm?.("Delete this snippet?");
      if (!confirmed) return;
    }
    this.snippets.splice(index, 1);
    this.persistSnippets();
    const list = this.visibleSnippets();
    this.setActiveIndex(Math.min(this.activeIndex, list.length - 1));
  },

  moveSnippet(id, direction) {
    const index = this.snippets.findIndex((item) => item.id === id);
    if (index < 0) return;
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= this.snippets.length) return;
    const [snippet] = this.snippets.splice(index, 1);
    this.snippets.splice(targetIndex, 0, snippet);
    this.persistSnippets();
    const list = this.visibleSnippets();
    const filteredIndex = list.findIndex((item) => item.id === snippet.id);
    this.setActiveIndex(filteredIndex >= 0 ? filteredIndex : this.activeIndex);
  },

  previewSnippet(id) {
    this.previewedId = id;
  },

  clearPreview(id) {
    if (this.previewedId === id) {
      this.previewedId = null;
    }
  },

  applySnippet(id, mode = "insert") {
    const snippet = this.snippets.find((item) => item.id === id);
    if (!snippet) return;
    const list = this.visibleSnippets();
    const idx = list.findIndex((item) => item.id === id);
    if (idx >= 0) this.setActiveIndex(idx);
    document.dispatchEvent(
      new CustomEvent("snippets:apply", {
        detail: {
          text: snippet.content,
          mode,
        },
      })
    );
    if (mode === "replace") {
      this.close();
    }
  },
});

snippetsStore.loadSnippets();

export default snippetsStore;
