#!/usr/bin/env python3
"""Usage: python3 translate.py "text to translate" [TARGET_LANG] [SOURCE_LANG]
Default target: EN-US. Example: python3 translate.py "Hola mundo" EN-US ES"""
import sys, os, deepl
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

args = sys.argv[1:]
if not args:
    sys.exit("Usage: translate.py <text> [target_lang] [source_lang]")

text   = args[0]
target = args[1] if len(args) > 1 else "EN-US"
source = args[2] if len(args) > 2 else None

result = deepl.Translator(os.environ["DEEPL_API_KEY"]).translate_text(text, target_lang=target, source_lang=source)
print(f"[{result.detected_source_lang} → {target}] {result.text}")
