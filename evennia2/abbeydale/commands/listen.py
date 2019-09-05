from evennia import Command
#from utils import send_multimedia

class Listen(Command):
    """
    Play a sound file attached to an object
    """
    key = "listen"
    def parse(self):
        if not self.args:
            self.target = self.caller.location
        else:
            self.target = self.caller.search(self.args)
        self.target_string = self.args.strip()
    def func(self):
        caller = self.caller
        if not self.target or self.target_string == "here":
            self.target = caller.location
        if self.target.attributes.has("sound_url"):
            caller.msg(sound=([],{"sound_url": self.target.attributes.get("sound_url")}))
        else:
            caller.msg("Nothing special.")
