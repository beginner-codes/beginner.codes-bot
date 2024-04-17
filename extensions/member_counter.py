from math import floor

import dippy


class MemberCounterExtension(dippy.Extension):
    client: dippy.Client
    log: dippy.Logging

    def __init__(self):
        super().__init__()
        self._current_counter = ""

    @dippy.Extension.listener("ready")
    async def on_ready(self):
        if self._current_counter == "":
            self.log.info("Starting member counter")
            self._parse_counter()
            self._update_member_counter()

    def _parse_counter(self):
        channel = self.client.get_channel(968972011407826954)
        self._current_counter = channel.name.split()[-1]

    def _update_member_counter(self):
        self._schedule_update()
        self._run_update()

    def _run_update(self):
        self.client.loop.create_task(self._do_update())

    def _schedule_update(self):
        self.client.loop.call_later(90, self._update_member_counter)

    async def _do_update(self):
        channel = self.client.get_channel(968972011407826954)
        guild = channel.guild
        members = len(guild.default_role.members)
        members_k = floor(members / 100) / 10
        decimal_format = ".0" if members_k.is_integer() else ".1"
        members_counter = f"{members_k:{decimal_format}f}k"
        if members_counter != self._current_counter:
            self.log.info(f"Updating counter {members_k} {self._current_counter}")
            await channel.edit(name=f"📊Members: {members_counter}")
            self._current_counter = members_counter
