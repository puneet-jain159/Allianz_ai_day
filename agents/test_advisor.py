"""Invoke the Coverage Gap Advisor supervisor endpoint and print the text output."""
import sys, json, requests
from databricks.sdk import WorkspaceClient

ENDPOINT = "mas-d4e8c021-endpoint"
w = WorkspaceClient(profile="DEFAULT")
cfg = w.config
prompt = sys.argv[1] if len(sys.argv) > 1 else (
    "Sarah Thompson has started a home catering business and bought 4,800 pounds of equipment "
    "including a camera for food photography. Her niece helps at weekend events. What are her "
    "coverage gaps and what should I recommend before her renewal?"
)
url = f"{cfg.host}/serving-endpoints/{ENDPOINT}/invocations"
headers = cfg.authenticate()
headers["Content-Type"] = "application/json"
r = requests.post(url, headers=headers, json={"input": [{"role": "user", "content": prompt}], "stream": False}, timeout=300)
print("HTTP", r.status_code, "len", len(r.text))

texts = []
def walk(o):
    if isinstance(o, dict):
        if o.get("type") == "output_text" and o.get("text"):
            texts.append(o["text"])
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)

# Response may be a single JSON object, JSON-lines, or SSE. Try each.
parsed = False
try:
    walk(json.loads(r.text)); parsed = True
except Exception:
    pass
if not parsed:
    dec = json.JSONDecoder()
    s = r.text.strip(); i = 0
    while i < len(s):
        while i < len(s) and s[i] in " \n\r\t":
            i += 1
        if s[i:i+5] == "data:":
            i += 5; continue
        try:
            obj, off = dec.raw_decode(s, i); walk(obj); i = off
        except Exception:
            i += 1

print("\n\n".join(texts) if texts else r.text[:3000])
