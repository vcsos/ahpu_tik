# your_project/ml_utils/model_loader.py
import os
from django.conf import settings
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

MODEL_CACHE = {}


def load_sentiment_model():
    if "sentiment" not in MODEL_CACHE:
        model_path = os.path.join(settings.BASE_DIR, "ml_models/sentiment_analysis")

        MODEL_CACHE["sentiment"] = {
            "model": AutoModelForSequenceClassification.from_pretrained(model_path),
            "tokenizer": AutoTokenizer.from_pretrained(model_path)
        }
    return MODEL_CACHE["sentiment"]


class SentimentAnalyzer:
    def __init__(self):
        resources = load_sentiment_model()
        self.model = resources["model"]
        self.tokenizer = resources["tokenizer"]
        self.model.eval()  # 设置为评估模式

    def predict(self, text):
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128
        )
        with torch.no_grad():
            outputs = self.model(**inputs)  # logits 形状为 (1, 2)

        # 获取两个类别的 logits 值（0=消极，1=积极）
        negative_logit, positive_logit = outputs.logits[0]
        # 预测类别：取 logits 更大的类别索引（0 或 1）
        predicted_class_idx = torch.argmax(outputs.logits[0]).item()
        return self._convert_score(predicted_class_idx)  # 传入类别索引而非单个分数

    def _convert_score(self, class_idx):
        """根据类别索引（0=消极，1=积极）转换为标签"""
        return "消极" if class_idx == 0 else "积极"

    def get_raw_score(self, text):
        """获取积极类别的 logits 值（索引 1）并保留两位小数"""
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128
        )
        with torch.no_grad():
            outputs = self.model(**inputs)
        positive_logit = outputs.logits[0][1].item()  # 取积极类别（索引 1）的 logits
        return round(positive_logit, 2)

    def get_full_prediction(self, text):
        """返回完整预测信息（类别索引、logits、概率）"""
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
        with torch.no_grad():
            outputs = self.model(**inputs)
        logits = outputs.logits[0].tolist()  # 二维列表转为一维
        probs = torch.softmax(outputs.logits[0], dim=0).tolist()  # 计算概率
        predicted_class_idx = torch.argmax(outputs.logits[0]).item()
        return {
            "text": text,
            "predicted_label": self._convert_score(predicted_class_idx),
            "logits": logits,  # 原始分数 [消极logits, 积极logits]
            "probs": probs  # 概率 [消极概率, 积极概率]
        }


