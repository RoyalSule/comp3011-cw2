import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from crawler import Crawler, BASE_URL, POLITENESS
from indexer import Indexer, INDEX_PATH
from search import SearchEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

HELP = """
Commands:
  build          Crawl the site and save the index
  load           Load a saved index from disk
  print <word>   Show the index entry for a word
  find <terms>   Find pages containing all given terms
  help           Show this message
  quit           Exit
"""

def do_build(indexer):
    print(f"Crawling {BASE_URL} (politeness: {POLITENESS}s)...")
    print("This will take a few minutes.")
    pages = Crawler(BASE_URL, POLITENESS).crawl()
    print(f"\nCrawled {len(pages)} pages. Building index...")
    indexer.build(pages)
    print(f"Done — {len(indexer.index)} unique words.")
    print(f"Saving to {INDEX_PATH}...")
    indexer.save()
    print("Saved.")

def do_load(indexer):
    try:
        indexer.load()
        print(f"Loaded — {len(indexer.index)} unique words.")
    except FileNotFoundError as e:
        print(f"Error: {e}")

def do_print(args, engine):
    if not args.strip():
        print("Usage: print <word>")
        return
    print(engine.print_word(args.strip()))

def do_find(args, engine):
    if not args.strip():
        print("Usage: find <term(s)>")
        return
    print(engine.find_pages(args.strip()))

def main():
    print("=" * 50)
    print("  COMP3011 Search Engine")
    print("=" * 50)
    print("Type 'help' for commands.")

    indexer = Indexer()
    engine = SearchEngine(indexer)

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not raw:
            continue

        cmd, _, args = raw.partition(" ")
        cmd = cmd.lower()

        if cmd == "build":
            do_build(indexer)
        elif cmd == "load":
            do_load(indexer)
        elif cmd == "print":
            if not indexer.index:
                print("Index is empty — run 'build' or 'load' first.")
            else:
                do_print(args, engine)
        elif cmd == "find":
            if not indexer.index:
                print("Index is empty — run 'build' or 'load' first.")
            else:
                do_find(args, engine)
        elif cmd in ("help", "?"):
            print(HELP)
        elif cmd in ("quit", "exit", "q"):
            print("Bye!")
            break
        else:
            print(f"Unknown command '{cmd}'. Type 'help' for options.")

if __name__ == "__main__":
    main()