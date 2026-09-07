# Terminal setup — full spec

Everything needed to rebuild this terminal environment on a fresh macOS machine. Written to be
handed to an agent and executed top to bottom.

**Source machine:** macOS 26.6.2 (Darwin 25.6), Apple Silicon (arm64), zsh 5.9.
**Versions pinned at capture time:** Ghostty 1.3.1 · herdr 0.8.2 · Powerlevel10k (brew HEAD) ·
tmux 3.5a · Neovim 0.11.1 · node 24.10.0 · rustc 1.95.0 · go 1.25.5 · python 3.11.9 (pyenv).

Not covered, deliberately: SSH hosts/keys/config, and the contents of any credential store.

---

## 0. The stack in one picture

```
┌─ Ghostty 1.3.1 ──────────────────────────────────────────────┐  window, font, palette, ⌘ keys
│ ┌─ herdr 0.8.2 ────────────────────────────────────────────┐ │  multiplexer, ctrl+f keys
│ │ ┌─ zsh ────────────────────────────────────────────────┐ │ │  history, completion, plugins
│ │ │  Powerlevel10k  ← ~/.zsh/color/* recolours it        │ │ │  prompt
│ │ │  fzf · fzf-tab · zoxide · direnv · eza · bat · delta │ │ │  tools, all Catppuccin-keyed
│ │ └──────────────────────────────────────────────────────┘ │ │
│ └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

One colour identity — **Catppuccin Mocha** — is declared once in `~/.zsh/color/palette.zsh` and
propagated to fzf, fzf-tab, eza, LS_COLORS, less, grep, zsh-syntax-highlighting, bat and the
prompt. Ghostty's `palette =` lines are the same 16 colours at the terminal level. Changing
flavour is one command (`flavor aurora`), not 12 config edits.

tmux is installed and configured but is **not** part of the daily path — herdr replaced it.
Alacritty likewise: config still on disk, superseded by Ghostty. Both documented at the end for
completeness; skip them if you want the minimum.

---

## 1. Success criteria

Deterministic. Do not report done until all pass:

| # | Check | Expected |
|---|---|---|
| 1 | `ghostty +validate-config; echo $?` | `0` |
| 2 | `ghostty +show-config \| grep -c '^keybind'` | `93` (stock; any other number = keybinds were overridden, see §3.2) |
| 3 | `herdr config check` | `config: ok` |
| 4 | `exec zsh` then `colortest` | 16 visually distinct swatches, `flavor=mocha style=tinted term=xterm-ghostty colorterm=truecolor` |
| 5 | `echo $LS_COLORS \| head -c 40` | non-empty (if empty, completion menus and fzf-tab go monochrome) |
| 6 | in herdr: `ctrl+f` `d` splits · `ctrl+f` `t` prompts for a tab name | both |
| 7 | in a bare Ghostty window: `cmd+d` splits · `cmd+t` opens a tab, **no stray characters typed** | both |

6 and 7 must **both** hold. If satisfying one breaks the other, the design was misread — re-read §3.2.

---

## 2. Bootstrap order

Order matters: Homebrew before `.zprofile` is sourced, pyenv before the first `exec zsh`,
zoxide's init last inside `.zshrc`.

```bash
# 1. Xcode CLI tools + Homebrew
xcode-select --install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Taps
brew tap oven-sh/bun
brew tap withgraphite/tap
brew tap encoredev/tap

# 3. Formulae (§9 explains what each one is for)
brew install \
  automake azure-cli bat colima direnv docker docker-buildx docker-compose eza fd ffmpeg \
  flyctl fzf gcc gh gifsicle git git-delta git-lfs glow go hugo k6 lazygit libmagic libpq \
  libtool neovim node openjdk@11 openjdk@17 pipx poppler powerlevel10k protobuf pyenv \
  python@3.11 python@3.12 render ripgrep sshpass syncthing temporal tilt tmux unar uv \
  zoxide zsh-autosuggestions zsh-syntax-highlighting

# 4. Casks
brew install --cask font-meslo-lg-nerd-font visual-studio-code

# 5. Ghostty — NOT from brew on the source machine; either is fine
#    https://ghostty.org  (or: brew install --cask ghostty)

# 6. fzf-tab (git clone, not a brew formula)
git clone --depth 1 https://github.com/Aloxaf/fzf-tab ~/.zsh/fzf-tab

# 7. herdr — pin the version; remote attach prefers a client/server match
mkdir -p ~/.local/bin
curl -fsSL https://github.com/herdrdev/herdr/releases/download/v0.8.2/herdr-macos-aarch64 \
  -o ~/.local/bin/herdr && chmod +x ~/.local/bin/herdr
#   assets: herdr-macos-aarch64 | herdr-macos-x86_64 | herdr-linux-x86_64 | herdr-linux-aarch64
#   unpinned alternative: curl -fsSL https://herdr.dev/install.sh | sh

# 8. Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 9. Node globals
npm i -g @anthropic-ai/claude-code @openai/codex @northflank/cli bun prettier typescript vibegroup

# 10. Python via pyenv
pyenv install 3.11.9 && pyenv global 3.11.9

