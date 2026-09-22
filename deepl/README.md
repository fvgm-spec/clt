# DeepL CLI Translator

A minimal command line tool to translate text using the DeepL API.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Credentials are stored in `.env`:
```
DEEPL_API_KEY=your-api-key-here
```

---

## Usage

```bash
python3 translate.py "<text>" [target_lang] [source_lang]
```

| Argument | Required | Default | Description |
|---|---|---|---|
| `text` | ✅ | — | Text to translate (wrap in quotes) |
| `target_lang` | ❌ | `EN-US` | Target language code |
| `source_lang` | ❌ | auto-detect | Source language code |

---

## Examples

```bash
# Auto-detect source, translate to English
python3 translate.py "Hola, ¿cómo estás?"
# [ES → EN-US] Hi, how are you?

# Translate to Spanish
python3 translate.py "Hello world" ES
# [EN → ES] Hola, mundo

# Translate to Brazilian Portuguese
python3 translate.py "Bonjour le monde" PT-BR
# [FR → PT-BR] Olá, mundo

# Specify both target and source explicitly
python3 translate.py "Hello world" FR EN
# [EN → FR] Bonjour le monde
```

---

## Supported Language Codes

| Code | Language |
|---|---|
| `EN-US` | English (US) |
| `EN-GB` | English (UK) |
| `ES` | Spanish |
| `FR` | French |
| `DE` | German |
| `IT` | Italian |
| `PT-BR` | Portuguese (Brazil) |
| `PT-PT` | Portuguese (Portugal) |
| `JA` | Japanese |
| `ZH` | Chinese (simplified) |
| `NL` | Dutch |
| `PL` | Polish |
| `RU` | Russian |

Full list: https://developers.deepl.com/docs/resources/supported-languages

---

## Plan

- API: DeepL API Free/Developer
- Character limit: 1,000,000 / month
- Check usage: `python3 translator.py` (prints current usage)
