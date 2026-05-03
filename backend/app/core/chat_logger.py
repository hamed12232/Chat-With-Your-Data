"""
Logging factory for the chat / retrieval pipeline.

Each call to `get_chat_logger` returns a Python Logger that writes to:
    Logs/chat/<timestamp>_<query_slug>.log

The helpers below produce a single, richly-formatted run report covering
all four pipeline steps: Embed → Retrieve → Context → Generate.
"""

import logging
import re
import time
from datetime import datetime
from pathlib import Path


# ── Directory setup ────────────────────────────────────────────────────────────

CHAT_LOGS_DIR = Path("Logs") / "chat"
CHAT_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ── Visual constants ───────────────────────────────────────────────────────────

WIDTH       = 80
DOUBLE_LINE = "=" * WIDTH
SINGLE_LINE = "─" * WIDTH
BLANK       = ""


def _slug(text: str, max_len: int = 40) -> str:
    """Turn arbitrary text into a safe, short filesystem slug."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s]+", "_", slug).strip("_")
    return slug[:max_len] if slug else "query"


# ── Logger factory ─────────────────────────────────────────────────────────────

def get_chat_logger(message: str) -> logging.Logger:
    """
    Create a file logger dedicated to one chat run.

    Log file location:
        Logs/chat/<YYYY-MM-DD_HH-MM-SS>_<query_slug>.log
    """
    ts      = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    slug    = _slug(message)
    logfile = CHAT_LOGS_DIR / f"{ts}_{slug}.log"

    logger = logging.getLogger(f"chat.{ts}.{slug}")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    fh = logging.FileHandler(logfile, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(message)s"))   # raw text — no prefix
    logger.addHandler(fh)
    logger.propagate = False    # don't bubble up to uvicorn root logger
    return logger


# ── Shared helper ─────────────────────────────────────────────────────────────

def _box(logger: logging.Logger, label: str, text: str) -> None:
    """Print `text` in full inside a labelled box — no truncation."""
    line_width = WIDTH - 6
    logger.info("  %s", label)
    logger.info("  ┌%s┐", "─" * (WIDTH - 4))
    for line in text.splitlines():
        # Wrap each source line into display-width slices
        if not line:
            logger.info("  │ %-*s │", line_width, "")
        else:
            for i in range(0, len(line), line_width):
                logger.info("  │ %-*s │", line_width, line[i : i + line_width])
    logger.info("  └%s┘", "─" * (WIDTH - 4))
    logger.info(BLANK)


# ── Section helpers ────────────────────────────────────────────────────────────

def log_chat_start(logger: logging.Logger, message: str) -> float:
    """Print the opening banner and return the start timestamp."""
    start = time.monotonic()
    logger.info(DOUBLE_LINE)
    logger.info("  CHAT PIPELINE")
    logger.info("  Started : %s", datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
    logger.info(DOUBLE_LINE)
    logger.info(BLANK)

    # Show the full user message in a box
    line_width = WIDTH - 6
    words      = message
    logger.info("  User Message:")
    logger.info("  ┌%s┐", "─" * (WIDTH - 4))
    for i in range(0, len(words), line_width):
        logger.info("  │ %-*s │", line_width, words[i : i + line_width])
    logger.info("  └%s┘", "─" * (WIDTH - 4))
    logger.info(BLANK)
    return start


def log_embed_query(
    logger: logging.Logger,
    model: str,
    message: str,
    vector: list[float],
) -> None:
    """Step 1 — embedding details for the user query."""
    dim = len(vector)

    logger.info(SINGLE_LINE)
    logger.info("  STEP 1 / 4  ·  EMBED QUERY")
    logger.info(SINGLE_LINE)
    logger.info("  %-26s %s", "Model :",             model)
    logger.info("  %-26s %d chars", "Query Length :", len(message))
    logger.info("  %-26s %d", "Vector Dimensions :", dim)
    logger.info(
        "  %-26s ~%.1f KB",
        "Memory Estimate :",
        (dim * 4) / 1024,   # 4 bytes per float32
    )

    # Show a small sample of the resulting vector
    sample = vector[:6]
    sample_str = "  [" + ",  ".join(f"{v:+.5f}" for v in sample) + ",  …]"
    logger.info("  %-26s", "Query Vector Sample :")
    logger.info(sample_str)
    logger.info("  %-26s %s", "Status :",            "✓  Query vector ready")
    logger.info(BLANK)


def log_retrieve_chunks(
    logger: logging.Logger,
    top_k: int,
    retrieved_docs: list[str],
    distances: list[float] | None,
) -> None:
    """Step 2 — what Chroma returned, with a preview table."""
    n = len(retrieved_docs)

    logger.info(SINGLE_LINE)
    logger.info("  STEP 2 / 4  ·  RETRIEVE CHUNKS")
    logger.info(SINGLE_LINE)
    logger.info("  %-26s %d", "Top-K Setting :",    top_k)
    logger.info("  %-26s %d", "Chunks Retrieved :", n)

    if n == 0:
        logger.info("  %-26s %s", "Status :", "✗  No chunks found — collection may be empty")
        logger.info(BLANK)
        return

    logger.info("  %-26s %s", "Status :", "✓  Chunks retrieved from Chroma")
    logger.info(BLANK)

    # ── Chunk preview table ────────────────────────────────────────────────────
    W_IDX  = 8    # "#  0"
    W_DIST = 10   # distance score
    W_LEN  = 10   # char count
    W_PREV = WIDTH - W_IDX - W_DIST - W_LEN - 12

    sep_top = "  ┌" + "─"*W_IDX + "┬" + "─"*W_DIST + "┬" + "─"*W_LEN + "┬" + "─"*W_PREV + "┐"
    sep_mid = "  ├" + "─"*W_IDX + "┼" + "─"*W_DIST + "┼" + "─"*W_LEN + "┼" + "─"*W_PREV + "┤"
    sep_bot = "  └" + "─"*W_IDX + "┴" + "─"*W_DIST + "┴" + "─"*W_LEN + "┴" + "─"*W_PREV + "┘"

    def tbl_row(idx: str, dist: str, length: str, preview: str) -> str:
        return (
            "  │"
            + f" {idx:<{W_IDX - 1}}" + "│"
            + f" {dist:^{W_DIST - 1}}" + "│"
            + f" {length:^{W_LEN - 1}}" + "│"
            + f" {preview:<{W_PREV - 1}}" + "│"
        )

    logger.info("  Retrieved Chunks:")
    logger.info(sep_top)
    logger.info(tbl_row("#", "Distance", "Chars", "Text Preview"))
    logger.info(sep_mid)

    for i, doc in enumerate(retrieved_docs):
        dist_str = f"{distances[i]:.4f}" if distances and i < len(distances) else "—"
        preview  = doc[:W_PREV - 4].replace("\n", " ").strip()
        if len(doc) > W_PREV - 4:
            preview += " …"
        logger.info(tbl_row(f"#{i}", dist_str, f"{len(doc):,}", preview))

    logger.info(sep_bot)
    logger.info(BLANK)


def log_build_context(
    logger: logging.Logger,
    retrieved_docs: list[str],
    context: str,
) -> None:
    """Step 3 — full context dump (no truncation)."""
    logger.info(SINGLE_LINE)
    logger.info("  STEP 3 / 4  ·  BUILD CONTEXT")
    logger.info(SINGLE_LINE)
    logger.info("  %-26s %d", "Chunks Joined :",        len(retrieved_docs))
    logger.info("  %-26s %d chars", "Context Length :",  len(context))
    logger.info("  %-26s %d", "Context Words :",         len(context.split()))
    logger.info(BLANK)

    # Print each chunk in its own labelled box so boundaries are clearly visible
    for i, chunk in enumerate(retrieved_docs):
        _box(logger, f"Chunk {i + 1} / {len(retrieved_docs)}:", chunk)

    logger.info("  %-26s %s", "Status :", "✓  Context string assembled")
    logger.info(BLANK)


def log_generate(
    logger: logging.Logger,
    model: str,
    temperature: float,
    system_prompt: str,
    message: str,
    context: str,
    answer: str,
) -> None:
    """Step 4 — full prompt dump (system prompt + user turn) and full answer."""
    user_turn     = f"{context}\n\nQuestion: {message}"
    est_prompt_tk = (len(system_prompt) + len(user_turn)) // 4
    est_reply_tk  = len(answer) // 4

    logger.info(SINGLE_LINE)
    logger.info("  STEP 4 / 4  ·  GENERATE RESPONSE")
    logger.info(SINGLE_LINE)
    logger.info("  %-26s %s",          "Model :",              model)
    logger.info("  %-26s %.2f",       "Temperature :",        temperature)
    logger.info("  %-26s ~%d tokens",  "Est. Prompt Tokens :", est_prompt_tk)
    logger.info("  %-26s ~%d tokens",  "Est. Reply Tokens :",  est_reply_tk)
    logger.info("  %-26s %d chars",    "Answer Length :",      len(answer))
    logger.info(BLANK)

    # ── Full system prompt ─────────────────────────────────────────────────────
    _box(logger, "[ SYSTEM PROMPT ]", system_prompt)

    # ── Full user turn: context + question ────────────────────────────────────
    _box(logger, "[ USER TURN  (context + question) ]", user_turn)

    # ── Full model answer ─────────────────────────────────────────────────────
    _box(logger, "[ GPT ANSWER ]", answer)

    logger.info("  %-26s %s", "Status :", "✓  Answer received from OpenAI")
    logger.info(BLANK)


def log_chat_end(
    logger: logging.Logger,
    start_time: float,
) -> None:
    """Print the closing banner with total elapsed time."""
    elapsed = time.monotonic() - start_time
    logger.info(DOUBLE_LINE)
    logger.info("  PIPELINE COMPLETE  ·  Total elapsed: %.2fs", elapsed)
    logger.info("  Finished : %s", datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
    logger.info(DOUBLE_LINE)
    logger.info(BLANK)


def log_chat_error(
    logger: logging.Logger,
    step: str,
    error: Exception,
    start_time: float,
) -> None:
    """Print a clearly-visible error banner so failures stand out in the log."""
    elapsed = time.monotonic() - start_time
    logger.info(BLANK)
    logger.info(DOUBLE_LINE)
    logger.info("  ✗  PIPELINE FAILED at step: %s", step)
    logger.info("  Error   : %s", error)
    logger.info("  Elapsed : %.2fs", elapsed)
    logger.info(DOUBLE_LINE)
    logger.info(BLANK)
