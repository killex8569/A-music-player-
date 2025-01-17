import customtkinter as ctk
import vlc
import os
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import shutil
from mutagen import File as MutagenFile

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Lecteur de Musique")
        self.root.geometry("900x600")
        
        # Configuration du thème
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Initialisation du lecteur VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.on_media_end)
        
        # Variables de gestion des musiques et playlists
        self.current_song = None
        self.paused = False
        self.playlists = {}
        self.current_playlist = None
        self.song_info = {}  # Structure : {playlist: {song_path: {'duration': float, 'loop': bool, 'favorite': bool}}}

        # Variables pour la fenêtre de menu déroulant
        self.menu_visible = False

        # Variable pour éviter les appels multiples de update_progress
        self.updating_progress = False

        self.create_gui()
        self.load_playlists()

    def create_gui(self):
        # Conteneur principal
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Frame du titre
        title_frame = ctk.CTkFrame(main_frame)
        title_frame.pack(fill="x")

        # Bouton du menu (icône hamburger)
        self.menu_button = ctk.CTkButton(
            title_frame,
            text="☰",  # Unicode pour l'icône hamburger
            width=30,
            height=30,
            corner_radius=5,
            command=self.toggle_menu
        )
        self.menu_button.pack(side="left", padx=(0, 10))

        # Label du titre
        title_label = ctk.CTkLabel(
            title_frame, 
            text="Lecteur de Musique",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")

        # Frame de contenu avec disposition en grille
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=(20, 0))

        # Section des Playlists (à gauche)
        self.playlist_frame = ctk.CTkFrame(content_frame)
        self.playlist_frame.pack(side="left", fill="both", padx=(0, 10), expand=True)

        playlist_label = ctk.CTkLabel(
            self.playlist_frame,
            text="Playlists",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        playlist_label.pack(pady=(0, 10))

        # Sous-frame pour la Listbox et la Scrollbar des playlists
        playlist_list_frame = ctk.CTkFrame(self.playlist_frame)
        playlist_list_frame.pack(fill="both", expand=True)

        # Listbox pour les playlists
        self.playlist_listbox = tk.Listbox(
            playlist_list_frame, 
            bg="#2B2B2B", 
            fg="white", 
            selectbackground="#3A3A3A", 
            selectforeground="white",
            bd=0,
            highlightthickness=0
        )
        self.playlist_listbox.pack(side="left", fill="both", expand=True)
        self.playlist_listbox.bind("<<ListboxSelect>>", self.on_playlist_select)

        # Scrollbar pour les playlists
        self.playlist_scrollbar = tk.Scrollbar(playlist_list_frame)
        self.playlist_scrollbar.pack(side="right", fill="y")
        self.playlist_listbox.config(yscrollcommand=self.playlist_scrollbar.set)
        self.playlist_scrollbar.config(command=self.playlist_listbox.yview)

        # Frame pour les boutons des playlists
        playlist_buttons_frame = ctk.CTkFrame(self.playlist_frame)
        playlist_buttons_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            playlist_buttons_frame,
            text="Nouvelle Playlist",
            command=self.create_playlist
        ).pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(
            playlist_buttons_frame,
            text="Supprimer Playlist",
            command=self.delete_playlist,
            fg_color="#FF5555",
            hover_color="#FF3333"
        ).pack(side="left", padx=5, fill="x", expand=True)

        # Section des Morceaux (à droite)
        self.songs_frame = ctk.CTkFrame(content_frame)
        self.songs_frame.pack(side="right", fill="both", expand=True)

        songs_label = ctk.CTkLabel(
            self.songs_frame,
            text="Morceaux",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        songs_label.pack(pady=(0, 10))

        # Sous-frame pour la Listbox et la Scrollbar des morceaux
        songs_list_frame = ctk.CTkFrame(self.songs_frame)
        songs_list_frame.pack(fill="both", expand=True)

        # Listbox pour les morceaux
        self.songs_listbox = tk.Listbox(
            songs_list_frame, 
            bg="#2B2B2B", 
            fg="white", 
            selectbackground="#3A3A3A", 
            selectforeground="white",
            bd=0,
            highlightthickness=0
        )
        self.songs_listbox.pack(side="left", fill="both", expand=True)
        self.songs_listbox.bind("<<ListboxSelect>>", self.on_song_select)

        # Scrollbar pour les morceaux
        self.songs_scrollbar = tk.Scrollbar(songs_list_frame)
        self.songs_scrollbar.pack(side="right", fill="y")
        self.songs_listbox.config(yscrollcommand=self.songs_scrollbar.set)
        self.songs_scrollbar.config(command=self.songs_listbox.yview)

        # Frame pour les contrôles (Ajouter, Lecture, Pause, Stop, Supprimer)
        controls_frame = ctk.CTkFrame(self.songs_frame)
        controls_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            controls_frame,
            text="Ajouter Musique",
            command=self.add_songs
        ).pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(
            controls_frame,
            text="Lecture",
            command=self.play_music
        ).pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(
            controls_frame,
            text="Pause",
            command=self.pause_music
        ).pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(
            controls_frame,
            text="Stop",
            command=self.stop_music,
            fg_color="#FF5555",
            hover_color="#FF3333"
        ).pack(side="left", padx=5, fill="x", expand=True)

        # Bouton "Supprimer" pour les morceaux
        ctk.CTkButton(
            controls_frame,
            text="Supprimer",
            command=self.delete_song,
            fg_color="#FF5555",
            hover_color="#FF3333"
        ).pack(side="left", padx=5, fill="x", expand=True)

        # Bouton "Lire Playlist" pour lire les playlists dans le répertoire racine
        ctk.CTkButton(
            controls_frame,
            text="Lire Playlist",
            command=self.play_root_playlists
        ).pack(side="left", padx=5, fill="x", expand=True)

        # Barre de progression
        self.progress_var = ctk.DoubleVar()
        self.progress_bar = ctk.CTkSlider(
            self.songs_frame,
            from_=0,
            to=100,
            variable=self.progress_var,
            command=self.seek,
            orientation="horizontal"
        )
        self.progress_bar.pack(fill="x", pady=(10, 10))
        self.progress_bar.configure(state='disabled')  # Désactiver la barre de progression avant la lecture

        # Label pour la musique en cours
        self.current_song_label = ctk.CTkLabel(
            self.songs_frame,
            text="Aucune musique sélectionnée",
            font=ctk.CTkFont(size=12)
        )
        self.current_song_label.pack()

        # Création du menu contextuel (clic droit sur les morceaux)
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Écouter en boucle", command=self.toggle_loop)
        self.context_menu.add_command(label="Ajouter aux favoris", command=self.toggle_favorite)
        self.context_menu.add_command(label="Supprimer", command=self.delete_song)

        # Bind du clic droit sur la Listbox des morceaux
        self.songs_listbox.bind("<Button-3>", self.show_context_menu)

        # Création des frames supplémentaires pour le menu déroulant
        self.create_menu_frames()

    def create_menu_frames(self):
        # Frame du menu déroulant
        menu_width = 225  # Ajustez cette valeur pour représenter environ un quart de la largeur de la fenêtre (900 * 0.25 = 225)
        self.menu_frame = ctk.CTkFrame(self.root, width=menu_width, corner_radius=0)
        self.menu_frame.place(x=-menu_width, y=0, relheight=1)  # Position initiale hors de l'écran
        self.menu_frame.pack_propagate(False)

        # Bouton "Accueil"
        home_button = ctk.CTkButton(
            self.menu_frame,
            text="Accueil",
            command=self.show_home
        )
        home_button.pack(pady=(50, 10), padx=20, fill="x")

        # Bouton "Mes Favoris"
        fav_button = ctk.CTkButton(
            self.menu_frame,
            text="Mes Favoris",
            command=self.show_favorites
        )
        fav_button.pack(pady=10, padx=20, fill="x")

        # Bouton "Info"
        info_button = ctk.CTkButton(
            self.menu_frame,
            text="Info",
            command=self.show_info
        )
        info_button.pack(pady=10, padx=20, fill="x")

        # Bouton pour fermer le menu
        close_button = ctk.CTkButton(
            self.menu_frame,
            text="Fermer",
            command=self.toggle_menu
        )
        close_button.pack(pady=10, padx=20, fill="x")

        # Frame pour les favoris
        self.favorites_frame = ctk.CTkFrame(self.root)
        self.favorites_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.favorites_frame.pack_forget()  # Masquer initialement

        favorites_label = ctk.CTkLabel(
            self.favorites_frame,
            text="Mes Favoris",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        favorites_label.pack(pady=(0, 10))

        # Listbox pour les favoris
        self.favorites_listbox = tk.Listbox(
            self.favorites_frame, 
            bg="#2B2B2B", 
            fg="white", 
            selectbackground="#3A3A3A", 
            selectforeground="white",
            bd=0,
            highlightthickness=0
        )
        self.favorites_listbox.pack(fill="both", expand=True)

        # Scrollbar pour les favoris
        self.favorites_scrollbar = tk.Scrollbar(self.favorites_frame)
        self.favorites_scrollbar.pack(side="right", fill="y")
        self.favorites_listbox.config(yscrollcommand=self.favorites_scrollbar.set)
        self.favorites_scrollbar.config(command=self.favorites_listbox.yview)

        # Frame pour la page Info
        self.info_frame = ctk.CTkFrame(self.root)
        self.info_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.info_frame.pack_forget()  # Masquer initialement

        info_label = ctk.CTkLabel(
            self.info_frame,
            text="Informations",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        info_label.pack(pady=(0, 10))

        info_text = ctk.CTkTextbox(
            self.info_frame,
            width=600,
            height=400,
            wrap="word",
            state="disabled"
        )
        info_text.pack(fill="both", expand=True)
        info_content = (
            "Bienvenue dans votre lecteur de musique personnalisé !\n\n"
            "Cette application vous permet de créer et de gérer des playlists, de lire vos morceaux préférés, de marquer des chansons en tant que favorites, et bien plus encore.\n\n"
            "Utilisez le menu en haut à gauche pour accéder à vos favoris ou pour en savoir plus sur l'application."
        )
        info_text.configure(state="normal")
        info_text.insert("end", info_content)
        info_text.configure(state="disabled")

    def toggle_menu(self):
        if not self.menu_visible:
            # Afficher le menu avec une animation simple
            menu_width = self.menu_frame.winfo_width()
            self.animate_menu(-menu_width, 0)
            self.menu_visible = True
            self.menu_frame.lift()  # Assurer que le menu est au-dessus des autres frames
        else:
            # Cacher le menu avec une animation simple
            menu_width = self.menu_frame.winfo_width()
            self.animate_menu(0, -menu_width)
            self.menu_visible = False

    def animate_menu(self, start, end, step=20):
        if start < end:
            new_x = start + step
            if new_x >= end:
                new_x = end
            self.menu_frame.place(x=new_x, y=0, relheight=1)
            if new_x < end:
                self.root.after(10, lambda: self.animate_menu(new_x, end, step))
        elif start > end:
            new_x = start - step
            if new_x <= end:
                new_x = end
            self.menu_frame.place(x=new_x, y=0, relheight=1)
            if new_x > end:
                self.root.after(10, lambda: self.animate_menu(new_x, end, step))
        self.menu_frame.lift()  # Toujours lever le menu après chaque déplacement

    def create_playlist(self):
        # Ouvrir une fenêtre de création de playlist personnalisée
        self.create_playlist_window()

    def create_playlist_window(self):
        # Création d'une nouvelle fenêtre avec customtkinter
        playlist_window = ctk.CTkToplevel(self.root)
        playlist_window.title("Créer une Nouvelle Playlist")
        playlist_window.geometry("400x200")
        playlist_window.resizable(False, False)

        # Assurer que la fenêtre de dialogue apparaisse devant la fenêtre principale
        playlist_window.transient(self.root)  # Associe la fenêtre principale
        playlist_window.grab_set()            # Rend la fenêtre modale
        playlist_window.focus_set()           # Définit le focus sur la fenêtre de dialogue
        playlist_window.lift()                # Amène la fenêtre au-dessus

        # Frame principale de la fenêtre
        frame = ctk.CTkFrame(playlist_window, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Label
        label = ctk.CTkLabel(
            frame,
            text="Nom de la Playlist",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        label.pack(pady=(0, 10))

        # Entry pour le nom de la playlist
        self.new_playlist_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Entrez le nom de la playlist",
            width=300
        )
        self.new_playlist_entry.pack(pady=(0, 20))

        # Bouton de création
        create_button = ctk.CTkButton(
            frame,
            text="Créer",
            command=lambda: self.confirm_create_playlist(playlist_window)
        )
        create_button.pack()

    def confirm_create_playlist(self, window):
        name = self.new_playlist_entry.get().strip()
        if name:
            if name in self.playlists:
                messagebox.showerror("Erreur", "Une playlist avec ce nom existe déjà.")
            else:
                self.playlists[name] = []
                self.song_info[name] = {}
                self.update_playlist_display()
                self.save_playlists()
                self.create_playlist_folder(name)
                window.destroy()
        else:
            messagebox.showwarning("Nom invalide", "Veuillez entrer un nom de playlist valide.")

    def create_playlist_folder(self, playlist_name):
        # Créer un dossier pour la playlist
        script_dir = Path(__file__).parent.resolve()
        playlist_path = script_dir / playlist_name
        try:
            playlist_path.mkdir(exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de créer le dossier de la playlist : {e}")

    def delete_playlist(self):
        selection = self.playlist_listbox.curselection()
        if selection:
            index = selection[0]
            selected_playlist = self.playlist_listbox.get(index)
            confirm = messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer la playlist '{selected_playlist}' ?")
            if confirm:
                del self.playlists[selected_playlist]
                del self.song_info[selected_playlist]
                self.update_playlist_display()
                self.save_playlists()
                self.delete_playlist_folder(selected_playlist)
                if self.current_playlist == selected_playlist:
                    self.current_playlist = None
                    self.update_songs_display()
                    self.stop_music()
        else:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner une playlist à supprimer.")

    def delete_playlist_folder(self, playlist_name):
        # Supprimer le dossier de la playlist
        script_dir = Path(__file__).parent.resolve()
        playlist_path = script_dir / playlist_name
        try:
            if playlist_path.exists() and playlist_path.is_dir():
                shutil.rmtree(playlist_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer le dossier de la playlist : {e}")

    def update_playlist_display(self):
        self.playlist_listbox.delete(0, tk.END)
        for playlist in self.playlists:
            self.playlist_listbox.insert(tk.END, playlist)
        self.check_playlist_scrollbar()

    def on_playlist_select(self, event):
        selection = self.playlist_listbox.curselection()
        if selection:
            index = selection[0]
            selected_playlist = self.playlist_listbox.get(index)
            self.current_playlist = selected_playlist
            self.update_songs_display()

    def update_songs_display(self):
        self.songs_listbox.delete(0, tk.END)
        if self.current_playlist and self.current_playlist in self.playlists:
            for song in self.playlists[self.current_playlist]:
                info = self.song_info[self.current_playlist].get(song, {})
                display_name = ""
                if info.get('loop', False):
                    display_name += "🔁 "
                if info.get('favorite', False):
                    display_name += "★ "
                display_name += os.path.basename(song)
                self.songs_listbox.insert(tk.END, display_name)
        self.check_songs_scrollbar()

    def add_songs(self):
        if not self.current_playlist:
            messagebox.showwarning("Aucune playlist sélectionnée", "Veuillez sélectionner une playlist avant d'ajouter des musiques.")
            return

        files = filedialog.askopenfilenames(
            title="Ajouter des musiques",
            filetypes=[("Fichiers audio", "*.mp3 *.wav *.ogg *.flac *.m4a")]
        )
        
        if files:
            script_dir = Path(__file__).parent.resolve()
            playlist_folder = script_dir / self.current_playlist
            for file in files:
                try:
                    # Vérifier si le fichier est déjà dans la playlist
                    if file in self.playlists[self.current_playlist]:
                        continue

                    # Copier le fichier dans le dossier de la playlist
                    dest_path = playlist_folder / os.path.basename(file)
                    
                    # Si le fichier existe déjà, éviter les doublons
                    if dest_path.exists():
                        base, ext = os.path.splitext(dest_path.name)
                        counter = 1
                        while True:
                            new_name = f"{base} ({counter}){ext}"
                            dest_path = playlist_folder / new_name
                            if not dest_path.exists():
                                break
                            counter += 1

                    shutil.copy(file, dest_path)

                    # Ajouter le chemin absolu à la playlist
                    song_path = str(dest_path)
                    self.playlists[self.current_playlist].append(song_path)

                    # Obtenir la durée de la chanson via mutagen
                    audio = MutagenFile(song_path)
                    if audio is not None and audio.info.length is not None:
                        duration = audio.info.length
                    else:
                        duration = 0
                    self.song_info[self.current_playlist][song_path] = {'duration': duration, 'loop': False, 'favorite': False}

                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible d'ajouter la musique '{file}' : {e}")
            self.update_songs_display()
            self.save_playlists()

    def play_music(self):
        selection = self.songs_listbox.curselection()
        if selection and self.current_playlist:
            index = selection[0]
            selected_song_display = self.songs_listbox.get(index)
            # Retirer les icônes éventuelles
            song_name = selected_song_display.replace("🔁 ", "").replace("★ ", "")
            # Trouver le chemin complet du morceau
            song_path = None
            for path in self.playlists[self.current_playlist]:
                if os.path.basename(path) == song_name:
                    song_path = path
                    break
            if not song_path:
                messagebox.showerror("Erreur", "Chemin de la musique introuvable.")
                return
            try:
                if self.current_song != song_path:
                    self.player.stop()  # Arrêter la musique actuelle avant de changer
                    media = self.instance.media_new(song_path)
                    self.player.set_media(media)
                    self.player.play()
                    self.current_song = song_path
                    self.current_song_label.configure(text=os.path.basename(song_path))

                    # Configurer la barre de progression
                    self.player.audio_set_volume(100)  # Réglage du volume si nécessaire
                    self.updating_progress = False
                    self.progress_bar.configure(state='disabled')
                    self.progress_var.set(0)
                    self.root.after(100, self.set_progress_duration)
                elif self.paused:
                    self.player.play()
                    self.paused = False
                    self.progress_bar.configure(state='normal')
                    if not self.updating_progress:
                        self.update_progress()
                        self.updating_progress = True
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de jouer la musique '{os.path.basename(song_path)}' : {e}")
        else:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner une musique à jouer.")

    def set_progress_duration(self):
        if self.current_song:
            try:
                duration_ms = self.player.get_length()
                if duration_ms > 0:
                    duration = duration_ms / 1000  # Convertir en secondes
                    self.progress_bar.configure(from_=0, to=duration)
                    current_time = self.player.get_time() / 1000
                    self.progress_var.set(current_time)
                    self.progress_bar.configure(state='normal')
                    if not self.updating_progress and self.player.is_playing():
                        self.update_progress()
                        self.updating_progress = True
                else:
                    # Réessayer après 100 ms si la durée n'est pas encore disponible
                    self.root.after(100, self.set_progress_duration)
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la configuration de la barre de progression : {e}")
                self.progress_bar.configure(state='disabled')

    def pause_music(self):
        if self.player.is_playing():
            self.player.pause()
            self.paused = True
            self.progress_bar.configure(state='disabled')
            self.updating_progress = False
        else:
            if self.current_song:
                self.player.play()
                self.paused = False
                self.progress_bar.configure(state='normal')
                if not self.updating_progress:
                    self.update_progress()
                    self.updating_progress = True

    def stop_music(self):
        self.player.stop()
        self.current_song = None
        self.progress_var.set(0)
        self.progress_bar.configure(state='disabled')
        self.current_song_label.configure(text="Aucune musique sélectionnée")
        self.updating_progress = False

    def seek(self, value):
        if self.current_song and self.player.get_length() > 0:
            try:
                pos = float(value)
                self.player.set_time(int(pos * 1000))  # VLC prend le temps en millisecondes
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de chercher dans la musique : {e}")

    def update_progress(self):
        if self.current_song and self.player.is_playing():
            try:
                current_time = self.player.get_time() / 1000  # Convertir en secondes
                self.progress_var.set(current_time)
                duration = self.song_info[self.current_playlist].get(self.current_song, {}).get('duration', 0)
                if current_time >= duration - 1:
                    # La chanson est terminée, gérer la boucle ou arrêter
                    if self.song_info[self.current_playlist][self.current_song].get('loop', False):
                        self.player.stop()
                        self.player.play()
                    else:
                        self.stop_music()
                else:
                    self.root.after(1000, self.update_progress)
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la mise à jour de la barre de progression : {e}")
                self.progress_bar.configure(state='disabled')
                self.updating_progress = False
        else:
            self.progress_bar.configure(state='disabled')
            self.updating_progress = False

    def on_media_end(self, event):
        """Gestionnaire d'événement pour la fin de la musique."""
        self.stop_music()

    def save_playlists(self):
        data = {
            "playlists": self.playlists,
            "song_info": self.song_info
        }
        try:
            with open('playlists.json', 'w') as f:
                json.dump(data, f)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder les playlists : {e}")

    def load_playlists(self):
        try:
            with open('playlists.json', 'r') as f:
                data = json.load(f)
                self.playlists = data.get("playlists", {})
                self.song_info = data.get("song_info", {})
                self.update_playlist_display()
        except FileNotFoundError:
            self.playlists = {}
            self.song_info = {}
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les playlists : {e}")
            self.playlists = {}
            self.song_info = {}

    def on_song_select(self, event):
        # Fonctionnalité supplémentaire lors de la sélection d'une chanson (optionnel)
        pass

    def delete_song(self):
        selection = self.songs_listbox.curselection()
        if selection and self.current_playlist:
            index = selection[0]
            selected_song_display = self.songs_listbox.get(index)
            # Retirer les icônes éventuelles
            song_name = selected_song_display.replace("🔁 ", "").replace("★ ", "")
            # Trouver le chemin complet du morceau
            song_path = None
            for path in self.playlists[self.current_playlist]:
                if os.path.basename(path) == song_name:
                    song_path = path
                    break
            if not song_path:
                messagebox.showerror("Erreur", "Chemin de la musique introuvable.")
                return
            confirm = messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer la musique '{song_name}' de la playlist ?")
            if confirm:
                try:
                    # Supprimer le fichier du disque
                    if os.path.exists(song_path):
                        os.remove(song_path)
                    
                    # Supprimer la musique de la playlist
                    index_in_playlist = self.playlists[self.current_playlist].index(song_path)
                    del self.playlists[self.current_playlist][index_in_playlist]
                    del self.song_info[self.current_playlist][song_path]
                    
                    self.update_songs_display()
                    self.save_playlists()

                    # Si la musique supprimée était en cours de lecture, arrêter la lecture
                    if self.current_song == song_path:
                        self.stop_music()

                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de supprimer la musique '{song_name}' : {e}")
        else:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner une musique à supprimer.")

    def show_context_menu(self, event):
        # Sélectionner l'élément cliqué
        try:
            index = self.songs_listbox.nearest(event.y)
            self.songs_listbox.selection_clear(0, tk.END)
            self.songs_listbox.selection_set(index)
            self.songs_listbox.activate(index)
            self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"Erreur lors de l'affichage du menu contextuel : {e}")

    def toggle_loop(self):
        selection = self.songs_listbox.curselection()
        if selection and self.current_playlist:
            index = selection[0]
            selected_song_display = self.songs_listbox.get(index)
            # Retirer les icônes éventuelles
            song_name = selected_song_display.replace("🔁 ", "").replace("★ ", "")
            # Trouver le chemin complet du morceau
            song_path = None
            for path in self.playlists[self.current_playlist]:
                if os.path.basename(path) == song_name:
                    song_path = path
                    break
            if not song_path:
                messagebox.showerror("Erreur", "Chemin de la musique introuvable.")
                return
            current_loop = self.song_info[self.current_playlist][song_path].get('loop', False)
            self.song_info[self.current_playlist][song_path]['loop'] = not current_loop
            self.update_songs_display()
            self.save_playlists()

    def toggle_favorite(self):
        selection = self.songs_listbox.curselection()
        if selection and self.current_playlist:
            index = selection[0]
            selected_song_display = self.songs_listbox.get(index)
            # Retirer les icônes éventuelles
            song_name = selected_song_display.replace("🔁 ", "").replace("★ ", "")
            # Trouver le chemin complet du morceau
            song_path = None
            for path in self.playlists[self.current_playlist]:
                if os.path.basename(path) == song_name:
                    song_path = path
                    break
            if not song_path:
                messagebox.showerror("Erreur", "Chemin de la musique introuvable.")
                return
            current_favorite = self.song_info[self.current_playlist][song_path].get('favorite', False)
            self.song_info[self.current_playlist][song_path]['favorite'] = not current_favorite
            self.update_songs_display()
            self.save_playlists()
            self.update_favorites_list()

    def check_playlist_scrollbar(self):
        """Afficher ou cacher la scrollbar des playlists en fonction du nombre d'éléments."""
        self.playlist_listbox.update_idletasks()
        listbox_height = self.playlist_listbox.winfo_height()
        num_items = self.playlist_listbox.size()
        if num_items == 0:
            self.playlist_scrollbar.pack_forget()
            return
        item_height = self.playlist_listbox.winfo_reqheight() / num_items
        visible_items = int(listbox_height / item_height)
        if num_items > visible_items:
            self.playlist_scrollbar.pack(side="right", fill="y")
        else:
            self.playlist_scrollbar.pack_forget()

    def check_songs_scrollbar(self):
        """Afficher ou cacher la scrollbar des morceaux en fonction du nombre d'éléments."""
        self.songs_listbox.update_idletasks()
        listbox_height = self.songs_listbox.winfo_height()
        num_items = self.songs_listbox.size()
        if num_items == 0:
            self.songs_scrollbar.pack_forget()
            return
        item_height = self.songs_listbox.winfo_reqheight() / num_items
        visible_items = int(listbox_height / item_height)
        if num_items > visible_items:
            self.songs_scrollbar.pack(side="right", fill="y")
        else:
            self.songs_scrollbar.pack_forget()

    def show_favorites(self):
        # Masquer toutes les frames excepté favorites_frame
        self.favorites_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.songs_frame.pack_forget()
        self.playlist_frame.pack_forget()
        self.info_frame.pack_forget()

        # Mettre à jour la liste des favoris
        self.update_favorites_list()

    def update_favorites_list(self):
        self.favorites_listbox.delete(0, tk.END)
        for playlist in self.playlists:
            for song in self.playlists[playlist]:
                if self.song_info[playlist].get(song, {}).get('favorite', False):
                    fav_display = f"★ {os.path.basename(song)}"
                    self.favorites_listbox.insert(tk.END, fav_display)
        self.check_favorites_scrollbar()

    def check_favorites_scrollbar(self):
        """Afficher ou cacher la scrollbar des favoris en fonction du nombre d'éléments."""
        self.favorites_listbox.update_idletasks()
        listbox_height = self.favorites_listbox.winfo_height()
        num_items = self.favorites_listbox.size()
        if num_items == 0:
            self.favorites_scrollbar.pack_forget()
            return
        item_height = self.favorites_listbox.winfo_reqheight() / num_items
        visible_items = int(listbox_height / item_height)
        if num_items > visible_items:
            self.favorites_scrollbar.pack(side="right", fill="y")
        else:
            self.favorites_scrollbar.pack_forget()

    def show_info(self):
        # Masquer toutes les frames excepté info_frame
        self.info_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.songs_frame.pack_forget()
        self.playlist_frame.pack_forget()
        self.favorites_frame.pack_forget()

    def show_home(self):
        # Masquer toutes les frames excepté songs_frame et playlist_frame
        self.favorites_frame.pack_forget()
        self.info_frame.pack_forget()
        self.playlist_frame.pack(side="left", fill="both", padx=(0, 10), expand=True)
        self.songs_frame.pack(side="right", fill="both", expand=True)

    def play_root_playlists(self):
        # Fonction pour lire les playlists dans le répertoire racine
        script_dir = Path(__file__).parent.resolve()
        playlists_in_root = [p for p in script_dir.iterdir() if p.is_dir() and p.name in self.playlists]
        if playlists_in_root:
            # Afficher une fenêtre pour sélectionner la playlist à jouer
            playlists_names = [p.name for p in playlists_in_root]
            selected_playlist = self.select_playlist_window(playlists_names)
            if selected_playlist:
                self.current_playlist = selected_playlist
                self.update_songs_display()
                self.play_music()
        else:
            messagebox.showinfo("Aucune Playlist", "Aucune playlist trouvée dans le répertoire racine.")

    def select_playlist_window(self, playlists):
        # Fenêtre pour sélectionner une playlist à partir de la liste fournie
        select_window = ctk.CTkToplevel(self.root)
        select_window.title("Sélectionner une Playlist")
        select_window.geometry("300x400")
        select_window.resizable(False, False)

        select_window.transient(self.root)
        select_window.grab_set()
        select_window.focus_set()
        select_window.lift()

        frame = ctk.CTkFrame(select_window)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        label = ctk.CTkLabel(
            frame,
            text="Sélectionnez une Playlist",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        label.pack(pady=(0, 10))

        playlist_listbox = tk.Listbox(
            frame,
            bg="#2B2B2B",
            fg="white",
            selectbackground="#3A3A3A",
            selectforeground="white",
            bd=0,
            highlightthickness=0
        )
        playlist_listbox.pack(fill="both", expand=True)
        for playlist in playlists:
            playlist_listbox.insert(tk.END, playlist)

        def confirm_selection():
            selection = playlist_listbox.curselection()
            if selection:
                selected = playlist_listbox.get(selection[0])
                self.current_playlist = selected
                select_window.destroy()
            else:
                messagebox.showwarning("Aucune sélection", "Veuillez sélectionner une playlist.")

        confirm_button = ctk.CTkButton(
            frame,
            text="Confirmer",
            command=confirm_selection
        )
        confirm_button.pack(pady=10)

        self.root.wait_window(select_window)
        return self.current_playlist

if __name__ == "__main__":
    root = ctk.CTk()
    app = MusicPlayer(root)
    root.mainloop()
