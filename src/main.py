import flet as ft
import flet_permission_handler as fph
from yt_dlp import YoutubeDL
import os

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
        hook_state = None
        print('0 - hook_output')
        print(f'status: {d["status"]}')
        if d['status'] == 'downloading' and not hook_state:
            self.hook_state = True
            self.display.value = f"Baixando: {d['info_dict']['title']}"
            if self.page: # This condition avoid NoneType exception when user is on other view
                self.page.update()
        if d['status'] == 'finished':
            self.display.value += f'\nDownload realizado com sucesso!'
            if self.page:
                self.page.update()
            else:
                self.player.refresh_songs()
            
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
                'paths': {'home': self.storage_path},
                'outtmpl': os.path.join(self.storage_path, '%(title)s.%(ext)s')
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
        self.storage_path = storage_path
        self.song_list = ft.ListView(expand=True)
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
    def refresh_songs(self):
        ''' Update list based on directory files '''
        self.song_list.controls.clear()
        for f in os.listdir(self.storage_path):
            self.song_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.PLAY_CIRCLE),
                    title=ft.Text(f),
                    selected_tile_color="#320344",
                    hover_color="#243D63"
                )
            )
        if self.page:  self.page.update()
        

def main(page: ft.Page):
    # CONFIGURA O TEMA
    page.theme_mode = ft.ThemeMode.DARK
    page.title='miPlayer'

    # PATH
    client_storage_data = os.getenv('FLET_APP_STORAGE_DATA')

    # CHECK-UP DE PERMISSÕES
    ph = fph.PermissionHandler()
    page.overlay.append(ph)
    try:
        if ph.check_permission(of=fph.PermissionType.MANAGE_EXTERNAL_STORAGE) == "DENIED":
            ph.request_permission(of=fph.PermissionType.MANAGE_EXTERNAL_STORAGE)
    except:
        print('Permission request timeout')

    # CARREGA VIEWS NA MEMÓRIA
    home = HomeView(page)
    player = PlayerView(page, client_storage_data)
    downloader = DownloadView(page, client_storage_data, player)

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
    page.go('/')

ft.app(target=main)
