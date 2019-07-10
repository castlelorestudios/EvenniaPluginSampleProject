from evennia.commands.default.general import CmdLook as DefaultCmdLook
from utils import send_multimedia

class Look(DefaultCmdLook):
    def func(self):
        super(Look, self).func()
        print('look')
        caller = self.caller
        if not self.args:
            target = caller.location
            if not target:
                print('no location')
                return
        else:
            target = caller.search(self.args)
            if not target:
                print('no target')
                return
        type = "foreground" if target != caller.location else "background"
        send_multimedia(target, caller, type)

