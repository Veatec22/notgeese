import { Check, Undo2, Save, RefreshCw, Download, Search, Pencil, Clock, TriangleAlert, ListFilter, Layers, BookOpen, Languages, LogOut, ArrowLeft, ArrowRight, X, createElement } from 'lucide';

const icons = { check: Check, undo: Undo2, save: Save, refresh: RefreshCw, download: Download, search: Search, draft: Pencil, pending: Clock, conflict: TriangleAlert, filter: ListFilter, all: Layers, journal: BookOpen, languages: Languages, logout: LogOut, back: ArrowLeft, next: ArrowRight, close: X };
const cache = new Map<string, string>();

export function icon(name: keyof typeof icons): string {
  if (!cache.has(name)) cache.set(name, createElement(icons[name], { class: 'ws-icon', width: 16, height: 16, 'aria-hidden': 'true', focusable: 'false' }).outerHTML);
  return cache.get(name)!;
}
