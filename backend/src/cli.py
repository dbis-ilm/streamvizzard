import argparse
import json
import sys

import requests
import time
import signal

from analysis.costModel.costModelAnalysis import performCostModelAnalysis
from config import NETWORKING_SERVER_PORT

server = "localhost"
port = NETWORKING_SERVER_PORT


# ------------------------------------------------------ Commands ------------------------------------------------------

def registerStartPipeline(subparsers):
    parser = subparsers.add_parser("startPipeline", help="Executes the specified pipeline if no current pipeline is running.")
    parser.add_argument("--path", type=str, required=True, help="The path to the pipeline file to execute.")
    parser.add_argument("--options", type=str, required=False, default=None, help="Additional JSON options for the pipeline execution.")
    parser.add_argument("--detached", action="store_true", help="If the script should detach the pipeline execution and terminate. Otherwise, interrupting the script (STR+C) will cancel the pipeline execution.")
    parser.set_defaults(func=_startPipeline)


def _startPipeline(args):
    try:
        metaData = json.loads(args.options) if args.options is not None else {}

        response = requests.post(f"http://{server}:{port}/startPipeline", json={"path": args.path, "meta": metaData})
        res = json.loads(response.text) if response.text is not None else None

        if res.get("res", False):
            print("Pipeline started!")

            if not args.detached:
                print("Pipeline execution can be canceled with CTRL+C!")

                signal.signal(signal.SIGTERM, lambda signum, frame: _stopPipeline())

                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    _stopPipeline()
        else:
            print("Error starting pipeline:\n" + res.get("error"))

            sys.exit(1)
    except requests.RequestException as e:
        print(f"Request failed: {e}")

        sys.exit(1)


def registerStopPipeline(subparsers):
    parser = subparsers.add_parser("stopPipeline", help="Stops the current pipeline execution.")
    parser.set_defaults(func=lambda args: _stopPipeline())


def _stopPipeline():
    res = requests.post(f"http://{server}:{port}/stopPipeline")

    if res.ok:
        print("Pipeline stopped!")
    else:
        print("Failed to stop pipeline!")

        sys.exit(1)


def registerCostModelAnalysis(subparsers):
    parser = subparsers.add_parser("analyzeCostModels", help="Calculates costModels for the configured operators.")
    parser.add_argument("--storagePath", type=str, required=True, help="The path to store the costModel results.")
    parser.add_argument("--forceRecordings", type=bool, required=False, default=False, help="Force a re-execution of all operator runs.")
    parser.set_defaults(func=_analyzeCostModels)


def _analyzeCostModels(args):
    performCostModelAnalysis(args.storagePath, args.forceRecordings)


# ----------------------------------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="CLI access to the running StreamVizzard system.")
    subparsers = parser.add_subparsers(title="commands", dest="command")

    registerStartPipeline(subparsers)
    registerStopPipeline(subparsers)
    registerCostModelAnalysis(subparsers)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
