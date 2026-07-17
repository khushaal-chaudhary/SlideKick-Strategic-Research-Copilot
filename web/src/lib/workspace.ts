/**
 * BYOD workspace identity.
 *
 * Each browser gets a stable UUID (localStorage) used as the Neo4j
 * namespace for uploaded documents. Sent with uploads and research queries.
 */

const STORAGE_KEY = "slidekick_workspace_id";

export function getWorkspaceId(): string {
  if (typeof window === "undefined") return "";

  let id = window.localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id =
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `ws-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    window.localStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}
