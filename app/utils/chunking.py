import tiktoken


def chunk_text_by_tokens(
    text: str,
    chunk_size_tokens: int = 500,
    overlap_tokens: int = 80,
    model: str = "text-embedding-3-small",
) -> list[str]:
    text = text.strip()
    if not text:
        return []

    if chunk_size_tokens <= 0:
        raise ValueError("chunk_size_tokens must be > 0")
    if overlap_tokens < 0:
        raise ValueError("overlap_tokens must be >= 0")
    if overlap_tokens >= chunk_size_tokens:
        raise ValueError("overlap_tokens must be smaller than chunk_size_tokens")

    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")

    token_ids = enc.encode(text)
    if not token_ids:
        return []

    chunks: list[str] = []
    start = 0
    step = chunk_size_tokens - overlap_tokens

    while start < len(token_ids):
        end = min(start + chunk_size_tokens, len(token_ids))
        chunk_ids = token_ids[start:end]
        chunk_text = enc.decode(chunk_ids).strip()
        if chunk_text:
            chunks.append(chunk_text)
        if end == len(token_ids):
            break
        start += step

    return chunks