# Terminal setup: Ghostty + herdr

Reproduce this terminal environment on a new macOS machine. Written for Claude Code to
execute. Source machine: macOS 26 (Darwin 25.6), Apple Silicon, Ghostty 1.3.1, herdr 0.8.2.

---

## Success criteria

Deterministic. Do not report done until all pass:

1. `ghostty +validate-config` → exit 0
2. `/Applications/Ghostty.app/Contents/MacOS/ghostty +show-config | grep -c '^keybind'` → **93**
   (93 = Ghostty's stock count. Any other number means keybinds were overridden — that is a bug, see §2.)
3. `herdr config check` → `config: ok`
4. In herdr: `ctrl+f` `d` splits a pane; `ctrl+f` `t` prompts for a tab name.
5. In a bare Ghostty window (no herdr): `cmd+d` splits Ghostty, `cmd+t` opens a Ghostty tab.

Criteria 4 and 5 must **both** hold. If satisfying one breaks the other, the design was
misread — re-read §2 before changing anything.

---

## 1. The design in one line

**⌘ addresses Ghostty. `ctrl+f` addresses herdr. Same letters, different modifier.**

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
`ctrl+b` because this machine's keyboard is an HHKB Professional Hybrid (Control sits where
Caps Lock normally is, so `ctrl+f` is a home-row roll).

---

## 2. Do NOT do these

Each was tried on the source machine and rejected for a specific, reproducible reason.
A fresh agent will be tempted by all three.

**Do not remap `cmd+*` in Ghostty to herdr byte sequences.** e.g.
`keybind = super+d=text:\x06v`. This works — Ghostty ships the same trick in its own
defaults (`super+arrow_right=text:\x05`) — but it fires **unconditionally**. Ghostty cannot
detect whether herdr is running, so in any bare Ghostty window `cmd+d` types a stray `v` and
`cmd+t` types a stray `c`. Only safe if *every* Ghostty window is a herdr client
(`command = herdr`), which is not the case here.

**Do not `unbind` the `cmd+*` keys in Ghostty.** herdr *can* receive `cmd+d` natively — it
negotiates the kitty keyboard protocol (`ESC[>7u`, flags 1+2+4), under which Super is
encodable, and all 17 chords were verified to fire. But `unbind` is global: `cmd+t` then
stops opening a Ghostty tab **everywhere**, becoming a silent no-op outside herdr. Rejected
because bare Ghostty windows are used daily here.

**Do not set `CARGO_TARGET_DIR` inside a Claude scratchpad.** On Linux hosts `/tmp` is
frequently a tmpfs (RAM). Rust debug artifacts there consumed 12 GB of RAM on the dev VM and
wedged the box. Point cargo at real disk.

---

## 3. Ghostty

**Install:** download from <https://ghostty.org> (the source machine did this — it is not a
Homebrew cask there), or `brew install --cask ghostty`. Either is fine.

**Fonts: nothing to install.** Ghostty bundles JetBrains Mono. `font-family = JetBrains Mono`
resolves with no font file on disk — verified with
`ghostty +show-face --string="Ag" --font-family="JetBrains Mono"`.

**Layout:** configs are kept as named variants with `config` as a symlink, so themes can be
swapped by re-pointing the link.

```bash
mkdir -p ~/.config/ghostty
# write config.mocha (below), then:
ln -sfn config.mocha ~/.config/ghostty/config
```

### `~/.config/ghostty/config.mocha`

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

**There are no `keybind` lines, and that is deliberate.** See §2.

---

## 4. herdr

**Install** — pin the version; remote attach prefers a client/server version match:

```bash
mkdir -p ~/.local/bin
curl -fsSL https://github.com/herdrdev/herdr/releases/download/v0.8.2/herdr-macos-aarch64 \
  -o ~/.local/bin/herdr
chmod +x ~/.local/bin/herdr
# assets: herdr-macos-aarch64 | herdr-macos-x86_64 | herdr-linux-x86_64 | herdr-linux-aarch64
```

Ensure `~/.local/bin` is on `PATH`. Alternative: `curl -fsSL https://herdr.dev/install.sh | sh`
(installs latest, not pinned).

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

### Why each non-obvious line exists

- `workspace_picker` / `close_workspace` are **relocated**, not invented. herdr's defaults for
  them are `prefix+w` and `prefix+shift+d`, which the Ghostty-mnemonic bindings claim.
  herdr emits **no warning** on such a collision — it silently picks one. Always relocate
  explicitly.
- `prompt_new_*_name = true`: herdr defaults both to off, so new spaces are labeled with the
  cwd basename. Launch from `~` and every space is called `~`, indistinguishable. The space
  name is the only thing that makes the sidebar readable.
- `window_title`: puts the focused space and the pane's terminal title into the Ghostty tab
  bar. Claude Code's `/rename` sets the pane's terminal title (OSC 2), so a rename there flows
  to the Ghostty tab automatically. Without this the title is `{hostname}: {workspace}`.
- `agent_panel_sort`: **herdr writes this itself** when the `grouped` toggle is used in the UI.
  The config file is shared between you and herdr — edit it in place, never overwrite wholesale,
  or you will silently eat herdr's own settings.