# 11. Write every config file in §3–§10, then:
exec zsh
```

---

## 3. Ghostty

### 3.1 Layout

Configs are kept as named flavour variants with `config` as a **symlink**, so the whole palette
swaps by re-pointing the link (the `flavor` shell function in §5.4 does this):

```bash
mkdir -p ~/.config/ghostty
# write config.mocha and config.aurora (below), then:
ln -sfn config.mocha ~/.config/ghostty/config
```

**Fonts: nothing to install for Ghostty.** It bundles JetBrains Mono; `font-family = JetBrains Mono`
resolves with no font file on disk — verify with
`ghostty +show-face --string="Ag" --font-family="JetBrains Mono"`. The MesloLGS Nerd Font cask is
for Powerlevel10k's glyphs (and for Alacritty, if you resurrect it), not for Ghostty's text.

`~/Library/Application Support/com.mitchellh.ghostty/config` also exists on the source machine but
contains only four `cmd+ctrl+arrow` pane-navigation binds that **duplicate Ghostty's own defaults**
(`super+ctrl+arrow_left=goto_split:left`, …). Effective keybind count is 93 either way. It is a
no-op — do not recreate it.

### 3.2 Do NOT do these

Each was tried on the source machine and rejected for a specific, reproducible reason. A fresh
agent will be tempted by all three.

**Do not remap `cmd+*` in Ghostty to herdr byte sequences** (e.g. `keybind = super+d=text:\x06v`).
It works — Ghostty ships the same trick in its own defaults — but fires **unconditionally**.
Ghostty cannot detect whether herdr is running, so in a bare Ghostty window `cmd+d` types a stray
`v` and `cmd+t` types a stray `c`. Only safe if *every* Ghostty window is a herdr client
(`command = herdr`), which is not the case here.

**Do not `unbind` the `cmd+*` keys in Ghostty.** herdr *can* receive `cmd+d` natively — it
negotiates the kitty keyboard protocol (`ESC[>7u`, flags 1+2+4), under which Super is encodable,
and all 17 chords were verified to fire. But `unbind` is global: `cmd+t` then stops opening a
Ghostty tab **everywhere**, becoming a silent no-op outside herdr. Rejected because bare Ghostty
windows are used daily here.

**Do not raise `minimum-contrast` to 4.5.** See the NOTE inside the config below.

### 3.3 `~/.config/ghostty/config.mocha` — the active flavour

```
# --- Font ---
font-family = JetBrains Mono
font-size = 15
font-feature = -calt, -liga

# --- Cursor ---
cursor-style = block
cursor-style-blink = true
cursor-color = #f5e0dc

# --- Window / Glass look ---
background-opacity = 1
# background-opacity = 0.75
background-blur = false
# background-blur = macos-glass-clear
macos-titlebar-style = transparent
window-padding-x = 8
window-padding-y = 4
window-save-state = always
unfocused-split-opacity = 0.7
mouse-hide-while-typing = true

# --- Readability ---
# NOTE: 4.5 clamps every dim colour (ANSI 0/8 can never reach 4.5 against a dark
# background by definition) so Ghostty rewrites them toward white and the palette
# flattens. 1.1 only rescues colours that would be invisible on the background.
bold-is-bright = true
minimum-contrast = 1.1

# --- Catppuccin Mocha, brights lifted so 16 slots are 16 colours ---
background = #1e1e2e
foreground = #cdd6f4

palette = 0=#585b70
palette = 1=#f38ba8
palette = 2=#a6e3a1
palette = 3=#f9e2af
palette = 4=#89b4fa
palette = 5=#f5c2e7
palette = 6=#94e2d5
palette = 7=#bac2de
palette = 8=#6c7086
palette = 9=#f9b8ca
palette = 10=#cbefc8
palette = 11=#fdf3de
palette = 12=#b9d3fd
palette = 13=#fceef8
palette = 14=#bbeee5
palette = 15=#e4e8f5

selection-foreground = #cdd6f4
selection-background = #45475a

# --- Mouse ---
# Claude Code's TUI turns on ?1000/?1002/?1003 mouse tracking, so it swallows every
# click and drag: no text selection, no cmd+click on links. `never` reserves shift
# for the terminal no matter what the program asks for, so shift+drag selects and
# cmd+shift+click opens links.
mouse-shift-capture = never

# --- Clipboard ---
# OSC 52 is the ONLY way a TUI over SSH can copy, so `deny` broke copying in the VM
# and `ask` put a confirmation dialog in front of every single copy. Tradeoff of
# `allow`: any program in any pane, local or remote, can silently overwrite the Mac
# clipboard.
clipboard-write = allow
```

**There are no `keybind` lines, and that is deliberate.** See §3.2.

### 3.4 `~/.config/ghostty/config.aurora` — alternate flavour

Same file with a different 16-colour palette and cursor colour. Switch with `flavor aurora`
(§5.4), which re-points the symlink *and* re-keys the whole shell colour layer to match.

```
# --- Font ---
font-family = JetBrains Mono
font-size = 15
font-feature = -calt, -liga

# --- Cursor ---
cursor-style = block
cursor-style-blink = true
cursor-color = #ee5d43

# --- Window / Glass look ---
background-opacity = 1
# background-opacity = 0.75
background-blur = false
# background-blur = macos-glass-clear
macos-titlebar-style = transparent
window-padding-x = 8
window-padding-y = 4
window-save-state = always
unfocused-split-opacity = 0.7
mouse-hide-while-typing = true

# --- Readability ---
# NOTE: 4.5 clamps every dim colour (ANSI 0/8 can never reach 4.5 against a dark
# background by definition) so Ghostty rewrites them toward white and the palette
# flattens. 1.1 only rescues colours that would be invisible on the background.
bold-is-bright = true
minimum-contrast = 1.1

# --- Aurora, repaired: 16 distinct hues, none below the contrast floor ---
background = #23262e
foreground = #dfe3ec

palette = 0=#3f4450
palette = 1=#ff3d71
palette = 2=#8fd46d
palette = 3=#ffe66d
palette = 4=#5aa9ff
palette = 5=#ff6ad5
palette = 6=#03d6b8
palette = 7=#c6ccdb
palette = 8=#6d7484
palette = 9=#ff7aa2
palette = 10=#b5f08f
palette = 11=#fff4a3
palette = 12=#8ec7ff
palette = 13=#ffa3e6
palette = 14=#5cf2dd
palette = 15=#e8ebf2

selection-foreground = #e8ebf2
selection-background = #333846

# --- Mouse ---
# Claude Code's TUI turns on ?1000/?1002/?1003 mouse tracking, so it swallows every
# click and drag: no text selection, no cmd+click on links. `never` reserves shift
# for the terminal no matter what the program asks for, so shift+drag selects and
# cmd+shift+click opens links.
mouse-shift-capture = never

# --- Clipboard ---
# OSC 52 is the ONLY way a TUI over SSH can copy, so `deny` broke copying in the VM
# and `ask` put a confirmation dialog in front of every single copy. Tradeoff of
# `allow`: any program in any pane, local or remote, can silently overwrite the Mac
# clipboard.
clipboard-write = allow
```

---

## 4. herdr

**The design in one line: ⌘ addresses Ghostty. `ctrl+f` addresses herdr. Same letters, different modifier.**

| Action | Ghostty (bare terminal) | herdr |
|---|---|---|
| split right | `cmd+d` | `ctrl+f` `d` |
| split down | `cmd+shift+d` | `ctrl+f` `shift+d` |
| new tab | `cmd+t` | `ctrl+f` `t` |
| close | `cmd+w` | `ctrl+f` `w` |
| move between panes | `cmd+ctrl+←↓↑→` | `ctrl+f` `←↓↑→` (or `h/j/k/l`) |
| switch tab | `cmd+1…9` | `ctrl+f` `1…9` |
| font zoom | `cmd+=` / `cmd+-` | same — Ghostty handles it inside herdr too |

Two layers, two key spaces, zero collisions. The prefix is `ctrl+f` rather than the default
`ctrl+b` because this machine's keyboard is an **HHKB Professional Hybrid** — Control sits where
Caps Lock normally is (done in the board's DIP switches, so there is *no* `hidutil` remap and no
macOS Modifier Keys change to reproduce), making `ctrl+f` a home-row roll.

### `~/.config/herdr/config.toml`

```toml
onboarding = false

[keys]
# Rule: whatever you press with Cmd in Ghostty, press with the prefix in herdr.
prefix = "ctrl+f"

# cmd+d / cmd+shift+d  ->  prefix+d / prefix+shift+d
split_vertical   = ["prefix+d", "prefix+v"]
split_horizontal = ["prefix+shift+d", "prefix+minus"]

# cmd+t -> prefix+t
new_tab = ["prefix+t", "prefix+c"]

# cmd+w -> prefix+w
close_pane = ["prefix+w", "prefix+x"]

# cmd+ctrl+arrows -> prefix+arrows
focus_pane_left  = ["prefix+left",  "prefix+h"]
focus_pane_down  = ["prefix+down",  "prefix+j"]
focus_pane_up    = ["prefix+up",    "prefix+k"]
focus_pane_right = ["prefix+right", "prefix+l"]

# displaced by the two above; workspaces have no Ghostty equivalent to honor
workspace_picker = "prefix+space"
close_workspace  = "prefix+shift+q"

[ui]
prompt_new_tab_name = true
prompt_new_workspace_name = true
window_title = "{workspace} · {terminal_title}"
agent_panel_sort = "spaces"
```

Apply without restarting: `herdr server reload-config` (or `ctrl+f` `shift+r` inside herdr).

**Why each non-obvious line exists**

- `workspace_picker` / `close_workspace` are **relocated**, not invented. herdr's defaults for them
  are `prefix+w` and `prefix+shift+d`, which the Ghostty-mnemonic bindings claim. herdr emits **no
  warning** on such a collision — it silently picks one. Always relocate explicitly.
- `prompt_new_*_name = true`: herdr defaults both to off, so new spaces are labelled with the cwd
  basename. Launch from `~` and every space is called `~`, indistinguishable. The space name is the
  only thing that makes the sidebar readable.
- `window_title`: puts the focused space and the pane's terminal title into the Ghostty tab bar.
  Claude Code's `/rename` sets the pane's terminal title (OSC 2), so a rename there flows to the
  Ghostty tab automatically. Without this the title is `{hostname}: {workspace}`.
- `agent_panel_sort`: **herdr writes this itself** when the `grouped` toggle is used in the UI. The
  config file is shared between you and herdr — edit it in place, never overwrite wholesale, or you
  will silently eat herdr's own settings.

### Remote hosts

herdr's remote mode runs a thin local client against a herdr **server on the remote host**;
`--remote-keybindings local` is the default, so local keybindings apply. Spaces belong to whichever
server you attach to — local and remote never merge into one sidebar.

```bash
herdr --remote <host>
```

Requirements on the remote: same herdr version on `PATH` (interactive runs offer to install;
non-interactive runs fail rather than modify the host), reachable over plain ssh.

**Copy `config.toml` to the remote host too.** `--remote-keybindings local` covers `[keys]` only —
`[ui]`, `[theme]` and `[terminal]` render server-side and come from the remote's own config. The
copy will drift; resync it when you change the local one.

#### The SSH port-forward trap

If a host's ssh config carries `LocalForward` entries, herdr's attach binds them — and it uses a
**private per-attach control socket**, so a plain `ssh <host>` afterwards cannot share the
connection and fails with `Address already in use` / `Could not request local forwarding`. Give
herdr a forward-free alias:

```
Host example
    HostName real.host.name
    User me
    LocalForward 3000 localhost:3000
    # ... more forwards

# herdr remote attach only. Deliberately carries no LocalForwards so it never
# fights the interactive session for ports.
Host example-her
    HostName real.host.name
    User me
```

Then `herdr --remote example-her` coexists with `ssh example`.
Ad-hoc escape hatch: `ssh -o ClearAllForwardings=yes example`.

---

## 5. zsh

Three files plus a colour layer directory. Load order: `.zprofile` (login) → `.zshrc`
(interactive) → `~/.zsh/color/init.zsh` (last, so it wins) → `zoxide init` (very last, per
zoxide's own doctor check — put anything after it and zoxide prints a warning on every shell).

### 5.1 `~/.zprofile`

```bash
# ---- Homebrew ----
eval "$(/opt/homebrew/bin/brew shellenv)"

# ---- pyenv ----
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"

# ---- Java ----
export JAVA_HOME="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"

```

### 5.2 `~/.profile`

```bash
. "$HOME/.cargo/env"
```

### 5.3 `~/.zshrc`

The `NF_API_TOKEN` line below is **redacted** — it is a live Northflank admin token. See §11.

```bash
# Enable Powerlevel10k instant prompt (must be at the very top)
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# ---- Theme ----
source /opt/homebrew/share/powerlevel10k/powerlevel10k.zsh-theme
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

# ---- History ----
HISTFILE=$HOME/.zhistory
SAVEHIST=10000
HISTSIZE=10000
setopt share_history
setopt hist_expire_dups_first
setopt hist_ignore_dups
setopt hist_ignore_space
setopt hist_verify

# ---- Completion system ----
autoload -Uz compinit && compinit -C
zstyle ':completion:*' menu select                       # arrow-key menu
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' # case-insensitive
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"  # colored results
zstyle ':completion:*:descriptions' format '%F{yellow}-- %d --%f'
zstyle ':completion:*:warnings' format '%F{red}-- no matches --%f'

# ---- Keybindings ----
bindkey '^[[A' history-search-backward
bindkey '^[[B' history-search-forward

# ---- Zsh plugins ----
source /opt/homebrew/share/zsh-autosuggestions/zsh-autosuggestions.zsh
source /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# ---- fzf-tab (must be after compinit, before other plugins that wrap completion) ----
source ~/.zsh/fzf-tab/fzf-tab.plugin.zsh
zstyle ':fzf-tab:*' fzf-flags --color=bg+:#313244,bg:#1e1e2e,spinner:#f5e0dc,hl:#f38ba8,fg:#cdd6f4,header:#f38ba8,info:#cba6f7,pointer:#f5e0dc,marker:#b4befe,fg+:#cdd6f4,prompt:#cba6f7,hl+:#f38ba8,selected-bg:#45475a
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'eza --icons=always --color=always $realpath'
zstyle ':fzf-tab:complete:ls:*' fzf-preview 'eza --icons=always --color=always $realpath'

# ---- fzf ----
source <(fzf --zsh)

# Catppuccin Mocha theme for fzf
export FZF_DEFAULT_OPTS=" \
--color=bg+:#313244,bg:#1e1e2e,spinner:#f5e0dc,hl:#f38ba8 \
--color=fg:#cdd6f4,header:#f38ba8,info:#cba6f7,pointer:#f5e0dc \
--color=marker:#b4befe,fg+:#cdd6f4,prompt:#cba6f7,hl+:#f38ba8 \
--color=selected-bg:#45475a \
--border='rounded' --border-label='' --preview-window='border-rounded' \
--prompt='> ' --marker='>' --pointer='◆' \
--separator='─' --scrollbar='│'"

# Use fd for fzf file/directory sources (respects .gitignore)
export FZF_DEFAULT_COMMAND='fd --type f --hidden --follow --exclude .git'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_ALT_C_COMMAND='fd --type d --hidden --follow --exclude .git'

# Preview with bat (Ctrl+T) and eza (Alt+C)
export FZF_CTRL_T_OPTS="--preview 'bat --color=always --style=numbers --line-range=:500 {}'"
export FZF_ALT_C_OPTS="--preview 'eza --icons=always --color=always --tree --level=2 {}'"

# ---- bat ----
export BAT_THEME="Catppuccin Mocha"
alias cat="bat --plain"
alias catn="bat"

# ---- eza (better ls) ----
alias ls="eza --icons=always"
alias ll="eza --icons=always -l --git"
alias la="eza --icons=always -la --git"
alias tree="eza --icons=always --tree --level=3"

# ---- direnv ----
eval "$(direnv hook zsh)"

# ---- pyenv (interactive) ----
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# ---- Compiler ----
alias g++="g++-14"

export PATH="$HOME/.local/bin:$PATH"

# Added by Antigravity
export PATH="/Users/kenyi/.antigravity/antigravity/bin:$PATH"

# bun completions
[ -s "/Users/kenyi/.bun/_bun" ] && source "/Users/kenyi/.bun/_bun"

# Read-only psql into a Northflank-hosted staging DB. Creds are fetched live from the
# service's runtime environment, used, then unset — nothing is stored in this file.
yvstg() {
  local psql=/opt/homebrew/opt/libpq/bin/psql
  eval "$(northflank get service runtime-environment --project <project> --service <service> -o json 2>/dev/null \
    | python3 -c 'import sys,json,shlex
from urllib.parse import urlsplit
u=urlsplit(json.load(sys.stdin)["runtimeEnvironment"]["<DB_URL_ENV_VAR>"])
[print("export %s=%s"%(k,shlex.quote(str(v)))) for k,v in [("PGHOST",u.hostname),("PGPORT",u.port or 5432),("PGUSER",u.username),("PGDATABASE",u.path.lstrip("/")),("PGPASSWORD",u.password)]]')" || { echo "creds fetch failed"; return 1; }
  PGOPTIONS='-c default_transaction_read_only=on' "$psql" "$@"
  unset PGHOST PGPORT PGUSER PGDATABASE PGPASSWORD
}
export NF_API_TOKEN="…"   # REDACTED — keep real tokens out of this file, see §11

# ---- Colour layer (palette, prompt tint, LS_COLORS, plugin styles) ----
source ~/.zsh/color/init.zsh

# ---- Zoxide (must be last per zoxide's own doctor check) ----
eval "$(zoxide init zsh)"
alias cd="z"
```

Note the two `FZF_DEFAULT_OPTS` definitions: the one in `.zshrc` is hard-coded Mocha hex, and
`~/.zsh/color/tools.zsh` (sourced later) **overwrites it** with the flavour-keyed version. The
`.zshrc` copy is dead weight kept as a fallback if the colour layer is ever removed. Same for the
`BAT_THEME` export and the two `fzf-tab` zstyles.

### 5.4 The colour layer — `~/.zsh/color/`

Five files. `init.zsh` is the entry point (sourced from `.zshrc`); everything else reads the `$C`
associative array that `palette.zsh` defines.

```
~/.zsh/color/
├── .flavor            # one word: mocha | aurora        (state, written by `flavor`)
├── .style             # one word: tinted | rainbow | lean (state, written by `promptstyle`)
├── init.zsh           # entry point + the flavor/promptstyle/colortest commands
├── palette.zsh        # $C — the 16 named colours per flavour, and rgb()
├── prompt-tinted.zsh  # p10k recolour: one hue per segment
├── prompt-rainbow.zsh # p10k recolour: filled powerline segments (sources tinted first)
└── tools.zsh          # LS_COLORS, EZA_COLORS, syntax-highlighting, less, grep, fzf, bat
```

Three commands it gives you:

| Command | Effect |
|---|---|
| `flavor mocha\|aurora` | re-points the Ghostty symlink **and** re-keys every shell colour. Needs `⌘⇧,` in Ghostty + `exec zsh`. |
| `promptstyle tinted\|rainbow\|lean` | swaps prompt look, `exec zsh`s itself |
| `colortest` | prints all 16 ANSI slots fg + bg, plus the active flavour/style/TERM — the fastest way to tell whether a palette actually landed |

#### `~/.zsh/color/init.zsh`

```bash
# Colour layer. Sourced from the END of .zshrc so it wins over earlier defaults.
: ${ZSH_FLAVOR:=${$([[ -r ~/.zsh/color/.flavor ]] && <~/.zsh/color/.flavor):-mocha}}
: ${ZSH_PROMPT_STYLE:=${$([[ -r ~/.zsh/color/.style ]] && <~/.zsh/color/.style):-tinted}}
export ZSH_FLAVOR ZSH_PROMPT_STYLE

source ~/.zsh/color/palette.zsh
source ~/.zsh/color/tools.zsh
[[ $ZSH_PROMPT_STYLE == lean ]] || source ~/.zsh/color/prompt-$ZSH_PROMPT_STYLE.zsh
(( ! $+functions[p10k] )) || p10k reload

# flavor [mocha|aurora]  — swaps the Ghostty palette and everything keyed to it.
flavor() {
  [[ -n $1 ]] || { print -r -- "flavor: $ZSH_FLAVOR  (mocha|aurora)"; return; }
  [[ -f ~/.config/ghostty/config.$1 ]] || { print -ru2 -- "no ~/.config/ghostty/config.$1"; return 1 }
  print -r -- "$1" > ~/.zsh/color/.flavor
  ln -sfn config.$1 ~/.config/ghostty/config
  print -r -- "flavor -> $1.  Reload Ghostty config (⌘⇧,) then: exec zsh"
}

# promptstyle [tinted|rainbow|lean]
promptstyle() {
  [[ -n $1 ]] || { print -r -- "promptstyle: $ZSH_PROMPT_STYLE  (tinted|rainbow|lean)"; return; }
  [[ $1 == lean || -f ~/.zsh/color/prompt-$1.zsh ]] || { print -ru2 -- "unknown style: $1"; return 1 }
  print -r -- "$1" > ~/.zsh/color/.style
  ZSH_PROMPT_STYLE=$1 exec zsh
}

# colortest — the 16 ANSI slots, so you can see what a palette actually gives you.
colortest() {
  local i
  print -r -- "\n  ANSI 0-7 / 8-15 (fg then bg):"
  for i in {0..15}; do printf '\e[38;5;%dm %3d ●\e[0m' $i $i; (( (i+1) % 8 )) || print; done
  for i in {0..15}; do printf '\e[48;5;%dm     \e[0m' $i; (( (i+1) % 8 )) || print; done
  print -r -- "\n  flavor=$ZSH_FLAVOR  style=$ZSH_PROMPT_STYLE  term=$TERM  colorterm=$COLORTERM\n"
}
```

#### `~/.zsh/color/palette.zsh`

```bash
# Named colours for the active flavour. Everything else in ~/.zsh/color reads $C.
typeset -gA C

case "${ZSH_FLAVOR:-mocha}" in
  aurora)
    C=(
      base '#23262e'  surface '#333846' overlay '#7c8494' subtext '#a8b0c0' text '#dfe3ec'
      red  '#ff3d71'  maroon  '#ee5d43' peach   '#ff9d5c' yellow  '#ffe66d'
      green '#8fd46d' teal    '#03d6b8' sky     '#5cf2dd' sapphire '#5aa9ff'
      blue '#5aa9ff'  lavender '#a78bfa' mauve  '#c74ded' pink    '#ff6ad5'
    ) ;;
  *)
    C=(
      base '#1e1e2e'  surface '#45475a' overlay '#7f849c' subtext '#a6adc8' text '#cdd6f4'
      red  '#f38ba8'  maroon  '#eba0ac' peach   '#fab387' yellow  '#f9e2af'
      green '#a6e3a1' teal    '#94e2d5' sky     '#89dceb' sapphire '#74c7ec'
      blue '#89b4fa'  lavender '#b4befe' mauve  '#cba6f7' pink    '#f5c2e7'
    ) ;;
