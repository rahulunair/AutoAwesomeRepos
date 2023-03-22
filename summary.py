from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

bart_model = AutoModelForSeq2SeqLM.from_pretrained("sshleifer/distilbart-cnn-12-6")
bart_tokenizer = AutoTokenizer.from_pretrained("sshleifer/distilbart-cnn-12-6")


def generate_summary(text, max_length=100):
    inputs = bart_tokenizer.encode(text, return_tensors="pt", truncation=True)
    summary_ids = bart_model.generate(
        inputs,
        max_length=max_length,
        min_length=35,
        num_beams=4,
    )
    summary = bart_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    last_fullstop = summary.rfind(".")
    if last_fullstop != -1:
        summary = summary[:last_fullstop]
    return summary
