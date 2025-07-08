from transformers import GPT2Config, GPT2LMHeadModel
from tokenizers import Tokenizer
import torch
import os
import json

class MyHandler:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None

    def initialize(self, ctx):
        model_dir = ctx.system_properties.get("model_dir")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load tokenizer
        self.tokenizer = Tokenizer.from_file(os.path.join(model_dir, "tokenizer.json"))

        # Load model config
        config_path = os.path.join(model_dir, "config.json")
        config = GPT2Config.from_json_file(config_path)

        # Load model weights using from_pretrained workaround
        model_path = os.path.join(model_dir, "mini_manual_gpt2.pth")
        self.model = GPT2LMHeadModel(config)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))

        self.model.to(self.device)
        self.model.eval()


    def handle(self, data, ctx):
        try:
            # Safely extract input
            raw_input = data[0].get("body") if data and data[0] else None

            # Decode if bytes, or pass through if already dict
            if isinstance(raw_input, (bytes, bytearray)):
                raw_input = raw_input.decode("utf-8")
            if isinstance(raw_input, str):
                input_json = json.loads(raw_input)
            elif isinstance(raw_input, dict):
                input_json = raw_input
            else:
                raise ValueError("Unsupported input format")

            input_text = input_json.get("text", "")

            # Tokenize and generate
            encoded = self.tokenizer.encode(input_text)
            input_ids = torch.tensor([encoded.ids], dtype=torch.long).to(self.device)

            output_ids = self.model.generate(input_ids, max_length=50)[0].tolist()
            output_text = self.tokenizer.decode(output_ids)

            return [output_text]
        except Exception as e:
            return [f"❌ Handler error: {str(e)}"]
