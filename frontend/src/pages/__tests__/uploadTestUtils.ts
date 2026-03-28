import type { ConsentRecord, ConsentStatus, ConsentStatusValue } from "../../api/consent";
import { tokenStore } from "../../auth/token";

type JwtPayload = Record<string, unknown> & {
  sub?: string;
  username?: string;
  exp?: number;
};

type BuildConsentResponseOptions = {
  userId?: number;
  internalConsent?: ConsentStatusValue | null;
  externalConsent?: ConsentStatusValue | null;
  internalSavedStatus?: ConsentStatusValue;
  externalSavedStatus?: ConsentStatusValue;
  internalTimestamp?: string;
  externalTimestamp?: string;
};

type ConsentApiSuccessResponse<T> = {
  success: true;
  data: T;
  error: null;
};

export function setRoute(path: string) {
  window.history.pushState({}, "", path);
}

export function setAuthenticatedTestUser(payload: JwtPayload = {}) {
  tokenStore.set(
    makeJwt({
      sub: "1",
      username: "testuser",
      exp: Math.floor(Date.now() / 1000) + 60 * 60,
      ...payload,
    })
  );
}

export function buildConsentSuccessResponses(
  options: BuildConsentResponseOptions = {}
): {
  status: ConsentApiSuccessResponse<ConsentStatus>;
  internalSave: ConsentApiSuccessResponse<ConsentRecord>;
  externalSave: ConsentApiSuccessResponse<ConsentRecord>;
} {
  const {
    userId = 1,
    internalConsent = null,
    externalConsent = null,
    internalSavedStatus = "accepted",
    externalSavedStatus = "accepted",
    internalTimestamp = "2026-03-08T00:00:00",
    externalTimestamp = "2026-03-08T00:00:01",
  } = options;

  return {
    status: {
      success: true,
      data: {
        user_id: userId,
        internal_consent: internalConsent,
        external_consent: externalConsent,
      },
      error: null,
    },
    internalSave: {
      success: true,
      data: {
        consent_id: 1,
        user_id: userId,
        status: internalSavedStatus,
        timestamp: internalTimestamp,
      },
      error: null,
    },
    externalSave: {
      success: true,
      data: {
        consent_id: 2,
        user_id: userId,
        status: externalSavedStatus,
        timestamp: externalTimestamp,
      },
      error: null,
    },
  };
}

function makeJwt(payload: JwtPayload) {
  const header = { alg: "HS256", typ: "JWT" };

  const b64url = (obj: unknown) =>
    btoa(JSON.stringify(obj))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/g, "");

  return `${b64url(header)}.${b64url(payload)}.sig`;
}
