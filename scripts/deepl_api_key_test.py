"""
This file is for validating that the DeepL API key works correctly.
It is a small manual check and is not part of the main application flow.
"""
import deepl
from dotenv import dotenv_values

config = dotenv_values(".env")

deepl_client = deepl.DeepLClient(config["DEEPL_API_KEY"])

result = deepl_client.translate_text(['Hello, World!'], target_lang="FR")
print(result[0].text)
