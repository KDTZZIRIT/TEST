import os

def load_prompt_template():
    path = os.path.join(os.path.dirname(__file__), "prompt_template.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def apply_template(template: str, data: dict) -> str:
    try:
        return template.format(**data)
    except KeyError as e:
        print("[ERROR] 프롬프트 템플릿 치환 실패:", e)
        raise