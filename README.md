
# Gainvest

**The AI-powered Proof of Thought protocol.**

Gainvest is a minimal blockchain and API stack that transforms human-AI interaction into a native currency: GNV tokens. Every user prompt + model output pair is hashed and mined into an append-only ledger — a blockchain for cognition, not electricity or stake.

## 🌐 Canonical Endpoints
| Network | URL | Purpose |
| ------- | --- | ------- |
| **Mainnet** | https://mainnet.gainvest.ai | Production mining, transfers, DAO, registry, canonical ledger |
| **Testnet** | https://testnet.gainvest.ai | Sandbox environment for testing and integration development |

## 🔧 API Overview
Gainvest exposes a minimal REST API:

- `/mine` — Mine GNV on mainnet
- `/testmine` — Mine GNV on testnet
- `/balance/<wallet>` — Query wallet balance
- `/supply` — Query total circulating supply
- `/blocks` — Full block history
- `/metrics` — Summary stats (supply, wallets, top holders)
- `/transfer` — Transfer tokens between wallets
- `/faucet` — Faucet funding (testnet only)
- `/dao/*` — DAO voting and governance API
- `/registry` — Public model registry
- `/status` — Current chain ID / service status

Wallet compatibility: Cosmos SDK / Keplr-compatible (`gnv1...` address format).

## 🔗 Developer Resources
- **Explorer UI:**  
  https://gainvest.ai/stats

- **White paper:**  
  [Gainvest: A Peer-to-Peer AI-Powered Protocol for the Thought Economy](https://gainvest.ai/whitepaper.pdf)

## 📦 Local Node (optional)
Run a Gainvest node locally for development or self-hosting:
```

pip install gainvest

```

Then configure and run your own ledger + API.

## 📖 Learn More
- Website: [https://gainvest.ai](https://gainvest.ai)
- Contact: nashid@gainvest.ai
```

