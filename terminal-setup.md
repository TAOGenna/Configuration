# Terminal Setup

## Terminal Emulator

- **Ghostty** — GPU-accelerated terminal with tabs at the top (`gtk-tabs-location = top`), otherwise running defaults for clean font rendering and performance.

## Shell — Zsh

### Custom Prompt

Two-line prompt with:
- Line 1: cyan box-drawing characters (`╭─`/`╰─`), bold blue directory path, magenta git branch with nerd font icon
- Line 2: green arrow on success, red on failure (`❯`)
- Right side: dimmed clock

### Plugins

- **zsh-autosuggestions** — inline gray ghost text as you type (`fg=8`), accept with `Ctrl+E`
- **zsh-syntax-highlighting** — live command coloring

### Completion

- Arrow-key menu selection
- Case-insensitive matching
- `LS_COLORS`-colored results
- Yellow-formatted descriptions, red warnings for no matches

### History

- 10,000 lines, ignore duplicates, ignore space-prefixed commands, shared across sessions, no beep

## Modern CLI Replacements

| Tool    | Replaces | Aliases                          |
|---------|----------|----------------------------------|
| **eza** | `ls`     | `ls`, `ll`, `la`, `tree` (icons, git status, color) |
| **bat** | `cat`    | `cat` (plain), `catn` (with line numbers/headers)    |

## Fuzzy Finder — fzf

- **Catppuccin Mocha** color scheme (pinks, purples, muted backgrounds)
- Rounded borders, margin and padding
- Shell key-bindings and completion enabled

## Navigation

- **zoxide** — smart `cd` that learns frequent directories (aliased to `cd`)

## Environment

- **direnv** — auto-loads `.envrc` per project

## Vim

- Relative + absolute line numbers
- Cursor line highlight (custom dark background `#2a2a2a`)
- True color support, syntax highlighting
- `desert` colorscheme
- `jk` mapped to escape
- Ruler and showcmd enabled
- 2-space indentation with spaces

## Color Theme

The overall palette is **Catppuccin Mocha**, visible in the fzf config and complemented by the prompt colors.
