// vim: expandtab shiftwidth=4 ts=4 ai si cindent
// indentexpr
"use strict";


let image_plugin = (function () {
    var onImage = function (args, kwargs){
        //console.log("onImage: args=", args, "; kwargs=", kwargs);
        const msgtype = kwargs["type"];
        const image_url = kwargs['image_url'];    
        const image_map_text = kwargs['image_map'];
        if(image_map_text){
            //console.log("image_map_text: " + image_map_text);
            const image_map = $($.parseHTML(image_map_text)).filter("map")[0];
            const image_text = "<img src='" + image_url + "' usemap='#" + image_map.name + "'>"
            plugins['splithandler'].onContent('<span>'+image_map_text+image_text+'</span>', msgtype)
            $('img[usemap]').rwdImageMaps();
            const added_image_map = $('#'+image_map.name)[0];
            for (var i = 0; i < added_image_map.children.length; i++) {
                const e = added_image_map.children[i];
                e.onclick = function(event){
                    const command = event.target.dataset.command;
                    Evennia.msg("text", [command], {});
                    event.preventDefault();
                }
            }
        }
        else
        {
            plugins['splithandler'].onContent("<img src='" + image_url + "'>", msgtype)
        }
        //var scrollHeight = mwin.parent().parent().prop("scrollHeight");
        //mwin.parent().parent().animate({ scrollTop: scrollHeight }, 0);
        return true;
    }

    //
    // Mandatory plugin init function
    var init = function () {
        console.log('Image plugin initialized');
        
    }

    return {
        init: init,
        onImage: onImage,
    }
})();
plugin_handler.add('image', image_plugin);


