" ==============================
" Basic Settings
" ==============================
set number              " show absolute line number
set relativenumber      " show relative numbers
set cursorline          " highlight current line
set termguicolors       " enable true color support (if terminal supports it)
syntax on               " enable syntax highlighting

" Tabs and indentation
set expandtab           " use spaces instead of tabs
set shiftwidth=2        " number of spaces to use for each indent
set tabstop=2           " number of spaces per tab
set smartindent         " auto-indent new lines

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