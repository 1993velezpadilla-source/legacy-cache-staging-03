extends SceneTree
# Native Godot-render proof: original licensed 3D game art, NOT V8 PBR/church.
var images: Dictionary = {}
func _initialize() -> void:
    call_deferred("_run")
func _run() -> void:
    var packed: PackedScene = load("res://source_original.glb") as PackedScene
    if packed == null:
        _bad("Original GLB failed import")
        return
    var level := Node3D.new()
    root.add_child(level)
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color(0.075, 0.095, 0.12)
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color(0.85, 0.9, 1.0)
    env.ambient_light_energy = 1.5
    var world := WorldEnvironment.new()
    world.environment = env
    level.add_child(world)
    var camera := Camera3D.new()
    camera.current = true
    camera.near = 0.01
    camera.fov = 63.0
    level.add_child(camera)
    var lamp := OmniLight3D.new()
    lamp.position = Vector3(0, 0.4, -0.12)
    lamp.light_energy = 7.0
    lamp.omni_range = 5.0
    camera.add_child(lamp)
    var model: Node3D = packed.instantiate() as Node3D
    if model == null:
        _bad("GLB root was not Node3D")
        return
    camera.add_child(model)
    var faces: int = _faces(model)
    if faces != 14450:
        _bad("Real model triangle count changed: %s" % faces)
        return
    model.rotation = Vector3(0, PI * .5, 0)
    model.position = Vector3(.19, -.16, -.42)
    model.visible = false
    await _photo("00-background")
    model.visible = true
    await _photo("01-hip")
    model.position = Vector3(0, -.115, -.36)
    await _photo("02-ads-pose")
    model.position = Vector3(.10, -.13, -.40)
    model.rotation.y = PI * .5 + deg_to_rad(18)
    await _photo("03-inspect")
    var f := FileAccess.open(_dir().path_join("report.json"), FileAccess.WRITE)
    if f == null:
        _bad("Report not writable")
        return
    f.store_string(JSON.stringify({"engine":Engine.get_version_info(), "triangles":faces, "source":"Moony_State ORIGINAL GLB 1K not V8 PBR", "images":images,"church_integrated":false,"ads_accuracy_proven":false, "reload_proven":false}, "\t"))
    f.close()
    print("GODOT_CAPTURE_READY_PENDING_IMAGE_GATE")
    quit(0)
func _faces(node: Node) -> int:
    var n: int = 0
    if node is MeshInstance3D:
        var mesh: Mesh = (node as MeshInstance3D).mesh
        if mesh != null:
            for surface in range(mesh.get_surface_count()):
                if mesh.surface_get_primitive_type(surface) != Mesh.PRIMITIVE_TRIANGLES:
                    continue
                var a: Array = mesh.surface_get_arrays(surface)
                var idx: PackedInt32Array = a[Mesh.ARRAY_INDEX]
                n += int(idx.size() / 3) if not idx.is_empty() else int((a[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3)
    for child in node.get_children():
        n += _faces(child)
    return n
func _dir() -> String:
    var p: String = OS.get_environment("MP40_CAPTURE_DIR")
    if p.is_empty():
        p = ProjectSettings.globalize_path("user://mp40_render")
    DirAccess.make_dir_recursive_absolute(p)
    return p
func _photo(name: String) -> void:
    for i in range(5):
        await process_frame
    await RenderingServer.frame_post_draw
    var img: Image = root.get_texture().get_image()
    if img == null or img.is_empty():
        _bad("Empty capture " + name)
        return
    var p: String = _dir().path_join(name + ".png")
    if img.save_png(p) != OK:
        _bad("Save failed " + name)
        return
    images[name] = p
func _bad(reason: String) -> void:
    push_error("GODOT_NATIVE_MP40_RED: " + reason)
    quit(2)
