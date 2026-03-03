import { tokenStore } from "./token";
import { getUsernameFromToken } from "./jwt";

export function getUsername(): string {
  return getUsernameFromToken(tokenStore.get()) ?? "user";
}