"""Module entrypoint for `python -m src.gui`."""

import tkinter as tk

from .app import BotOMatGUI


def main():
    root = tk.Tk()
    root.geometry("1320x640")
    BotOMatGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
