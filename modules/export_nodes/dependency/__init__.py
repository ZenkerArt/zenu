import json
import os.path
import re
import shutil
from enum import Enum, auto
from hashlib import sha1
from typing import Any

import bpy

from ..nodes import BaseNode
from ..sockets.armature_socket import ArmatureSocketResponse
from ..utils import activate_animation


def make_serializable(obj):
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_serializable(v) for v in obj]
    elif hasattr(obj, "name"):
        return obj.name  # Blender-friendly
    elif isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    else:
        return str(obj)  # fallback


def normalize_meta(meta):
    return sha1(json.dumps(make_serializable(meta), sort_keys=True).encode()).hexdigest()


def safe_name(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


class DepType(Enum):
    ANIMATION = auto()
    SOUND = auto()


class Dependency:
    users: set[bpy.types.Node]
    meta_per_node: dict[bpy.types.Node, dict[str, any]]

    def __init__(self, dep_type: DepType, resource: Any, node: bpy.types.Node, meta: dict[str, any] = None):
        self.type = dep_type
        self.resource = resource
        self.node = node
        self.meta = meta or {}
        self.users = set()

    def __repr__(self):
        name = None

        if hasattr(self.resource, 'name'):
            name = self.resource.name

        return f'<Dependency type={self.type.name} {name=}>'

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return (
                self.type == other.type and
                self.resource is other.resource
        )

    @property
    def meta_hash(self):
        return normalize_meta(self.meta)

    @property
    def key(self):
        return self.type, id(self.resource), self.meta_hash


class DependencyCollection:
    _deps: dict[Any, Dependency]

    def __init__(self):
        self._deps = {}

    def add_dep(self, dep: Dependency | list[Dependency]):
        if isinstance(dep, list):
            for d in dep:
                self.add_dep(d)
            return

        key = dep.key

        if key not in self._deps:
            dep.users = set()
            self._deps[key] = dep

        d = self._deps[key]
        d.users.add(dep.node)

    def get_deps(self):
        return tuple(self._deps.values())

    def get_by_node(self, node: BaseNode):
        deps: list[Dependency] = []

        for dep in self._deps.values():
            if node in dep.users:
                deps.append(dep)
        return deps


class DependencyExporter:
    def __init__(self, folder: str, deps: DependencyCollection):
        self._folder = folder
        self._deps = deps

    @staticmethod
    def get_slot(action: bpy.types.Action, slot_name: str):
        for sl in action.slots:
            if sl.name_display == slot_name:
                return sl

        return None

    def _export_animation(self, dep: Dependency):
        path = self.get_assets_path(dep)
        print(f"[ANIMATION] → {path}")

        armatures: list[ArmatureSocketResponse] = dep.meta.get('armatures')
        action: bpy.types.Action = dep.resource

        activate_animation(action, armatures)

        bpy.ops.export_scene.gltf(
            filepath=f'{path}.glb',
            use_selection=True,
            export_animation_mode='ACTIVE_ACTIONS',
            export_anim_scene_split_object=False,
            export_nla_strips_merged_animation_name=self.get_name(dep),
            export_image_format='NONE',
            use_renderable=False,
            export_reset_pose_bones=False,
            export_rest_position_armature=False,
            export_vertex_color='NONE',
            export_all_vertex_colors=False,
        )

        import bpy
        import numpy as np

        # ======================
        # SETTINGS
        # ======================
        STEPS = 32
        EMISSION_MAX = 4.0
        OUTPUT_FILE = "//tone_curve_rgb.csv"

        scene = bpy.context.scene
        scene.render.engine = 'CYCLES'

        # ======================
        # CLEAN SCENE
        # ======================
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

        # ======================
        # CAMERA
        # ======================
        bpy.ops.object.camera_add(location=(0, 0, 1))
        cam = bpy.context.object
        cam.rotation_euler = (0, 0, 0)
        scene.camera = cam

        # ======================
        # PLANE
        # ======================
        bpy.ops.mesh.primitive_plane_add(size=2)
        plane = bpy.context.object

        # ======================
        # MATERIAL (Emission)
        # ======================
        mat = bpy.data.materials.new("EmissionMat")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        emission = nodes.new("ShaderNodeEmission")
        output = nodes.new("ShaderNodeOutputMaterial")

        links.new(emission.outputs[0], output.inputs[0])

        plane.data.materials.append(mat)

        # ======================
        # COMPOSITOR (Viewer)
        # ======================
        # tree = scene.node_tree
        # tree.nodes.clear()

        # rlayers = tree.nodes.new("CompositorNodeRLayers")
        # viewer = tree.nodes.new("CompositorNodeViewer")

        # tree.links.new(rlayers.outputs["Image"], viewer.inputs["Image"])

        # ======================
        # READ VIEWER IMAGE
        # ======================
        def get_viewer_pixel():
            img = bpy.data.images['Render Result']
            if not img:
                raise RuntimeError("Viewer Node image not found")

            w, h = img.size
            print(w, h)
            if w == 0 or h == 0:
                raise RuntimeError("Viewer image not ready")

            pixels = np.array(img.pixels[:])

            x = w // 2
            y = h // 2

            i = (y * w + x) * 4

            return pixels[i], pixels[i + 1], pixels[i + 2]

        # ======================
        # RENDER LOOP
        # ======================
        results = []

        for i in range(STEPS + 1):
            t = i / STEPS
            strength = t * EMISSION_MAX

            emission.inputs["Strength"].default_value = strength
            emission.inputs["Color"].default_value = (1, 1, 1, 1)

            bpy.ops.render.render(write_still=False)

            try:
                r, g, b = get_viewer_pixel()
            except Exception as e:
                print("Retrying viewer read:", e)
                bpy.context.view_layer.update()
                r, g, b = get_viewer_pixel()

            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

            print(f"{strength:.3f} -> R:{r:.4f} G:{g:.4f} B:{b:.4f} L:{lum:.4f}")

            results.append((strength, r, g, b, lum))

        # ======================
        # SAVE CSV
        # ======================
        path = bpy.path.abspath(OUTPUT_FILE)

        with open(path, "w") as f:
            f.write("input,R,G,B,luminance\n")
            for row in results:
                f.write(",".join(map(str, row)) + "\n")

        print("DONE →", path)

        return {
            'type': dep.type.name,
            'path': self.get_relative_path(f'{path}.glb')
        }

    def _export_sound(self, dep: Dependency):
        path = self.get_assets_path(dep)
        print(f"[SOUND] → {path}")

        return {
            'type': dep.type.name,
            'path': None
        }

    def get_name(self, dep: Dependency):
        name = getattr(dep.resource, "name", None)
        base = f"{dep.type.name}_{dep.meta_hash[:6]}_{name or id(dep.resource)}"

        return safe_name(base)

    def get_path(self, dep: Dependency):
        return os.path.join(self._folder, self.get_name(dep))

    def get_assets_path(self, dep: Dependency):
        folder = os.path.join(self._folder, 'assets')

        return os.path.join(folder, self.get_name(dep))

    def get_relative_path(self, path: str):
        return os.path.relpath(path, self._folder)

    def save_config(self, data: str):
        with open(os.path.join(self._folder, 'mainfest.json'), mode='w') as fs:
            fs.write(data)

    def export(self):
        folder = os.path.join(self._folder, 'assets')
        result = {}
        if os.path.exists(folder):
            shutil.rmtree(folder)

        os.mkdir(folder)

        handlers = {
            DepType.ANIMATION: self._export_animation,
            DepType.SOUND: self._export_sound,
        }

        for dep in self._deps.get_deps():
            if not dep.resource:
                continue

            handler = handlers.get(dep.type)
            if handler:
                result[self.get_name(dep)] = handler(dep)

        return result
