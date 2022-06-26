#!/usr/bin/env python3

import requests
import json
import argparse
from typing import Any

from web3 import Web3

ETHERSCAN_API_KEY = "YOUR_KEY"

ETHERSCAN_DATA_SOURCE = "// Data source: https://etherscan.io\n"


def parse_args() -> Any:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=["metadata", "upload"],
        help="print metadata or directly upload source code to sourcify.",
    )
    parser.add_argument("--address", help="address to upload source code to sourcify.")
    return parser.parse_args()


def main():
    args = parse_args()
    resp = requests.get(
        "https://api.etherscan.io/api",
        params={
            "module": "contract",
            "action": "getsourcecode",
            "address": args.address,
            "apikey": ETHERSCAN_API_KEY,
        },
    )
    etherscan = resp.json()["result"][0]

    source_code = etherscan["SourceCode"]
    source_code = ETHERSCAN_DATA_SOURCE + source_code

    contract = etherscan["ContractName"]

    metadata = {
        "compiler": {"version": etherscan["CompilerVersion"]},
        "language": "Solidity",
        "output": {"abi": json.loads(etherscan["ABI"])},
        "settings": {
            "compilationTarget": {f"{contract}.sol": contract},
            "libraries": {},
            "optimizer": {
                "enabled": bool(int(etherscan["OptimizationUsed"])),
                "runs": int(etherscan["Runs"]),
            },
            "remappings": [],
        },
        "sources": {
            f"{contract}.sol": {
                "content": source_code,
                "keccak256": Web3.keccak(text=source_code).hex(),
                "license": etherscan["LicenseType"],
            }
        },
        "version": 1,
    }

    if etherscan["EVMVersion"] != "Default":
        metadata["settings"]["evmVersion"] = etherscan["EVMVersion"]

    if args.mode == "metadata":
        print(json.dumps(metadata, indent=4))
        return

    data = {
        "address": Web3.toChecksumAddress(args.address),
        "chain": "1",
        "files": {"metadata.json": json.dumps(metadata)},
    }

    resp = requests.post("https://sourcify.dev/server/", json=data)


if __name__ == "__main__":
    main()
