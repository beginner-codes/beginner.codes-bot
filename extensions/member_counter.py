import dippy


class MemberCounterExtension(dippy.Extension):
    client: dippy.Client
    log: dippy.Logging

    def __init__(self):
        super().__init__()
        self._last_count = 0

    @dippy.Extension.listener("ready")
    async def on_ready(self):
        if self._last_count == 0:
            self.log.info("Starting member counter")
            self._parse_counter()
            self._update_member_counter()

    def _parse_counter(self):
        channel = self.client.get_channel(968972011407826954)
        self._last_count = int(channel.name.replace(",", "").split()[-1])

    def _update_member_counter(self):
        self._schedule_update()
        self._run_update()

    def _run_update(self):
        self.client.loop.create_task(self._do_update())

    def _schedule_update(self):
        self.log.info("Scheduling next member count update")
        self.client.loop.call_later(90, self._update_member_counter)

    async def _do_update(self):
        channel = self.client.get_channel(968972011407826954)
        guild = channel.guild
        members = sum(not member.bot for member in guild.default_role.members)
        self.log.info(f"Updating counter {members:,} {self._last_count:,}")
        close_achievement = self._last_count // 250 < (members + 5) // 250
        new_members = members > self._last_count
        substantial_drop = members < self._last_count - 5
        if new_members or substantial_drop or close_achievement:
            await channel.edit(name=f"📊Members: {members:,}")
            self._last_count = members
