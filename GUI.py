import subprocess
import tkinter
from tkinter import ttk
from tkinter import filedialog
import configparser
import Generator


class UserInterface(ttk.Frame):

    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read('config.txt')
        self.init_gui()

    def on_quit(self):
        """Exits program."""
        quit()

    def init_gui(self):
        """Builds GUI."""
        self.root.title('Playlist Generator')
        self.root.option_add('*tearOff', 'FALSE')

        self.grid(column=0, row=0, sticky='nsew')

        self.playlistName = tkinter.StringVar()
        self.playlistName.set('Playlist Name')
        self.playlistEntry = ttk.Entry(self, textvariable=self.playlistName, justify='center')
        self.playlistEntry.grid(column=0, row=0, columnspan=3)
        self.playlistEntry.bind('<Button-1>', self.clearPlaylistName)

        self.listOfItems = tkinter.Listbox(self)
        self.listOfItems.grid(column=0, row=3, columnspan=2, rowspan=2)
        self.listOfItems.bind('<Delete>', self.removeEntry)

        tkinter.Label(self, text='Insert band names or setlist links or import from file').grid(column=0, row=1, columnspan=3)
        self.entry = tkinter.StringVar()
        self.entry.set('Band or Setlist link')
        self.ent = ttk.Entry(self, textvariable=self.entry)
        self.ent.bind('<Button-1>', self.clearInput)
        self.ent.bind('<Return>', self.addEntry)

        self.ent.grid(column=0, row=2, columnspan=2)

        ttk.Button(self, text='Import', command=self.loadfile).grid(column=2, row=2)

        """All songs vs Setlists"""
        self.playlistType = tkinter.IntVar()
        self.playlistType.set(1)
        tkinter.Radiobutton(self, text='Latest Set', variable=self.playlistType, value=1).grid(column=2, row=3)
        tkinter.Radiobutton(self, text='All songs', variable=self.playlistType, value=2).grid(column=2, row=4)

        self.specificSet = tkinter.StringVar()
        self.specificSet.set('Optional search phrase')
        self.specific = ttk.Entry(self, textvariable=self.specificSet, justify='center')
        self.specific.grid(column=0, row=5, columnspan=2)
        self.specific.bind('<Button-1>', self.clearSpecific)

        """Type of playlist"""
        self.spotify = tkinter.IntVar()
        ttk.Checkbutton(self, text='Spotify', variable=self.spotify, command=self.updateButton).grid(column=0, row=8)
        self.googlemusic = tkinter.IntVar()
        ttk.Checkbutton(self, text='GoogleMusic', variable=self.googlemusic, command=self.updateButton).grid(column=1, row=8)
        self.local = tkinter.IntVar()
        ttk.Checkbutton(self, text='Local', variable=self.local, command=self.checkLocal).grid(column=2, row=8)

        self.status = tkinter.StringVar()
        self.status.set("Generate!")
        ttk.Button(self, textvariable=self.status, command=self.generate).grid(column=0, row=9)
        self.message = tkinter.StringVar()
        self.message.set("")
        tkinter.Label(self, textvariable=self.message).grid(column=0, row=10, columnspan=3)

        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)

    def checkLocal(self):
        self.updateButton()
        if not self.config.get('Local Playlists', 'Music Directory', fallback=None):
            tkinter.messagebox.showerror('Error', 'Please check config settings. Exiting.')
            self.openConfig()
            self.on_quit()

    def openConfig(self):
        subprocess.Popen('start config.txt', shell=True)

    def updateButton(self):
        self.message.set('')
        self.status.set('Generate!')

    def addEntry(self, pointless_var=None):
        self.listOfItems.insert(tkinter.END, self.entry.get())
        self.ent.delete(0, tkinter.END)
        self.status.set('Generate!')
        self.message.set('')

    def removeEntry(self, pointless_var=None):
        selection = self.listOfItems.curselection()
        self.listOfItems.delete(selection[0])

    def clearPlaylistName(self, pointless_var=None):
        self.playlistName.set('')

    def clearInput(self, pointless_var=None):
        self.entry.set('')

    def clearSpecific(self, pointless_var=None):
        self.specificSet.set('')

    def loadfile(self):
        self.file = filedialog.askopenfile(title='Load a file', mode='r')
        if not self.file:
            return
        for line in self.file.readlines():
            self.listOfItems.insert(tkinter.END, line)

    def openLog(self):
        subprocess.Popen('start log.txt', shell=True)

    def generate(self):
        list_of_items = self.listOfItems.get(0, tkinter.END)
        list_of_items = [item.strip() for item in list_of_items]
        options = {}
        options['playlist_name'] = self.playlistName.get()
        options['spotify'] = self.spotify.get()
        options['google_music'] = self.googlemusic.get()
        options['local'] = self.local.get()
        options['playlist_type'] = self.playlistType.get()
        options['specific_set'] = self.specificSet.get()
        options['gui_interface'] = self.root
        generator = Generator.Generator(list_of_items, options)
        self.status.set('Working...')
        status, message = generator.run()
        self.status.set(status)
        self.message.set(message)
        if status == 'Finished':
            self.message.set('Enter new playlist info and press Finished to run again!')
            ttk.Button(self, text='Open Log', command=self.openLog).grid(column=1, row=9)
            if self.local.get():
                ttk.Button(self, text='Copy Files', command=lambda: self.copy(generator)).grid(column=2, row=9)

    def copy(self, generator):
        self.dir = filedialog.askdirectory(title='Choose dir')
        generator.copyFiles(self.dir)
        self.message.set('Copied files from playlist')
