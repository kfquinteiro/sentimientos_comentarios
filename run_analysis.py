"""Executa la consolidación + análisis de sentimiento + generación del
reporte para un run_dir. Pensado para ejecutarse como proceso en segundo
plano, desacoplado de la interfaz Streamlit."""
import json
import os
import sys

import ai_sentiment as ai_sent
import consolidate as cons
import report as rep
import sentiment as sent

ANALYSIS_STATE_FILENAME = "analysis_state.json"
ANALYSIS_RUNNING_FLAG = "analysis_running.flag"
REPORT_FILENAME = "analisis_sentimiento.xlsx"


def analysis_state_path(run_dir):
    return os.path.join(run_dir, ANALYSIS_STATE_FILENAME)


def analysis_running_flag_path(run_dir):
    return os.path.join(run_dir, ANALYSIS_RUNNING_FLAG)


def is_analysis_running(run_dir):
    return os.path.exists(analysis_running_flag_path(run_dir))


def save_analysis_state(run_dir, state):
    path = analysis_state_path(run_dir)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def load_analysis_state(run_dir):
    path = analysis_state_path(run_dir)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main(run_dir, engine="local"):
    running_flag = analysis_running_flag_path(run_dir)
    open(running_flag, "w").close()

    state = {
        "stage": "consolidando",
        "processed": 0,
        "total": 0,
        "error": None,
        "report_file": None,
        "engine": engine,
    }
    save_analysis_state(run_dir, state)

    try:
        df, read_errors = cons.build_consolidated(run_dir)
        state["total"] = len(df)
        state["read_errors"] = read_errors

        def on_progress(done, total):
            state["processed"] = done
            save_analysis_state(run_dir, state)

        if engine == "ai":
            state["stage"] = "analizando_sentimiento"
            save_analysis_state(run_dir, state)
            labels, scores = ai_sent.analyze(df["comentario"], on_progress=on_progress)
        else:
            state["stage"] = "cargando_modelo"
            save_analysis_state(run_dir, state)
            sent.get_analyzer()

            state["stage"] = "analizando_sentimiento"
            save_analysis_state(run_dir, state)
            labels, scores = sent.analyze(df["comentario"], on_progress=on_progress)

        df["sentimiento"] = labels
        df["confianza"] = scores

        import blocklist
        df, bl_changes = blocklist.apply_blocklist(df)
        state["blocklist_changes"] = bl_changes

        state["stage"] = "generando_reporte"
        save_analysis_state(run_dir, state)

        report_path = os.path.join(run_dir, REPORT_FILENAME)
        rep.build_report(df, report_path)

        state["stage"] = "completado"
        state["report_file"] = REPORT_FILENAME
        save_analysis_state(run_dir, state)
    except Exception as e:
        state["stage"] = "error"
        state["error"] = str(e)
        save_analysis_state(run_dir, state)
    finally:
        if os.path.exists(running_flag):
            os.remove(running_flag)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "local")