esac

# "#89b4fa" -> "137;180;250", for LS_COLORS / termcap escapes.
rgb() { local h=${1#\#}; print -r -- "$((16#${h:0:2}));$((16#${h:2:2}));$((16#${h:4:2}))"; }
```

#### `~/.zsh/color/tools.zsh`

```bash
# --- LS_COLORS -------------------------------------------------------------
# Was unset, so `eza` fell back to defaults and the `list-colors` zstyle in
# .zshrc expanded to nothing — completion menus and fzf-tab were monochrome.
local -a _ls
_ls=(
  "di=1;38;2;$(rgb $C[blue])"          # directory
  "ln=38;2;$(rgb $C[teal])"            # symlink
  "or=38;2;$(rgb $C[red])"             # broken symlink
  "ex=1;38;2;$(rgb $C[green])"         # executable
  "fi=38;2;$(rgb $C[text])"
  "pi=38;2;$(rgb $C[yellow])" "so=38;2;$(rgb $C[pink])"
  "bd=38;2;$(rgb $C[yellow])" "cd=38;2;$(rgb $C[yellow])"
  "su=38;2;$(rgb $C[base]);48;2;$(rgb $C[red])"
  "sg=38;2;$(rgb $C[base]);48;2;$(rgb $C[peach])"
  "tw=38;2;$(rgb $C[base]);48;2;$(rgb $C[green])"
  "ow=1;38;2;$(rgb $C[sapphire])"
)
local ext
for ext in tar tgz zip gz bz2 xz zst 7z rar dmg pkg;      do _ls+=("*.$ext=38;2;$(rgb $C[red])");      done
for ext in png jpg jpeg gif webp svg ico heic tiff;        do _ls+=("*.$ext=38;2;$(rgb $C[mauve])");    done
for ext in mp4 mov mkv webm mp3 wav flac m4a;              do _ls+=("*.$ext=38;2;$(rgb $C[pink])");     done
for ext in pdf md txt rst epub docx xlsx csv;              do _ls+=("*.$ext=38;2;$(rgb $C[subtext])");  done
for ext in json toml yaml yml ini conf cfg env lock;       do _ls+=("*.$ext=38;2;$(rgb $C[yellow])");   done
for ext in rs go py ts tsx js jsx rb java c cpp h sh zsh;  do _ls+=("*.$ext=38;2;$(rgb $C[sapphire])"); done
for ext in o pyc class d rlib bak swp tmp;                 do _ls+=("*.$ext=38;2;$(rgb $C[overlay])");  done
export LS_COLORS="${(j.:.)_ls}"

# eza's own columns (permissions, sizes, dates, git status) which LS_COLORS can't reach.
export EZA_COLORS="ur=38;2;$(rgb $C[yellow]):uw=38;2;$(rgb $C[red]):ux=38;2;$(rgb $C[green]):ue=38;2;$(rgb $C[green]):gr=38;2;$(rgb $C[yellow]):gw=38;2;$(rgb $C[red]):gx=38;2;$(rgb $C[green]):tr=38;2;$(rgb $C[yellow]):tw=38;2;$(rgb $C[red]):tx=38;2;$(rgb $C[green]):su=38;2;$(rgb $C[peach]):sf=38;2;$(rgb $C[peach]):xa=38;2;$(rgb $C[teal]):sn=38;2;$(rgb $C[green]):sb=38;2;$(rgb $C[teal]):uu=38;2;$(rgb $C[yellow]):un=38;2;$(rgb $C[overlay]):gu=38;2;$(rgb $C[yellow]):gn=38;2;$(rgb $C[overlay]):da=38;2;$(rgb $C[overlay]):ga=38;2;$(rgb $C[green]):gm=38;2;$(rgb $C[yellow]):gd=38;2;$(rgb $C[red]):gv=38;2;$(rgb $C[mauve]):gt=38;2;$(rgb $C[teal]):xx=38;2;$(rgb $C[surface]):in=38;2;$(rgb $C[overlay]):bl=38;2;$(rgb $C[blue]):hd=1;38;2;$(rgb $C[lavender]):lp=38;2;$(rgb $C[teal]):cc=38;2;$(rgb $C[red])"

# --- zsh plugins -----------------------------------------------------------
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE="fg=$C[overlay]"

typeset -gA ZSH_HIGHLIGHT_STYLES
ZSH_HIGHLIGHT_STYLES[unknown-token]="fg=$C[red],bold"
ZSH_HIGHLIGHT_STYLES[reserved-word]="fg=$C[mauve]"
ZSH_HIGHLIGHT_STYLES[alias]="fg=$C[green]"
ZSH_HIGHLIGHT_STYLES[suffix-alias]="fg=$C[green]"
ZSH_HIGHLIGHT_STYLES[builtin]="fg=$C[green]"
ZSH_HIGHLIGHT_STYLES[function]="fg=$C[blue]"
ZSH_HIGHLIGHT_STYLES[command]="fg=$C[green]"
ZSH_HIGHLIGHT_STYLES[precommand]="fg=$C[green],italic"
ZSH_HIGHLIGHT_STYLES[commandseparator]="fg=$C[pink]"
ZSH_HIGHLIGHT_STYLES[path]="fg=$C[text],underline"
ZSH_HIGHLIGHT_STYLES[globbing]="fg=$C[sky]"
ZSH_HIGHLIGHT_STYLES[single-hyphen-option]="fg=$C[yellow]"
ZSH_HIGHLIGHT_STYLES[double-hyphen-option]="fg=$C[yellow]"
ZSH_HIGHLIGHT_STYLES[back-quoted-argument]="fg=$C[mauve]"
ZSH_HIGHLIGHT_STYLES[single-quoted-argument]="fg=$C[yellow]"
ZSH_HIGHLIGHT_STYLES[double-quoted-argument]="fg=$C[yellow]"
ZSH_HIGHLIGHT_STYLES[dollar-quoted-argument]="fg=$C[yellow]"
ZSH_HIGHLIGHT_STYLES[dollar-double-quoted-argument]="fg=$C[sky]"
ZSH_HIGHLIGHT_STYLES[assign]="fg=$C[text]"
ZSH_HIGHLIGHT_STYLES[redirection]="fg=$C[pink]"
ZSH_HIGHLIGHT_STYLES[comment]="fg=$C[surface],italic"
ZSH_HIGHLIGHT_STYLES[named-fd]="fg=$C[text]"
ZSH_HIGHLIGHT_STYLES[arg0]="fg=$C[green]"

# --- pagers ----------------------------------------------------------------
export LESS='-R'
export LESS_TERMCAP_mb=$'\e[1;38;2;'"$(rgb $C[red])"'m'
export LESS_TERMCAP_md=$'\e[1;38;2;'"$(rgb $C[blue])"'m'
export LESS_TERMCAP_me=$'\e[0m'
export LESS_TERMCAP_so=$'\e[38;2;'"$(rgb $C[base])"';48;2;'"$(rgb $C[yellow])"'m'
export LESS_TERMCAP_se=$'\e[0m'
export LESS_TERMCAP_us=$'\e[4;38;2;'"$(rgb $C[teal])"'m'
export LESS_TERMCAP_ue=$'\e[0m'
export MANROFFOPT='-c'
export GREP_COLORS="mt=1;38;2;$(rgb $C[yellow]):fn=38;2;$(rgb $C[blue]):ln=38;2;$(rgb $C[overlay]):se=38;2;$(rgb $C[surface])"

# --- completion ------------------------------------------------------------
# Re-applied here because .zshrc runs this zstyle before LS_COLORS exists.
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*:*:*:*:descriptions' format "%F{$C[mauve]}%B%d%b%f"
zstyle ':completion:*:*:*:*:messages'     format "%F{$C[teal]}%d%f"
zstyle ':completion:*:*:*:*:warnings'     format "%F{$C[red]}no matches%f"
zstyle ':completion:*:*:*:*:corrections'  format "%F{$C[yellow]}%d (errors: %e)%f"

# --- fzf -------------------------------------------------------------------
export FZF_DEFAULT_OPTS="\
--color=bg+:$C[surface],bg:-1,spinner:$C[pink],hl:$C[red] \
--color=fg:$C[text],header:$C[red],info:$C[mauve],pointer:$C[pink] \
--color=marker:$C[lavender],fg+:$C[text],prompt:$C[mauve],hl+:$C[red] \
--color=border:$C[mauve],gutter:-1,query:$C[text] \
--border=rounded --preview-window=border-rounded \
--prompt='❯ ' --marker='▎' --pointer='◆' --separator='─' --scrollbar='│'"
zstyle ':fzf-tab:*' fzf-flags --color=bg+:$C[surface],bg:-1,spinner:$C[pink],hl:$C[red],fg:$C[text],header:$C[red],info:$C[mauve],pointer:$C[pink],marker:$C[lavender],fg+:$C[text],prompt:$C[mauve],hl+:$C[red],border:$C[mauve]

# --- bat -------------------------------------------------------------------
case "${ZSH_FLAVOR:-mocha}" in
  aurora) export BAT_THEME="Monokai Extended" ;;
  *)      export BAT_THEME="Catppuccin Mocha" ;;
