KEY_ACTIONS={"left":"move_left","right":"move_right","up":"rotate_cw","z":"rotate_ccw","down":"soft_drop","space":"hard_drop","c":"hold"}
def action_for_key(name: str):
    return KEY_ACTIONS.get(name.lower())
