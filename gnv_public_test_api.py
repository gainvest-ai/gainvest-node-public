import os
os.environ["GNV_REAL"] = "false"

from google.cloud import firestore

db = firestore.Client(project="gainvest-6ed7e")
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # <- enable CORS before defining routes

from gnv_node import load_state, save_state, create_block, compute_reward
import uuid, time, os, json
import requests
import base64
from dotenv import load_dotenv
load_dotenv()


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


# Load dev wallet after config is defined
DEV_WALLET = load_config().get("dev_wallet", "0xYourFallbackWalletHere")

@app.route("/testmine", methods=["POST"])
def testmine():
    import hashlib

    def transfix(prompt, output):
        return hashlib.sha256(f"{prompt}|{output}".encode()).hexdigest()

    # 🧠 Parse input
    data = request.get_json() or {}
    user = data.get("wallet")
    prompt = data.get("prompt")

    print("📥 Raw input:", data)
    if not user or not isinstance(user, str):
        print("⚠️ Invalid or missing wallet:", user)
        return jsonify({"error": "Missing or invalid wallet"}), 400
    if not prompt or not isinstance(prompt, str):
        print("⚠️ Invalid or missing prompt:", prompt)
        return jsonify({"error": "Missing or invalid prompt"}), 400

    print(f"🚀 Mining request from {user} with prompt: {prompt}")

        # 🔗 Query model
    try:
        model_url = "https://b41aad4e4811.ngrok-free.app/predictions/gnv-model"
        payload = {"text": prompt}
        print("📡 Sending to model:", model_url)
        print("📦 Payload:", payload)

        model_response = requests.post(
            model_url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10, 
            verify=False  

        )

        if not model_response:
            raise ValueError("Empty response from model server")

        print("📡 Raw response object:", model_response)
        print("📡 Status code:", model_response.status_code)

        content_type = model_response.headers.get("Content-Type", "")
        print("📡 Content-Type:", content_type)

        if "application/json" in content_type:
            try:
                resp_json = model_response.json()
                print("📄 Parsed JSON:", resp_json)
                model_output = resp_json.get("output") or resp_json.get("result") or resp_json.get("text")
            except Exception as parse_err:
                print("❌ JSON parse error:", parse_err)
                model_output = None
        else:
            model_output = model_response.text.strip()
            print("📄 Raw Text Output:", model_output)

        if not model_output:
            print("❌ Model output is empty or invalid")
            return jsonify({"error": "Empty model output"}), 500

    except Exception as e:
        import traceback
        print("❌ Exception Traceback:")
        traceback.print_exc()
        return jsonify({"error": "Model HTTP request failed", "details": str(e)}), 500



    # 💰 Score and reward calculation
    score = len(set(model_output.split()))
    miner, burn, dev = compute_reward(score)
    total = miner + burn + dev
    content_hash = transfix(prompt, model_output)

    print("✅ Score:", score, "| Miner:", miner, "Burn:", burn, "Dev:", dev)

    # 🧾 Load + update state
    state = load_state()
    old_balance = state["balances"].get(user, 0)
    state["balances"][user] = old_balance + miner
    state["balances"][DEV_WALLET] = state["balances"].get(DEV_WALLET, 0) + dev
    state["supply"] += total - burn  # Burned tokens don't count

    print(f"💰 Updated {user} balance: {old_balance} → {state['balances'][user]}")
    print(f"💰 Updated dev wallet {DEV_WALLET} balance: {state['balances'][DEV_WALLET]}")
    print(f"📈 New supply: {state['supply']}")

    # ⛓️ Create block
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
    state["chain"].append(block)

    save_state(state)

    print("✅ Block created:", block["hash"])

    db.collection("gnv-ledger").document("testnet").set(state)


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

    # 💸 Update balances
    state["balances"][from_wallet] -= amount
    state["balances"].setdefault(to_wallet, 0)
    state["balances"][to_wallet] += amount

    # ⛓️ Record the transfer in a block
    from gnv_node import create_block  # in case not already imported
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


@app.route("/state", methods=["GET"])
def state():
    return jsonify(load_state())

@app.route("/dao/vote", methods=["POST"])
def vote():
    data = request.get_json()
    user = data["wallet"]
    vote = data["vote"]

    dao = load_json(DAO_FILE, {"proposals": [], "votes": []})
    dao["votes"].append({"id": str(uuid.uuid4()), "user": user, "vote": vote, "time": time.time()})
    save_json(DAO_FILE, dao)
    return jsonify({"status": "vote recorded"})

@app.route("/dao/report", methods=["POST"])
def report():
    data = request.get_json()
    reporter = data.get("wallet")
    target = data.get("target")
    reason = data.get("reason")

    dao = load_json(DAO_FILE, {"proposals": [], "votes": []})
    proposal = {
        "id": str(uuid.uuid4()),
        "target": target,
        "action": "slash",
        "reason": reason,
        "proposed_by": reporter,
        "time": time.time(),
        "votes": []
    }
    dao["proposals"].append(proposal)
    save_json(DAO_FILE, dao)
    return jsonify({"status": "proposal submitted", "proposal": proposal})

@app.route("/status")
def status():
    return jsonify({"status": "ok", "chain": "gnv-testnet"})

@app.route("/dao/proposals", methods=["GET"])
def proposals():
    dao = load_json(DAO_FILE, {"proposals": [], "votes": []})
    return jsonify(dao.get("proposals", []))

