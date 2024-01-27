# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 13:38:47 2019

@author: AsteriskAmpersand
"""

bl_info = {
    "name": "MHW Mod3 Model Importer",
    "description": "Import-Export Monster Hunter World mod3 files",
    "author": "AsteriskAmpersand (Code) & CrazyT (Structure), newvoid7 updated",
    "version": (3, 0, 0),
    "blender": (3, 20, 0),   # required by new blender
    "location": "File > Import-Export",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Import-Export",
}
 
import bpy
from bpy_extras.io_utils import (
    ImportHelper, 
    ExportHelper,
)
from bpy.props import (
    StringProperty, 
    BoolProperty, 
    CollectionProperty, 
    EnumProperty,
    FloatProperty,
)
from bpy.types import (
    Operator, 
    OperatorFileListElement,
)

from .operators.mod3properties import symmetricPair
from .mod3 import Mod3ImporterLayer as Mod3IL
from .mod3 import Mod3ExporterLayer as Mod3EL
from .blender import BlenderMod3Importer as Api
from .blender import BlenderSupressor
from .common import FileLike as FL


class Context():
    def __init__(self, path, meshes, armature):
        self.path = path
        self.meshes = meshes
        self.armature = armature
        self.setDefaults = False

class ImportMOD3(Operator, ImportHelper):
    bl_idname = "import_mesh.mod3"
    bl_description = 'Import from MHW MOD3 file format (.mod3)'
    bl_label = 'Import MOD3'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}

    filename_ext = ".mod3"
    
    filter_glob: StringProperty(
        default="*.mod3", 
        options={'HIDDEN'}, 
        maxlen=255
    )
    files: CollectionProperty(
        name="File Path",
        type=OperatorFileListElement,
    )
    directory: StringProperty(
        subtype='DIR_PATH',
    )
    
    global_scale: FloatProperty(
        name="Scale",
        soft_min=0.001, soft_max=1000.0,
        min=1e-6, max=1e6,
        default=1.0,
    )
    clear_scene: BoolProperty(
        name = "Clear scene before import.",
        description = "Clears all contents before importing",
        default = True)
    maximize_clipping: BoolProperty(
        name = "Maximizes clipping distance.",
        description = "Maximizes clipping distance to be able to see all of the model at once.",
        default = True)
    high_lod: BoolProperty(
        name = "Only import the highest LOD part.",
        description = "Skip meshparts with low level of detail.",
        default = True)
    import_header: BoolProperty(
        name = "Import File Header.",
        description = "Imports file headers as scene properties.",
        default = True)
    import_meshparts: BoolProperty(
        name = "Import Meshparts.",
        description = "Imports mesh parts as meshes.",
        default = True)
    import_textures: BoolProperty(
        name = "Import Textures.",
        description = "Imports texture as specified by mrl3.",
        default = True)
    import_materials: BoolProperty(
        name = "Import Materials.",
        description = "Imports maps as materials as specified by mrl3.",
        default = False)
    omit_empty: BoolProperty(
        name = "Omit Unused Weights.",
        description = "Omit weights not in any Bounding Box.",
        default = False)
    load_group_functions: BoolProperty(
        name = "Load Bounding Boxes.",
        description = "Loads the mod3 as bounding boxes.",
        default = False,
        )
    texture_path: StringProperty(
        name = "Texture Source",
        description = "Root directory for the MRL3 (Native PC if importing from a chunk).",
        default = "")
    import_skeleton: EnumProperty(
        name = "Import Skeleton.",
        description = "Imports the skeleton as an armature.",
        items = [("None","Don't Import","Does not import the skeleton.",0),
                  ("EmptyTree","Empty Tree","Import the skeleton as a tree of empties",1),
                  ("Armature","Animation Armature","Import the skeleton as a blender armature",2),
                  ],
        default = "EmptyTree")
    weight_format: EnumProperty(
        name = "Weight Format",
        description = "Preserves capcom scheme of having repeated weights and negative weights by having multiple weight groups for each bone.",
        items = [("Group","Standard","Weights under the same bone are grouped, negative weights are dropped",0),
                 ("Signed","Signed","Weights under the same bone are grouped, negative weights are kept",1),
                  ("Split","Split Weight Notation","Mirrors the Mod3 separation of the same weight",2),
                  ("Slash","Split-Slash Notation","As split weight but also conserves weight order",3),
                  ],
        default = "Group")
    
    def draw(self, context):
        layout = self.layout
        layout.label(text='Options')
        box = layout.box()
        box.label(text='General')
        box.prop(self, "clear_scene")
        box.prop(self, "maximize_clipping")
        box.prop(self, "high_lod")
        box.prop(self, "import_header")
        box.prop(self, "import_meshparts")
        box.prop(self, "import_textures")
        box.prop(self, "import_materials")
        box.prop(self, "omit_empty")
        box.prop(self, "load_group_functions")
        box.prop(self, "texture_path")
        box.prop(self, "import_skeleton")
        box.prop(self, "weight_format")

    def execute(self,context):
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        bpy.ops.object.select_all(action='DESELECT')
        Mod3File = FL.FileLike(open(self.filepath,'rb').read())
        BApi = Api.BlenderImporterAPI()
        options = self.parseOptions()
        blenderContext = Context(self.filepath,{},None)
        with BlenderSupressor.SupressBlenderOps():
            Mod3IL.Mod3ToModel(Mod3File, BApi, options).execute(blenderContext)
            bpy.ops.object.select_all(action='DESELECT')
        #bpy.ops.object.mode_set(mode='OBJECT')
        #bpy.context.area.type = 'INFO'
        return {'FINISHED'}

    def parseOptions(self):
        options = {}
        if self.clear_scene:
            options["Clear"]=True
        if self.maximize_clipping:
            options["Max Clip"]=True
        if self.high_lod:
            options["High LOD"]=True
        if self.import_header:
            options["Scene Header"]=True
        if self.import_skeleton != "None":
            options["Skeleton"]=self.import_skeleton
        if self.import_meshparts:
            options["Mesh Parts"]=True
        if self.high_lod:
            options["Only Highest LOD"]=True
        if self.import_textures:
            options["Import Textures"]=self.texture_path
        if self.import_materials:
            options["Import Materials"]=self.texture_path
        if self.omit_empty:
            options["Omit Unused Groups"]=True
        if self.load_group_functions:
            options["Load Groups and Functions"]=True
        options["Split Weights"]=self.weight_format
        return options

class ExportMOD3(Operator, ExportHelper):
    bl_idname = "custom_export.export_mhw_mod3"
    bl_label = "Save MHW MOD3 file (.mod3)"
    bl_options = {'REGISTER', 'PRESET', 'UNDO'}
 
    # ImportHelper mixin class uses this
    filename_ext = ".mod3"
    filter_glob = StringProperty(default="*.mod3", options={'HIDDEN'}, maxlen=255)

    split_normals = BoolProperty(
        name = "Use Custom Normals",
        description = "Use split/custom normals instead of Blender autogenerated normals.",
        default = True)
    highest_lod = BoolProperty(
        name = "Set Meshparts to Highest LOD",
        description = "Overwrites all meshparts' explicit LODs to the highest LOD.",
        default = True)
    coerce_fourth = BoolProperty(
        name = "Coerce 4th Negative Weight",
        description = "Forces non-explicit 4 weight vertices into a 4 weight blocktype.",
        default = True)
    export_hidden = BoolProperty(
        name = "Export Hidden Meshes",
        description = "Also exports hidden meshes.",
        default = True            
        )
    export_bounds = EnumProperty(
        name = "Export Mesh Bounding Box",
        description = "Overrides the file bounding boxes.",
        items= [("Calculate","Calculate","Recalculates a box for each mesh",0),
                ("Explicit","Explicit","Exports Lattices as Bounding Boxes.",1)                
                ],
        default = "Calculate",
        )
    errorItems = [("Ignore","Ignore","Will not log warnings. Catastrophical errors will still break the process.",0),
                  ("Warning","Warning","Will be logged as a warning. This are displayed in the console. (Window > Toggle_System_Console)",1),
                  ("Error","Error","Will stop the exporting process. An error will be displayed and the log will show details. (Window > Toggle_System_Console)",2),
                  ]
    levelProperties = ["propertyLevel","blocktypeLevel","loopLevel","uvLevel","colourLevel","weightLevel","weightCountLevel"]
    levelNames = ["Property Error Level", "Blocktype Error Level", "Loops Error Level", "UV Error Level", "Colour Error Level", "Weighting Error Level", "Weight Count Error Level"]
    levelDescription = ["Missing and Duplicated Header Properties",
                        "Conflicting Blocktype Declarations",
                        "Redundant, Mismatched and Missing Normals",
                        "UV Map Incompatibilities",
                        "Colour Map Incompatibilities",
                        "Vertex Weight Groups Irregularities",
                        "Weight Count Errors"]
    levelDefaults = ["Warning","Error","Ignore","Error","Ignore","Warning","Warning","Error"]
    propString = """EnumProperty(
                    name = name,
                    description = desc,
                    items = errorItems,
                    default = pred,                
                    )"""
    for prop,name,desc,pred in zip(levelProperties, levelNames, levelDescription, levelDefaults):
        exec("%s = %s"%(prop, propString))

    def execute(self,context):
        self.cleanScene(context)
        BApi = Api.BlenderExporterAPI()
        with BlenderSupressor.SupressBlenderOps():
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except:
                pass
            bpy.ops.object.select_all(action='DESELECT')
            for obj in bpy.context.scene.objects:
                obj.select = obj.type == "MESH"
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            bpy.ops.object.select_all(action='DESELECT')

        options = self.parseOptions()
        Mod3EL.ModelToMod3(BApi, options).execute(self.properties.filepath)
        with BlenderSupressor.SupressBlenderOps():
            bpy.ops.object.select_all(action='DESELECT')
            for ob in bpy.context.selected_objects:
                ob.select = False
        #bpy.ops.object.mode_set(mode='OBJECT')
        #bpy.context.area.type = 'INFO'
        return {'FINISHED'}

    @staticmethod
    def cleanScene(context):
        data = set(bpy.data.objects)
        scene = set(bpy.context.scene.objects)
        for obj in data.difference(scene):
            bpy.data.objects.remove(obj)    

    def parseOptions(self):
        options = {
                "lod":self.highest_lod,
                "levels":{prop:self.__getattribute__(prop) for prop in self.levelProperties},
                "splitnormals":self.split_normals,
                "coerce":self.coerce_fourth,
                "hidden":self.export_hidden,
                "boundingbox":self.export_bounds,
                }        
        return options
    

def menu_func_import(self, context):
    self.layout.operator(ImportMOD3.bl_idname, text="MHW MOD3 (.mod3)")
    

def menu_func_export(self, context):
    self.layout.operator(ExportMOD3.bl_idname, text="MHW MOD3 (.mod3)")

def register():
    bpy.utils.register_class(ImportMOD3)
    bpy.utils.register_class(ExportMOD3)    
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.Object.MHW_Symmetric_Pair = symmetricPair
    

def unregister():
    del bpy.types.Object.MHW_Symmetric_Pair
    bpy.utils.unregister_class(ImportMOD3)
    bpy.utils.unregister_class(ExportMOD3)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    
    #del bpy.types.Object.MHWSkeleton

if __name__ == "__main__":
    register()
