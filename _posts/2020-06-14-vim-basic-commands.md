---
layout: single
title: Vim basic commands
date: 2020-06-14 08:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - vim
permalink: "2020/06/14/vim-basic-command"
---

Cheat sheet
[https://vim.rtorr.com/](https://vim.rtorr.com/)

# Vim's Automatic Marks

` `` ` Position before the last jump within current file
`‘.` Location of last change
`‘^` Location of last insertion
`‘[` Start of last change or yank
`‘]` End of last change or yank
`‘<` Start of last visual selection
`‘>` End of last visual selection

# Changing mode

- Insert mode: `i`
- Replace mode: `R`
- Visual mode: `v`
- Line visual mode: `V`
- Block mode: `<C-v>` or `<C-V>`
- Command line mode: `:`

# Movement

- Basic movement: `hjkl` (left, down, up, right)
- Words: `w` (next word), `b` (beginning of word), `e` (end of word)
- Lines: `0` (beginning of line), `^` or `_` (first non-blank character), `$` (end of line)
- Screen: `H` (top of screen), `M` (middle of screen), `L` (bottom of screen)
- Scroll: `Ctrl-u` (up), `Ctrl-d` (down)
- File: `gg` (beginning of file), `G` (end of file)
- Line numbers: `:{number}<CR>` or `{number}G` (line {number})
- Misc: `%` (corresponding item)
- Find: `f{character}`, `t{character}`, `F{character}`, `T{character}`
  - find/to forward/backward {character} on the current line
  - `,` / `;` for navigating matches
- Search: `/{regex}`, `n` / `N` for navigating matches

# Edits

- `i` enter Insert mode
  - but for manipulating/deleting text, want to use something more than backspace
- `o` / `O` insert line below / above
- `d{motion}` delete {motion}
  - e.g. `dw` is delete word, `d$` is delete to end of line, `d0` is delete to beginning of line
- `c{motion}` change {motion}
  - e.g. `cw`is change word
  - like `d{motion}` followed by `i`
- `x` delete character (equal do `dl`)
- `s` substitute character (equal to `xi`)
- Visual mode `+` manipulation
  - select text, `d` to delete it or `c` to change it
- `u` to undo, `<C-r>` to redo
- `y` to copy / “yank” (some other commands like d also copy)
- `p` to paste
- Lots more to learn: e.g. `~` flips the case of a character
- `dG` will delete all lines until end of file.

# Count

- `3w` move 3 words forward
- `5j` move 5 lines down
- `7dw` delete 7 words

# Modifiers

You can use modifiers to change the meaning of a noun. Some modifiers are `i`, which means “inner” or “inside”, and `a`, which means “around”.

- `ci(` change the contents inside the current pair of parentheses
- `ci[` change the contents inside the current pair of square brackets
- `da'` delete a single-quoted string, including the surrounding single quotes
- `yiw` copy the current word

# Shell
Open shell from vim
- `:shell` open shell window
- `:ter[minal]` will open shell in a separated window(Neovim)

# Etc

- To turn off highlighting until the next search:
  `:noh`

- Or turn off highlighting completely:
  `set nohlsearch`

- Search replace in an interactive mode

  - adding the flag `c` in command prompt

  ```
  :%s/foo/bar/gc
  ```

- Indent multiple lines
  select lines with visual mode then type `>`

- Repeat last changes
  The `.` command repeats the last change made in normal mode.

  - `dw` can be repeated

  The `@:` command repeats the last command-line change

  - `:s/old/new/` can be repeated

- Replacing a word with a copied word

  - `yiw` -> move cursor to another location -> `ciw<C-r>0<Esc>`: replacing a word with a copied word.
  - we can repeat with `.` command

- Search the current word

  - `*` to search the word
  - `#` to search the word in backward direction

- Adding double quotes for selected text with a visual mode

  - If vim support the surround, select text with a visual mode then press `S"`
  - surround mode, `:set surround`

- Display searching a result in the middle of screen

  - after search, type `zz` will display in the middle of screen
  - `:set scrolloff=10` will always have 10 lines before and after.
  - `:set so=10` is shortcut
  - [https://vim.fandom.com/wiki/Make_search_results_appear_in_the_middle_of_the_screen](https://vim.fandom.com/wiki/Make_search_results_appear_in_the_middle_of_the_screen)

- Copy in a different buffer

  - `"ayy`: copy the current line in buffer a.
  - `"ap`: paste the contents in a buffer a at the cursor.

- Add indentation from the current line until the end of the file

  - `>G`

- Show search history
  - `q\`

- Scroll off 8 lines
 - `set scrolloff=8`

- Do not lose the yanked buffer on visual mode
 - `vnoremap <leader>p "_dP`

- Always copy into system clipboard
 - `vnoremap <leader>y "+y`

- Moving selected text up/down
 - `vnoremap J :m '>+1<CR>gv=gv`
 - `vnoremap K :m '<-2<CR>gv=gv`