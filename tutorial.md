How to import Lara AOD animation into Tomb Editor Wad Tool

1) Search the installation directory of TRAOD. In the Data/Maps directory
there are many files with CLZ extension. Let's take PARIS1.GMX.CLZ and copy
it on the TRAODAE directory

2) Drag the PARIS1.GMX.CLZ over the UnCLZ.exe icon in order to decompress it.
It will create a file named PARIS1.GMX in the same directory.

3) Drag the PARIS1.GMX over the unGMX.exe icon. This will create a folder
called PARIS1. Browse into that folder and find the file LARA.CAL and LARAD.CHR. Copy
them into the TRAODAE directory and rename LARAD.CHR to LARA.CHR.

4) Drag the LARA.CAL over the TRAODAE.exe icon. A window will pop up: say yes
to everything. It will create a new folder named LARA containing the model,textures
and animations. The animations are in the LARA_ANIMATIONS subfolder. Unfortunately
these FBXs cannot be imported into Blender since they are in ASCII format.

5) Open Autodesk FBX Converter 2013, click on Add FBX converter. Click on the
add button and select the animations you want to use. Let's convert the
LARA_KICKOVERKNIGHT.FBX file. Be sure that FBX 2013 is selected and that FBX Save
is binary. Click on convert on the bottom right. This will create a folder named
FBX 2013 inside the LARA_ANIMATIONS folder. Inside there are the converted FBX files.

6) Open Blender and import->TRLE Wad File -> Import: Lara Full model. You can uncheck
import animations. Once imported unhide the LARA collection.

7) From the import menu select import FBX. In the Transform->Scale option insert the
value 0.2. Select the animation file and click on Import FBX

8) Select both the LARA_RIG and the imported Armature RIG (hold shift to multiselect)
and go into pose mode

9) Press N and select the KeeMapRig tab. Click on the folder icon and select the
lara_aod_retarget.json file and click Accept. Click on Read In Bone Mapping File button.

10) Set the number of frames field to 150. Then, click on the Transfer Animation 
from Source to Destination.

11) Now the animation can be exported as an xml Wad Tool File. Click on 
File->Export->TRLE animation. From the action menu select the transferred action: LARA_RIGAction.
Choose a filename and click on export. If you overwrite an existing anim file it will
keep its state changes, commands, frame rate, etc.


UnCLZ.exe:
https://www.aspidetr.com/it/tools/aod-texture-editor/

unGMX.EXE:
https://core-design.com/community_aodgmxunpacker.html

TRAODAE:
https://core-design.com/community_aodanimationexporter.html

Autodesk FBX Converter 2013
https://www.autodesk.com/developer-network/platform-technologies/fbx-converter-archives