import { api } from "./client";

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: { message: string; code: number } | null;
}

export interface UserProfile {
  user_id: number;
  email: string | null;
  full_name: string | null;
  phone: string | null;
  linkedin: string | null;
  github: string | null;
  location: string | null;
  profile_text: string | null;
}

export interface UserEducationEntry {
  entry_id: number;
  entry_type: "education" | "certificate";
  title: string;
  organization: string | null;
  date_text: string | null;
  description: string | null;
  display_order: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface UserEducationList {
  entries: UserEducationEntry[];
}

export interface UserEducationEntryInput {
  title: string;
  organization?: string | null;
  date_text?: string | null;
  description?: string | null;
}

export interface UserEducationEntriesUpdate {
  entries: UserEducationEntryInput[];
}

export function getProfile(): Promise<UserProfile> {
  return api
    .get<ApiResponse<UserProfile>>("/profile")
    .then((r) => r.data as UserProfile);
}

export function updateProfile(payload: Partial<Omit<UserProfile, "user_id">>): Promise<UserProfile> {
  return api
    .putJson<ApiResponse<UserProfile>>("/profile", payload)
    .then((r) => r.data as UserProfile);
}

export function getEducation(): Promise<UserEducationList> {
  return api
    .get<ApiResponse<UserEducationList>>("/profile/education")
    .then((r) => r.data ?? { entries: [] });
}

export function replaceEducation(payload: UserEducationEntriesUpdate): Promise<UserEducationList> {
  return api
    .putJson<ApiResponse<UserEducationList>>("/profile/education", payload)
    .then((r) => r.data ?? { entries: [] });
}

export function getCertifications(): Promise<UserEducationList> {
  return api
    .get<ApiResponse<UserEducationList>>("/profile/certifications")
    .then((r) => r.data ?? { entries: [] });
}

export function replaceCertifications(payload: UserEducationEntriesUpdate): Promise<UserEducationList> {
  return api
    .putJson<ApiResponse<UserEducationList>>("/profile/certifications", payload)
    .then((r) => r.data ?? { entries: [] });
}

