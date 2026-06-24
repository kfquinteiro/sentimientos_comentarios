"""Orquestra a exportação sequencial de links via API do ExportComments.

O plano da conta só permite 1 export simultâneo, então o processamento é
sequencial: cria o job, aguarda finalizar (done/error) e baixa o arquivo.
O estado é persistido em disco a cada passo, permitindo retomar a execução
caso o processo seja interrompido.
"""
import json
import os
import time
from datetime import datetime, timezone

import requests

from exportcomments_client import ExportCommentsClient

STATE_FILENAME = "state.json"
FILES_DIRNAME = "files"
STOP_FLAG_FILENAME = "stop.flag"

ACTIVE_STATUSES = {"pending", "queueing", "progress", "creating"}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def state_path(run_dir):
    return os.path.join(run_dir, STATE_FILENAME)


def files_dir(run_dir):
    return os.path.join(run_dir, FILES_DIRNAME)


def stop_flag_path(run_dir):
    return os.path.join(run_dir, STOP_FLAG_FILENAME)


def load_state(run_dir):
    path = state_path(run_dir)
    for attempt in range(3):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            time.sleep(0.2)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(run_dir, state):
    path = state_path(run_dir)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    for attempt in range(5):
        try:
            os.replace(tmp_path, path)
            return
        except OSError:
            time.sleep(0.1)
    os.replace(tmp_path, path)


def init_run(run_dir, links_df, source_file=None, column_mapping=None):
    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(files_dir(run_dir), exist_ok=True)

    items = []
    for i, row in links_df.iterrows():
        items.append({
            "index": int(i),
            "link": row["link"],
            "network": row.get("network"),
            "profile": row.get("profile"),
            "status": "pending",
            "guid": None,
            "file_name": None,
            "download_url": None,
            "error": None,
            "total": None,
            "total_exported": None,
            "attempts": 0,
            "started_at": None,
            "updated_at": None,
        })

    state = {
        "source_file": source_file,
        "column_mapping": column_mapping or {},
        "created_at": now_iso(),
        "items": items,
    }
    save_state(run_dir, state)
    return state


def should_stop(run_dir):
    return os.path.exists(stop_flag_path(run_dir))


def create_job_with_retry(client, url, max_retries=12, base_wait=10):
    for attempt in range(max_retries):
        try:
            return client.create_job(url)
        except requests.exceptions.HTTPError as e:
            resp = e.response
            if resp is not None and resp.status_code == 429:
                time.sleep(base_wait)
                continue
            raise
    raise RuntimeError("Falha ao criar job para {} após {} tentativas".format(url, max_retries))


def download_export(client, job, dest_dir):
    download_url = job.get("download_url") or job.get("download_link")
    if not download_url:
        return None
    response = requests.get(download_url, headers=client.headers)
    response.raise_for_status()
    file_name = job.get("file_name") or os.path.basename(download_url)
    with open(os.path.join(dest_dir, file_name), "wb") as f:
        f.write(response.content)
    return file_name


def process_item(client, item, dest_dir, run_dir, poll_seconds=5, job_timeout=900):
    if not item.get("guid"):
        item["attempts"] += 1
        item["status"] = "creating"
        item["error"] = None
        if not item.get("started_at"):
            item["started_at"] = now_iso()
        resp = create_job_with_retry(client, item["link"])
        item["guid"] = resp["guid"]
        item["status"] = resp.get("status", "queueing")
        item["updated_at"] = now_iso()

    elapsed = 0
    while elapsed <= job_timeout:
        if should_stop(run_dir):
            return

        job = client.get_job(item["guid"])
        item["status"] = job["status"]
        item["total"] = job.get("total")
        item["total_exported"] = job.get("total_exported")
        item["updated_at"] = now_iso()

        if job["status"] == "done":
            item["file_name"] = download_export(client, job, dest_dir)
            item["download_url"] = job.get("download_url")
            return
        if job["status"] == "error":
            item["error"] = job.get("error")
            return

        time.sleep(poll_seconds)
        elapsed += poll_seconds

    item["status"] = "timeout"
    item["error"] = "Job não finalizou em {}s".format(job_timeout)


def run(run_dir, poll_seconds=5):
    """Processa todos os itens pendentes/ativos do run. Retorna o estado final."""
    state = load_state(run_dir)
    client = ExportCommentsClient()
    dest_dir = files_dir(run_dir)

    for item in state["items"]:
        if should_stop(run_dir):
            break

        if item["status"] not in ACTIVE_STATUSES:
            continue

        try:
            process_item(client, item, dest_dir, run_dir, poll_seconds=poll_seconds)
        except Exception as e:
            item["status"] = "error"
            item["error"] = str(e)

        item["updated_at"] = now_iso()
        save_state(run_dir, state)

    return state


if __name__ == "__main__":
    import sys
    run(sys.argv[1])
