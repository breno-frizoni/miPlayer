import flet as ft
import flet_permission_handler as fph
import flet_audio as faudio
from yt_dlp import YoutubeDL
import os
from time import sleep
import shutil
import json

class HomeView(ft.View):
    def __init__(self, page):
        super().__init__(
            route='/',
            bgcolor='#022626',
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.IconButton(icon=ft.Icons.HEADSET, icon_color='#C4E5F2', icon_size=80, on_click=lambda e: page.go('/player')),
                        ft.IconButton(icon=ft.Icons.DOWNLOAD, icon_color='#C4E5F2', icon_size=80, on_click=lambda e: page.go('/downloader'))
                    ],
                    spacing=80
                )
            ]
        )
class DownloadView(ft.View):
    def __init__(self, page, storage_path, player, config):
        print('0 - Init DownloadView')
        self.page = page
        self.display = ft.Text('')
        self.url_getter = ft.TextField(autofocus=True, width=400)
        self.storage_path = storage_path
        self.config = config
        self.player = player
        print('0 - super init')
        super().__init__(
            route='/downloader',
            appbar=ft.AppBar(
                leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: page.go('/')),
                title=ft.Text('Baixar'),
                center_title=True,
                elevation=3,
                color="#AFE4EB"
            ),
            controls = [
                ft.Text('Insira o link abaixo: '),
                self.url_getter,
                ft.ElevatedButton(text='Download', icon=ft.Icons.DOWNLOAD, on_click=lambda e: self.download_song(self.page)),
                self.display
            ],
            adaptive=True
        )
        print('1 - super init e Init DownloadView')

    def hook_output(self, d: dict):
        print('0 - hook_output')
        print(f'status: {d["status"]}')
        if d['status'] == 'finished':
            self.display.value += f'\nDownload realizado com sucesso!'
            if self.config["copy_download"]:
                shutil.copy(src=d['filename'], dst=self.config["user_path"])
                print('Arquivo copiado para pasta escolhida pelo usuário')
            if self.page:
                self.page.update()
            else:
                self.player.refresh_songs()
        else:
            self.display.value = f"Baixando: {d['info_dict']['title']}"
            if self.page: # This condition avoid NoneType exception when user is on other view
                self.page.update()
            
        print('1 - hook_output')

    def download_song(self, page):
        print('0 - download_song')
        URL = [self.url_getter.value]
        print(f'Valor de ULR está {URL}')
        
        if URL[0]:
            self.url_getter.value = ''
            self.display.value = 'Aguarde...'
            page.update()
            print('update url_getter to None')
            yt_dlp_conf = {
                'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio',
                'noplaylist': True,
                'noprogress': False,
                'overwrites': True,
                'progress_hooks': [self.hook_output],
                'outtmpl': os.path.join(self.storage_path, 'songs', '%(title)s.%(ext)s')
            }
            print('yt_dlp_conf criada')
            try:
                with YoutubeDL(yt_dlp_conf) as dl:
                    print('YoutubeDL aberto ...')
                    dl.download(URL)
                print('YoutobeDL concluído sem Exception')
            except Exception as ex:
                self.display.value = f'Erro desconhecido. Tente outro URL.'
                page.update()
                print(f'YoutubeDL não concluído por Exception {str(ex)}')
        else:
            print('URL vazia')
            self.display.value = 'Insira a URL acima'
            page.update()
            print('update')
        print('1 - download_song')