esac
```

#### `~/.zsh/color/prompt-tinted.zsh`  (the active style)

```bash
# Lean p10k, but every segment gets its own hue instead of sharing four ANSI slots.

# Frame + gap were colour 0, which is bg-adjacent and got clamped to grey.
typeset -g POWERLEVEL9K_MULTILINE_FIRST_PROMPT_PREFIX="%F{$C[mauve]}╭─"
typeset -g POWERLEVEL9K_MULTILINE_NEWLINE_PROMPT_PREFIX="%F{$C[mauve]}├─"
typeset -g POWERLEVEL9K_MULTILINE_LAST_PROMPT_PREFIX="%F{$C[mauve]}╰─"
typeset -g POWERLEVEL9K_MULTILINE_FIRST_PROMPT_GAP_FOREGROUND=$C[surface]
typeset -g POWERLEVEL9K_MULTILINE_FIRST_PROMPT_GAP_CHAR='·'

typeset -g POWERLEVEL9K_OS_ICON_FOREGROUND=$C[pink]

# Parents dim, anchors bright: the path reads as depth instead of one flat string.
typeset -g POWERLEVEL9K_DIR_FOREGROUND=$C[blue]
typeset -g POWERLEVEL9K_DIR_SHORTENED_FOREGROUND=$C[overlay]
typeset -g POWERLEVEL9K_DIR_ANCHOR_FOREGROUND=$C[lavender]
typeset -g POWERLEVEL9K_DIR_ANCHOR_BOLD=true
typeset -g POWERLEVEL9K_DIR_NOT_WRITABLE_FOREGROUND=$C[red]

