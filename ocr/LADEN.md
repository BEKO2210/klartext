# Modellgewichte nachladen

Die großen Modelldateien liegen nicht im Git. Nach einem frischen Checkout:

```bash
cd /pfad/zu/klartext

# PP-OCRv6 medium (Texterkennung, aktiv seit 1.4.0) — Apache-2.0
mkdir -p ocr/rapidocr-v6
curl -L -o ocr/rapidocr-v6/PP-OCRv6_det_medium.onnx \
  "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.9.1/onnx/PP-OCRv6/det/PP-OCRv6_det_medium.onnx"
curl -L -o ocr/rapidocr-v6/PP-OCRv6_rec_medium.onnx \
  "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.9.1/onnx/PP-OCRv6/rec/PP-OCRv6_rec_medium.onnx"

# TableFormer v2 (Tabellenmodell, NICHT aktiv — am Messstand abgelehnt,
# liegt als Kandidat für spätere Versionen bereit) — siehe CHANGELOG 1.4.0
mkdir -p ocr/tableformer-v2
for f in config.json generation_config.json model.safetensors \
         special_tokens_map.json tokenizer.json tokenizer_config.json; do
  curl -L -o "ocr/tableformer-v2/$f" \
    "https://huggingface.co/docling-project/TableFormerV2/resolve/main/$f"
done
```

`ocr/tessdata/deu.traineddata` (Tesseract-Sprachpaket) liegt im Git, weil es
klein genug ist.

Der Download passiert auf dem **Host** — der Docling-Container läuft bewusst
mit `HF_HUB_OFFLINE=1` und kann selbst nichts nachladen. Die Verzeichnisse
werden read-only in den Container gemountet (siehe `docker-compose.yml`).
