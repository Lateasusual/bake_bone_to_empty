# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Bake bones to Empty",
    "author" : "Lateasusual",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 1, 0),
    "location" : "",
    "warning" : "",
    "category" : "Animation"
}


from bpy.utils import register_class, unregister_class
from bpy.types import Panel, Operator
from bpy.props import *
import bpy


constraint_types = [
    ('NONE', "None", "Don't add constraints to the bones after baking"),
    ('COPY_TRANSFORMS', "Copy Transforms", "Add Copy Transforms constraints to affected bones"),
    ('DAMPED_TRACK', "Damped Track", "Add Damped Track constraints to affected bones")
]


class ARM_OT_BakeBonesToEmpties(Operator):
    bl_idname = 'armature.bake_bones_to_empty'
    bl_label = 'Bake bones to empties'

    frame_start: IntProperty(name="Start", default=1)
    frame_end: IntProperty(name="End", default=100)

    bake: BoolProperty(name="Bake animation", default=True)
    use_scene: BoolProperty(name="Use scene start/end", default=True)
    use_head: BoolProperty(name="Place at head", default=False)

    subcol_name: StringProperty(
        name="Collection Name", 
        description="Collection to dump baked empties into",
        default="Baked Empties"
    )

    bone_prefix: StringProperty(
        name="Prefix",
        description="Prefix for empty names (e.g. bake_Bone.001)",
        default="bake_"
    )

    constraint: EnumProperty(
        items=constraint_types,
        name="Constraint",
        description="Constraint type to add to bones"
    )

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.type == 'ARMATURE'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, 'bake')
        row.prop(self, 'use_scene')
        if self.bake and not self.use_scene:
            row = layout.row(align=True)
            row.prop(self, 'frame_start')
            row.prop(self, 'frame_end')
        layout.prop(self, 'use_head')
        layout.prop(self, 'subcol_name')
        layout.prop(self, 'bone_prefix')
        layout.prop(self, 'constraint')

    def execute(self, context):
        col = bpy.data.collections.new(self.subcol_name)
        context.collection.children.link(col)
        pairs = []
        for bone in context.selected_pose_bones_from_active_object:
            empty = bpy.data.objects.new(self.bone_prefix + bone.name, None)

            col.objects.link(empty)
            empty.parent = context.object
            empty.parent_bone = bone.name
            empty.parent_type = 'BONE'
            if self.use_head:
                empty.location.y -= bone.bone.length
            pairs.append((bone, empty))

        if self.bake:
            con = context.copy()
            con['selected_editable_objects'] = [p[1] for p in pairs]
            if self.use_scene:
                self.frame_start = context.scene.frame_start
                self.frame_end = context.scene.frame_end
            bpy.ops.nla.bake(
                con, 
                frame_start=self.frame_start, 
                frame_end=self.frame_end,
                clear_parents=True,
                visual_keying=True,
                bake_types={'OBJECT'}
            )

        if self.constraint != 'NONE':
            for bone, empty in pairs:
                con = bone.constraints.new(self.constraint)
                con.target = empty

        return {'FINISHED'}


classes = [
    ARM_OT_BakeBonesToEmpties
]

def register():
    for cls in classes:
        register_class(cls)

def unregister():
    for cls in classes:
        unregister_class(cls)
