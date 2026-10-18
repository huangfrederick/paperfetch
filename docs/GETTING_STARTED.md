# Getting started with paperfetch

**No programming experience needed.** This is a step by step guide for new users, from downloading paperfetch to having PDFs of papers in a folder on
your computer.

- **Time:** about 15 minutes the first time, mostly waiting for downloads. After that,
  starting paperfetch takes under a minute.
- **You need:** a Mac or Windows computer, an internet connection, and about 1 GB of
  free disk space.
- **Optional:** a free OpenAlex account, which gets you access to their hosted PDFs ([Part 2](#getting-a-free-api-key-recommended)).
- **Using Linux?** See [Linux](#linux).


## Contents

1. [Words you'll see](#words-youll-see)
2. [Part 1: One-time setup](#part-1-one-time-setup)
3. [Part 2: Find and download papers](#part-2-find-and-download-papers)
4. [Part 3: Stopping, coming back and updating](#part-3-stopping-coming-back-and-updating)
5. [Part 4 (optional): Use paperfetch from the terminal](#part-4-optional-use-paperfetch-from-the-terminal)
6. [Troubleshooting](#troubleshooting)
7. [Getting help](#getting-help)
8. [Citing paperfetch](#citing-paperfetch)

## Words you'll see

| Word | What it means here |
|---|---|
| **Terminal** | A window where you type instructions for your computer instead of clicking on a user interface. On Windows it may be called *PowerShell* or *Windows Terminal*. You only need it for a few short commands. |
| **Command** | One line of text you paste into the terminal, then press **Enter** to run. |
| **Folder path** | A folder's full address, like `/Users/JohnDoe/Documents/paperfetch-main` (Mac) or `C:\Users\JaneDoe\Documents\paperfetch-main` (Windows). |
| **pixi** | A package management tool that sets up Python and everything paperfetch needs *inside the paperfetch folder*, without changing anything else on your computer. |
| **Notebook** | A document in your web browser that mixes instructions with small blocks of code, which you run by pressing a key. paperfetch comes with one. |
| **JupyterLab** | The program that shows the notebook in your browser. pixi installs it for you. |
| **API key** | A free, password-like code from OpenAlex that identifies you, so you get your own daily allowance of downloads from their repository. |
| **Open access** | Papers that the publisher or authors have made free to read, legally. paperfetch only downloads these. |

## Part 1: One-time setup

You only do this part once per computer.

### Step 1: Download paperfetch

1. Go to <https://github.com/huangfrederick/paperfetch>.
2. Click the green **Code** button, then **Download ZIP**.
3. Unzip it:
   - **Mac:** open your **Downloads** folder. If you see a folder named
     `paperfetch-main`, it's already unzipped. If you only see `paperfetch-main.zip`,
     double-click it.
   - **Windows:** open your **Downloads** folder, right-click `paperfetch-main.zip`,
     choose **Extract All…**, then **Extract**. 
4. Drag the `paperfetch-main` folder into your **Documents** folder. Your papers will
   be saved inside it, too.

<!-- SCREENSHOT: docs/images/download-zip.png | GitHub page with the green Code menu open, "Download ZIP" visible -->

**You should now have** a folder called `paperfetch-main` in Documents, containing
files like `README.md` and folders like `notebooks`.

### Step 2: Open a terminal in the paperfetch folder

The terminal has to be "in" the paperfetch folder, so it knows which project you mean. If you have an IDE such as VSCode, you can open the folder and terminal session directly from there.

**Mac**

1. Press **Cmd + Space**, type `Terminal`, and press **Enter**. A window with a
   blinking cursor opens.
2. Type `cd` followed by a **space**, but don't press Enter yet. (`cd` means
   "change directory", i.e. go to a folder.)
3. Drag the `paperfetch-main` folder from Finder into the terminal window. Its path
   appears after `cd `.
4. Press **Enter**.

**Windows 11**

1. Open the `paperfetch-main` folder in File Explorer.
2. Right-click an empty area inside the folder and choose **Open in Terminal**.

**Windows 10:** hold **Shift**, right-click an empty area inside the `paperfetch-main`
folder, and choose **Open PowerShell window here**.

<!-- SCREENSHOT: docs/images/terminal-open.png | terminal in the paperfetch-main folder, Mac and Windows side by side -->

**You should now see** a line ending in `paperfetch-main` followed by `%` (Mac) or
`>` (Windows), then a blinking cursor. This line is called the *prompt*: the terminal
is waiting for a command.

**How to run a command from this guide:** copy it from the grey box (on GitHub there's
a copy button in the box's top-right corner), click in the terminal, paste it
(**Cmd + V** on Mac; **Ctrl + V** or right-click on Windows), and press **Enter**.
While a command is working, the prompt disappears. When the prompt comes back, the
command is finished.

### Step 3: Install pixi

pixi sets up the right version of Python and every tool paperfetch needs. You install
it once per computer.

**Mac:** paste this and press Enter:

```bash
curl -fsSL https://pixi.sh/install.sh | sh
```

**Windows:** paste this and press Enter:

```powershell
powershell -ExecutionPolicy Bypass -c "irm -useb https://pixi.sh/install.ps1 | iex"
```

These are the official install commands from pixi's website, <https://pixi.sh>.

**Then close the terminal window completely, and open a new one in the paperfetch
folder (repeat [Step 2](#step-2-open-a-terminal-in-the-paperfetch-folder)).** A
terminal only notices newly installed programs when it starts.

Check that it worked:

```
pixi --version
```

✅ **You should now see** something like `pixi 0.82.0`. Any version number is fine.

### Step 4: Start the notebook

```
pixi run notebook
```

**The first time, this takes several minutes.** pixi downloads Python, JupyterLab and
the other things paperfetch needs (about 400 MB) into the paperfetch folder, and shows
progress messages while it works. Later starts take a few seconds.

When it's ready, your web browser opens **JupyterLab** showing the paperfetch notebook.

<!-- SCREENSHOT: docs/images/jupyterlab-quickstart.png | JupyterLab with quickstart.ipynb open at the top -->

✅ **You should now see** a browser tab with **paperfetch quickstart** at the top of
the page.

**Keep the terminal window open** while you use the notebook (minimizing it is fine).
The terminal runs JupyterLab behind the scenes, so closing it stops the notebook.

If no browser window opens, look in the terminal for a link starting with
`http://localhost:8888/lab?token=` and copy the whole link into your browser.

## Part 2: Find and download papers

The notebook explains each step as you go. In short:

1. Click the first grey box and press **Shift + Enter** to run it. Keep pressing
   **Shift + Enter** to move down one cell at a time.
2. **Step 1** asks for an API key ([see below](#getting-a-free-api-key-recommended)).
   Press **Enter** to skip it.
3. In **Step 2**, change the text between the quotation marks to your search, for
   example `"coral bleaching thermal tolerance"`. Then run that cell and every cell
   below it.
4. **Step 3** shows a numbered table of results. Click a title to read the paper online.
5. **Step 4:** keep `"all"`, or pick papers by their numbers from the table.
6. **Step 5** downloads the PDFs. **Step 6** writes `index.csv`, a list of which file
   is which paper.

<!-- SCREENSHOT: docs/images/results-table.png | the Step 3 results table -->

**Where are my papers?** In the `papers` folder inside `paperfetch-main`, for example
`Documents/paperfetch-main/papers`. Files are named by their OpenAlex ID, like
`W3082255212.pdf`. Open `index.csv` in Excel, Numbers or Google Sheets to see which
title belongs to which file.

### Getting a free API key (recommended)

Without a key, paperfetch still searches and downloads PDFs from publishers. With a
free key you also get **OpenAlex's own copies** of papers whose publisher link doesn't
work (about 100 per day), and your own daily allowance instead of one shared with
everyone on your network.

1. Go to <https://openalex.org/settings/api> and create a free account.
2. Copy your API key.
3. In the notebook, run Step 1 and paste the key into the box that appears. The box
   hides what you type. That's normal.

**Don't want to paste it every time?** When Step 1 asks *"Remember this key on this
computer?"*, type `y` and press Enter. paperfetch saves the key in a file named `.env`
in the `paperfetch-main` folder, and won't ask again. The key is stored as plain text,
so once you've done this, don't share your `paperfetch-main` folder with other people.
To make paperfetch forget the key, see [Troubleshooting](#troubleshooting).

## Part 3: Stopping, coming back and updating

**When you're done:** in JupyterLab, choose **File → Shut Down** and confirm. When the
terminal's prompt comes back, you can close the terminal window.

**Next time:**

1. Open a terminal in the `paperfetch-main` folder
   ([Step 2](#step-2-open-a-terminal-in-the-paperfetch-folder)).
2. Run `pixi run notebook`.

That's it. pixi is already installed, so this takes seconds.

> **Your papers are saved inside the paperfetch folder.** Move the `papers`
> folder somewhere else before you delete a paperfetch folder.

**Updating to a new version of paperfetch:**

1. Rename your current folder, for example to `paperfetch-old`.
2. Download and unzip the new version ([Step 1](#step-1-download-paperfetch)).
3. Move the `papers` folder from `paperfetch-old` into the new `paperfetch-main`.
4. Delete `paperfetch-old`. If you had saved your API key, the notebook will ask for
   it once more.
5. In a terminal in the new folder, run `pixi run notebook`. The first start takes a
   few minutes again.

**Removing paperfetch:** move your `papers` folder somewhere safe, then delete the
`paperfetch-main` folder. That removes paperfetch and its Python setup. To remove pixi
itself too, follow the **Uninstall** section of
[pixi's installation page](https://pixi.sh/latest/installation/).

## Part 4 (optional): Use paperfetch from the terminal

The notebook is the easiest way to use paperfetch. Once you're comfortable, the
terminal is quicker: one line instead of several cells.

Open a terminal in the `paperfetch-main` folder
([Step 2](#step-2-open-a-terminal-in-the-paperfetch-folder)) and try:

**List results without downloading anything:**

```
pixi run paperfetch "machine learning in materials science" --no-download
```

**Download 5 papers:**

```
pixi run paperfetch "machine learning in materials science" --limit 5
```

Each part of the command means:

| Part | Meaning |
|---|---|
| `pixi run` | "Run the next thing with paperfetch's setup." Always put this first. |
| `paperfetch` | The program to run. |
| `"machine learning in materials science"` | What to search for. Keep the quotation marks: they hold several words together as one search. |
| `--limit 5` | An *option*. Options start with `--` and change what the program does. |

Downloaded papers go into the same `papers` folder the notebook uses. Each line of
output starts with `[saved]` or `[no PDF]`, and the last line says how many PDFs were
saved.

**All options:**

| Option | Short form | What it does | If you leave it out |
|---|---|---|---|
| `--limit 25` | `-n 25` | How many results, from 1 to 100 | 10 |
| `--out my-folder` | `-o my-folder` | Which folder to save PDFs in | `papers` |
| `--no-download` | | Only list the results | Downloads |
| `--help` | `-h` | Show all options | |

**Tips**

- Press the **↑ (up arrow)** key to bring back your previous command. Edit it and
  press Enter to run it again, with no retyping.
- If you told the notebook to remember your API key, the terminal uses it too.
- When something goes wrong, paperfetch prints one line explaining what happened.

## Troubleshooting

Look for the message you see, or the closest match.

**`pixi: command not found` (Mac) or `The term 'pixi' is not recognized` (Windows)**
: The terminal was opened before pixi was installed. Close it, open a new one
  ([Step 2](#step-2-open-a-terminal-in-the-paperfetch-folder)), and try again. If it
  still happens, repeat [Step 3](#step-3-install-pixi).

**`could not find pixi.toml or pyproject.toml`**
: The terminal isn't in the paperfetch folder. Repeat
  [Step 2](#step-2-open-a-terminal-in-the-paperfetch-folder).

**Windows: `running scripts is disabled on this system` while installing pixi**
: Install pixi with this command instead, then close and reopen the terminal:
  `winget install prefix-dev.pixi`

**The first `pixi run notebook` stops with a network or download error**
: Check your internet connection and run the command again; pixi picks up where it
  left off. Some university or company networks block these downloads. Try another
  network (a home connection or phone hotspot), or ask your IT department.

**The browser didn't open**
: Copy the link starting with `http://localhost:8888/lab?token=` from the terminal
  into your browser.

**In the notebook: `No module named 'paperfetch'`**
: The notebook was opened some other way, for example by double-clicking the file.
  Close it, and start it from the paperfetch folder with `pixi run notebook`.

**In the notebook: `NameError: name '...' is not defined`**
: A cell was run before the cells above it. Choose **Run → Run All Cells**, or start
  again from the top with Shift + Enter.

**A cell shows `[*]` for a long time**
: It's still working. Bigger searches and downloads take longer. If nothing has
  changed after several minutes, click the **■** (stop) button in the toolbar and run
  the cell again.

**Many papers say "no PDF"**
: That's normal. Some free papers only exist as web pages. Click their titles in the
  Step 3 table to read them. An API key adds more PDFs.

**"OpenAlex stopped the downloads"**
: Today's free allowance is used up. Try again tomorrow, or download fewer papers.

**I want paperfetch to forget my API key**
: Delete the file `.env` in the `paperfetch-main` folder. Its name starts with a dot,
  so it's hidden. On Mac, press **Cmd + Shift + .** in Finder to show hidden files. On
  Windows, in File Explorer choose **View → Show → Hidden items**.

## Linux

Install pixi using the Mac command in [Step 3](#step-3-install-pixi) (or see
<https://pixi.sh>), then run `pixi run notebook` in the paperfetch folder. Everything
else in this guide applies, and the terminal commands are the same as on Mac.

## Getting help

Please file an issue on GitHub.

## Citing paperfetch

If paperfetch helped your research, please cite it. On the
[paperfetch GitHub page](https://github.com/huangfrederick/paperfetch), click
**Cite this repository** on the right-hand side for APA and BibTeX formats.

Please also cite OpenAlex, which provides the paper data:

> Priem, J., Piwowar, H., & Orr, R. (2022). *OpenAlex: A fully-open index of scholarly
> works, authors, venues, institutions, and concepts.* arXiv:2205.01833.
> <https://arxiv.org/abs/2205.01833>
