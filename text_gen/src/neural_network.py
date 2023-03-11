import sys
import re
import json

from tqdm import tqdm

import torch
from transformers import TextDataset, DataCollatorForLanguageModeling
from torch.utils.data import DataLoader

from accelerate import Accelerator
from transformers import AdamW, AutoModelForSequenceClassification, get_scheduler
from transformers import AutoModelForCausalLM, AutoTokenizer


class NeuralNetwork:
    def __init__(self, group_id=0):
        self.DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        checkpoint = "Kirili4ik/ruDialoGpt3-medium-finetuned-telegram"
        self.tokenizer = AutoTokenizer.from_pretrained(checkpoint)
        self.model = AutoModelForCausalLM.from_pretrained(checkpoint)
        self.group_id = group_id
        self.train_dataset = None
        self.test_dataset = None
        self.data_collator = None

    def get_length_param(self, text: str) -> str:
        tokens_count = len(self.tokenizer.encode(text))
        if tokens_count <= 15:
            len_param = '1'
        elif tokens_count <= 50:
            len_param = '2'
        elif tokens_count <= 256:
            len_param = '3'
        else:
            len_param = '-'
        return len_param

    def build_text_file(self, texts: list[str], dest_path: str):
        with open(dest_path, 'w') as f:
            for text in texts:
                post_text = re.sub(r"\n", ". ", text)
                if len(post_text) == 0 or type(post_text) != str:
                    continue
                length = self.get_length_param(post_text)
                f.write(f"|{length}|{post_text}{self.tokenizer.eos_token}\n")

    def load_dataset(self, train_path, test_path):
        self.train_dataset = TextDataset(
            tokenizer=self.tokenizer,
            file_path=train_path,
            block_size=256
        )

        self.test_dataset = TextDataset(
            tokenizer=self.tokenizer,
            file_path=test_path,
            block_size=256
        )

        self.data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer, mlm=False
        )

    def train(self, checkpoint_path: str):
        train_loader = DataLoader(self.train_dataset, shuffle=True, batch_size=1, collate_fn=self.data_collator)
        test_loader = DataLoader(self.test_dataset, batch_size=1, collate_fn=self.data_collator)

        num_epochs = 3
        optimizer = AdamW(self.model.parameters(), lr=3e-5)
        save_checkpoint_path = checkpoint_path

        num_training_steps = num_epochs * len(self.train_dataset)
        lr_scheduler = get_scheduler(
            "linear",
            optimizer=optimizer,
            num_warmup_steps=100,
            num_training_steps=num_training_steps
        )

        accelerator = Accelerator()
        train_dl, test_dl, self.model, optimizer = accelerator.prepare(
            train_loader, test_loader, self.model, optimizer
        )

        progress_bar = tqdm(range(num_training_steps))

        for epoch in range(num_epochs):
            self.model.train()
            for batch in train_dl:
                optimizer.zero_grad()
                outputs = self.model(**batch)
                loss = outputs.loss
                accelerator.backward(loss)
                optimizer.step()
                lr_scheduler.step()
                progress_bar.update(1)

            torch.save({
                'model_state_dict': self.model.state_dict(),
            }, save_checkpoint_path)

            cum_loss = 0
            self.model.eval()
            with torch.inference_mode():
                for batch in test_dl:
                    outputs = self.model(**batch)
                    cum_loss += float(outputs.loss.item())
            print(cum_loss / len(self.test_loader))


class NeuralGenerator:
    def __init__(self, path_to_checkpoint):
        self.DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        checkpoint = "Kirili4ik/ruDialoGpt3-medium-finetuned-telegram"
        self.tokenizer = AutoTokenizer.from_pretrained(checkpoint)
        self.model = AutoModelForCausalLM.from_pretrained(checkpoint)
        checkpoint = torch.load(path_to_checkpoint, map_location=self.DEVICE)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()

    def generate(self, text):
        text = "<|startoftext|>" + text
        input_ids = self.tokenizer.encode(text, return_tensors="pt").to(self.DEVICE)
        self.model.eval()
        with torch.no_grad():
            out = self.model.generate(input_ids,
                                      do_sample=True,
                                      num_beams=2,
                                      temperature=1.5,
                                      top_p=0.9,
                                      max_length=500,
                                      num_return_sequences=1,
                                      )
        generated_text = list(map(self.tokenizer.decode, out))[0]
        generated_text = generated_text.replace("<|startoftext|>", "")
        generated_text = generated_text.split("</s>")[0].strip()
        return generated_text
