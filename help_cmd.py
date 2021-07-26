import discord
from discord.ext import commands


class Help(commands.Cog):
    """Sends this help message"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['h'])
    async def help(self, ctx):
        """Shows all modules of that bot"""
        shoam, shoam_help, prefix, cog = '', '', '-', 'Music'

        emb = discord.Embed(title=f'{cog} - Commands',
                            color=discord.Color.blue())

        # getting commands from cog
        for command in self.bot.get_cog(cog).get_commands():
            if command.name == 'shoam':
                shoam, shoam_help = '||-shoam||', f'||{command.help}||'
                continue

            if not command.hidden:
                aliases = ', '.join(f'{prefix}{alias}' for alias in [command.name] + command.aliases)
                emb.add_field(name=aliases, value=command.help, inline=False)

        emb.add_field(name=shoam, value=shoam_help, inline=False)
        await ctx.send(embed=emb)
