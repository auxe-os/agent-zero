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
  selectedTags: [], // Array of selected tags for multi-tag filtering
  searchQuery: "",
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
    let filtered = this.snippets;

    // Apply multi-tag filter (AND logic - snippet must have ALL selected tags)
    if (this.selectedTags.length > 0) {
      filtered = filtered.filter((item) =>
        this.selectedTags.every((selectedTag) =>
          item.tags?.some((tag) => tag.toLowerCase() === selectedTag.toLowerCase())
        )
      );
    }
    // Fallback to single tag filter for backward compatibility
    else if (this.filterTag) {
      filtered = filtered.filter((item) =>
        item.tags?.some((tag) => tag.toLowerCase() === this.filterTag?.toLowerCase())
      );
    }

    // Apply enhanced search filter with fuzzy matching
    if (this.searchQuery.trim()) {
      const query = this.searchQuery.toLowerCase().trim();
      filtered = filtered.map((item) => ({
        ...item,
        searchScore: this.calculateSearchScore(item, query)
      })).filter((item) => item.searchScore > 0)
        .sort((a, b) => b.searchScore - a.searchScore)
        .map(({ searchScore, ...item }) => item); // Remove searchScore from final result
    }

    return filtered;
  },

  // Enhanced search scoring with fuzzy matching
  calculateSearchScore(item, query) {
    let score = 0;
    const queryLower = query.toLowerCase();
    
    // Exact name match (highest priority)
    if (item.name.toLowerCase() === queryLower) {
      score += 100;
    }
    // Name starts with query
    else if (item.name.toLowerCase().startsWith(queryLower)) {
      score += 80;
    }
    // Name contains query
    else if (item.name.toLowerCase().includes(queryLower)) {
      score += 60;
    }
    // Fuzzy name match
    else {
      const nameScore = this.fuzzyMatch(item.name.toLowerCase(), queryLower);
      if (nameScore > 0) {
        score += nameScore * 50;
      }
    }

    // Content search
    if (item.content.toLowerCase().includes(queryLower)) {
      score += 30;
    } else {
      const contentScore = this.fuzzyMatch(item.content.toLowerCase(), queryLower);
      if (contentScore > 0) {
        score += contentScore * 20;
      }
    }

    // Tag search
    if (item.tags?.some((tag) => tag.toLowerCase().includes(queryLower))) {
      score += 40;
    } else if (item.tags?.some((tag) => {
      const tagScore = this.fuzzyMatch(tag.toLowerCase(), queryLower);
      return tagScore > 0;
    })) {
      score += 25;
    }

    return score;
  },

  // Simple fuzzy matching algorithm
  fuzzyMatch(text, pattern) {
    if (!text || !pattern) return 0;
    
    const textLower = text.toLowerCase();
    const patternLower = pattern.toLowerCase();
    
    // If pattern is longer than text, no match
    if (patternLower.length > textLower.length) return 0;
    
    // Exact match
    if (textLower === patternLower) return 1;
    
    // Check if all pattern characters exist in order in text
    let patternIndex = 0;
    let consecutiveMatches = 0;
    let maxConsecutive = 0;
    
    for (let i = 0; i < textLower.length && patternIndex < patternLower.length; i++) {
      if (textLower[i] === patternLower[patternIndex]) {
        patternIndex++;
        consecutiveMatches++;
        maxConsecutive = Math.max(maxConsecutive, consecutiveMatches);
      } else {
        consecutiveMatches = 0;
      }
    }
    
    // If we didn't match all pattern characters, no match
    if (patternIndex < patternLower.length) return 0;
    
    // Calculate score based on consecutive matches and pattern length
    const baseScore = maxConsecutive / patternLower.length;
    const lengthBonus = patternLower.length / textLower.length;
    
    return Math.min(baseScore + lengthBonus * 0.3, 1);
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

  // Search-related methods
  updateSearch() {
    this.setActiveIndex(0);
  },

  // Debounced search to improve performance
  debouncedSearch: null,
  
  initDebouncedSearch() {
    if (this.debouncedSearch) return;
    
    this.debouncedSearch = this.debounce(() => {
      this.setActiveIndex(0);
    }, 300);
  },

  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  onSearchInput() {
    this.initDebouncedSearch();
    this.debouncedSearch();
  },

  clearSearch() {
    this.searchQuery = "";
    this.setActiveIndex(0);
  },

  // Multi-tag filtering methods
  toggleTagFilter(tag) {
    const tagLower = tag.toLowerCase();
    const index = this.selectedTags.findIndex(t => t.toLowerCase() === tagLower);
    
    if (index >= 0) {
      // Remove tag if already selected
      this.selectedTags.splice(index, 1);
    } else {
      // Add tag if not selected
      this.selectedTags.push(tag);
    }
    
    // Clear single tag filter when using multi-tag
    this.filterTag = null;
    this.setActiveIndex(0);
  },

  clearAllTagFilters() {
    this.selectedTags = [];
    this.filterTag = null;
    this.setActiveIndex(0);
  },

  isTagSelected(tag) {
    return this.selectedTags.some(t => t.toLowerCase() === tag.toLowerCase());
  },

  getSelectedTagsCount() {
    return this.selectedTags.length;
  },

  getVisibleSnippetsCount() {
    return this.visibleSnippets().length;
  },

  selectNext() {
    this.setActiveIndex(this.activeIndex + 1);
  },

  selectPrevious() {
    this.setActiveIndex(this.activeIndex - 1);
  },

  applySelected() {
    const list = this.visibleSnippets();
    if (this.activeIndex >= 0 && this.activeIndex < list.length) {
      const selectedSnippet = list[this.activeIndex];
      if (selectedSnippet) {
        this.applySnippet(selectedSnippet.id, "insert");
      }
    }
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
