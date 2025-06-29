import base64


def decode_text(encoded_text: str):
    try:
        return base64.urlsafe_b64decode(encoded_text.encode('utf-8')).decode('utf-8')
    except Exception as e:
        return e