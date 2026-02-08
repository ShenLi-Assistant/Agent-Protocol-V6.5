import solcx
from web3 import Web3
import json
import os
import sys

# Ensure solc is installed
solcx.install_solc("0.8.24")

# Read contract source
contract_path = "projects/agent_protocol/backend/AgentMarketplaceMock.sol"
with open(contract_path, "r") as f:
    source = f.read()

# Compile
print("Compiling contract...")
compiled_sol = solcx.compile_source(
    source,
    output_values=["abi", "bin"],
    solc_version="0.8.24"
)
contract_id, contract_interface = compiled_sol.popitem()
abi = contract_interface["abi"]
bytecode = contract_interface["bin"]

# Setup Web3
w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
creds_path = os.path.expanduser("~/.config/clawtasks/credentials.json")
with open(creds_path, "r") as f:
    creds = json.load(f)

priv_key = creds["private_key"]
account = w3.eth.account.from_key(priv_key)

print(f"Deploying to Base Mainnet from: {account.address}")
balance = w3.eth.get_balance(account.address)
print(f"Balance: {w3.from_wei(balance, 'ether')} ETH")

if balance < w3.to_wei(0.0002, 'ether'):
    print("Insufficient balance for deployment (need ~0.0002 ETH)")
    sys.exit(1)

# Build Tx
Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
nonce = w3.eth.get_transaction_count(account.address)

print("Building transaction...")
tx = Contract.constructor().build_transaction({
    "from": account.address,
    "nonce": nonce,
    "gas": 1500000,
    "gasPrice": w3.eth.gas_price
})

# Sign & Send
print("Signing and sending...")
signed_tx = w3.eth.account.sign_transaction(tx, priv_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
print(f"TX Hash: {tx_hash.hex()}")

print("Waiting for receipt...")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"✅ Contract Deployed Successfully!")
print(f"Address: {receipt.contractAddress}")

# Save deployment info
deploy_info = {
    "address": receipt.contractAddress,
    "abi": abi,
    "tx_hash": tx_hash.hex(),
    "network": "Base Mainnet"
}
with open("projects/agent_protocol/backend/deployment_info.json", "w") as f:
    json.dump(deploy_info, f, indent=2)
