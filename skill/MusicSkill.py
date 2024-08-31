from pycloudmusic import Music163Api
from robot.AudioPlayer import load_audio



class MusicSkill():
    def __init__(self):
      # 进行同步初始化，不包括异步逻辑
        self.music_api = None
        self.my = None
        self.user = None

    async def initialize(self):
        self.Music = Music163Api(
        '_ntes_nuid=9da0d88ee75b8ff3afb129b1d9964071; WEVNSM=1.0.0; WM_TID=8AhKWPLl%2BsdARAAVVUaFgB%2FWlBnSG1Gl; ntes_utid=tid._.2f9N689300VAQxUBREeAkF%252BThR3TSTK6._.0; _ga=GA1.1.534684940.1701681782; Qs_lvt_382223=1701681781; Qs_pv_382223=253199295622736160; _clck=13jdlhd%7C2%7Cfh9%7C0%7C1433; _ga_C6TGHFPQ1H=GS1.1.1701684066.2.0.1701684066.0.0.0; __remember_me=true; ntes_kaola_ad=1; _ntes_nnid=9da0d88ee75b8ff3afb129b1d9964071,1717382362552; NMTID=00Omf43Ygm6IIQ41kQtsRPtD0r415EAAAGQ3TBH-g; WNMCID=drumav.1722311040159.01.0; sDeviceId=YD-tBV0FdoTLCRBVwRARFPBfEHLsYnHy%2BOn; __snaker__id=4EkFiTUUaV04Dmcu; JSESSIONID-WYYY=X9xaHeaRaKU32jR%2F2voQPbIVfkisT5n%2F7CPH7OM5sYsEQMJhnCAEflQAehGpqU0NhHZhnwQN25xzNsyzDV1JjSicFYh7fHhvtODk3cUHgRpviVC4W9Aue0lFhbsVrQAq7PGvZlvzu6Y7%5CE3VwCzhiCo88NNlaJXohrY%2FSPmB0EY9AHNA%3A1724830426172; _iuqxldmzr_=32; WM_NI=tVGzo%2Fx4%2BN%2F7NLj3IW0WugASprf7jbdAAB8IKaejhmvaxJZiTzDEflkQZF0BmEbVjI3apYQopG6lljf3ZNyvY3Gxb7RcQPDp14AdUxTbz3D6DW8W%2Fdxd0FQnjIueVAstWVU%3D; WM_NIKE=9ca17ae2e6ffcda170e2e6eea7eb668ab5bfd3f14ba9b88bb6d14e878f8a86c24ab887f9d5e14a8fafbbb4fc2af0fea7c3b92ab88a899bee25bcece5afae3d8e94a6d4cc5df489bb88c459b4aeaad8e96aa89f8fa3bb4389bfab8beb67b6bfb8abd96398a68ca6e568a98f96a7b34aaf9baeb7e943f1bfc0bad465b499fa8def62a6ed96affc7e9bed8999e13d92bd9fb1c77cf3ec8f85d87498beb6d4c73e8889f8b8ae70bcbc00a7d466aa97bb86d54bb1ac99b7d837e2a3; gdxidpyhxdE=WNa%2FzDntUNh1IT0Q6JcfbTYXIK6bZl2%2FzVby6iA3pHLIazOBXcWwWHIJfJbR9Oi%2F%2FHsxf1I4pn2UYZIESa5qGJ%5Cmx9Qp%5CXE5ZUiYKxC2qXZjtutUEB9Mab%5C35uYQG2VnNoGwz6yD3qmLnkL2ATDnUjz%2FBHPbo9WxBfCs6RR%5CzL4t%2BvpO%3A1724829529171; MUSIC_U=0094A68E8E5C6062DC2228C6526CEE2D8D1B376A9CABE76574D3BC4E2FDBBCCF63AFD4F8B30521AFBEA9B171436242236C65119B482F6BD8741ED454A9311790D73483F632C4CE296A779A62F5C2EE65DE190F8F90EE328B99F3CB54C59134FA1C677CCDE52C82D988C322DF38289EE5389556032F7408FB23B73B22983B9D12CB217616EE8D592019CE03366798932D1058D53F742210A36306ED862428E8E618221005950CD6F00A2C87895B0192757F9E8F946ECD51B669EB80163003650998B8A9E4C5FFE2FE4545906C4F9FB5749BF8B5997130970CE870EA0981B4CFE3C2A042D01FCB0E4E91CD51CC5F8D20F9619176F6443083A0F7F93CDAF1E39F7427EF14A818FB05C9601C84CCFAFEB3AC4C92000A9875050299DA77858DE69C560B93A8F68C529214068C01EEBA7F59DFD0248BE74F2A28A2CC1D92DD6323CE96A1E9AEA197D573C7B05622BF224374461677DC25F86E235C55AA5A524AE71581B2; __csrf=a63077e7315475da58073eaa1d5aa12c')
        self.my = await self.Music.my()
        self.user = await self.Music.user(self.my.id)

    async def likeList(self,play):
        likeList = await self.user.like_music()
        music = await self.Music.music(ids=65528)
        playFile = await music.play(download_path='../download')
        initial_audio = load_audio(playFile)
        play.append_audio(initial_audio)
        return likeList
    
    async def search_music(self,play,data):
        print('的'.join(data))
        likeList = await self.Music._search(key=' '.join(data))
        likeList['result']['songs']
        music = await self.Music.music(ids=likeList['result']['songs'][0]['id'])
        playFile = await music.play(download_path='../download')
        initial_audio = load_audio(playFile)
        play.append_audio(initial_audio)
        return playFile
        