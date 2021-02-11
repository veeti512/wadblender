# WAD Blender
Addon to import Tomb Raider Level Editor objects and animations into Blender and export them into Wad Tool or Unity.

## Download and Install
* Click on the green Code button and download zip;
* Open Blender and from the edit menu select Preferences;
* Select the Addons tab and click on Install... select the downloaded zip file and click on the WAD Blender checkbox.
* When updating, it may happen that blender python cache does not update. In that case, locate the addon folder (it is inside blender\2.90\scripts\addons\wadblender ) and delete the __pycache__ folder.

## Usage

### Import WAD
From File -> Import click on TRLE Wad File (.wad).

Options: 
* **Import Lara Full Model**: Import Lara Meshes including skin, skin joints and skeleton.
* **Import All Movables**: Import all movables objects.
* **Import All Statics**: Import all static objects. Light information is stored as vertex painting.
* **Import Everything**: Import all the three above. It may be slow since a wad file usually includes a lot of objects and animations.
* **Discard placeholders**: when importing movables, there are objects such as AI and emitters that are represented with a placeholder mesh (e.g. lara thigh or a red/yellow piramid).
* **Single object**: first you have to select a wad file, then click on "Choose Object" to see a list of objects inside the wad. Select the one you would like to import.
* **Discard Shine and Translucency**: in order to render these properties and import them into Tomb Editor, WADBlender needs to generate 64 materials since there are 32 shine values and 2 translucency values (on off). This is because the same texture image may be used with different shine/translucency values. This option allows for creating a single material fully opaque.
* **Flip Normals**: if you uncheck this, faces are inverted when exporting to Unity or 3D apps with backface culling enabled. If Flip Normals is checked and you would like to import the obj into Tomb Editor, you have to check the option "invert faces" on Wad Tool obj import dialog.
* **Import Animations**: import Lara and Movables animations as Blender actions and NLA strips.
* **Scale**: if set to 512, one TRLE block (4 clicks) corresponds to 2 meters.
* **Batch Export Objects and Animations (FBX)**: save wad objects and animations in FBX file format.
* **Batch Export Objects (OBJ)**: save wad objects in FBX file format.
* **Batch Export Additional Data (JSON)**: save a json file for each object. Each file include information such as state changes, speed and commands. It may be useful to generate a Unity state machine animation controller.

Notes:
* Be careful when importing multiple wads into the same Blender workspace since name conflicts may occur.
* When importing a new wad, WADBlender checks if a texture with the same wad name has been already imported and use it instead of creating a new one.
* NLA strips may cause issues when exporting into FBX.

### Edit Shine and Translucency

You can show the WADBlender entry in the N panel when in edit mode. Set the selection mode to face and select the polygons you want to edit. The shine values are from 0 (fully opaque) to 31 (maximum shine).
[Video tutorial](https://www.youtube.com/watch?v=hQ1DtBUQkSg)

### Import Mixamo animations

* Go to mixamo.com and upload [this FBX file](https://drive.google.com/file/d/1fcfc7URO3I4XuOO9_fDoMsNhYTH8sDV6/view?usp=sharing) as charater.
* Select the animation you want to import, and download it with default settings (30 fps, FBX with skin).
* From File -> Import select Mixamo to TRLE and choose the downloaded file. Be sure to have a Lara Full Model imported so that you can select it as the target RIG.
* From File -> Export select TRLE animation and choose a file name. If you overwrite an existing anim file, WADBlender will keep its commands, state changes, etc Be sure to select the correct action from the active actions list!
* [Video Tutorial](https://www.youtube.com/watch?v=ErSYyMgzUS4)

### Import Animations from other sources:
* WADBlender includes the [Blender Rig Retargeting Addon](https://github.com/nkeeline/Keemap-Blender-Rig-ReTargeting-Addon) that allows mapping motions of one rig to another.
* Few modifications were made for compatibility with WADBlender skeletons. There are also some additional options for inverting rotation angles and location coordinates.
* See [Tutorial](https://github.com/veeti512/wadblender/blob/master/tutorial.md) for importing Tomb Raider Angel of Darkness Animations.
