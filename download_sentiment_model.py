import os
# 1. 在导入 huggingface 相关库之前设置环境变量
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"          # 强制使用镜像
os.environ["HF_HUB_DISABLE_SSL_VERIFY"] = "1"                # 正确禁用 SSL 验证

# 2. 现在再导入 transformers
from pathlib import Path
from transformers import AutoModelForSequenceClassification, AutoTokenizer

def main():
    model_name = "uer/roberta-base-finetuned-jd-binary-chinese"
    target_dir = Path(__file__).resolve().parent / "ml_models" / "sentiment_analysis"
    target_dir.mkdir(parents=True, exist_ok=True)

    # 打印当前环境变量，确认生效
    print(f"当前 HF_ENDPOINT = {os.environ.get('HF_ENDPOINT')}")
    print(f"当前 HF_HUB_DISABLE_SSL_VERIFY = {os.environ.get('HF_HUB_DISABLE_SSL_VERIFY')}")

    print(f"正在从镜像下载模型: {model_name}")
    print(f"目标目录: {target_dir}")

    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    model.save_pretrained(target_dir)
    tokenizer.save_pretrained(target_dir)

    print("模型和分词器下载并保存完成。")

if __name__ == "__main__":
    main()