typeset -g POWERLEVEL9K_VCS_CLEAN_FOREGROUND=$C[green]
typeset -g POWERLEVEL9K_VCS_MODIFIED_FOREGROUND=$C[peach]
typeset -g POWERLEVEL9K_VCS_UNTRACKED_FOREGROUND=$C[teal]
typeset -g POWERLEVEL9K_VCS_CONFLICTED_FOREGROUND=$C[red]
typeset -g POWERLEVEL9K_VCS_LOADING_FOREGROUND=$C[overlay]
typeset -g POWERLEVEL9K_VCS_VISUAL_IDENTIFIER_COLOR=$C[green]

typeset -g POWERLEVEL9K_PROMPT_CHAR_OK_{VIINS,VICMD,VIVIS,VIOWR}_FOREGROUND=$C[green]
typeset -g POWERLEVEL9K_PROMPT_CHAR_ERROR_{VIINS,VICMD,VIVIS,VIOWR}_FOREGROUND=$C[red]

typeset -g POWERLEVEL9K_STATUS_ERROR_FOREGROUND=$C[red]
typeset -g POWERLEVEL9K_STATUS_ERROR_SIGNAL_FOREGROUND=$C[red]
typeset -g POWERLEVEL9K_STATUS_ERROR_PIPE_FOREGROUND=$C[red]
typeset -g POWERLEVEL9K_STATUS_OK_PIPE_FOREGROUND=$C[green]
typeset -g POWERLEVEL9K_COMMAND_EXECUTION_TIME_FOREGROUND=$C[yellow]
typeset -g POWERLEVEL9K_BACKGROUND_JOBS_FOREGROUND=$C[mauve]
typeset -g POWERLEVEL9K_DIRENV_FOREGROUND=$C[yellow]
typeset -g POWERLEVEL9K_TIME_FOREGROUND=$C[overlay]

