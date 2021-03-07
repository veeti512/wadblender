# WAD Blender
Addon to import Tomb Raider Level Editor objects and animations into Blender and export them into Tomb Editor or Unity.

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
* **Materials**: "one texture per object" selects for each object its own textures and creates a new material; "texture pages" splits the wad texture map in 256x256 pages; "full texture map" uses the entire wad texture map. Only the first two options are compatible with Sprytile.
* **Import Animations**: import Lara and Movables animations as Blender actions and NLA strips.
* **Game Slot Names**: assign the proper names for objects and animations coming from different Tomb Raider games.
* **Scale**: if set to 512, one TRLE block (4 clicks) corresponds to 2 meters.
* **Batch Export Objects and Animations (FBX)**: save wad objects and animations in FBX file format.
* **Batch Export Objects (OBJ)**: save wad objects in OBJ file format.
* **Batch Export Additional Data (JSON)**: save a json file for each object. Each file include information such as state changes, speed and commands. It may be useful to generate a Unity state machine animation controller.
* **Install Libraries**: install Numpy and PIL python libraries. They enable additional texture mappings and Sprytile compatibility.

Notes:
* The addon is still in development, your work may get lost or not be compatible with TRLE at this stage
* Be careful when importing multiple wads into the same Blender workspace since name conflicts may occur.
* When importing a new wad, WADBlender checks if a texture with the same wad name has been already imported and use it instead of creating a new one.
* NLA strips may cause issues when exporting into FBX.

### Object Panel

This panel contains utilities for creating objects/materials from scratch:

* **Create Blank Texture Page**: creates a new 256x256 black png image and assign it as a material.
* **Add Texture Image**: import a png image and assign it to a material.
* **Create Layer**: creates vertex color layers to set shade, shine and opacity attributes.

### Edit Shine and Translucency

You can show the WADBlender entry in the N panel when in edit mode. Set the selection mode to face and select the polygons you want to edit. The shine values are from 0 (fully opaque) to 31 (maximum shine).

### Import Mixamo animations

* Go to mixamo.com and upload [this FBX file](https://drive.google.com/file/d/1A3sFUF__01j9FpYnK4CzJATJHfisIyTy/view?usp=sharing) as charater.
* Select the animation you want to import, and download it with default settings (30 fps, FBX with skin).
* From File -> Import select Mixamo to TRLE and choose the downloaded file. Be sure to have a Lara Full Model imported so that you can select LARA_RIG as the target RIG.
* From File -> Export select TRLE animation and choose a file name. If you overwrite an existing anim file, WADBlender will keep its commands, state changes, etc Be sure to select the correct action from the active actions list!
* [Video Tutorial](https://www.youtube.com/watch?v=ErSYyMgzUS4)

### Export animations

* It is possible to export animations in Tomb Editor .anim and WadMerger .trw file format.
* To export an animation, make sure that it is the active animation of the rig.
* Click on File->Export->TRLE Animation and be sure to select from the right menu the active action.

### Import Animations from other sources:
* WADBlender includes the [Blender Rig Retargeting Addon](https://github.com/nkeeline/Keemap-Blender-Rig-ReTargeting-Addon) that allows mapping motions of one rig to another.
* Few modifications were made for compatibility with WADBlender skeletons. There are also some additional options for inverting rotation angles and location coordinates.
* See [Tutorial](https://github.com/veeti512/wadblender/blob/master/docs/tutorial.md) for importing Tomb Raider Angel of Darkness Lara Animations.

### Sprytile:
* Sprytile gives artists tools in Blender that speed up crafting stylized textured low poly models that evoke the feel of that era in gaming.
* WAD Blender is compatible with Sprytile. WAD Blender appends to each object sprytile metadata. This metadata is used for features such as picking textures from one object face and assigning it to other faces.
* Download Sprytile from https://jeiel.itch.io/sprytile 
