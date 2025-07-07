import json, time, hashlib, os

REAL_MODE = os.getenv("GNV_REAL", "false") == "true"
STATE_FILE = "data/state_main.json" if REAL_MODE else "data/state.json"
GENESIS_FILE = "genesis.json"

REWARD_START = 1_000_000
REWARD_END = 10
REWARD_DURATION = 365 * 24 * 60 * 60  # 1 year in seconds

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
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"height": 0, "chain": [], "balances": {}, "supply": 0, "votes": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

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
    print("✅ GNV mainnet node running.")
    print(f"📂 Using state file: {STATE_FILE}")
    print(f"🌱 Genesis time: {GENESIS_TIME}")
    print("⛏️  Awaiting block creation via gnv_api.py...")
    while True:
        time.sleep(60)
