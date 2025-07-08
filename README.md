# Gainvest GNV Node + AI Mining Model

Welcome to the Gainvest GNV Node. This repo allows anyone to run the Gainvest blockchain and mine GNV tokens by running an AI model locally.

---

## 🚀 Quick Start

### 1. Clone the Repo

```bash
git clone https://github.com/gainvest-ai/gainvest-node-public.git
cd gainvest-node-public
```

### 2. Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Start the Blockchain Node

```bash
python3 gnv_node.py  # Run this first to initialize state
```

### 4. Start the Blockchain API

```bash
export GNV_REAL=true  # or use .env for secrets
python3 gnv_api.py
```

---

## 🧠 Run the AI Model (TorchServe)

### A. Install TorchServe

```bash
pip install torchserve torch-model-archiver
```

### B. Directory Structure

Your model directory should look like this:

```
gvaimodel/
├── model-store/
│   └── gnv-model.mar
├── gnv_handler.py
```

You can download the model file (`gnv-model.mar`) from Hugging Face:

> [https://huggingface.co/gainvest-ai/gnv-11m](https://huggingface.co/gainvest-ai/gnv-11m)

Place the `.mar` file in `gvaimodel/model-store/`.

### C. Start TorchServe

```bash
cd gvaimodel
torchserve --start --model-store model-store --models gnv=gnv-model.mar --ts-config config.properties
```

> You can customize `config.properties` if needed, or just omit it to use default settings.

TorchServe will be available at:

```
http://localhost:8080/predictions/gnv
```

---

## ⛏️ Mine GNV Tokens

With both the blockchain and model running locally, you can mine like this:

```bash
curl -X POST http://localhost:8080/mine \
  -H "Content-Type: application/json" \
  -d '{"wallet": "gnv1examplewallet000000000000000000000", "prompt": "What is money?"}'
```

You’ll receive mined tokens if the model output is valid.

---

## 📦 Included Files

* `gnv_node.py` – Blockchain logic
* `gnv_api.py` – API backend
* `gvaimodel/` – Model files and TorchServe config
* `requirements.txt` – All dependencies

---

## 📌 Model Info

* Model: `gnv-model` (11M parameters)
* Format: GPT-style LM
* Language: English
* Purpose: Used for GNV mining
* License: MIT

### Hosted on Hugging Face:

[https://huggingface.co/gainvest-ai/gnv-11m](https://huggingface.co/gainvest-ai/gnv-11m)

---

## 📦 Install from PyPI (Optional CLI)

You can also install the Gainvest node tools via pip:

```bash
pip install gainvest
```

Then run:

```bash
gainvest-node --help
```

> This supports blockchain state queries, transfers, and other automation tasks.

---

## 🔐 Developer Wallet

By default, mined GNV is partially sent to the configured dev wallet. This can be customized in `config.json`.

---

## 💡 Tip

Want to build a website or app on top of GNV? You can use `/mine`, `/balance`, and `/transfer` endpoints to integrate directly with the chain.

---

## 🔗 Tags

`gainvest`, `gnv`, `blockchain`, `mining`, `llm`, `torchserve`, `ai`, `gpt`, `language-model`

---

© Gainvest 2025. MIT License.