@app.route("/dao/register_model", methods=["POST"])
def register_model():
    data = request.get_json()
    user = data.get("wallet")
    model_id = data.get("model")

    state = load_state()
    if state["balances"].get(user, 0) < STAKE_REQUIREMENT:
        return jsonify({"error": "insufficient GNV to stake"}), 400

    state["balances"][user] -= STAKE_REQUIREMENT
    registry = load_json(REGISTRY_FILE, {"models": {}})
    registry["models"][model_id] = {"owner": user, "stake": STAKE_REQUIREMENT, "active": True}
    save_json(REGISTRY_FILE, registry)
    save_state(state)

    return jsonify({"status": "model registered", "model": model_id})

@app.route("/dao/tally_votes", methods=["POST"])
def tally_votes():
    dao = load_json(DAO_FILE, {"proposals": [], "votes": []})
    registry = load_json(REGISTRY_FILE, {"models": {}})
    state = load_state()

    for proposal in dao["proposals"]:
        if proposal.get("resolved"):
            continue
        proposal_id = proposal["id"]
        proposal_votes = [v for v in dao["votes"] if v["vote"].get("proposal_id") == proposal_id]
        unique_voters = set(v["user"] for v in proposal_votes)
        if len(unique_voters) / max(1, len(state["balances"])) > VOTE_THRESHOLD:
            target = proposal["target"]
            model = registry["models"].get(target)
            if model and model["active"]:
                model["active"] = False
                state["supply"] -= model["stake"]
                del registry["models"][target]
                proposal["resolved"] = True

    save_json(DAO_FILE, dao)
    save_json(REGISTRY_FILE, registry)
    save_state(state)
    return jsonify({"status": "tally complete"})

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
    print(f"🧱 Chain length: {len(chain)}")
    return jsonify({"blocks": chain})


@app.route("/last_block", methods=["GET"])
def last_block():
    state = load_state()
    return jsonify({"block": state.get("chain", [])[-1] if state.get("chain") else None})

@app.route("/registry", methods=["GET"])
def registry():
    reg = load_json(REGISTRY_FILE, {"models": {}})
    return jsonify(reg)

@app.route("/update_dev_wallet", methods=["POST"])
def update_dev_wallet():
    data = request.get_json()
    if data.get("password") != ADMIN_PASSWORD:
        return jsonify({"error": "unauthorized"}), 401

    new_wallet = data.get("wallet")
    if not new_wallet or not new_wallet.startswith("0x") or len(new_wallet) != 42:
        return jsonify({"error": "invalid wallet"}), 400

    cfg = load_config()
    cfg["dev_wallet"] = new_wallet
    save_config(cfg)
    return jsonify({"status": "dev wallet updated", "new_wallet": new_wallet})


@app.route("/metrics", methods=["GET"])
def metrics():
    state = load_state()
    balances = state.get("balances", {})
    supply = state.get("supply", 0)
    chain = state.get("chain", [])

    tx_count = sum(len(b["txns"]) for b in chain)
    top_wallets = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10]

    return jsonify({
        "total_supply": supply,
        "wallets": len(balances),
        "tx_count": tx_count,
        "top_wallets": top_wallets
    })

def deliver_tx(tx_bytes):
    try:
        # Convert base64-encoded JSON string into dict
        tx_json = base64.b64decode(tx_bytes).decode()
        tx = json.loads(tx_json)

        if tx.get("type") == "send":
            from_addr = tx.get("from")
            to_addr = tx.get("to")
            amount = int(tx.get("amount"))

            balances = state["balances"]
            if balances.get(from_addr, 0) >= amount:
                balances[from_addr] -= amount
                balances[to_addr] = balances.get(to_addr, 0) + amount

                block = create_block([{
                    "type": "send",
                    "from": from_addr,
                    "to": to_addr,
                    "amount": amount
                }])

                return {"code": 0, "log": "transfer success", "block": block}
            else:
                return {"code": 1, "log": "insufficient funds"}

        else:
            return {"code": 1, "log": "unknown tx type"}

    except Exception as e:
        return {"code": 1, "log": f"tx decode error: {str(e)}"}

@app.route("/faucet", methods=["POST"])
def faucet():
    data = request.get_json()
    wallet = data.get("wallet")
    if not wallet:
        return jsonify({"error": "missing wallet"}), 400

    state = load_state()
    state["balances"].setdefault(wallet, 0)
    state["balances"][wallet] += 10_000_000  # 10 million GNV test

    block = create_block([{
        "type": "faucet",
        "to": wallet,
        "amount": 10_000_000
    }])

    save_state(state)
    db.collection("gnv-ledger").document("testnet").set(state)

    return jsonify({"status": "success", "wallet": wallet, "amount": 10_000_000, "block": block})


@app.route("/cosmos_tx", methods=["POST"])
def cosmos_tx():
    try:
        from base64 import b64decode
        import json

        tx = request.get_json()
        if not tx:
            return jsonify({"error": "no tx received"}), 400

        print("🔐 Received Cosmos TX:", tx)

        # Decode and parse the tx
        tx_bytes_b64 = tx.get("tx_bytes")
        if not tx_bytes_b64:
            return jsonify({"error": "tx_bytes missing"}), 400

        tx_json_str = b64decode(tx_bytes_b64).decode()
        tx_data = json.loads(tx_json_str)
        print("📦 Parsed TX:", tx_data)

        result = deliver_tx(tx_bytes_b64)
        return jsonify({"result": result})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "tx decode error", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080) 

