import os
import re
import mimetypes
import argparse

# Define ignore patterns
ignore_patterns = [
    r'.*\.git(ignore)?$',  # Ignore .git and .gitignore
    r'.*\.ipynb$',         # Ignore Jupyter notebook files
    r'^LICENSE$',          # Ignore LICENSE file
    r'\.env$',             # Ignore .env files
    r'__pycache__$',       # Ignore __pycache__ directories
    r'.*\.pyc$',           # Ignore .pyc files
    r'.*\.out$',           # Ignore output files
    r'test-results\.json$',# Ignore test results
    r'.*\.sum$'            # Ignore checksum files
    r'\.terraform\.lock\.hcl$',
    r'\.terraform*'
]

# Define a blacklist for files/folders never to consider
blacklist = [
    ".git",  # Entire .git folder
    "node_modules",  # Common for JavaScript projects
    "__pycache__"  # Common for Python projects
]

def should_ignore(name, path, patterns, blacklist):
    """
    Check if a file or folder should be ignored.
    - Matches ignore patterns (regex).
    - Enforces strict blacklist checking based on exact names or absolute paths.
    """
    # Match ignore patterns
    if any(re.match(pattern, name) or re.match(pattern, path) for pattern in patterns):
        return True

    # Enforce blacklist (check if path starts with any blacklisted folder)
    abs_path = os.path.abspath(path)
    for bl in blacklist:
        if os.path.basename(abs_path) == bl or abs_path.startswith(os.path.abspath(bl)):
            return True

    return False

def count_lines_or_get_type(filepath):
    """Count the number of lines in a file or return its type if unreadable."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except (UnicodeDecodeError, IsADirectoryError):
        # Get file type using mimetypes
        file_type, _ = mimetypes.guess_type(filepath)
        return file_type or "unknown file type"

def display_tree_structure(folder_path, ignore_patterns=None, prefix="", show_line_counts=False):
    """Recursively display folder structure with optional line counts."""
    if not os.path.isdir(folder_path):
        return 0  # Return total lines in folder

    items = os.listdir(folder_path)
    items.sort()

    # Filter out ignored items and blacklist
    items = [
        item for item in items
        if not should_ignore(item, os.path.join(folder_path, item), ignore_patterns or [], blacklist)
    ]

    pointers = ["├── "] * (len(items) - 1) + ["└── "]
    total_lines = 0

    for pointer, item in zip(pointers, items):
        path = os.path.join(folder_path, item)
        if os.path.isdir(path):
            print(prefix + pointer + item + "/")
            extension = "│   " if pointer == "├── " else "    "
            # Recurse into subdirectory
            total_lines += display_tree_structure(
                path, ignore_patterns, prefix=prefix + extension, show_line_counts=show_line_counts
            )
        else:
            line_info = ""
            if show_line_counts:
                line_count = count_lines_or_get_type(path)
                if isinstance(line_count, int):
                    line_info = f" ({line_count} lines)"
                    total_lines += line_count
                else:
                    line_info = f" ({line_count})"  # File type if not readable
            print(prefix + pointer + item + line_info)

    return total_lines

def print_file_contents(folder_path, ignore_patterns=None):
    """Print the contents of files, skipping those matching ignore patterns."""
    for root, dirs, files in os.walk(folder_path):
        # Filter out ignored directories and blacklist
        dirs[:] = [
            d for d in dirs
            if not should_ignore(d, os.path.join(root, d), ignore_patterns or [], blacklist)
        ]

        for filename in files:
            # Skip ignored files
            if should_ignore(filename, os.path.join(root, filename), ignore_patterns or [], blacklist):
                continue
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"{filepath}:\n{content}")
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Print file content from a directory",
        epilog="Example usage:\n"
               "  python script.py /path/to/directory\n"
               "  python script.py /path/to/directory --structure\n"
               "  python script.py /path/to/directory --structure-all\n"
               "  python script.py --help-only"
    )
    parser.add_argument("folder_path", type=str, nargs="?", help="Path to the directory to process")
    parser.add_argument(
        "--structure", action="store_true",
        help="Print the structure only, subject to ignore_patterns"
    )
    parser.add_argument(
        "--structure-all", action="store_true",
        help="Print the structure only, without applying ignore_patterns"
    )
    parser.add_argument(
        "--help-only", action="store_true",
        help="Display this help information"
    )
    args = parser.parse_args()

    if args.help_only:
        parser.print_help()
        exit(0)

    if not args.folder_path:
        print("Error: folder_path is required unless --help-only is used.")
        parser.print_help()
        exit(1)

    if args.structure and args.structure_all:
        print("Error: Cannot use --structure and --structure-all at the same time.")
        exit(1)

    if args.structure:
        print("Directory structure (subject to ignore_patterns):\n")
        total_lines = display_tree_structure(
            args.folder_path, ignore_patterns, show_line_counts=True
        )
        print(f"\nTotal lines in readable files: {total_lines}")
    elif args.structure_all:
        print("Directory structure (no ignore_patterns applied):\n")
        total_lines = display_tree_structure(
            args.folder_path, ignore_patterns=None, show_line_counts=True
        )
        print(f"\nTotal lines in readable files: {total_lines}")
    else:
        print("Directory structure (subject to ignore_patterns):\n")
        total_lines = display_tree_structure(
            args.folder_path, ignore_patterns, show_line_counts=True
        )
        print(f"\nTotal lines in readable files: {total_lines}")
        print("\nFile contents:\n")
        print_file_contents(args.folder_path, ignore_patterns)
