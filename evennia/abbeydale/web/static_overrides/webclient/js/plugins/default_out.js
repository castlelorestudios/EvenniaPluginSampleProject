/*
 *
 * Evennia Webclient default outputs plugin
 *
 */
let defaultout_plugin = (function () {

    //
    // By default add all unclaimed onText messages to the #messagewindow <div> and scroll
    var onText = function (args, kwargs) {
        const msgtype = kwargs["type"];
        plugins['splithandler'].onContent(args[0], msgtype)
        return true;
    }

    //
    // By default just show the prompt.
    var onPrompt = function (args, kwargs) {
        // show prompt
        $('#prompt')
            .addClass("out")
            .html(args[0]);

        return true;
    }

    //
    // By default just show an error for the Unhandled Event.
    var onUnknownCmd = function (cmdname, args, kwargs) {
        var mwin = $("#messagewindow");
        mwin.append(
            "<div class='msg err'>"
            + "Error or Unhandled event:<br>"
            + cmdname + ", "
            + JSON.stringify(args) + ", "
            + JSON.stringify(kwargs) + "<p></div>");
        mwin.scrollTop(mwin[0].scrollHeight);
        console.log("Error or Unhandled event:" + cmdname + ", " + JSON.stringify(args) + ", " + JSON.stringify(kwargs))
        return true;
    }

    //
    // Mandatory plugin init function
    var init = function () {
        console.log('DefaultOut initialized');
        
    }

    return {
        init: init,
        onText: onText,
        onPrompt: onPrompt,
        onUnknownCmd: onUnknownCmd,
    }
})();
plugin_handler.add('defaultout', defaultout_plugin);
