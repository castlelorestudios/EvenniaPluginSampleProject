def send_multimedia(obj, player, type):
    sent = False
    if obj.attributes.has("image_url"):
        sent = True
        image_data = {"type":type}
        image_data["image_url"] = obj.attributes.get("image_url")
        if obj.attributes.has("image_map"):
            image_data["image_map"] = obj.attributes.get("image_map")
        player.msg(image=((), image_data))
    if obj.attributes.has("sound_url"):
        sent = True
        player.msg(sound=((),{"sound_url": obj.attributes.get("sound_url")}))
    return sent

def get_visible_things(contents, looker):
    return (con for con in contents if con != looker and con.access(looker, "view"))