---

## 5. Verification gates

Run in order. Stop at the first failure.

> `ghostty` is on `PATH` only inside a shell Ghostty itself spawned — it injects
> `/Applications/Ghostty.app/Contents/MacOS`, and no shell rc file does. From any other
> terminal use the full path `/Applications/Ghostty.app/Contents/MacOS/ghostty`.

```bash
# Gate 1 - configs parse
ghostty +validate-config; echo "exit=$?"                        # expect exit=0
herdr config check                                              # expect: config: ok

# Gate 2 - Ghostty keybinds untouched (93 = stock)
/Applications/Ghostty.app/Contents/MacOS/ghostty +show-config | grep -c '^keybind'
/Applications/Ghostty.app/Contents/MacOS/ghostty +list-keybinds | grep -E 'super\+(d|t|w)='
#   expect: super+w=close_surface / super+t=new_tab / super+d=new_split:right

# Gate 3 - no byte-injection bridge crept in (see §2)
/Applications/Ghostty.app/Contents/MacOS/ghostty +show-config | grep -c 'text:.*x06'   # expect 0
```

**Gate 4 — by hand**, both must hold:
- Run `herdr`, press `ctrl+f` `d` → splits. `ctrl+f` `t` → prompts for a name.
- Open a bare Ghostty tab (`cmd+t`), press `cmd+d` → Ghostty splits, no stray characters.

---

## 6. Optional: remote hosts

herdr's remote mode runs a thin local client against a herdr **server on the remote host**;
`--remote-keybindings local` is the default, so local keybindings apply. Spaces belong to
whichever server you attach to — local and remote never merge into one sidebar.

```bash
herdr --remote <ssh-host>
```

Requirements on the remote host: same herdr version on `PATH` (interactive runs offer to
install; non-interactive runs fail rather than modify the host), and reachable via plain `ssh`.

**Copy `config.toml` to the remote host too.** `--remote-keybindings local` covers `[keys]`
only — `[ui]`, `[theme]` and `[terminal]` render server-side and come from the remote's own
config. The copy will drift; resync with
`scp ~/.config/herdr/config.toml <host>:~/.config/herdr/config.toml`.

### The SSH port-forward trap

If the host's SSH config has `LocalForward` entries, herdr's attach binds them — and it uses a
**private per-attach control socket**, so a plain `ssh <host>` cannot share the connection and
fails with `Address already in use` / `Could not request local forwarding`. Give herdr a
forward-free alias:

```
Host myhost
    HostName real.host.name
    User me
    LocalForward 3000 localhost:3000
    # ... more forwards

# herdr remote attach only. Deliberately carries no LocalForwards so it never
# fights the interactive session for ports.
Host myhost-her
    HostName real.host.name
    User me
```

Then `herdr --remote myhost-her` coexists with `ssh myhost`.
Ad-hoc escape hatch: `ssh -o ClearAllForwardings=yes myhost`.

---

## 7. Behaviours that look like bugs but are not

- **Multiple clients attach to one session and mirror each other**, and the session **resizes
  to the smallest attached client** (measured: 200×50 + 90×24 → session became 64×23).
  Detach with `ctrl+f` `q` before working from a smaller terminal.
- **Extra Ghostty tabs running `herdr` do not give you extra workspaces.** They all attach to
  the `default` session. Use *spaces* (`ctrl+f` `shift+n`) to separate work; use
  `herdr --session <name>` only for genuinely independent instances.
- **Rename prompts pre-fill with the current name.** Press `ctrl+u` to clear first, or you get
  `1yago` instead of `yago`.
- **`ctrl+f` is swallowed inside every pane** (vim page-down, zsh `forward-char`). Press it
  twice to send a literal one.
- **herdr themes cannot clash with Ghostty's palette.** Pane contents are forwarded as palette
  *indices* (`ESC[38;5;1m`), which Ghostty resolves; a herdr theme only paints its own chrome
  in true-color RGB. Default `catppuccin` (`#1e1e2e` base) already matches this Ghostty config
  exactly. `[theme] name = "terminal"` makes herdr query the host's real colors instead of
  matching by coincidence.
- **Image paste behaves differently on remote.** Locally `ctrl+v` passes through to the pane
  app. Under `herdr --remote`, herdr intercepts it (`remote_image_paste = "ctrl+v"`), copies
  the image to a temp file on the remote host and inserts the *path*. Set it to `""` to
  disable.

---

## 8. Reference

| | |
|---|---|
| Ghostty config | `~/.config/ghostty/config` → symlink → `config.mocha` |
| herdr config | `~/.config/herdr/config.toml` |
| herdr binary | `~/.local/bin/herdr` |
| herdr logs | `~/.config/herdr/herdr-{server,client}.log` |
| all herdr options | `herdr --default-config` |
| all Ghostty options | `ghostty +show-config --default --docs` |
| reload herdr | `herdr server reload-config` |
| reload Ghostty | `cmd+shift+,` |
| sessions | `herdr session list / attach <name> / stop <name>` |
