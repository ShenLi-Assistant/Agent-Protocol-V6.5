#!/usr/bin/env python3
"""
Web3 Integration Demo for Agent Protocol.

This script simulates an agent interacting with a Base L2-compatible
Agent Marketplace contract:
1. Connect wallet
2. Check USDC balance
3. Claim bounty by staking 10% USDC (simulated transaction)
4. Verify work delivery hash on-chain
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import secrets
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Dict


USDC_DECIMALS = 6
USDC_QUANTIZER = Decimal("0.000001")
BASE_CHAIN_ID = 8453
BASE_NETWORK = "Base Mainnet (L2)"
STAKE_BPS = 1000
BPS_DENOMINATOR = 10_000


class DemoError(Exception):
    """Raised when the demo flow cannot continue."""


def to_usdc_base_units(amount: Decimal) -> int:
    """Convert decimal USDC value into 6-decimal base units."""
    normalized = amount.quantize(USDC_QUANTIZER, rounding=ROUND_DOWN)
    return int(normalized * (10 ** USDC_DECIMALS))


def from_usdc_base_units(amount: int) -> Decimal:
    """Convert 6-decimal base units into decimal USDC value."""
    return (Decimal(amount) / (10 ** USDC_DECIMALS)).quantize(USDC_QUANTIZER)


def keccak_like_hash(payload: Dict[str, str]) -> str:
    """
    Generate a deterministic hash for delivered work payload.

    We use sha256 in this mock demo for portability. In production, use
    keccak256 to match Solidity-native hashing semantics.
    """
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "0x" + hashlib.sha256(encoded).hexdigest()


def random_tx_hash() -> str:
    return "0x" + secrets.token_hex(32)


@dataclass(frozen=True)
class BaseWallet:
    address: str
    chain_id: int = BASE_CHAIN_ID
    network: str = BASE_NETWORK


@dataclass
class Bounty:
    bounty_id: int
    agent: str
    expected_work_hash: str
    stake_amount: int
    verified: bool = False


@dataclass(frozen=True)
class TxReceipt:
    tx_hash: str
    action: str
    status: str


class AgentMarketplaceMockClient:
    """
    In-memory stand-in for on-chain marketplace interactions.

    The behavior mirrors what the Solidity mock contract does.
    """

    def __init__(self) -> None:
        self._usdc_balances: Dict[str, int] = {}
        self._bounties: Dict[int, Bounty] = {}

    def seed_usdc(self, wallet: str, amount_base_units: int) -> None:
        self._usdc_balances[wallet] = self._usdc_balances.get(wallet, 0) + amount_base_units

    def usdc_balance_of(self, wallet: str) -> int:
        return self._usdc_balances.get(wallet, 0)

    def claim_bounty(self, bounty_id: int, wallet: str, expected_work_hash: str) -> TxReceipt:
        if bounty_id in self._bounties:
            raise DemoError(f"bounty {bounty_id} already claimed")

        balance = self.usdc_balance_of(wallet)
        stake_amount = (balance * STAKE_BPS) // BPS_DENOMINATOR
        if stake_amount <= 0:
            raise DemoError("insufficient USDC to meet 10% staking requirement")

        self._usdc_balances[wallet] = balance - stake_amount
        self._bounties[bounty_id] = Bounty(
            bounty_id=bounty_id,
            agent=wallet,
            expected_work_hash=expected_work_hash,
            stake_amount=stake_amount,
        )
        return TxReceipt(tx_hash=random_tx_hash(), action="claim_bounty", status="success")

    def verify_work_delivery(self, bounty_id: int, delivered_hash: str) -> TxReceipt:
        bounty = self._bounties.get(bounty_id)
        if bounty is None:
            raise DemoError(f"bounty {bounty_id} not found")
        if bounty.verified:
            raise DemoError(f"bounty {bounty_id} already verified")
        if bounty.expected_work_hash != delivered_hash:
            raise DemoError("work hash mismatch; verification failed")

        bounty.verified = True

        # Mock payout to demonstrate closed-loop marketplace settlement.
        reward = bounty.stake_amount * 2
        self._usdc_balances[bounty.agent] = self.usdc_balance_of(bounty.agent) + reward
        return TxReceipt(tx_hash=random_tx_hash(), action="verify_work_delivery", status="success")


class AgentProtocolWeb3Demo:
    def __init__(
        self,
        wallet: BaseWallet,
        marketplace: AgentMarketplaceMockClient,
        bounty_id: int,
        initial_usdc: Decimal,
    ) -> None:
        self.wallet = wallet
        self.marketplace = marketplace
        self.bounty_id = bounty_id
        self.marketplace.seed_usdc(wallet.address, to_usdc_base_units(initial_usdc))

    def run(self) -> None:
        self.connect_wallet()
        start_balance = self.check_usdc_balance("Initial")
        work_hash = self.claim_bounty(start_balance)
        self.verify_delivery(work_hash)
        self.check_usdc_balance("Final")

    def connect_wallet(self) -> None:
        logging.info("Connected wallet %s", self.wallet.address)
        logging.info("Network: %s (chainId=%s)", self.wallet.network, self.wallet.chain_id)

    def check_usdc_balance(self, label: str) -> int:
        base_units = self.marketplace.usdc_balance_of(self.wallet.address)
        logging.info("%s USDC balance: %s USDC", label, from_usdc_base_units(base_units))
        return base_units

    def claim_bounty(self, current_balance: int) -> str:
        payload = {
            "task_id": str(self.bounty_id),
            "agent": self.wallet.address,
            "delivery_uri": "ipfs://bafybeifaketaskartifact",
            "result_digest": "sha256:demo-result",
        }
        expected_work_hash = keccak_like_hash(payload)
        stake = (current_balance * STAKE_BPS) // BPS_DENOMINATOR

        logging.info("Prepared work delivery hash: %s", expected_work_hash)
        logging.info("Staking 10%% of USDC balance: %s USDC", from_usdc_base_units(stake))

        receipt = self.marketplace.claim_bounty(
            bounty_id=self.bounty_id,
            wallet=self.wallet.address,
            expected_work_hash=expected_work_hash,
        )
        logging.info("Claim transaction: %s [%s]", receipt.tx_hash, receipt.status)
        self.check_usdc_balance("Post-claim")
        return expected_work_hash

    def verify_delivery(self, delivered_hash: str) -> None:
        receipt = self.marketplace.verify_work_delivery(self.bounty_id, delivered_hash)
        logging.info("Verification transaction: %s [%s]", receipt.tx_hash, receipt.status)
        logging.info("Work hash verified on-chain for bounty %s", self.bounty_id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agent Protocol Web3 integration demo")
    parser.add_argument(
        "--wallet",
        default="0xA93fAe90B9300A12B38E3a4F03949c2A3DB4A8b7",
        help="Base L2 wallet address (simulated)",
    )
    parser.add_argument(
        "--bounty-id",
        default=1001,
        type=int,
        help="Bounty ID to claim and verify",
    )
    parser.add_argument(
        "--initial-usdc",
        default="250.000000",
        type=str,
        help="Initial USDC balance in decimal form",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    args = parse_args()

    initial_usdc = Decimal(args.initial_usdc)
    if initial_usdc <= 0:
        raise DemoError("initial USDC must be greater than zero")

    wallet = BaseWallet(address=args.wallet)
    marketplace = AgentMarketplaceMockClient()
    demo = AgentProtocolWeb3Demo(
        wallet=wallet,
        marketplace=marketplace,
        bounty_id=args.bounty_id,
        initial_usdc=initial_usdc,
    )
    demo.run()


if __name__ == "__main__":
    main()
