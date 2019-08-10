from datetime import datetime

from cogs.utils.formatters import readable_time


class DatabaseGuild:
    __slots__ = ('bot', 'guild_id', 'id', 'updates_channel_id', 'updates_toggle',
                 'auto_claim', 'donationboard_title', 'icon_url', 'donationboard_render')

    def __init__(self, *, guild_id, bot, record=None):
        self.guild_id = guild_id
        self.bot = bot

        if record:
            get = record.get
            self.id = get('id')
            self.updates_channel_id = get('updates_channel_id')
            self.updates_toggle = get('updates_toggle')
            self.auto_claim = get('auto_claim')
            self.donationboard_title = get('donationboard_title')
            self.icon_url = get('icon_url')
            self.donationboard_render = get('donationboard_render')
        else:
            self.updates_channel_id = None
            self.updates_toggle = False
            self.auto_claim = False

    @property
    def donationboard(self):
        return self.bot.get_channel(self.updates_channel_id)

    async def updates_messages(self):
        query = "SELECT id, message_id, guild_id, channel_id FROM messages WHERE guild_id = $1"
        fetch = await self.bot.pool.fetch(query, self.guild_id)
        return [DatabaseMessage(bot=self.bot, record=n) for n in fetch]


class DatabasePlayer:
    def __init__(self, *, bot, player_tag=None, record=None):
        self.bot = bot

        if record:
            get = record.get
            self.id = get('id')
            self.player_tag = get('player_tag')
            self.donations = get('donations')
            self.received = get('received')
            self.user_id = get('user_id')
        else:
            self.user_id = None
            self.player_tag = player_tag

    @property
    def owner(self):
        return self.bot.get_user(self.user_id)

    async def full_player(self):
        return await self.bot.coc.get_player(self.player_tag)


class DatabaseClan:
    def __init__(self, *, bot, clan_tag=None, record=None):
        self.bot = bot

        if record:
            get = record.get
            self.id = get('id')
            self.guild_id = get('guild_id')
            self.clan_tag = get('clan_tag')
            self.clan_name = get('clan_name')
            self.channel_id = get('channel_id')
            self.log_interval = get('log_interval')
            self.log_toggle = get('log_toggle')
        else:
            self.guild_id = None
            self.clan_tag = clan_tag

    @property
    def guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def channel(self):
        return self.bot.get_channel(self.channel_id)

    @property
    def interval_seconds(self):
        return self.log_interval.total_seconds()

    async def full_clan(self):
        return await self.bot.coc.get_clan(self.clan_tag)


class DatabaseMessage:
    def __init__(self, *, bot, record=None):
        self.bot = bot

        if record:
            get = record.get
            self.id = get('id')
            self.guild_id = get('guild_id')
            self.message_id = get('message_id')
            self.channel_id = get('channel_id')

        else:
            self.guild_id = None
            self.channel_id = None
            self.message_id = None

    @property
    def guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def channel(self):
        return self.bot.get_channel(self.channel_id)

    async def get_message(self):
        return await self.bot.donationboard.get_message(self.channel, self.message_id)


class DatabaseEvent:
    def __init__(self, *, bot, record=None):
        self.bot = bot

        if record:
            get = record.get
            self.id = get('id')
            self.player_tag = get('player_tag')
            self.player_name = get('player_name')
            self.clan_tag = get('clan_tag')
            self.donations = get('donations')
            self.received = get('received')
            self.time = get('time')

        else:
            self.time = None

    @property
    def readable_time(self):
        return readable_time((datetime.utcnow() - self.time).total_seconds())

    @property
    def delta_since(self):
        return datetime.utcnow() - self.time