class PlayerView(ft.View):
    def __init__(self, page, storage_path):
        self.page = page
        self.songs_path = os.path.join(storage_path, 'songs')
        self.song_controls = ft.ListView(expand=True)
        self.song_titles = list()
        self.audio = faudio.Audio(
            src = 'none.mp3',
            autoplay= False,
            on_state_changed=lambda e: self.audio_state_changed(e)
        )
        self.page.overlay.append(self.audio)
        self.audioState = faudio.AudioState.STOPPED
        self.log = list()
        super().__init__(
            route='/player',
            appbar=ft.AppBar(
                leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: page.go('/')),
                title=ft.Text('Ouvir'),
                center_title=True,
                elevation=3,
                color="#AFE4EB"
            ),
            controls = [self.song_controls]
        )

    def audio_state_changed(self, e):
        self.audioState = e.data

    def resume(self, i):
        self.song_controls.controls[i].leading = ft.Icon(ft.Icons.PAUSE_CIRCLE)
        self.page.update()
        sleep(0.1)
        self.audio.resume()

    def pause(self, i):
        self.song_controls.controls[i].leading = ft.Icon(ft.Icons.PLAY_CIRCLE)
        self.page.update()
        sleep(0.1)
        self.audio.pause()

    def play(self, i):
        if self.log:
            prev_i = self.log[-1][0]
            if i == prev_i:
                match self.audioState:
                    case 'playing':
                        self.pause(i)
                        return None
                    case 'paused':
                        self.resume(i)
                        return None
            self.song_controls.controls[prev_i].leading = ft.Icon(ft.Icons.PLAY_CIRCLE)
            self.song_controls.controls[prev_i].selected = False
        
        self.log.append((i, self.song_titles[i]))
        print(f'log : {self.log[-1]}')
        self.audio.src = os.path.join(self.songs_path, self.song_titles[i])
        self.song_controls.controls[i].leading = ft.Icon(ft.Icons.PAUSE_CIRCLE)
        self.song_controls.controls[i].selected = True
        self.page.update()
        sleep(0.1)
        self.audio.play()


    def refresh_songs(self):
        ''' Update list based on app/storage/data/songs directory files '''
        self.song_controls.controls.clear()
        self.song_titles = []
        i = 0
        for f in os.listdir(self.songs_path):
            self.song_controls.controls.append(
                ft.ListTile(
                    title=ft.Text(f),
                    leading=ft.Icon(ft.Icons.PLAY_CIRCLE),
                    selected_tile_color="#243D63",
                    enable_feedback=True,
                    hover_color="#243D63",
                    on_click=lambda e, idx=i: self.play(idx),
                    shape=ft.RoundedRectangleBorder(ft.border_radius.all(30)),
                    content_padding= ft.Padding(10,10,10,10),
                    text_color= "#8092AF",
                    selected_color="#6FBEFF"
                )
            )
            self.song_titles.append(f)
            i += 1
        if self.page:  self.page.update()
        

def main(page: ft.Page):

    # CONFIGURA O TEMA
    page.theme_mode = ft.ThemeMode.DARK
    page.title='miPlayer'

    # APP STORAGE PATH
    internal_app_storage = os.getenv('FLET_APP_STORAGE_DATA')

    # SISTEMA DE NAVEGAÇÃO
    def route_change(e):
        page.views.clear()
        page.views.append(home)
        if page.route == '/downloader':
            page.views.append(downloader)
        if page.route == '/player':
            player.refresh_songs()
            page.views.append(player)
        page.update()
        print('update route_change')
    def view_pop(e):
        page.views.pop()
        page.update()
        print('update view_pop')
    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # INICIALIZAÇÃO
    if not os.path.exists(os.path.join(internal_app_storage, 'config.json')):
        with open(os.path.join(internal_app_storage, 'config.json'), 'w') as f:
            f.write(r'{"first_init": true, "copy_download": false, "user_path": ""}')
    config = None
    with open(os.path.join(internal_app_storage, 'config.json'), 'r') as f:
        config = json.load(f)
    ph = fph.PermissionHandler()
    page.overlay.append(ph)        
    
    # PRIMEIRA EXECUÇÃO DO APP
    if config["first_init"]:
        waiting = True
        p_status = None
        def wants_copy(e):
            nonlocal waiting
            nonlocal p_status
            waiting = False
            p_status = ph.request_permission(fph.PermissionType.STORAGE)
            config['copy_download'] = True
        def dismiss(e):
            config['copy_download'] = False
            nonlocal waiting
            waiting = False
        
        page.add(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.ListTile(
                                title=ft.Text("Pasta de Downloads"),
                                subtitle=ft.Text(
                                    "Deseja escolher um diretório alternativo para salvar seus downloads?"
                                ),
                            ),
                            ft.Row(
                                [ft.TextButton("Não", on_click=dismiss), ft.TextButton("Sim", on_click=wants_copy)],
                                alignment=ft.MainAxisAlignment.END,
                            ),
                        ]
                    ),
                    width=400,
                    padding=10,
                ),
                shadow_color=ft.Colors.ON_SURFACE_VARIANT,
                elevation=1
            )
        )
        
        while waiting:
            sleep(0.1)
        
        if config['copy_download']:
            waiting = True
            assert p_status == fph.PermissionStatus.GRANTED, "O usuário optou por downloads alternativos mas a requisição de permissão STORAGE falhou."
            def on_result(e):
                nonlocal waiting
                waiting = False
                config['user_path'] = e.path
            file_picker = ft.FilePicker(
                on_result=on_result
            )
            page.overlay.append(file_picker)
            page.update()
            file_picker.get_directory_path()
            while waiting:
                sleep(0.1)
    
        config["first_init"] = False
        with open(os.path.join(internal_app_storage, 'config.json'), 'w') as fp:
            json.dump(config, fp)
    
    page.overlay.clear()
    page.controls.clear()
    home = HomeView(page)
    player = PlayerView(page, internal_app_storage)
    downloader = DownloadView(page,internal_app_storage, player, config)
    page.go('/')
        
ft.app(target=main)