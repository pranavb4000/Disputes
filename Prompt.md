Recreate a software project on this Mac exactly as it exists in a GitHub repository, using only the Chrome browser to read it. (git clone and zip download are blocked, so do not try them.)

SOURCE: https://github.com/pranavb4000/Disputes  (branch: main; I am signed in to GitHub in Chrome)
DESTINATION: ~/projects/Disputes  (create it; change nothing else on this Mac)

STEP 1 - FILE LIST
Open https://github.com/pranavb4000/Disputes/blob/main/MANIFEST.txt and click "Raw".
Every line not starting with # has the format:  <hash>  <size in bytes>  <file path>
This is the complete list of files to create. Save MANIFEST.txt itself to ~/projects/Disputes/MANIFEST.txt exactly.

STEP 2 - COPY THE CHECKER FIRST
Copy tools/verify_manifest.py (method below) before anything else.

STEP 3 - COPY EVERY FILE IN THE LIST
For each path in MANIFEST.txt:
- Open https://github.com/pranavb4000/Disputes/blob/main/<path> and click "Raw"
  (or open https://github.com/pranavb4000/Disputes/raw/main/<path> directly).
  If the Raw page is blocked, use the "Copy raw file" button on the file page.
  Never copy from the normal code view, because it contains line numbers.
- Write the content to ~/projects/Disputes/<path>, creating folders as needed.

COPY RULES - VERY IMPORTANT
- Copy byte-for-byte. Do NOT reformat, re-indent, fix, improve, complete, summarise, shorten, translate or add comments. Keep every space, blank line, quote style and trailing newline exactly as in the original.
- Use Unix (LF) line endings.
- Keep file names exactly, including case and names that start with a dot (.gitignore, .gitattributes, .env.example, .dockerignore, .gitkeep).
- Files whose size is 0 must be created as empty files.
- Long files (ARCHITECTURE.md, TECH_STACK.md, README.md, DEPENDENCIES.md, pubspec.lock) must be copied completely. Their byte size must equal the size in MANIFEST.txt.
- If you write files from the terminal, use a quoted heredoc (cat > "file" <<'DMS_EOF' ... DMS_EOF) so $, backticks and backslashes are not changed.
- SKIP binary files (.ttf and .png). They cannot be copied as text; just list them.
- Do NOT create a .env file. Do NOT create files that are not in MANIFEST.txt. Do NOT run git, docker, flutter or pip, and do not install anything.

STEP 4 - VERIFY AND FIX
Run:  cd ~/projects/Disputes && python3 tools/verify_manifest.py
It lists every file that is MISSING, DIFFERENT (with expected vs actual size) or has CRLF line endings.
Re-open each listed file on GitHub, copy it again exactly, and re-run the check.
Repeat until it prints "ALL TEXT FILES MATCH". The only acceptable leftovers are the 7 lines marked BINARY.

STEP 5 - REPORT
Tell me: how many files match, which binary files are still missing, and any file you could not open.