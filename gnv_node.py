import json, time, hashlib, os
from google.cloud import firestore

REAL_MODE = os.getenv("GNV_REAL", "false") == "true"
NETWORK_ID = "mainnet" if REAL_MODE else "testnet"

GENESIS_FILE = "genesis.json"

REWARD_START = 1_000_000
REWARD_END = 10
REWARD_DURATION = 365 * 24 * 60 * 60  # 1 year

# Init Firestore
db = firestore.Client()
COLLECTION = "gnv-ledger"

def load_genesis_time():
    if os.path.exists(GENESIS_FILE):
        with open(GENESIS_FILE, "r") as f:
            return json.load(f)["genesis_time"]
    genesis_time = time.time()
    with open(GENESIS_FILE, "w") as f:
        json.dump({"genesis_time": genesis_time}, f)
    return genesis_time

GENESIS_TIME = load_genesis_time()

def load_state():
    doc = db.collection(COLLECTION).document(NETWORK_ID).get()
    if doc.exists:
        return doc.to_dict()
    return {"height": 0, "chain": [], "balances": {}, "supply": 0, "votes": []}

def save_state(state):
    db.collection(COLLECTION).document(NETWORK_ID).set(state)

def create_block(txns):
    state = load_state()
    height = state["height"] + 1
    block = {
        "height": height,
        "timestamp": time.time(),
        "txns": txns,
        "hash": hashlib.sha256(json.dumps(txns).encode()).hexdigest(),
    }
    state["height"] = height
    state["chain"].append(block)
    save_state(state)
    return block

def compute_reward(score):
    now = time.time()
    elapsed = min(now - GENESIS_TIME, REWARD_DURATION)
    decay_ratio = 1 - (elapsed / REWARD_DURATION)
    base_reward = REWARD_END + (REWARD_START - REWARD_END) * decay_ratio
    reward = base_reward
    burn = reward * 0.10
    dev = reward * 0.10
    miner = reward - burn - dev
    return miner, burn, dev

if __name__ == "__main__":
    print(f"✅ GNV {NETWORK_ID} node running with Firestore-backed ledger.")
    print(f"🌱 Genesis time: {GENESIS_TIME}")
    print("⛏️  Awaiting block creation via gnv_api.py...")
    while True:
        time.sleep(60)
