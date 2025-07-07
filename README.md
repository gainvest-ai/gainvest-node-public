
# 🚀 Gainvest Node (Public MVP)

A lightweight Python blockchain node for mining GNV tokens through AI interactions.

---

## 📦 Directory Structure

```

gainvest-node-public/
├── gnv\_api.py              # Flask backend API
├── gnv\_node.py             # Blockchain + mining logic
├── genesis.json            # Genesis timestamp for mining decay (optional)
├── config.json.example     # Template config (safe public version)
├── requirements.txt        # Python dependencies
├── README.md               # You're reading it!
├── .gitignore              # Ignores state, secrets, local dev files
└── data/
├── state.json          # Dummy local chain state
└── state\_main.json     # Dummy mainnet chain state

````

---

## ⚙️ Setup Instructions

### 1. Clone + Install

```bash
git clone https://github.com/gainvest-ai/gainvest-node-public.git
cd gainvest-node-public
pip install -r requirements.txt
````

### 2. Configure the Node

```bash
cp config.json.example config.json
```

Edit `config.json` with your dev wallet address and auth key:

```json
{
  "dev_wallet": "gnv1examplewallet000000000000000000000",
  "auth_key": "YOUR_PUBLIC_AUTH_KEY"
}
```

---

## 🚀 Run the Node

```bash
python gnv_api.py
```

This starts the API server at:
`http://localhost:8080`

---

## ⛏️ Mining GNV Tokens

Use the `/mine` endpoint to submit prompts and mine tokens:

```bash
curl -X POST http://localhost:8080/mine \
  -H "Content-Type: application/json" \
  -d '{
    "wallet": "gnv1examplewallet...",
    "prompt": "What was the market cap of Apple in 2023?"
  }'
```

### 🤖 Expected Model Endpoint

Your AI model should be accessible at:

```http
POST /predictions/gnv-model
```

And return a JSON response like:

```json
{
  "output": "Apple's 2023 market cap was $3 trillion."
}
```

Update `model_url` inside `gnv_api.py` to match your model location.

---

## 🔁 Token Transfers

```bash
POST /transfer
{
  "from": "gnv1...",
  "to": "gnv1...",
  "amount": 1000
}
```

Transfers GNV from one wallet to another, on-chain.

---

## 💧 Faucet for Testing

```bash
POST /faucet
{
  "wallet": "gnv1..."
}
```

Grants 10,000,000 test GNV to the given wallet.

---

## 🔍 Explorer APIs

| Endpoint            | Description                   |
| ------------------- | ----------------------------- |
| `/state`            | Full chain state and balances |
| `/supply`           | Current total GNV supply      |
| `/balance/<wallet>` | Balance of a specific wallet  |
| `/blocks`           | All blocks in the chain       |
| `/last_block`       | Most recent block             |
| `/metrics`          | Supply, top wallets, tx count |

---

## 🗳️ DAO + Governance

| Endpoint              | Description                              |
| --------------------- | ---------------------------------------- |
| `/dao/register_model` | Stake GNV to register an AI model        |
| `/dao/report`         | Flag a model for slashing                |
| `/dao/vote`           | Vote on a proposal                       |
| `/dao/proposals`      | View all open proposals                  |
| `/dao/tally_votes`    | Finalize proposals if vote threshold met |

> Voting and governance are stored on-chain in `dao_state.json`

---

## 🧠 Customization

### 🔗 Update the Model URL

In `gnv_api.py`, change:

```python
model_url = "http://localhost:5000/predictions/gnv-model"
```

To your actual model serving URL.

---

## 🔐 Secrets + Git Ignore

**Never commit sensitive info.** Use `.gitignore` to exclude:

```gitignore
# Secrets
.env
config.json

# State files
data/state.json
data/state_main.json

# Dev/Editor
__pycache__/
*.pyc
.vscode/
```

---

## 🧾 License

MIT © 2025 Gainvest AI
Public open-source implementation of GNV node logic.

---

## 🙌 Contributing

Fork the repo, create a branch, and submit a PR to improve the project!

```

---

Let me know if you'd like:
- A prewritten `requirements.txt`
- Final dummy `state.json` and `state_main.json` again
- Help with pushing the repo live to GitHub
```
