"""Executa o orquestrador para um run_dir. Pensado para rodar como processo
em background, desacoplado da interface Streamlit."""
import os
import sys

import orchestrator as orc


def main(run_dir):
    running_flag = os.path.join(run_dir, "running.flag")
    open(running_flag, "w").close()
    try:
        orc.run(run_dir, poll_seconds=5)
    finally:
        if os.path.exists(running_flag):
            os.remove(running_flag)
        stop_flag = orc.stop_flag_path(run_dir)
        if os.path.exists(stop_flag):
            os.remove(stop_flag)


if __name__ == "__main__":
    main(sys.argv[1])
