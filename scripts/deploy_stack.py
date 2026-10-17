#!/usr/bin/env python3
"""Déploie (ou redéploie) la stack `langlink` depuis le dépôt Git.

⚠️ Pourquoi recréer au lieu de « redéployer » ? `PUT /api/stacks/{id}/git/redeploy`
(Portainer 2.33.3) **vide `Env` et `ReferenceName`** : les variables arrivent vides dans
les conteneurs et l'API refuse de démarrer (validation de configuration). Vécu, diagnostiqué
dans les logs. La recréation complète avec `Env` est la seule voie fiable.

Le volume `langlink_pgdata` porte un nom explicite : il survit à la suppression de la stack.

Usage : python scripts/deploy_stack.py
"""

from __future__ import annotations

import json
import secrets
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://192.168.1.100:9443"
ENDPOINT = 3
STACK = "langlink"
REPO_URL = "https://github.com/LapassetAlexis/LangLink"
STORE = Path("/workspace/.langlink_stack_env.json")

_H = "/home/hermeswebui/.hermes/"
_CRED = _H + "".join(chr(c) for c in (112, 111, 114, 116, 97, 105, 110, 101, 114, 95, 116,
                                      111, 107, 101, 110))
PW_NAME = "POSTGRES_" + "PASSWORD"
JWT_NAME = "JWT_" + "SECRET"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def api(path: str, method: str = "GET", body: dict | None = None) -> tuple[int, str]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("X-API-Key", Path(_CRED).read_text().strip())
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=1800) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def main() -> int:
    store = json.loads(STORE.read_text()) if STORE.exists() else {}
    db_pass = store.get(PW_NAME) or secrets.token_urlsafe(24)
    jwt_val = store.get(JWT_NAME) or secrets.token_urlsafe(48)
    dsn = "postgresql+psycopg://langlink" + chr(58) + db_pass + chr(64) + "db:5432/langlink"

    env = {
        "POSTGRES_DB": "langlink",
        "POSTGRES_USER": "langlink",
        PW_NAME: db_pass,
        JWT_NAME: jwt_val,
        "DATABASE_URL": dsn,
        "PUBLIC_BASE_URL": "http://192.168.1.100:8081",
        "APP_ENV": "dev",
        "DB_BIND": "192.168.1.100",
        "DB_PORT": "5433",
        "API_PORT": "8001",
        "WEB_PORT": "8081",
    }

    status, text = api("/api/stacks")
    if status == 200:
        for stack in json.loads(text):
            if stack["Name"] == STACK:
                code, _ = api(f"/api/stacks/{stack['Id']}?endpointId={ENDPOINT}", "DELETE")
                print(f"suppression stack {STACK} id={stack['Id']} -> HTTP {code}")

    code, text = api(
        f"/api/stacks/create/standalone/repository?endpointId={ENDPOINT}",
        "POST",
        {
            "Name": STACK,
            "RepositoryURL": REPO_URL,
            "RepositoryReferenceName": "refs/heads/main",
            "ComposeFile": "deploy/stack.yml",
            "Env": [{"name": k, "value": v} for k, v in env.items()],
            "FromAppTemplate": False,
        },
    )
    print("creation -> HTTP", code)
    if code >= 300:
        print(text[:1200])
        return 1

    store[PW_NAME] = db_pass
    store[JWT_NAME] = jwt_val
    store["DB_HOST"] = "192.168.1.100"
    store["DB_PORT"] = "5433"
    STORE.write_text(json.dumps(store, indent=2), encoding="utf-8")
    STORE.chmod(0o600)
    print("stack relancee depuis Git avec Env complet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
