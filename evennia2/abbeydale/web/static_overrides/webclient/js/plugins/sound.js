let sound_plugin = (function () {

    var onSound = function (args, kwargs){
        console.log("onSound: args=", args, "; kwargs=", kwargs);
        const sound_url = kwargs['sound_url'];
        const msgtype = kwargs["type"];
        const content = "<audio src='" + sound_url + "' autoplay='autoplay'>";
        plugins['splithandler'].onContent(content, msgtype)
        return true;
    }

    //
    // Mandatory plugin init function
    var init = function () {
        console.log('Sound plugin initialized');
        
    }

    return {
        init: init,
        onSound: onSound,
    }
})();
plugin_handler.add('sound', sound_plugin);
