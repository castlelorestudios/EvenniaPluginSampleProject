from evennia.commands.default.unloggedin import CmdUnconnectedLook as DefaultCmdUnconnectedLook

class CmdUnconnectedLook(DefaultCmdUnconnectedLook):
    def func(self):
        super(CmdUnconnectedLook, self).func()
        self.caller.msg(image=([],{
            "type": "background",
            "image_url": "/static/webclient/media/apple.png",
            "image_map": """
                <map name="connect_guest" id="connect_guest">
                    <area alt="Connect as guest" title="" href="#" data-command="connect guest" shape="circle" coords="145,150,110" />
                    <area alt="Connect as aaa" title="" href="#" data-command="connect aaa aaa" shape="circle" coords="250,50,55" />
                    <area alt="build the world" title="" href="#" data-command="@batchcommand world.init" shape="circle" coords="250,200,55" />
                </map>
            """
        }))
