import os

lara_skin_names = ['HIPS', 'LEFT_THIGH', 'LEFT_SHIN', 'LEFT_FOOT',
                   'RIGHT_THIGH', 'RIGHT_SHIN', 'RIGHT_FOOT',
                   'TORSO', 'RIGHT_UPPER_ARM', 'RIGHT_FOREARM', 'RIGHT_HAND',
                   'LEFT_UPPER_ARM', 'LEFT_FOREARM', 'LEFT_HAND', 'HEAD']

lara_skin_joints_names = ['HIPS_JOINT', 'LEFT_HIP', 'LEFT_KNEE', 'LEFT_ANKLE',
                          'RIGHT_HIP', 'RIGHT_KNEE', 'RIGHT_ANKLE',
                          'PELVIS', 'RIGHT_SHOULDER', 'RIGHT_ELBOW', 'RIGHT_WRIST',
                          'LEFT_SHOULDER', 'LEFT_ELBOW', 'LEFT_WRIST', 'NECK']

movables2discard = {'LARA', 'PISTOLS_ANIM', 'UZI_ANIM', 'SHOTGUN_ANIM', 'CROSSBOW_ANIM', 'GRENADE_GUN_ANIM',
                    'SIXSHOOTER_ANIM', 'FLARE_ANIM', 'LARA_SKIN', 'LARA_SKIN_JOINTS', 'LARA_CROSSBOW_LASER',
                    'LARA_REVOLVER_LASER', 'LARA_HOLSTERS', 'LARA_HOLSTERS_PISTOLS', 'LARA_HOLSTERS_UZIS',
                    'LARA_HOLSTERS_SIXSHOOTER', 'CROWBAR_ANIM',
                    'TORCH_ANIM', 'LARA_SCREAM', 'AI_GUARD', 'AI_AMBUSH', 'AI_PATROL1', 'AI_MODIFY', 'AI_FOLLOW', 'AI_PATROL2', 'AI_X1', 'AI_X2',
                    'LARA_START_POS', 'KILL_ALL_TRIGGERS', 'TRIGGER_TRIGGERER', 'DARTS', 'DART_EMITTER', 'HOMING_DART_EMITTER',
                    'FLAME', 'FLAME_EMITTER', 'FLAME_EMITTER2', 'FLAME_EMITTER3', 'ROPE',
                    'FIREROPE', 'SMOKE_EMITTER_WHITE', 'SMOKE_EMITTER_BLACK', 'STEAM_EMITTER', 'EARTHQUAKE', 'BUBBLES', 'WATERFALLMIST',
                    'CAMERA_TARGET', 'VEHICLE_EXTRA_MVB'}


import xml.etree.ElementTree as ET


def get_partial_names(version):
    cur_script_path = os.path.dirname(os.path.realpath(__file__))
    filename = cur_script_path + '\\resources\\trcatalog.xml'
    tree = ET.parse(filename)
    root = tree.getroot()

    movables = {}
    statics = {}
    animations = {}
    states = {}

    for game in root:
        if game.attrib['id'] != version:
            continue

        for g in game:
            if g.tag == 'moveables':
                for mov in g:
                    movables[mov.attrib['id']] = mov.attrib['name']

            if g.tag == 'statics':
                for static in g:
                    statics[static.attrib['id']] = static.attrib['name']

            if g.tag == 'animations':
                for anim in g:
                    item_id = anim.attrib['item']

                    if item_id not in animations:
                        animations[item_id] = {}

                    animations[item_id][anim.attrib['id']] = anim.attrib['name']

            if g.tag == 'states':
                for state in g:
                    item_id = state.attrib['item']
                    if item_id not in states:
                        states[item_id] = {}
                    states[item_id][state.attrib['id']] = state.attrib['name']

    return movables, statics, animations, states


def get_names(ver):
    movables, statics, animations, states = get_partial_names(ver)

    for g in ['TR1', 'TR2', 'TR3', 'TR4', 'TR5', 'TR5Main']:
        if g == ver:
            break

        _, _, animations2, states2 = get_partial_names(g)

        for item, obj in animations2.items():
            if item in movables and item not in animations:
                animations[item] = {}
                for id, name in obj.items():
                    animations[item][id] = name
            elif item in movables and item in animations:
                for id, name in obj.items():
                    if id not in animations[item]:
                        animations[item][id] = name


        for item, obj in states2.items():
            if item in movables and item not in states:
                states[item] = {}
                for id, name in obj.items():
                    states[item][id] = name
            elif item in movables and item in states2:
                for id, name in obj.items():
                    if id not in states[item]:
                        states[item][id] = name


    return movables, statics, animations, states