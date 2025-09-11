import flet as ft
import flet_permission_handler as fph
import flet_audio as faudio
from yt_dlp import YoutubeDL
import os
from time import sleep
import shutil

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
    def __init__(self, page, storage_path, player):
        print('0 - Init DownloadView')
        self.page = page
        self.display = ft.Text('')
        self.url_getter = ft.TextField(autofocus=True, width=400)
        self.storage_path = storage_path
        with open(os.path.join(storage_path, 'downloads_path.txt'), 'r') as f:
            self.download_path = f.read()
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
            if os.path.exists(self.download_path):
                shutil.copy(src=d['filename'], dst=self.download_path)
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
        self.song_list = ft.ListView(expand=True)
        self.song_index = list()
        super().__init__(
            route='/player',
            appbar=ft.AppBar(
                leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: page.go('/')),
                title=ft.Text('Ouvir'),
                center_title=True,
                elevation=3,
                color="#AFE4EB"
            ),
            controls = [self.song_list]
        )
    
    def play(self, i):
        audio = faudio.Audio(
            src=os.path.join(self.songs_path, self.song_index[i]),
            autoplay=True,
            volume=1,
            balance=0
        )
        if self.page.overlay and isinstance(self.page.overlay[0], faudio.Audio):
            if self.page.overlay[0].src == audio.src:
                return None
            else:
                self.refresh_songs()
        print(f'Iniciada rotina do som {self.song_index[i]}')
        self.song_list.controls[i].leading = ft.Icon(ft.Icons.PAUSE_CIRCLE)
        self.song_list.controls[i].selected = True
        self.page.overlay.clear()
        self.page.overlay.append(audio)
        self.page.update()
        

    def refresh_songs(self):
        ''' Update list based on app/storage/data/songs directory files '''
        self.song_list.controls.clear()
        self.song_index = []
        i = 0
        for f in os.listdir(self.songs_path):
            self.song_list.controls.append(
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
            self.song_index.append(f)
            i += 1
        if self.page:  self.page.update()
        

def main(page: ft.Page):

    # CONFIGURA O TEMA
    page.theme_mode = ft.ThemeMode.DARK
    page.title='miPlayer'

    # APP STORAGE PATH
    internal_app_storage = os.getenv('FLET_APP_STORAGE_DATA')

    # DEFINE FUNÇÕES E CARREGA VIEWS NA MEMÓRIA
    home = None
    downloader = None
    player = None
    def send_msg(title: str, content: str):
        showing = True
        def on_dismiss(e):
            nonlocal showing
            showing = False
        
        dlg = ft.AlertDialog(
            title=ft.Row([ft.Text(title)], alignment=ft.MainAxisAlignment.CENTER), 
            content=ft.Text(content),
            on_dismiss=on_dismiss,
        )
        page.open(dlg)
        # sync provision
        while showing:
            sleep(0.5)
    def path_getter(e):
        nonlocal internal_app_storage
        with open(os.path.join(internal_app_storage, 'downloads_path.txt'), 'w') as f:
            if e.path:
                f.write(e.path)
            else:
                f.write('None')
    def file_picker():
        waiting = True
        print('file_picker inicializado')
        nonlocal internal_app_storage
        f = os.path.join(internal_app_storage, 'downloads_path.txt')
        print(f)
        file_picker = ft.FilePicker(
            on_result=path_getter
        )
        page.overlay.append(file_picker)
        page.update()
        file_picker.get_directory_path()
        while waiting:
            sleep(1)
            print(waiting)
            if os.path.exists(f):
                waiting = False
    def init():
        nonlocal home, downloader, player
        page.overlay.clear()
        ph = fph.PermissionHandler()
        page.overlay.append(ph)
        page.update()
        sleep(1)
        pstat = ph.request_permission(fph.PermissionType.STORAGE, 10)
        print(f'PermissionStatus: {pstat}') 
        if pstat == fph.PermissionStatus.GRANTED:
            if not os.path.exists(os.path.join(internal_app_storage, 'downloads_path.txt')):
                send_msg(
                    title='Pasta de Downloads',
                    content='Caso não escolha um diretório válido suas músicas' \
                    ' serão salvas no armazenamento interno do aplicativo. Esta ' \
                    'configuração pode ser alterada posteriormente.'
                )
                file_picker()
            home = HomeView(page)
            player = PlayerView(page, internal_app_storage)
            downloader = DownloadView(page, internal_app_storage, player)
            page.go('/')
            return pstat
        else:
            return None

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
    if not init():      
        page.add(
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Container(
                                    ft.Text('Para o correto funcionamento do aplicativo, ' \
                                    'precisamos sua permissão para armazenar as músicas em ' \
                                    'seu dispositivo.'),
                                    width=300,
                                    height=100,
                                    adaptive=True
                                ),
                                ft.ElevatedButton(
                                    'Conceder Permissão',
                                    on_click=lambda _: init(),
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    expand=True
                )
        )
        page.update()

ft.app(target=main)