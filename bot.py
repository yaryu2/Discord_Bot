import asyncio
import itertools
import discord
import youtube_dl
from discord.ext import commands
from async_timeout import timeout
import  random
from Constants import *
from help_cmd import Help

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

now_playing_id = ''


def secs_to_hms(total_seconds: float) -> str:
    seconds = total_seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    if hour > 0:
        return "%dh %02dm %02ds" % (hour, minutes, seconds)
    elif minutes > 0:
        return "%02dm %02ds" % (minutes, seconds)
    else:
        return "%02ds" % seconds


class YTDLSource(discord.PCMVolumeTransformer):
    __slots__ = ('data', 'title', 'url', 'duration')

    def __init__(self, source, *, data=None, volume=0.5):
        super().__init__(source, volume)

        if data:
            self.data = data

            self.title = data.get('title')
            self.url = data.get('url')
            self.duration = secs_to_hms(data.get('duration'))

    @classmethod
    async def from_url(cls, url, loop=None, change='+3', tones=False, stream=False):
        import os
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)

        if not stream:
            f, e = os.path.splitext(filename)
            os.rename(filename, (filename := f'{f}.{songs_type.get(e, "webm")}'))
            os.system(f'nightcore {filename} {change} {["", "tones"][tones]} > out.mp3')
            os.remove(filename)
            filename = 'out.mp3'

        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @classmethod
    async def imale(cls):
        return cls(discord.FFmpegPCMAudio(IMALE, **ffmpeg_options), volume=1)

    @classmethod
    async def boom(cls):
        return cls(discord.FFmpegPCMAudio(BOOM, **ffmpeg_options), volume=1)

    @classmethod
    async def adi(cls, name, loop, **kwargs):
        path = f'./Media/{name.lower().replace(" ", "_")}.mp3'
        return cls(discord.FFmpegPCMAudio(path, **ffmpeg_options),
                   data={'title': name, 'url': path, 'duration': ADI_DURATION[path]})


class MusicPlayer:
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume', 'np')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(900):
                    item = await self.queue.get()
            except asyncio.TimeoutError:
                pass

            # if not isinstance(source, YTDLSource):
            #     # Source was probably a stream (not downloaded)
            #     # So we should regather to prevent stream expiration
            #     try:
            #         source = await YTDLSource.from_url(source, loop=self.bot.loop, stream=not self.bot.get_nightcore)
            #     except Exception as e:
            #         await self._channel.send(f'There was an error processing your song.\n'
            #                                  f'```css\n[{e}]\n```')
            #         continue

            func, *args, tones, stream = item
            source = await func(*args, tones=tones, stream=stream)

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))

            embed = Embed(title="Now playing",
                          description=f"[{source.title}]",
                          color=green)

            global now_playing_id
            if now_playing_id:
                msg = await self._channel.fetch_message(now_playing_id)
                await msg.delete()

            self.np = await self._channel.send(embed=embed)
            now_playing_id = self.np.id

            await self.next.wait()

            self.current = None


