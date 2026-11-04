import { ChatSession } from '../types';

const STORAGE_KEY = 'reading_room_chat_sessions';

export function loadSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch (e) {
    console.error('Failed to load chat sessions from localStorage:', e);
    return [];
  }
}

export function saveSessions(sessions: ChatSession[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  } catch (e) {
    console.error('Failed to save chat sessions to localStorage:', e);
  }
}

export function generateSessionTitle(question: string): string {
  // Strip leading scope tags like [Scope: xxx] or [Referenced: xxx]
  let clean = question.replace(/\[Scope:[^\]]+\]/gi, '').replace(/\[Context[^\]]+\]/gi, '').trim();

  // Common question starters to distill
  const patterns: Array<[RegExp, string]> = [
    [/^what\s+is\s+the\s+standard\s+hardware\s+bundle/i, 'Remote Work Hardware & Stipend'],
    [/^what\s+encryption\s+algorithm/i, 'Backup Archive Encryption'],
    [/^what\s+were\s+acme.*total\s+revenue/i, 'Acme Q3 2026 Financials'],
    [/^under\s+what\s+conditions.*pto/i, 'PTO Carry-over Ceiling Exceptions'],
    [/^what\s+are\s+our\s+rollover\s+policies/i, 'PTO Rollover Policies'],
    [/^what\s+is\s+the\s+/i, ''],
    [/^what\s+are\s+the\s+/i, ''],
    [/^what\s+does\s+/i, ''],
    [/^how\s+do\s+we\s+/i, ''],
    [/^how\s+does\s+/i, ''],
    [/^how\s+to\s+/i, ''],
  ];

  for (const [regex, replacement] of patterns) {
    if (regex.test(clean)) {
      if (replacement) {
        return replacement;
      }
      clean = clean.replace(regex, '');
      break;
    }
  }

  // Capitalize first character and truncate if too long
  clean = clean.trim();
  if (!clean) return 'Archival Inquiry';
  const capitalized = clean.charAt(0).toUpperCase() + clean.slice(1);
  return capitalized.length > 40 ? `${capitalized.slice(0, 37)}…` : capitalized;
}
