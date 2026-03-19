"""
DebateX — Fine-Tuning Script
============================
Fine-tunes google/flan-t5-base on the debate dataset using LoRA (parameter-efficient).

Requirements:
    pip install transformers peft torch datasets accelerate

Run:
    python training/train.py

Output:
    training/debate_model/   (LoRA adapter + tokenizer)
"""

import json
import os
from pathlib import Path

# ── Imports ──────────────────────────────────────────────────

try:
    import torch
    from transformers import (
        T5ForConditionalGeneration,
        T5Tokenizer,
        TrainingArguments,
        Trainer,
        DataCollatorForSeq2Seq,
    )
    from peft import (
        LoraConfig,
        get_peft_model,
        TaskType,
        PeftModel,
    )
    from datasets import Dataset
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Install with: pip install transformers peft torch datasets accelerate")
    exit(1)


# ── Config ───────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
DATASET_PATH = SCRIPT_DIR / "debate_dataset.jsonl"
MODEL_OUTPUT_DIR = SCRIPT_DIR / "debate_model"
BASE_MODEL = "google/flan-t5-base"

MAX_SOURCE_LEN = 192   # Shorter = faster tokenization
MAX_TARGET_LEN = 256

# ── CPU vs GPU auto-tuning ────────────────────────────────────
import torch as _torch
_on_gpu = _torch.cuda.is_available()

# CPU mode: 200 samples, bs=8, 3 epochs  → ~20-35 min
# GPU mode: full dataset, bs=8, 3 epochs → ~10-15 min
MAX_SAMPLES   = None if _on_gpu else 200
BATCH_SIZE    = 8
EPOCHS        = 3
LEARNING_RATE = 3e-4


# ── LoRA Config ───────────────────────────────────────────────

LORA_CONFIG = LoraConfig(
    task_type=TaskType.SEQ_2_SEQ_LM,
    r=8,                    # LoRA rank (lower = faster, less memory)
    lora_alpha=32,          # Scaling factor
    lora_dropout=0.05,
    target_modules=["q", "v"],   # Attention layers to adapt
    bias="none",
)


# ── Data Loading ─────────────────────────────────────────────

def load_dataset_from_jsonl(path: Path) -> Dataset:
    """Load JSONL file into HuggingFace Dataset."""
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}. Run generate_dataset.py first."
        )

    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    prompts = [r["prompt"] for r in records]
    completions = [r["completion"] for r in records]

    print(f"   Loaded {len(records)} training samples from {path.name}")
    return Dataset.from_dict({"input_text": prompts, "target_text": completions})


def tokenize_function(examples, tokenizer):
    """Tokenize both prompt and completion for seq2seq training."""
    model_inputs = tokenizer(
        examples["input_text"],
        max_length=MAX_SOURCE_LEN,
        truncation=True,
        padding="max_length",
    )
    labels = tokenizer(
        examples["target_text"],
        max_length=MAX_TARGET_LEN,
        truncation=True,
        padding="max_length",
    )
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


# ── Training ─────────────────────────────────────────────────

def train():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n🚀 DebateX Fine-Tuning")
    print(f"   Base model : {BASE_MODEL}")
    print(f"   Device     : {device.upper()}")
    print(f"   Epochs     : {EPOCHS}")
    print(f"   Batch size : {BATCH_SIZE}")
    print(f"   Output     : {MODEL_OUTPUT_DIR}")
    print()

    # 1. Load tokenizer and base model
    print("📥 Loading base model and tokenizer...")
    tokenizer = T5Tokenizer.from_pretrained(BASE_MODEL)
    model = T5ForConditionalGeneration.from_pretrained(BASE_MODEL)

    # 2. Apply LoRA
    print("🔧 Applying LoRA adapter...")
    model = get_peft_model(model, LORA_CONFIG)
    model.print_trainable_parameters()

    # 3. Load and tokenize dataset
    print(f"\n📂 Loading dataset from {DATASET_PATH.name}...")
    raw_dataset = load_dataset_from_jsonl(DATASET_PATH)

    # Cap dataset size for CPU runs (auto-detected)
    if MAX_SAMPLES and len(raw_dataset) > MAX_SAMPLES:
        raw_dataset = raw_dataset.shuffle(seed=42).select(range(MAX_SAMPLES))
        print(f"   ⚡ CPU mode: using {MAX_SAMPLES} samples (dataset capped for speed)")

    # Split 90/10 train/validation
    split = raw_dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = split["train"]
    eval_dataset = split["test"]

    print(f"   Train: {len(train_dataset)} | Eval: {len(eval_dataset)}")
    print("\n🔄 Tokenizing dataset...")

    tokenize_fn = lambda examples: tokenize_function(examples, tokenizer)
    train_tokenized = train_dataset.map(
        tokenize_fn, batched=True, remove_columns=["input_text", "target_text"]
    )
    eval_tokenized = eval_dataset.map(
        tokenize_fn, batched=True, remove_columns=["input_text", "target_text"]
    )

    # 4. Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer, model=model, padding=True
    )

    # 5. Training arguments
    training_args = TrainingArguments(
        output_dir=str(MODEL_OUTPUT_DIR / "checkpoints"),
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        warmup_steps=50,
        weight_decay=0.01,
        learning_rate=LEARNING_RATE,
        logging_dir=str(MODEL_OUTPUT_DIR / "logs"),
        logging_steps=50,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        fp16=torch.cuda.is_available(),   # use fp16 if GPU available
        report_to="none",                 # disable wandb / tensorboard
    )

    # 6. Trainer
    print("\n🏋️  Starting training...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_tokenized,
        eval_dataset=eval_tokenized,
        data_collator=data_collator,
    )

    trainer.train()

    # 7. Save model + tokenizer
    print(f"\n💾 Saving fine-tuned model to {MODEL_OUTPUT_DIR}...")
    MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(MODEL_OUTPUT_DIR))
    tokenizer.save_pretrained(str(MODEL_OUTPUT_DIR))

    print("\n✅ Training complete!")
    print(f"   Model saved to: {MODEL_OUTPUT_DIR}")
    print(f"\n🧪 Test it with:")
    print(f"   python training/test_model.py")


if __name__ == "__main__":
    train()
