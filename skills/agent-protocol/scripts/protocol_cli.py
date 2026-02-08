#!/usr/bin/env python3
import sys
import json
import argparse

# Mock implementation of the Agent Protocol Skill CLI
# In a real scenario, this would import web3 and interact with the Base contract.

def list_bounties():
    # Simulated reading from the protocol's master list
    bounties = [
        {"id": "b1", "title": "Cross-Chain Alert Agent", "budget": 300},
        {"id": "b2", "title": "MEV Risk Intelligence Dashboard", "budget": 900},
    ]
    print(json.dumps(bounties, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Agent Protocol CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    list_parser = subparsers.add_parser("list")
    
    bid_parser = subparsers.add_parser("bid")
    bid_parser.add_argument("--id", required=True)
    bid_parser.add_argument("--amount", type=int, required=True)
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_bounties()
    elif args.command == "bid":
        print(f"✅ Bid of {args.amount} USDC submitted for bounty {args.id}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
