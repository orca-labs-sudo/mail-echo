"""
Import leads from CSV into PROD Kanban API (ycnex.de/mcp)
MCP Streamable HTTP Transport: initialize → Session-ID → tool calls
"""
import csv
import json
import time
import urllib.request
import urllib.error

CSV_PATH = r"C:\Users\Vadim\Downloads\pflegedienste_rheinmain_final (1).csv"
MCP_URL = "https://ycnex.de/mcp"
PHASE_ID = 2
PAUSE = 0.3


def parse_sse_body(body: str) -> dict | None:
    """Extrahiert JSON aus SSE-Antwort (event/data-Format)."""
    for line in body.splitlines():
        if line.startswith("data:"):
            try:
                return json.loads(line[5:].strip())
            except json.JSONDecodeError:
                pass
    # Fallback: direkt als JSON
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def mcp_post(session_id: str, payload: dict, timeout: int = 15) -> tuple[bool, str, dict | None]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        MCP_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": session_id,
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            parsed = parse_sse_body(body)
            return True, "", parsed
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return False, f"HTTP {e.code}: {body[:300]}", None
    except Exception as e:
        return False, str(e), None


def initialize_session() -> str:
    """Führt MCP-Initialize durch und gibt die Session-ID zurück."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "lead-import-script", "version": "1.0"}
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        MCP_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        session_id = resp.headers.get("mcp-session-id")
        if not session_id:
            raise RuntimeError("Kein mcp-session-id im Initialize-Response")
        return session_id


def hat_gueltige_email(email: str) -> bool:
    return "@" in email and email.strip().lower() != "email_fehlt"


def main():
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)

    total = len(rows)
    importiert = 0
    uebersprungen = 0
    fehler = 0

    print(f"CSV geladen: {total} Einträge")
    print("MCP-Session wird aufgebaut ...", flush=True)

    session_id = initialize_session()
    print(f"Session-ID: {session_id}\n")

    for i, row in enumerate(rows, 1):
        firma = row.get("firmenname", "").strip()
        email = row.get("email", "").strip()

        if not hat_gueltige_email(email):
            print(f"[{i}/{total}] ÜBERSPRUNGEN — {firma} (keine E-Mail)")
            uebersprungen += 1
            continue

        print(f"[{i}/{total}] {firma} — {email}", end=" ... ", flush=True)

        payload = {
            "jsonrpc": "2.0",
            "id": i,
            "method": "tools/call",
            "params": {
                "name": "lead_erstellen",
                "arguments": {
                    "titel": firma,
                    "phase_id": PHASE_ID,
                    "email": email,
                    "telefon": row.get("telefon", "").strip(),
                    "ansprechpartner": row.get("ansprechpartner", "").strip(),
                    "notizen": (
                        f"Ort: {row.get('ort','').strip()} | "
                        f"Web: {row.get('webseite','').strip()} | "
                        f"Quelle: {row.get('quelle','').strip()}"
                    )
                }
            }
        }

        ok, err, result = mcp_post(session_id, payload)

        if ok:
            # Prüfe ob JSON-RPC Error im Result
            if result and result.get("error"):
                err_msg = result["error"].get("message", str(result["error"]))
                print(f"FEHLER: {err_msg}")
                fehler += 1
            else:
                print("OK")
                importiert += 1
        else:
            print(f"FEHLER: {err}")
            fehler += 1

        time.sleep(PAUSE)

    print("\n" + "=" * 50)
    print(f"Importiert:    {importiert}")
    print(f"Übersprungen:  {uebersprungen}")
    print(f"Fehler:        {fehler}")
    print(f"Gesamt:        {total}")
    print("=" * 50)


if __name__ == "__main__":
    main()