typeset -g POWERLEVEL9K_RUST_VERSION_FOREGROUND=$C[peach]
typeset -g POWERLEVEL9K_NODE_VERSION_FOREGROUND=$C[green]
typeset -g POWERLEVEL9K_GO_VERSION_FOREGROUND=$C[sky]
typeset -g POWERLEVEL9K_JAVA_VERSION_FOREGROUND=$C[maroon]
typeset -g POWERLEVEL9K_PACKAGE_FOREGROUND=$C[teal]
typeset -g POWERLEVEL9K_{PYENV,VIRTUALENV,ANACONDA}_FOREGROUND=$C[yellow]
typeset -g POWERLEVEL9K_KUBECONTEXT_DEFAULT_FOREGROUND=$C[sapphire]
typeset -g POWERLEVEL9K_AWS_DEFAULT_FOREGROUND=$C[peach]
typeset -g POWERLEVEL9K_TERRAFORM_OTHER_FOREGROUND=$C[mauve]
typeset -g POWERLEVEL9K_CONTEXT_FOREGROUND=$C[subtext]

# Language versions only appear inside a matching project, so they read as
# "what am I standing in" rather than clutter.
typeset -g POWERLEVEL9K_{RUST,NODE,GO,JAVA}_VERSION_PROJECT_ONLY=true
typeset -g POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(
  status command_execution_time background_jobs direnv
  virtualenv pyenv rust_version node_version go_version java_version package
  kubecontext terraform aws azure gcloud context
  nix_shell vim_shell time newline
)
```

#### `~/.zsh/color/prompt-rainbow.zsh`

```bash
# Powerline style: filled segment backgrounds. Louder than tinted; same segments.
source ~/.zsh/color/prompt-tinted.zsh

typeset -g POWERLEVEL9K_BACKGROUND=$C[surface]
typeset -g POWERLEVEL9K_{LEFT,RIGHT}_SUBSEGMENT_SEPARATOR=''
typeset -g POWERLEVEL9K_LEFT_SEGMENT_SEPARATOR=''
typeset -g POWERLEVEL9K_RIGHT_SEGMENT_SEPARATOR=''
typeset -g POWERLEVEL9K_LEFT_PROMPT_LAST_SEGMENT_END_SYMBOL=''
typeset -g POWERLEVEL9K_RIGHT_PROMPT_FIRST_SEGMENT_START_SYMBOL=''
typeset -g POWERLEVEL9K_LEFT_PROMPT_FIRST_SEGMENT_START_SYMBOL=''
typeset -g POWERLEVEL9K_RIGHT_PROMPT_LAST_SEGMENT_END_SYMBOL=''
typeset -g POWERLEVEL9K_{LEFT,RIGHT}_{LEFT,RIGHT}_WHITESPACE=' '

typeset -g POWERLEVEL9K_OS_ICON_BACKGROUND=$C[mauve]
typeset -g POWERLEVEL9K_OS_ICON_FOREGROUND=$C[base]
typeset -g POWERLEVEL9K_DIR_BACKGROUND=$C[blue]
typeset -g POWERLEVEL9K_DIR_FOREGROUND=$C[base]
typeset -g POWERLEVEL9K_DIR_SHORTENED_FOREGROUND=$C[surface]
typeset -g POWERLEVEL9K_DIR_ANCHOR_FOREGROUND=$C[base]
typeset -g POWERLEVEL9K_VCS_CLEAN_BACKGROUND=$C[green]
typeset -g POWERLEVEL9K_VCS_MODIFIED_BACKGROUND=$C[peach]
typeset -g POWERLEVEL9K_VCS_UNTRACKED_BACKGROUND=$C[teal]
typeset -g POWERLEVEL9K_VCS_CONFLICTED_BACKGROUND=$C[red]
typeset -g POWERLEVEL9K_VCS_{CLEAN,MODIFIED,UNTRACKED,CONFLICTED}_FOREGROUND=$C[base]
typeset -g POWERLEVEL9K_STATUS_ERROR_BACKGROUND=$C[red]
typeset -g POWERLEVEL9K_STATUS_ERROR_FOREGROUND=$C[base]
typeset -g POWERLEVEL9K_COMMAND_EXECUTION_TIME_BACKGROUND=$C[yellow]
typeset -g POWERLEVEL9K_COMMAND_EXECUTION_TIME_FOREGROUND=$C[base]
typeset -g POWERLEVEL9K_TIME_BACKGROUND=$C[surface]
typeset -g POWERLEVEL9K_TIME_FOREGROUND=$C[subtext]
typeset -g POWERLEVEL9K_PROMPT_CHAR_BACKGROUND=
```

#### State files

```bash
print -r -- mocha  > ~/.zsh/color/.flavor
print -r -- tinted > ~/.zsh/color/.style
```

---

## 6. Prompt — Powerlevel10k

`~/.p10k.zsh` is 90 KB of wizard output, but it is **only 11 settings away from a file Homebrew
already ships**. Do not transcribe it; derive it.

```bash
cp /opt/homebrew/share/powerlevel10k/config/p10k-lean-8colors.zsh ~/.p10k.zsh
```

Then apply exactly these 11 deltas (verified by diff against the source machine's file):

| Line | From | To |
|---|---|---|
| `LEFT_PROMPT_ELEMENTS` | `# os_icon` (commented) | `os_icon` (enabled) |
| `RIGHT_PROMPT_ELEMENTS` | `# time` (commented) | `time` (enabled) |
| `POWERLEVEL9K_MODE` | `nerdfont-complete` | `nerdfont-v3` |
| `MULTILINE_FIRST_PROMPT_PREFIX` | empty | `'%0F╭─'` |
| `MULTILINE_NEWLINE_PROMPT_PREFIX` | empty | `'%0F├─'` |
| `MULTILINE_LAST_PROMPT_PREFIX` | empty | `'%0F╰─'` |
| `LEFT_PROMPT_FIRST_SEGMENT_START_SYMBOL` | empty | `' '` |
| `RULER_FOREGROUND` | `7` | `0` |
| `MULTILINE_FIRST_PROMPT_GAP_CHAR` | `' '` | `'·'` |
| `MULTILINE_FIRST_PROMPT_GAP_FOREGROUND` | `7` | `0` |
| `VCS_BRANCH_ICON` | empty | `' '` |
| `BATTERY_STAGES` | block-glyph array | `'\UF008E\UF007A…\UF0079'` (nerdfont battery ramp) |
| `TIME_FORMAT` | `'%D{%H:%M:%S}'` | `'%D{%I:%M:%S %p}'` (12h) |

Equivalent path if you'd rather not hand-edit: run `p10k configure` and answer —
*nerdfont-v3 + powerline · small icons · unicode · lean_8colors · 12h time · 2 lines · dotted ·
left frame · black-ornaments · sparse · many icons · concise · instant_prompt=verbose*.

Shape: **2 lines**, left = `os_icon  dir  git`, newline, `❯`. Right = status, duration, jobs,
direnv, virtualenv/pyenv, language versions (project-only), kube/aws/terraform, clock.

`~/.zsh/color/prompt-tinted.zsh` then **overrides** the frame colours, gap colour and every segment
foreground with true-colour hex — the `%0F` / `7` / `0` ANSI values above are what you see only if
the colour layer is missing. Both are kept so the prompt degrades gracefully.

Instant prompt is `verbose` and hot reload is disabled — the block at the very top of `.zshrc`
must stay first, before anything that prints.

---

## 7. CLI tool configuration

### `~/.gitconfig`

```ini
[user]
	email = <your-email>
[url "git@github.com:"]
	insteadOf = https://github.com/
[filter "lfs"]
	clean = git-lfs clean -- %f
	smudge = git-lfs smudge -- %f
	process = git-lfs filter-process
	required = true
[core]
	pager = delta
[interactive]
	diffFilter = delta --color-only
[delta]
	navigate = true
	side-by-side = true
	line-numbers = true
	syntax-theme = Catppuccin Mocha
[merge]
	conflictstyle = diff3
[diff]
	colorMoved = default
```

Pager is **delta**, side-by-side, with the same Catppuccin Mocha syntax theme as bat.
`url.insteadOf` rewrites every `https://github.com/` clone to SSH. `conflictstyle = diff3` shows
the merge base — worth keeping.

### `~/.config/git/ignore` (global gitignore)

```
**/.claude/settings.local.json
```

### bat

The theme is not built in — the `.tmTheme` file has to be present, then the cache rebuilt:

```bash
mkdir -p "$(bat --config-dir)/themes"
curl -fsSL -o "$(bat --config-dir)/themes/Catppuccin Mocha.tmTheme" \
  https://raw.githubusercontent.com/catppuccin/bat/main/themes/Catppuccin%20Mocha.tmTheme
bat cache --build          # required — without it BAT_THEME silently falls back
```

