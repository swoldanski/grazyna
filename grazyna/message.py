from .irc import User
from . import irc, log, config
from .threads import is_admin_con, waiting_events


class MessageController(object):

    command = ''
    prefix = ''
    user = None
    data = None

    NUMERIC_COMMANDS = {
        '005': 'start',
        '330': 'whois_account'  # I don't have idea where is in RFC
    }

    def __init__(self, data):
        self.prefix, self.command = data[0:2]
        self.data = data
        self.user = User(self.prefix)

    def execute_message(self):
        command = self.command
        command = self.NUMERIC_COMMANDS.get(command, command.lower())
        method = getattr(self, 'command_%s' % command, None)

        if method is not None:
            method()

    def command_join(self):
        channel = self.data[2]
        log.write(channel, '%s(%s)::JOIN' % (self.user.nick, self.user.prefix))

    def command_part(self):
        channel = self.data[2]
        if len(self.data) == 4:
            reason = self.data[3]
            log.write(channel, "%s::PART[%s]" % (self.user.nick, reason))
        else:
            log.write(channel, "%s::PART" % self.user.nick)

    def command_kick(self):
        channel, nick = self.data[2:4]
        log.write(channel, "%s KICK %s" % (self.user.nick, nick))

        if nick == config.nick:
            irc.join(channel)

    def command_error(self):
        pass

    def command_privmsg(self):
        channel, text = self.data[2:]
        log.write(channel, "<%s> %s" % (self.user.nick, text))
        waiting_events.put_nowait((
            "msg", self.user, {"chan": channel, "txt": text}
        ))

    def command_notice(self):
        self.command_privmsg()

    def command_start(self):
        if irc.ready:
            return

        irc.ready = True

        from .threads.func import ping
        ping.start()

        for channel in config.channels:
            irc.send('JOIN', channel)

        config.auth.auth()

    def command_whois_account(self):
        nick, account = self.data[3:5]

        if (is_admin_con.nick == nick
           and account in config.admin):
            is_admin_con.nick = None
            is_admin_con.set()