# noinspection PyTypeChecker,PyProtectedMember
class Music(commands.Cog):
    __slots__ = ('bot', 'players', 'nightcore')

    def __init__(self):
        self.bot = bot
        self.players = {}
        self.nightcore = False
        self.tones = False
        self.change = '+3'

    def stream(self):
        return not self.nightcore and not self.tones

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        return self.players.setdefault(ctx.guild.id, MusicPlayer(ctx))

    """-------------commands-------------"""

    @commands.command()
    async def shoam(self, ctx):
        """Announces the arrival of the gever and the horse. ילד הכרובית!🧜‍♀️"""
        if ctx.author.name != 'shoam':
            channel = discord.utils.get(ctx.guild.channels, name='general')
            await channel.send('ילד הכרובית 🧜‍♀️')
            await ctx.message.add_reaction('🧜‍♀️')
            await channel.send(file=discord.File(KRUVIT))

    @commands.command()
    async def adi(self, ctx):
        """Adds the best song ever in some variation to the top of the queue. יא כוסית שאת."""
        prev_nc = self.nightcore
        remix = 'remix' in ctx.message.content
        nc = 'nc' in ctx.message.content

        self.nightcore = nc

        player = self.get_player(ctx)
        name = ADI_LIST[2 * remix + nc]
        name = name[name.rfind('/') + 1: name.rfind('.')]
        name = name.replace('_', ' ').replace('a', 'A').replace('n', 'N').replace('r', 'R')
        player.queue._queue.insert(0, (YTDLSource.adi, name, self.bot.loop, not self.tones, not self.nightcore))

        self.nightcore = prev_nc

        if now_playing_id:
            await self.queue_info(ctx)

    @commands.command(name='nightcore', aliases=['nc'])
    async def nightcore_(self, ctx):
        """Play songs as a nightcore mode"""
        self.nightcore = not self.nightcore
        await ctx.send(embed=Embed(title='',
                                   description=f'Nightcore has been **{["disabled", "enabled"][self.nightcore]}.**',
                                   color=green))
        await ctx.message.add_reaction(f'{["🌞", "🌛"][self.nightcore]}')

    @commands.command()
    async def tones(self, ctx):
        """Play songs as a nightcore mode + Add a tones to the songs"""
        self.tones = not self.tones
        await ctx.send(embed=Embed(title='',
                                   description=f'Tones has been **{["disabled", "enabled"][self.tones]}.**',
                                   color=green))
        await ctx.message.add_reaction(f'{["🔕", "🎶"][self.tones]}')

    @commands.command()
    async def join(self, ctx):
        """Joins a voice channel"""
        if not ctx.author.voice:
            await ctx.send(embed=Embed(title='',
                                       description='You are not connected to a voice channel.',
                                       color=red))
            raise commands.CommandError('Author not connected to a voice channel.')

        channel = ctx.author.voice.channel

        if ctx.voice_client is None:
            await ctx.send(embed=Embed(title='',
                                       description=f'Joining channel **{channel.name}**.',
                                       color=green))
            await channel.connect()
            return await ctx.message.add_reaction('✅')

        if ctx.voice_client.channel != channel:
            await ctx.send(embed=Embed(title='',
                                       description=f'Moving to channel **{channel.name}.**',
                                       color=green))
            await ctx.voice_client.move_to(channel)
            return await ctx.message.add_reaction('✅')

        await ctx.send(embed=Embed(title='',
                                   description=f'Already connected to **{channel.name}.**',
                                   color=red))

    @commands.command(aliases=['leave', 'dc', 'stop'])
    async def disconnect(self, ctx):
        """Stops and disconnects the bot from voice"""
        if ctx.voice_client is not None:
            ctx.voice_client.stop()
            ctx.voice_client.play(source=await YTDLSource.imale())

            leave = await ctx.send(LEAVE_GIF)

            await asyncio.sleep(5.6)
            await leave.delete()
            ctx.voice_client.play(source=await YTDLSource.boom())

            await ctx.send(LEAVE_GIF_DANNY)
            await asyncio.sleep(3)

            await ctx.message.add_reaction('👋')
            await ctx.voice_client.disconnect()

    @disconnect.before_invoke
    async def reset_queue(self, ctx):
        """Reset queue"""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send(embed=NOT_CONNECTED_EMBED)

        player = self.get_player(ctx)
        player.queue._queue.clear()
        self.nightcore = False
        self.tones = False

    """-------------Music-------------"""

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, url='', send=True):
        """Play songs"""
        if url:
            async with ctx.typing():
                player = self.get_player(ctx)

                await player.queue.put((YTDLSource.from_url, url, self.bot.loop, self.tones, not self.nightcore))

                if send:
                    embed = Embed(title='', description=f'Queued [{url}].', color=green)
                    await ctx.send(embed=embed)

    @adi.before_invoke
    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                self.players = {}
                return await ctx.author.voice.channel.connect()

            await ctx.send(embed=Embed(title='',
                                       description="You are not connected to a voice channel.",
                                       color=red))
            raise commands.CommandError("Author not connected to a voice channel.")

    @commands.command(aliases=['stfu'])
    async def pause(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            if vc and vc.is_paused():
                return await ctx.send(embed=Embed(title='',
                                                  description='I am already paused :smiling_face_with_tear:',
                                                  color=red))

            return await ctx.send(embed=NOT_PLAYING_EMBED)

        vc.pause()
        await ctx.send(embed=Embed(title='',
                                   description='Paused ⏸️',
                                   color=green))
        await ctx.message.add_reaction(['⏸️', '👹'][ctx.invoked_with == 'stfu'])

    @commands.command(aliases=['keep_singing_mother_fucker', 'ksmf'])
    async def resume(self, ctx):
        """Resume the currently paused song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send(embed=NOT_CONNECTED_EMBED)

        if not vc.is_paused():
            return await ctx.send(embed=Embed(title='',
                                              description='I am not paused :smiling_face_with_tear:',
                                              color=red))

        vc.resume()
        await ctx.send(embed=Embed(title='',
                                   description='Resuming ⏯️',
                                   color=green))

        if ctx.invoked_with in ['keep_singing_mother_fucker', 'ksmf']:
            await ctx.message.add_reaction('✅')
            return await ctx.message.add_reaction('🥲')  # :smiling_face_with_tear:

        await ctx.message.add_reaction('⏯️')

    @commands.command(aliases=['vol', 'v'])
    async def volume(self, ctx, volume: int = -1):
        """Changes the player's volume."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send(embed=NOT_CONNECTED_EMBED)

        if not vc.is_playing():
            return await ctx.send(embed=NOT_PLAYING_EMBED)

        prev = ctx.voice_client.source.volume * 100
        if volume < 0:
            return await ctx.send(embed=Embed(title='',
                                              description=f'Volume is currently at **{prev:.0f}%**',
                                              color=blue))

        emoji = [['🔉', '🔊'][prev < volume], '🔇'][volume == 0]
        ctx.voice_client.source.volume = volume / 100

        await ctx.send(embed=Embed(title='',
                                   description=f"Changed volume to **{volume:.0f}%** {emoji}",
                                   color=green))

    @commands.command(aliases=['s'])
    async def skip(self, ctx):
        """Skip the song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send(embed=NOT_CONNECTED_EMBED)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()

    @commands.command()
    async def shuffle(self, ctx):
        """Shuffle the songs in queue."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send(embed=NOT_CONNECTED_EMBED)

        player = self.get_player(ctx)
        if player.queue.empty():
            return await ctx.send(embed=Embed(title='',
                                              description='Try doing this when there are songs in the queue.',
                                              color=red))

        await ctx.send(SHUFFLE)
        random.shuffle(player.queue._queue)
        await self.queue_info(ctx)

    @commands.command(aliases=['j'])
    async def jump(self, ctx, num):
        """Jump to a specific song number in the queue."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send(embed=NOT_CONNECTED_EMBED)

        await ctx.send(JUMP)

        player = self.get_player(ctx)
        for _ in range(min(int(num) - 1, player.queue.qsize())):
            del player.queue._queue[0]

        await ctx.message.add_reaction('🐐')
        vc.stop()

    @commands.command(aliases=['m'])
    async def move(self, ctx, index, *track_name):
        """Moves a song from one place to another in the queue"""
        if not type(index) == str or not index.isdigit() or int(index) < 1:
            return await ctx.send(embed=Embed(title='',
                                              description=f'Invalid index [{index}].',
                                              color=red))

        if not track_name:
            return await ctx.send(embed=Embed(title='',
                                              description=f'Track name must not be empty.',
                                              color=red))

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send(embed=NOT_CONNECTED_EMBED)

        track_name = ' '.join(track_name)

        player = self.get_player(ctx)
        for i, track in enumerate(player.queue._queue):
            if track[1] == track_name:
                temp = track
                del player.queue._queue[i]

                try:
                    player.queue._queue.insert(int(index) - 1, temp)

                except Exception as e:
                    print('oofie:', e)

                finally:
                    await self.queue_info(ctx)
                    break

        else:
            await ctx.send(embed=Embed(title='',
                                       description=f'`Could not find "{track_name}" in queue.`',
                                       color=green))

    @commands.command(aliases=['rm', 'rem'])
    async def remove(self, ctx, pos: int = None):
        """Removes specified song from queue"""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send(embed=NOT_CONNECTED_EMBED)

        player = self.get_player(ctx)
        if pos is None:
            removed = player.queue._queue.pop()
            return await ctx.send(embed=Embed(title='',
                                              description=f'Removed [{removed}].',
                                              color=green))

        try:
            s = player.queue._queue[pos - 1]
            del player.queue._queue[pos - 1]
            await ctx.send(embed=Embed(title='',
                                       description=f'Removed [{s[1]}]',
                                       color=green))
            await self.queue_info(ctx)

        except Exception as e:
            embed = Embed(title='',
                          description=f'Could not find a track for "{pos}"',
                          color=red)
            await ctx.send(embed=embed)
            print('oof :( ', e)

    @commands.command(name='queue', aliases=['q', 'playlist', 'que', 'queueueueueueue'], description='shows the queue')
    async def queue_info(self, ctx):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send(embed=NOT_CONNECTED_EMBED)

        player = self.get_player(ctx)
        if player.queue.empty() and not vc.is_playing():
            await ctx.send(embed=Embed(title='',
                                       description='No more songs to play 🥲🔫',
                                       color=red))
            return await ctx.message.add_reaction('🥲')

        # Grabs the songs in the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, int(len(player.queue._queue))))

        fmt = f"\n__Now Playing__:\n[{vc.source.title}]({vc.source.url}) | ` {vc.source.duration}`\n\n__Up Next:__\n"

        i = 0
        if not player.queue.empty():
            fmt = fmt + '\n'.join(f"`{(i := i + 1)}.` [{_[1]}]\n" for _ in upcoming) \
                  + f"\n**{len(upcoming)} songs in queue**"
        else:
            fmt = fmt + '**No more songs in queue.**'
        embed = Embed(title=f'Queue for {ctx.guild.name}', description=fmt, color=green)
        embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(aliases=['clear', 'clr'])
    async def queue_clear(self, ctx):
        """Reset the queue"""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send(embed=NOT_CONNECTED_EMBED)

        player = self.get_player(ctx)
        player.queue = asyncio.Queue()

        await self.queue_info(ctx)


"""==================main runner code start=================="""

bot = commands.Bot(command_prefix='-', help_command=None)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.event
async def on_message(message):
    if message.author.name == KRUVIT_NAME:
        await message.reply("shtok ya 🧜‍♀️ ילד כרובית")
        await message.add_reaction('🧜‍♀️')
        await message.channel.send(file=discord.File(KRUVIT))

    if message.content == 'כוסיין בולט':
        await message.add_reaction('👧')
        await message.channel.send(file=discord.File(KUSAIN))

    await bot.process_commands(message)


bot.add_cog(Music())
bot.add_cog(Help(bot))
bot.run(DISCORD_TOKEN)


# TODO: find out how to load on a server or something
# TODO: proper documentation, placing, kruvit-ness
# TODO: check that not stupid