`BAT_THEME` is exported from `tools.zsh` (Mocha) / (`Monokai Extended` for aurora, since no
Catppuccin equivalent exists there). Aliases: `cat` → `bat --plain`, `catn` → `bat` (with the
frame and line numbers).

### gh

```yaml
git_protocol: https
aliases:
    co: pr checkout
```

Everything else is gh's default. `gh auth login` on the new machine.

### Others, all configured inline in `.zshrc` / `tools.zsh`

| Tool | Config lives in | What it does here |
|---|---|---|
| **fzf** | `tools.zsh` (`FZF_DEFAULT_OPTS`) | flavour-keyed colours, rounded borders, `❯` prompt |
| **fzf-tab** | `.zshrc` + `tools.zsh` | replaces the zsh completion menu with fzf; `eza` preview for `cd`/`ls` |
| **fd** | `.zshrc` (`FZF_*_COMMAND`) | backs fzf's file/dir sources, respects `.gitignore` |
| **eza** | `tools.zsh` (`EZA_COLORS`) | `ls`/`ll`/`la`/`tree` aliases, icons always on |
| **zoxide** | `.zshrc`, last line | `cd` is aliased to `z` |
| **direnv** | `.zshrc` (`direnv hook zsh`) | per-project env; p10k shows a segment when active |
| **pyenv** | `.zprofile` (path) + `.zshrc` (init) | both halves are required |
| **less / grep** | `tools.zsh` (`LESS_TERMCAP_*`, `GREP_COLORS`) | coloured man pages and grep hits |

---

## 8. Claude Code

Installed twice on the source machine — the native install
(`~/.local/bin/claude` → `~/.local/share/claude/versions/…`, currently the live one) and the npm
global `@anthropic-ai/claude-code`. Pick **one** on the new machine; native is the current path.

`~/.claude/settings.json` — the terminal-relevant parts:

```json
{
  "statusLine": { "type": "command", "command": "bash /Users/<you>/.claude/statusline-command.sh" },
  "tui": "fullscreen",
  "theme": "dark",
  "effortLevel": "xhigh",
  "voice": { "enabled": true, "mode": "hold" },
  "skipDangerousModePermissionPrompt": true
}
```

Plugin marketplaces to re-add (`/plugin marketplace add …`): `claude-plugins-official` (superpowers,
vercel, frontend-design, mattpocock-skills), `cloudflare/skills`, `cathrynlavery/diagram-design`,
`DietrichGebert/ponytail`, `actionbook/rust-skills`, vibegroup from the local npm module path, plus
any private work marketplaces (re-add those from their own repos; not listed here).

The statusline script (`~/.claude/statusline-command.sh`, needs `jq`) mirrors the p10k prompt —
`user@host  dir (branch*) [ctx%] | model`, green/yellow git, cyan context percentage. Copy it; it's
in the "carry these files" list in §11.

---

## 9. Package inventory

Everything in `brew leaves` on the source machine, grouped by why it exists. The install command
in §2 has the flat list.

| Group | Formulae |
|---|---|
| **Terminal experience** | `powerlevel10k` `zsh-autosuggestions` `zsh-syntax-highlighting` `fzf` `fd` `ripgrep` `eza` `bat` `zoxide` `direnv` `glow` `tmux` `neovim` |
| **Git** | `git` `git-delta` `git-lfs` `gh` `lazygit` |
| **Languages / toolchains** | `node` `go` `pyenv` `python@3.11` `python@3.12` `uv` `pipx` `openjdk@11` `openjdk@17` `gcc` `automake` `libtool` `protobuf` |
| **Containers / infra** | `colima` `docker` `docker-buildx` `docker-compose` `tilt` `temporal` `k6` |
| **Cloud CLIs** | `azure-cli` `flyctl` `render` |
| **Media / misc** | `ffmpeg` `gifsicle` `poppler` `unar` `libmagic` `libpq` `hugo` `syncthing` `sshpass` |

Casks: `font-meslo-lg-nerd-font` `visual-studio-code` `alacritty`¹ `musescore`.
Taps: `oven-sh/bun` `withgraphite/tap` `encoredev/tap`.
npm globals: `@anthropic-ai/claude-code` `@openai/codex` `@northflank/cli` `bun` `prettier`
`typescript` `vibegroup` `corepack`.
uv tools: `yt-dlp`. cargo: `sea-orm-cli`.

¹ legacy — see §12.

---

## 10. Editors and tmux (secondary path)

### `~/.vimrc`

Plain vim, no plugin manager. Relative numbers, 2-space indent, `jk` → Esc, `desert` colourscheme
with a transparent-background override so the Ghostty palette shows through.

```vim
" ==============================
" Basic Settings
" ==============================
set number              " show absolute line number
set relativenumber      " show relative numbers
set cursorline          " highlight current line
set termguicolors       " enable true color support (if terminal supports it)
syntax on               " enable syntax highlighting
filetype plugin indent on  " enable filetype detection, plugins, and indent
" Treat Metal Shading Language as C++ (closest builtin match)
" Treat .mm as Objective-C++ (vim defaults it to nroff, which is wrong)
augroup metal_ft
  autocmd!
  autocmd BufRead,BufNewFile *.metal set filetype=cpp
  autocmd BufRead,BufNewFile *.mm    set filetype=objcpp
augroup END
set clipboard=unnamedplus
" Tabs and indentation
set expandtab           " use spaces instead of tabs
set shiftwidth=2        " number of spaces to use for each indent
set tabstop=2           " number of spaces per tab
set smartindent         " auto-indent new lines

set backspace=indent,eol,start
set softtabstop=2
" ==============================
" Key Mappings
" ==============================
" Map jk to escape insert mode quickly
inoremap jk <Esc>

" ==============================
" Colorscheme
" ==============================
colorscheme desert
" Other good built-in ones: peachpuff, evening, industry, slate

" ==============================
" Visual tweaks
" ==============================
highlight CursorLine cterm=NONE ctermbg=236 guibg=#2a2a2a
set ruler               " show line and column number
set showcmd             " show incomplete commands

" ==============================
" Transparent background (let terminal show through)
" ==============================
augroup transparent_bg
  autocmd!
  autocmd ColorScheme * hi Normal      ctermbg=NONE guibg=NONE
                    \ | hi NonText     ctermbg=NONE guibg=NONE
                    \ | hi LineNr      ctermbg=NONE guibg=NONE
                    \ | hi SignColumn  ctermbg=NONE guibg=NONE
                    \ | hi EndOfBuffer ctermbg=NONE guibg=NONE
augroup END
" Apply once now, since colorscheme was already set above
hi Normal      ctermbg=NONE guibg=NONE
hi NonText     ctermbg=NONE guibg=NONE
hi LineNr      ctermbg=NONE guibg=NONE
hi SignColumn  ctermbg=NONE guibg=NONE
hi EndOfBuffer ctermbg=NONE guibg=NONE

```

Neovim is installed (0.11.1) but has **no config on the source machine** — `~/.config/nvim` does
not exist. Nothing to reproduce.

### `~/.tmux.conf`

Not in the daily path — herdr replaced tmux — but the config is complete and worth carrying.
Prefix is `C-Space`. Requires TPM: `git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm`
then `prefix + I` inside tmux.

