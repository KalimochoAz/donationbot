import asyncio
import discord
import datetime
from dateutil import relativedelta

from discord.ext import commands


class SeasonConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.season_id = 0
        self.season_sleeper_task = bot.loop.create_task(self.next_season_sleeper())

    async def get_season_id(self):
        if not self.season_id:
            query = "SELECT id FROM seasons WHERE start < CURRENT_TIMESTAMP " \
                    "ORDER BY start DESC LIMIT 1;"
            fetch = await self.bot.pool.fetchrow(query)
            if not fetch:
                await self.new_season()
                return await self.get_season_id()

            self.season_id = fetch[0]
        return self.season_id

    @staticmethod
    def next_last_monday():
        return datetime.datetime.utcnow() + \
               relativedelta.relativedelta(day=31, weekday=relativedelta.MO(-1))

    async def new_season(self):
        query = "INSERT INTO seasons (start, finish) VALUES ($1, $2)"
        await self.bot.pool.execute(query, datetime.datetime.utcnow(), self.next_last_monday())
        self.season_id = await self.get_season_id()
        query = "INSERT INTO players (player_tag, donations, received, user_id, season_id) " \
                "SELECT player_tag, 0, 0, user_id, season_id+1 FROM players WHERE season_id=$1"
        await self.bot.pool.execute(query, await self.get_season_id())
        await self.update_fin_sic()

    async def update_fin_sic(self):
        query = "SELECT DISTINCT player_tag FROM players WHERE season_id=$1"
        fetch = await self.bot.pool.fetch(query, await self.get_season_id())
        data = []
        async for player in self.bot.coc.get_players((n[0] for n in fetch)):
            data.append({
                'player_tag': player.tag,
                'friend_in_need': player.achievements_dict['Friend in Need'].value,
                'sharing_is_caring': player.achievements_dict['Sharing is caring'].value
            })
        query = """UPDATE players SET friend_in_need = x.friend_in_need, 
                                      sharing_is_caring = x.sharing_is_caring 
                        FROM(
                            SELECT x.player_tag, x.friend_in_need, x.sharing_is_caring
                                FROM jsonb_to_recordset($1::jsonb)
                            AS x(player_tag TEXT, friend_in_need INTEGER, sharing_is_caring INTEGER)
                            )
                    AS x
                    WHERE players.player_tag = x.player_tag
                    AND players.season_id=$2
                """
        await self.bot.pool.execute(query, data, await self.get_season_id())

    async def next_season_sleeper(self):
        try:
            while not self.bot.is_closed():
                delta = datetime.datetime.utcnow() - self.next_last_monday()
                await asyncio.sleep(delta.total_seconds())
                self.season_id = 0
                await self.get_season_id()

        except asyncio.CancelledError:
            raise
        except (OSError, discord.ConnectionClosed):
            self.season_sleeper_task.cancel()
            self.season_sleeper_task = self.bot.loop.create_task(self.next_season_sleeper())

    @commands.command()
    @commands.is_owner()
    async def resetseason(self, ctx):
        prompt = await ctx.prompt('Are you sure?')
        if not prompt:
            return
        self.season_id = 0
        season_id = await self.get_season_id()
        if not season_id:
            return await ctx.confirm()
        prompt = await ctx.prompt('Current season found. '
                                  'Would you like to create a new one anyway?')
        if not prompt:
            return
        await self.new_season()
        self.season_id = 0
        await self.get_season_id()
        await ctx.confirm()

    @commands.command()
    @commands.is_owner()
    async def refreshfin(self, ctx):
        await self.update_fin_sic()
        await ctx.confirm()


def setup(bot):
    bot.add_cog(SeasonConfig(bot))