"""Look inside ONE booklet the way the pipeline sees it (native pypdf, level 1).
  python scripts/inspect_pdf.py data/full/booklets/2024_09_22_de.pdf                  # page table with quality flags
  python scripts/inspect_pdf.py data/full/booklets/2024_09_22_de.pdf --page 12         # print page 12 (1-based)
  python scripts/inspect_pdf.py data/full/booklets/2024_09_22_de.pdf --find "Bundesrat empfiehlt"
  python scripts/inspect_pdf.py data/full/booklets/2024_09_22_de.pdf --mode layout     # pypdf layout mode
  python scripts/inspect_pdf.py data/full/booklets/2024_09_22_de.pdf --bench           # plain vs layout speed
"""
import argparse
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pdf_loader import load_pages


def normalize(text: str) -> str:
    """Normalize text for case-insensitive phrase searching."""
    text = text.casefold()
    text = re.sub(r"\s+", " ", text)
    return text.replace("- ", "")

def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect PDF text extracted by src.pdf_loader.")
    parser.add_argument("pdf", help="Path to the PDF booklet")
    parser.add_argument( "--page",type=int,help="Print one page (1-based page number)",)
    parser.add_argument("--find", help="Find a phrase in the extracted pages",)
    parser.add_argument("--bench",action="store_true",help="Measure the time needed to load the PDF",)
    args = parser.parse_args()
    if args.page is not None and args.page < 1:
        parser.error("--page must be 1 or greater")
    if not os.path.isfile(args.pdf):
        parser.error(f"PDF file not found: {args.pdf}")
    start = time.perf_counter()
    pages = load_pages(args.pdf)
    elapsed = time.perf_counter() - start
    total_chars = sum(len(page) for page in pages)

    print(f"{args.pdf}: {len(pages)} pages, "f"{total_chars:,} characters "f"(roughly {total_chars // 4:,} tokens), "f"loaded in {elapsed:.2f}s")
    if args.bench:
        print("Note: this measures load_pages(), including any cache hit. ""It does not compare extraction modes.")
        return

    if args.page is not None:
        if args.page > len(pages):
            parser.error(f"Page {args.page} does not exist; "f"PDF has {len(pages)} pages")
        print(f"\n----- page {args.page} -----\n")
        print(pages[args.page - 1])
        return

    if args.find:
        query = normalize(args.find)
        hits = [i for i, page in enumerate(pages, start=1) if query in normalize(page)]
        print(f"'{args.find}' found on pages: {hits or 'NOWHERE'}")
        return

    print("\nPage  chars  words  flag        first 60 characters")
    for i, page in enumerate(pages, start=1):
        chars = len(page)
        words = len(page.split())
        flag = "EMPTY" if not page.strip() else ""
        preview = page[:60].replace("\n", " ")
        print(f"{i:>4}  {chars:>5}  {words:>5}  "f"{flag:<10}  {preview!r}")
    empty_pages = sum(not page.strip() for page in pages)
    print(f"\n{empty_pages} empty page(s).")
    print("EMPTY means no text was extracted; the page may be blank ""or may require OCR.")

if __name__ == "__main__":
    main()
