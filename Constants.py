from discord import Embed
from discord import Color
from dotenv import load_dotenv
from os import getenv

"""==================Colors=================="""
green = Color.green()
blue = Color.blue()
red = Color.red()

"""==================Embeds=================="""
NOT_CONNECTED_EMBED = Embed(title='', description='I am not connected to a voice channel.', color=red)
NOT_PLAYING_EMBED = Embed(title='', description='I am currently not playing anything.', color=red)

"""==================YTDL, FFMPEG=================="""
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

songs_type = {
    'weba': 'webm',
    'm4a': 'mp4'
}


"""==================Shoam=================="""
KRUVIT_NAME = 'shoam'


"""==================GIFs=================="""
LEAVE_GIF = 'https://tenor.com/view/suicide-gif-14427950'
LEAVE_GIF_DANNY = 'https://tenor.com/view/danny-devito-walking-away-money-raining-money-explosions-gif-16685519'
SHUFFLE = 'https://tenor.com/view/cards-shuffle-trick-shuffling-oceans8-gif-10669532'
JUMP = 'https://tenor.com/view/excited-jump-goat-shelby-jumping-on-the-bed-gif-16335183'


"""==================Local Media=================="""
KRUVIT = './Media/kruvit.jpg'
KUSAIN = './Media/Adi.jpg'

IMALE = './Media/Imale.mp3'
BOOM = './Media/boom.mp3'

ADI = './Media/adi.mp3'
ADI_NC = './Media/adi_nc.mp3'
ADI_REMIX = './Media/adi_remix.mp3'
ADI_REMIX_NC = './Media/adi_remix_nc.mp3'
ADI_LIST = [ADI, ADI_NC, ADI_REMIX, ADI_REMIX_NC]

# in seconds
ADI_DURATION = {ADI: 31,
                ADI_NC: 21,
                ADI_REMIX: 62,
                ADI_REMIX_NC: 44}


"""==================Token=================="""
load_dotenv()
# Get the API token from the .env file.
DISCORD_TOKEN = getenv("DISCORD_TOKEN")

