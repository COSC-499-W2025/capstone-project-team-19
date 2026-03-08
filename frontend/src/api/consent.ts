import { api } from "./client";

export type ConsentStatusValue = "accepted" | "rejected";

export type ApiError = {
  message: string;
  code: number;
};

export type ApiResponse<T> = {
  success: boolean;
  data: T | null;
  error: ApiError | null;
};

export type ConsentRecord = {
  consent_id: number;
  user_id: number;
  status: ConsentStatusValue;
  timestamp: string;
};

export type ConsentStatus = {
  user_id: number;
  internal_consent: ConsentStatusValue | null;
  external_consent: ConsentStatusValue | null;
};

export function getConsentStatus() {
  return api.get<ApiResponse<ConsentStatus>>("/privacy-consent/status");
}

export function postInternalConsent(status: ConsentStatusValue) {
  return api.postJson<ApiResponse<ConsentRecord>>("/privacy-consent/internal", { status });
}

export function postExternalConsent(status: ConsentStatusValue) {
  return api.postJson<ApiResponse<ConsentRecord>>("/privacy-consent/external", { status });
}
