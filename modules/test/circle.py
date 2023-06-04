from mathutils import Matrix


def draw_circle(position, color, radius, *, segments=None, mat=Matrix.Identity(4)):
    from math import sin, cos, pi, ceil, acos
    import gpu
    from gpu.types import (
        GPUBatch,
        GPUVertBuf,
        GPUVertFormat,
    )

    if segments is None:
        max_pixel_error = 0.25  # TODO: multiply 0.5 by display dpi
        segments = int(ceil(pi / acos(1.0 - max_pixel_error / radius)))
        segments = max(segments, 8)
        segments = min(segments, 1000)

    if segments <= 0:
        raise ValueError("Amount of segments must be greater than 0.")

    with gpu.matrix.push_pop():
        gpu.matrix.translate(position)
        gpu.matrix.load_matrix(gpu.matrix.get_model_view_matrix() @ mat)
        gpu.matrix.scale_uniform(radius)

        mul = (1.0 / (segments - 1)) * (pi * 2)
        verts = [(sin(i * mul), cos(i * mul)) for i in range(segments)]

        fmt = GPUVertFormat()
        pos_id = fmt.attr_add(id="pos", comp_type='F32', len=2, fetch_mode='FLOAT')
        vbo = GPUVertBuf(len=len(verts), format=fmt)
        vbo.attr_fill(id=pos_id, data=verts)
        gpu.state.line_width_set(3)
        batch = GPUBatch(type='LINE_STRIP', buf=vbo)
        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        batch.program_set(shader)
        shader.uniform_float("color", color)
        batch.draw()