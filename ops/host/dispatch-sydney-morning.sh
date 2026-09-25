#!/usr/bin/env bash
# Dispatch hybrid-sydney-morning via the GitHub workflow_dispatch API.
#
# PR #124 (merged on main) allowlists workflow_dispatch to this workflow only.
# This script matches that mechanism. It does not send repository_dispatch.
# Execution (fetch, brief, capture, DM) stays on GitHub Actions.
#
# The token is read from a 0600 file and is never written to stdout, stderr,
# or the dispatch log. One retry after 60s on network error or HTTP 5xx only.
# A log-write failure is non-fatal: the line goes to stderr and the POST
# (including the retry) still runs.
set -euo pipefail

TOKEN_FILE="${MM_HOST_TOKEN_FILE:-/etc/market-memory/github-dispatch.token}"
LOG_FILE="${MM_HOST_LOG:-/var/log/market-memory/sydney-morning-dispatch.log}"
REPO="${MM_HOST_REPO:-ElChopa11/market-memory}"
WORKFLOW="${MM_HOST_WORKFLOW:-hybrid-sydney-morning.yml}"
REF="${MM_HOST_REF:-main}"
RETRY_SLEEP="${MM_HOST_RETRY_SLEEP:-60}"
CURL_BIN="${MM_HOST_CURL:-curl}"

DRY=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY=1
elif [[ -n "${1:-}" ]]; then
  echo "usage: dispatch-sydney-morning.sh [--dry-run]" >&2
  exit 2
fi

log_line() {
  local ts line
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  line="$(printf '%s %s' "$ts" "$1")"
  if mkdir -p -- "$(dirname -- "$LOG_FILE")" 2>/dev/null \
    && printf '%s\n' "$line" >>"$LOG_FILE" 2>/dev/null; then
    return 0
  fi
  printf '%s\n' "$line" >&2
}

refuse() {
  log_line "refused $1"
  echo "refused $1" >&2
  exit 1
}

if [[ ! -f "$TOKEN_FILE" ]]; then
  refuse "missing_token_file"
fi
# GNU stat. The host is a Linux VPS. Accept 600 and 0600.
mode="$(stat -c %a -- "$TOKEN_FILE")"
if [[ "$mode" != "600" && "$mode" != "0600" ]]; then
  refuse "token_file_mode=${mode}"
fi
if [[ ! -s "$TOKEN_FILE" ]]; then
  refuse "empty_token_file"
fi

# Hard allowlist. Do not take a workflow name from an untrusted argument.
case "$WORKFLOW" in
  hybrid-sydney-morning.yml) ;;
  *)
    refuse "workflow_not_allowlisted"
    ;;
esac

if [[ ! "$REF" =~ ^[A-Za-z0-9._/-]+$ ]]; then
  refuse "bad_ref"
fi
if [[ ! "$REPO" =~ ^[A-Za-z0-9._/-]+$ ]]; then
  refuse "bad_repo"
fi

URL="https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches"

if [[ "$DRY" -eq 1 ]]; then
  log_line "dry-run event=workflow_dispatch workflow=${WORKFLOW} ref=${REF} input=i_mean_it_deliver http=skipped"
  echo "dry-run event=workflow_dispatch workflow=${WORKFLOW} ref=${REF} input=i_mean_it_deliver=true"
  echo "url=${URL}"
  exit 0
fi

# REST API sends workflow inputs as strings. The workflow accepts boolean true
# and the string 'true'. Schedule crons ignore this input and still deliver.
PAYLOAD="$(printf '{"ref":"%s","inputs":{"i_mean_it_deliver":"true"}}' "$REF")"

HDR=""
BODY=""
cleanup() {
  if [[ -n "${HDR}" ]]; then
    rm -f -- "$HDR"
  fi
  if [[ -n "${BODY}" ]]; then
    rm -f -- "$BODY"
  fi
}
trap cleanup EXIT

post_once() {
  HDR="$(mktemp)"
  BODY="$(mktemp)"
  chmod 600 "$HDR" "$BODY"
  {
    printf 'Authorization: Bearer '
    tr -d '\r\n' <"$TOKEN_FILE"
    printf '\nAccept: application/vnd.github+json\n'
    printf 'X-GitHub-Api-Version: 2022-11-28\n'
    printf 'Content-Type: application/json\n'
    printf 'User-Agent: market-memory-host-dispatch\n'
  } >"$HDR"
  local http rc
  set +e
  http="$("$CURL_BIN" --silent --show-error --proto '=https' \
    --header "@${HDR}" \
    --data-binary "$PAYLOAD" \
    --output "$BODY" \
    --write-out '%{http_code}' \
    --max-time 30 \
    "$URL")"
  rc=$?
  set -e
  rm -f -- "$HDR" "$BODY"
  HDR=""
  BODY=""
  if [[ "$rc" -ne 0 ]]; then
    printf 'network:%s' "$rc"
    return 0
  fi
  printf 'http:%s' "$http"
}

attempt=1
result="$(post_once)"
log_line "dispatch attempt=${attempt} event=workflow_dispatch workflow=${WORKFLOW} ref=${REF} result=${result}"

need_retry=0
case "$result" in
  network:*) need_retry=1 ;;
  http:5*) need_retry=1 ;;
  *) need_retry=0 ;;
esac

if [[ "$need_retry" -eq 1 ]]; then
  sleep "$RETRY_SLEEP"
  attempt=2
  result="$(post_once)"
  log_line "dispatch attempt=${attempt} event=workflow_dispatch workflow=${WORKFLOW} ref=${REF} result=${result}"
fi

case "$result" in
  http:2*)
    exit 0
    ;;
  *)
    echo "dispatch failed result=${result}" >&2
    exit 1
    ;;
esac