```
### ────────────────────────────────
###  Terminal and Input Behavior
### ────────────────────────────────

# Enable full 256-color and truecolor support.
set -g default-terminal "tmux-256color"
set -ag terminal-overrides ",xterm-256color:RGB"

# Enable extended keys so Shift+Enter etc. are passed correctly to apps.
set -s extended-keys on
set -as terminal-features 'xterm*:extkeys'

# Shorten the delay after pressing ESC (snappier Vim inside tmux).
set -sg escape-time 25


### ────────────────────────────────
###  Prefix Key (command trigger)
### ────────────────────────────────

# Prefix: Ctrl-Space (thumb-friendly, minimal pinky load).
set -g prefix C-Space
unbind C-b
bind C-Space send-prefix


### ────────────────────────────────
###  Pane Splitting and Navigation
### ────────────────────────────────

# Splits:
#   Prefix + | → vertical split
#   Prefix + - → horizontal split
bind | split-window -h
bind - split-window -v

# Navigate panes Vim-style (Prefix + h/j/k/l).
bind -r h select-pane -L
bind -r j select-pane -D
bind -r k select-pane -U
bind -r l select-pane -R

# Resize panes (Prefix + Shift + h/j/k/l).
# Lowercase = move, Uppercase = resize.
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5


### ────────────────────────────────
###  Mouse and Copy Mode
### ────────────────────────────────

# Disable mouse to preserve native terminal selection.
set -g mouse off

# Vim-style copy mode.
set-window-option -g mode-keys vi

# Enter copy mode: Prefix + [
# v → select | y → copy | q → exit
bind [ copy-mode
bind-key -T copy-mode-vi v send -X begin-selection
bind-key -T copy-mode-vi y send -X copy-selection


### ────────────────────────────────
###  Status Bar (minimal)
### ────────────────────────────────

set -g status-position bottom
set -g status-bg colour234
set -g status-fg colour137
set -g status-left ''
set -g status-right '#[fg=colour233,bg=colour241,bold] %d/%m #[fg=colour233,bg=colour245,bold] %H:%M:%S '
set -g status-right-length 50
set -g status-left-length 20


### ────────────────────────────────
###  Plugin Management (TPM)
### ────────────────────────────────

set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'christoomey/vim-tmux-navigator'
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'

set -g @resurrect-capture-pane-contents 'on'
set -g @continuum-restore 'on'

# TPM initialization (must be last).
run '~/.tmux/plugins/tpm/tpm'

```

---

## 11. Things a document cannot reproduce — carry these

**Secrets are stripped from this document and must stay stripped.** The source machine's real
`~/.zshrc` carries an API token inline; §5.3 shows it as a placeholder. Do not paste a real one
back in. On the new machine keep tokens out of the dotfile entirely — `op read`, Keychain via
`security find-generic-password -w`, or a `~/.zshenv.local` that is git-ignored.

Credential files that live on the source machine and are **not** transcribed here: `~/.config/vercel-token`,
`~/.config/posthog-key`, `~/.config/clipimg/token`, `~/.config/gh/hosts.yml`, `~/.northflank`,
`~/.azure`, `~/.fly`, `~/.render`, `~/.docker`. Re-authenticate each on the new machine rather
than copying.

**Personal scripts in `~/.local/bin`** — plain files, no upstream, copy them across:

| File | What it is |
|---|---|
| `clipimg-grab` | JXA script: macOS clipboard image → PNG on disk |
| `clipimg-serve` | serves that PNG over HTTP so a remote terminal can fetch it |
| `clipimg-tunnel` | the tunnel wrapper for the above |
| `~/.claude/statusline-command.sh` | Claude Code statusline (§8) |
| `mystery-shopper` | work binary, rebuilt from its own repo |

**Not worth copying:** `~/.zhistory` (unless you want the history), the `config.glass*` /
`config.catppuccin` Ghostty variants (superseded backups), `~/.config/alacritty` (§12),
`~/.p10k.zsh` itself (derive it, §6).

---

## 12. Behaviours that look like bugs but are not

**herdr**

- **Multiple clients attach to one session and mirror each other**, and the session **resizes to
  the smallest attached client** (measured: 200×50 + 90×24 → session became 64×23). Detach with
  `ctrl+f` `q` before working from a smaller terminal.
- **Extra Ghostty tabs running `herdr` do not give you extra workspaces.** They all attach to the
  `default` session. Use *spaces* (`ctrl+f` `shift+n`) to separate work; use `herdr --session <name>`
  only for genuinely independent instances.
- **Rename prompts pre-fill with the current name.** Press `ctrl+u` to clear first, or you get
  `1yago` instead of `yago`.
- **`ctrl+f` is swallowed inside every pane** (vim page-down, zsh `forward-char`). Press it twice to
  send a literal one.
- **herdr themes cannot clash with Ghostty's palette.** Pane contents are forwarded as palette
  *indices* (`ESC[38;5;1m`), which Ghostty resolves; a herdr theme only paints its own chrome in
  true-colour RGB. Default `catppuccin` (`#1e1e2e` base) already matches this Ghostty config
  exactly. `[theme] name = "terminal"` makes herdr query the host's real colours instead of matching
  by coincidence.
- **Image paste differs on remote.** Locally `ctrl+v` passes through to the pane app. Under
  `herdr --remote`, herdr intercepts it (`remote_image_paste = "ctrl+v"`), copies the image to a temp
  file on the remote host and inserts the *path*. Set it to `""` to disable.

**Ghostty**

- `ghostty` is on `PATH` **only inside a shell Ghostty itself spawned** — it injects
  `/Applications/Ghostty.app/Contents/MacOS`, and no rc file does. From any other terminal (or from
  an agent's shell) use the full path.
- `minimum-contrast = 4.5` **flattens the palette**. ANSI 0/8 can never reach 4.5 against a dark
  background by definition, so Ghostty rewrites every dim colour toward white. `1.1` only rescues
  colours that would be genuinely invisible.
- `mouse-shift-capture = never` is what makes selection work under Claude Code. Claude's TUI turns
  on `?1000/?1002/?1003` mouse tracking and swallows every click; `never` reserves shift for the
  terminal regardless, so `shift+drag` selects and `cmd+shift+click` opens links.
- `clipboard-write = allow` is a deliberate trade. `deny` breaks copying from any TUI over SSH
  (OSC 52 is the only channel it has); `ask` puts a dialog in front of every copy. The cost of
  `allow`: any program in any pane, local or remote, can silently overwrite the Mac clipboard.

**zsh**

- **`LS_COLORS` must be set before the `list-colors` zstyle is useful.** `.zshrc` sets that zstyle
  early, when `LS_COLORS` is still empty, which silently produced monochrome completion menus and
  fzf-tab. `tools.zsh` re-applies it after building `LS_COLORS` — that duplicate is load-bearing,
  do not "clean it up".
- **zoxide must be the last thing in `.zshrc`.** Anything after it triggers zoxide's doctor warning
  on every shell start. (`_ZO_DOCTOR=0` silences it, but fix the order instead.)
- `compinit -C` skips the security check for speed; the cache is `~/.zcompdump`. If completions go
  stale after a brew upgrade, `rm ~/.zcompdump && exec zsh`.

**Coding agents running in these panes**

- **Do not point `CARGO_TARGET_DIR` at a scratchpad or `/tmp`.** On Linux hosts `/tmp` is often a
  tmpfs (RAM). Rust debug artifacts there consumed 12 GB of RAM on a dev VM and wedged the box.
  Point cargo at real disk.

**Legacy on disk, safe to ignore**

- `~/.config/alacritty/` — the previous terminal (MesloLGS Nerd Font Mono 18pt, `coolnight` theme,
  0.7 opacity + blur). Superseded by Ghostty. The cask is still installed; drop it unless you want
  a fallback.
- `~/.config/ghostty/config.{glass,glass.bak,glass.bak2,glass.pre-aurora,catppuccin}` — iterations
  toward `config.mocha`. Do not carry them.
- `~/.tcshrc`, `~/.zsh_history` (725 bytes, superseded by `~/.zhistory`) — vestigial.

---

## 13. Reference

| | |
|---|---|
| Ghostty config | `~/.config/ghostty/config` → symlink → `config.mocha` |
| Ghostty binary (full path) | `/Applications/Ghostty.app/Contents/MacOS/ghostty` |
| all Ghostty options | `ghostty +show-config --default --docs` |
| reload Ghostty | `⌘⇧,` |
| herdr config | `~/.config/herdr/config.toml` |
| herdr binary | `~/.local/bin/herdr` |
| herdr logs | `~/.config/herdr/herdr-{server,client}.log` |
| all herdr options | `herdr --default-config` |
| reload herdr | `herdr server reload-config` or `ctrl+f` `shift+r` |
| herdr sessions | `herdr session list / attach <name> / stop <name>` |
| shell | `~/.zprofile`, `~/.zshrc`, `~/.zsh/color/*` |
| prompt | `~/.p10k.zsh` + `~/.zsh/color/prompt-tinted.zsh`; `p10k configure` to regenerate |
| flavour / style / diagnose | `flavor`, `promptstyle`, `colortest` |
| history | `~/.zhistory`, 10 000 lines, shared across sessions |
| `TERM` inside Ghostty | `xterm-ghostty`, `COLORTERM=truecolor` |
