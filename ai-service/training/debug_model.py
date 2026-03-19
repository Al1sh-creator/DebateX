"""Quick debug — see what the fine-tuned model actually outputs (raw)."""
import sys
sys.path.insert(0, '.')

from pathlib import Path
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
from peft import PeftModel

MODEL_DIR = Path("training/debate_model")
BASE = "google/flan-t5-base"

print("Loading model...")
tokenizer = T5Tokenizer.from_pretrained(str(MODEL_DIR))
base_model = T5ForConditionalGeneration.from_pretrained(BASE)
model = PeftModel.from_pretrained(base_model, str(MODEL_DIR))
model.eval()

prompt = (
    "You are a philosopher debater. "
    'DEBATE TOPIC: "Dogs are better pets than cats". '
    "YOUR STANCE: IN FAVOR OF (PRO). "
    "ROUND: 1 of 3. "
    "STRATEGY: LOGICAL ARGUMENT. "
    "Generate a persuasive 2-3 paragraph debate argument."
)

inputs = tokenizer(prompt, return_tensors="pt", max_length=192, truncation=True)

print("\n--- Greedy (no sampling) ---")
with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=400, num_beams=4)
result = tokenizer.decode(out[0], skip_special_tokens=True)
print(repr(result))
print("Length:", len(result))

print("\n--- Sampling (temperature=0.7) ---")
with torch.no_grad():
    out2 = model.generate(**inputs, max_new_tokens=400, do_sample=True, temperature=0.7, top_p=0.95)
result2 = tokenizer.decode(out2[0], skip_special_tokens=True)
print(repr(result2))
print("Length:", len(result2))
