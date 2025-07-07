from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # <- enable CORS before defining routes

from gnv_node import load_state, save_state, create_block, compute_reward
import uuid, time, os, json
import requests
import base64

CONFIG_FILE = "config.json"
ADMIN_PASSWORD = os.getenv("GNV_ADMIN_PASSWORD")
DEV_WALLET = None

DAO_FILE = "dao_state.json"
REGISTRY_FILE = "model_registry.json"
STAKE_REQUIREMENT = 100  # GNV stake required to register a model
VOTE_THRESHOLD = 0.67  # >2/3 vote needed to slash

# Load config
def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"dev_wallet": "0xYourFallbackWalletHere"}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

# DAO / Registry helpers
def load_json(path, fallback):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return fallback

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

CONFIG = load_config()
DEV_WALLET = CONFIG.get("dev_wallet", "0xYourFallbackWalletHere")
AUTH_KEY = CONFIG.get("auth_key", "DEFAULT_FALLBACK_KEY")

@app.route("/mine", methods=["POST"])
def mine():
    import hashlib

    def transfix(prompt, output):
        return hashlib.sha256(f"{prompt}|{output}".encode()).hexdigest()

    data = request.get_json() or {}
    user = data.get("wallet")
    prompt = data.get("prompt")

    if not user or not isinstance(user, str):
        return jsonify({"error": "Missing or invalid wallet"}), 400
    if not prompt or not isinstance(prompt, str):
        return jsonify({"error": "Missing or invalid prompt"}), 400

    try:
        model_url = "http://localhost:5000/predictions/gnv-model"
        payload = {"text": prompt}
        model_response = requests.post(
            model_url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10,
            verify=False
        )

        if not model_response:
            raise ValueError("Empty response from model server")

        content_type = model_response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                resp_json = model_response.json()
                model_output = resp_json.get("output") or resp_json.get("result") or resp_json.get("text")
            except Exception:
                model_output = None
        else:
            model_output = model_response.text.strip()

        if not model_output:
            return jsonify({"error": "Empty model output"}), 500

    except Exception as e:
        return jsonify({"error": "Model HTTP request failed", "details": str(e)}), 500

    score = len(set(model_output.split()))
    miner, burn, dev = compute_reward(score)
    total = miner + burn + dev
    content_hash = transfix(prompt, model_output)

    state = load_state()
    old_balance = state["balances"].get(user, 0)
    state["balances"][user] = old_balance + miner
    state["balances"][DEV_WALLET] = state["balances"].get(DEV_WALLET, 0) + dev
    state["supply"] += total - burn

    txn = {
        "type": "mine",
        "user": user,
        "prompt_hash": content_hash,
        "reward_total": total,
        "split": {
            "miner": miner,
            "dev": dev,
            "burn": burn
        }
    }
    block = create_block([txn])
    save_state(state)

    return jsonify({
        "block": block,
        "score": score,
        "output": model_output,
        "content_hash": content_hash,
        "earned": {
            "miner": miner,
            "dev": dev,
            "burned": burn,
            "total": total
        }
    })

@app.route("/transfer", methods=["POST"])
def transfer():
    data = request.get_json()
    from_wallet = data.get("from")
    to_wallet = data.get("to")
    amount = data.get("amount")

    if not from_wallet or not to_wallet or not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "invalid transfer request"}), 400

    state = load_state()
    if state["balances"].get(from_wallet, 0) < amount:
        return jsonify({"error": "insufficient balance"}), 400

    state["balances"][from_wallet] -= amount
    state["balances"].setdefault(to_wallet, 0)
    state["balances"][to_wallet] += amount

    block = create_block([{
        "type": "transfer",
        "from": from_wallet,
        "to": to_wallet,
        "amount": amount
    }])

    return jsonify({
        "status": "transfer complete",
        "block": block,
        "from": from_wallet,
        "to": to_wallet,
        "amount": amount
    })

@app.route("/balance/<wallet>", methods=["GET"])
def balance(wallet):
    state = load_state()
    return jsonify({"wallet": wallet, "balance": state["balances"].get(wallet, 0)})

@app.route("/supply", methods=["GET"])
def supply():
    state = load_state()
    return jsonify({"supply": state.get("supply", 0)})

@app.route("/blocks", methods=["GET"])
def blocks():
    chain = load_state().get("chain", [])
    return jsonify({"blocks": chain})

@app.route("/last_block", methods=["GET"])
def last_block():
    state = load_state()
    return jsonify({"block": state.get("chain", [])[-1] if state.get("chain") else None})

@app.route("/faucet", methods=["POST"])
def faucet():
    data = request.get_json()
    wallet = data.get("wallet")
    if not wallet:
        return jsonify({"error": "missing wallet"}), 400

    state = load_state()
    state["balances"].setdefault(wallet, 0)
    state["balances"][wallet] += 10_000_000

    block = create_block([{
        "type": "faucet",
        "to": wallet,
        "amount": 10_000_000
    }])

    save_state(state)

    return jsonify({"status": "success", "wallet": wallet, "amount": 10_000_000, "block": block})

@app.route("/status")
def status():
    return jsonify({"status": "ok", "chain": "gnv-testnet"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
