from unidecode import unidecode
def normalizar_texto(txt: str) -> str:
    if not txt: return ""
    return " ".join(unidecode(txt).lower().strip().split())
