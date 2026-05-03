"""
Logging factory for the indexing pipeline.

Each call to `get_indexing_logger` returns a Python Logger that writes to:
    Logs/indexing/<timestamp>_<filename>.log

The helpers below (log_before_chunks, log_after_chunks, log_embedding,
log_chroma_stored) produce a single, richly-formatted run report.
"""

import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path


# ── Directory setup ────────────────────────────────────────────────────────────

LOGS_DIR = Path("Logs") / "indexing"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ── Visual constants ───────────────────────────────────────────────────────────

WIDTH        = 80
DOUBLE_LINE  = "=" * WIDTH
SINGLE_LINE  = "─" * WIDTH
BLANK        = ""


def _safe_name(filename: str) -> str:
    """Strip unsafe characters so the filename can be used inside a log path."""
    return re.sub(r"[^\w\-.]", "_", filename)


# ── Logger factory ─────────────────────────────────────────────────────────────

def get_indexing_logger(source_filename: str) -> logging.Logger:
    """
    Create (or return) a file logger dedicated to one indexing run.

    The log file is placed at:
        Logs/indexing/<YYYY-MM-DD_HH-MM-SS>_<source_filename>.log
    """
    ts      = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe    = _safe_name(source_filename)
    logfile = LOGS_DIR / f"{ts}_{safe}.log"

    logger = logging.getLogger(f"indexing.{ts}.{safe}")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers when the same logger name is reused
    if logger.handlers:
        return logger

    fh = logging.FileHandler(logfile, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(message)s"))   # raw text — no prefix
    logger.addHandler(fh)
    logger.propagate = False    # don't bubble up to uvicorn root logger
    return logger


# ── Section helpers ────────────────────────────────────────────────────────────

def log_pipeline_start(logger: logging.Logger, filename: str) -> float:
    """Print the banner and return the start timestamp."""
    start = time.monotonic()
    logger.info(DOUBLE_LINE)
    logger.info("  INDEXING PIPELINE  ·  %s", filename)
    logger.info("  Started : %s", datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
    logger.info(DOUBLE_LINE)
    logger.info(BLANK)
    return start


def log_before_chunks(
    logger: logging.Logger,
    filename: str,
    file_size_bytes: int,
    num_pages: int,
    full_text: str,
) -> None:
    """Section 1 — raw document info before any splitting."""
    preview = full_text[:300].replace("\n", " ").strip()
    if len(full_text) > 300:
        preview += " …"

    logger.info(SINGLE_LINE)
    logger.info("  STEP 1 / 4  ·  BEFORE CHUNKING")
    logger.info(SINGLE_LINE)
    logger.info("  %-18s %s",   "File Name :",    filename)
    logger.info("  %-18s %s",   "File Size :",    f"{file_size_bytes:,} bytes  ({file_size_bytes / 1024:.1f} KB)")
    logger.info("  %-18s %s",   "Pages :",        num_pages)
    logger.info("  %-18s %s",   "Total Chars :",  f"{len(full_text):,}")
    logger.info("  %-18s %s",   "Total Words :",  f"{len(full_text.split()):,}")
    logger.info(BLANK)
    logger.info("  Raw Text Preview (first 300 chars):")
    logger.info("  ┌%s┐", "─" * (WIDTH - 4))
    # Wrap preview into lines of (WIDTH - 6) chars
    line_width = WIDTH - 6
    for i in range(0, len(preview), line_width):
        logger.info("  │ %-*s │", line_width, preview[i : i + line_width])
    logger.info("  └%s┘", "─" * (WIDTH - 4))
    logger.info(BLANK)


def log_after_chunks(
    logger: logging.Logger,
    chunks: list[str],
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    """Section 2 — chunk statistics after splitting."""
    lengths   = [len(c) for c in chunks]
    avg_len   = sum(lengths) / len(lengths) if lengths else 0
    min_len   = min(lengths) if lengths else 0
    max_len   = max(lengths) if lengths else 0

    logger.info(SINGLE_LINE)
    logger.info("  STEP 2 / 4  ·  AFTER CHUNKING")
    logger.info(SINGLE_LINE)
    logger.info("  %-22s %s", "Chunk Size (setting) :",   chunk_size)
    logger.info("  %-22s %s", "Chunk Overlap (setting) :", chunk_overlap)
    logger.info("  %-22s %s", "Total Chunks :",            len(chunks))
    logger.info("  %-22s %s", "Avg Chunk Length :",        f"{avg_len:.0f} chars")
    logger.info("  %-22s %s", "Min Chunk Length :",        f"{min_len} chars")
    logger.info("  %-22s %s", "Max Chunk Length :",        f"{max_len} chars")
    logger.info(BLANK)

    # Table header
    col_idx     = 7
    col_len     = 14
    col_preview = WIDTH - col_idx - col_len - 10
    border_top  = f"  ┌{'─' * col_idx}┬{'─' * col_len}┬{'─' * col_preview}┐"
    border_head = f"  ├{'─' * col_idx}┼{'─' * col_len}┼{'─' * col_preview}┤"
    border_bot  = f"  └{'─' * col_idx}┴{'─' * col_len}┴{'─' * col_preview}┘"

    logger.info("  Chunk Details:")
    logger.info(border_top)
    logger.info(
        "  │ %-*s│ %-*s│ %-*s│",
        col_idx - 1,  " #",
        col_len - 1,  " Length",
        col_preview - 1, " Preview",
    )
    logger.info(border_head)

    max_show = 20   # print at most 20 rows to keep log manageable
    for i, chunk in enumerate(chunks[:max_show]):
        preview = chunk[:col_preview - 4].replace("\n", " ").strip()
        if len(chunk) > col_preview - 4:
            preview += " …"
        logger.info(
            "  │ %-*s│ %-*s│ %-*s│",
            col_idx - 1,  f" #{i:04d}",
            col_len - 1,  f" {len(chunk):,} chars",
            col_preview - 1, f" {preview}",
        )

    if len(chunks) > max_show:
        logger.info(
            "  │ %-*s│ %-*s│ %-*s│",
            col_idx - 1,  " …",
            col_len - 1,  " …",
            col_preview - 1, f" … ({len(chunks) - max_show} more chunks not shown)",
        )

    logger.info(border_bot)
    logger.info(BLANK)


def log_embedding(
    logger: logging.Logger,
    model: str,
    num_chunks: int,
    vector_dim: int | None = None,
) -> None:
    """Section 3 — embedding model info including vector shape."""
    logger.info(SINGLE_LINE)
    logger.info("  STEP 3 / 4  ·  EMBEDDING")
    logger.info(SINGLE_LINE)
    logger.info("  %-26s %s", "Model :",            model)
    logger.info("  %-26s %s", "Chunks to Embed :",  num_chunks)

    if vector_dim is not None:
        logger.info("  %-26s %s", "Vector Dimensions :", vector_dim)
        logger.info(
            "  %-26s (%d chunks  ×  %d dims)  =  %s floats total",
            "Output Tensor Shape :",
            num_chunks,
            vector_dim,
            f"{num_chunks * vector_dim:,}",
        )
        logger.info("  %-26s %s", "Dtype :",            "float32  (OpenAI default)")
        logger.info(
            "  %-26s ~%.1f KB",
            "Memory Estimate :",
            (num_chunks * vector_dim * 4) / 1024,   # 4 bytes per float32
        )
    else:
        logger.info("  %-26s %s", "Vector Dimensions :", "(probing …)")

    logger.info("  %-26s %s", "Status :",           "✓  Embeddings received from OpenAI")
    logger.info(BLANK)


def log_vectors_table(
    logger: logging.Logger,
    vectors: list[list[float]],
    max_chunks: int = 8,
    sample_dims: int = 4,
) -> None:
    """
    After-embedding analysis — prints a table where every row is one chunk-vector
    and the columns are a sample of its raw float values plus the L2 norm.

    Layout (sample_dims=4):
      │ Chunk  │   dim[0]   │   dim[1]   │   dim[2]   │   dim[3]   │  L2 norm  │
    """
    total_chunks = len(vectors)
    vector_dim   = len(vectors[0]) if vectors else 0
    show_n       = min(max_chunks, total_chunks)

    logger.info(SINGLE_LINE)
    logger.info("  STEP 3 / 4  ·  EMBEDDING  —  VECTOR ANALYSIS")
    logger.info(SINGLE_LINE)
    logger.info(
        "  Showing %d of %d chunk-vectors  ·  %d of %d dimensions displayed",
        show_n, total_chunks, sample_dims, vector_dim,
    )
    logger.info(BLANK)

    # ── Column widths ──────────────────────────────────────────────────────────
    W_IDX = 8    # "Chunk" / "#0000"
    W_VAL = 11   # "  dim[n]  " / " +0.02341 "

    def h_sep(left: str, mid: str, right: str, fill: str) -> str:
        return (
            left
            + fill * W_IDX
            + (mid + fill * W_VAL) * sample_dims
            + right
        )

    def row(idx_val: str, dim_vals: list[str]) -> str:
        cells = "│ " + f"{idx_val:<{W_IDX - 2}}" + " "
        for v in dim_vals:
            cells += "│" + f"{v:^{W_VAL}}"
        cells += "│"
        return cells

    # ── Header ────────────────────────────────────────────────────────────────
    logger.info("  " + h_sep("┌", "┬", "┐", "─"))
    logger.info("  " + row("Chunk", [f"dim[{i}]" for i in range(sample_dims)]))
    logger.info("  " + h_sep("├", "┼", "┤", "─"))

    # ── Data rows ─────────────────────────────────────────────────────────────
    for i, vec in enumerate(vectors[:show_n]):
        dim_strs = [f"{vec[d]:+.5f}" for d in range(sample_dims)]
        logger.info("  " + row(f"#{i:04d}", dim_strs))

    if total_chunks > show_n:
        logger.info(
            "  " + row("…", [f"… +{total_chunks - show_n} more" if d == 0 else "…"
                              for d in range(sample_dims)])
        )

    # ── Footer ────────────────────────────────────────────────────────────────
    logger.info("  " + h_sep("└", "┴", "┘", "─"))
    logger.info(BLANK)

    # ── How similarity search works ───────────────────────────────────────────
    all_vals = [x for v in vectors for x in v]

    logger.info("  HOW CHROMA FINDS THE BEST MATCHING CHUNKS")
    logger.info("  " + "·" * (WIDTH - 4))
    logger.info(BLANK)
    logger.info("  Every chunk above is stored as a vector of %d floats.", vector_dim)
    logger.info("  When you ask a question, it is embedded into the same space.")
    logger.info(BLANK)
    logger.info("  Chroma compares the question vector (Q) against every stored")
    logger.info("  chunk vector (C) using a simple dot product:")
    logger.info(BLANK)
    logger.info("    cos(Q, C)  =  Q · C")
    logger.info("               =  Q[0]×C[0] + Q[1]×C[1] + … + Q[1535]×C[1535]")
    logger.info(BLANK)
    logger.info("  Score range:   -1.0  →  opposite meaning  (worst)")
    logger.info("                  0.0  →  unrelated")
    logger.info("                 +1.0  →  identical meaning  (best match)")
    logger.info(BLANK)
    logger.info("  Value range in your vectors:  min = %+.5f   max = %+.5f",
                min(all_vals), max(all_vals))
    logger.info("  " + "·" * (WIDTH - 4))
    logger.info(BLANK)


def log_chroma_stored(
    logger: logging.Logger,
    collection_name: str,
    persist_dir: str,
    num_docs: int,
    collection=None,        # chromadb.Collection — passed in to query stored rows
    peek_ids: list[str] | None = None,
) -> None:
    """
    Section 4 — what was persisted in Chroma, including a peek inside the DB.

    When `peek_ids` is set (the UUIDs from the current `collection.add` call),
    only those rows are fetched for the table — otherwise a bare `collection.get()`
    would list the whole collection and the "Source File" column could show
    unrelated documents uploaded earlier.
    """
    abs_dir = os.path.abspath(persist_dir)

    existing_files: list[str] = []
    try:
        existing_files = [f for f in os.listdir(abs_dir) if not f.startswith(".")]
    except FileNotFoundError:
        pass

    logger.info(SINGLE_LINE)
    logger.info("  STEP 4 / 4  ·  CHROMA STORAGE")
    logger.info(SINGLE_LINE)
    logger.info("  %-24s %s", "Collection :",        collection_name)
    logger.info("  %-24s %s", "Persist Dir :",       persist_dir)
    logger.info("  %-24s %s", "Absolute Path :",     abs_dir)
    logger.info("  %-24s %d", "Docs Stored :",       num_docs)
    logger.info("  %-24s %d", "Total in Collection :", collection.count() if collection else num_docs)
    if existing_files:
        logger.info("  %-24s %s", "DB Files Present :",  ", ".join(sorted(existing_files)))
    logger.info("  %-24s %s", "Status :",            "✓  Successfully persisted to disk")
    logger.info(BLANK)

    # ── Peek inside: rows from this run only (peek_ids), or whole collection ───
    if collection is None:
        return

    try:
        if peek_ids:
            result = collection.get(
                ids=peek_ids,
                include=["documents", "metadatas", "embeddings"],
            )
        else:
            result = collection.get(include=["documents", "metadatas", "embeddings"])
    except Exception:
        return

    ids        = result.get("ids") or []
    documents  = result.get("documents") or []
    metadatas  = result.get("metadatas") or []
    raw_emb    = result.get("embeddings")
    embeddings = raw_emb if raw_emb is not None else []

    if not ids:
        return

    def _chunk_order_key(row: int) -> int:
        if row >= len(metadatas):
            return row
        v = metadatas[row].get("chunk_index", row)
        try:
            return int(v)
        except (TypeError, ValueError):
            return row

    order = sorted(range(len(ids)), key=_chunk_order_key)
    ids        = [ids[i] for i in order]
    documents  = [documents[i] for i in order]
    metadatas  = [metadatas[i] for i in order]
    embeddings = [embeddings[i] for i in order] if embeddings else []

    if peek_ids:
        logger.info(
            "  WHAT IS STORED INSIDE CHROMA  —  This upload only (%d new row%s)",
            len(ids),
            "" if len(ids) == 1 else "s",
        )
    else:
        logger.info("  WHAT IS STORED INSIDE CHROMA  —  Entire collection (%d row%s)", len(ids), "" if len(ids) == 1 else "s")
    logger.info("  " + "·" * (WIDTH - 4))
    logger.info(BLANK)
    logger.info(
        "  Each row = 1 chunk.  "
        "Columns: ID (short) · source file · chunk # · text preview · embedding peek"
    )
    logger.info(BLANK)

    # ── Column widths ─────────────────────────────────────────────────────────
    W_ID      = 8     # first 8 chars of UUID
    W_SRC     = 20    # source filename
    W_IDX     = 7     # chunk_index
    W_TEXT    = 24    # text preview
    W_EMB     = 26    # embedding peek  e.g. [+0.023, -0.089, +0.042 …]

    sep_top = "  ┌" + "─"*W_ID +"┬"+"─"*W_SRC+"┬"+"─"*W_IDX+"┬"+"─"*W_TEXT+"┬"+"─"*W_EMB+"┐"
    sep_mid = "  ├" + "─"*W_ID +"┼"+"─"*W_SRC+"┼"+"─"*W_IDX+"┼"+"─"*W_TEXT+"┼"+"─"*W_EMB+"┤"
    sep_bot = "  └" + "─"*W_ID +"┴"+"─"*W_SRC+"┴"+"─"*W_IDX+"┴"+"─"*W_TEXT+"┴"+"─"*W_EMB+"┘"

    def tbl_row(id_: str, src: str, idx: str, text: str, emb: str) -> str:
        return (
            "  │"
            + f" {id_:<{W_ID - 1}}"  + "│"
            + f" {src:<{W_SRC - 1}}" + "│"
            + f" {idx:^{W_IDX - 1}}" + "│"
            + f" {text:<{W_TEXT - 1}}"+ "│"
            + f" {emb:<{W_EMB - 1}}" + "│"
        )

    logger.info(sep_top)
    logger.info(tbl_row("ID", "Source File", "Chunk#", "Text Preview", "Embedding Peek"))
    logger.info(sep_mid)

    max_rows = 10
    for i, row_id in enumerate(ids[:max_rows]):
        short_id  = row_id[:W_ID - 1] if row_id else "?"
        src       = (metadatas[i].get("source", "?") if i < len(metadatas) else "?")
        src       = src[: W_SRC - 2] + "…" if len(src) > W_SRC - 2 else src
        chunk_idx = str(metadatas[i].get("chunk_index", "?")) if i < len(metadatas) else "?"
        text_raw  = (documents[i] or "") if i < len(documents) else ""
        text_prev = text_raw[:W_TEXT - 2].replace("\n", " ").strip()
        if len(text_raw) > W_TEXT - 2:
            text_prev += "…"

        if i < len(embeddings) and embeddings[i] is not None:
            vec      = list(embeddings[i])
            emb_peek = f"[{vec[0]:+.3f}, {vec[1]:+.3f}, {vec[2]:+.3f}, …]"
        else:
            emb_peek = "(not returned)"

        logger.info(tbl_row(short_id, src, chunk_idx, text_prev, emb_peek))

    if len(ids) > max_rows:
        logger.info(tbl_row("…", "…", "…", f"… {len(ids)-max_rows} more rows", "…"))

    logger.info(sep_bot)
    logger.info(BLANK)
    logger.info("  Legend:")
    logger.info("    ID           →  first 8 chars of the UUID assigned at storage time")
    logger.info("    Source File  →  original PDF filename from metadata")
    logger.info("    Chunk#       →  position of this chunk inside the document (0-based)")
    logger.info("    Text Preview →  first ~22 chars of the stored chunk text")
    logger.info("    Embedding    →  first 3 of 1536 float values stored in Chroma")
    logger.info("  " + "·" * (WIDTH - 4))
    logger.info(BLANK)


def log_pipeline_end(
    logger: logging.Logger,
    filename: str,
    num_chunks: int,
    start_time: float,
) -> None:
    """Print the closing banner with elapsed time."""
    elapsed = time.monotonic() - start_time
    logger.info(DOUBLE_LINE)
    logger.info(
        "  PIPELINE COMPLETE  ·  %d chunks indexed from '%s'  in %.2fs",
        num_chunks, filename, elapsed,
    )
    logger.info("  Finished : %s", datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
    logger.info(DOUBLE_LINE)
    logger.info(BLANK)


def log_pipeline_error(
    logger: logging.Logger,
    step: str,
    error: Exception,
    start_time: float,
) -> None:
    """Print an error banner so failures are obvious in the log."""
    elapsed = time.monotonic() - start_time
    logger.info(BLANK)
    logger.info("  ✗  PIPELINE FAILED at step: %s", step)
    logger.info("  Error   : %s", error)
    logger.info("  Elapsed : %.2fs", elapsed)
    logger.info(DOUBLE_LINE)
    logger.info(BLANK)
